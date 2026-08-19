# Reachable Critical Audit v3.3.2 — 系统需求规格书（System Requirements）

> 从 `SYSTEM_DESIGN_V3_3_2.md`（问题域 P-A~P-G）导出的系统开发需求。每条附来源追溯与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.3.2 段）。日期：2026-08-19
> 编号规则：REQ-V3.3.2-xxx；优先级：P0=影响结论正确性，P1=影响效率/文档一致性
> 最高判据：SKILL.md「第一原则：通用型 Skill」；本版新增「义务入库三问」（REQ-V3.3.2-022）为所有 REQ 的默认门槛

## 1. 编排结果归属与完整性（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-001 | wave registry：每波 workflow 派发后登记 `.audit_results/wave_registry.jsonl`（append-only：run_id/mode/project/dispatched/payload_hash）；collect 以注册表对账 | 设计 §2.1 | P0 | 派发后注册表存在且含该波；SKILL.md 编排条款写明簿记义务 |
| REQ-V3.3.2-002 | `--from-journal` 全集校验：提供 `--expect <ids>`（或自动读注册表）时，journal 提取结果必须覆盖 dispatched 全集，不足/多余 → 报错不落盘（复用铁律 1 重试读，仍不足才报错） | 设计 §2.1 | P0 | 用不完整 journal 目录测试 → 报错 exit≠0；全集 → 正常落盘 |
| REQ-V3.3.2-003 | workflow 脚本（verify/refutation/resurrect 三模式）返回补 `project` + `dispatched_ids` 字段（注册表数据源，断 resume 恢复时可直接对账） | 设计 §2.1 | P1 | 三模式返回含两字段且值与 payload 一致 |
| REQ-V3.3.2-004 | resurrect 抽样决策落盘：export_script_resurrect 产出 selected/unselected/rule（声称类全量+其他 20%，min 2 max 8 的逐项套用记录）。**记录型义务**：消费者=事后问责与报告追溯，无 gate 消费此文件 | 设计 §2.1 | P1 | 抽样后 `.audit_results/_resurrect_sample.json` 存在且 unselected 非空时附理由 |

## 2. 复活-重验-复核链路（P-B）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-005 | 修订 REQ-V3.2-021：复活重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 证伪池（放行方向的独立复核义务） | 设计 §2.2 | P0 | REQ 修订表更新；SKILL.md R3.5 触发条款含该句 |
| REQ-V3.3.2-006 | assert_ledger 新增检查：候选带 re_verify_gap 且 verdict=REACHABLE 且无 refutation 字段 → 违规（沿用 resurrection_required 检查形态，不改六门禁①-⑧判据） | 设计 §2.2 | P0 | 构造复活改判且无 refutation 的队列 → assert 违规；补 refutation 后放行 |

## 3. 分级证据链（P-C）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-007 | r35-collect：`--stage r35-collect --from-journal` 把 refutation decisions 机械落候选 `refutation` 字段（correction/strengthened/poc_evidence/note），复用 evidence_ledger.commit merge 语义；修订 REQ-V3.1-051 落盘位置为「候选字段为权威，报告从队列派生」（队列唯一事实源原则） | 设计 §2.3 | P0 | refutation 波次后候选 refutation 字段存在；报告渲染读队列 |
| REQ-V3.3.2-008 | verifier 任务书 claim 自洽条款：「实证结果与 claim_type 矛盾时，必须按实证方向修正 claim 并在 evidence 说明」 | 设计 §2.3 | P0 | 任务书输出格式段含该条款 |
| REQ-V3.3.2-009 | grade_verdict 的 empirical status 比较前大小写归一化；stored grade 与机械结果不一致时输出告警（不再静默） | 设计 §2.3 | P0 | "CONFIRMED"（大写）与 "confirmed" 判定一致；不一致场景有告警输出 |

## 4. 门禁语义（P-D）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-010 | gate ③（empirical_required）前置 verdict=="REACHABLE"——NEEDS_REVIEW/UNREACHABLE 携带 claim 不触发实证门禁 | 设计 §2.4 | P0 | NEEDS_REVIEW 带 claim=crash 的队列 assert 不报 empirical_required |
| REQ-V3.3.2-011 | evidence_ledger.commit 的 demote_to 分支自动清 claim_type + claim_nulled_by 标记（与 collect 的 claim-null 对称） | 设计 §2.4 | P0 | commit demote 后候选 claim_type=null 且带标记 |
| REQ-V3.3.2-012 | gate ③b 结构化：改读 R4 finding 的 empirical_result/claim_type 结构字段；强制范围收窄至 Medium+/forced-claim 类，Low 接受 source_fact/机制级；关键词文本匹配降为 fallback warn（修订 W6 §18.9） | 设计 §2.4 | P0 | 结构化字段驱动的 ③b 判定可单测；Low finding 无实证不再阻断 |
| REQ-V3.3.2-013 | r4_feedback 消费者接线：读收缩后的 H7 结构化表与 R3 gate 证据 key:value 比对，产出 warn（v3.3 设计以来首次机械运行） | 设计 §2.4 | P1 | 构造冲突队列 → warn 输出；无冲突 → 无输出 |

