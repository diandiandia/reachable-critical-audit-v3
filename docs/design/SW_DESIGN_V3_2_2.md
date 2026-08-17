# Reachable Critical Audit v3.2.2 — 软件设计（组件级）

> 从 `SYSTEM_DESIGN_V3_2_2.md` 导出的组件修改设计。日期：2026-08-17
> 最高判据：SKILL.md「第一原则：通用型 Skill」——本版全部组件修改都必须通过
> 自检四问（去项目名 / 语言无关或按 lang 分派 / 无具体项目路径 / 新项目验收）。

## 组件影响清单

| 组件 | 修改点 |
|---|---|
| M1 signature_lib.py | ①数据模型 v2: validate() 增加 L2 lang 必填（VALID_LANGS）、cwe/semantic 非空、去项目化扫描（DEPROJECT_BLACKLIST）；known_instances 非空强制退役 ②smoke_test 锚点源改为 tests/fixtures/known_instances.json，非 fixture 仓库输出完整性自检（integrity_selfcheck）③CLI 新增 selfcheck 子命令（R0 单一事实源） |
| M2 resources/signature_library.json | 13 签名重构：全部加 lang（L3=any，L2=具体语言）；污染 grep 清理（PY-PICKLE 拆分/TS 去 multer/KT 去 Ktor 配置名/AUTHZ-BOUND 去 lighttpd 变量/HEADER-INJ 去 CleanXSS）；known_instances 移入 tests/fixtures |
| M3 signature_matcher.py | ①match(): site 过滤 tests/test 路径段 ②gen(): L1/L2 命中全部降为 reading_hints（仅 L3 生成假设） |
| M4 surface_mapper.py | ①merge 默认落盘 + 产出 mirror_pairs（无序对去重）②tier 语言混合度只计 server-side ③language_inventory 运行时占比修正（>90% 非运行时目录→build-config）④新增 scope snapshot/diff 子命令 |
| M5 r2_guard.py | ①drops 双键归一（drop/dropped）②anchor 兼容 hit_sites 数组形态 + anchor_check_all 批量检查 ③drop 数据模型支持 scope_dependent 字段 |
| M6 batch_verify.py | ①collect: verdict≠REACHABLE→claim_type=null（claim_nulled_by 标记）②r4 id 归一化 _norm_hypothesis_id ③IMPORTABILITY_STEPS 按 lang 分派步骤 0.5（python/c/cpp/go/rust/java/default）④--from-journal 桥接（_extract_journal_verdicts）⑤workflow-script 阶段入队前 scope diff 输出 scope_changed |
| M7 evidence_ledger.py | ①门禁⑦ tracked_ids + mirror_pairs 镜像自动传播 ②r4_feedback resolved 标记位（r4_feedback_resolved 队列字段） |
| M8 lessons_recorder.py | resurrection_review lenient 加载（str→dict 包装；list→空） |
| M9 harness_runner.py | parser_fuzz 模板注册（langs: c/cpp）；覆盖矩阵加载 |
| M10 resources/harness_coverage_matrix.json | 新增（claim × 语言） |
| M11 tools/target_kind.py | listener/startup-chain 信号路径分域（nonproduct/libdir/examples/product 四类） |
| M12 resources/precedent_library.json / checklist_library.json | 运行时字段（criterion/counterexample/applicability_scope/steps/binding）脱敏，追溯字段（applications/source_lessons）保留 |
| M13 workflow_export.py | VERDICT_SCHEMA claim_type 增加 enum（含 null）+ 语义注释 |
| M14 task_templates/hypothesis_filter.md | drop 条目支持 scope_dependent 标记 + 说明段 |
| M15 SKILL.md | R0 增加 1.5 scope 快照步；R0 自检命令收敛为 selfcheck；门禁⑦ coverage_bridge 正式化；R3.5-N 落盘契约 |
| M16 tests/ | test_doc_lint.py（新增）+ test_signature_lib 契约更新（lang 必填/去项目化/完整性自检/fixture 锚点）+ tests/fixtures/known_instances.json（回归锚点库） |

## 数据模型变更

1. **签名 v2**：`lang` 新增（L2 必填具体语言、L3 缺省 "any"）；`known_instances` 从运行时资产退役（回归锚点 → tests/fixtures/known_instances.json `{sig_id, project, file, line, confirmed}`）
2. **input_surface.json v3.0+**：merge 产出新增 `mirror_pairs: [[surface_a, surface_b], ...]`
3. **verify_queue** 新增字段：`scope_advice`（batch_verify 入队输出）、`r4_feedback_resolved: [{candidate, key, resolved_by, note}]`、候选级 `claim_nulled_by`、`resurrection_review` 契约固定为 dict{revived, outcome}
4. **scope_snapshot.json**（.audit_results/）：`{schema_version, submodules{name:sha}, key_dirs{path:materialized}}`

## 兼容性

- smoke_test 返回三元组不变（results, hit_rate, testable）
- assert_ledger 计数型 surface_data 调用（无 tracked_ids）保持原语义（无镜像传播）
- 旧队列（无 lang 字段候选）在 collect 时按扩展名推断 language，行为不变
- selfcheck 对 fixture 仓库（锚点可定位）保持 anchor recall hit_rate 语义
