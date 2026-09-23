# 嘉立创 EDA / BOM 导出格式

## 典型记录

```text
C0402 ! CC0402JRNPO9BN470容值:47pF;精度:±5%;额定电压:50V;材质(温度系数):NP0;https://atta.szlcsc.com/example.pdf ! 47pF ,
        ; CC3
,
```

字段含义：

| 位置 | 含义 | 示例 |
|---|---|---|
| 第一个 `!` 前 | 封装 | `C0402`、`C0603` |
| 两个 `!` 之间 | 型号、规格属性和数据手册链接 | `CC0402JRNPO9BN470...` |
| 第二个 `!` 后 | 表格中的参数值 | `47pF`、`100nF` |
| 后续以 `;` 开头的行 | 使用该型号的位号 | `C1 C2` |
| 单独一行 `,` | 记录分隔符 | `,` |

## 快速预检（首选）

拿到导出文件后，先执行一次批量预检。该命令会解析、按型号去重、默认以 6
路并发查询立创/JLC，并只输出需要处理的项目：

```bash
python scripts/review_export.py export.txt --jobs 6
python scripts/review_export.py export.txt --verbose
python scripts/review_export.py export.txt --json
```

- 默认只输出解析告警、未精确匹配、无现货、封装冲突、参数冲突和关键参数无法核实项。
- 查询结果默认缓存 24 小时；可用 `--no-cache`、`--cache-ttl` 和 `--cache-file` 调整。
- `--verbose` 同时显示通过项，`--json` 用于后续自动化处理。
- 只有在需要原始清单、位号明细或自定义格式时，才继续调用解析器。

## 解析命令（补充）

```bash
python scripts/parse_schematic_export.py export.txt
python scripts/parse_schematic_export.py export.txt --format json
python scripts/parse_schematic_export.py export.txt --format lcsc
```

- 默认 `tsv` 输出适合人工核对。
- `json` 输出保留属性、位号、原始行号和解析告警。
- `lcsc` 输出每行一个去重型号，可直接保存后交给：
  `python scripts/lcsc_lookup.py bom <型号清单>`

## 证据边界

这类文件经常只是**元件清单**，不等同于完整原理图网表：

- 它能证明存在哪些位号、型号、封装、参数和手册链接。
- 它不能证明某个电容连接到了哪个 VDD 引脚，也不能证明 I2C 上拉、UART 交叉、晶振负载电容或 DCDC 网络是否正确，除非文件中另有明确的网络与引脚连接记录。
- 缺少精度、耐压或温度系数属于导出信息不完整，不能单独判定为电路设计错误；应结合完整型号、数据手册和电路工作条件核实。
- 同一型号可能拆成多条记录，不能只按行数判断器件数量；以位号去重后的数量为准。
- 型号、属性和位号发生冲突时，先把冲突作为待确认证据列出，不要静默采用其中一条。
- 预检中的参数冲突来自导出值与接口值比对；只能证明两处资料不一致，最终设计结论仍需结合数据手册和实际工作条件。

## 解析器行为

`parse_schematic_export.py` 会：

- 容忍行首行尾空格、引号包裹的参数值和多行位号。
- 从型号文本中拆分 `容值`、`阻值`、`精度`、`额定电压`、`温度系数` 等属性。
- 提取 `http://` 或 `https://` 数据手册链接。
- 汇总同一记录中的多个位号。
- 对缺少位号、参数值冲突、位号重复、同型号封装冲突和未识别字段给出告警。

解析器不会推断不存在的网络连接，也不会自动修改输入文件。
