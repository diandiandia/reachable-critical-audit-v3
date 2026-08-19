# Reachable Critical Audit v3.1 — 系统需求规格书（System Requirements）

> **文档性质**：从 `SYSTEM_DESIGN_V3_1.md`（十大问题域 P-A~P-J）与 `SKILL.md` v3.1 增量条款导出的
> 系统开发需求。每条附来源追溯（设计章节/组件 ID/lesson 出处）与验收判据。
> 需求状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.1 段）。
> **日期**：2026-08-17
> **优先级定义**：P0 = 影响结论正确性/可问责性；P1 = 影响效率/可用性；P2 = 增强项
> **编号规则**：REQ-V3.1-xxx；来源列含 W6 出处（15 语言战役 lessons）

## 1. 总体与机器资产需求（P-A/P-F）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-001 | 系统维护三个随审计进化的机器资产：precedent_library（裁决先例）、checklist_library（检查清单）、harness_manuals（15 语言手册）；三者均为代码可读 JSON/MD，裁决与自查不再依赖主代理记忆 | 设计 §0/§2、D-COMP-09/10 | P0 | 三资产文件存在且 schema 校验通过；裁决流程引用先例 id |
| REQ-V3.1-002 | 每条先例必须携带 applicability_scope 与 counterexample（论据适用前提范围先于论据本身判定） | 设计 P-F、W6 §11 | P0 | 先例库 100% 条目含两字段 |
| REQ-V3.1-003 | LLM 假设生成为 R2 正式主路径；签名命中降级为佐证器，假设不依赖签名存在 | 设计 P-A、W6 §9.1/§14.1 | P0 | 签名库全空时 R2 仍可产出假设（8 语言零覆盖先例） |
| REQ-V3.1-004 | 签名库三层化：L1 通用危险词（不生成假设）/ L2 语言词族 / L3 框架语义族；签名带 runtime_prereq 字段 | 设计 P-A、D-COMP-02 | P1 | signature_library.json 含 tier 字段；L1 命中零假设 |
| REQ-V3.1-005 | 签名贡献度度量：每假设记录 sources；连续 2 批次贡献度 <10% 的签名退役入 retired 区 | 设计 P-A、W6 §14.1 | P2 | 退役判定可脚本化执行 |
| REQ-V3.1-006 | 先例匹配器（precedent_library.py）按候选前提形态检索先例，匹配结果注入自证伪提示与裁决上下文 | 设计 P-D/P-F、D-COMP-09 | P0 | 候选可检索到能力支配/三层默认等先例 |
| REQ-V3.1-007 | 先例匹配失败不阻塞裁决；主代理自由裁量后可回填新先例（库随审计进化） | 设计 §7 权衡 2 | P1 | 新先例可经 CLI 追加且 schema 校验 |

## 2. R0 需求（maturity 判定 + 门禁修正）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-010 | R0 上下文输出 project_kind ∈ {framework, library, infra, app} 判定 | 设计 P-H、SWR-V3.1-020 | P0 | surface_mapper context 输出含 project_kind |
| REQ-V3.1-011 | mature framework 项目 R4 与 R3 并行启动，H1/H7 深度上调；非 mature 保持串行 | 设计 P-H、W6 §23.6/§24.6 | P0 | 编排指令按 project_kind 分支 |
| REQ-V3.1-012 | R0 签名冒烟门禁条件修正：hit_rate < 1.0 且 testable > 0 才阻止；全 skipped 放行 | 设计 P-J、W6 §7 | P0 | 跨仓库锚点单仓库审计不误伤 |
| REQ-V3.1-013 | R0 装载 harness_manuals/<lang>.md 到实证上下文 | 设计 P-G | P1 | R5 任务书含语言手册要点 |

