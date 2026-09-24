# Coding Standards Skill

用于集中维护 Codex 工程检查与编码规范类 skills。

## 当前包含

### stm32-coding-standard

面向 STM32 裸机、HAL/LL/CMSIS C 代码的审查、重构与编写规范。技能会先识别
目标 MCU，再结合工程约定、芯片手册、勘误、MISRA/CERT 和实际硬件约束检查问题。

主要覆盖：

- 文件头、Doxygen 接口注释、include guard 和 `extern "C"` 兼容。
- C 类型、函数、宏、全局变量、静态符号和模块前缀命名。
- 头文件职责、声明与定义边界、模块队列与接口所有权。
- 中断、DMA、缓存一致性、并发、错误处理、边界与未定义行为。
- STM32 时钟、GPIO、外设复用、实时性、编译器和地图文件验证。
- 注释率、圈复杂度、嵌套深度、函数长度和重复代码门禁。

入口文件：

- `skills/stm32-coding-standard/SKILL.md`
- `skills/stm32-coding-standard/README.md`

## 目录结构

```text
Coding-standards-skill/
|-- README.md
`-- skills/
    `-- stm32-coding-standard/
        |-- SKILL.md
        |-- README.md
        |-- agents/
        `-- references/
```

## 安装到 Codex

将 skill 目录复制到 `$HOME\.codex\skills`：

```powershell
Copy-Item -Recurse `
  .\skills\stm32-coding-standard `
  "$HOME\.codex\skills\stm32-coding-standard"
```

## 使用

在 Codex 中指定要检查的文件或工程，并明确目标 MCU 和工程约束。例如：

```text
使用 stm32-coding-standard 检查 Hardware\inc\hw_can.h。
目标 MCU 是 STM32G431CBT6，项目要求 HAL + C99，注释编码按工程现有规则。
```

```text
按 stm32-coding-standard 审查这个 CAN 驱动，重点检查中断上下文、
接收队列所有权、错误恢复、命名和 Doxygen 注释。
```

技能默认先给高风险问题，再给规范问题；报告中包含文件、行号、影响、
修改建议和验证结果。不能确认的型号、协议或电气假设会单独标注。

## 代码规范摘要

- 文件头使用 `/** ... */`，至少包含 `@file`、`@author`、`@version`、
  `@date`、`@brief`，需要时补充 `@attention`。
- 头文件必须有 include guard；C/C++ 共用头文件使用 `extern "C"`。
- 变量和函数使用小写 `snake_case`，类型使用 UpperCamelCase，宏和常量使用
  `UPPER_SNAKE_CASE`。
- 模块类型和公共接口带模块前缀，例如 `HW_CanMsg`、`HW_CAN_Init`。
- 注释使用 `/* ... */`；接口文档使用 Doxygen `@param`、`@retval`、
  `@note` 和 `@warning`。
- 公共 API 要写清单位、范围、所有权、前置条件、调用上下文和失败语义。
- 中断和回调只做有限工作；共享状态、队列所有者和恢复路径必须明确。
- 修改后必须编译、检查警告、编码、镜像大小和未被测试覆盖的硬件假设。

## 维护约定

- 每个 skill 放入独立的 `skills/<skill-name>/` 目录。
- 不提交 `config.json`、密钥、日志、`__pycache__` 或本机状态文件。
- 修改规则后同步更新 skill README 和根 README。
- 芯片规则以 ST 官方 Datasheet、Reference Manual 和 Errata 为准。
