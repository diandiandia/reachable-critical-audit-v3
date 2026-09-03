# SOFTWARE DESIGN V3.20 — 函数级设计与分层序列（2026-09-03）

## P1 机械（先做——独立可测，零文本耦合）

### 1. lessons_recorder.py 方向对（D-3，最小改动）

`collect_issues`（或等价 issue 生成处，:62-64）：
```python
if c.get("grade_recomputed_by"):
    sr = c.get("grade_self_reported", "?")
    eg = c.get("evidence_grade", "?")
    issues.append({"stage": "R3", "kind": "grade_recomputed",
                   "detail": f"{cid}: 机械分级重算 {sr}->{eg} ({c['grade_recomputed_by'][:80]})"})
```
无条件渲染（两字段均缺失时 "?->?" 无害——该分支仅在 grade_recomputed_by
存在时触发，而该标记只在重算差异时写入，故必有值）。

### 2. stage_collect drift_summary + 条件 warn（D-2/D-4/D-5）

在 stage_collect（tools/batch_verify.py:449-571）中：

a) 循环外初始化：
```python
drift_pairs = {}
drift_promoted = drift_demoted = 0
warnings = []
```
b) 重算块（:519-549）内，`_g != entry["grade_self_reported"]` 分支：
```python
_pair = f"{entry['grade_self_reported']}->{_g}"
drift_pairs[_pair] = drift_pairs.get(_pair, 0) + 1
if _GRADE_RANK.get(_g, 0) > _GRADE_RANK.get(entry["grade_self_reported"], 0):
    drift_promoted += 1
else:
    drift_demoted += 1
```
（模块级常量 `_GRADE_RANK = {"static_only": 0, "edge_proven": 1, "empirically_confirmed": 2}`）
c) 条件校验（放在字段落盘区之后，只 warn 不改 verdict）：
```python
if v.get("verdict") == "UNREACHABLE" and v.get("blocking_point") != "no production callers":
    if not v.get("guard_pass_subsets"):
        warnings.append(f"{cand_id}: UNREACHABLE 阻断论证未附 guard_pass_subsets 枚举 (SWR-V3.20-004)")
    if not v.get("premises_verified"):
        warnings.append(f"{cand_id}: UNREACHABLE 前提断裂判定未附 premises_verified (SWR-V3.20-005)")
if v.get("guard_pass_subsets"):
    entry["guard_pass_subsets"] = v["guard_pass_subsets"]
if v.get("premises_verified"):
    entry["premises_verified"] = v["premises_verified"]
```
d) result（:563-571）增：
```python
"drift_summary": {"recomputed": drift_promoted + drift_demoted,
                  "promoted": drift_promoted, "demoted": drift_demoted,
                  "pairs": drift_pairs},
"warnings": warnings,
```
（warnings 与既有 errors 分离：errors 跳过条目，warnings 不跳过。）

## P2 结构（次做——schema 先行，collect 校验才可能有输入）

workflow_export.py VERDICT_SCHEMA（:39-50）properties 增两个 optional：
```python
"guard_pass_subsets": {"type": "array"},
"premises_verified": {"type": "array"},
```
required 列表不动。VERDICT_SCHEMA 由 workflow-script 阶段 JSON 序列化进
workflow JS——两侧同源，零双实现漂移。

## P3 内容（三做——文本依赖 schema/collect 已就位后才有完整语境）

`_build_prompt`（tools/batch_verify.py）三处：

1. 输出格式节 evidence_grade 行 → 三值枚举；规则 1 增口径注记
   （SWR-V3.20-001 文案，两句以内）。
2. 步骤 4（:2886-2895）增守卫通过子集义务条文（SWR-V3.20-004 文案）。
3. 步骤 0 尾增 premises_verified 结构化输出说明（SWR-V3.20-005 文案）。
4. 输出格式节 JSON 增两字段示例行（条件触发注释）。

## P4 版本链（四做）

1. workflow_export.py:22 TOOLING_VERSION "3.19" → "3.20"。
2. 版本守卫测试行 ×10（test_v310:276 / test_v312:180 / test_v313:191 /
   test_v39:266 / test_v314:219 / test_v315:253 / test_v316:120 /
   test_v317:347 / test_v318:132 / test_v319 守卫行）→ "3.20"（逐处实测行号）。
3. SKILL.md v3.20 增量段（列 SWR 号+验收判据）+ 数据模型速查 candidates
   增两字段 + R3 输出契约一句。
4. REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
   gen_tracking.py VERSIONS 登记。

## tests/test_v320.py（约 10 用例，随各层落地）

- D-1: `_build_prompt` 产物含三值枚举 / 含口径注记（用最小 ctx 构造调用）。
- D-2: 临时项目队列跑 stage_collect：满边→edge_proven 漂移对计数；
   empirical dict→empirically_confirmed 漂移对计数；零漂移→零计数。
- D-3: recorder 对漂移候选产出含 "static_only->edge_proven" detail。
- D-4: 任务书含义务条文；schema optional 且不在 required；
  UNREACHABLE+非豁免无字段→warnings 非空；no production callers→零 warn；
  REACHABLE→零 warn；字段非空→entry 落盘。
- D-5: 任务书含步骤 0 说明；同 D-4 正反分支；premises_verified 落盘。
- 反面分支（全版通用）：warn 不改写任何字段/不改变 verdict；
  grade_self_reported 保留原值。
- P4: TOOLING=="3.20"。
