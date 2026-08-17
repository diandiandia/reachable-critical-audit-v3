# Reachable Critical Audit v3.1 — 软件开发需求（Software Requirements）

> **文档性质**：从 `SW_DESIGN_V3_1.md` 导出的软件级开发需求（v3.1 增量）。
> 每条附"满足"列追溯系统需求（REQ-V3.1），状态 ∈ 未开发/开发中/已完成。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.1 段）。**日期**：2026-08-17

## M1+ surface_mapper.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-001 | 实现 `size_tier(project_root)`：源码文件计数 → small/medium/large 三档（agent 数/时限/落盘间隔/分域方案） | REQ-V3.1-026 | 已完成 | sinatra→small 档、actix→medium、wordpress→large 分级正确（实测通过） |
| SWR-V3.1-002 | 实现 `repair_surfaces()`：±2 主窗口 → 首行键全文件匹配（±80 语义）→ suggested_line 写回 + 行号修正 | REQ-V3.1-022 | 已完成 | 漂移样例自动修复（测试通过） |
| SWR-V3.1-003 | repair 零命中标记 `paraphrased=true`；幂等契约（已修复 entry 不重标） | REQ-V3.1-023/024 | 已完成 | 臆造 snippet 被标记；二次 repair 零改动（测试通过） |
| SWR-V3.1-004 | 实现 `_classify_project_kind()`：framework/library/infra/app | REQ-V3.1-010 | 已完成 | sinatra/actix→framework、lighttpd→infra（实测通过） |
| SWR-V3.1-005 | validate 首行键 fallback 匹配 + paraphrased 标记（与 repair 共用逻辑） | REQ-V3.1-021/023 | 已完成 | 16 基线测试全绿 |
| SWR-V3.1-006 | CLI 子命令 `repair`/`tier` 走通序列化路径 | REQ-V3.1-085 | 已完成 | 命令可运行 |

## M4+ evidence_ledger.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-010 | 实现 `load_lenient()` + `_fix_escapes_single_pass()`：单遍转义修复，幂等 | REQ-V3.1-081 | 已完成 | §3.1-3.3 场景修复 + 幂等断言（测试通过） |
| SWR-V3.1-011 | 实现 `extract_empirical_marker()`：实证标记自动提取，等级升级需 confirmed 状态 | REQ-V3.1-044/091 | 已完成 | 标记提取 + 不自动升 grade（测试通过） |
| SWR-V3.1-012 | 实现 `consistency_check()`：同 (source_file, sink_type) 家族 verdict 可比性断言 | REQ-V3.1-052 | 已完成 | 无解释不对称被检出（测试通过） |
| SWR-V3.1-013 | 实现 `check_correction_schema()`：降级必落盘 correction_record；precedent_ids 存在性校验 | REQ-V3.1-053 | 已完成 | CLI consistency 可用 |
| SWR-V3.1-014 | grade_verdict 升级条件收紧（empirical.status ∈ confirmed 集） | REQ-V3.1-045 | 已完成 | marker_found_unverified 不升 grade |
| SWR-V3.1-015 | assert_ledger 新增 gate empirical_required_r4（R4 findings 同受实证类门禁） | REQ-V3.1-090 | 已完成 | R4 未实证 oom 类 finding 违规可检出 |
| SWR-V3.1-016 | `assert`/`grade`/`check`/`consistency` CLI 全走 load_lenient | REQ-V3.1-081 | 已完成 | 非法转义文件可加载 |

## M10 checklist_binder.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-020 | 实现 `bind()`：结构化 binding（cwe 并集/keywords 备选拆分/verdict_context/applies_to_phase）+ 字符串兼容 | REQ-V3.1-041 | 已完成 | 13/13 绑定矩阵测试全 PASS |
| SWR-V3.1-021 | 实现 `bind_all()`：checklist_ids 写回候选（不覆盖已有） | REQ-V3.1-041 | 已完成 | 全队列绑定可运行 |
| SWR-V3.1-022 | 实现 `h7_template_bind()` | REQ-V3.1-060 | 已完成 | 返回三清单固定集 |
| SWR-V3.1-023 | checklist_library.json 结构化 binding 重构（19 条全 dict 形态） | REQ-V3.1-041 | 已完成 | schema 校验通过 |

## M11 precedent_library.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-030 | 实现 `match()`：按 cwe 家族/summary 关键词/claim_type 检索先例（返回 criterion + counterexample） | REQ-V3.1-006 | 已完成 | Host 采信族候选命中 HOST-FAMILY/VICTIM-TRIGGER |
| SWR-V3.1-031 | 实现 `self_refutation_hints()`：匹配先例 → ≤2 条证伪论据模板化 | REQ-V3.1-006/043 | 已完成 | 三层默认候选产出 gate 论据 |
| SWR-V3.1-032 | 实现 `record_application()`：审计后回填 applications（幂等） | REQ-V3.1-007 | 已完成 | 回填不重复 |
| SWR-V3.1-033 | 实现 `add_precedent()`：schema 校验后追加新先例 | REQ-V3.1-007 | 已完成 | 非法先例拒收 |

