# SYSTEM DESIGN V3.22 — 变更边界不变式与模块影响面（2026-09-04）

## 变更边界不变式

1. **阶段骨架不变**：R0-R6 零改动。
2. **六门禁①-⑧判据语义不变**：D-4 补簿记使 ③c 可机械满足（不改变判据,
   只消除手工补写）; D-2 改报告严重度渲染（门禁不依赖 SEVERITY_BY_CWE,
   batch_verify.py:1720 注释已明示）; 无新门禁名。
3. **队列数据模型主体不变**：无新字段（feasibility decision 是
   empirical_feasibility.json 笔记级产物, 不进队列）。
4. **零自动改写**：D-2 是确定性渲染规则（claim=other 是候选自报事实,
   非猜测）; D-4 只补缺席簿记（幂等, 不覆盖既有）。
5. **taskFile 化是导出形态对齐**（refutation/resurrect 对齐 verify 既有
   形态）——workflow 脚本消费契约（c.taskFiles 优先）已在位, 零脚本改动。

## 模块影响面

| 模块 | 改动 | 性质 |
|---|---|---|
| surface_mapper.py | size_tier 分支调序（super-large 前移） | P1 机械 |
| tools/batch_verify.py | _mechanical_severity claim=other 封顶; stage_r35n_collect 未选中自动簿记 | P1 机械 |
| workflow_export.py | refutation budget/阈值; refutation/resurrect 导出 taskFile 化 | P1+P2 |
| task_templates/biz_hypothesis.md | 落盘契约 + severity 分派指引 | P3 内容 |
| SKILL.md | R2/R5/R6 条款 + workflow 规范条款 + 数据模型速查注记 + v3.22 增量段 | P3+P4 文档 |
| workflow_export.py:22 + tests 守卫 ×12 | TOOLING 3.22 | P4 版本链 |
| tools/gen_tracking.py / REQUIREMENTS_TRACKING.md | VERSIONS 登记 + 手工段 | P4 版本链 |

## 兼容性矩阵

| 面向 | 判定 | 依据 |
|---|---|---|
| 旧队列复跑 | 零新增告警 | D-2 只影响报告渲染; D-4 只补缺席簿记（旧队列无 UNREACHABLE 未簿记者=零行为）; 门禁判据未动 |
| 旧 workflow 脚本 | 兼容 | taskFile 契约已在位（v3.10.2-005） |
| 旧导出 payload | 兼容 | 内联 prompt 回退形态保留 |
| R4 已落盘结果 | 兼容 | r4-collect 自适应归一化在位 |
| Firefox 真实队列复跑 | claim=other 严重度变 medium 渲染（34 例与主代理 override 一致——override 仍优先, 零变化）; UNREACHABLE 簿记已手工补写（幂等跳过） | 零新增告警预期 |

## 风险与回退

- **风险**：claim=other 封顶可能低估个别有实质机制的结构性条目——
  主代理仍可 severity_override 升档（SWR-V3.7-001 既有通道）, 风险可控。
- **回退**：各改动独立可 revert（分支调序/封顶/簿记/预算/导出/条款
  互不依赖）。
