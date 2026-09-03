# REQ V3.20 — WebKit 审计复盘缺陷修复（2026-09-03）

## 上下文

WebKit 审计（2026-09-02，首个 super-large 浏览器引擎验收项目）闭合后，
lessons 落盘 `/root/WebKit/.audit_results/lessons.md`（唯一读入口，已按纪律读取）。
复盘发现 lessons 首版蒸馏报漏 5 条（已补记 §一补 5-9 条）；本版入库其中 2 条
（§一补 5/6），§一补 7/8/9（探针→可行性路由 / R1 矛盾扫描 / lessons 回填 DDL）
按排队纪律留 v3.21+。

缺陷全部经代码取证核实（编辑点行号为 dev 树实测，2026-09-03）；修法全部为
提示级/warn 级——不自动改写、不新增门禁、不新增强制义务。本版不改阶段骨架、
六门禁①-⑧判据语义、队列数据模型主体（candidates 增两个可选追溯字段）。

## 修复清单（6 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | verifier 任务书 evidence_grade 自报枚举只给两值（static_only/edge_proven），empirically_confirmed 结构性不可自报；且未明示「自报仅追溯、collect 机械重算为唯一权威」口径——WebKit 实测 15/20 漂移：6 例实证升档（R5 harness 回填）+ 9 例 static_only→edge_proven（evidence 文本 grep 命中未结构化进 edge_evidence 数组，主代理 collect 期重工） | 输出格式节 evidence_grade 补三值枚举 + 口径注记（自报仅追溯；机械规则=逐跳边证据计数 + empirical 结构化字段；evidence 中的 grep 命中必须结构化进 edge_evidence，合并边必须拆分）——提示级 | tools/batch_verify.py `_build_prompt` 输出格式块（:2924-2945，"evidence_grade": "static_only \| edge_proven" 行） |
| D-2 | collect 落盘结果无漂移汇总——75% 自报漂移到报告阶段才人工对账发现（WebKit 实录：主代理报告期回填 15 候选证据分级） | stage_collect 结果 JSON 增 `drift_summary`（recomputed 计数 + 方向对计数 {stored→mechanical: n}，无根因臆测——方向对即事实） | tools/batch_verify.py stage_collect 重算块统计（:519-549）+ result（:563-571） |
| D-3 | lessons_recorder 的 grade_recomputed 信号无方向——WebKit 29 条机械证据中 15 条同名裸条目（「机械分级重算 (source)」）成噪声，蒸馏时整体丢弃（报漏直接成因之一） | 条目 detail 附方向对（stored→mechanical） | lessons_recorder.py:62-64 |
| D-4 | R3 verifier 无守卫通过子集枚举义务（resurrect 维度 7 仅事后存在）——CAND-001/006 两例复活命中该缺口；v3.19 第 9 维前移后 CAND-011 仍漏证明「提示词加义务」不足以保证执行，须字段级强制 | ① 步骤 4 增守卫通过子集枚举义务条文（提示级）② 输出格式节增 `guard_pass_subsets` 条件触发字段（阻断论证引用守卫/封顶时必填）③ VERDICT_SCHEMA 增 optional 属性 ④ collect 条件校验 warn（UNREACHABLE 且非死代码豁免而无该字段 → warn，不阻断）⑤ 字段白名单落盘（非空时） | tools/batch_verify.py 步骤 4 块（:2886-2895）+ 输出格式块 + stage_collect；workflow_export.py VERDICT_SCHEMA（:39-50） |
| D-5 | 承重前提验证无结构化输出——resurrect 派发时主代理只能从 evidence 自由文本人工判断 verifier 是否核过前提（WebKit 复活派发评估实录） | ① 步骤 0 增结构化输出说明 ② `premises_verified` 条件触发字段（前提断裂终止回溯时必填）③ schema optional ④ collect 条件校验 warn（同上触发条件）⑤ 白名单落盘 | 同上三处 |
| D-6 | SKILL.md R5 回填规范的 canonical 键集与 grade_verdict 判级条件互斥——按规范回填的 empirical dict（outcome/evidence_numbers/report，无 status）永远无法机械评到 empirically_confirmed；WebKit 6 例实证候选存储分级不可复算（2026-09-03 复跑对账实测：14/15 可复算，6 例实证方向对全部失效） | ① grade_verdict 增 canonical 保留键推断（三键齐全且无 status/scope → empirically_confirmed + 回填提示，同 v3.4.1 scope_infer 先例形态）② SKILL.md canonical 键集补 `status:"confirmed"`（回填正解） | evidence_ledger.py grade_verdict（:125-134 后）+ SKILL.md canonical 键集段 |

