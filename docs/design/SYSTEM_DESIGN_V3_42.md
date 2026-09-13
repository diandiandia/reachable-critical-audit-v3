# SYSTEM_DESIGN_V3_42

版本: v3.42 | 变更边界不变式 + 模块影响面 + 兼容性

## 变更边界不变式（不改）

- 阶段骨架（R0-R6）不变
- 六门禁判据语义不变（D-1 只改 R3.5 派发资格判定，不触碰 assert_ledger 门禁本身）
- 队列数据模型主体不变（无新必填字段；refutation 判定只读既有 votes/summary 键）
- 不新增门禁名/阶段/强制义务（全部提示级或判定健壮化）

## 模块影响面

| 模块 | 变更 | 性质 |
|---|---|---|
| src/workflow_export.py | refutation 资格判定 + 空转 advisory | P1 判定健壮化 |
| tools/batch_verify.py | R4_COLLECT_WARNING diagnosis 近似键提示 | P1 诊断完备性 |
| verifier 任务书生成（_build_prompt） | 分支级声称提示 | P3 提示级 |
| SKILL.md | D-4 upstream 对账 + D-6 前缀级联 | P3 提示级 |
| assets/task_templates/hypothesis_filter.md | D-5 drop 判据补维度 | P3 提示级 |

## 兼容性

- 旧队列零行为变化：refutation 资格判定收紧方向（空 dict 从「已复核」改为「未复核」）
  只影响导出器出队行为，不改变已落盘队列数据；旧队列复跑 assert_ledger 不受影响
- TOOLING 3.42 → workflow_export 输出 tooling_version 前进（下游消费方零依赖该值语义）
- 提示级条款对已完成审计的产物零影响（只影响未来派发的任务书文本）

## 去项目化检查

- 运行时正文（提示文本）中的案例引用一律去项目化表述（「CAND-010 isAbsolute 子断言被
  real-target 证伪实录」保留追溯形态，不含项目名/框架名）
- 项目名只出现在 docs/design 追溯字段与 lessons 来源列
