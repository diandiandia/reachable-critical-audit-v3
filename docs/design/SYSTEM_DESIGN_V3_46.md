# SYSTEM_DESIGN_V3_46 — 变更边界不变式 + 模块影响面

## 1. 不变式（本周期不改）

- **阶段骨架**（R0/R1/R2/R3/R3.5/R4/R5/R6）：零改动。
- **六门禁判据语义**：零改动（D-1 的 tier=None 只影响候选生成侧的
  attacker_tier 推导提示，不影响门禁判定输入结构——verify 任务书该字段
  仍由子智能体证据判定，tier 推导仅作预填提示）。
- **队列数据模型主体**：候选/假说字段零新增（D-2 的 norm_flags 为
  collect 输出侧 warn 计数，不落队列）。
- **新义务禁令**：无新门禁名、无新强制义务、无新阶段——全部修复为
  机械修正/提示级条款/warn 输出。

## 2. 模块影响面

| 模块 | 变更 | 影响 |
|---|---|---|
| tools/batch_verify.py | D-1 句级清洗（457-459 附近）、D-2 归一器（964-970）、D-3 参数解析（3396-3398）、D-6 告警文案（864-905） | 单文件，向后兼容（旧队列零新增告警约束） |
| src/workflow_export.py | D-3 JS 预检段、D-7 注释、P4 版本号 | 导出 JS 行为加预检（快失败），payload schema 不变 |
| assets/task_templates/biz_hypothesis.md | D-2 canonical 键说明 | 任务书文本，提示级 |
| assets/task_templates/surface_map_domain.md | D-4 config 门核条款 | 任务书文本，提示级 |
| assets/harness_manuals/ | D-5 新手册文件 | 只增文件，不触现有手册 |

## 3. 兼容性

- 旧队列复跑：violations blocking=0、warn 数与变更前一致（K6-K9 已闭合
  队列不在复跑范围——其产物已归档；复跑集=gpac/freetype/av 代表队列）。
- fixture 三锚点：不触碰（D-1 清洗只改推导函数，anchor recall 路径不经过）。
- workflow payload：导出 JS 仅加预检段，args 形态不变——已有未 collect
  的 journal 不受影响。

## 4. 架构重设计判据核对（SWR-V3.43-007）

五信号零触发：单文件小修无冲突、无特例化累积、门禁不涉、教训库复用率
维持（K6-K9 教训直接驱动本周期缺陷清单）、兼容性债务不增。
