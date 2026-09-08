# SWR_V3.31

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.31-001 | 门禁 ①b：keep=0 且 bc≥80% 时 spot_checked≥3 强制（r2_filter 参数提供才检查；None→skip_note） | D-1 ③c/③d 同款条件子检查先例 | test_v331: 缺 spot_checked→blocking；有→pass；None→skip |
| SWR-V3.31-002 | `hints <lang>` 单命令合并 cells+inventory | D-2 单命令降低执行摩擦且可查 | test_v331: 输出含两段+该语言条目 |
| SWR-V3.31-003 | write_lesson 落项目本地 lessons.md（删除仓库写路径） | D-3 v3.16.1 裁定执行 | test_v331: 项目本地落盘+仓库 lessons/ 无新文件 |
| SWR-V3.31-004 | R4 触发条件扩展 target_kind∈{library,hybrid} | D-4 QuickJS 7/9 证据 | test_v331: SKILL.md 条款文本 |
| SWR-V3.31-005 | equivalent 档 collect 条件 warn（缺 ownership_model） | D-5 guard_pass_subsets 同款 warn | test_v331: 触发/不触发双分支 |
| SWR-V3.31-006 | 四轴职责表+R2/R4 通道边界条款（文档） | D-6 | test_v331: 文本断言 |

## 四缺陷评估
①盲目带入：零项目名入正文；QuickJS 案例只入追溯字段 ✓
②设计偏见：①b 是条件子检查非新门禁名；D-5 warn 不自动改写 ✓
③死代码：hints 消费者=R2 流程；write_lesson 新落盘消费者=skill-optimizer 读入口 ✓
④过设计：不建 spotcheck 自动执行器（抽样仍是人做，门禁只验"做过没有"）；不建 ownership 自动建模 ✓
