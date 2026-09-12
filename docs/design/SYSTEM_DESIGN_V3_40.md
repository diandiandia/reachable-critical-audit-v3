# SYSTEM_DESIGN_V3_40 — 变更边界不变式 + 模块影响面 + 兼容性

## 变更边界不变式（不改）

1. 阶段骨架 (R0-R6) 与六门禁判据语义不变——D-1 只改判级函数内部分支,
   gate ③ 的判定输入 (grade) 语义与门禁断言语义零变更
2. 队列数据模型主体不变——无新候选字段 (D-7 的 empirical_backfill_candidates
   是 collect 输出提示, 不落队列 schema)
3. 无新门禁名/无新强制义务/无新阶段 (四缺陷④)
4. verifier/refuter 输出 schema 不变 (D-2 义务由 evidence 文本承载)

## 模块影响面

| 文件 | 变更 | 风险 |
|---|---|---|
| src/evidence_ledger.py | grade_verdict 增 fidelity 分支 (~10 行) | 旧队列复跑回归 (mechanism 档候选判级变化——预期为合规修正) |
| tools/batch_verify.py | verifier 任务书步骤 3.5 (~8 行); r35-collect 扫描 (~15 行) | 任务书文本变化无 schema 影响; collect 输出增 warn 键 |
| assets/resources/checklist_library.json | +1 条目 | 计数守卫同步 (48→49) |
| assets/task_templates/hypothesis_filter.md | 两处条款增补 | 提示级 |
| assets/harness_manuals/ENVIRONMENT_PROBES.md | +1 段 | 内容资产 |

## 兼容性

- 旧队列复跑: D-1 生效后, 历史队列中 fidelity=mechanism 且 status=confirmed 的
  候选判级从 empirically_confirmed 回退 edge_proven——**这是合规修正** (该判级
  本属越级); 复跑断言必须对照: blocking 零新增, warn 变化须逐条审阅后签收
- collect 输出新增键 empirical_backfill_candidates: 消费端为主代理, 无下游
  机械消费者 (assert_ledger 不读)——加键零破坏
- TOOLING_VERSION 3.39 → 3.40: 旧队列 tooling 告警 (SWR-V3.4.4-008) 会提示
  version skew——按既有惯例复跑时不阻断 (warn 级)
