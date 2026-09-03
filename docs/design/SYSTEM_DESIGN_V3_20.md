# SYSTEM DESIGN V3.20 — 变更边界不变式与模块影响面（2026-09-03）

## 变更边界不变式

1. **阶段骨架不变**：R0-R6 零改动。
2. **六门禁①-⑧判据语义不变**：本版全部为提示级（任务书文本）/warn 级
   （collect 结果 warnings）/optional schema 属性；warn 不进任何门禁判据。
   无新门禁名。
3. **队列数据模型主体不变**：candidates 增两个可选追溯字段
   （guard_pass_subsets / premises_verified，非空才落盘）——与 v3.17
   containment 落盘形态同构（可选、缺省空、无消费方必读）。
4. **分级权威不变（修订 2026-09-03 对账后）**：evidence_grade 机械重算仍为
   唯一权威，grade_self_reported 仍仅追溯。evidence_ledger.py 增一条
   canonical 保留键推断分支（SWR-V3.20-006）——对账实测存储分级不可复算
   （SKILL.md 回填键集与判级条件互斥），推断只做 lenient 兼容 + 提示，
   不改变显式 status/scope 路径的既有语义。
5. **零根因臆测**：drift_summary 只报方向对（stored→mechanical），不做
   backfill/underreport 归因——无机械判据的归因是误猜（v3.14 D-3 先例）。

## 模块影响面

| 模块 | 改动 | 性质 |
|---|---|---|
| evidence_ledger.py | grade_verdict canonical 保留键推断分支（SWR-V3.20-006，lenient+提示） | P1 机械 |
| tools/batch_verify.py | `_build_prompt` 输出格式节（三值枚举+口径注记+两字段）+ 步骤 0/步骤 4 条文；stage_collect 重算块统计 + result.drift_summary/warnings + 两字段条件校验与白名单落盘 | P1 机械 + P3 内容 |
| workflow_export.py | VERDICT_SCHEMA properties 增 guard_pass_subsets/premises_verified（optional） | P2 结构 |
| lessons_recorder.py | grade_recomputed detail 附方向对 | P1 机械 |
| SKILL.md | R3 输出契约一句 + 数据模型速查两字段 + v3.20 增量段 | P4 文档 |
| workflow_export.py:22 + tests 守卫 ×10 | TOOLING 3.20 | P4 版本链 |
| tools/gen_tracking.py / REQUIREMENTS_TRACKING.md | VERSIONS 登记 + 手工段 | P4 版本链 |

## 兼容性矩阵

| 面向 | 判定 | 依据 |
|---|---|---|
| 旧队列复跑 | 零新增告警 | evidence_grade 规则未动；新字段 optional 缺失即跳过；warn 只出现在 collect 运行时输出，不落盘断言面 |
| 旧 workflow 脚本 | 兼容 | VERDICT_SCHEMA 只增 optional properties，旧 agent 输出照常通过 |
| 旧 SKILL.md 指引流程 | 兼容 | 输出格式节新字段为条件触发（空数组合法），规则 1 措辞只增不改 |
| 渲染器/报告 | 零影响 | 不消费新字段 |
| harness/资产计数 | 零变化 | 本轮不新增计数资产 |

## 风险与回退

- **风险**：任务书输出格式节变长 → verifier 输出噪声？措辞为提示级且字段
  optional，最坏情况=字段缺失 → collect warn（可忽略）。
- **回退**：全部改动可逐条 revert（P1/P2/P3 无交叉依赖：schema optional
  先落，collect 校验后落，任一 revert 不破坏另一侧）。
