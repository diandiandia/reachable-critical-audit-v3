# Reachable Critical Audit v3 — 系统需求规格书（System Requirements）

> **文档性质**：从 `SYSTEM_DESIGN_V3.md` 导出的系统开发需求。每条附来源追溯（设计章节/组件 ID）与验收判据。
> 需求状态追踪见 `REQUIREMENTS_TRACKING.md`。
> **日期**：2026-08-16
> **优先级定义**：P0 = 影响结论正确性/可问责性；P1 = 影响效率/可用性；P2 = 增强项

## 1. 总体与架构需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-001 | 系统主分析引擎为 LLM 子智能体（测绘/回溯/判断），规则库仅作提示器，不作为判定器 | §1 P1/P2 | P0 | 任一阶段无"规则命中即判定"路径 |
| REQ-V3-002 | 审计起点为输入面测绘（input_surface.json），禁止全库规则轰炸作为默认路径 | §1 P3、§4 R1 | P0 | 默认流程中 ast_scanner 全库扫描不可达 |
| REQ-V3-003 | 每个 verdict 必须携带证据类型（evidence_grade）与来源，不得存在无证据断言 | §1 P4、§3.3 | P0 | 队列中 100% verdict 有 evidence_grade |
| REQ-V3-004 | DoS/崩溃/内存/无界类声称必须经实证抽验（R5）确认后方可申报 | §1 P5、§4 R5 | P0 | 该类声称 empirically_confirmed 率=100% |
| REQ-V3-005 | 系统无 LLM API 之外的新技术依赖 | §8 | P1 | 依赖清单仅含 python3/tree-sitter/LLM 编排原语 |
| REQ-V3-006 | 全流程产物（队列/测绘/假设/报告）可问责：每个结论可追溯到证据文件 | §1 P6 | P0 | 报告任一 finding 可回查证据链 |
| REQ-V3-007 | 兼容 Mode A'（Agent 工具）为默认执行模式 | §2 | P0 | 单平台即可跑通全阶段 |

## 2. R0/R0.5 需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-010 | R0 自检包含签名库冒烟测试：每个签名必须至少有 1 个 known_instance 可复现 | §3.4、D-COMP-02 | P0 | 冒烟失败阻止启动 |
| REQ-V3-011 | R0 自检检查 harness 执行器可用性（R5 前置） | D-COMP-05 | P1 | 不可用则 R5 阶段降级并告警 |
| REQ-V3-012 | R0.5 支持 `--cross-tags t1,t2,...` 输出"修复 commit 是否在各 tag"矩阵 | §4 R0.5、D-COMP-07 | P1 | AWStats 式三 tag 交叉可用脚本化完成 |
| REQ-V3-013 | R0.5 对无 git 历史输出 NO_GIT 状态而非误导性文本 | D-COMP-07 | P1 | 输出 `{"status":"NO_GIT"}` |
| REQ-V3-014 | R0.5 对 HEAD 审计自动切换"修复变体复核"模式（修复已在树，价值在兄弟路径残留复核） | §4 R0.5 | P1 | 任务书为变体复核形态 |
| REQ-V3-015 | R0.5 默认落盘 JSON（-o 可选而非必需） | D-COMP-07 | P1 | 无 -o 也有产物文件 |
| REQ-V3-016 | R0.5 grep 词表分级：security 关键词与通用 fix 词分开，噪声可控 | D-COMP-07 | P1 | 噪声 commit 占比可配置阈值 |

## 3. R1 输入面测绘需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-020 | surface_mapper 按 4 域（网络/数据/进程/存储）生成测绘任务书 | §4 R1、D-COMP-01 | P0 | 每域 1 份任务书 |
| REQ-V3-021 | 测绘任务书必须携带项目背景（架构线索：README/依赖清单/构建文件摘要） | §4 R1 | P0 | 任务书含背景字段且非空 |
| REQ-V3-022 | 每个 surface 必须附 entry_points 源码证据（file:line + 代码片段） | §3.1、§4 R1 | P0 | 校验失败拒收 |
| REQ-V3-023 | 每个 surface 必须记录 trust_boundary（未认证远程/受信通道/gate） | §3.1 | P0 | 字段存在且枚举合法 |
| REQ-V3-024 | surface 携带 downstream_hints（下游可能到达的功能面提示） | §3.1 | P1 | 供 R2 定向 |
| REQ-V3-025 | 多 agent 测绘产出合并去重（同 entry_point 多域归属、冲突标注） | D-COMP-01 | P1 | 合并后无重复 entry_point |
| REQ-V3-026 | 测绘产出经主 Agent 复核后生效 | §4 R1 | P0 | input_surface.json 有复核标记 |

