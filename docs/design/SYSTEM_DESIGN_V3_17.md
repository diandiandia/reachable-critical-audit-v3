# SYSTEM DESIGN V3.17 — 变更边界不变式与模块影响面（2026-09-01）

## 变更边界不变式

1. **阶段骨架不变**：R0-R6 阶段名、次序、交接契约零改动。
2. **六门禁①-⑧判据语义不变**：本版不新增门禁名、不改任何门禁的判定输入；
   containment/surface_model 只服务严重度呈现与 R1/R2 派发深度，不进 gate。
3. **队列数据模型主体不变**：candidate 新增可选字段（containment）与
   surface 新增可选字段（semantic_axis）均为增量可选，缺省 = 现状；
   旧队列加载路径 lenient。
4. **兼容性不变式**：所有新机制默认关闭（profile 未签收 = 现状行为）；
   旧队列复跑零新增告警。

## 数据流

```
R0: surface_mapper context ──┐
   tools/target_profile.py ──┴→ 推荐值 ──主代理签收──→ .audit_results/target_profile.json
                                                    │(未签收 = 全默认)
R1: size_tier(读 profile.scale_class/组件清单) ──→ 两阶段派发(super-large)
    surface_map_domain.md(读 profile.surface_model) ──→ 语义轴段(仅 semantic/hybrid)
    language_inventory / CODE_EXTENSIONS / _EXT_LANG(读 generation_registry ∪
        profile.generation_layers) ──→ .tq/.pb.cc 可见 + provenance
R2: 假设生成沿语义轴采样(profile.surface_model)
R3: workflow_export 注入块(读 profile.containment_default) ──→ verifier 提问
    collect: _derive_containment(缺省 none) ──→ candidate.containment
R5: differential_probe 模板(主代理按 empirical_modes 选型)
报告: severity_for(读 containment) ──→ 调整 + 行标记
```

## 模块影响面

| 模块 | 改动 | 性质 |
|---|---|---|
| surface_mapper.py | 扩展名合并视图（注册表+profile）；size_tier super-large 档+components；validate/merge 容忍 semantic_axis | 机械+结构 |
| signature_matcher.py | CODE_EXTENSIONS 视图；scaled_caps | 机械 |
| tools/batch_verify.py | _EXT_LANG 视图；_derive_containment；collect 落盘 containment；severity_for/_mechanical_severity/_r4_severity 调整步；报告行标记；tracked-ids 轴计数 | 结构 |
| tools/target_profile.py（新） | 信号探测 + 推荐 + --write | 结构 |
| workflow_export.py | verifier 注入块 containment 提问（默认零注入, profile 签收才注入） | 结构 |
| harness_runner.py | TEMPLATES + differential 注册 | 机械 |
| resources/generation_registry.json（新） | 默认扩展名 + 通用 DSL 族 | 数据 |
| resources/checklist_library.json | +5 清单（2 族） | 数据 |
| templates/harness/differential_probe.py（新） | 通用差分模板 | 内容 |
| task_templates/surface_map_domain.md | 语义轴段 + two_phase 条款 | 内容 |
| harness_manuals/mixed_build.md | 生成物重超大型构建章节 | 内容 |
| SKILL.md | R0 增 target_profile 步骤；R1 两阶段/语义轴条款；R5 模板枚举；严重度表 containment 行；数据模型速查；v3.17 增量段 | 文档 |
| install.sh | 无需改（目录级复制自动携带新文件） | 无 |

## 兼容性矩阵（旧队列复跑）

- gpac/freetype/av 代表队列：assert_ledger violations blocking=0、warn 与
  变更前逐条一致（新 warn 仅 profile 签收后出现，三队列无 profile）。
- 旧 fixture（三锚点 known_instances）：hit_rate 断言零变化。
- test_v39.py:253 清单 39 条断言 → 44（守卫同步，非语义变化）。
- test_doc_lint.py 资产计数断言同步（清单 39→44、模板 5→6）。
