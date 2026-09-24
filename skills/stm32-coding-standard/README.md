# STM32 Coding Standard

用于 Codex 的 STM32 C 代码审查、重构和实现规范。技能重点不是机械格式化，
而是让代码在资源受限、中断并发、硬件异常和不同编译器下仍然可读、可测、
可恢复。

## 适用场景

- STM32 裸机主循环、状态机和板级驱动。
- HAL、LL、CMSIS 和标准外设库代码。
- CAN、UART、I2C、SPI、DMA、定时器和中断相关代码。
- 代码评审、提交前检查、重构、错误恢复和实时性分析。
- 按工程规范生成新的头文件、源文件和公共接口文档。

以下情况需要项目规则或芯片资料优先：已有编码约定、安全要求、芯片勘误、
协议时序、启动文件和第三方库修改。

## 核心检查

### 文件和接口

- 文件头采用 STM32 标准外设库风格，包含 `@file`、`@author`、
  `@version`、`@date`、`@brief` 和必要的 `@attention`。
- 头文件必须有 include guard；C/C++ 共用头文件使用 `extern "C"`。
- 头文件只保留声明、typedef、宏和接口说明，普通定义放入 `.c`。
- 公共接口使用 Doxygen，并说明单位、范围、所有权、前置条件、调用上下文、
  返回值和失败恢复。
- 硬件时序、异步回调和共享资源应在接口注释中明确约束，不能只重复函数名。

### 命名与排版

- 变量、函数和文件名使用小写 `snake_case`。
- 类型使用 UpperCamelCase，宏和常量使用 `UPPER_SNAKE_CASE`。
- 模块公共符号带统一前缀，例如 `HW_CanMsg`、`HW_CAN_Init`。
- 使用 4 空格缩进，不使用 Tab；保持工程现有换行和注释编码。
- 注释使用 `/* ... */`，多行注释每行以 ` * ` 对齐。

### 安全与实时性

- 初始化所有自动变量；访问指针和数组前检查边界。
- 所有可能失败的调用都要检查返回值，并保留错误语义。
- 禁止在实时路径动态分配；禁止 `gets`、`strcpy`、`strcat`、`sprintf`
  和 `scanf` 等不安全接口。
- 中断和回调只允许有限操作，例如写 `static volatile` 标志、诊断计数或
  单生产者/单消费者队列，不推进复杂状态机或直接驱动执行器。
- DMA、缓存、时钟、GPIO 复用和外设实例的结论必须能追溯到 MCU 文档。

### 验证

- 修改后至少完成一次完整编译，目标是零错误、零警告。
- 检查编码、换行、ELF/HEX/MAP 产物、RAM 和 Flash 使用。
- 对无法在本地验证的板级行为，明确列出硬件、时序和测试缺口。

## 参考文档

- `references/local-rules.md`：本地 C 规范映射和门禁。
- `references/stm32-device-documentation.md`：MCU 型号识别和官方资料检索。
- `references/check-commands.md`：编码、编译和静态检查命令。
- `references/authoritative-sources.md`：C、MISRA、CERT 和 ST 资料入口。
- `references/review-template.md`：审查报告输出模板。

## 使用示例

```text
使用 stm32-coding-standard 检查 Hardware\inc\hw_can.h。
目标 MCU 是 STM32G431CBT6，项目使用 HAL + C99。
重点检查文件头、命名、include guard、接口前置条件和中断约束。
```

```text
按 stm32-coding-standard 审查 CAN 驱动。
先检查接收队列所有权、FIFO 错误恢复和中断上下文，再给最小修改方案。
```

## 输出要求

- 先列高风险问题，再列规范问题。
- 每条问题包含文件、行号、影响、修改建议和依据。
- 引用芯片资料时给出文档类型、文档号、修订版和页码或章节。
- 不确定的型号、协议和电气假设必须单独标注。