## 3. R1 输入面测绘需求（validate v3.1 + 预算档位）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-020 | 证据校验双态匹配：原始 snippet 与 snippet_unescaped 变体任一命中即过 | W6 §1.1 | P0 | Perl 字面实体场景测试通过 |
| REQ-V3.1-021 | 反向包含匹配过滤超短行（首行折叠后 <10 字符不参与匹配） | W6 §1.2 | P0 | 超短行不产生假 suggested_line |
| REQ-V3.1-022 | 行号漂移修复器 repair：主窗口 ±2 → 全文件首行键匹配（±80 语义）；命中唯一时写 suggested_line 并修正行号 | W6 §18.7/§22.1 | P0 | 漂移 30+ 场景自动修复 |
| REQ-V3.1-023 | 无命中 entry 标记 paraphrased=true（可能臆造，主代理必须人工复核），不得静默 | W6 §22.1 | P0 | 臆造 snippet 被标记 |
| REQ-V3.1-024 | repair 幂等契约：已修复（有 suggested_line/paraphrased）entry 不重标；best-match 非空否则回滚 | W6 §9.5 | P0 | 二次 repair 零改动 |
| REQ-V3.1-025 | 相对路径自动解析（非绝对路径 → project_root 拼接） | W6 §24.7/§10.1 | P0 | 相对路径证据可校验 |
| REQ-V3.1-026 | 规模自适应档位 tier：<100 文件 2 agents 无限时 / 100-500 4 agents 无限时 / >500 4 agents + 45min 硬时限 + 10min 中间产物落盘 | W6 §17.1/§18.6/§20.5/§24.7 | P0 | 档位输出含 agent_count/time_limit/checkpoint |
| REQ-V3.1-027 | 空域签收（reviewed_by + empty_domain_reason）与逐字段断言（confidence_added_by 审计）维持 | W6 §9.2/§9.3 | P0 | 空域可合法闭合；主代理补字段可追溯 |

## 4. R2 假设生成需求（LLM 主路径 + schema 强制）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-030 | 假设 schema 强制 surface_ids 数组（多 surface 归属），拒绝单值/缺失 | W6 §9.6/§12.6/§16.7 | P0 | 校验器拒收无 surface_ids 假设 |
| REQ-V3.1-031 | 锚点行入队前 Read 验证非文档/注释行（退化候选拦截） | W6 §23.7 | P0 | doc block 锚点被拦截 |
| REQ-V3.1-032 | boundary-confirmation 类（防御已验证）假设单独归类，不占 R3 队列 | W6 §14.2 | P1 | 签收类假设不进队列 |
| REQ-V3.1-033 | r2_filter keep/drop 决定全量落盘（dropped_by + reason） | W6 §16.7 | P0 | 任何 drop 可追溯理由 |
| REQ-V3.1-034 | 复审计模式：R2 上下文自动注入旧审计终稿摘要（reachable/needs_review 清单），禁止凭记忆 | W6 §22.2 | P0 | 复审计任务书含终稿摘要 |
| REQ-V3.1-035 | 大代码库假设生成限时限额（≤30 分钟或 N 条硬上限），主代理兜底生成是正式退路 | W6 §17.1/§18.1 | P0 | 超时判据 + 主代理路径文档化 |

## 5. R3 证据链回溯需求（verifier v3.1）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-040 | verifier 任务书含步骤 0 承重前提验证：先 grep 证实/证伪假设前提，断裂立即终止 | W6 §17.10 | P0 | 任务书含步骤 0 且产出记录前提验证 |
| REQ-V3.1-041 | checklist_binder 按结构化 binding（cwe 并集/keywords/verdict_context）为候选自动绑定家族清单 | D-COMP-10、SWR-V3.1-050 | P0 | 绑定矩阵测试全 PASS |
| REQ-V3.1-042 | 绑定清单注入 verifier 任务书，verifier 必须逐条执行并写入证据「清单执行记录」段 | 设计 P-D | P0 | verify prompt 含清单步骤 |
| REQ-V3.1-043 | 自证伪提示：候选附先例匹配的最可能证伪论据，verifier 自查结论分离记录（不影响裁决结论） | 设计 P-D §7 权衡 1 | P1 | 任务书含自证伪段 |
| REQ-V3.1-044 | verifier 轻量实证白名单（语言对应探针方式）显式写入任务书；实证标记结构化落 empirical 字段 | W6 §14.5/§15.2/§24.8 | P0 | empirical 字段可从 evidence 自动提取 |
| REQ-V3.1-045 | 实证范围分级 scope ∈ {mechanism, function_body, full_chain, e2e} 强制；机制级只能支撑 edge_proven，不得升 empirically_confirmed | W6 §17.7/§15.6 | P0 | 分级规则在 ledger 强制 |
| REQ-V3.1-046 | claim_type 按攻击影响定类先于实证，不得因实证成本降级 claim | W6 §13.9 | P0 | 声称类与实证义务不脱钩 |
| REQ-V3.1-047 | R3.5 拦截率作为 R3 质量指标：目标从战役均值 ~50% 收敛 <30%（拦截率下降在此为正向指标） | 设计 P-D | P2 | Phase 3.1.3 复跑对照测量 |

