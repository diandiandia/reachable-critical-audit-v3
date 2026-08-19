# Reachable Critical Audit v3.3.2 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_3_2.md` 组件 M1~M9 导出的软件开发需求。
> 编号规则：SWR-V3.3.2-xxx；状态：未开发 / 开发中 / 已经完成开发。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.3.2 段）。日期：2026-08-19

## M1: evidence_ledger 门禁与分级修复（REQ-V3.3.2-010/011/009/012/006/013）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-001 | assert_ledger gate ③（empirical_required）判定前加 `c.get("verdict")=="REACHABLE"` 前置条件 | 已经完成开发 |
| SWR-V3.3.2-002 | commit 的 correction.demote_to 分支：verdict 置为 demote 值的同时清 claim_type + 写 claim_nulled_by="commit-demote-v3.3.2" | 已经完成开发 |
| SWR-V3.3.2-003 | grade_verdict：empirical.status 比较前 `.lower()` 归一化；stored evidence_grade 与机械结果不一致时返回 warn 条目（不再静默） | 已经完成开发 |
| SWR-V3.3.2-004 | assert_ledger ③b 重写：读 R4 finding 的 empirical_result/claim_type 结构字段；强制范围=severity≥Medium 或 claim_type∈forced-claim 类；Low 且无实证接受 source_fact/机制级（REQ-V3.1-074 语义）；旧文本关键词匹配降为 fallback warn | 已经完成开发 |
| SWR-V3.3.2-005 | assert_ledger 新增复活改判检查：候选 `re_verify_gap` 非空 且 verdict==REACHABLE 且无 `refutation` 字段 → 违规（gate 名 post_resurrect_refutation） | 已经完成开发 |
| SWR-V3.3.2-006 | assert_ledger r4_feedback 实现：读 H7 default_value_table（收缩 schema 行）与 R3 REACHABLE gate 证据做 key:value 比对，差异产出 warn（r4_feedback 数组） | 已经完成开发 |

## M2: batch_verify 载体补全（REQ-V3.3.2-002/007/015/017/019/016）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-010 | `--from-journal` 增 `--expect <ids>`（逗号分隔或自动读 wave_registry）：journal 提取 id 集合 ⊇ expect 全集才落盘，不足/多余 → stderr 报错 exit≠0 | 已经完成开发 |
| SWR-V3.3.2-011 | 新命令 `--stage r35-collect --from-journal <dir>`：提取 refutation decisions（demote/strengthened/attribution_correction/note/PoC 文本），经 evidence_ledger.commit 落候选（correction 走 demote 语义，其余落 refutation 字段） | 已经完成开发 |
| SWR-V3.3.2-012 | 新命令 `--stage coverage`：tracked = hypotheses.surface_ids ∪ r4_findings[].findings[].tracked_surfaces ∪ mirror_pairs ∪ coverage_bridge.surfaces，全部经 norm_id（SURF- 前缀剥离+去空格）；输出 {total, tracked, missing, unknown_ids, surface_data} | 已经完成开发 |
| SWR-V3.3.2-013 | 新命令 `--stage grade-recheck`：逐候选跑 grade_verdict，grade 与 stored 不一致 → 更新 evidence_grade + grade_recomputed_by="main-agent-mechanical-recheck"，打印差异清单 | 已经完成开发 |
| SWR-V3.3.2-014 | IMPORTABILITY_STEPS 注入门控：`lang ∈ {python, javascript, java}` 或 target_kind==application 时注入完整步骤 0.5；静态编译语言（c/cpp/go/rust）注入一行"build 列表核对"短段 | 已经完成开发 |
| SWR-V3.3.2-015 | r4-collect：对 findings[].tracked_surfaces 逐 id 经 norm_surface_id 归一化后校验（对照 input_surface 归一化 id 集），未知 id 产出 warning 条目（不阻断落盘） | 已经完成开发 |

## M3: workflow_export 载体补全（REQ-V3.3.2-014/004/003/020）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-020 | export verify 模式：候选含 re_verify_gap 字段时在 prompt 追加「复活复核 gap（主代理注入, REQ-V3.2-021）」段（位置：checklist/self-refutation 之后）；无字段不渲染 | 已经完成开发 |
| SWR-V3.3.2-021 | export_script_resurrect：抽样后落盘 `.audit_results/_resurrect_sample.json`（{rule, selected[], unselected[]}），unselected 附抽样规则套用说明 | 已经完成开发 |
| SWR-V3.3.2-022 | 三模式 script 返回增加 project + dispatched_ids 字段（export 时注入模板常量） | 已经完成开发 |
| SWR-V3.3.2-023 | precedent_library.self_refutation_hints 精度门：cwe 交集 / lang 交集 / sink 类别匹配三重过滤，任一维度不匹配不注入；全不匹配返回空 | 已经完成开发 |

## M4: 任务书裁剪与契约（REQ-V3.3.2-018/012/022/008）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-030 | biz_hypothesis.md H7 段：default_value_table 收缩 schema（安全相关默认值清单 ≤10 项：{name, default, code_point, source_control, risk_dimensions(仅风险行), disposition}） | 已经完成开发 |
| SWR-V3.3.2-031 | biz_hypothesis.md R4 finding schema 增可选 claim_type 字段（enum 同候选 claim_type） | 已经完成开发 |
| SWR-V3.3.2-032 | biz_hypothesis.md 增「义务入库三问」说明段（触发条件/消费者/案例支撑） | 已经完成开发 |
| SWR-V3.3.2-033 | verifier 任务书输出格式段增条款：实证结果与 claim_type 矛盾时必须按实证方向修正 claim 并在 evidence 说明 | 已经完成开发 |

