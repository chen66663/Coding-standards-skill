# Coding Standards Skill

用于集中维护 Codex 工程检查与编码规范类的 skills。

## 当前包含

### schematic-reviewer

原理图检查与审核 skill。支持：

- 读取芯片数据手册并整理关键电源、复位、接口和外围电路约束。
- 检查去耦、上下拉、时钟、接口电平、功率路径和 ESD 保护。
- 解析嘉立创 EDA/BOM 导出，按型号去重后并发核验立创库存、封装和参数。
- 计算大电流走线宽度并给出 PCB 加宽建议。
- 直接输出问题清单，不生成报告、HTML 或图片。

入口文件：

- `skills/schematic-reviewer/SKILL.md`
- `skills/schematic-reviewer/README.md`

## 安装到 Codex

将目录复制到 `$HOME\.codex\skills`：

```powershell
Copy-Item -Recurse .\skills\schematic-reviewer "$HOME\.codex\skills\schematic-reviewer"
```

## 验证

```powershell
python .\skills\schematic-reviewer\tests\test_parse_schematic_export.py
python .\skills\schematic-reviewer\tests\test_lcsc_lookup.py
python .\skills\schematic-reviewer\tests\test_review_export.py
```

## 仓库约定

- 每个 skill 放入独立的 `skills/<skill-name>/` 目录。
- 不提交 `config.json`、密钥、日志、`__pycache__` 和本机状态文件。
- 新增 skill 后同步更新本 README。