## 义务入库三问（每条新义务）

| 义务 | ① 触发条件 | ② 消费者 | ③ 裁掉丢什么 |
|---|---|---|---|
| guard_pass_subsets 字段 | 条件触发：阻断论证引用守卫/封顶（机械触发=UNREACHABLE 且非死代码豁免） | collect 条件校验 warn + 主代理 resurrect 派发评估 + queue 落盘追溯 | 复活波继续以 3/4 命中率抓 R3 本应拦截的维度（WebKit 实录 CAND-001/006） |
| premises_verified 字段 | 条件触发：前提断裂致终止回溯 | 同上 | resurrect 派发继续靠自由文本人工评估（派发决策无结构化输入） |
| drift_summary | 无条件（每次 collect 一段计数，成本≈0） | 主代理收波对账 + lessons_recorder 信号上下文 | 75% 漂移继续到报告阶段才被发现 |
| 三值枚举+口径注记 | 无条件（输出格式节固有文本） | verifier 自报口径对齐 + 主代理重工削减 | 6 例实证升档结构性不可自报 + 9 例边证据重工重演 |
| canonical 保留键推断 | 条件触发（dict 缺 status/scope 且三保留键齐全） | grade_verdict 唯一权威复算 + 旧队列对账 | 存储 empirically_confirmed 永不可机械复算（契约互斥） |

## 版本链 v3.20

- workflow_export.py:22 TOOLING_VERSION → "3.20"
- SKILL.md v3.20 增量段 + 数据模型速查 candidates 补 `guard_pass_subsets[]?`/`premises_verified[]?`
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、
  test_v39.py:266、test_v314.py:219、test_v315.py:253、test_v316.py:120、
  test_v317.py:347、test_v318.py:132、test_v319.py（v3.19 新守卫行）→ "3.20"（P4 逐处实测行号核对）
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
  gen_tracking VERSIONS 登记

## 开发序列

- **C0**（本文档集）
- **P1 机械**：D-2（drift_summary）+ D-3（lessons_recorder 方向对）+
  D-4/D-5 collect 条件校验 warn + 白名单落盘
- **P2 结构**：VERDICT_SCHEMA 两个 optional 属性
- **P3 内容**：D-1（输出格式节）+ D-4 步骤 4 义务条文 + D-5 步骤 0 结构化输出说明
- **P4 文档+版本链**：SKILL.md 增量段/数据模型速查 + TOOLING/守卫/tracking/test_v320

## 测试守卫约束

- 必须保持绿：全量基线（当前 408+test_v319 8 用例）、test_evidence_ledger.py
  （门禁名不增）、test_doc_lint.py（资产计数零变化——本轮不新增计数资产）
- 新增 tests/test_v320.py（13 用例）：D-1 三值枚举+口径注记存在 /
  D-2 drift_summary 计数分类正确 / D-3 detail 含方向对 / D-4 义务条文+字段
  条件校验 warn 正反分支（死代码豁免零 warn；REACHABLE 零 warn）/
  D-5 同形态正反分支 / schema optional 不在 required / 白名单落盘 /
  D-6 canonical 推断正反分支（三键齐全→empirically_confirmed+提示；
  键不全→不升级） / TOOLING 3.20 / 反面分支（零改写：grade_self_reported
  保留原值、evidence_grade 不因自报值回写）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck /root/WebKit
bash install.sh
```

## 边界声明

- **不做**：新门禁/新强制义务/新阶段/自动改写/根因臆测（drift 只报方向对，
  不猜 edge_backfill vs self_underreport）；D-4/D-5 的 warn 不阻断落盘；
  §一补 7/8/9 三条排队 v3.21+（本版不实现）。
- **注**：D-6 为复跑对账阶段新取证（设计件原边界声明"evidence_ledger 不动"
  被对账结果推翻——存储分级不可复算是机械权威本身的缺陷，修复属本版 S1
  双轨校准的机械侧，已同步修订 SYSTEM_DESIGN 第 4 条）。
