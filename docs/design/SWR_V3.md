# Reachable Critical Audit v3 — 软件开发需求（Software Requirements）

> **文档性质**：从 `SW_DESIGN_V3.md` 导出的软件级开发需求。每条附"满足"列追溯系统需求（REQ-V3）。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`。**日期**：2026-08-16

## M1 surface_mapper.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-001 | 实现 `build_architecture_context(project_root)`：从 README/依赖清单/构建文件提取 {lang, deps[], entry_hints[], maturity} | REQ-V3-021 | 对 sinatra/actix 各产出非空 context |
| SWR-V3-002 | 实现 `gen_surface_tasks()`：按 network/data/process/storage 4 域生成任务书，任务书含架构背景字段 | REQ-V3-020/021 | 每域 1 份、背景非空 |
| SWR-V3-003 | 实现 `validate_surfaces()`：entry_points 非空 + evidence 含 file:line 与 snippet + 源码行模糊匹配校验 | REQ-V3-022 | 缺证据样例被拒收 |
| SWR-V3-004 | trust_boundary/confidence 枚举校验 | REQ-V3-023 | 非法值报错 |
| SWR-V3-005 | 实现 `merge_surfaces()`：同 entry_point 多域归属合并、冲突标注 conflicts[] | REQ-V3-025 | 合并后无重复、冲突可见 |

## M2 signature_library.json

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-010 | 定义签名 schema（sig_id/semantic/cwe/platform_profiles/detection_hints/known_instances/empirical_harness）并附 schema 校验器 | REQ-V3-030 | 校验器可运行 |
| SWR-V3-011 | 新增签名强制 known_instances 非空（校验拒绝空实例签名） | REQ-V3-031 | 空实例签名被拒 |
| SWR-V3-012 | 初版签名库：v2.1 security_profiles.json 转写 + 本战役 33 个确认家族回填（至少含 SIG-BUFFER-ACCUM-001 跨 3 语言实例） | REQ-V3-032/033 | 转写清单齐备、多语言签名存在 |
| SWR-V3-013 | 冒烟测试：每签名取 1 个 known_instance 在源码副本上验证 hints 可命中，命中率 <100% 阻止启动 | REQ-V3-010 | 冒烟报告含 per-sig 命中 |

## M3 signature_matcher.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-020 | 实现 ProjectIndex 构建（{callee_name: [caller_sites]} 全库索引） | REQ-V3-034 | 索引构建完成 |
| SWR-V3-021 | 实现 `expand_window(entry, depth=3)` 沿调用图展开窗口 | REQ-V3-034 | 深度 3 窗口正确（对照已知链验证） |
| SWR-V3-022 | 实现 `match_signatures()`：窗口内调用点源码行跑 detection_hints.grep，产出 Hit{surface_id,sig_id,site,pattern} | REQ-V3-034 | 窗口外代码零命中 |
| SWR-V3-023 | 实现 `gen_hypotheses()`：同 surface×sig 去重、附 checklist 与 semantic_family、生成 HYP-xxx | REQ-V3-035/036 | 无重复假设 |
| SWR-V3-024 | 实现 `emit_filter_tasks()`：批量 LLM 快速筛选任务书（排除常量/白名单/死代码） | REQ-V3-037 | 任务书含排除判据 |
| SWR-V3-025 | LOGIC_PATTERN 类签名独立匹配队列（不依赖污点链） | REQ-V3-038 | 该类假设独立生成 |

## M4 evidence_ledger.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-030 | 实现 `grade_verdict()`：三级分级规则（REACHABLE 无逐跳 edge_evidence → static_only；empirical 非空 → empirically_confirmed） | REQ-V3-041/042 | 规则单测通过 |
| SWR-V3-031 | 边证据校验：edge_evidence 每项含 edge 与 proof 文本，缺 proof 拒收 | REQ-V3-040 | 缺 proof 样例报错 |
| SWR-V3-032 | 实现 `check_preconditions()`：platform_precondition 需 platform_evidence；trust_boundary 需逐通道验证记录；gate 记录 | REQ-V3-043/044/045 | 三类 Issue 均可触发 |
| SWR-V3-033 | 实现 `commit()`：merge 语义写回 + correction_record 追加 | REQ-V3-051 | 证伪写回可查 |
| SWR-V3-034 | 实现 `assert_ledger()`：无 PENDING / REACHABLE 无 static_only / 实证类声称 100% empirically_confirmed / H1-H7 全 VERIFIED | REQ-V3-070/071 | 门禁违规样例全部报出 |

## M5 harness_runner.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-040 | 实现 `needs_harness()`：claim ∈ EMPIRICAL_CLAIMS 且 grade < empirically_confirmed 触发 | REQ-V3-060 | 判定函数单测通过 |
| SWR-V3-041 | 内置 4 模板：ws_frame_alloc / ws_frame_accum / xss_path_sim / multipart_align（攻击脚本+判据+环境字段） | REQ-V3-061 | 模板注册齐备 |
| SWR-V3-042 | 实现时序采样：/proc/<pid>/status VmRSS 每秒采样 + kill -0 存活 + exit code 采集 | REQ-V3-062 | 采样数据落盘 |
| SWR-V3-043 | 采样协议含投递速率确认步骤（先慢速采样，以服务器实测到达量为准） | REQ-V3-062 | 协议文本入模板 |
| SWR-V3-044 | 实现 `apply_result()`：confirmed→empirically_confirmed；refuted→correction_record+降级+superseded_by | REQ-V3-063/051 | 两条路径单测通过 |
| SWR-V3-045 | 环境记录：工具链版本/依赖/端口/沙箱限流备注写入结果 | REQ-V3-064 | 结果含环境字段 |

## M6 batch_verify.py（v2.1 迁移改造）

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-050 | collect 按字面候选 id 匹配（接受 R05-* 等任意前缀） | REQ-V3-080 | R05-* id 可 collect |
| SWR-V3-051 | 全部入队阶段 merge 语义（r05/r1/r15/collect 不覆写既有候选） | REQ-V3-081 | 重跑扫描不丢 R05 候选 |
| SWR-V3-052 | collect/assert 共用 _validate_verdict_payload；UNREACHABLE 允许 blocking_point ∈ {"N/A","no production callers"} | REQ-V3-082 | 无手工回填 |
| SWR-V3-053 | `--stage next-cluster`（file×sink 聚合任务书）+ `--cluster <id>` 广播 + clustered_verified 标记 | REQ-V3-047 | 簇级流程可用 |
| SWR-V3-054 | `--batch-size N` 与 `--group-by-file` 参数 | REQ-V3-083 | 参数生效 |
| SWR-V3-055 | `--stage r4-collect / r4-assert / report` | REQ-V3-084 | 三 stage 可用 |
| SWR-V3-056 | JSON 容错加载（非法转义修复重试；失败记 errors 不丢批） | REQ-V3-085 | 损坏样例可恢复 |
| SWR-V3-057 | 入队填充 source_pattern/language（按扩展名推断） | REQ-V3-086 | 无 '?' 字段 |
| SWR-V3-058 | 任务书心跳契约：先写 <out>.pending（含 started_at）；collect 产出对账；落盘冲突加 .agent-<id> 后缀 | REQ-V3-049/050 | 冲突检测可演示 |
| SWR-V3-059 | 死代码豁免：blocking_point="no production callers" 不触发 depth 门禁降级 | REQ-V3-046 | 死代码候选判 UNREACHABLE 而非 NEEDS_REVIEW |

## M7 r05_diff_archaeology.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-060 | `--cross-tags` 用 git merge-base --is-ancestor 生成"修复 commit × tag"矩阵 | REQ-V3-012 | AWStats 7.6/7.7/7.8 已知结论可复现 |
| SWR-V3-061 | 无 .git → 输出 {"status":"NO_GIT"} | REQ-V3-013 | 无 git 目录输出正确 |
| SWR-V3-062 | HEAD 审计自动"变体复核"任务书模式 | REQ-V3-014 | 任务书为变体复核形态 |
| SWR-V3-063 | 默认落盘 JSON（-o 可选） | REQ-V3-015 | 无 -o 有产物 |
| SWR-V3-064 | grep 词表分级（security vs fix 两组，噪声占比可配） | REQ-V3-016 | 两组分开输出 |

## M8 ast_scanner.py

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-070 | LANG_TEST_PATH_MAP 语言映射过滤（ruby/powershell/rust/ts 5 形态） | REQ-V3-087 | 5 形态样例全拦截 |
| SWR-V3-071 | `--mode deep`（tree-sitter 佐证模式，非默认路径） | REQ-V3-002 | 默认流程不含全库扫描 |
| SWR-V3-072 | `--noise-check`：按 sink_type 抽样误报率，>80% 自动降权并提示 | REQ-V3-072 | 噪音报告产出 |
| SWR-V3-073 | 入队 merge 语义（不覆写队列） | REQ-V3-081 | 与 SWR-V3-051 同判据 |

## M9 task_templates/

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-080 | surface_map_domain.md（4 域变体，含背景/证据强制/产出 schema） | REQ-V3-020/022 | 模板齐备 |
| SWR-V3-081 | hypothesis_filter.md（排除判据：常量/白名单/死代码） | REQ-V3-037 | 判据清单齐备 |
| SWR-V3-082 | verifier_edge_proof.md（边证据要求/前提维度/死代码豁免/分级规则） | REQ-V3-040/043/044/046 | 模板含全部强制项 |
| SWR-V3-083 | biz_hypothesis.md（H1-H7，含 H7 信任边界检查项） | REQ-V3-053/054 | H7 检查项齐备 |
| SWR-V3-084 | empirical_test.md（采样协议/环境记录/判据） | REQ-V3-062/064 | 协议文本齐备 |
| SWR-V3-085 | 全部模板尾部含 self_json_guard（json.load 校验后提交） | REQ-V3-048 | 模板尾部统一 |

## 集成需求

| 编号 | 需求 | 满足 | 验收判据 |
|---|---|---|---|
| SWR-V3-090 | 端到端数据流可用：surface→hypothesis→queue→assert→report 单项目跑通 | REQ-V3-006/007 | 集成测试通过 |
| SWR-V3-091 | 回归验证：sinatra/lighttpd/actix 三个已审计项目复跑，结论与已知对照（Phase 3 判据） | REQ-V3-006 | 关键家族结论一致 |
| SWR-V3-092 | 全部新组件附单测（tests/ 下 test_<module>.py） | REQ-V3-006 | 测试覆盖核心函数 |
EOF