## W1+ workflow_export.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-040 | VERIFY/REFUTATION 脚本 args 缺失防御（resume 契约） | REQ-V3.1-055 | 已完成 | 缺 args 返回 error 不崩溃 |
| SWR-V3.1-041 | 实现 `lint_script()`：顶层 const 模板 `${}` 静态检查 | REQ-V3.1-080 | 已完成 | §17.2 坏脚本被检出（测试通过） |
| SWR-V3.1-042 | refute_prompt 工具箱注入（interval/parser/proxy 三类） | REQ-V3.1-050 | 已完成 | 三类声称各有工具箱提示（测试通过） |
| SWR-V3.1-043 | REFUTATION_SCHEMA 增加 strengthened/attribution_correction/note | REQ-V3.1-051 | 已完成 | 三字段进入 decisions 聚合 |
| SWR-V3.1-044 | verify payload 构建时注入绑定清单步骤（checklist_binder.bind） | REQ-V3.1-042 | 已完成 | 生成的 prompt 含清单执行记录要求 |
| SWR-V3.1-045 | verify payload 构建时注入自证伪提示（precedent.self_refutation_hints） | REQ-V3.1-043 | 已完成 | 生成的 prompt 含自证伪段 |
| SWR-V3.1-046 | next_step 规范条款（整读整传/resume 一致/result\|value 双字段/半程作废） | REQ-V3.1-082/083/056 | 已完成 | next_step 文本含条款 |
| SWR-V3.1-047 | refutation pool 出队排除已复核候选 | REQ-V3.1-084 | 已完成 | v3 已实现，回归保持 |

## M2+/M3+ signature_library 三层

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-050 | signature_library.json 增加 tier（L1/L2/L3）+ runtime_prereq 字段；L1 通用危险词标注 | REQ-V3.1-004 | 已完成 | 库含 tier 字段 |
| SWR-V3.1-051 | signature_matcher 消费 tier：L1 命中不生成假设（仅阅读提示） | REQ-V3.1-004 | 已完成 | L1 命中零假设 |
| SWR-V3.1-052 | 贡献度统计：hypothesis.sources 回填 + 连续 2 批次 <10% 签名退役入 retired 区 | REQ-V3.1-005 | 已完成 | 退役判定脚本化 |
| SWR-V3.1-053 | L2 语言词族首版回填（PowerShell/Shell/C#/Python/TS/Kotlin 战役词族） | REQ-V3.1-004 | 已完成 | 词族条目含 known_instances |

## M5+ harness_runner.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-060 | 实现 `load_manual(lang)`：手册要点注入实证任务书 | REQ-V3.1-070/013 | 已完成 | 任务书含语言陷阱要点 |
| SWR-V3.1-061 | 实现 `check_scope()`：scope 必填 + 机制级不得升 empirically_confirmed | REQ-V3.1-045 | 已完成 | 违规可检出 |
| SWR-V3.1-062 | 实现 `env_trap_checklist(lang)`：环境陷阱自检清单 | REQ-V3.1-072 | 已完成 | 自检清单按语言输出 |
| SWR-V3.1-063 | 实现 `contrast_matrix_prompt()`：对照矩阵模板 | REQ-V3.1-073 | 已完成 | 模板可生成 |
| SWR-V3.1-064 | 实现 `source_fact_rule()`：源事实级降级（blocker 记录 + 哨兵值/算术类豁免） | REQ-V3.1-074 | 已完成 | 阻断记录强制 |

## M12 r2_guard.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-070 | 实现 `validate_hypothesis()`：surface_ids 强制数组 + 存在性校验 | REQ-V3.1-030 | 已完成 | 单值/缺失拒收 |
| SWR-V3.1-071 | 实现 `anchor_check()`：锚点行 doc block/注释拦截 | REQ-V3.1-031 | 已完成 | 注释锚点被标记 |
| SWR-V3.1-072 | 实现 `audit_filter_drops()`：keep/drop 落盘（dropped_by+reason） | REQ-V3.1-033 | 已完成 | drop 全量可追溯 |

## M9+ 任务书模板与 R0

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-080 | verifier_edge_proof.md v3.1（步骤 0/清单执行记录/自证伪段/实证白名单/范围纪律） | REQ-V3.1-040/044/045 | 已完成 | 模板含五要素 |
| SWR-V3.1-081 | biz_hypothesis.md v3.1：tracked_surfaces 强制 + r3_link + H7 默认值全表模板 | REQ-V3.1-060/062/063 | 已完成 | 模板含三要素 |
| SWR-V3.1-082 | hypothesis_filter.md v3.1：surface_ids 数组 + sources + boundary-confirmation 归类 | REQ-V3.1-030/032 | 已完成 | 模板含三要素 |
| SWR-V3.1-083 | R0 smoke 门禁条件修正（hit_rate<1.0 AND testable>0 才阻止） | REQ-V3.1-012 | 已完成 | 全 skipped 放行 |
| SWR-V3.1-084 | SKILL.md 报告条款：NEEDS_REVIEW↔R4 映射表 + 前提逐条列出 | REQ-V3.1-092/093 | 已完成 | SKILL.md v3.1 增量段含条款 |

## 资产数据（Phase 3.1.1 产物）

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.1-090 | precedent_library.json：20 条先例（criterion/counterexample/applicability_scope 齐备） | REQ-V3.1-001/002 | 已完成 | schema 校验 + 三字段齐备 |
| SWR-V3.1-091 | checklist_library.json：19 条清单（结构化 binding） | REQ-V3.1-001/041 | 已完成 | 结构化 binding 齐备 |
| SWR-V3.1-092 | harness_manuals × 15（六节结构，事实带 lesson 出处） | REQ-V3.1-070 | 已完成 | 15 文件齐备 |

## 统计

- 总计 49 条：已完成 49 / 未开发 0 / 开发中 0（全部开发完成, 2026-08-17）
- 剩余验证义务：Phase 3.1.3 三项目复跑验收（REQ-V3.1-100/101）
