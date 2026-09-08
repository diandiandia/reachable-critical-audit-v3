# REQ_V3.30 — paired_control_probe 双测对照探针（2026-09-08）

> 触发：用户问"templates/harness 需要丰富吗"→ 评估结论:模板纪律(v3.6 裁减
> 裁决/v3.12 明确不做)下只补一个达标候选——QuickJS 验收审计 5 次现场构造
> 同形态(对照+攻击双测, VmHWM 差分)后模板化。
> 性质:模板增量——零流水线/门禁/裁决层改动。

## 缺陷清单

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | 双测对照形态 5 次重复现场构造, 无模板承载(采样时序坑/对照缺失误判每次重付) | QuickJS 审计 5 harness(ctrl/attack/sab/flood)+"RSS 平=测法伪影"实录 | templates/harness/paired_control_probe.py + TEMPLATES 注册 + SKILL.md R5 枚举 | 新文件 + harness_runner.py + SKILL.md |

## 义务三问
①触发=R5 资源类声称实证(主代理选型);②消费者=R5 实证执行;③裁掉丢什么=5 次重复现场构造成本+采样时序坑。

## 四缺陷
盲目带入:零项目名/argv 驱动;设计偏见:只读判定不自动降级;死代码:TEMPLATES 注册+test_v330 消费;过设计:不建反序列化载荷/语言陷阱模板(案例支撑不足, 见裁决)。