## 6. R3.5 独立复核与裁决需求（工具箱 + 先例库）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-050 | 证伪者任务书按声称类别注入实证工具箱（区间=参照模型+百万对拍 / 解析=真实构件+畸形矩阵+触发计数 / 代理分歧=标准部署实测） | W6 §21.1/§19.4/§16.10 | P0 | 三类声称各有工具箱提示 |
| REQ-V3.1-051 | refutation 结果 schema 含 strengthened（补强向量）与 attribution_correction（归因更正）结构化字段 | W6 §13.6/§12.5 | P0 | 两字段进入报告 |
| REQ-V3.1-052 | 同族一致性断言：同 (source_file, sink_type) 家族 REACHABLE/UNREACHABLE 并存且无阻断点/裁决记录解释 → 告警 | PREC-CONSISTENCY-001、W6 §18.3 | P0 | evidence_ledger consistency 检出未解释不对称 |
| REQ-V3.1-053 | 裁决产出 correction_record schema 化（demoted_by/date/reason/precedent_ids），降级裁决必须落盘 | W6 §24.9/§16.12 | P0 | 降级无 correction_record 告警 |
| REQ-V3.1-054 | 同事实双口径：候选 NEEDS_REVIEW 与 R4 confirmed gap 共存合法，报告强制映射表 | PREC-DUAL-LENS-001、W6 §24.9 | P0 | 报告含映射表 |
| REQ-V3.1-055 | resume 必须携带与首跑一致 args；脚本内 args 缺失防御返回错误 | W6 §5 | P0 | 缺 args 不崩溃 |
| REQ-V3.1-056 | 只采信 schema-validated 最终返回；半程输出作废；同 id 多 entry 合并投票 | W6 §5/§15.7 | P0 | 投票语义不破碎 |

## 7. R4 业务假说需求（前置化 + H7 模板）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-060 | H7 标准化为默认值全表模板：每默认值 × {三层语义、哨兵语义、文档声明、数值红旗、正向默认确认} | 设计 P-H、CK-DEFAULT-VALUE-TABLE | P0 | H7 任务书含五维模板 |
| REQ-V3.1-061 | H7 数值红旗：MAX_VALUE/-1/0 三值即红旗；查依赖库哨兵处理 | W6 §19.7/§21.3 | P0 | 模板含哨兵检查步骤 |
| REQ-V3.1-062 | R4 finding schema 强制 tracked_surfaces（SURF- 前缀 id） | W6 §4/§9.7 | P0 | 覆盖率簿记不再语义重建 |
| REQ-V3.1-063 | R4 finding 与候选裁决重叠时强制 r3_link 引用 + 严重度以 R3.5 correction_record 为准 | W6 §16.12 | P0 | 重叠 finding 带 r3_link |
| REQ-V3.1-064 | R4 异常路径描述实证抽验，结果写 empirical_result/mechanism_correction | W6 §13.5 | P1 | 实证纠正可落盘 |
| REQ-V3.1-065 | H1-H7 检查清单动态回填（每批次新家族自动入清单） | W6 §12.7/§15.4/§14.3 | P2 | 新家族有回填入口 |

## 8. R5 实证抽验需求（语言手册 + 范围强制）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-070 | harness_manuals 覆盖 15 语言 × {工具链探测/版本记录义务/常见陷阱/阳性模式/网络依赖/范围建议} | 设计 P-G | P0 | 15 文件存在且含六节 |
| REQ-V3.1-071 | harness 元数据记录工具链精确版本（swift --version 等） | W6 §16.1 | P0 | 实证记录含版本 |
| REQ-V3.1-072 | 环境陷阱自检清单（stale 进程清理 + diag 路由 / daemon 线程 / env 传播验证 / PATH 检查 / 测量点放服务端） | W6 §16.5/§16.6/§16.3/§23.3 | P0 | 自检清单在任务书/runner 内建 |
| REQ-V3.1-073 | 对照矩阵实证模式（默认配置拒绝 + 弱化配置接受）入模板 | W6 §24.4 | P1 | 反序列化/签名类实证可用对照矩阵 |
| REQ-V3.1-074 | 源事实级降级规则：网络阻断 → source_fact + blocker 记录；哨兵值/算术类主张接受源事实级 | W6 §21.4/§17.7 | P0 | 阻断记录强制 |
| REQ-V3.1-075 | 多维度主张多维度实证（解压放大 = 单 chunk ratio + 多 member 行为） | W6 §23.8 | P0 | 单维度实证不得定级 |
| REQ-V3.1-076 | 0ms 假阴性先怀疑语义前提（filter 作用对象等）再怀疑结论 | W6 §13.7 | P1 | 实证设计含前提验证步 |

