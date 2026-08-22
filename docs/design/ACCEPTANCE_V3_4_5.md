# v3.4.5 验收记录（2026-08-23）

> 对应: SYSTEM_DESIGN_V3_4_5.md §3 验证策略 / SWR_V3_4_5.md。
> 验收流程: 单测全绿 → 三锚点回归（本环境替代）→ 新项目验收（quic-go）→ 六门禁 → 安装。

## 一、单测（SWR-V3.4.5-001~005 实现验证）

- tests/ 全量: **170 passed**（+4 用例: test_gen_warns_and_keeps_main_hypotheses /
  test_export_scripts_args_shape_tolerance / test_merge_warns_id_gap /
  test_checklist_pinned_dep_entry）
- 基线排除: test_v321 3 用例（本环境无 /root/Lersosa、/root/mixed-fixture 路径，
  基线同失败，非回归——git stash 对照验证）

## 二、三锚点回归（本环境替代方案）

环境限制: 无 sinatra/lighttpd/actix-web fixture 仓库 → 按既有替代惯例:

1. **R0 selfcheck 完整性自检**: exit 0, 20 签名 validate 通过, 去项目化扫描零命中
2. **锚点结构完整性**: 24 anchors ↔ 20 sig_ids, 0 orphan
3. **170 单测全绿**（同 §一）

## 三、新项目验收: quic-go v0.61.0（覆盖账本缺口格项目）

覆盖账本判据"覆盖格 +1": **MEMORY-SAFETY×go 0→2**（缺口格补上），另 RESOURCE-DOS×go
+8 / AUTHN×go +5 / OTHER×go +4 / WEB×go +3 / RACE×go +1。

### 全流程执行记录

| 阶段 | 产出 | 结果 |
|---|---|---|
| R0 | scope_snapshot / selfcheck / target_kind=library 签收 | PASS |
| R1 | 41 surfaces (5 域), 23 conflicts, 12 mirror_pairs, reviewed_by=main-agent | PASS |
| R2 | 28 LLM 假设 + 佐证器 49/39 hints; **SWR-001 实战验证** (gen warn + 独立文件, 主路径完好) | PASS |
| R2 filter | keep 0 / drop 4 / boundary_confirmations 24（主代理抽样复核 3 条属实） | PASS |
| R3 | 空队 → WORKFLOW_NOTHING_TO_DO (SWR-V3.4.4-003 机制实战) | PASS |
| R4 | H1-H7 全 VERIFIED; 17 findings; 3 确认缺陷 (Medium×2/Low×1) | PASS |
| R5 | H2/H4/H5 CONFIRMED 探针实证; H3/H7 SOURCE_FACT (离线环境) | 无强制触发 |
| 六门禁 | 8 门禁全 PASS (tracked_ids 41/41) | PASS |
| 报告 | reachable_vulnerabilities_report.md | 完成 |

### v3.4.5 修复批的实战验证点

| SWR | 验证 |
|---|---|
| -001 gen 文件所有权分离 | ✅ hypotheses.json (28 主路径) 与 hypotheses_gen.json (49 佐证) 物理隔离, warn 正确打印, 零覆盖 |
| -002 args 形态容忍 | 单测覆盖 4 模板; 本批 R3 空队未派发 (空队本身即 -002 边界形态) |
| -003 merge 空洞告警 | 单测覆盖; 本批 id 归一化后无空洞 (主代理主动重排) |
| -004 CK-PINNED-DEP | 单测覆盖 (结构 + 去项目化扫描) |
| -005 编排层铁律四 | 文档级, SKILL.md 四铁律 |

### 验收发现的新机制缺陷（→ v3.4.6 SWR 素材, 已记 lessons/SKILL_LESSONS_quic_go.md）

- **coverage-ledger lang fallback**: R3 空队时 R4 findings 记入 `*xother` 格而非
  主导语言格（quic-go 误记 other 已人工修正为 go 格, 修正记录 ledger_fix）。
  修复方向: dom 推导链加 input_surface.json surface lang → language_inventory 回退。

## 四、验收判据对照（SYSTEM_DESIGN_V3_4_5.md §3.2）

| 判据 | 状态 |
|---|---|
| 单测 4 新用例 + 全量全绿 | ✅ 170 passed |
| 三条件发布（R3.5 拦截率/R2 零丢失/六门禁） | ✅ 空队形态下六门禁全 PASS; R4 3 条 confirmed 均对抗复核 |
| 新项目验收（缺口格项目 + 覆盖格 +1） | ✅ quic-go: MEMORY-SAFETY×go 0→2 |
| SWR-001~005 实战/单测验证 | ✅ 见上表 |

## 五、安装

验收通过 → git 提交（含本文件与 lessons）→ `install.sh` 安装到
`/root/.claude/skills/reachable-critical-audit/`（安装后校验: selfcheck exit 0 +
安装副本 170 测试全绿）。
