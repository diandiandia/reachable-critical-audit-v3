# SWR V3.9 — 软件需求（REQ→SWR 追踪）

> 上游：REQ_V3_9.md。每 SWR 含：实现位置 / 行为 / 错误语义 / 测试用例 id。

## tools/batch_verify.py

- **SWR-V3.9-001**（REQ-001）`_adapt_r4_finding` 扩展四类归一化，返回 flags
  含 "cwe-str"/"callchain-str"/"location->callchain"/"surfaces->tracked"。
  拆分规则：cwe 按 `CWE-\d+` 正则 + `/`、`;` 分隔；无 CWE token 时保留原文单元素。
  测试：t_v39_001。
- **SWR-V3.9-002**（REQ-002）`stage_r4_collect` 前置：`_check_r4_tracked(items, known_ids)`
  → 违规 hypothesis 列表 + 诊断；存在违规时 stdout 输出
  `{"status":"R4_TRACKED_MISSING", "violations":[...]}`、exit 1、**不写回队列**
  （硬失败原子性：部分合并禁止）。测试：t_v39_002。
- **SWR-V3.9-003**（REQ-003）`_render_appendix_a_needs_review` 过滤条件改双语义：
  `(status=="VERIFIED" and verdict=="NEEDS_REVIEW") or status=="NEEDS_REVIEW"`。
  测试：t_v39_003。
- **SWR-V3.9-004**（REQ-004）`_render_appendix_b_process` B.2：inventory 行 lang 与
  surface.lang 双侧经 `_norm_lang` 归一后计数；`_norm_lang` 对 ".py"/"py" 均映射
  "python"（现实现已 lstrip(".")，补测试锁定契约）。测试：t_v39_004。
- **SWR-V3.9-005**（REQ-005）`_render_problem_list` R4 行位置列：
  `_r4_location(fi)` = call_chain[0]（字符串直接取）→ location[0]（dict 取 file:line）
  → 皆缺 "-"；`_render_problem_details` R4 段同步渲染。测试：t_v39_005。
- **SWR-V3.9-006**（REQ-006）`_tracked_ids` 改源：优先读
  `.audit_results/r2_filter_result.json`（keep/drop/boundary_confirmations 三组
  surface_ids；缺失字段经 hypotheses.json 反查补齐——SWR-V3.4.6-002），
  hypotheses.json 仅作无 filter 结果时兜底。新 `stage_tracked_ids(project_root)`：
  输出 {status:"TRACKED_IDS", total, tracked, missing[]}，写 `_tracked_ids.json`，
  覆盖率 <100% 时 exit 1（供脚本链使用，主代理可决定继续）。CLI 注册
  `elif stage == "tracked-ids"`。测试：t_v39_006。
- **SWR-V3.9-007**（REQ-007）`stage_workflow_script`：`payload_key`/`payload`
  存在时落盘 `.audit_results/{mode}_payload.json`（utf-8，ensure_ascii=False），
  stderr 打印写入状态；result["payload_file"] 与 next_step 文本更新。
  测试：t_v39_007。

## evidence_ledger.py

- **SWR-V3.9-008**（REQ-010）`assert_ledger(..., require_r4_independent=True)`：
  在 ③b 块后新增 ③d 块——confirmed 假说 findings 满足
  `severity in {"high","medium","critical"}` 且 empirical_result 前缀 CONFIRMED
  且无 independent_review（dict，by/method/artifacts 任一非空）且 r3_link 为空
  → violations.append({"gate":"r4_independent_review", hypothesis, finding})。
  豁免分支（require_r4_independent=False）产出 warn 注记（同 ③c 豁免形态）。
  测试：t_v39_008。
- **SWR-V3.9-009**（REQ-010）`_gates_for_report` gate_rows 增
  ("r4_independent_review", "③d R4 confirmed 独立复核")；问题详情 R4 段渲染
  independent_review（{by} {method} artifacts={artifacts}）。测试：t_v39_009。

## 提示资产与文档

- **SWR-V3.9-010**（REQ-008）`task_templates/surface_map_domain.md` 强制要求段
  新增双向核实条款（机制形态措辞，含"判缺检查前须两侧 Read 并各引证据行"）。
  测试：t_v39_010（模板含条款、去项目化扫描零命中）。
- **SWR-V3.9-011**（REQ-009）`resources/checklist_library.json` 增
  CK-POSTOP-INVARIANT（id/name/family="memory-safety"/binding.cwe=[787,125]/
  binding.keywords 中英双形态/applies_to=[verifier,refuter]/steps 3 条机制形态）。
  `checklist_binder.py` 绑定逻辑零改动（信号驱动自动生效）。
  测试：t_v39_011（库长度 30、条目可被 binder 命中、无项目 token）。
- **SWR-V3.9-012**（REQ-011）SKILL.md:346 repair 行加"（v3.5.2 已裁除…）"注记；
  SKILL.md 顶部增 v3.9 增量段（本文件摘要 + 文档指针）；
  `workflow_export.py` TOOLING_VERSION "3.7"→"3.9"。
  测试：t_v39_012（TOOLING_VERSION=="3.9"；SKILL.md 含注记与 v3.9 段）。
- **SWR-V3.9-013**（REQ-012）`/root/.claude/skills/cve-ghsa-draft/tools/check_no_cjk.py`：
  参数 <file> [--max N] [--ignore-blocks name...]；统计 CJK 字符并逐行报告；
  超阈值 exit 1。cve-ghsa-draft/SKILL.md 自查清单引用该命令。
  测试：t_v39_013（含 CJK 文件 exit 1；纯英文 exit 0；ignore-blocks 生效）。