## 9. 工程健壮性需求（workflow 规范条款）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-080 | lint_script 静态检查：顶层 const 模板字面量禁 ${} 插值 | W6 §17.2 | P0 | 坏脚本被检出 |
| REQ-V3.1-081 | collect 全家族 lenient load + 单遍转义修复（\ 后接合法转义保留；\u 仅后接 4hex 合法；不重审杜绝振荡） | W6 §3.1-3.3 | P0 | 修复幂等（二次修复零变化） |
| REQ-V3.1-082 | workflow args 从落盘 payload 文件整读整传，禁止复制预览截断 | W6 §10.3 | P0 | next_step 规范条款 |
| REQ-V3.1-083 | journal 提取兼容 result/value 双字段 | W6 §10.4 | P0 | 双字段提取脚本 |
| REQ-V3.1-084 | refutation pool 出队排除已复核候选 | W6 §12.3 | P0 | 多波不重复出队 |
| REQ-V3.1-085 | CLI 子命令走通序列化路径的薄测试（生成逻辑与打印分离） | W6 §8 | P1 | main() 路径有测试 |

## 10. 门禁与报告需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-090 | gate ③（实证类强制实证）扩展覆盖 R4 confirmed findings | W6 §18.9 | P0 | R4 的 oom/unbounded/xss 类 findings 未实证即违规 |
| REQ-V3.1-091 | 实证标记提取器自动填充 empirical 字段供门禁③可见性检查（等级升级仍需主代理确认） | W6 §15.2 | P0 | 门禁③不再假 FAIL |
| REQ-V3.1-092 | 报告模板含 NEEDS_REVIEW ↔ R4 finding 同事实映射表 | W6 §24.9 | P0 | 报告生成含映射 |
| REQ-V3.1-093 | 条件式 REACHABLE 前提逐条列出（blocking_point 显式记录前提方可保留） | W6 §6 | P0 | 报告前提清单齐备 |
| REQ-V3.1-094 | 覆盖率簿记只认 SURF- 前缀 id，由 tracked_surfaces + surface_ids 数组驱动 | W6 §9.7/§4 | P0 | 门禁⑦机械统计 |

## 11. 验收需求（Phase 3.1.3）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.1-100 | 三项目复跑对照（akka-http/etcd/actix-web）验收：① R3.5 拦截率较战役基线下降 ② 原 REACHABLE 结论零丢失 ③ 六门禁全 PASS | 设计 §8 | P0 | 三条件同时满足 |
| REQ-V3.1-101 | 验收通过后合并 main 并 install 到 skill 目录；未通过不得覆盖 v3 运行时 | 设计 §8 | P0 | 运行时权威切换有验收背书 |

---

## 附：v3.1 需求 ↔ 问题域覆盖矩阵

| 问题域 | 覆盖需求编号 | 实现状态（2026-08-17） |
|---|---|---|
| P-A 签名零区分度 | 003/004/005 | 部分（三层重构未做） |
| P-B 证据质量 | 020-027 | 已完成（repair/tier 测试通过） |
| P-C 假设持久化 | 030-035 | 部分（schema 校验器未写） |
| P-D verifier 乐观 | 040-047 | 部分（清单注入/先例匹配未接线） |
| P-E 证伪者机制 | 050/051/055/056 | 已完成（工具箱/字段/防御已实现） |
| P-F 裁决先例 | 001/002/006/007/052/053 | 部分（先例库+断言完成，匹配器未写） |
| P-G 实证体系 | 070-076 | 部分（手册完成，runner 范围强制未写） |
| P-H R4 前置化 | 010/011/060-065 | 部分（project_kind 完成，模板未升级） |
| P-I 工程健壮 | 080-085 | 已完成（lint/lenient/resume 已实现） |
| P-J 门禁 | 012/090-094 | 部分（gate③→R4 完成，R0 条件修正未改） |
| 验收 | 100/101 | 未开始（Phase 3.1.3） |

## 修订记录（v3.3.2, SWR-V3.3.2-073）

- **REQ-V3.1-051 落盘位置收敛**（2026-08-19, 依据七项目批次复盘 §27 A3）：
  原验收判据"两字段进入报告"收敛为：**strengthened/attribution_correction 经
  `batch_verify.py --stage r35-collect --from-journal` 机械落候选 `refutation`
  字段（队列是唯一事实源原则），报告从队列派生**——原判据仍然成立，只是
  数据流从"手工抄进报告"改为"落盘队列→报告派生"。
