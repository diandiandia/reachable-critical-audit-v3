# REQ_V3.31 — 人因闭环点机械化（2026-09-08）

> 触发：用户"开始修正这些问题"——采纳工程控制论诊断的六修正清单
> （keep=0 抽样靠人/R2 接通靠人/lessons 遗留双写/R4 触发轴错配/
> fidelity 核实靠人/形态四轴与通道重叠文档收敛）。
> 性质：机制修复版——不改变阶段骨架；门禁新增条件子检查 ①b（同 ③c/③d 先例）。

## 缺陷清单（代码核实）

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | keep=0 抽样复核是义务不是门禁——"通道失效"与"目标干净"不可机械区分 | QuickJS keep=0/bc=87.5% 实录；成熟网络库 28 条全防御先例 | assert_ledger 新增条件子检查 ①b：r2_filter 参数提供且 keep 空且 bc≥80% 时，spot_checked≥3 缺失即 blocking；旧队列（参数 None）skip_note | evidence_ledger.py + SKILL.md 门禁代码块 |
| D-2 | R2 接通靠自觉（v3.29 提示级条款） | v3.29 P1 诊断 | `hints <lang>` 单命令（cells+inventory 合并输出）+ R2 条款引用单命令 | language_issue_matrix.py + SKILL.md |
| D-3 | lessons 遗留双写（v3.16.1 裁定后仍写仓库） | QuickJS 收官实录（SKILL_LESSONS_quickjs.md 落 installed） | write_lesson 改落项目本地 .audit_results/lessons.md；删除仓库写入路径；install 同步删残留 | lessons_recorder.py |
| D-4 | R4 并行触发轴错配（maturity 不预测贡献） | QuickJS（developing）R4 产出 7/9 条确认问题 | 触发条件改为 `maturity==mature 或 target_kind∈{library,hybrid}`（提示级） | SKILL.md R4 段两处 |
| D-5 | fidelity=equivalent 所有权核实是义务非校验 | H3-F1 反证实录 | collect 条件校验：fidelity=equivalent 且 empirical 无 ownership_model → warn（同 guard_pass_subsets 先例，不阻断） | tools/batch_verify.py |
| D-6 | 形态四轴与 R2/R4 通道边界只靠注释维持 | 三轮评估实录 | SKILL.md 数据模型速查增四轴职责表 + R2/R4 通道边界条款（P3 文档） | SKILL.md |

## 义务三问（逐项）
D-1：①触发=keep=0 且 bc≥80%（条件触发）；②消费者=六门禁 assert_ledger；③裁掉丢什么=空队误放行（QuickJS 实录）。旧队列零影响（参数 None skip）。
D-2：①触发=R2 假设生成；②消费者=主代理/假设生成 agent；③裁掉丢什么=资产不传导。
D-3：①触发=R6 收官；②消费者=skill-optimizer（唯一读入口=项目本地）；③裁掉丢什么=无（v3.16.1 已裁定）。
D-4：①触发=R4 调度；②消费者=R4 并行决策；③裁掉丢什么=R4 发现力延迟兑现（7/9 实录）。
D-5：①触发=collect；②消费者=主代理裁决；③裁掉丢什么=等价实证建模失真静默（H3-F1 实录）。
D-6：文档条款，无义务。

## 修法形态纪律
零自动改写（warn 级 D-5）；①b 为条件子检查（同 ③c/③d 先例，旧队列 skip）；裁决层零改动。

## 验收判据（Phase 3.31）
test_v331 新增用例全绿 + 全量回归全绿 + install 双副本同步 + QuickJS 队列复跑零新增 blocking（①b 参数 None skip）。