## 4. R2 签名库与假设生成需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-030 | 签名库 schema 含语义族描述、CWE、平台 profile、grep hints、检查清单、known_instances、harness 关联 | §3.4、D-COMP-02 | P0 | schema 校验通过 |
| REQ-V3-031 | 新增签名必须携带至少 1 个真实审计实例（known_instances 非空），禁止凭空造签名 | §3.4 | P0 | 校验强制 |
| REQ-V3-032 | 签名按语义族表达且语言无关（一个签名覆盖多语言同源缺陷） | §3.4 | P0 | 至少 1 个签名覆盖 ≥2 语言实例 |
| REQ-V3-033 | v2.1 security_profiles.json 规则转写为语义签名（方法名→语义族），作为签名库种子 | §6 迁移表 | P1 | 转写清单齐备 |
| REQ-V3-034 | signature_matcher 沿调用图展开窗口（默认深度 3，可配）并对窗口内调用点匹配签名 hints | §4 R2、D-COMP-03 | P0 | 窗口外代码不参与匹配 |
| REQ-V3-035 | 签名命中生成 hypothesis（含语义家族+检查清单+sink 提示），不直接生成候选 | §3.2、§4 R2 | P0 | 队列对象为 HYP-xxx |
| REQ-V3-036 | 同 surface×签名 命中合并去重 | D-COMP-03 | P1 | 无重复假设 |
| REQ-V3-037 | LLM 快速筛选假设（排除常量/白名单场景）后再入 R3 | §4 R2 | P1 | 筛选题任务书可用 |
| REQ-V3-038 | LOGIC_PATTERN 类签名（授权谓词弱化/修复-再暴露）独立匹配，不依赖污点链 | §4 R2 | P0 | 该类假设独立生成 |

## 5. R3 证据链回溯需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-040 | verifier 任务书强制每跳调用边 grep 证据（call_chain 相邻两跳附调用点证明） | §4 R3、D-COMP-04 | P0 | 缺证据自动降级 static_only |
| REQ-V3-041 | evidence_grade 三级：static_only < edge_proven < empirically_confirmed | §3.3 | P0 | 分级枚举合法 |
| REQ-V3-042 | REACHABLE 且 static_only 的候选不得进入可申报清单 | §3.3、§5 | P0 | 断言强制 |
| REQ-V3-043 | 前提维度检查：platform_precondition 必须附 platform_evidence（CI matrix/平台声明） | §4 R3 | P0 | 无证据→NEEDS_REVIEW |
| REQ-V3-044 | trust_boundary 逐通道验证"远端数据确实无法流入"，禁止惯例假设 | §4 R3 | P0 | 任务书含该准则 |
| REQ-V3-045 | 可降级配置门控（gate）显式记录于 verdict | §4 R3 | P1 | gate 字段存在 |
| REQ-V3-046 | 死代码豁免：blocking_point="no production callers" 是合法阻断，不强制 3 层链 | §4 R3 | P1 | 不再产生凑数链 |
| REQ-V3-047 | 簇级验证官方化：cluster_id + 簇级 verdict 广播 + 簇成员共享证据 | §4 R3、lessons 2.1 | P0 | 簇级 collect/assert 可用 |
| REQ-V3-048 | 子智能体任务书强制输出 JSON 且必须本地 json.load 校验通过后方可提交 | D-COMP-04 | P1 | 格式损坏率降至 0 |
| REQ-V3-049 | 子智能体心跳：任务开始先写 pending 占位（含 started_at），主代理可判"在跑/丢失" | lessons 1.4 | P1 | 心跳文件存在 |
| REQ-V3-050 | 落盘冲突检测：目标文件已存在且非本人 pending → 追加 .agent-<id> 后缀，禁止静默覆盖 | lessons 1.4 | P1 | 无双写竞态 |
| REQ-V3-051 | 证伪回溯闭环：R5 证伪 → verifier 错误记录 + 候选降级 + 任务书反例注入 | §4 R5 | P0 | correction_record 落盘 |

## 6. R4 业务假说需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-053 | 保留 H1-H6 六类假说（每类三选一 verdict） | §4 R4 | P0 | H1-H6 全部 VERIFIED |
| REQ-V3-054 | 新增 H7 信任边界专项（同 UID/IPC 高危操作、路径语义越界、鉴权谓词弱化） | §4 R4 | P0 | H7 存在且 VERIFIED |
| REQ-V3-055 | R4 规模自适应档位：小项目 3×2 / 大项目 6 / 战役模式 1×6 + r4_consolidated 标注 | §4 R4 | P1 | 档位自动选择 |
| REQ-V3-056 | R4 发现推翻 R3 结论时回写 superseded_by 标记 | §4 R4 | P1 | 报告带修正记录 |