## 5. 载体补全（P-E）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-014 | export verify 模式读候选 re_verify_gap 字段自动渲染「复活复核 gap」段（挂在 checklist/self-refutation 同扩展点）；无 gap 候选不渲染 | 设计 §2.5 | P0 | 带 re_verify_gap 的候选导出 payload 含 gap 段；无 gap 不含 |
| REQ-V3.3.2-015 | `--stage coverage` CLI：内置 tracked 计算（hypotheses ∪ R4 tracked_surfaces ∪ mirror_pairs ∪ coverage_bridge）+ id 归一化（SURF- 前缀剥离、去空格）+ unknown id 告警；输出即 assert_ledger 的 surface_data | 设计 §2.5 | P1 | 七项目批次队列复跑一次出数；SURF-S-XXX 归一化命中 |
| REQ-V3.3.2-016 | 共享 norm_surface_id 纯函数（SURF- 前缀剥离+去空格，定义于 surface_mapper，batch_verify 复用）；r4-collect 对 tracked_surfaces 归一化后不在 input_surface 归一化 id 集的告警。**不持久化 aliases**（可推导数据不落盘，防过设计） | 设计 §2.5/§2.5.1 | P1 | norm 函数可复用；未知 id 触发告警；input_surface.json 无新增 aliases 字段 |
| REQ-V3.3.2-017 | `--stage grade-recheck` CLI：批量逐候选跑 grade_verdict，差异写 grade_recomputed_by（v3.2 已设计条款的机械载体） | 设计 §2.5 | P1 | 批量运行输出差异清单；SKILL.md 引用该命令 |

## 6. 义务裁剪（P-F）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-018 | H7 default_value_table 收缩：安全相关默认值清单（tls/auth/listen/password/limits/timeouts 类）≤10 项，schema {name, default, code_point, source_control, risk_dimensions(仅风险行), disposition}；修订 REQ-V3.3 H7 表义务 | 设计 §2.6 | P1 | 任务书 schema 更新；r4-collect 校验行数/字段 |
| REQ-V3.3.2-019 | 步骤 0.5 按型门控：动态导入风险语言（python/js/java 反射场景）或 application 目标注入完整预检；静态编译语言（c/cpp/go/rust）降为"build 列表一行核对"短段 | 设计 §2.6 | P1 | C/Go 候选 prompt 不含完整 0.5 模板文本 |
| REQ-V3.3.2-020 | PREC 自证伪提示精度门：cwe/语言/sink 类三重过滤，匹配不足不注入；先例库主用途回归主代理裁决匹配 | 设计 §2.6 | P1 | Host 族先例不再注入 Java 配置候选 |
| REQ-V3.3.2-021 | R2 签名 index/match 降为可选佐证器（SKILL.md 写明）；R0 selfcheck（回归锚点 + 去项目化扫描）不动——第一原则守卫保留 | 设计 §2.6 | P1 | SKILL.md R2 节更新；selfcheck 语义不变 |
| REQ-V3.3.2-022 | 义务入库三问写入 SKILL.md（触发条件/消费者/案例支撑），作为此后所有 REQ 的默认门槛 | 设计 §2.6 | P1 | SKILL.md 含三问条款 |

## 7. 环境与文档（P-G）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3.2-023 | 环境能力探针清单入 harness_manuals 环境陷阱节：机制所需 syscall 探针（io_uring_setup 等）、依赖存在性（头/库/子模块物化）、工具存在性及替代（ss→/proc/net/tcp、time→getrusage）、shell 陷阱（zsh 展开、pkill 自匹配） | 设计 §2.7 | P1 | 手册含探针清单；R5 流程引用 |
| REQ-V3.3.2-024 | SKILL.md 三处措辞对齐：复活抽样口径（声称类全量+其他 20%，对齐 REQ-V3.2-020/023）、grade-recheck 命令引用、R6 write_lesson 幂等语义 | 设计 §2.7 | P1 | 三处文本与实现一致；doc-lint 测试通过 |
