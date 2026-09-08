# SYSTEM_DESIGN_V3.29 — 闭环接线

## 变更边界不变式

- 阶段骨架/六门禁判据语义/队列数据模型/运行时模块业务逻辑:零改动
- 裁决层(先例/清单/签名/harness):零改动
- 流水线运行时行为:零改动(本周期全部改动为加载器+数据+SKILL.md 提示级条款)

## 控制论视角的回路补全

| 回路环节 | v3.29 前 | v3.29 后 |
|---|---|---|
| 设定值 | goal.target=10 (v3.28) | 不变 |
| 变送器 | goal 视图 (v3.28) | 不变 |
| 控制器 | 无 | gap 降序优先级 + 选题建议 (SWR-001) |
| 执行器 | 空管道 | Top25 试点种格 156 条目 (SWR-004) + seed 双写 (SWR-003) |
| 输出反馈 | 无 | hitrate 命中率 (SWR-002) + R6 条款 (SWR-005) |
| 被控对象 | 知识资产(与发现层未接通) | + R2 接通条款 (SWR-005) |
| 限幅器 | 诚实纪律 (v3.28 seed 校验) | 不变 |

## 模块影响面

| 文件 | 改动 | 性质 |
|---|---|---|
| language_issue_matrix.py | goal priority 段 + hitrate 命令 + seed 双写 + _CWE_FAMILY 映射 | 加载器增量 |
| resources/language_issue_inventory.json | 156 试点条目(经 seed 命令入库) | 数据 |
| resources/language_issue_matrix.json | 双写新增 cells/pattern(经 seed 命令) | 数据 |
| SKILL.md | v3.29 增量段(含 R2 接通/R6 命中率条款) | 版本链 |
| workflow_export.py + tests ×19 | TOOLING 3.29 | 版本链 |
| tests/test_v329.py | 新建 | 回归 |
| docs/design/REQUIREMENTS_TRACKING.md + gen_tracking | 手工段 + 登记 | 版本链 |

## 兼容性

- 旧队列复跑零影响(流水线零改动)
- cells_for 消费契约不变(seed 双写只增不改既有格语义)
- 去项目化:新条目正文键扫描(test_v329 显式断言)