## M5: surface_mapper id 归一化（REQ-V3.3.2-016）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-040 | surface_mapper 定义共享 norm_surface_id(sid)（SURF- 前缀剥离+去空格，纯函数）；batch_verify 复用；不持久化 aliases 字段 | 已经完成开发 |

## M6: SKILL.md 编排与文档修订（REQ-V3.3.2-001/005/024/021/022）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-050 | SKILL.md 编排条款：每波 workflow 派发后登记 wave_registry.jsonl（run_id/mode/project/dispatched/payload_hash）；collect 以注册表+--expect 对账 | 已经完成开发 |
| SWR-V3.3.2-051 | SKILL.md R3.5 触发条款补：「复活重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 证伪池」（对应 REQ-V3.2-021 修订） | 已经完成开发 |
| SWR-V3.3.2-052 | SKILL.md 三处措辞对齐：复活抽样口径（声称类全量+其他 20%，对齐 REQ-V3.2-020/023）；分级机械复核改引 `--stage grade-recheck` 命令；R6 写明 write_lesson 幂等语义（全量重渲染，--write 与 process_notes 顺序无关） | 已经完成开发 |
| SWR-V3.3.2-053 | SKILL.md R2 节：签名 index/match 降为可选佐证器（"签名命中降为佐证器"表述改为"可选，LLM 主路径不受影响"）；R0 selfcheck 描述不动 | 已经完成开发 |
| SWR-V3.3.2-054 | SKILL.md 增「义务入库三问」条款（触发条件/消费者/案例支撑），置于 REQ 门槛/第一原则区 | 已经完成开发 |

## M7: harness_manuals 环境能力探针（REQ-V3.3.2-023）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-060 | 环境陷阱节增探针清单：机制 syscall 探针（io_uring_setup 等，附 C 探针片段）；依赖存在性（头文件/库/子模块物化）；工具替代（ss→/proc/net/tcp、time→getrusage）；shell 陷阱（zsh 等号展开、pkill -f 自匹配） | 已经完成开发 |

## M8: REQ 修订表（REQ-V3.3.2-005/018/012/007）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-070 | REQ_V3_2.md 增补修订记录：REQ-V3.2-021 追加"重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 池" | 已经完成开发 |
| SWR-V3.3.2-071 | REQ_V3_3.md 增补修订记录：H7 default_value_table 义务收缩为安全相关默认值清单（≤10 项） | 已经完成开发 |
| SWR-V3.3.2-072 | W6 发现文件 §18.9 修订记录：gate ③ 扩展 R4 收窄为 Medium+/forced-claim 类强制，Low 接受 source_fact/机制级 | 已经完成开发 |
| SWR-V3.3.2-073 | REQ_V3_1.md 增补修订记录：REQ-V3.1-051 落盘位置收敛为候选 refutation 字段（报告从队列派生） | 已经完成开发 |

## M9: tests（承接全部 REQ）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3.2-080 | test_gate3_verdict_condition：NEEDS_REVIEW 带 claim_type=crash → assert 无 empirical_required | 已经完成开发 |
| SWR-V3.3.2-081 | test_commit_demote_clears_claim：demote_to 后 claim_type=null + claim_nulled_by | 已经完成开发 |
| SWR-V3.3.2-082 | test_empirical_status_case：status="CONFIRMED" 机械复核 = empirically_confirmed | 已经完成开发 |
| SWR-V3.3.2-083 | test_gate3b_structured：③b 读结构字段；Low finding 无实证不阻断；Medium+ forced-claim 无实证阻断 | 已经完成开发 |
| SWR-V3.3.2-084 | test_post_resurrect_refutation：re_verify_gap + REACHABLE + 无 refutation → 违规；补 refutation 后放行 | 已经完成开发 |
| SWR-V3.3.2-085 | test_coverage_normalize：SURF-S-001 归一化命中 S-001；unknown id 告警 | 已经完成开发 |
| SWR-V3.3.2-086 | test_gap_render：带 re_verify_gap 候选导出含 gap 段；无 gap 不含 | 已经完成开发 |
| SWR-V3.3.2-087 | test_resurrect_sample_dump：_resurrect_sample.json 存在且 selected/unselected 与 payload 一致 | 已经完成开发 |
| SWR-V3.3.2-088 | test_journal_expect：--expect 全集校验（不足报错/多余报错/恰好通过） | 已经完成开发 |
| SWR-V3.3.2-089 | test_step05_gating：C/Go 候选 prompt 不含完整 0.5 模板；python/application 含 | 已经完成开发 |
| SWR-V3.3.2-090 | test_prec_precision_gate：Host 族先例不注入非 HTTP 候选 | 已经完成开发 |
| SWR-V3.3.2-091 | test_r4_feedback：构造 H7 表与 R3 gate 证据冲突队列 → warn 输出 | 已经完成开发 |
