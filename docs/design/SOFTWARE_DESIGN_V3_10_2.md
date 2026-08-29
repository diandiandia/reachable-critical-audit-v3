# SOFTWARE_DESIGN_V3_10_2 — 软件方案（v3.10.2 缺陷修复）

> 对应需求文档：REQ_V3_10_2.md（13 条 REQ）。本方案只增改不重写：模块改动点、数据模型变更、测试计划三节。
> 原则：改动最小面；旧队列/旧队列产物零告警；新增行为全部有开关或缺省兼容。

## 1. 模块改动点

### 1.1 `evidence_ledger.py`（Q-A/Q-E/Q-G/Q-I）
- `assert_ledger`：
  - gate ③ 分支输出增加 fidelity 提示（`fidelity_hint` 字段：等价复现候选列表，不改变 PASS/FAIL 判定）。
  - 新增 warn 级断言 `adjudication_unverified`：存在 demote correction_record 且无 `adjudication_verification` 字段 → 输出提示（不阻断）。
  - 新增 warn 级断言 `strengthen_unverified`：REACHABLE 候选存在 refutation.strengthened/attribution_correction 且无 `strengthen_verified_by` → 输出提示（不阻断）。
  - `empirical_required_r4` 分支不变（判据不因 fidelity 改变）。
- `commit`：correction 条目透传新增 `adjudication_verification` 键（无 schema 限制，只增不改）。

### 1.2 `tools/batch_verify.py`（Q-C/Q-D/Q-H/Q-K）
- `stage_r4_collect`：finding/假说级 tracked 读取兼容 `surfaces` 别名（`tracked_surfaces = tracked_surfaces or surfaces`，幂等）；空 findings 假说的「全量扫掠」tracked 不再拒收（移除 R4_TRACKED_MISSING 对空面形态的拦截，保留对其他缺口的拦截）。
- `stage_report`：渲染前检查报告中「三、修复建议与结论」段是否已含主代理内容（非占位符），已含 → 拒绝重跑（exit 1 + stderr 提示 `--force`）；`--force` 参数放行并输出主代理段落丢失告警。
- 新子命令 `--stage reopen --id <ID>`：NEEDS_REVIEW → PENDING（保留全部历史字段），写 `reopen_reason`（必填，缺省拒绝）；重开候选 attempt 计数保留。
- `--stage workflow-script`：scope_changed 分支扩展——changed 非空时输出「受影响面重开建议」（由 scope snapshot 的 key_dirs 与 R1 面 entry_points 路径交叉生成候选面清单，建议级）；主代理裁决落盘走新 helper `write_scope_review`（append `.audit_results/scope_review.jsonl`）。
- `stage_collect`（含 r35/r35n）：journal 后验信号——同 id 多 result 且 payload hash（content 级 sha256）各异 → stderr 输出 `journal_anomaly` 告警（Q-B 后验）。
- 报告渲染：empirical 行 `fidelity=equivalent` 前缀 `等价复现:`；harness 路径非 `.audit_results/` 前缀 → 行尾 `[产物目录违规 warn]`；NEEDS_REVIEW 成因=`环境受限`+上游佐证 → 附录 A「佐证注记」列；strengthen 未签收 → 「（未复核）」标记（Q-I 渲染侧）。

### 1.3 `workflow_export.py`（Q-B）
- 导出脚本模板（VERIFY_SCRIPT/REFUTATION_SCRIPT/RESURRECT_SCRIPT/SHIPPED_CONFIG_SCRIPT）统一加入输入校验首步：契约键（`c.prompt` 或 `c.taskFile`）缺失/空 → 不调 `agent()`，该候选返回模式对应的错误结构（verify: `{id, verdict:"NEEDS_REVIEW", evidence:"workflow input missing: <key>"}`；refutation: `{id, refuted:false, reason:"input missing"}`；resurrect: `{id, revived:false, outcome:"input missing"}`）。
- TOOLING_VERSION → `3.10.2`。

### 1.4 `task_templates/`（Q-F/Q-J/Q-I）
- `surface_map_domain.md` / `hypothesis_filter.md` / `biz_hypothesis.md`：信任边界几何段增加「平台信任模型清单」绑定条款——按目标平台（由 R1 测绘平台信号判定）引用 checklist_library 对应清单段，判定前逐条过；无对应平台 → 条款空转。
- verifier/refuter 任务书（workflow_export 内嵌 prompt 模板）：步骤 1.5 扩展可选步「构建依赖 CVE 对账注记」（触发条件：R1 context 输出含 pinned 依赖清单）——产出 `dependency_cve_notes`，不改变 verdict。
- `biz_hypothesis.md`：NEEDS_REVIEW 成因三分指引（保守裁决/证据不足/环境受限）+ strengthen 签收注记条款。

