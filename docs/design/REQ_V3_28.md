# REQ_V3.28 — Top15×Top10 目标物化:问题粒度层 + 双通道 + 目标闭环（2026-09-08）

> 本周期触发：用户澄清设计目标——**Top15 编程语言 × 每语言 Top10 信息安全
> 问题的审计与验证**；reachable-critical-audit 是承载载体。
> 诊断（三轮评估 + 钱学森视角裁决 + 第一性原理检验）：非架构问题、非设计
> 不可实现，是"设计没做完整"——审计机器完整，知识资产只设计了容器（矩阵），
> 容器之上的目标层（排序单位/外部来源通道/进度闭环/条目级验证追溯）从未设计。
> 性质：**内容+加载器增量**——零流水线改动、零门禁改动、裁决层零改动。

## DDL 消化

无新 lessons（QuickJS lessons 已 v3.27 消化 5/5）；本周期触发为战略目标澄清，
缺陷清单以三轮评估实录为案例支撑。

## 缺陷清单（代码核实）

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | 目标计量单位错配：需求单位="每语言 Top10 问题"（有排序/有数量），系统单位="语言×族格"——矩阵数得出格数，数不出 Top10 | 实测：16 语言无一达到 10（最高 C=6）；34/192 格 | 新增问题清单资产 resources/language_issue_inventory.json：每语言排序条目（cwe/pattern/sink_hint/pitfall/source.tier/verify），rank 由加载器按族严重度档机械计算（不落盘防漂移） | 新文件 + language_issue_matrix.py |
| D-2 | 知识输入单通道：只有战役回填一条摄入路径，两轮战役 +2 格，速率与目标差数量级 | v3.18→v3.27 实录：32→34 格 | seed CLI：外部权威源种格第二通道——tier=external_seeded 强制 origin+date 出处、去项目化扫描、lang 枚举校验、幂等（lang+title 唯一） | language_issue_matrix.py main |
| D-3 | 目标与系统开环：有传感器（stats）无设定值、无误差信号——"距 Top10 差几/哪年达标"不可答 | stats 只出计数；无里程碑概念 | goal CLI：每语言条目数/距 10 缺口/档位分布 + K1（骨架：每语言 ≥10 条带来源条目）/K2（战役验证：每语言 ≥10 条 battle_confirmed）里程碑进度 | language_issue_matrix.py main |
| D-4 | "验证"不可条目级追溯：战役级有回归集与全景评估，条目级无 | 2886 CVE 是项目级盘点 | inventory 条目 verify 字段（status/battles/candidates/date）+ 回填升档条款（P3 提示级）：验收收官把确认问题 cwe 命中条目升档 battle_confirmed | 新文件 + SKILL.md 增量段 |
| D-5 | 首版内容：34 格机械派生为 34 条目（真实溯源），零臆造——外部批量种格留待下一数据周期（逐条 WebFetch 权威源后 seed） | 种格诚实纪律（v3.18） | 派生规则：cell→1 条目；source.tier=battle_verified（cells 溯源自战役）；verify 仅对 QuickJS 实证据条目升 battle_confirmed（CAND-001/003/H-1-F1/H-2-F1/H-2-F2/H-7-F2），其余 unverified（诚实：旧战役候选 id 不可溯） | 引导派生脚本（一次性，不落仓库） |

## 义务入库三问（逐项）

- D-1~D-4：①触发=goal/inventory/seed 命令显式调用 + 回填纪律收官时点；②消费者=主代理战略盘点（goal 视图）+ R2 假设空间（提示级，经由既有 cells 路径不变）+ 验收报告；③裁掉丢什么=Top10 目标无承载物（D-1 本轮诊断核心）。
- D-5：派生条目全部带真实溯源，零新义务。

## 修法形态纪律

- 零自动改写（seed 是显式命令，幂等拒绝重复）；零新门禁；流水线/裁决层零改动。
- rank 机械计算不落盘——排序是视图不是数据（防 rank 漂移的冗余同步）。

## 召回率回归集评估

本周期缺陷属知识资产层，与发现力 fixture 方向零重叠——不适用。

## 验收判据（Phase 3.28）

test_v328 新增用例全绿（inventory 加载/rank 顺序/goal 数学/seed 校验含反面分支/
去项目化）+ 全量回归全绿 + install 双副本同步。
里程碑达成不属本周期验收判据（K1/K2 是资产建设里程碑，由 goal 视图持续追踪）。
