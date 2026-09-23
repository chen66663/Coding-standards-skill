#!/usr/bin/env python3
"""Parse component-list exports from EDA/BOM tools into a stable inventory.

Supported record shape:
    C0402 ! CC0402JRNPO9BN470容值:47pF;精度:±5% ! 47pF ,
            ; CC3
    ,

The parser is intentionally read-only. It normalizes component metadata but
does not claim that a component-list export contains schematic connectivity.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


URL_RE = re.compile(r"https?://[^\s,;]+")
RECORD_RE = re.compile(r"^\s*(?P<footprint>.+?)\s*!\s*(?P<part>.+?)\s*!\s*(?P<value>.+?)\s*,?\s*$")
REFERENCE_LINE_RE = re.compile(r"^\s*;\s*(?P<references>.*?)\s*$")
ATTRIBUTE_RE = re.compile(r"^\s*(?P<key>[^:]+?)\s*:\s*(?P<value>.*?)\s*$")

ATTRIBUTE_LABELS = (
    r"容值",
    r"阻值",
    r"电感量",
    r"电容",
    r"电阻",
    r"精度",
    r"误差",
    r"容差",
    r"额定\s*电压",
    r"耐压",
    r"工作\s*电压",
    r"额定\s*电流",
    r"额定\s*功率",
    r"功率",
    r"电流",
    r"材质\s*\(\s*温度系数\s*\)",
    r"温度\s*系\s*数",
    r"封装",
    r"品牌",
    r"厂商",
    r"类型",
    r"极性",
    r"频率",
    r"负载\s*电容",
    r"饱和\s*电流",
    r"DCR",
    r"ESR",
    r"VDS",
    r"VGS",
    r"RDS\s*\(?\s*on\s*\)?",
)
ATTRIBUTE_START_RE = re.compile(r"(?=(?:%s)\s*:)" % "|".join(ATTRIBUTE_LABELS))


@dataclass
class ComponentRecord:
    footprint: str
    part_number: str
    value: str
    attributes: List[Tuple[str, str]] = field(default_factory=list)
    datasheet_urls: List[str] = field(default_factory=list)
    designators: List[str] = field(default_factory=list)
    unknown_fields: List[str] = field(default_factory=list)
    source_line: int = 0
    source_text: str = ""


def normalize_key(value: str) -> str:
    value = re.sub(r"\s+", "", value)
    return value.replace("（", "(").replace("）", ")")


def normalize_value(value: str) -> str:
    value = value.strip().strip("'\"")
    value = value.replace("µ", "u").replace("μ", "u")
    return re.sub(r"\s+", "", value).lower()


def parse_part_text(text: str) -> Tuple[str, List[Tuple[str, str]], List[str], List[str]]:
    urls = URL_RE.findall(text)
    without_urls = URL_RE.sub("", text)
    chunks = [chunk.strip() for chunk in without_urls.split(";")]
    chunks = [chunk for chunk in chunks if chunk]
    if not chunks:
        return "", [], urls, []

    first = chunks[0]
    match = ATTRIBUTE_START_RE.search(first)
    if match:
        part_number = first[: match.start()].strip()
        chunks[0] = first[match.start() :]
    else:
        colon = first.find(":")
        if colon > 0:
            part_number = first[:colon].strip()
            chunks[0] = first[colon:]
        else:
            part_number = first.strip()
            chunks[0] = ""

    attributes: List[Tuple[str, str]] = []
    unknown: List[str] = []
    for chunk in chunks:
        if not chunk:
            continue
        attribute = ATTRIBUTE_RE.match(chunk)
        if not attribute:
            unknown.append(chunk)
            continue
        key = normalize_key(attribute.group("key"))
        value = attribute.group("value").strip()
        if key and value:
            attributes.append((key, value))
    return part_number, attributes, urls, unknown


def parse_designators(text: str) -> List[str]:
    return [token for token in re.split(r"[\s,;]+", text.strip()) if token]


def comparable_attribute(record: ComponentRecord, names: Sequence[str]) -> Optional[str]:
    for key, value in record.attributes:
        if key in names:
            return value
    return None


def finalize_record(
    data: Dict[str, object],
    parsed_records: List[ComponentRecord],
    warnings: List[str],
) -> None:
    raw_part = str(data["raw_part"]).strip()
    part_number, attributes, urls, unknown = parse_part_text(raw_part)
    record = ComponentRecord(
        footprint=str(data["footprint"]).strip(),
        part_number=part_number,
        value=str(data["value"]).strip().strip("'\""),
        attributes=attributes,
        datasheet_urls=urls,
        designators=list(data["designators"]),
        unknown_fields=unknown,
        source_line=int(data["source_line"]),
        source_text=str(data["source_text"]),
    )
    parsed_records.append(record)

    line = record.source_line
    if not record.footprint:
        warnings.append("第 %s 行：缺少封装" % line)
    if not record.part_number:
        warnings.append("第 %s 行：缺少型号" % line)
    if not record.designators:
        warnings.append("第 %s 行：缺少位号（例如 ; C1 C2）" % line)
    if record.unknown_fields:
        warnings.append(
            "第 %s 行：未识别字段 %s"
            % (line, "; ".join(record.unknown_fields))
        )

    expected = comparable_attribute(
        record,
        ("容值", "阻值", "电感量", "电容", "电阻"),
    )
    if expected and record.value and normalize_value(expected) != normalize_value(record.value):
        warnings.append(
            "第 %s 行：参数值 `%s` 与属性 `%s` 不一致"
            % (line, record.value, expected)
        )


def parse_text(text: str) -> Tuple[List[ComponentRecord], List[str]]:
    records: List[ComponentRecord] = []
    warnings: List[str] = []
    current: Optional[Dict[str, object]] = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == ",":
            continue

        record_match = RECORD_RE.match(line)
        if record_match:
            if current is not None:
                finalize_record(current, records, warnings)
            current = {
                "footprint": record_match.group("footprint"),
                "raw_part": record_match.group("part"),
                "value": record_match.group("value"),
                "designators": [],
                "source_line": line_number,
                "source_text": line.rstrip(),
            }
            continue

        reference_match = REFERENCE_LINE_RE.match(line)
        if current is not None and reference_match:
            current["designators"].extend(
                parse_designators(reference_match.group("references"))
            )
            continue

        if current is not None:
            warnings.append("第 %s 行：当前记录中的未解析内容 `%s`" % (line_number, stripped))
        else:
            warnings.append("第 %s 行：记录外的未解析内容 `%s`" % (line_number, stripped))

    if current is not None:
        finalize_record(current, records, warnings)

    designator_lines: Dict[str, List[int]] = {}
    footprint_by_part: Dict[str, str] = {}
    for record in records:
        for designator in record.designators:
            designator_lines.setdefault(designator, []).append(record.source_line)

        if record.part_number:
            previous = footprint_by_part.get(record.part_number)
            if previous is not None and previous != record.footprint:
                warnings.append(
                    "型号 `%s` 同时出现封装 `%s` 和 `%s`"
                    % (record.part_number, previous, record.footprint)
                )
            else:
                footprint_by_part[record.part_number] = record.footprint

    for designator, source_lines in designator_lines.items():
        if len(source_lines) > 1:
            warnings.append(
                "位号 `%s` 重复出现于第 %s 行"
                % (designator, ", ".join(str(line) for line in source_lines))
            )

    return records, warnings


def record_as_row(record: ComponentRecord) -> List[str]:
    attributes = "; ".join("%s=%s" % pair for pair in record.attributes)
    return [
        " ".join(record.designators),
        record.footprint,
        record.part_number,
        record.value,
        attributes,
        " ".join(record.datasheet_urls),
    ]


def print_tsv(records: Sequence[ComponentRecord], warnings: Sequence[str]) -> None:
    headers = ("位号", "封装", "型号", "参数值", "关键属性", "数据手册")
    print("\t".join(headers))
    for record in records:
        print("\t".join(record_as_row(record)))
    for warning in warnings:
        print(warning, file=sys.stderr)


def print_json(source: str, records: Sequence[ComponentRecord], warnings: Sequence[str]) -> None:
    payload = {
        "source": source,
        "record_count": len(records),
        "records": [asdict(record) for record in records],
        "warnings": list(warnings),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_lcsc_list(records: Sequence[ComponentRecord]) -> None:
    seen = set()
    for record in records:
        model = record.part_number.strip()
        if model and model not in seen:
            seen.add(model)
            print(model)


def read_source(path: str) -> Tuple[str, str]:
    if path == "-":
        return sys.stdin.read(), "<stdin>"
    source = Path(path)
    return source.read_text(encoding="utf-8-sig"), str(source)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="解析嘉立创 EDA/BOM 的 `封装 ! 型号+属性 ! 参数 ; 位号` 导出格式",
    )
    parser.add_argument("source", help="输入文件；使用 - 从标准输入读取")
    parser.add_argument(
        "--format",
        choices=("tsv", "json", "lcsc"),
        default="tsv",
        help="输出格式；lcsc 输出去重后的型号列表，可交给 lcsc_lookup.py bom",
    )
    args = parser.parse_args()

    try:
        text, source_name = read_source(args.source)
    except OSError as error:
        print("读取失败: %s" % error, file=sys.stderr)
        return 1

    records, warnings = parse_text(text)
    if not records:
        print("没有解析到元件记录", file=sys.stderr)
        for warning in warnings:
            print(warning, file=sys.stderr)
        return 1

    if args.format == "tsv":
        print_tsv(records, warnings)
    elif args.format == "json":
        print_json(source_name, records, warnings)
    else:
        print_lcsc_list(records)
        for warning in warnings:
            print(warning, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