### 1.5 `resources/checklist_library.json`（Q-F）
- 新增清单族 `platform_trust_model`：按平台维度分派（`mobile`/`desktop`/`web`/`embedded_kernel`/`server_deploy`…），条目为平台机制级描述（示例形态：同设备异主体注入面——导出组件/意图参数/跨应用调用；平台鉴权中介——系统服务绑定/用户授权；网络策略门——平台级明文/域名限制；沙箱语义——进程级资源隔离边界）。**不含任何具体项目 API 名**（去项目化扫描 0 命中验收）。
- 校验：`checklist_binder.py` 绑定逻辑按目标平台信号分派，无对应平台零注入。

### 1.6 `templates/harness/` + `harness_manuals/`（Q-M）
- parser_fuzz 模板头部加资源防护样板（按 lang 分派：进程限额/上限参数化/极值预设防护），docstring 加「复现安全性」注记。
- 语言手册（c/cpp 等对应小节）补样板代码与「无防护环境勿跑极值预设」警告。

### 1.7 `SKILL.md`（文档同步）
- v3.10.2 增量段：实证保真度三档、裁决核验义务、平台信任模型清单、NEEDS_REVIEW 成因三分、reopen 命令、报告防覆盖、补强签收、依赖对账注记、物化增量面重审、实证产物前缀 warn、防误伤样板。
- 数据模型速查表补 `empirical.fidelity`、`correction_record.adjudication_verification`、`needs_review_reason` 三档、`reopen_reason`。

## 2. 数据模型变更（向后兼容）

```
verify_queue 候选新增（全部可选，旧队列零影响）：
  empirical.fidelity          : "real_target" | "equivalent" | "mechanism"   (缺省 real_target)
  correction_record[].adjudication_verification: [{claim, verified, evidence_ref}]
  needs_review_reason         : 三档语义 (现存字符串字段, 文档规范化)
  reopen_reason               : string (reopen 时写入)
  refutation.strengthened_verified_by / attribution_correction_verified_by : "main-agent" | null
新增落盘文件：
  .audit_results/scope_review.jsonl : [{changed_dir, surfaces_reopened, decision, reason}]
报告新增渲染（不改队列）：
  实证行 fidelity 前缀 / [产物目录违规 warn] / 佐证注记列 / （未复核）标记
```

## 3. 测试计划（tests/test_v3102.py）

| 测试 | 断言 |
|---|---|
| test_fidelity_equivalent_prefix | empirical.fidelity=equivalent → 报告行首「等价复现:」；real_target/缺省无前缀 |
| test_fidelity_mechanism_no_upgrade | fidelity=mechanism + 回填 attempted → grade 维持 edge_proven（不升 empirically_confirmed） |
| test_gate3_fidelity_unchanged | equivalent 满足 gate ③（PASS 不变）+ fidelity_hint 输出等价复现候选列表 |
| test_workflow_input_fail_fast | 导出脚本 args 缺契约键 → 返回结构化错误 verdict，agent 未被调用（journal 无该 agent started 行） |
| test_journal_anomaly_detection | 构造同 id 多 result 内容各异 journal → collect 输出 journal_anomaly 告警 |
| test_r4_tracked_surfaces_alias | findings 用 `surfaces` 别名 → r4-collect 合并成功，gate ⑦ 覆盖率计齐 |
| test_r4_empty_sweep_accepted | 空 findings 假说全量扫掠 tracked → collect 不再 R4_TRACKED_MISSING |
| test_report_refuse_overwrite | 报告含主代理段落 → --stage report exit 1；--force 重生成 + 告警行 |
| test_reopen_flow | reopen → verdict=PENDING 且 correction_record/needs_review_reason 保留 + reopen_reason 必填校验 |
| test_adjudication_verification_warn | demote 无 adjudication_verification → warn 不阻断；有 → 无 warn |
| test_needs_review_three_causes | 成因=环境受限+上游佐证 → 附录 A 佐证注记列渲染 |
| test_strengthen_unverified_marker | 未签收补强渲染「（未复核）」；签收后去标记；门禁 warn 级 |
| test_scope_review_advice | scope_changed 输出受影响面重开建议；write_scope_review 落盘 append |
| test_harness_guard_sample | parser_fuzz 模板含资源防护样板（按 c 分派断言代码存在） |
| test_platform_checklist_deproject | 平台清单 JSON 去项目化扫描 0 命中；无对应平台目标零注入 |
| test_old_queue_compat | v3.10 及更早队列样本复跑：零告警零误判（fidelity 缺省等全部兼容） |

## 4. 开发顺序（P7-P9 提交序列，延续 v3.10 P1-P4 惯例）

- **P7 机械层**：evidence_ledger（fidelity/warn 断言）+ batch_verify（别名容错/防覆盖/reopen/scope 建议/后验信号/渲染四标记）+ workflow_export（fail-fast + TOOLING_VERSION）
- **P8 知识/契约层**：checklist_library 平台清单族 + checklist_binder 分派 + 三任务书绑定条款 + verifier/refuter 依赖对账可选步 + biz_hypothesis 成因三分
- **P9 文档与验收**：SKILL.md 增量段 + harness 模板防误伤样板 + 语言手册小节 + test_v3102 全绿 + 旧队列兼容 + 去项目化扫描 + 新项目验收（覆盖账本缺口格）
