# SOFTWARE_DESIGN_V3_12 — 软件方案（v3.12 状态机分析能力补强）

> 对应需求文档：REQ_V3_12.md（5 条 REQ）。只增改不重写：模块改动点、数据模型变更、测试计划。
> 原则：改动最小面；旧队列零告警；新增行为全部有触发条件（cwe/关键词/信号命中）。
> 评估：BIAS_EVAL_V3_12.md（4 处历史信息带入错误 + 3 处过设计已随本方案修正）。

## 1. 模块改动点

### 1.1 `resources/issue_coverage_matrix.json`（纯数据）
- `families` 加 `STATE`（cwe [841, 696, 670]，置于 OTHER 前）；
- `rows` 加 `{"family": "STATE", "langs": {}}` 空行（置于 OTHER 行前——
  read 模式缺口扫描只遍历 rows，无行则族不可见；write 路径按 cwe 归族自动计数）。

### 1.2 `tools/batch_verify.py`（纯映射追加）
- `SEVERITY_BY_CWE`：`"high"` 集加 841/696、`"medium"` 集加 670（注释补
  STATE 族说明）。override 优先级/claim_type 回退/default medium 语义零变化。

### 1.3 `resources/checklist_library.json`（纯数据，`checklists` 数组尾插 4 条）
- **CK-STATE-TRANSITION**：CWE-841 锚定（唯一 841 锚定条目）+ 关键词
  （状态机/state machine/状态转移/state transition/非法状态/状态跃迁/会话状态/协议状态）；
  3 步（显式拒绝 vs 静默通过/守卫与状态持久化时序/外部输入驱动触发面）。
- **CK-STATE-CONFUSION**：无 CWE 锚定 + 关键词绑定（重入/reentrancy/复用/
  对象复用/双解释/状态混淆/共享状态/两路径）——避免与 TRANSITION 双锚 841
  机械共绑（BIAS_EVAL O-1）；3 步（双路径独立状态/共享面污染/复用后残留）。
- **CK-MULTISTEP-INVARIANT**：CWE-696 锚定 + 关键词（多步/multi-step/重放/
  replay/乱序/out-of-order/跳步/序对/步骤顺序/前置/invariant/不变量）；3 步
  （每步前置独立校验/重放乱序副作用/序对依赖入口重验）。
- **CK-FRAME-GATE-REENTRY**：无 CWE 锚定 + 关键词（状态机/state machine/逐帧/
  多帧/逐块/帧门禁/重入/chunked gate/frame gate/一次性检查）+ `applicability_signals.text`
  词边界门控（frame/chunk/handshake/renegotiation/transition/fsm/帧/分块/逐块/
  逐帧/多帧）；3 步（一次性门禁 vs 逐项重入路径/重入路径全枚举/状态更新先于检查）。
- 形态纪律：不带 `applications` 字段（v3.4 遗留死字段，BIAS_EVAL O-2）；
  keywords 只放 CJK 与多词 ASCII 短语（禁裸 state/frame——子串会中 statement/
  framework）；禁裸「块」（中「模块」）；词边界敏感 ASCII 术语全部走
  applicability_signals.text；source_lessons 引用实证属实的来源
  （CK-BIZ-LOGIC 步骤升级为族 / SKILL_LESSONS_Pillow 教训——BIAS_EVAL H-3 修正）。

### 1.4 `precedent_library.py` + `resources/precedent_library.json`（映射追加 + 纯数据）
- `CWE_FAMILY_MAP` 加 `("CWE-841", "CWE-696", "CWE-670"): ["PREC-STATE-GATE-REENTRY"]`；
- `KEYWORD_MAP` 加 `"状态机"` 与 `"state machine"` 双键（CJK/ASCII 候选路径；test_v321
  全先例可达断言强制双路径触达）；
- JSON `precedents` 数组尾加 PREC-STATE-GATE-REENTRY（沿用既有 6 字段 schema——
  `applications` 为 schema 字段保留，非死代码，BIAS_EVAL D-4）；5 字段机制形态
  零项目 token（项目名仅 source_lessons 追溯列）；不加 applicability_signals
  （CWE 锚点已窄，避免门控掉无帧词汇的 841 候选）。

### 1.5 `workflow_export.py`
- `TOOLING_VERSION = "3.12"`（收口 v3.11 文档声称 3.11 未落码的漂移）。

### 1.6 `SKILL.md`
- 严重度表（高/中行）补 STATE 族注记；
- 资产地图：`16 条裁决先例`→`17`、`30 条检查清单`→`34`；
- 存量漂移顺手修正：`29 条 CK-*`→`34 条 CK-*`、`25 条先例`→`17 条先例`、
  `243+ 个单测`→`300+ 个单测`（test_doc_lint 计数守卫以磁盘实况为准）；
- 文末追加「🆕 v3.12 增量」段（机制新增 4 项 + 明确不做 + 验收判据）。

