# SWR V3.20 — 设计规则（2026-09-03）

## SWR-V3.20-001（D-1 自报分级三值枚举 + 机械口径注记）

`_build_prompt` 输出格式节两处改动（纯文本提示级）：
1. `"evidence_grade": "static_only | edge_proven"` → 三值枚举
   `"static_only | edge_proven | empirically_confirmed"`；
2. 规则 1 增口径注记（约两句）：
   "evidence_grade 是自报值，**仅追溯**——collect 落盘时由 evidence_ledger
   机械重算为唯一权威（规则：empirical 结构化字段非空 → empirically_confirmed；
   REACHABLE 逐跳 edge_evidence 计数 ≥ 链长-1 → edge_proven，否则 static_only）。
   evidence 文本中的 grep 调用方命中必须结构化进 edge_evidence 数组（合并边
   必须拆分）——文本证据不会被机械分级采纳。"
**不改写任何字段、不设任何新校验**。测试：导出 verify payload 的 prompt 含
三值枚举与口径注记；非库型目标同样渲染（本段语言无关）。

## SWR-V3.20-002（D-2 collect drift_summary）

`stage_collect` 重算块统计漂移方向对（stored→mechanical，rank 序
static_only<edge_proven<empirically_confirmed），落盘结果 JSON 增
`drift_summary: {recomputed, promoted, demoted, pairs: {pair: count}}`。
只报方向对事实，**不猜测根因归属**（edge_backfill vs self_underreport 无机械
判据——误猜风险>收益，v3.14 D-3 先例方向）。测试：构造单候选项目队列跑
stage_collect，自报 static_only + 满边证据 → pairs 含 static_only→edge_proven；
自报 edge_proven + empirical dict → pairs 含 edge_proven→empirically_confirmed；
无漂移 → drift_summary 零计数。

## SWR-V3.20-003（D-3 lessons_recorder 方向对）

lessons_recorder.py:62-64 的 grade_recomputed 条目 detail 由
`机械分级重算 (source)` 改为 `机械分级重算 stored→mechanical (source)`
（stored 取自 grade_self_reported，mechanical 取自 evidence_grade——
两字段均为队列既有字段，零新增）。测试：构造含 grade_self_reported≠
evidence_grade 的队列，recorder 产出 detail 含 `static_only→edge_proven`
形态；无漂移候选不产出该条目（既有行为不变）。

## SWR-V3.20-004（D-4 守卫通过子集枚举义务 + guard_pass_subsets 字段）

1. **P3 任务书**：`_build_prompt` 步骤 4 增一条义务（提示级）：
   "守卫封顶类阻断必须枚举**守卫通过子集**（文件真实包含的声明尺寸/自动
   切换 tier/重试路径/错误路径分支）——只论证主路径的封顶不构成完整阻断
   （复活维度 7 前移：该缺口已在实战被复活波命中）"。
2. **P3 输出格式**：JSON 增
   `"guard_pass_subsets": [{"guard_location": "file:line", "enumerated_subsets": "...", "coverage": "全覆盖 | 有未枚举子集"}],`——条件触发：阻断论证引用守卫/封顶时必填，否则空数组。
3. **P2 schema**：workflow_export.py VERDICT_SCHEMA properties 增
   `"guard_pass_subsets": {"type": "array"}`（optional，不进 required——
   条件触发校验在 collect 侧）。
4. **P1 collect**：条件校验 warn（不阻断）：`verdict==UNREACHABLE` 且
   `blocking_point != "no production callers"` 且 `guard_pass_subsets` 缺失/空
   → result.warnings 增条目（"UNREACHABLE 阻断论证未附 guard_pass_subsets
   枚举——resurrect 派发前主代理据此评估缺口维度"）。字段非空时白名单落盘
   `entry["guard_pass_subsets"]`。
5. **P4**：SKILL.md 数据模型速查 candidates 增 `guard_pass_subsets[]?`。

测试：任务书含义务条文；schema 含 optional 属性且不在 required；UNREACHABLE
非死代码豁免无字段 → warnings 非空；`no production callers` → warnings 零；
REACHABLE → warnings 零；字段非空 → 队列 entry 落盘；反面分支（warn 不改写
任何字段、不改变 verdict）。

## SWR-V3.20-005（D-5 premises_verified 字段）

1. **P3 任务书**：步骤 0 尾增一句："前提断裂终止回溯时，断裂前提必须逐条
   写入 premises_verified（每项 premise/file:line/status）"。
2. **P3 输出格式**：JSON 增
   `"premises_verified": [{"premise": "...", "file": "file:line", "status": "verified | broken"}],`——条件触发：前提断裂按断裂方向判 UNREACHABLE 时必填，否则空数组。
3. **P2 schema**：`"premises_verified": {"type": "array"}`（optional）。
4. **P1 collect**：条件校验 warn（触发条件同 SWR-V3.20-004）+ 白名单落盘。
5. **P4**：数据模型速查增 `premises_verified[]?`。

测试：任务书含该句；schema optional；正反分支同 D-4 形态；落盘断言。

## SWR-V3.20-006（D-6 canonical 保留键推断）

1. **P1 evidence_ledger**：`grade_verdict` 增推断分支——empirical dict 无
   status/scope 且 `outcome`/`evidence_numbers`/`report` 三键齐全 →
   empirically_confirmed + errors 附回填提示（同 v3.4.1 scope_infer 形态）。
   三键不全 → 不升级（现有规则不变）。测试：canonical 形态 dict →
   empirically_confirmed 且 errors 含 status 提示；部分键 dict →
   维持 edge_proven；status 显式值路径零变化（既有用例覆盖）。
2. **P4 SKILL.md**：R5 回填规范 canonical 键集补 `status:"confirmed"`——
   回填时直接写 status 是正解，推断只是 lenient 兼容（存储分级可复算）。

## 通用约束（本版全部 SWR 适用）

- **零改写**：任何修复不得自动修改 verifier 输出字段值（self_report 保留
  原值、evidence_grade 不按自报回写、warn 不触发降级/阻断）。
- **零新门禁**：warn 不进 assert_ledger 判据。
- **去项目化**：运行时正文零项目名/零候选 id（WebKit/CAND-001/GLib 只允许
  出现在 source_lessons 追溯与测试注释）。
