# SOFTWARE_DESIGN_V3_11 — 软件方案（v3.11 设计缺陷修复）

> 对应需求文档：REQ_V3_11.md（7 条 REQ）。只增改不重写：模块改动点、数据模型变更、测试计划。
> 原则：改动最小面；旧队列零告警；新增行为全部有开关或缺省兼容。

## 1. 模块改动点

### 1.1 `tools/batch_verify.py`
- `_build_prompt`（verifier 任务书）：
  - 步骤 3 跨边界判定段加 attacker_tier 判定要求（四层枚举 + 填写指引 + 推导规则）；
  - 步骤 4 阻断检测清单加「运行时版本条件」项（REQ-V3.11-005 提示级条款）；
  - 步骤 0.5 构建包含性段加「模板 → 实例化产物」判定条款（REQ-V3.11-003）。
- `stage_collect`：verdict payload 落盘时从 evidence 文本推导 attacker_tier
  （verifier 未显式给出时按推导规则；结构字段名 `attacker_tier`）。
- 报告渲染（render_report_md）：
  - 问题清单行尾附 tier 标注（`[tier: remote]` 类）；
  - 附录 B 增加「审计树与部署物差异」段（读 scope_snapshot.json 的构建差异声明）。
- `stage_workflow_script`（verify/refutation/resurrect 三模式共用注入点）：
  契约库注入（与 PTM 同管线：detect_platforms → platform_api_contracts 条目拼接）。

### 1.2 `surface_mapper.py`
- `merge`：输出 `mirror_candidates` 提示（语义相似 + 跨 lang 的面组；仅提示不组族）。
- `scope snapshot`：扩展「构建差异声明」段——读构建清单（按生态分派）声明的
  依赖/生成物 vs 树内物化状态，产出差异表（空差异也落盘）。

### 1.3 `resources/checklist_library.json` + `checklist_binder.py`
- 新增 `platform_api_contracts` 清单族（条目含必填 source）；`platform_api_contracts(targets)`
  查询函数（与 platform_models 同管线）；加载时校验条目 source 非空（无来源条目
  拒收 + stderr 告警）。

### 1.4 `task_templates/`
- `surface_map_domain.md`：模板产物面指引段（REQ-V3.11-003）。
- `biz_hypothesis.md`：H4 检测要点加初始化时序子项（REQ-V3.11-006）。
- `hypothesis_filter.md`：逻辑镜像枚举条款（REQ-V3.11-007 的 R2 侧）。

### 1.5 `SKILL.md`
- v3.11 增量段：attacker_tier 四层/契约库/模板产物面/运行时版本项/H4 时序子项/
  镜像提示/差异声明；数据模型速查补 `attacker_tier`、`instantiated_artifact`、
  scope snapshot 构建差异段。

## 2. 数据模型变更（向后兼容）

```
候选新增（可选，旧队列零影响）：
  attacker_tier: "same_process" | "same_device_cross_app" | "system_broker" | "remote"
    (verifier evidence 注明 → collect 落盘; 缺省推导)
R1 surface entry_points 新增（可选）：
  instantiated_artifact: true   (模板/生成器产物面标记)
scope_snapshot.json 新增（可选段）：
  build_divergence: [{declared, materialized, kind}]  (构建差异声明)
input_surface.json merge 输出新增（可选）：
  mirror_candidates: [[surface_id, surface_id], ...]  (提示级)
checklist_library.json 新增（平级清单族）：
  platform_api_contracts: [{id, platform, api_pattern, behavior,
                            security_effect, probe, source}]
```

## 3. 测试计划（tests/test_v311.py）

| 测试 | 断言 |
|---|---|
| test_attacker_tier_enum_and_derive | 四层枚举合法值校验；缺省推导（DIRECT+host_api→same_process）；非法值回退+告警 |
| test_attacker_tier_render | 报告问题清单行含 tier 标注 |
| test_contracts_schema_source_required | 契约条目缺 source → 加载拒收+告警；首版条目全部带 source |
| test_contracts_deproject | 契约族去项目化扫描 0 命中（api_pattern 机制描述形态） |
| test_contracts_injection | verify/refutation/resurrect prompt 均含契约条目（信号驱动；零信号零注入） |
| test_template_artifact_clause | surface_map_domain 模板含模板产物面指引段 |
| test_runtime_version_clause | verifier prompt 步骤 4 含运行时版本条件项 |
| test_h4_timing_subitem | biz_hypothesis H4 检测要点含初始化时序子项；SKILL.md H4 表同步 |
| test_mirror_candidates_hint | merge 输出 mirror_candidates（构造跨 lang 语义相似面）；单语言仓库无输出 |
| test_scope_build_divergence | scope snapshot 含构建差异段（空差异也落盘）；报告附录 B 渲染该段 |
| test_old_queue_compat | v3.10.2 及更早队列复跑零新增告警（attacker_tier 缺省推导） |

## 4. 开发顺序（P10-P12 提交序列，延续 v3.10.2 P7-P9b 惯例）

- **P10 机制级**：attacker_tier（任务书判定 + collect 落盘 + 报告渲染）+
  platform_api_contracts（清单族 + source 校验 + 三层注入）
- **P11 提示级**：verifier 步骤 4 运行时版本项 + surface_mapper merge 镜像提示 +
  hypothesis_filter 逻辑镜像条款
- **P12 轻量+验收**：模板产物面指引（R1 任务书 + 步骤 0.5 条款）+ H4 时序子项
  （SKILL.md + biz_hypothesis）+ scope 构建差异声明 + SKILL.md v3.11 增量段 +
  test_v311 全绿 + install
