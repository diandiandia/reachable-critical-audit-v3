# Reachable Critical Audit v3.4 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_4.md` 组件 M1~M5 导出的软件开发需求。
> 编号规则：SWR-V3.4-xxx；状态：未开发 / 开发中 / 已经完成开发。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.4 段）。日期：2026-08-19

## M1: batch_verify 覆盖账本命令（REQ-V3.4-002/003/007）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4-001 | `--stage coverage-ledger --write`：读 verify_queue，逐候选聚合 cwe×lang——cwe 双形态归一（cwe 数组取全部；sink_type 字符串按 `CWE-\d+` 提取）；候选无 lang 时按 source_file 扩展名推断；R4 findings 的 cwe 按项目语言集（候选 lang 并集）近似计入；项目级去重（同项目重复 --write 幂等） | 已经完成开发 |
| SWR-V3.4-002 | 账本家族映射：CWE 码 → family 查账本 assets families 表（未知码归 OTHER）；计数写 rows[{family, langs:{lang:count}}]，merge 语义累加；updated_at 更新 | 已经完成开发 |
| SWR-V3.4-003 | `--stage coverage-ledger` 无参：打印缺口格（rows 中 count==0 的 family×lang 格 + count==1 低深度格清单）与全矩阵计数表；账本资产缺失时 stderr 报错 exit≠0 | 已经完成开发 |
| SWR-V3.4-004 | stage_report 输出增 coverage_ledger 段：读账本资产，渲染缺口格摘要（不写回队列） | 已经完成开发 |

## M2: 账本资产（REQ-V3.4-001）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4-010 | resources/issue_coverage_matrix.json：{schema_version:"3.4", langs:[15 语言], families:{RESOURCE-DOS/MEMORY-SAFETY/INJECTION/CRYPTO/AUTHN/DATA-INTEGRITY/WEB/RACE/OTHER: {cwe:[...]}}, rows, updated_at}；初始 rows 从 /root 下历史审计项目 .audit_results/verify_queue.json 聚合回填（30 项目） | 已经完成开发 |
| SWR-V3.4-011 | 资产去项目化自检：families/rows 无项目名；15 语言清单 = v3 战役覆盖集（perl/powershell/shell/csharp/python/javascript/java/kotlin/scala/go/c/cpp/rust/php/ruby/swift） | 已经完成开发 |

## M3: 问题类清单（REQ-V3.4-004）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4-020 | checklist_library.json +4 条：CK-CRYPTO-MISUSE（binding cwe 327/326/338/347/330/310/311/295）、CK-AUTHN-BYPASS（287/862/863/285/639/926/306）、CK-BIZ-LOGIC（keywords 越权/状态机/限额/金额/流程不变式）、CK-DATA-INTEGRITY（345/351/829/347）；每条 3-6 个通用检查步骤（去项目化，无项目名） | 已经完成开发 |
| SWR-V3.4-021 | 绑定验证：cwe=CWE-327 候选经 checklist_binder.bind 产出 CK-CRYPTO-MISUSE；cwe=CWE-770 候选绑定结果与 v3.3.2 一致（无回归） | 已经完成开发 |

## M4: SKILL.md（REQ-V3.4-006/008）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4-030 | SKILL.md 批次选题规则条款：选题先跑 `--stage coverage-ledger` 读缺口格，优先未覆盖（语言 × CWE 族）格项目；可实证性=可行性约束（非第一判据） | 已经完成开发 |
| SWR-V3.4-031 | SKILL.md 报告节加"覆盖账本尾注"（本批新增覆盖格清单，经 stage_report 渲染） | 已经完成开发 |
| SWR-V3.4-032 | SKILL.md 第一原则新项目验收条款强化：验收项目优先选补缺口格项目，验收判据含"覆盖格 +1" | 已经完成开发 |

## M5: tests（承接 REQ-V3.4-001/002/004）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4-040 | test_coverage_ledger_write：构造双候选队列（cwe 数组形态 + sink_type 字符串形态、双语言）→ --write → 账本计数正确；重复 --write 幂等 | 已经完成开发 |
| SWR-V3.4-041 | test_coverage_ledger_gaps：账本置 crypto×lang 全 0 → 无参命令输出含该缺口格 | 已经完成开发 |
| SWR-V3.4-042 | test_checklist_crypto_bind：CWE-327 候选 bind 出 CK-CRYPTO-MISUSE；CWE-770 绑定无回归 | 已经完成开发 |
