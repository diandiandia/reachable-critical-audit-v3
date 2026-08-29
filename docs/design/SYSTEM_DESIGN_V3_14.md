# SYSTEM_DESIGN_V3_14 — protobuf 复审计复盘缺陷修复

> 版本链：v3.13（2026-08-29，错误路径处理族 + 数值语义族 + 锚点修复）→ **v3.14（2026-08-29，protobuf 复审计复盘缺陷修复）**。
> 缺陷修复版：不改变阶段骨架 R0-R6、不改变六门禁①-⑧判据语义、不改变队列数据模型主体。
> 背景审计：protobuf 复审计（v3.13 验收审计，52 面/29 假设/12 候选/3 验证波 +
> 2 证伪波 + 2 复活波，六门禁 PASS）。复盘发现 8 项缺陷（D-1~D-8）→ 本版修复 8 项；
> 全部过义务入库三问与四缺陷评估（BIAS_EVAL_V3_14.md）。

## 0. 第一原则自检

8 项缺陷全部来自本次审计会话内实录并经代码取证核实（编辑点/测试守卫逐行确认）。
无新门禁、无新强制义务（sample 文件保持可选、D-7 一行指引）、无自动改写用户数据
（D-4 只提示）。验收含旧队列复跑零新增告警与 protobuf 受影响阶段复跑零回退。

## 1. 问题域（8 项，按本次审计出现时序）

| 编号 | 问题 | 复盘案例（本次审计实录） | 形态 |
|---|---|---|---|
| D-1 | journal_anomaly 在 r35-collect 恒误报——N=2 证伪者同 id 多 result 是设计形态，检测器按 verify 语义（1 result/id）判断 | 2 次 r35-collect 均输出「同 id 多 result 且内容各异」，主代理手工判 by-design | 收集链误报 |
| D-2 | 账本复审计幂等盲区——sources key 烧录后 re-audit 增量（would_be 真增量）被 dropped，无 re-credit 路径无手工协议 | LEDGER_IDEMPOTENT_SKIP + STATExc=1 增量被迫摸索手工合并 | 账本数据模型缺口 |
| D-3 | 复活抽样三权威——导出器内部池/gate ③c 独立要求/sample 文件 write-only 无人读 | 主代理 selected=[004,009] vs 导出池 [004,006,009] 冲突，被迫以机械为准 | 簿记一致性缺陷 |
| D-4 | unknown_surface_ids 告警无建议——S-DATA-* vs SURF-DATA-* 跨前缀形态恰在既有归一化覆盖之外 | H2×2 + H6×1 三处手工逐条定位修复 | 告警信息缺口 |
| D-5 | r3_link 值域无校验——"HYP-001"（假设 id）静默落盘至报告 | H2-F1 事后手工置 null | 校验缺口 |
| D-6 | R4 finding 终态表述 vs r3_link 候选终态矛盾无检查——r4_feedback 只比 H7-vs-R3 | H4-F5「维持 UNREACHABLE」vs CAND-009 终态 NEEDS_REVIEW，报告定稿前零拦截 | 一致性检查缺口 |
| D-7 | R1 派发写盘能力无指引——只读代理 4/5 UNWRITTEN 转写负担 | ~80KB 主代理上下文转写 | 编排指引缺口 |
| D-8 | strengthen 签收 note 未指明字段名与层级 | 先签 entry 内无效再读 gate 代码才发现字段位置 | 文案缺口 |

## 2. 修复策略（9 项 REQ，详见 REQ_V3_14.md）

1. journal 异常检测按 mode 形态区分（max_distinct_per_id 参数，r35 传 2）
2. unknown_surface_ids 建议映射（仅提示不自动改写）
3. r3_link 值域校验（warn）
4. R4 finding 终态表述与候选终态一致性 warn（字段级，非新门禁）
5. 复审计幂等分支增量指引（手工合并协议，不做自动 re-credit）
6. 复活抽样单真相（导出器读 sample 文件，可选）
7. R1 派发写盘能力指引（SKILL.md 一行）
8. strengthen 签收指引文案（字段名+层级）
9. 版本链

## 3. 义务入库三问（新义务逐条）

| 新义务 | ①触发条件 | ②消费者 | ③案例支撑 |
|---|---|---|---|
| anomaly 阈值参数 | r35/r35n collect（恒） | collect 输出告警 | 2 次 r35 误报实录 |
| suggested_corrections | unknown_surface_ids 非空 | 主代理复核 | 三处手工修复实录 |
| r3_link_invalid warn | finding 带非 CAND-* link | 主代理复核/渲染 | HYP-001 落盘实录 |
| r4_verdict_link_conflict warn | 带 r3_link 且含终态关键词 | 主代理报告定稿核对 | H4-F5 矛盾实录 |
| 幂等分支增量指引 | 幂等跳过且增量非空 | 主代理手工合并 | STATExc 摸索合并实录 |
| sample 文件读序 | resurrect 导出（恒检查条件采用） | 导出池 | 三权威冲突实录 |
| R1 写盘指引 | R1 派发（指引性） | 主代理编排 | 4/5 UNWRITTEN 实录 |
| 签收文案 | gate warn 触发 | 主代理签收 | entry 内误签实录 |

## 4. 明确不做（义务棘轮防护 + 四缺陷评估裁决）

- 不做自动 re-credit（第二案例再评）；不做 unknown_surface_ids 自动改写；
  不加新门禁；不把 D-7 升为 SWR；不改 revive/demote 裁决语义；
  sample 文件保持可选（不新增强制义务）。

## 5. 验收判据（Phase 3.14）

1. 全量回归全绿（329 基线 + test_v314 新增）+ 旧队列复跑零新增告警
2. protobuf 受影响阶段复跑零回退（r35-collect 无 anomaly 误报、coverage-ledger
   幂等分支输出增量指引、resurrect 导出读 sample 文件）
3. 审计工件修正完成（H4-F5 与 CAND-009 终态一致）
4. 源仓库分 commit + install + 安装版测试全绿