### 1.7 `tools/gen_tracking.py` + `docs/design/REQUIREMENTS_TRACKING.md`
- `VERSIONS` 登记 `("V3.12", "docs/design/REQ_V3_12.md", "docs/design/SWR_V3_12.md")`
  （未来-proof，extract 仅解析表格行——V3.12 REQ/SWR 为标题形态零提取，登记无害）；
- REQUIREMENTS_TRACKING.md **手工追加** V3.12 REQ/SWR 段（表格形态）；
- ⚠️ 禁止运行 `tools/gen_tracking.py` 再生成（V3.4.4-V3.7 为手工维护段且不在
  VERSIONS——再生成会删除，实测核验）。

### 1.8 既有测试守卫更新
- `tests/test_v39.py`：`:253` `== 30`→`== 34`；`:266` TOOLING `"3.10.2"`→`"3.12"`；
  `:269` `"30 条检查清单"`→`"34 条检查清单"`。
- `tests/test_v310.py`：`:276` TOOLING `"3.10.2"`→`"3.12"`。
- 无需改动：test_doc_lint（计数从磁盘派生）、test_v321（新 PREC 入 map 即可达）、
  test_deproject_assets、test_v37_report、test_batch_verify_v3（CWE 归属零碰撞）。

## 2. 数据模型变更（向后兼容）

```
resources/issue_coverage_matrix.json:
  families:  +STATE{cwe:[841,696,670]}   (fam_map 数据驱动自动生效)
  rows:      +{"family":"STATE","langs":{}}  (缺口扫描可见性)
resources/checklist_library.json:
  checklists: +4 条 CK-STATE-* (标准 binding dict; 零 binder 代码改动)
resources/precedent_library.json:
  precedents: +PREC-STATE-GATE-REENTRY (标准 6 字段 schema)
tools/batch_verify.py:
  SEVERITY_BY_CWE: high +{841,696}, medium +{670}
precedent_library.py:
  CWE_FAMILY_MAP/KEYWORD_MAP: +3 键
队列/候选/surface schema: 零变更
```

## 3. 测试计划（tests/test_v312.py，14 用例）

| 测试 | 断言 |
|---|---|
| test_ledger_state_family_and_rows | families 含 STATE(841/696/670)；rows 含空行；`_aggregate_counts` 841→STATE 非 OTHER |
| test_ledger_gap_scan_shows_state | 缺口读含 `STATE x <lang>` 格 |
| test_severity_state_cwes | 841/696→high、670→medium；override 优先级与 claim_type 回退不变 |
| test_ck_state_bind_via_cwe | CWE-841 绑 CK-STATE-TRANSITION（唯一 841 锚定条目，不与 CONFUSION 共绑） |
| test_ck_state_co_binding_bizlogic | 状态机关键词绑 CK-STATE-TRANSITION 且 CK-BIZ-LOGIC（共绑合法） |
| test_ck_multistep_binds | CWE-696 与多步关键词双路径绑定 |
| test_ck_confusion_binds_keyword_only | 重入/双解释关键词绑 CK-STATE-CONFUSION；CWE-841 无关键词不绑 |
| test_ck_frame_gate_signal_gating | 正例（状态机逐帧帧门禁）绑定；负例（状态机重入模块化）不绑定 |
| test_no_bare_word_false_positive | framework/statement/裸 state 不误绑任何 CK-STATE-* |
| test_state_checklists_deproject | 4 条零黑名单 token、零 /root/ |
| test_precedent_state_reachable | match() CWE 元组+关键词双路径触达；self_refutation_hints 含之；5 字段去项目化 |
| test_tooling_version_and_skillmd | TOOLING=3.12；「🆕 v3.12 增量」段；34/17 计数；严重度表含 841/670 |
| test_verify_prompt_injects_state_checklist | 导出 verify 脚本含 CK-STATE-TRANSITION 段 |

（test_precedents_all_matchable 全局守卫由 test_v321 恒执行覆盖，不重复断言——
BIAS_EVAL O-3。）

## 4. 开发顺序（C0 + P14-P17 提交序列，延续 v3.11 P13 惯例）

- **C0 设计件**：REQ/SWR/SYSTEM_DESIGN/SOFTWARE_DESIGN_V3_12 + BIAS_EVAL_V3_12
- **P14 机制级**：账本 STATE 族 + SEVERITY_BY_CWE + SKILL.md 严重度表
- **P15 清单与先例**：4 条 CK + 1 条 PREC + precedent_library.py 双 map
- **P16 版本链与文档**：TOOLING_VERSION 3.12 + SKILL.md 增量段/资产地图/存量修正
  + gen_tracking 登记 + tracking 手工段 + test_v39/test_v310 守卫更新
- **P17 测试与验收**：test_v312.py（14 用例）+ 全量回归 + selfcheck + 账本干跑 + install

## 5. 验证

```bash
python3 -m pytest tests/ -q            # 301 基线 + test_v312 全绿
python3 signature_lib.py selfcheck /root/phpseclib   # R0 自检（去项目化扫描绿）
python3 tools/batch_verify.py /root/Pillow --stage coverage-ledger   # STATE×16 缺口格
# 禁止: python3 tools/gen_tracking.py（见 §1.7）
```
