# SYSTEM_DESIGN_V3_33

## 变更边界不变式

**不改**: 阶段骨架 (R0-R6)、六门禁判据语义 (①-⑧+③c/③d 的 blocking 判定)、
队列数据模型主体 (candidates/r4_findings 字段集)、target_kind/profile 签收流程、
Mode W 波次机制、三锚点回归基线。

**新增全部为 warn 级或标注级** (D-1/D-2 标注, D-3/D-4 校验 error 但属 r2_guard
fidelity 工具面, D-5 warn, D-6 渲染修正, D-7/D-8 提示通道增强)——零新门禁名、
零新强制义务 (义务三问逐项过, 见 SWR)。

## 模块影响面

| 模块 | 变更 |
|---|---|
| surface_mapper.py | D-1: merge 同 id 碰撞 conflicts 标注; D-2: merge 域覆盖 warn |
| r2_guard.py | D-3: fidelity focus_sink 路径存在性; D-4: fidelity surface_ids 一致性 |
| batch_verify.py | D-5: r4-collect reviewed_clean Medium+ warn; D-6: 报告去重终态检查 |
| language_issue_matrix.py | D-7: hints lessons_refs 种格通道 |
| fixminer.py | D-8: 文件路径信号评分 |
| SKILL.md | D-9/D-10/D-11 P3 条款 (报告段/R1 段/R5 段) |

## 兼容性

- D-1: conflicts 条目新增 resolution 形态, 既有 kept-first-multi-domain 不变;
  渲染器对 conflicts 新形态的消费为渐进 (无消费也不影响队列)。
- D-2: warn 级, 旧队列 merge 复跑零行为变化 (仅新增 warn 输出)。
- D-3/D-4: r2_guard fidelity 仅在本工具调用时生效; 旧 r2_filter_result 文件
  (合规) 零 error; 违规文件此前人工修复, 无存量阻断。
- D-5: warn 级, 旧队列 r4-collect 复跑可能新出 warn (servo 队列 2 条)——属
  预期提示而非告警回退, 复跑基线以 blocking=0 + warn 增量说明为准。
- D-6: 渲染输出变化 (承载非 REACHABLE 时 finding 自列) —— 对既有已手工修复
  的队列 (servo: r3_link 已置空) 零变化; 对未修复形态队列是正确性修复。
- D-7: hints 输出 lessons_refs 增 matrix/ 条目——纯增量。
- D-8: fixminer 入选集合可能扩大——R2 假设消费侧零契约变化。

## 版本链

TOOLING_VERSION → 3.33; 版本守卫 ×22 → 3.33; SKILL.md 增量段; tracking 手工段;
gen_tracking VERSIONS 登记; 资产计数守卫同步 (SKILL.md 附录与正文节)。
