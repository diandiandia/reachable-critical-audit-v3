# Reachable Critical Audit v3 — 需求追踪矩阵（Requirements Tracking）

> 状态枚举：`未开发` / `开发中` / `已完成`；完成判据 = 对应测试通过。

> 本文件由 tools/gen_tracking.py 生成（保留既有状态）。


## 系统需求（REQ-V3）（共 72 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| REQ-V3-001 | 系统主分析引擎为 LLM 子智能体（测绘/回溯/判断），规则库仅作提示器，不作为判定器 | 开发中 |  |
| REQ-V3-002 | 审计起点为输入面测绘（input_surface.json），禁止全库规则轰炸作为默认路径 | 开发中 |  |
| REQ-V3-003 | 每个 verdict 必须携带证据类型（evidence_grade）与来源，不得存在无证据断言 | 已完成 |  |
| REQ-V3-004 | DoS/崩溃/内存/无界类声称必须经实证抽验（R5）确认后方可申报 | 已完成 |  |
| REQ-V3-005 | 系统无 LLM API 之外的新技术依赖 | 已完成 |  |
| REQ-V3-006 | 全流程产物（队列/测绘/假设/报告）可问责：每个结论可追溯到证据文件 | 开发中 |  |
| REQ-V3-007 | 兼容 Mode A'（Agent 工具）为默认执行模式 | 已完成 |  |
| REQ-V3-010 | R0 自检包含签名库冒烟测试：每个签名必须至少有 1 个 known_instance 可复现 | 已完成 |  |
| REQ-V3-011 | R0 自检检查 harness 执行器可用性（R5 前置） | 已完成 |  |
| REQ-V3-012 | R0.5 支持 `--cross-tags t1,t2,...` 输出"修复 commit 是否在各 tag"矩阵 | 已完成 |  |
| REQ-V3-013 | R0.5 对无 git 历史输出 NO_GIT 状态而非误导性文本 | 已完成 |  |
| REQ-V3-014 | R0.5 对 HEAD 审计自动切换"修复变体复核"模式（修复已在树，价值在兄弟路径残留复核） | 已完成 |  |
| REQ-V3-015 | R0.5 默认落盘 JSON（-o 可选而非必需） | 已完成 |  |
| REQ-V3-016 | R0.5 grep 词表分级：security 关键词与通用 fix 词分开，噪声可控 | 已完成 |  |
| REQ-V3-020 | surface_mapper 按 4 域（网络/数据/进程/存储）生成测绘任务书 | 已完成 |  |
| REQ-V3-021 | 测绘任务书必须携带项目背景（架构线索：README/依赖清单/构建文件摘要） | 已完成 |  |
| REQ-V3-022 | 每个 surface 必须附 entry_points 源码证据（file:line + 代码片段） | 已完成 |  |
| REQ-V3-023 | 每个 surface 必须记录 trust_boundary（未认证远程/受信通道/gate） | 已完成 |  |
| REQ-V3-024 | surface 携带 downstream_hints（下游可能到达的功能面提示） | 已完成 |  |
| REQ-V3-025 | 多 agent 测绘产出合并去重（同 entry_point 多域归属、冲突标注） | 已完成 |  |
| REQ-V3-026 | 测绘产出经主 Agent 复核后生效 | 已完成 |  |
| REQ-V3-030 | 签名库 schema 含语义族描述、CWE、平台 profile、grep hints、检查清单、known_instances、harness 关联 | 已完成 |  |
| REQ-V3-031 | 新增签名必须携带至少 1 个真实审计实例（known_instances 非空），禁止凭空造签名 | 已完成 |  |
| REQ-V3-032 | 签名按语义族表达且语言无关（一个签名覆盖多语言同源缺陷） | 开发中 |  |
| REQ-V3-033 | v2.1 security_profiles.json 规则转写为语义签名（方法名→语义族），作为签名库种子 | 开发中 |  |
| REQ-V3-034 | signature_matcher 沿调用图展开窗口（默认深度 3，可配）并对窗口内调用点匹配签名 hints | 已完成 |  |
| REQ-V3-035 | 签名命中生成 hypothesis（含语义家族+检查清单+sink 提示），不直接生成候选 | 已完成 |  |
| REQ-V3-036 | 同 surface×签名 命中合并去重 | 已完成 |  |
| REQ-V3-037 | LLM 快速筛选假设（排除常量/白名单场景）后再入 R3 | 已完成 |  |
| REQ-V3-038 | LOGIC_PATTERN 类签名（授权谓词弱化/修复-再暴露）独立匹配，不依赖污点链 | 已完成 |  |
| REQ-V3-040 | verifier 任务书强制每跳调用边 grep 证据（call_chain 相邻两跳附调用点证明） | 已完成 |  |
| REQ-V3-041 | evidence_grade 三级：static_only < edge_proven < empirically_confirmed | 已完成 |  |
| REQ-V3-042 | REACHABLE 且 static_only 的候选不得进入可申报清单 | 已完成 |  |
| REQ-V3-043 | 前提维度检查：platform_precondition 必须附 platform_evidence（CI matrix/平台声明） | 已完成 |  |
| REQ-V3-044 | trust_boundary 逐通道验证"远端数据确实无法流入"，禁止惯例假设 | 已完成 |  |
| REQ-V3-045 | 可降级配置门控（gate）显式记录于 verdict | 已完成 |  |
| REQ-V3-046 | 死代码豁免：blocking_point="no production callers" 是合法阻断，不强制 3 层链 | 已完成 |  |
| REQ-V3-047 | 簇级验证官方化：cluster_id + 簇级 verdict 广播 + 簇成员共享证据 | 已完成 |  |
| REQ-V3-048 | 子智能体任务书强制输出 JSON 且必须本地 json.load 校验通过后方可提交 | 已完成 |  |
| REQ-V3-049 | 子智能体心跳：任务开始先写 pending 占位（含 started_at），主代理可判"在跑/丢失" | 已完成 |  |
| REQ-V3-050 | 落盘冲突检测：目标文件已存在且非本人 pending → 追加 .agent-<id> 后缀，禁止静默覆盖 | 已完成 |  |
| REQ-V3-051 | 证伪回溯闭环：R5 证伪 → verifier 错误记录 + 候选降级 + 任务书反例注入 | 已完成 |  |
| REQ-V3-053 | 保留 H1-H6 六类假说（每类三选一 verdict） | 未开发 |  |
| REQ-V3-054 | 新增 H7 信任边界专项（同 UID/IPC 高危操作、路径语义越界、鉴权谓词弱化） | 未开发 |  |
| REQ-V3-055 | R4 规模自适应档位：小项目 3×2 / 大项目 6 / 战役模式 1×6 + r4_consolidated 标注 | 未开发 |  |
| REQ-V3-056 | R4 发现推翻 R3 结论时回写 superseded_by 标记 | 未开发 |  |
| REQ-V3-060 | 触发判定：crash/OOM/无界/XSS/协议 DoS 声称且 grade < empirically_confirmed → 强制实证 | 已完成 |  |
| REQ-V3-061 | harness 模板库含至少 4 个模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/multipart_align） | 已完成 |  |
| REQ-V3-062 | harness 执行包含时序采样（RSS/存活/exit code）与结果采集 | 已完成 |  |
| REQ-V3-063 | 实测确认 → empirically_confirmed；证伪 → 回溯修正（同 REQ-V3-051） | 已完成 |  |
| REQ-V3-064 | harness 结果附环境记录（工具链版本/依赖/端口）确保可复现 | 已完成 |  |
| REQ-V3-070 | 核心指标：输入面覆盖率、证据分级分布、实证验证率、verdict 修正记录 | 已完成 |  |
| REQ-V3-071 | 输入面覆盖率门禁 =100%（同 v2.1 PENDING 清零语义） | 开发中 |  |
| REQ-V3-072 | SDR/SNR 降为参考指标；新增签名命中→真实候选转化率（噪音自检，>80% 提示修整） | 开发中 |  |
| REQ-V3-073 | NEEDS_REVIEW 显式列出，不允许静默丢弃 | 已完成 |  |
| REQ-V3-080 | collect 按字面候选 id 匹配（接受任意前缀），不再强制拼接 CAND- | 已完成 |  |
| REQ-V3-081 | ast_scanner 入队为 merge 语义，禁止覆写既有队列 | 已完成 |  |
| REQ-V3-082 | assert 与 collect 校验规则统一（UNREACHABLE blocking_point 前置校验，允许 "N/A"/"no production callers"） | 已完成 |  |
| REQ-V3-083 | batch size 可配置 + --group-by-file 聚合模式 | 已完成 |  |
| REQ-V3-084 | R4 内置 collect/assert/report stage | 已完成 |  |
| REQ-V3-085 | collect 容错 JSON 加载（非法转义修复后重试） | 已完成 |  |
| REQ-V3-086 | 候选入队填充 source_pattern/language 字段 | 已完成 |  |
| REQ-V3-087 | 路径过滤按语言映射表（spec/tst/*_tests.rs/.Tests/*.spec.ts） | 已完成 |  |
| REQ-V3-088 | 指标口径修正：avg_depth 只统计有深度候选；NEEDS_REVIEW 单独计数 | 已完成 |  |
| REQ-V3-089 | 同点跨 CWE 关联标注（related_candidates），维度拆分裁决互引 | 未开发 |  |
| REQ-V3-090 | 平台兼容层新增 Mode W：Workflow 工具可用时，R1/R2/R3 批处理以确定性 workflow 脚本执行（loop-until-dry + schema 校验自动重试 + resumeFromRunId 断点续传）；Mode A' 手工循环保留为降级路径 | 已完成 |  |
| REQ-V3-091 | batch_verify 提供 `--stage workflow-script`：从当前队列导出 workflow 脚本（dequeue→verify→collect 循环，journal 记账） | 已完成 |  |
| REQ-V3-092 | 候选增加 attempt 计数与 escalated 终态：单候选 ≥3 次验证失败自动升级主代理裁决，不得静默无限重试 | 已完成 |  |
| REQ-V3-093 | 对账门禁：任务清单（已派发）与产出清单（文件+journal）零差异方可关闭队列；缺失任务自动重派（有上限） | 已完成 |  |
| REQ-V3-094 | 独立复核：REACHABLE 且 grade≥edge_proven 的候选经 N=2 证伪者多数决复核（task_templates/verifier_refutation.md） | 已完成 |  |
| REQ-V3-095 | 输入面覆盖率门禁：surface 总数 vs 已追踪 surface =100% 才允许关闭队列（REQ-V3-071 的编排层执行） | 已完成 |  |
| REQ-V3-096 | assert_ledger 扩展：在既有四门禁基础上增加 对账零差异 / escalated=0 或主代理签收 / surface 覆盖 100% | 已完成 |  |

## 软件需求（SWR-V3）（共 54 条）

| 编号 | 需求 | 状态 | 备注 |
|---|---|---|---|
| SWR-V3-001 | 实现 `build_architecture_context(project_root)`：从 README/依赖清单/构建文件提取 {lang, deps[], entry_hints[], maturity} | 已完成 |  |
| SWR-V3-002 | 实现 `gen_surface_tasks()`：按 network/data/process/storage 4 域生成任务书，任务书含架构背景字段 | 已完成 |  |
| SWR-V3-003 | 实现 `validate_surfaces()`：entry_points 非空 + evidence 含 file:line 与 snippet + 源码行模糊匹配校验 | 已完成 |  |
| SWR-V3-004 | trust_boundary/confidence 枚举校验 | 已完成 |  |
| SWR-V3-005 | 实现 `merge_surfaces()`：同 entry_point 多域归属合并、冲突标注 conflicts[] | 已完成 |  |
| SWR-V3-010 | 定义签名 schema（sig_id/semantic/cwe/platform_profiles/detection_hints/known_instances/empirical_harness）并附 schema 校验器 | 已完成 |  |
| SWR-V3-011 | 新增签名强制 known_instances 非空（校验拒绝空实例签名） | 已完成 |  |
| SWR-V3-012 | 初版签名库：v2.1 security_profiles.json 转写 + 本战役 33 个确认家族回填（至少含 SIG-BUFFER-ACCUM-001 跨 3 语言实例） | 开发中 |  |
| SWR-V3-013 | 冒烟测试：每签名取 1 个 known_instance 在源码副本上验证 hints 可命中，命中率 <100% 阻止启动 | 已完成 |  |
| SWR-V3-020 | 实现 ProjectIndex 构建（{callee_name: [caller_sites]} 全库索引） | 已完成 |  |
| SWR-V3-021 | 实现 `expand_window(entry, depth=3)` 沿调用图展开窗口 | 已完成 |  |
| SWR-V3-022 | 实现 `match_signatures()`：窗口内调用点源码行跑 detection_hints.grep，产出 Hit{surface_id,sig_id,site,pattern} | 已完成 |  |
| SWR-V3-023 | 实现 `gen_hypotheses()`：同 surface×sig 去重、附 checklist 与 semantic_family、生成 HYP-xxx | 已完成 |  |
| SWR-V3-024 | 实现 `emit_filter_tasks()`：批量 LLM 快速筛选任务书（排除常量/白名单/死代码） | 已完成 |  |
| SWR-V3-025 | LOGIC_PATTERN 类签名独立匹配队列（不依赖污点链） | 已完成 |  |
| SWR-V3-030 | 实现 `grade_verdict()`：三级分级规则（REACHABLE 无逐跳 edge_evidence → static_only；empirical 非空 → empirically_confirmed） | 已完成 |  |
| SWR-V3-031 | 边证据校验：edge_evidence 每项含 edge 与 proof 文本，缺 proof 拒收 | 已完成 |  |
| SWR-V3-032 | 实现 `check_preconditions()`：platform_precondition 需 platform_evidence；trust_boundary 需逐通道验证记录；gate 记录 | 已完成 |  |
| SWR-V3-033 | 实现 `commit()`：merge 语义写回 + correction_record 追加 | 已完成 |  |
| SWR-V3-034 | 实现 `assert_ledger()`：无 PENDING / REACHABLE 无 static_only / 实证类声称 100% empirically_confirmed / H1-H7 全 VERIFIED | 已完成 |  |
| SWR-V3-040 | 实现 `needs_harness()`：claim ∈ EMPIRICAL_CLAIMS 且 grade < empirically_confirmed 触发 | 已完成 |  |
| SWR-V3-041 | 内置 4 模板：ws_frame_alloc / ws_frame_accum / xss_path_sim / multipart_align（攻击脚本+判据+环境字段） | 已完成 |  |
| SWR-V3-042 | 实现时序采样：/proc/<pid>/status VmRSS 每秒采样 + kill -0 存活 + exit code 采集 | 已完成 |  |
| SWR-V3-043 | 采样协议含投递速率确认步骤（先慢速采样，以服务器实测到达量为准） | 已完成 |  |
| SWR-V3-044 | 实现 `apply_result()`：confirmed→empirically_confirmed；refuted→correction_record+降级+superseded_by | 已完成 |  |
| SWR-V3-045 | 环境记录：工具链版本/依赖/端口/沙箱限流备注写入结果 | 已完成 |  |
| SWR-V3-050 | collect 按字面候选 id 匹配（接受 R05-* 等任意前缀） | 已完成 |  |
| SWR-V3-051 | 全部入队阶段 merge 语义（r05/r1/r15/collect 不覆写既有候选） | 已完成 |  |
| SWR-V3-052 | collect/assert 共用 _validate_verdict_payload；UNREACHABLE 允许 blocking_point ∈ {"N/A","no production callers"} | 已完成 |  |
| SWR-V3-053 | `--stage next-cluster`（file×sink 聚合任务书）+ `--cluster <id>` 广播 + clustered_verified 标记 | 已完成 |  |
| SWR-V3-054 | `--batch-size N` 与 `--group-by-file` 参数 | 已完成 |  |
| SWR-V3-055 | `--stage r4-collect / r4-assert / report` | 已完成 |  |
| SWR-V3-056 | JSON 容错加载（非法转义修复重试；失败记 errors 不丢批） | 已完成 |  |
| SWR-V3-057 | 入队填充 source_pattern/language（按扩展名推断） | 已完成 |  |
| SWR-V3-058 | 任务书心跳契约：先写 <out>.pending（含 started_at）；collect 产出对账；落盘冲突加 .agent-<id> 后缀 | 已完成 |  |
| SWR-V3-059 | 死代码豁免：blocking_point="no production callers" 不触发 depth 门禁降级 | 已完成 |  |
| SWR-V3-060 | `--cross-tags` 用 git merge-base --is-ancestor 生成"修复 commit × tag"矩阵 | 已完成 |  |
| SWR-V3-061 | 无 .git → 输出 {"status":"NO_GIT"} | 已完成 |  |
| SWR-V3-062 | HEAD 审计自动"变体复核"任务书模式 | 已完成 |  |
| SWR-V3-063 | 默认落盘 JSON（-o 可选） | 已完成 |  |
| SWR-V3-064 | grep 词表分级（security vs fix 两组，噪声占比可配） | 已完成 |  |
| SWR-V3-070 | LANG_TEST_PATH_MAP 语言映射过滤（ruby/powershell/rust/ts 5 形态） | 已完成 |  |
| SWR-V3-071 | `--mode deep`（tree-sitter 佐证模式，非默认路径） | 开发中 |  |
| SWR-V3-072 | `--noise-check`：按 sink_type 抽样误报率，>80% 自动降权并提示 | 已完成 |  |
| SWR-V3-073 | 入队 merge 语义（不覆写队列） | 已完成 |  |
| SWR-V3-080 | surface_map_domain.md（4 域变体，含背景/证据强制/产出 schema） | 已完成 |  |
| SWR-V3-081 | hypothesis_filter.md（排除判据：常量/白名单/死代码） | 已完成 |  |
| SWR-V3-082 | verifier_edge_proof.md（边证据要求/前提维度/死代码豁免/分级规则） | 已完成 |  |
| SWR-V3-083 | biz_hypothesis.md（H1-H7，含 H7 信任边界检查项） | 已完成 |  |
| SWR-V3-084 | empirical_test.md（采样协议/环境记录/判据） | 已完成 |  |
| SWR-V3-085 | 全部模板尾部含 self_json_guard（json.load 校验后提交） | 已完成 |  |
| SWR-V3-090 | 端到端数据流可用：surface→hypothesis→queue→assert→report 单项目跑通 | 已完成 |  |
| SWR-V3-091 | 回归验证：sinatra/lighttpd/actix 三个已审计项目复跑，结论与已知对照（Phase 3 判据） | 未开发 |  |
| SWR-V3-092 | 全部新组件附单测（tests/ 下 test_<module>.py） | 已完成 |  |

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
| REQ-V3.1-100 | 三项目复跑对照（akka-http/etcd/actix-web）验收：① R3.5 拦截率较战役基线下降 ② 原 REACHABLE 结论零丢失 ③ 六门禁全 PASS | 已完成 |  |
| REQ-V3.1-101 | 验收通过后合并 main 并 install 到 skill 目录；未通过不得覆盖 v3 运行时 | 已完成 |  |

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

---

## v3.2 增量（REQ-V3.2 共 17 条 / SWR-V3.2 共 18 条）

> 完整规格见 REQ_V3_2.md / SWR_V3_2.md。设计完成（2026-08-17），开发未开始。

### 系统需求（REQ-V3.2）状态汇总

| 编号段 | 主题 | 状态 |
|---|---|---|
| REQ-V3.2-001~005 | 语言维度（inventory/候选级 lang/词族过滤/手册装载） | 开发完成 |
| REQ-V3.2-010~014 | FFI 边界域（第五域/cross_evidence/CK-FFI/PREC-MULTI-LANG） | 开发完成（cross_evidence 落盘为流程义务，报告条款入 SKILL） |
| REQ-V3.2-020~024 | R3.5-N 复活攻击（抽样/裁决/模式/门禁/任务书） | 开发完成 |
| REQ-V3.2-030~031 | 验收缺陷制度化（分级条款/关键词回填流程） | 开发完成（031 的关键词回填以回归测试追加为判据） |
| REQ-V3.2-040~041 | 报告语言覆盖表/FFI 边界表 | 开发完成（SKILL 条款） |
| REQ-V3.2-100~102 | Phase 3.2.3 验收（混合试审/零回退回归/install） | 已经完成开发（fixture 4/5+1 证伪、Lersosa 三判据 PASS 六门禁 51/51、akka 零回退、install 完成） |

### 软件需求（SWR-V3.2）状态汇总

全部 21 条已完成（2026-08-17）；剩余义务 = Phase 3.2.3 验收

---

## v3.2.1 增量（REQ-V3.2.1 共 17 条 / SWR-V3.2.1 共 20 条）

> 完整规格见 REQ_V3_2_1.md / SWR_V3_2_1.md。设计完成（2026-08-17），验收暴露四缺陷的修复版。

### 系统需求（REQ-V3.2.1）状态汇总

| 编号段 | 主题 | 状态 |
|---|---|---|
| REQ-V3.2.1-001~005 | target_kind 判定与按型装载 | 开发完成（fixture→library、Lersosa→application 实测） |
| REQ-V3.2.1-010~013 | verifier 两盲区制度化（可导入性/中间层枚举） | 开发完成（任务书三段 + CK 22/23 + PREC 21/22） |
| REQ-V3.2.1-020~021 | 判据①措辞 + 组件角色列 | 开发完成 |
| REQ-V3.2.1-030~032 | shipped-config 前置化 + r4_feedback | 开发完成（r4_feedback 历史回放检出 CAND-008 tls 冲突） |
| REQ-V3.2.1-040~042 | Phase 3.2.1.3 验收 | 进行中 |

### 软件需求（SWR-V3.2.1）状态汇总

| 模块 | 条目数 | 状态 |
|---|---|---|
| M1 target_kind | 4 | 已经完成开发 |
| M2 verifier 三段 | 3 | 已经完成开发 |
| M3 shipped-config workflow | 2 | 已经完成开发 |
| M4 清单/先例库 | 4 | 已经完成开发 |
| M5 evidence_ledger | 1 | 已经完成开发 |
| M6 r2_guard | 1 | 已经完成开发 |
| M7 组件角色 | 1 | 已经完成开发 |
| M8 SKILL/报告/判据 | 2 | 已经完成开发 |
| M9 测试 | 2 | 已经完成开发（90/90 全绿） |