## 7. R5 实证抽验需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-060 | 触发判定：crash/OOM/无界/XSS/协议 DoS 声称且 grade < empirically_confirmed → 强制实证 | D-COMP-05 | P0 | 触发判定函数可用 |
| REQ-V3-061 | harness 模板库含至少 4 个模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/multipart_align） | §4 R5 | P1 | 模板注册齐备 |
| REQ-V3-062 | harness 执行包含时序采样（RSS/存活/exit code）与结果采集 | D-COMP-05 | P0 | 采样数据落盘 |
| REQ-V3-063 | 实测确认 → empirically_confirmed；证伪 → 回溯修正（同 REQ-V3-051） | D-COMP-05 | P0 | 结果写回队列 |
| REQ-V3-064 | harness 结果附环境记录（工具链版本/依赖/端口）确保可复现 | D-COMP-05 | P1 | 环境字段齐备 |

## 8. 指标与报告需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-070 | 核心指标：输入面覆盖率、证据分级分布、实证验证率、verdict 修正记录 | §5 | P0 | 报告含全部核心指标 |
| REQ-V3-071 | 输入面覆盖率门禁 =100%（同 v2.1 PENDING 清零语义） | §5 | P0 | 断言强制 |
| REQ-V3-072 | SDR/SNR 降为参考指标；新增签名命中→真实候选转化率（噪音自检，>80% 提示修整） | §5 | P1 | 指标定义齐备 |
| REQ-V3-073 | NEEDS_REVIEW 显式列出，不允许静默丢弃 | §5 | P0 | 报告含清单 |

## 9. 工具链通用需求（v2.1 工程修复迁移）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-080 | collect 按字面候选 id 匹配（接受任意前缀），不再强制拼接 CAND- | lessons C1 | P0 | R05-* 等 id 可 collect |
| REQ-V3-081 | ast_scanner 入队为 merge 语义，禁止覆写既有队列 | lessons C2 | P0 | R0.5 候选不被冲掉 |
| REQ-V3-082 | assert 与 collect 校验规则统一（UNREACHABLE blocking_point 前置校验，允许 "N/A"/"no production callers"） | lessons C3 | P0 | 无手工回填 |
| REQ-V3-083 | batch size 可配置 + --group-by-file 聚合模式 | lessons C5 | P1 | 参数生效 |
| REQ-V3-084 | R4 内置 collect/assert/report stage | lessons C6 | P1 | --stage r4-* 可用 |
| REQ-V3-085 | collect 容错 JSON 加载（非法转义修复后重试） | lessons C7 | P1 | 损坏文件可恢复 |
| REQ-V3-086 | 候选入队填充 source_pattern/language 字段 | lessons C8 | P1 | 无 '?' 字段 |
| REQ-V3-087 | 路径过滤按语言映射表（spec/tst/*_tests.rs/.Tests/*.spec.ts） | lessons A7 | P0 | 5 形态全拦截 |
| REQ-V3-088 | 指标口径修正：avg_depth 只统计有深度候选；NEEDS_REVIEW 单独计数 | lessons C11 | P1 | 口径一致 |
| REQ-V3-089 | 同点跨 CWE 关联标注（related_candidates），维度拆分裁决互引 | lessons C12 | P2 | 关联字段存在 |
## 10. 编排与验证完整性需求（2026-08-16 新增，来源 WORKFLOW_EVAL.md）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3-090 | 平台兼容层新增 Mode W：Workflow 工具可用时，R1/R2/R3 批处理以确定性 workflow 脚本执行（loop-until-dry + schema 校验自动重试 + resumeFromRunId 断点续传）；Mode A' 手工循环保留为降级路径 | WE §2.2 | P0 | 同一队列两种模式可跑通 |
| REQ-V3-091 | batch_verify 提供 `--stage workflow-script`：从当前队列导出 workflow 脚本（dequeue→verify→collect 循环，journal 记账） | WE §4.1 | P0 | 脚本可从真实队列生成且语义等价 |
| REQ-V3-092 | 候选增加 attempt 计数与 escalated 终态：单候选 ≥3 次验证失败自动升级主代理裁决，不得静默无限重试 | WE §3.2-G2 | P0 | 坏任务书候选 3 次后进 escalated |
| REQ-V3-093 | 对账门禁：任务清单（已派发）与产出清单（文件+journal）零差异方可关闭队列；缺失任务自动重派（有上限） | WE §3.2-G1/§3.3 | P0 | 模拟失联任务被检出 |
| REQ-V3-094 | 独立复核：REACHABLE 且 grade≥edge_proven 的候选经 N=2 证伪者多数决复核（task_templates/verifier_refutation.md） | WE §3.2-G3 | P1 | 复核模板可用且结论落盘 |
| REQ-V3-095 | 输入面覆盖率门禁：surface 总数 vs 已追踪 surface =100% 才允许关闭队列（REQ-V3-071 的编排层执行） | WE §3.2-G4 | P0 | 漏 surface 时队列不可关闭 |
| REQ-V3-096 | assert_ledger 扩展：在既有四门禁基础上增加 对账零差异 / escalated=0 或主代理签收 / surface 覆盖 100% | WE §3.3 | P0 | 六门禁全部可触发 |
