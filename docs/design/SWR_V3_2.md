# Reachable Critical Audit v3.2 — 软件开发需求（Software Requirements）

> **文档性质**：从 `SW_DESIGN_V3_2.md` 导出的软件级开发需求（v3.2 增量）。
> 每条附"满足"列追溯系统需求（REQ-V3.2），状态 ∈ 未开发/开发中/已完成。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.2 段）。**日期**：2026-08-17

## M1+ surface_mapper.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-010 | `build_architecture_context` 输出 language_inventory（{lang, file_count, component_hint}，绑定层/核心/前端/脚本启发式） | REQ-V3.2-001 | 未开发 | 混合 fixture 检出 ≥2 语言且组件提示合理 |
| SWR-V3.2-011 | `gen_surface_tasks` 新增 boundary 第五域（boundary_kind 枚举 + 调用方向 + 语言对 schema） | REQ-V3.2-010 | 未开发 | 任务书含 boundary 域且 schema 完整 |
| SWR-V3.2-012 | 4 域任务书架构背景按语言分片（每语言组件摘要段） | REQ-V3.2-003 | 未开发 | 任务书含分片段 |
| SWR-V3.2-013 | normalize/validate 增加 surface/entry_point lang 字段（默认继承主语言；boundary surface 必填 boundary_kind） | REQ-V3.2-002 | 未开发 | 校验器拒收缺 boundary_kind 的 boundary surface |
| SWR-V3.2-014 | size_tier 混合项目保底（languages>2 → large 档） | REQ-V3.2-001 | 未开发 | 3 语言 fixture 判 large |

## M3+ signature_matcher / M10 checklist_binder

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-020 | L2 词族按 surface.lang 过滤（词族表增加 lang 字段） | REQ-V3.2-004 | 未开发 | C 词族命中不出现在 Rust surface |
| SWR-V3.2-021 | Hit 输出带 lang | REQ-V3.2-002 | 未开发 | hits.json 含 lang |
| SWR-V3.2-022 | checklist_library 增加 CK-FFI-BOUNDARY（第 21 条）并验证绑定矩阵命中 ffi/ctypes 类候选 | REQ-V3.2-012 | 未开发 | 绑定测试通过 |

## M11 precedent_library / M12 r2_guard

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-030 | precedent_library 增加 PREC-MULTI-LANG-001；match 增加 lang 维度 | REQ-V3.2-013 | 未开发 | 多语言候选匹配到该先例 |
| SWR-V3.2-031 | r2_guard 假设 schema 增加 lang 字段校验 | REQ-V3.2-002 | 未开发 | 缺 lang 假设告警 |

## W1+ workflow_export.py（R3.5-N 复活攻击）

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-040 | 实现 `resurrect_pool`：声称类 UNREACHABLE 全量 + 其他 20%（最少 2，上限 8）；排除已复核 | REQ-V3.2-020 | 未开发 | 抽样规则单测通过 |
| SWR-V3.2-041 | 实现 `resurrect_prompt`（尽力复活任务书：枚举阻断缺口/错误前提/三层语义误用） | REQ-V3.2-024 | 未开发 | 任务书含复活者视角条款 |
| SWR-V3.2-042 | 新增 refutation-resurrect workflow 模式（N=1、RESURRECT_SCHEMA、lint 干净） | REQ-V3.2-022 | 未开发 | 模式可导出且 lint 通过 |
| SWR-V3.2-043 | 复活裁决字段：{id, revived, reason, gap} 落盘 | REQ-V3.2-021 | 未开发 | decisions 含 gap 字段 |

## M4+ evidence_ledger.py

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-050 | consistency_check 分组键增加 lang（跨语言组不触发告警） | REQ-V3.2-013 | 未开发 | 跨语言同 sink 形态零告警；同 lang 组仍告警 |
| SWR-V3.2-051 | assert_ledger 新增 resurrection_required 门禁（声称类 UNREACHABLE 无 resurrection_review → 违规） | REQ-V3.2-023 | 未开发 | 缺记录候选被拦截 |

## M5+ harness_runner / 资产

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-060 | harness_manuals 新增 mixed_build.md（组件级构建矩阵 + FFI harness 模板 + 跨语言编排） | REQ-V3.2-005 | 未开发 | 手册含三要素 |
| SWR-V3.2-061 | harness_runner 混合项目多组件构建提示（按候选.lang 组装构建矩阵） | REQ-V3.2-005 | 未开发 | 混合候选任务书含两侧组件构建命令 |

## 流程条款（SKILL.md 承载）

| 编号 | 需求 | 满足 | 状态 | 验收判据 |
|---|---|---|---|---|
| SWR-V3.2-070 | SKILL.md 增加分级机械复核条款（collect 后强制 grade_verdict 重算 + verifier 任务书加注"分级是证据的机械函数"） | REQ-V3.2-030 | 未开发 | 条款入 SKILL；verifier 模板含加注 |
| SWR-V3.2-071 | SKILL.md 增加 R3.5-N 编排条款（时机/抽样/复活回 R3 重验路径） | REQ-V3.2-021 | 未开发 | 条款入 SKILL |
| SWR-V3.2-072 | SKILL.md 增加报告语言覆盖表 + FFI 边界表条款 | REQ-V3.2-040/041 | 未开发 | 条款入 SKILL |

## 统计

- 总计 18 条：已完成 0 / 未开发 18 / 开发中 0（2026-08-17，v3.2 设计刚完成）
- 注：REQ-V3.2-030 的 grade_verdict 重算**函数**在 v3.1 已实现（313 验收中实际使用），
  本表 SWR-V3.2-070 指其**流程条款化**，故仍标未开发
- 开发依赖序：M1（inventory/boundary）→ 资产（CK-FFI/PREC）→ M3/M11 → W1 复活模式 →
  M4 门禁 → M5/harness → 流程条款 → Phase 3.2.3 验收
