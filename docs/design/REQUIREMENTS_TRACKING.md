# Reachable Critical Audit v3 — 需求追踪矩阵（Requirements Tracking）

> 状态枚举：`未开发` / `开发中` / `已完成`；完成判据 = 对应测试通过。

> 本文件由 tools/gen_tracking.py 生成（保留既有状态）。


## 系统需求（REQ-V3）（共 72 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3-001 | 系统主分析引擎为 LLM 子智能体（测绘/回溯/判断），规则库仅作提示器，不作为判定器 | 未开发 |  |
| REQ-V3-002 | 审计起点为输入面测绘（input_surface.json），禁止全库规则轰炸作为默认路径 | 未开发 |  |
| REQ-V3-003 | 每个 verdict 必须携带证据类型（evidence_grade）与来源，不得存在无证据断言 | 未开发 |  |
| REQ-V3-004 | DoS/崩溃/内存/无界类声称必须经实证抽验（R5）确认后方可申报 | 未开发 |  |
| REQ-V3-005 | 系统无 LLM API 之外的新技术依赖 | 未开发 |  |
| REQ-V3-006 | 全流程产物（队列/测绘/假设/报告）可问责：每个结论可追溯到证据文件 | 未开发 |  |
| REQ-V3-007 | 兼容 Mode A'（Agent 工具）为默认执行模式 | 未开发 |  |
| REQ-V3-010 | R0 自检包含签名库冒烟测试：每个签名必须至少有 1 个 known_instance 可复现 | 未开发 |  |
| REQ-V3-011 | R0 自检检查 harness 执行器可用性（R5 前置） | 未开发 |  |
| REQ-V3-012 | R0.5 支持 `--cross-tags t1,t2,...` 输出"修复 commit 是否在各 tag"矩阵 | 未开发 |  |
| REQ-V3-013 | R0.5 对无 git 历史输出 NO_GIT 状态而非误导性文本 | 未开发 |  |
| REQ-V3-014 | R0.5 对 HEAD 审计自动切换"修复变体复核"模式（修复已在树，价值在兄弟路径残留复核） | 未开发 |  |
| REQ-V3-015 | R0.5 默认落盘 JSON（-o 可选而非必需） | 未开发 |  |
| REQ-V3-016 | R0.5 grep 词表分级：security 关键词与通用 fix 词分开，噪声可控 | 未开发 |  |
| REQ-V3-020 | surface_mapper 按 4 域（网络/数据/进程/存储）生成测绘任务书 | 未开发 |  |
| REQ-V3-021 | 测绘任务书必须携带项目背景（架构线索：README/依赖清单/构建文件摘要） | 未开发 |  |
| REQ-V3-022 | 每个 surface 必须附 entry_points 源码证据（file:line + 代码片段） | 未开发 |  |
| REQ-V3-023 | 每个 surface 必须记录 trust_boundary（未认证远程/受信通道/gate） | 未开发 |  |
| REQ-V3-024 | surface 携带 downstream_hints（下游可能到达的功能面提示） | 未开发 |  |
| REQ-V3-025 | 多 agent 测绘产出合并去重（同 entry_point 多域归属、冲突标注） | 未开发 |  |
| REQ-V3-026 | 测绘产出经主 Agent 复核后生效 | 未开发 |  |
| REQ-V3-030 | 签名库 schema 含语义族描述、CWE、平台 profile、grep hints、检查清单、known_instances、harness 关联 | 未开发 |  |
| REQ-V3-031 | 新增签名必须携带至少 1 个真实审计实例（known_instances 非空），禁止凭空造签名 | 未开发 |  |
| REQ-V3-032 | 签名按语义族表达且语言无关（一个签名覆盖多语言同源缺陷） | 未开发 |  |
| REQ-V3-033 | v2.1 security_profiles.json 规则转写为语义签名（方法名→语义族），作为签名库种子 | 未开发 |  |
| REQ-V3-034 | signature_matcher 沿调用图展开窗口（默认深度 3，可配）并对窗口内调用点匹配签名 hints | 未开发 |  |
| REQ-V3-035 | 签名命中生成 hypothesis（含语义家族+检查清单+sink 提示），不直接生成候选 | 未开发 |  |
| REQ-V3-036 | 同 surface×签名 命中合并去重 | 未开发 |  |
| REQ-V3-037 | LLM 快速筛选假设（排除常量/白名单场景）后再入 R3 | 未开发 |  |
| REQ-V3-038 | LOGIC_PATTERN 类签名（授权谓词弱化/修复-再暴露）独立匹配，不依赖污点链 | 未开发 |  |
| REQ-V3-040 | verifier 任务书强制每跳调用边 grep 证据（call_chain 相邻两跳附调用点证明） | 未开发 |  |
| REQ-V3-041 | evidence_grade 三级：static_only < edge_proven < empirically_confirmed | 未开发 |  |
| REQ-V3-042 | REACHABLE 且 static_only 的候选不得进入可申报清单 | 未开发 |  |
| REQ-V3-043 | 前提维度检查：platform_precondition 必须附 platform_evidence（CI matrix/平台声明） | 未开发 |  |
| REQ-V3-044 | trust_boundary 逐通道验证"远端数据确实无法流入"，禁止惯例假设 | 未开发 |  |
| REQ-V3-045 | 可降级配置门控（gate）显式记录于 verdict | 未开发 |  |
| REQ-V3-046 | 死代码豁免：blocking_point="no production callers" 是合法阻断，不强制 3 层链 | 未开发 |  |
| REQ-V3-047 | 簇级验证官方化：cluster_id + 簇级 verdict 广播 + 簇成员共享证据 | 未开发 |  |
| REQ-V3-048 | 子智能体任务书强制输出 JSON 且必须本地 json.load 校验通过后方可提交 | 未开发 |  |
| REQ-V3-049 | 子智能体心跳：任务开始先写 pending 占位（含 started_at），主代理可判"在跑/丢失" | 未开发 |  |
| REQ-V3-050 | 落盘冲突检测：目标文件已存在且非本人 pending → 追加 .agent-<id> 后缀，禁止静默覆盖 | 未开发 |  |
| REQ-V3-051 | 证伪回溯闭环：R5 证伪 → verifier 错误记录 + 候选降级 + 任务书反例注入 | 未开发 |  |
| REQ-V3-053 | 保留 H1-H6 六类假说（每类三选一 verdict） | 未开发 |  |
| REQ-V3-054 | 新增 H7 信任边界专项（同 UID/IPC 高危操作、路径语义越界、鉴权谓词弱化） | 未开发 |  |
| REQ-V3-055 | R4 规模自适应档位：小项目 3×2 / 大项目 6 / 战役模式 1×6 + r4_consolidated 标注 | 未开发 |  |
| REQ-V3-056 | R4 发现推翻 R3 结论时回写 superseded_by 标记 | 未开发 |  |
| REQ-V3-060 | 触发判定：crash/OOM/无界/XSS/协议 DoS 声称且 grade < empirically_confirmed → 强制实证 | 未开发 |  |
| REQ-V3-061 | harness 模板库含至少 4 个模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/multipart_align） | 未开发 |  |
| REQ-V3-062 | harness 执行包含时序采样（RSS/存活/exit code）与结果采集 | 未开发 |  |
| REQ-V3-063 | 实测确认 → empirically_confirmed；证伪 → 回溯修正（同 REQ-V3-051） | 未开发 |  |
| REQ-V3-064 | harness 结果附环境记录（工具链版本/依赖/端口）确保可复现 | 未开发 |  |
| REQ-V3-070 | 核心指标：输入面覆盖率、证据分级分布、实证验证率、verdict 修正记录 | 未开发 |  |
| REQ-V3-071 | 输入面覆盖率门禁 =100%（同 v2.1 PENDING 清零语义） | 未开发 |  |
| REQ-V3-072 | SDR/SNR 降为参考指标；新增签名命中→真实候选转化率（噪音自检，>80% 提示修整） | 未开发 |  |
| REQ-V3-073 | NEEDS_REVIEW 显式列出，不允许静默丢弃 | 未开发 |  |
| REQ-V3-080 | collect 按字面候选 id 匹配（接受任意前缀），不再强制拼接 CAND- | 未开发 |  |
| REQ-V3-081 | ast_scanner 入队为 merge 语义，禁止覆写既有队列 | 未开发 |  |
| REQ-V3-082 | assert 与 collect 校验规则统一（UNREACHABLE blocking_point 前置校验，允许 "N/A"/"no production callers"） | 未开发 |  |
| REQ-V3-083 | batch size 可配置 + --group-by-file 聚合模式 | 未开发 |  |
| REQ-V3-084 | R4 内置 collect/assert/report stage | 未开发 |  |
| REQ-V3-085 | collect 容错 JSON 加载（非法转义修复后重试） | 未开发 |  |
| REQ-V3-086 | 候选入队填充 source_pattern/language 字段 | 未开发 |  |
| REQ-V3-087 | 路径过滤按语言映射表（spec/tst/*_tests.rs/.Tests/*.spec.ts） | 未开发 |  |
| REQ-V3-088 | 指标口径修正：avg_depth 只统计有深度候选；NEEDS_REVIEW 单独计数 | 未开发 |  |
| REQ-V3-089 | 同点跨 CWE 关联标注（related_candidates），维度拆分裁决互引 | 未开发 |  |
| REQ-V3-090 | 平台兼容层新增 Mode W：Workflow 工具可用时，R1/R2/R3 批处理以确定性 workflow 脚本执行（loop-until-dry + schema 校验自动重试 + resumeFromRunId 断点续传）；Mode A' 手工循环保留为降级路径 | 未开发 |  |
| REQ-V3-091 | batch_verify 提供 `--stage workflow-script`：从当前队列导出 workflow 脚本（dequeue→verify→collect 循环，journal 记账） | 未开发 |  |
| REQ-V3-092 | 候选增加 attempt 计数与 escalated 终态：单候选 ≥3 次验证失败自动升级主代理裁决，不得静默无限重试 | 未开发 |  |
| REQ-V3-093 | 对账门禁：任务清单（已派发）与产出清单（文件+journal）零差异方可关闭队列；缺失任务自动重派（有上限） | 未开发 |  |
| REQ-V3-094 | 独立复核：REACHABLE 且 grade≥edge_proven 的候选经 N=2 证伪者多数决复核（task_templates/verifier_refutation.md） | 未开发 |  |
| REQ-V3-095 | 输入面覆盖率门禁：surface 总数 vs 已追踪 surface =100% 才允许关闭队列（REQ-V3-071 的编排层执行） | 未开发 |  |
| REQ-V3-096 | assert_ledger 扩展：在既有四门禁基础上增加 对账零差异 / escalated=0 或主代理签收 / surface 覆盖 100% | 未开发 |  |

## 软件需求（SWR-V3）（共 54 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3-001 | 实现 `build_architecture_context(project_root)`：从 README/依赖清单/构建文件提取 {lang, deps[], entry_hints[], maturity} | 未开发 |  |
| SWR-V3-002 | 实现 `gen_surface_tasks()`：按 network/data/process/storage 4 域生成任务书，任务书含架构背景字段 | 未开发 |  |
| SWR-V3-003 | 实现 `validate_surfaces()`：entry_points 非空 + evidence 含 file:line 与 snippet + 源码行模糊匹配校验 | 未开发 |  |
| SWR-V3-004 | trust_boundary/confidence 枚举校验 | 未开发 |  |
| SWR-V3-005 | 实现 `merge_surfaces()`：同 entry_point 多域归属合并、冲突标注 conflicts[] | 未开发 |  |
| SWR-V3-010 | 定义签名 schema（sig_id/semantic/cwe/platform_profiles/detection_hints/known_instances/empirical_harness）并附 schema 校验器 | 未开发 |  |
| SWR-V3-011 | 新增签名强制 known_instances 非空（校验拒绝空实例签名） | 未开发 |  |
| SWR-V3-012 | 初版签名库：v2.1 security_profiles.json 转写 + 本战役 33 个确认家族回填（至少含 SIG-BUFFER-ACCUM-001 跨 3 语言实例） | 未开发 |  |
| SWR-V3-013 | 冒烟测试：每签名取 1 个 known_instance 在源码副本上验证 hints 可命中，命中率 <100% 阻止启动 | 未开发 |  |
| SWR-V3-020 | 实现 ProjectIndex 构建（{callee_name: [caller_sites]} 全库索引） | 未开发 |  |
| SWR-V3-021 | 实现 `expand_window(entry, depth=3)` 沿调用图展开窗口 | 未开发 |  |
| SWR-V3-022 | 实现 `match_signatures()`：窗口内调用点源码行跑 detection_hints.grep，产出 Hit{surface_id,sig_id,site,pattern} | 未开发 |  |
| SWR-V3-023 | 实现 `gen_hypotheses()`：同 surface×sig 去重、附 checklist 与 semantic_family、生成 HYP-xxx | 未开发 |  |
| SWR-V3-024 | 实现 `emit_filter_tasks()`：批量 LLM 快速筛选任务书（排除常量/白名单/死代码） | 未开发 |  |
| SWR-V3-025 | LOGIC_PATTERN 类签名独立匹配队列（不依赖污点链） | 未开发 |  |
| SWR-V3-030 | 实现 `grade_verdict()`：三级分级规则（REACHABLE 无逐跳 edge_evidence → static_only；empirical 非空 → empirically_confirmed） | 未开发 |  |
| SWR-V3-031 | 边证据校验：edge_evidence 每项含 edge 与 proof 文本，缺 proof 拒收 | 未开发 |  |
| SWR-V3-032 | 实现 `check_preconditions()`：platform_precondition 需 platform_evidence；trust_boundary 需逐通道验证记录；gate 记录 | 未开发 |  |
| SWR-V3-033 | 实现 `commit()`：merge 语义写回 + correction_record 追加 | 未开发 |  |
| SWR-V3-034 | 实现 `assert_ledger()`：无 PENDING / REACHABLE 无 static_only / 实证类声称 100% empirically_confirmed / H1-H7 全 VERIFIED | 未开发 |  |
| SWR-V3-040 | 实现 `needs_harness()`：claim ∈ EMPIRICAL_CLAIMS 且 grade < empirically_confirmed 触发 | 未开发 |  |
| SWR-V3-041 | 内置 4 模板：ws_frame_alloc / ws_frame_accum / xss_path_sim / multipart_align（攻击脚本+判据+环境字段） | 未开发 |  |
| SWR-V3-042 | 实现时序采样：/proc/<pid>/status VmRSS 每秒采样 + kill -0 存活 + exit code 采集 | 未开发 |  |
| SWR-V3-043 | 采样协议含投递速率确认步骤（先慢速采样，以服务器实测到达量为准） | 未开发 |  |
| SWR-V3-044 | 实现 `apply_result()`：confirmed→empirically_confirmed；refuted→correction_record+降级+superseded_by | 未开发 |  |
| SWR-V3-045 | 环境记录：工具链版本/依赖/端口/沙箱限流备注写入结果 | 未开发 |  |
| SWR-V3-050 | collect 按字面候选 id 匹配（接受 R05-* 等任意前缀） | 未开发 |  |
| SWR-V3-051 | 全部入队阶段 merge 语义（r05/r1/r15/collect 不覆写既有候选） | 未开发 |  |
| SWR-V3-052 | collect/assert 共用 _validate_verdict_payload；UNREACHABLE 允许 blocking_point ∈ {"N/A","no production callers"} | 未开发 |  |
| SWR-V3-053 | `--stage next-cluster`（file×sink 聚合任务书）+ `--cluster <id>` 广播 + clustered_verified 标记 | 未开发 |  |
| SWR-V3-054 | `--batch-size N` 与 `--group-by-file` 参数 | 未开发 |  |
| SWR-V3-055 | `--stage r4-collect / r4-assert / report` | 未开发 |  |
| SWR-V3-056 | JSON 容错加载（非法转义修复重试；失败记 errors 不丢批） | 未开发 |  |
| SWR-V3-057 | 入队填充 source_pattern/language（按扩展名推断） | 未开发 |  |
| SWR-V3-058 | 任务书心跳契约：先写 <out>.pending（含 started_at）；collect 产出对账；落盘冲突加 .agent-<id> 后缀 | 未开发 |  |
| SWR-V3-059 | 死代码豁免：blocking_point="no production callers" 不触发 depth 门禁降级 | 未开发 |  |
| SWR-V3-060 | `--cross-tags` 用 git merge-base --is-ancestor 生成"修复 commit × tag"矩阵 | 未开发 |  |
| SWR-V3-061 | 无 .git → 输出 {"status":"NO_GIT"} | 未开发 |  |
| SWR-V3-062 | HEAD 审计自动"变体复核"任务书模式 | 未开发 |  |
| SWR-V3-063 | 默认落盘 JSON（-o 可选） | 未开发 |  |
| SWR-V3-064 | grep 词表分级（security vs fix 两组，噪声占比可配） | 未开发 |  |
| SWR-V3-070 | LANG_TEST_PATH_MAP 语言映射过滤（ruby/powershell/rust/ts 5 形态） | 未开发 |  |
| SWR-V3-071 | `--mode deep`（tree-sitter 佐证模式，非默认路径） | 未开发 |  |
| SWR-V3-072 | `--noise-check`：按 sink_type 抽样误报率，>80% 自动降权并提示 | 未开发 |  |
| SWR-V3-073 | 入队 merge 语义（不覆写队列） | 未开发 |  |
| SWR-V3-080 | surface_map_domain.md（4 域变体，含背景/证据强制/产出 schema） | 未开发 |  |
| SWR-V3-081 | hypothesis_filter.md（排除判据：常量/白名单/死代码） | 未开发 |  |
| SWR-V3-082 | verifier_edge_proof.md（边证据要求/前提维度/死代码豁免/分级规则） | 未开发 |  |
| SWR-V3-083 | biz_hypothesis.md（H1-H7，含 H7 信任边界检查项） | 未开发 |  |
| SWR-V3-084 | empirical_test.md（采样协议/环境记录/判据） | 未开发 |  |
| SWR-V3-085 | 全部模板尾部含 self_json_guard（json.load 校验后提交） | 未开发 |  |
| SWR-V3-090 | 端到端数据流可用：surface→hypothesis→queue→assert→report 单项目跑通 | 未开发 |  |
| SWR-V3-091 | 回归验证：sinatra/lighttpd/actix 三个已审计项目复跑，结论与已知对照（Phase 3 判据） | 未开发 |  |
| SWR-V3-092 | 全部新组件附单测（tests/ 下 test_<module>.py） | 未开发 |  |

## 系统需求（REQ-V3.1）（共 66 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3.1-001 | 系统维护三个随审计进化的机器资产：precedent_library（裁决先例）、checklist_library（检查清单）、harness_manuals（15 语言手册）；三者均为代码可读 JSON/MD，裁决与自查不再依赖主代理记忆 | 已完成 |  |
| REQ-V3.1-002 | 每条先例必须携带 applicability_scope 与 counterexample（论据适用前提范围先于论据本身判定） | 已完成 |  |
| REQ-V3.1-003 | LLM 假设生成为 R2 正式主路径；签名命中降级为佐证器，假设不依赖签名存在 | 已完成 |  |
| REQ-V3.1-004 | 签名库三层化：L1 通用危险词（不生成假设）/ L2 语言词族 / L3 框架语义族；签名带 runtime_prereq 字段 | 已完成 |  |
| REQ-V3.1-005 | 签名贡献度度量：每假设记录 sources；连续 2 批次贡献度 <10% 的签名退役入 retired 区 | 已完成 |  |
| REQ-V3.1-006 | 先例匹配器（precedent_library.py）按候选前提形态检索先例，匹配结果注入自证伪提示与裁决上下文 | 已完成 |  |
| REQ-V3.1-007 | 先例匹配失败不阻塞裁决；主代理自由裁量后可回填新先例（库随审计进化） | 已完成 |  |
| REQ-V3.1-010 | R0 上下文输出 project_kind ∈ {framework, library, infra, app} 判定 | 已完成 |  |
| REQ-V3.1-011 | mature framework 项目 R4 与 R3 并行启动，H1/H7 深度上调；非 mature 保持串行 | 已完成 |  |
| REQ-V3.1-012 | R0 签名冒烟门禁条件修正：hit_rate < 1.0 且 testable > 0 才阻止；全 skipped 放行 | 已完成 |  |
| REQ-V3.1-013 | R0 装载 harness_manuals/<lang>.md 到实证上下文 | 已完成 |  |
| REQ-V3.1-020 | 证据校验双态匹配：原始 snippet 与 snippet_unescaped 变体任一命中即过 | 已完成 |  |
| REQ-V3.1-021 | 反向包含匹配过滤超短行（首行折叠后 <10 字符不参与匹配） | 已完成 |  |
| REQ-V3.1-022 | 行号漂移修复器 repair：主窗口 ±2 → 全文件首行键匹配（±80 语义）；命中唯一时写 suggested_line 并修正行号 | 已完成 |  |
| REQ-V3.1-023 | 无命中 entry 标记 paraphrased=true（可能臆造，主代理必须人工复核），不得静默 | 已完成 |  |
| REQ-V3.1-024 | repair 幂等契约：已修复（有 suggested_line/paraphrased）entry 不重标；best-match 非空否则回滚 | 已完成 |  |
| REQ-V3.1-025 | 相对路径自动解析（非绝对路径 → project_root 拼接） | 已完成 |  |
| REQ-V3.1-026 | 规模自适应档位 tier：<100 文件 2 agents 无限时 / 100-500 4 agents 无限时 / >500 4 agents + 45min 硬时限 + 10min 中间产物落盘 | 已完成 |  |
| REQ-V3.1-027 | 空域签收（reviewed_by + empty_domain_reason）与逐字段断言（confidence_added_by 审计）维持 | 已完成 |  |
| REQ-V3.1-030 | 假设 schema 强制 surface_ids 数组（多 surface 归属），拒绝单值/缺失 | 已完成 |  |
| REQ-V3.1-031 | 锚点行入队前 Read 验证非文档/注释行（退化候选拦截） | 已完成 |  |
| REQ-V3.1-032 | boundary-confirmation 类（防御已验证）假设单独归类，不占 R3 队列 | 已完成 |  |
| REQ-V3.1-033 | r2_filter keep/drop 决定全量落盘（dropped_by + reason） | 已完成 |  |
| REQ-V3.1-034 | 复审计模式：R2 上下文自动注入旧审计终稿摘要（reachable/needs_review 清单），禁止凭记忆 | 已完成 |  |
| REQ-V3.1-035 | 大代码库假设生成限时限额（≤30 分钟或 N 条硬上限），主代理兜底生成是正式退路 | 已完成 |  |
| REQ-V3.1-040 | verifier 任务书含步骤 0 承重前提验证：先 grep 证实/证伪假设前提，断裂立即终止 | 已完成 |  |
| REQ-V3.1-041 | checklist_binder 按结构化 binding（cwe 并集/keywords/verdict_context）为候选自动绑定家族清单 | 已完成 |  |
| REQ-V3.1-042 | 绑定清单注入 verifier 任务书，verifier 必须逐条执行并写入证据「清单执行记录」段 | 已完成 |  |
| REQ-V3.1-043 | 自证伪提示：候选附先例匹配的最可能证伪论据，verifier 自查结论分离记录（不影响裁决结论） | 已完成 |  |
| REQ-V3.1-044 | verifier 轻量实证白名单（语言对应探针方式）显式写入任务书；实证标记结构化落 empirical 字段 | 已完成 |  |
| REQ-V3.1-045 | 实证范围分级 scope ∈ {mechanism, function_body, full_chain, e2e} 强制；机制级只能支撑 edge_proven，不得升 empirically_confirmed | 已完成 |  |
| REQ-V3.1-046 | claim_type 按攻击影响定类先于实证，不得因实证成本降级 claim | 已完成 |  |
| REQ-V3.1-047 | R3.5 拦截率作为 R3 质量指标：目标从战役均值 ~50% 收敛 <30%（拦截率下降在此为正向指标） | 已完成 |  |
| REQ-V3.1-050 | 证伪者任务书按声称类别注入实证工具箱（区间=参照模型+百万对拍 / 解析=真实构件+畸形矩阵+触发计数 / 代理分歧=标准部署实测） | 已完成 |  |
| REQ-V3.1-051 | refutation 结果 schema 含 strengthened（补强向量）与 attribution_correction（归因更正）结构化字段 | 已完成 |  |
| REQ-V3.1-052 | 同族一致性断言：同 (source_file, sink_type) 家族 REACHABLE/UNREACHABLE 并存且无阻断点/裁决记录解释 → 告警 | 已完成 |  |
| REQ-V3.1-053 | 裁决产出 correction_record schema 化（demoted_by/date/reason/precedent_ids），降级裁决必须落盘 | 已完成 |  |
| REQ-V3.1-054 | 同事实双口径：候选 NEEDS_REVIEW 与 R4 confirmed gap 共存合法，报告强制映射表 | 已完成 |  |
| REQ-V3.1-055 | resume 必须携带与首跑一致 args；脚本内 args 缺失防御返回错误 | 已完成 |  |
| REQ-V3.1-056 | 只采信 schema-validated 最终返回；半程输出作废；同 id 多 entry 合并投票 | 已完成 |  |
| REQ-V3.1-060 | H7 标准化为默认值全表模板：每默认值 × {三层语义、哨兵语义、文档声明、数值红旗、正向默认确认} | 已完成 |  |
| REQ-V3.1-061 | H7 数值红旗：MAX_VALUE/-1/0 三值即红旗；查依赖库哨兵处理 | 已完成 |  |
| REQ-V3.1-062 | R4 finding schema 强制 tracked_surfaces（SURF- 前缀 id） | 已完成 |  |
| REQ-V3.1-063 | R4 finding 与候选裁决重叠时强制 r3_link 引用 + 严重度以 R3.5 correction_record 为准 | 已完成 |  |
| REQ-V3.1-064 | R4 异常路径描述实证抽验，结果写 empirical_result/mechanism_correction | 已完成 |  |
| REQ-V3.1-065 | H1-H7 检查清单动态回填（每批次新家族自动入清单） | 已完成 |  |
| REQ-V3.1-070 | harness_manuals 覆盖 15 语言 × {工具链探测/版本记录义务/常见陷阱/阳性模式/网络依赖/范围建议} | 已完成 |  |
| REQ-V3.1-071 | harness 元数据记录工具链精确版本（swift --version 等） | 已完成 |  |
| REQ-V3.1-072 | 环境陷阱自检清单（stale 进程清理 + diag 路由 / daemon 线程 / env 传播验证 / PATH 检查 / 测量点放服务端） | 已完成 |  |
| REQ-V3.1-073 | 对照矩阵实证模式（默认配置拒绝 + 弱化配置接受）入模板 | 已完成 |  |
| REQ-V3.1-074 | 源事实级降级规则：网络阻断 → source_fact + blocker 记录；哨兵值/算术类主张接受源事实级 | 已完成 |  |
| REQ-V3.1-075 | 多维度主张多维度实证（解压放大 = 单 chunk ratio + 多 member 行为） | 已完成 |  |
| REQ-V3.1-076 | 0ms 假阴性先怀疑语义前提（filter 作用对象等）再怀疑结论 | 已完成 |  |
| REQ-V3.1-080 | lint_script 静态检查：顶层 const 模板字面量禁 ${} 插值 | 已完成 |  |
| REQ-V3.1-081 | collect 全家族 lenient load + 单遍转义修复（\ 后接合法转义保留；\u 仅后接 4hex 合法；不重审杜绝振荡） | 已完成 |  |
| REQ-V3.1-082 | workflow args 从落盘 payload 文件整读整传，禁止复制预览截断 | 已完成 |  |
| REQ-V3.1-083 | journal 提取兼容 result/value 双字段 | 已完成 |  |
| REQ-V3.1-084 | refutation pool 出队排除已复核候选 | 已完成 |  |
| REQ-V3.1-085 | CLI 子命令走通序列化路径的薄测试（生成逻辑与打印分离） | 已完成 |  |
| REQ-V3.1-090 | gate ③（实证类强制实证）扩展覆盖 R4 confirmed findings | 已完成 |  |
| REQ-V3.1-091 | 实证标记提取器自动填充 empirical 字段供门禁③可见性检查（等级升级仍需主代理确认） | 已完成 |  |
| REQ-V3.1-092 | 报告模板含 NEEDS_REVIEW ↔ R4 finding 同事实映射表 | 已完成 |  |
| REQ-V3.1-093 | 条件式 REACHABLE 前提逐条列出（blocking_point 显式记录前提方可保留） | 已完成 |  |
| REQ-V3.1-094 | 覆盖率簿记只认 SURF- 前缀 id，由 tracked_surfaces + surface_ids 数组驱动 | 已完成 |  |
| REQ-V3.1-100 | 三项目复跑对照（akka-http/etcd/actix-web）验收：① R3.5 拦截率较战役基线下降 ② 原 REACHABLE 结论零丢失 ③ 六门禁全 PASS | 未开发 |  |
| REQ-V3.1-101 | 验收通过后合并 main 并 install 到 skill 目录；未通过不得覆盖 v3 运行时 | 未开发 |  |

## 软件需求（SWR-V3.1）（共 49 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3.1-001 | 实现 `size_tier(project_root)`：源码文件计数 → small/medium/large 三档（agent 数/时限/落盘间隔/分域方案） | 已完成 |  |
| SWR-V3.1-002 | 实现 `repair_surfaces()`：±2 主窗口 → 首行键全文件匹配（±80 语义）→ suggested_line 写回 + 行号修正 | 已完成 |  |
| SWR-V3.1-003 | repair 零命中标记 `paraphrased=true`；幂等契约（已修复 entry 不重标） | 已完成 |  |
| SWR-V3.1-004 | 实现 `_classify_project_kind()`：framework/library/infra/app | 已完成 |  |
| SWR-V3.1-005 | validate 首行键 fallback 匹配 + paraphrased 标记（与 repair 共用逻辑） | 已完成 |  |
| SWR-V3.1-006 | CLI 子命令 `repair`/`tier` 走通序列化路径 | 已完成 |  |
| SWR-V3.1-010 | 实现 `load_lenient()` + `_fix_escapes_single_pass()`：单遍转义修复，幂等 | 已完成 |  |
| SWR-V3.1-011 | 实现 `extract_empirical_marker()`：实证标记自动提取，等级升级需 confirmed 状态 | 已完成 |  |
| SWR-V3.1-012 | 实现 `consistency_check()`：同 (source_file, sink_type) 家族 verdict 可比性断言 | 已完成 |  |
| SWR-V3.1-013 | 实现 `check_correction_schema()`：降级必落盘 correction_record；precedent_ids 存在性校验 | 已完成 |  |
| SWR-V3.1-014 | grade_verdict 升级条件收紧（empirical.status ∈ confirmed 集） | 已完成 |  |
| SWR-V3.1-015 | assert_ledger 新增 gate empirical_required_r4（R4 findings 同受实证类门禁） | 已完成 |  |
| SWR-V3.1-016 | `assert`/`grade`/`check`/`consistency` CLI 全走 load_lenient | 已完成 |  |
| SWR-V3.1-020 | 实现 `bind()`：结构化 binding（cwe 并集/keywords 备选拆分/verdict_context/applies_to_phase）+ 字符串兼容 | 已完成 |  |
| SWR-V3.1-021 | 实现 `bind_all()`：checklist_ids 写回候选（不覆盖已有） | 已完成 |  |
| SWR-V3.1-022 | 实现 `h7_template_bind()` | 已完成 |  |
| SWR-V3.1-023 | checklist_library.json 结构化 binding 重构（19 条全 dict 形态） | 已完成 |  |
| SWR-V3.1-030 | 实现 `match()`：按 cwe 家族/summary 关键词/claim_type 检索先例（返回 criterion + counterexample） | 已完成 |  |
| SWR-V3.1-031 | 实现 `self_refutation_hints()`：匹配先例 → ≤2 条证伪论据模板化 | 已完成 |  |
| SWR-V3.1-032 | 实现 `record_application()`：审计后回填 applications（幂等） | 已完成 |  |
| SWR-V3.1-033 | 实现 `add_precedent()`：schema 校验后追加新先例 | 已完成 |  |
| SWR-V3.1-040 | VERIFY/REFUTATION 脚本 args 缺失防御（resume 契约） | 已完成 |  |
| SWR-V3.1-041 | 实现 `lint_script()`：顶层 const 模板 `${}` 静态检查 | 已完成 |  |
| SWR-V3.1-042 | refute_prompt 工具箱注入（interval/parser/proxy 三类） | 已完成 |  |
| SWR-V3.1-043 | REFUTATION_SCHEMA 增加 strengthened/attribution_correction/note | 已完成 |  |
| SWR-V3.1-044 | verify payload 构建时注入绑定清单步骤（checklist_binder.bind） | 已完成 |  |
| SWR-V3.1-045 | verify payload 构建时注入自证伪提示（precedent.self_refutation_hints） | 已完成 |  |
| SWR-V3.1-046 | next_step 规范条款（整读整传/resume 一致/result\|value 双字段/半程作废） | 已完成 |  |
| SWR-V3.1-047 | refutation pool 出队排除已复核候选 | 已完成 |  |
| SWR-V3.1-050 | signature_library.json 增加 tier（L1/L2/L3）+ runtime_prereq 字段；L1 通用危险词标注 | 已完成 |  |
| SWR-V3.1-051 | signature_matcher 消费 tier：L1 命中不生成假设（仅阅读提示） | 已完成 |  |
| SWR-V3.1-052 | 贡献度统计：hypothesis.sources 回填 + 连续 2 批次 <10% 签名退役入 retired 区 | 已完成 |  |
| SWR-V3.1-053 | L2 语言词族首版回填（PowerShell/Shell/C#/Python/TS/Kotlin 战役词族） | 已完成 |  |
| SWR-V3.1-060 | 实现 `load_manual(lang)`：手册要点注入实证任务书 | 已完成 |  |
| SWR-V3.1-061 | 实现 `check_scope()`：scope 必填 + 机制级不得升 empirically_confirmed | 已完成 |  |
| SWR-V3.1-062 | 实现 `env_trap_checklist(lang)`：环境陷阱自检清单 | 已完成 |  |
| SWR-V3.1-063 | 实现 `contrast_matrix_prompt()`：对照矩阵模板 | 已完成 |  |
| SWR-V3.1-064 | 实现 `source_fact_rule()`：源事实级降级（blocker 记录 + 哨兵值/算术类豁免） | 已完成 |  |
| SWR-V3.1-070 | 实现 `validate_hypothesis()`：surface_ids 强制数组 + 存在性校验 | 已完成 |  |
| SWR-V3.1-071 | 实现 `anchor_check()`：锚点行 doc block/注释拦截 | 已完成 |  |
| SWR-V3.1-072 | 实现 `audit_filter_drops()`：keep/drop 落盘（dropped_by+reason） | 已完成 |  |
| SWR-V3.1-080 | verifier_edge_proof.md v3.1（步骤 0/清单执行记录/自证伪段/实证白名单/范围纪律） | 已完成 |  |
| SWR-V3.1-081 | biz_hypothesis.md v3.1：tracked_surfaces 强制 + r3_link + H7 默认值全表模板 | 已完成 |  |
| SWR-V3.1-082 | hypothesis_filter.md v3.1：surface_ids 数组 + sources + boundary-confirmation 归类 | 已完成 |  |
| SWR-V3.1-083 | R0 smoke 门禁条件修正（hit_rate<1.0 AND testable>0 才阻止） | 已完成 |  |
| SWR-V3.1-084 | SKILL.md 报告条款：NEEDS_REVIEW↔R4 映射表 + 前提逐条列出 | 已完成 |  |
| SWR-V3.1-090 | precedent_library.json：20 条先例（criterion/counterexample/applicability_scope 齐备） | 已完成 |  |
| SWR-V3.1-091 | checklist_library.json：19 条清单（结构化 binding） | 已完成 |  |
| SWR-V3.1-092 | harness_manuals × 15（六节结构，事实带 lesson 出处） | 已完成 |  |

## 系统需求（REQ-V3.2）（共 24 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3.2-001 | 系统上下文输出 language_inventory：每语言 {lang, file_count, component_hint}（组件归属提示） | 已完成 |  |
| REQ-V3.2-002 | 语言成为候选级属性：surface/entry_point/假设/候选均带 lang 字段，从所属组件继承 | 已完成 |  |
| REQ-V3.2-003 | R1 任务书架构背景按语言清单分片（每语言一段组件摘要），同一 4 域框架不变 | 已完成 |  |
| REQ-V3.2-004 | L2 词族匹配按 surface.lang 选择；verifier 上下文语言按候选.lang 取 | 已完成 |  |
| REQ-V3.2-005 | harness 手册按候选.lang 装载（混合项目按组件分别选择） | 已完成 |  |
| REQ-V3.2-010 | R1 新增第五域 boundary：测绘跨语言调用表 {调用方向, 语言对, 桥接文件:行, 边界类型 extern/ctypes/cffi/N-API/JNI/embed, 数据流方向} | 已完成 |  |
| REQ-V3.2-011 | boundary surface 的可达性判定采用双侧证据链 + cross_evidence 落盘（边界调用点为对接点） | 已完成 |  |
| REQ-V3.2-012 | checklist_library 新增 CK-FFI-BOUNDARY（第 21 条）：所有权转移方向/unsafe 桥不变量/ABI 布局一致性/跨语言释放责任/引用计数对称/序列化格式一致性 | 已完成 |  |
| REQ-V3.2-013 | precedent_library 新增 PREC-MULTI-LANG-001：同 sink 家族一致性断言按 lang 维度分组，跨语言组不强制一致 | 已完成 |  |
| REQ-V3.2-014 | R4 H4 检查清单引用 CK-FFI-BOUNDARY（跨语言信任边界破坏） | 已完成 |  |
| REQ-V3.2-020 | UNREACHABLE 候选按 claim_type 抽样做 N=1 复活攻击（尽力复活立场）：crash/panic/oom/unbounded/xss/protocol_dos 类全量；其他类 20% 抽样（最少 2 个，上限 8 个/项目） | 已完成 |  |
| REQ-V3.2-021 | 复活成功（清除判定被推翻）→ 候选回 R3 重验（附复活者证据），不直接改 verdict；复活失败 → 保持 UNREACHABLE 附 resurrection_review 记录 | 已完成 |  |
| REQ-V3.2-022 | workflow_export 新增 refutation-resurrect 模式（N=1、尽力复活任务书、复活裁决 schema） | 已完成 |  |
| REQ-V3.2-023 | evidence_ledger 门禁新增 R3.5-N 完成度检查：声称类 UNREACHABLE 无 resurrection_review → 违规 | 已完成 |  |
| REQ-V3.2-024 | 复活攻击任务书措辞方向为"尽力复活"（枚举 verifier 未覆盖的阻断缺口/错误前提），证据要求轻量 | 已完成 |  |
| REQ-V3.2-030 | 分级机械复核条款化：collect 后对全部 REACHABLE 强制跑 grade_verdict 重算，差异写 grade_recomputed_by；verifier 任务书加注"evidence_grade 是证据的机械函数，非自我评估" | 已完成 |  |
| REQ-V3.2-031 | 绑定关键词回填流程化：复跑/验收发现的清单绑定缺口当日回填 + 绑定矩阵回归测试追加用例 | 已完成 |  |
| REQ-V3.2-060 | 审计六门禁通过后强制 R6 lessons 回写：生成 lessons/SKILL_LESSONS_<project>.md 描述遇到的问题 | 已完成 |  |
| REQ-V3.2-061 | lessons 文档证据必须机械提取（裁决纠正/降级/复活/分级重算/paraphrased/验收记录），过程观察由主代理补充并区分标注 | 已完成 |  |
| REQ-V3.2-040 | 报告新增语言覆盖表（每语言 surface 数/候选数/REACHABLE 数/结论） | 已完成 |  |
| REQ-V3.2-041 | 报告新增 FFI 边界表（语言对/边界类型/裁决/cross_evidence 摘要） | 已完成 |  |
| REQ-V3.2-100 | 混合项目试审验收：选型判据 = ≥3 语言组件 + 存在 FFI 边界 + 公开项目（备选自造最小 fixture：C 核心 + Python ctypes + Rust cdylib）。判据：① 语言覆盖表每服务端组件语言 ≥1 surface 且非零候选（客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据，v3.2.1 REQ-V3.2.1-020 修正）② 全部 FFI 边界有 cross_evidence ③ 六门禁 PASS | 已完成 |  |
| REQ-V3.2-101 | 单语言零回退回归：任选 1 个 313 项目（akka-http）重跑，结论与 313 验收一致 | 已完成 |  |
| REQ-V3.2-102 | 验收通过后合并 main + install 到 skill 目录 | 已完成 |  |

## 软件需求（SWR-V3.2）（共 24 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3.2-010 | `build_architecture_context` 输出 language_inventory（{lang, file_count, component_hint}，绑定层/核心/前端/脚本启发式） | 已完成 |  |
| SWR-V3.2-011 | `gen_surface_tasks` 新增 boundary 第五域（boundary_kind 枚举 + 调用方向 + 语言对 schema） | 已完成 |  |
| SWR-V3.2-012 | 4 域任务书架构背景按语言分片（每语言组件摘要段） | 已完成 |  |
| SWR-V3.2-013 | normalize/validate 增加 surface/entry_point lang 字段（默认继承主语言；boundary surface 必填 boundary_kind） | 已完成 |  |
| SWR-V3.2-014 | size_tier 混合项目保底（languages>2 → large 档） | 已完成 |  |
| SWR-V3.2-020 | L2 词族按 surface.lang 过滤（词族表增加 lang 字段） | 已完成 |  |
| SWR-V3.2-021 | Hit 输出带 lang | 已完成 |  |
| SWR-V3.2-022 | checklist_library 增加 CK-FFI-BOUNDARY（第 21 条）并验证绑定矩阵命中 ffi/ctypes 类候选 | 已完成 |  |
| SWR-V3.2-030 | precedent_library 增加 PREC-MULTI-LANG-001；match 增加 lang 维度 | 已完成 |  |
| SWR-V3.2-031 | r2_guard 假设 schema 增加 lang 字段校验 | 已完成 |  |
| SWR-V3.2-040 | 实现 `resurrect_pool`：声称类 UNREACHABLE 全量 + 其他 20%（最少 2，上限 8）；排除已复核 | 已完成 |  |
| SWR-V3.2-041 | 实现 `resurrect_prompt`（尽力复活任务书：枚举阻断缺口/错误前提/三层语义误用） | 已完成 |  |
| SWR-V3.2-042 | 新增 refutation-resurrect workflow 模式（N=1、RESURRECT_SCHEMA、lint 干净） | 已完成 |  |
| SWR-V3.2-043 | 复活裁决字段：{id, revived, reason, gap} 落盘 | 已完成 |  |
| SWR-V3.2-050 | consistency_check 分组键增加 lang（跨语言组不触发告警） | 已完成 |  |
| SWR-V3.2-051 | assert_ledger 新增 resurrection_required 门禁（声称类 UNREACHABLE 无 resurrection_review → 违规） | 已完成 |  |
| SWR-V3.2-060 | harness_manuals 新增 mixed_build.md（组件级构建矩阵 + FFI harness 模板 + 跨语言编排） | 已完成 |  |
| SWR-V3.2-061 | harness_runner 混合项目多组件构建提示（按候选.lang 组装构建矩阵） | 已完成 |  |
| SWR-V3.2-070 | SKILL.md 增加分级机械复核条款（collect 后强制 grade_verdict 重算 + verifier 任务书加注"分级是证据的机械函数"） | 已完成 |  |
| SWR-V3.2-071 | SKILL.md 增加 R3.5-N 编排条款（时机/抽样/复活回 R3 重验路径） | 已完成 |  |
| SWR-V3.2-072 | SKILL.md 增加报告语言覆盖表 + FFI 边界表条款 | 已完成 |  |
| SWR-V3.2-080 | 实现 `collect()`：从 verify_queue/验收记录机械提取问题证据（correction_record/r35 降级与补强/resurrection/grade_recomputed/paraphrased/adjudication_note/target_kind） | 已完成 |  |
| SWR-V3.2-081 | 实现 `render()/write_lesson()`：生成 lessons 文档（自动提取段 + 主代理过程观察段 + 待回填段）+ 索引自动更新 | 已完成 |  |
| SWR-V3.2-082 | SKILL.md R6 条款（回写时机/价值判定/闭合门禁）+ install.sh 安装模块 | 已完成 |  |

## 系统需求（REQ-V3.2.1）（共 17 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3.2.1-001 | R0 新增 target_kind 判定：机械信号（包清单/监听器/README/Dockerfile/发布物）→ {application, library, hybrid} 推荐值 + 证据，落盘 .audit_results/target_kind.json | 已完成 |  |
| REQ-V3.2.1-002 | 主代理签收 target_kind 并写入 verify_queue.target_kind；未签收 → R3 不得启动（门禁级） | 已完成 |  |
| REQ-V3.2.1-003 | verifier 任务书按 target_kind 装载存在性规则段：application=三层默认检查含 shipped 配置实际值+运行时注册+platform_precondition；library=公共 API 即边界、仓内调用者缺失非阻断 | 已完成 |  |
| REQ-V3.2.1-004 | hybrid 目标按组件分别判定（component_hint → per-component target_kind），候选从所属组件继承 | 已完成 |  |
| REQ-V3.2.1-005 | precedent_library 新增 PREC-TARGET-KIND-001（存在性规则矩阵，Newtonsoft.Json 先例） | 已完成 |  |
| REQ-V3.2.1-010 | verifier 任务书新增必做步骤"模块可导入性预检"：顶层包解析（find_spec/构建包含）+ DI/扫描器吞错路径审查 + broken_edge 标记（NEEDS_REVIEW 条件候选） | 已完成 |  |
| REQ-V3.2.1-011 | checklist_library 新增 CK-IMPORT-REGISTRATION（可绑定 import/DI/注册类候选） | 已完成 |  |
| REQ-V3.2.1-012 | verifier 任务书新增必做步骤"消费端中间层枚举"：adapter↔domain 间缓存/门闩/降级层逐层列出 + 缓存层三查（错误分支方向/写读形状一致/缓存键写路径） | 已完成 |  |
| REQ-V3.2.1-013 | checklist_library 新增 CK-CACHE-GATE-LAYER（缓存/门闩/降级类候选绑定） | 已完成 |  |
| REQ-V3.2.1-020 | REQ-V3.2-100 判据①措辞修正：服务端组件语言 ≥1 surface 且非零候选；客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据 | 已完成 |  |
| REQ-V3.2.1-021 | 语言覆盖表新增"组件角色"列（server-side/client-only/build-config），由 component_hint 派生 | 已完成 |  |
| REQ-V3.2.1-030 | R1.5 追加 shipped-config 实际值盘点子任务：监听地址/tls_enable/认证开关的提交值 → shipped_config.json | 已完成 |  |
| REQ-V3.2.1-031 | r2_guard 对"默认可达/默认开启"gate 假设强制引用 shipped_config.json（存在时） | 已完成 |  |
| REQ-V3.2.1-032 | evidence_ledger 新增 r4_feedback 断言（warn 级）：R4 H-7 findings 与 R3 REACHABLE gate 证据冲突告警 | 已完成 |  |
| REQ-V3.2.1-040 | target_kind 判定准确：fixture→library/hybrid、Lersosa→application | 已完成 |  |
| REQ-V3.2.1-041 | Lersosa 复跑零回退：终态与 v3.2 验收一致（5 REACHABLE / 2 条件 / 4 UNREACHABLE），且 P-B1/P-B2 在 R3 即捕获 | 已完成 |  |
| REQ-V3.2.1-042 | 六门禁 PASS + r4_feedback 断言生效 + install 到 skill 目录 | 已完成 |  |

## 软件需求（SWR-V3.2.1）（共 20 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3.2.1-001 | tools/target_kind.py：determine_target_kind() 六类信号（包清单/监听器/启动链/Dockerfile/README/发布物）+ 推荐值 + 证据 + 置信度 | 已完成 |  |
| SWR-V3.2.1-002 | hybrid 判定：多组件信号相斥时按 component_hint 输出 component_kinds | 已完成 |  |
| SWR-V3.2.1-003 | CLI：`--write` 落盘 .audit_results/target_kind.json；无参数时仅打印推荐 | 已完成 |  |
| SWR-V3.2.1-004 | 主代理签收契约：verify_queue.target_kind 写入 + evidence_ledger 门禁⑧ target_kind_required（缺失→violation；--legacy-no-target-kind 仅复跑兼容） | 已完成 |  |
| SWR-V3.2.1-010 | _build_prompt 步骤 0.5 模块可导入性预检（顶层包解析/扫描器吞错路径审查/broken_edge→NEEDS_REVIEW；application 强制、library 记录型） | 已完成 |  |
| SWR-V3.2.1-011 | _build_prompt 步骤 5.5 消费端中间层枚举（write→read 注入族触发：缓存/门闩/降级层逐层列出 + 三查） | 已完成 |  |
| SWR-V3.2.1-012 | target_kind 存在性规则段装载（application/library 两版，由 verify_queue.target_kind 选择；缺省读 target_kind.json；均缺不注入兼容旧队列） | 已完成 |  |
| SWR-V3.2.1-020 | workflow_export：SHIPPED_CONFIG_SCHEMA + export_script_shipped_config()（每含 config 组件 1 agent，提交值 vs 代码零值对照），脚本 lint 干净 | 已完成 |  |
| SWR-V3.2.1-021 | 主代理收集流程：落盘 .audit_results/shipped_config.json {component, items[{file,key,committed_value,code_default,mismatched}]} | 已完成 |  |
| SWR-V3.2.1-030 | checklist_library 新增 CK-IMPORT-REGISTRATION（4 步：顶层包解析/构建包含/扫描器吞错路径/扫描日志核对） | 已完成 |  |
| SWR-V3.2.1-031 | checklist_library 新增 CK-CACHE-GATE-LAYER（4 步：中间层横向枚举/错误分支方向/写读形状/缓存键写路径） | 已完成 |  |
| SWR-V3.2.1-032 | precedent_library 新增 PREC-TARGET-KIND-001（存在性规则矩阵，Newtonsoft.Json 先例）+ PREC-IMPORT-BREAK-001（导入断裂→条件候选，Lersosa CAND-004/009 先例） | 已完成 |  |
| SWR-V3.2.1-033 | 绑定测试用例固化：import/DI/缓存/门闩类候选命中两条新清单 | 已完成 |  |
| SWR-V3.2.1-040 | r4_feedback 断言：H-7 findings 的 key:value 断言与 R3 REACHABLE 候选 gate 证据关键词冲突检测 → r4_feedback_conflicts[]（warn 级，不阻断 PASS） | 已完成 |  |
| SWR-V3.2.1-050 | gate 语义含"默认可达/默认开启"时，shipped_config.json 存在 → 提示强制追加第三层检查引用条款 | 已完成 |  |
| SWR-V3.2.1-060 | language_inventory 输出 component_role（frontend→client-only；scripts/headers→build-config；其余→server-side） | 已完成 |  |
| SWR-V3.2.1-070 | SKILL.md：R0 target_kind 步骤 + 签收条款；R1.5 shipped-config 子任务；R3 三段扩展说明；门禁⑧ | 已完成 |  |
| SWR-V3.2.1-071 | REQ_V3_2.md 判据①措辞修正（服务端组件语言判据 + 客户端组件边界面等价判据）；报告语言覆盖表组件角色列 | 已完成 |  |
| SWR-V3.2.1-080 | tests：target_kind（fixture→hybrid/Lersosa→application/单库→library）+ batch_verify 三段注入 + 门禁⑧ + r4_feedback 冲突 fixture + component_role + r2_guard 引用 + shipped-config 导出 lint | 已完成 |  |
| SWR-V3.2.1-081 | 全量回归：既有 73 测试全绿 + 新用例通过 | 已完成 |  |

## 系统需求（REQ-V3.2.2）（共 29 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3.2.2-001 | 资产入库门禁（去项目化检查器）：签名 semantic/grep 命中项目专属名黑名单（DEPROJECT_BLACKLIST）即 validate 拒绝 | 已完成 |  |
| REQ-V3.2.2-002 | 签名数据模型 v2：L2 词族 lang 必填（VALID_LANGS）；L3 语义族 cwe 非空 + semantic 抽象形态非空；污染签名重构（PY-PICKLE 拆分、TS/KT/AUTHZ/HEADER-INJ 删项目专属名） | 已完成 |  |
| REQ-V3.2.2-003 | match 阶段强制 surface.lang 过滤 + tests/test 路径段排除 | 已完成 |  |
| REQ-V3.2.2-004 | gen 只从 L3 语义族命中生成假设；L1/L2 命中仅 reading_hints 佐证 | 已完成 |  |
| REQ-V3.2.2-005 | R0 冒烟语义修正：fixture 仓库保持 anchor recall hit_rate 检查；非 fixture 仓库改为签名库完整性自检（validate+lang 完备+去项目化 0 命中+grep 可编译），失败阻止启动；回归锚点移入 tests/fixtures/known_instances.json | 已完成 |  |
| REQ-V3.2.2-006 | verifier 任务书步骤 0.5 按候选 lang 分派模板（python/c/cpp/go/rust/java/default 各一版）；例证去项目名 | 已完成 |  |
| REQ-V3.2.2-007 | 先例库/清单库运行时字段脱敏：项目名只允许出现在追溯字段（applications/source_lessons） | 已完成 |  |
| REQ-V3.2.2-008 | harness_runner 新增 parser_fuzz 模板（C/C++：ASan+UBSan 骨架，mbedtls 实战模板化），绑定 crash 声称类 | 已完成 |  |
| REQ-V3.2.2-009 | harness 覆盖矩阵（claim × 语言）落盘 resources/harness_coverage_matrix.json；R5 现场构造引用矩阵缺口 | 已完成 |  |
| REQ-V3.2.2-010 | signature_lib 新增 selfcheck CLI 子命令（R0 单一事实源）；SKILL.md 只保留该命令；新增 doc-lint 测试从 SKILL.md 抽取代码块真实执行 | 已完成 |  |
| REQ-V3.2.2-011 | surface_mapper merge 默认落盘 input_surface.json（--out 可选） | 已完成 |  |
| REQ-V3.2.2-012 | r2_guard drops 输入归一化（drop/dropped 双键） | 已完成 |  |
| REQ-V3.2.2-013 | r2_guard anchor 支持 hit_sites 数组形态（假设文件批量检查） | 已完成 |  |
| REQ-V3.2.2-014 | batch_verify r4 假说 id 归一化（H1/H-1 双向，内部统一 H-N） | 已完成 |  |
| REQ-V3.2.2-015 | lessons_recorder resurrection_review lenient 加载（str→dict 包装）；SKILL.md R3.5-N 写明候选级 dict 落盘契约 | 已完成 |  |
| REQ-V3.2.2-016 | collect 机械规则：verdict≠REACHABLE → claim_type=null + claim_nulled_by 标记 | 已完成 |  |
| REQ-V3.2.2-017 | VERDICT_SCHEMA 声明 claim_type 仅 REACHABLE 有意义（enum 含 null） | 已完成 |  |
| REQ-V3.2.2-018 | R0 落盘 scope_snapshot.json（submodule status+关键目录存在性）；batch_verify 入队前自动 diff → scope_changed 输出 | 已完成 |  |
| REQ-V3.2.2-019 | R2 drop 条目支持 scope_dependent 标记（"树外不可验证"类理由强制 true）；scope 变更时提示复活流程 | 已完成 |  |
| REQ-V3.2.2-020 | merge 落盘 mirror_pairs；assert_ledger 门禁⑦ tracked 计算自动传播镜像面 | 已完成 |  |
| REQ-V3.2.2-021 | coverage_bridge 文档化为 relay 面正式通道（SKILL.md 门禁⑦） | 已完成 |  |
| REQ-V3.2.2-022 | target_kind listener/startup-chain 信号路径分域：非产品段（tests/scripts/tools/docs）不计；库段（library/lib）与示例段（examples/demos/programs）计 lib 方向 | 已完成 |  |
| REQ-V3.2.2-023 | tier 语言混合度只计 component_role=server-side；language_inventory 运行时占比修正（>90% 非运行时目录 → build-config） | 已完成 |  |
| REQ-V3.2.2-024 | batch_verify collect --from-journal 自动提取 schema-validated 结果落盘（result/value 双字段） | 已完成 |  |
| REQ-V3.2.2-030 | evidence_ledger r4_feedback 冲突支持 resolved 标记位（{candidate,key,resolved_by,note}），已裁决冲突不再重复告警 | 已完成 |  |
| REQ-V3.2.2-040 | mbedtls 本树机械复跑：8 缺陷对应手工绕过全部消失（selfcheck/merge 落盘/drops=3/anchor 直过/r4 直连 PASS/lessons 不崩/UNREACHABLE 无 empirical 违规/镜像免手写桥） | 已完成 |  |
| REQ-V3.2.2-041 | mbedtls 复跑结论零丢失（0 REACHABLE / 6 R4 findings / 4 UNREACHABLE 复活未复活） | 已完成 |  |
| REQ-V3.2.2-042 | 三锚点回归（tests）+ 新增契约测试全绿 + install.sh 安装完成 | 已完成 |  |
| REQ-V3.2.2-043 | 第一原则验收条款：本版验收对象 mbedtls 为 v3 首审 C 库项目（此前无 C 库先例），满足"每版本至少一个新项目验收"约束并在 ACCEPTANCE 明示 | 已完成 |  |

## 软件需求（SWR-V3.2.2）（共 39 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3.2.2-001 | validate(): L2 词族 lang 必填（VALID_LANGS 集合，any 不接受）；L3 缺省 any 不强制 | 已完成 |  |
| SWR-V3.2.2-002 | validate(): cwe 非空 + semantic 非空 + 去项目化扫描（DEPROJECT_BLACKLIST 大小写不敏感子串命中即报错） | 已完成 |  |
| SWR-V3.2.2-003 | DEPROJECT_BLACKLIST 常量（mbedtls 复盘取证 24 token）+ VALID_LANGS 常量 | 已完成 |  |
| SWR-V3.2.2-004 | known_instances 非空强制退役；validate 对空列表不报错 | 已完成 |  |
| SWR-V3.2.2-005 | load_fixture_instances() 读 tests/fixtures/known_instances.json（{instances:[...]} 形态，缺失返回空表） | 已完成 |  |
| SWR-V3.2.2-006 | smoke_test 锚点源改为 fixture；testable=0 时执行 integrity_selfcheck 并挂 results["__integrity__"] | 已完成 |  |
| SWR-V3.2.2-007 | integrity_selfcheck(): validate + L2 lang 完备 + 去项目化 0 命中 + grep 可编译 | 已完成 |  |
| SWR-V3.2.2-008 | CLI selfcheck 子命令：validate 失败 exit 2；fixture 仓库 hit_rate<required exit 2；非 fixture 完整性失败 exit 2；其余 exit 0 | 已完成 |  |
| SWR-V3.2.2-010 | 13 签名重构：L3 加 lang=any；L2 加具体语言；PY-PICKLE 拆纯 pickle（pickle\\.loads/pickle\\.load\\b/Unpickler）；TS 去 multer/replyTo；KT 去 maxFrameSize/maxDecodedContentLength/respondRedirect/Cookie.parse；AUTHZ-BOUND 去 get_host/good_origin/request_origin/session_secret 加 X-Real-IP；HEADER-INJ 去 CleanXSS；LOGIC-WEAKEN 去 checkAutoType；PATH-WHITELIST 去 configdir/serve_from/valid_path 加 realpath/canonicalize | 已完成 |  |
| SWR-V3.2.2-011 | 24 条 known_instances 迁入 tests/fixtures/known_instances.json（'XPC 鉴权' 条目移除）；platform_profiles 去重 | 已完成 |  |
| SWR-V3.2.2-020 | match(): site 文件路径含 tests/test 段时跳过 | 已完成 |  |
| SWR-V3.2.2-021 | gen(): tier != L3 命中全部降为 reading_hints（附 tier 与 note），仅 L3 生成假设 | 已完成 |  |
| SWR-V3.2.2-030 | merge CLI 默认落盘 input_surface.json（--out 可选）；stderr 输出落盘路径 | 已完成 |  |
| SWR-V3.2.2-031 | merge_surfaces 产出 mirror_pairs（kept-first 冲突对，无序去重） | 已完成 |  |
| SWR-V3.2.2-032 | tier 语言混合度只计 component_role=server-side | 已完成 |  |
| SWR-V3.2.2-033 | language_inventory 运行时占比修正：core/scripts hint 且 runtime_files/file_count<0.1 → build-config | 已完成 |  |
| SWR-V3.2.2-034 | scope snapshot/diff 子命令：git submodule status + .gitmodules 路径存在性；diff 输出 changed/changes/affected_dirs | 已完成 |  |
| SWR-V3.2.2-040 | drops CLI 双键归一（dropped 优先，drop 兜底） | 已完成 |  |
| SWR-V3.2.2-041 | anchor_check 兼容 hit_sites[0] 回退；新增 anchor_check_all 批量检查（假设文件含 hypotheses 键时 CLI 自动批量） | 已完成 |  |
| SWR-V3.2.2-042 | hypothesis_filter 模板 drop 条目 scope_dependent 字段 + 说明段 | 已完成 |  |
| SWR-V3.2.2-050 | IMPORTABILITY_STEPS 常量（python/c/cpp/go/rust/java/default）；_build_prompt 按 ctx language 分派步骤 0.5 | 已完成 |  |
| SWR-V3.2.2-051 | 任务书例证脱敏（Newtonsoft.Json 先例→库型先例；Lersosa 例证→抽象形态；步骤 5.5 先例抽象化） | 已完成 |  |
| SWR-V3.2.2-052 | collect: verdict≠REACHABLE 且带 claim → claim_type=null + claim_nulled_by 标记 | 已完成 |  |
| SWR-V3.2.2-053 | _norm_hypothesis_id（H1↔H-1）；r4-collect/assert 双向归一 | 已完成 |  |
| SWR-V3.2.2-054 | --from-journal 参数 + _extract_journal_verdicts（result/value 双字段，只采信 schema-validated） | 已完成 |  |
| SWR-V3.2.2-055 | workflow-script 阶段：scope_snapshot 存在时输出 scope_changed + scope_advice | 已完成 |  |
| SWR-V3.2.2-060 | 门禁⑦ tracked_ids + mirror_pairs 镜像传播（计数型调用保持原语义） | 已完成 |  |
| SWR-V3.2.2-061 | r4_feedback resolved 标记位（r4_feedback_resolved 队列字段，冲突按 (candidate,key) 抑制） | 已完成 |  |
| SWR-V3.2.2-070 | resurrection_review lenient：str→{revived:False, outcome:str}；list→{} | 已完成 |  |
| SWR-V3.2.2-080 | templates/harness/parser_fuzz_c.py（ASan+UBSan 包装/随机矩阵/截断形态/极值前缀） | 已完成 |  |
| SWR-V3.2.2-081 | TEMPLATES 注册 parser_fuzz（langs c/cpp） | 已完成 |  |
| SWR-V3.2.2-082 | resources/harness_coverage_matrix.json（claim × 语言 + coverage 摘要） | 已完成 |  |
| SWR-V3.2.2-090 | listener/startup-chain 路径分域四类（nonproduct/libdir/examples/product）：product→app 2.0；examples-only→lib 0.8；libdir-only→lib 0.8；startup-chain 排除 nonproduct | 已完成 |  |
| SWR-V3.2.2-100 | precedent/checklist 运行时字段脱敏（12 处替换，追溯字段保留） | 已完成 |  |
| SWR-V3.2.2-101 | VERDICT_SCHEMA claim_type enum（含 null）+ 语义注释 | 已完成 |  |
| SWR-V3.2.2-102 | SKILL.md：R0 1.5 scope 快照步；R0 自检命令收敛 selfcheck；门禁⑦ coverage_bridge；R3.5-N 落盘契约 | 已完成 |  |
| SWR-V3.2.2-110 | test_doc_lint.py：R0 命令单一事实源断言 + selfcheck 对非 fixture 项目真实执行 exit 0 + 三元组契约 | 已完成 |  |
| SWR-V3.2.2-111 | test_signature_lib 契约更新：lang 必填/去项目化/完整性自检/fixture 锚点（4 新测 + 2 改造） | 已完成 |  |
| SWR-V3.2.2-112 | tests/fixtures/known_instances.json 回归锚点库 | 已完成 |  |

## 系统需求（REQ-V3.3）（共 14 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3.3-001 | L2 词族新增 c/go/rust/java 4 族（每族 ≥1 签名、lang 必填、去项目化扫描 0 命中）；VALID_LANGS 同步扩充 | 已完成 |  |
| REQ-V3.3-002 | L3 新增 SIG-STATE-RACE（CWE-362/367：check-then-act/TOCTOU/跨线程无同步）与 SIG-CRYPTO-WEAK（CWE-327/330：非密码学随机种子/可预测种子/弱哈希替代校验）语义族 | 已完成 |  |
| REQ-V3.3-003 | L3 既有族补系统形态 grep hints：PREALLOC-LEN 补声明计数→分配类词、TRUNC-CAST 补 C 窄化 cast 形态、BUFFER-ACCUM 补流式无界读形态（全部去项目化） | 已完成 |  |
| REQ-V3.3-004 | L2 词族与 harness_manual 覆盖语言对齐检查：新 4 族对应语言手册已存在（c/go/rust/java 在 harness_manuals/ 中） | 已完成 |  |
| REQ-V3.3-005 | `_classify_project_kind` 返回四值 {framework, library, infra, app}（补 library 返回路径）；构建文件降为加权信号之一；新增公共 API 主导信号（导出符号/头文件率/无 main/无监听）与框架扩展标志信号 | 已完成 |  |
| REQ-V3.3-006 | context 新增独立 maturity 信号（版本标签语义/成熟标志文件/已知框架对照表）；maturity 与 project_kind 解耦；unknown 时保守 | 已完成 |  |
| REQ-V3.3-007 | SKILL.md「R4 与 R3 并行启动」触发条件改为 maturity==mature（机械信号），主代理复核后可手动覆盖；project_kind==framework 不再单独触发 | 已完成 |  |
| REQ-V3.3-008 | trust_boundary.type 枚举补 `host_api`（语义：数据经宿主对公共 API 的调用进入；library 组件默认建议值）；surface_mapper normalize/validate 与 R1 任务书 schema 同步 | 已完成 |  |
| REQ-V3.3-009 | R1 任务书 4 域 guide 增补「非网络/离线项目」映射段（解析引擎/数据处理库/硬件协议栈示例；network 空域 + empty_domain_reason 为合法产出） | 已完成 |  |
| REQ-V3.3-010 | SKILL.md R5 段明示「不实证不申报」路径（NEEDS_REVIEW 合法终态）与源事实级降级规则引用（W6 §17.7/§21.4）为 verifier 可引用条款 | 已完成 |  |
| REQ-V3.3-011 | 报告模板 NEEDS_REVIEW 段注明「保守裁决」与「证据不足」两种成因的区分写法 | 已完成 |  |
| REQ-V3.3-012 | 先例库新增 PREC-ALLOC-VIRTUAL-001（分配请求类声称的提交内存判据）与 PREC-ENV-SAME-PRINCIPAL-001（env→代码加载类声称的同主体边界几何）；全部去项目化（项目名仅入追溯字段） | 已完成 |  |
| REQ-V3.3-013 | tools/gen_tracking.py DOCS 字典覆盖全部版本段（v3~v3.3 的 REQ/SWR 文档）；提取正则泛化为 `(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`；重建 REQUIREMENTS_TRACKING.md 含 v3.2~v3.3 全部段 | 已完成 |  |
| REQ-V3.3-014 | 验收判据强化：每版本至少一个新项目验收 + 该新项目须覆盖非 Web 形态（系统库/解析引擎/CLI 工具类） | 已完成 |  |

## 软件需求（SWR-V3.3）（共 32 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3.3-001 | L2 词族新增 `c`：grep 词覆盖 malloc/realloc 无上限家族（无预算检查的分配点）、varint/长度字段计数驱动分配形态；lang 必填 c | 已完成 |  |
| SWR-V3.3-002 | L2 词族新增 `go`：流式累积/无界 reader 消费词（io.Copy 无 limit/append 无总量预算）；lang 必填 go | 已完成 |  |
| SWR-V3.3-003 | L2 词族新增 `rust`：unsafe 块特征词、FFI 指针逃逸（transmute/from_raw_parts 无边界）、Vec 无界增长；lang 必填 rust | 已完成 |  |
| SWR-V3.3-004 | L2 词族新增 `java`：流式无界读取（InputStream.read 循环无 limit）、反序列化 sink（ObjectInputStream/readObject 不可信源）；lang 必填 java | 已完成 |  |
| SWR-V3.3-005 | L3 新增 SIG-STATE-RACE：cwe=[CWE-362, CWE-367]，semantic=检查与使用分离（TOCTOU/check-then-act）、跨线程共享状态无同步；grep 词去项目化 | 已完成 |  |
| SWR-V3.3-006 | L3 新增 SIG-CRYPTO-WEAK：cwe=[CWE-327, CWE-330]，semantic=非密码学随机源作安全用途、可预测种子（时间戳/地址）、弱哈希替代完整性校验；grep 词去项目化 | 已完成 |  |
| SWR-V3.3-007 | L3 既有族 hints 扩充：PREALLOC-LEN 补声明计数→分配类词（newvector 类/checked 分配前无预算）；TRUNC-CAST 补 C 窄化 cast 形态；BUFFER-ACCUM 补流式无界读形态；去项目化扫描 0 命中 | 已完成 |  |
| SWR-V3.3-010 | VALID_LANGS 扩充 c/go/rust/java；validate 对新 L2 族执行 lang 必填 + 去项目化检查（与既有族同路径） | 已完成 |  |
| SWR-V3.3-011 | integrity_selfcheck 自动覆盖新签名（无签名数硬编码）；L2 词族 ↔ harness_manuals 对齐检查（c/go/rust/java 手册存在性）输出 | 已完成 |  |
| SWR-V3.3-020 | lang 过滤对新 4 族生效（由 VALID_LANGS 驱动，无硬编码语言表）；命中落盘沿用 .audit_results/ 路径 | 已完成 |  |
| SWR-V3.3-030 | `_classify_project_kind` 四值返回 {framework, library, infra, app}；library 判据=公共 API 主导（导出符号密度/头文件率/无 main/无监听器）且无独立可执行入口 | 已完成 |  |
| SWR-V3.3-031 | 构建文件信号加权：原硬映射表降为 SIG 权重表（framework 标志文件 +x、infra 标志文件 +y、公共 API 信号 +z），阈值决策并输出 signals 证据列表 | 已完成 |  |
| SWR-V3.3-032 | BUILD_FILES 检出修复：确认 Makefile/CMakeLists 等根目录构建文件的扫描路径正确（Lua 审计实测 build_files=[] 根因修复） | 已完成 |  |
| SWR-V3.3-033 | context 新增 maturity 信号对象 {level: mature|developing|unknown, signals: [...]}；与 project_kind 解耦；mature 判据=版本标签语义（≥1.0 或稳定发布）+ 已知框架对照表命中 | 已完成 |  |
| SWR-V3.3-034 | trust_boundary normalize/validate 接受 host_api（枚举扩充为加性变更；旧文件不受影响） | 已完成 |  |
| SWR-V3.3-040 | surface_map_domain.md：schema trust_boundary.type 枚举补 host_api；4 域 guide 增补「非网络/离线项目」映射段（解析引擎/数据处理库/硬件协议栈示例；network 空域 + empty_domain_reason 合法）；library 组件默认边界建议 host_api | 已完成 |  |
| SWR-V3.3-041 | biz_hypothesis.md：H7 五维表模板补密码学/随机数默认值行（seed/随机源）为红旗项 | 已完成 |  |
| SWR-V3.3-042 | verifier 任务书步骤 3 跨边界判定补 host_api 边界语义（库组件：公共 API 即边界；跨边界≠跨主体——R3.5 惯例假设拦截的制度化预防） | 已完成 |  |
| SWR-V3.3-050 | PREC-ALLOC-VIRTUAL-001 入库：分配请求类声称的提交内存判据（虚拟分配≠资源耗尽；提交内存受输入流限制→无放大→severity ≤ Low）；applicability_scope=allocation/oom 类 | 已完成 |  |
| SWR-V3.3-051 | PREC-ENV-SAME-PRINCIPAL-001 入库：env→代码加载类声称的同主体边界几何（env 控制者=启动者本人→LD_PRELOAD 等效；无 shipped 特权部署证据→DIRECT+Low）；applicability_scope=env-driven 代码执行类 | 已完成 |  |
| SWR-V3.3-060 | DOCS 字典覆盖 v3/v3.1/v3.2/v3.2.1/v3.2.2/v3.3 全部 REQ/SWR 文档；提取与 load_status 正则泛化为 `(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`（兼容旧 REQ-V3-001 形态） | 已完成 |  |
| SWR-V3.3-061 | 重建 REQUIREMENTS_TRACKING.md：含全部版本段；保留既有状态列；v3.2~v3.3 新段初始状态=未开发 | 已完成 |  |
| SWR-V3.3-070 | v3.1 段「mature framework → R4 并行」触发条件改写为 maturity==mature（机械信号 + 主代理复核可覆盖）；project_kind==framework 不再单独触发 | 已完成 |  |
| SWR-V3.3-071 | R5 段明示「不实证不申报」路径（NEEDS_REVIEW 合法终态）与源事实级降级规则引用（W6 §17.7/§21.4） | 已完成 |  |
| SWR-V3.3-072 | R1 段 trust_boundary 枚举表补 host_api（语义：宿主对公共 API 的调用进入；library 组件默认） | 已完成 |  |
| SWR-V3.3-073 | 报告段 NEEDS_REVIEW 双成因字段（保守裁决 / 证据不足） | 已完成 |  |
| SWR-V3.3-074 | SKILL.md 新增 v3.3 增量段（P-A~P-F 摘要 + SYSTEM_DESIGN/REQ/SW_DESIGN/SWR 文档指针） | 已完成 |  |
| SWR-V3.3-080 | test_surface_mapper 四值分类用例：纯库 Cargo.toml→library / main+监听→app / 无构建文件→app / CMakeLists→infra；maturity 信号用例 | 已完成 |  |
| SWR-V3.3-081 | test_signature_lib：新 4 L2 族 lang 必填 + 去项目化；新 2 L3 族 cwe 完备；对齐检查输出 | 已完成 |  |
| SWR-V3.3-082 | test_signature_matcher：新族按 surface.lang 过滤命中用例 | 已完成 |  |
| SWR-V3.3-083 | test_v33.py：gen_tracking 泛化重建用例（REQ-V3.2.2-001 与 REQ-V3.3-001 均被提取） | 已完成 |  |
| SWR-V3.3-084 | fixture 扩充：非 Web 系统语言 fixture（C 解析器/系统库形态）作为 v3.3 验收新项目锚点 | 已完成 |  |
