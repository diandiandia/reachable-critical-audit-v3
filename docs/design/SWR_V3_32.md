# SWR_V3.32

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.32-001 | R2 对抗枚举条款（P3）：hints 装载后按族 Top 条目做缺陷形态展开 | D-1 | test_v332: SKILL.md 条款文本 |
| SWR-V3.32-002 | tools/fixminer.py：安全修复挖掘+族分类（git 仓库；关键词分级；--since 可选；无 git 历史输出 NO_GIT） | D-2 提示级工具 | test_v332: QuickJS 仓库实跑输出形态/family 字段/NO_GIT 分支 |
| SWR-V3.32-003 | r35-collect 回显 strengthened + sibling 裁决提示 | D-3 | test_v332: 含补强队列 collect 后结果含 strengthened_notes |
| SWR-V3.32-004 | hints --kind 加权 + lessons_refs 轻量检索 | D-4 | test_v332: kind 重排断言/library 目标 MEMORY-SAFETY 前置/lessons_refs 非空(c) |

## 四缺陷评估
①盲目带入：fixminer 输出无项目名语义(commit message 原文回显属目标自身数据, 非资产)；hints 检索引用文件名不写正文 ✓
②设计偏见：全部提示级；fixminer 不自动生成假设(输出分类摘要, 主代理生成) ✓
③死代码：fixminer 消费者=R2 流程；--kind 消费者=hints 调用者；sibling 回显消费者=主代理裁决 ✓
④过设计：不建 lessons 全文检索索引(轻量文件名/族头匹配足矣)；不建 fixminer 自动入队 ✓
