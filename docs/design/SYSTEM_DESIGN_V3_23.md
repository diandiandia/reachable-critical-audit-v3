# SYSTEM_DESIGN_V3_23

## 变更边界不变式（不得违反）

- **不改阶段骨架**（R0-R6）
- **不改六门禁判据语义**（①-⑧+③c+③d 原样）
- **不改队列数据模型主体**（verify_queue/input_surface/hypotheses 字段集不变；
  本版不新增字段——D-1/D-2 是条款与裁决质量约束，D-3 是模板内容与 profile
  建议信号，D-5 是测试 fixture）
- **不改第一原则三禁止**（运行时资产零项目名/零机器路径/回归锚点仅限 fixture）

## 模块影响面

| 模块 | 变更 |
|---|---|
| SKILL.md | fidelity 条款段补所有权核实（D-1）；报告/R6 段补边界声明（D-2）；严重度表补 843（D-3①）；R2 段补 differential 提示（D-4）；评估判据处引回归集（D-5） |
| task_templates/surface_map_domain.md | 语义轴测绘段补 JIT 优化正确性层轴（profile 门控注入）（D-3②） |
| task_templates/biz_hypothesis.md | 补 R2 进行中结论注入条款（D-6） |
| tools/target_profile.py | generation_layers 建议逻辑补 jit 信号（仅 recommends，不自动改写）（D-3③） |
| templates/harness/differential_probe.py | 头部/docstring 补发现化用途说明（逻辑不变）（D-4） |
| tests/fixtures/recall_regression_set.json | 新建（D-5） |
| tests/test_v323.py | 新建（守卫） |
| skill-optimizer/SKILL.md（另一 skill 仓） | 阶段 0 必读清单补回归集引用（D-5 的评估消费者；跨 skill 变更，随本周期一并提交到各自仓） |

## 兼容性

- 旧队列复跑：零行为变化（全部条款为提示/warn 级，无数据模型变更）
- target_profile 旧签收文件：无 jit 建议 = 现状行为（零强制）
- differential_probe.py 逻辑零改动（仅 docstring）
- 三队列 assert_ledger 零新增告警为验收硬项

## 风险与回滚

- D-3③ 的目录信号误报（如 `src/jit` 为无关模块）→ 信号只进 recommends，主代理
  签收可拒，零风险
- D-1 条款加重 equivalent 档成本 → 条款为提示级；真实所有权图不明时按
  "无法映射 → 不得作为缺陷前提"保守处理（与"不实证不申报"同向）
- 全部变更可逐 SWR 独立回滚（无跨模块硬依赖）
