# Reachable Critical Audit v3.3.2 — 系统设计

> **文档性质**：v3.3.2 系统设计。上游输入：七项目 library 批次复盘（tiny_http / uWebSockets / libuv / HikariCP / fasthttp / node-sqlite3 / cJSON，2026-08-19）暴露的 16 项 skill 缺陷（lessons/W6_MORE_LANGS_FINDINGS.md §27）+ 4 项过设计审计（同文件 §28）。
> **版本定位**：缺陷修复 + 义务裁剪批次——不新增阶段、不改六门禁①-⑧判据语义（v3.2.1/3.2.2 同款约束）；本版主题为「**先裁后接**」：修复载体时不得把过设计坐实。
> **最高判据**：SKILL.md「第一原则：通用型 Skill」；本版新增「义务入库三问」作为 REQ 门槛（见 §2.6）。
> **日期**：2026-08-19

---

## 1. 问题域（全部来自七项目批次真实失败 + 机制取证）

### P-A：编排结果归属与完整性缺陷（张冠李戴，正确性级）

**证据**：
- tiny_http 复活波次结果（CAND-007/011）按候选 id 子集误匹配 uwebsockets，覆写其 `_resurrect_results.json`；node-sqlite3 结果（CAND-001/006）又覆写 libuv——主代理两次人工发现并恢复，若未发现则复活复核结论错配到别的项目
- workflow 最终通知（wme8jx0c0）含 journal 快照缺失的第 7 个决策（CAND-001）——journal 读取时点与通知到达之间的竞态真实发生
- 根因：workflow 结果无项目归属字段；主代理按候选 id 子集猜测 runId→项目映射；journal 是增量文件，读取时点决定完整性

### P-B：复活-重验-复核链路的防漏放缺口

**证据**：本批 9 个候选经 R3.5-N 复活，8 个重验改判 REACHABLE——全部由单个 verifier 附 gap 重验即定案，无一再经 R3.5 独立证伪。改判方向是 UNREACHABLE→REACHABLE（放行方向），按防漏放原则应强制对抗复核；REQ-V3.2-021 只规定"回 R3 重验"，未规定重验改判后的复核义务，主代理无依据启动第二轮 R3.5。

### P-C：分级证据链断裂点

**证据**：
- fasthttp CAND-002（512MB→539MB makeslice）与 CAND-004（EMFILE 61 连接退出）的反驳者 PoC 只存在于 workflow 结果，候选无记录——本批靠主代理重做实证补齐；REQ-V3.1-051 已规定 strengthened/attribution_correction 字段但落盘位置模糊（"进入报告"），无机械落盘命令
- uwebsockets CAND-002：verifier 实证自己的 crash 声称不成立（-O2/-O3 exit 0）仍保留 claim=crash——claim 与实证事实矛盾时 verifier 无修正义务，主代理事后重校准
- cjson 既有 empirical dict status="CONFIRMED"（大写）与 `CONFIRMED_EMPIRICAL_STATUSES` 小写元组不匹配——grade_verdict 静默降级 edge_proven，与 stored grade 冲突且无告警

### P-D：门禁语义漏洞与"假运行"检查

**证据**：
- 4 个 NEEDS_REVIEW 候选（tiny_http CAND-012、uwebsockets CAND-006/008/015）残留 claim_type 误触发 gate ③ empirical_required——assert_ledger 不检查 verdict==REACHABLE；`commit` 的 demote_to 分支不清 claim（与 REQ-V3.2.2-016「声称只属 REACHABLE」矛盾，collect 已清而 demote 未清，不对称）
- gate ③b（R4 findings 实证门禁，W6 §18.9）以"claim_type/evidence 文本关键词匹配"实现——中文证据文本命中与否不可预测，本批 7 项目全部"通过"但判定从未真实发生；R4 schema 已有 `empirical_result` 字段未被 ③b 读取
- r4_feedback（H7 默认值 vs R3 gate 冲突检测）自 v3.3 设计以来从未机械运行——其消费方不存在（见 P-F O1）

### P-E：义务无载体（机械化作坊缺口）

**证据**：
- REQ-V3.2-021 要求"回 R3 重验（附复活者证据）"，SW_DESIGN_V3_2.md:156 明写"附复活者 gap"，但 export verify 模式不读任何 gap 字段——本批 6 波重验全部靠主代理导出后手工把 gap 追加进 payload prompt 再内联派发
- 门禁⑦ 的 tracked 计算（hypotheses ∪ R4 tracked_surfaces ∪ mirror_pairs ∪ coverage_bridge）无 CLI——本批主代理写了三版脚本；且 libuv/cjson 的 R4 agent 产出 SURF-S-XXX 前缀 id 与 input_surface 的 S-XXX 不一致，无归一化契约
- v3.2 已设计"collect 后强制 grade_verdict 重算（grade_recomputed_by 标记）"但无批量命令——主代理按直觉传整个 queue 得到"verdict 非法"
- REQ-V3.2-020 抽样规则（声称类全量+其他 20%，min 2 max 8）执行后无决策记录——libuv/uwebsockets 各 1 个 UNREACHABLE 未入池但无追溯

### P-F：过设计——义务棘轮（义务入库无门槛）

**证据**（§28 四项裁决）：
- **O1 H7 五维全表**：hikaricp 17 行/fasthttp 31 项/tiny_http 14 项，80% 行零信息量（"安全有界，保留"）；消费方 r4_feedback 从未运行——有义务无消费者。真正有价值的发现（hikaricp keepaliveTime 代码 2min vs javadoc "0 disabled"）一行文字即承载
- **O2 步骤 0.5 无条件强制**：本批 71 候选全部"在构建列表"零 broken_edge，verifier 逐候选写 boilerplate——为 Lersosa 式失误设计但未按型门控（对照步骤 5.5 按 write→read 家族门控做对了）
- **O3 先例提示低精度注入**：hikaricp CAND-001/002（PropertyElf/JNDI）被注入 PREC-HOST-FAMILY-001（Host 头采信）完全无关先例，多个 verifier 写"不适用"——in-prompt 提示支线精度不足，先例库真实价值在主代理裁决侧
- **O4 签名库 R2 强制链路**：本批 7 项目（库型目标）签名命中 0；v3.1 已降为佐证器但 R2 流程仍强制跑 index/match——运行时角色已退休
- **根因：义务棘轮**——v3.1/v3.2/v3.2.1 每个新义务源于一次真实失误（Lersosa/mbedtls/313 验收），但入库时未写触发条件，对新审计无条件生效，prompt 体积与主代理义务单调膨胀

### P-G：环境与文档契约

**证据**：
- io_uring_setup 被容器 seccomp 阻断（liburing 可装、编译通过、实测 -1）——CAND-008 e2e 白跑一轮后才走 R5 可选路径；CAND-015 的 lsquic 子模块为空同理。v3.1 已有"环境陷阱自检"（stale 进程/diag 路由/daemon 线程/env 传播/PATH）但无 syscall/能力探针项；本环境另记录无 ss、无 /usr/bin/time、zsh `echo ===` 展开炸复合命令、pkill -f 匹配自身命令行自杀
- SKILL.md 写"复活全量落盘 resurrection_review"，实际 REQ-V3.2-023 只查声称类——抽样口径文档漂移
- R6 的 `--write` 与 `write_lesson(process_notes=)` 合并语义未写明（write_lesson 全量重渲染，幂等，但文档不说明）

---

## 2. 设计方案（每域论证"为什么能解决"）

### 2.1 P-A：派发-收集显式注册（wave registry）

**为什么能解决**：张冠李戴的根因是"结果无归属、映射靠猜测"。给派发侧建 append-only 注册表，collect 以注册表对账——映射从"主代理记忆+子集猜测"变成机械事实；通知与 journal 的竞态以"dispatched 全集校验"兜底（不足全集 → 重试读或报错，复用铁律 1 的写读竞态模式）。

设计要点：
1. `.audit_results/wave_registry.jsonl`：`{run_id, mode, project, dispatched[], payload_hash}`，每波派发后登记（SKILL.md 编排条款）
2. workflow script 返回补 `project` + `dispatched_ids` 字段（注册表数据源）
3. `--from-journal` 增 `--expect <ids>`：journal 提取结果必须覆盖 dispatched 全集，否则报错不落盘
4. resurrect 抽样决策落盘（selected/unselected/rule，REQ-V3.2-020 追溯）

### 2.2 P-B：复活改判强制复核（修订 REQ-V3.2-021）

**为什么能解决**：机制已在——export refutation 的 pool 条件（REACHABLE 且 grade≥edge_proven 且无 refutation 字段）天然覆盖复活改判候选，缺的只是强制力。修订 REQ-V3.2-021 增补"重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 池"，assert_ledger 加同形态检查（候选带 re_verify_gap 且 REACHABLE 且无 refutation 字段 → 违规）——义务由 gate 承载，不再依赖主代理自觉。

### 2.3 P-C：证据链落盘位置收敛（队列唯一事实源）

**为什么能解决**：workflow_export.py 头部原则是"队列是唯一事实源"，但 refutation 正面结果被 REQ-V3.1-051 导向"报告"——落盘位置与原则矛盾。收敛为：r35-collect 把 refutation decisions 机械落候选 `refutation` 字段（复用 evidence_ledger.commit 的 merge 语义），报告从队列派生；claim 自洽条款写入 verifier 任务书（实证证伪声称方向 → 按实证修正 claim）；status 大小写归一化在 grade_verdict 内完成，不匹配返回告警而非静默。

### 2.4 P-D：门禁实现层补条件 + ③b 结构化与收窄捆绑

**为什么能解决**：gate ③ 的条件缺失与 demote 清 claim 是 2 行级实现修复；③b 的问题是"假运行"——结构化接线会让它突然开始真阻断，所以必须与义务收窄捆绑交付（见 2.6 三问第②条：先裁后接）。r4_feedback 的消费者接线以收缩后的 H7 表为输入（见 2.5）。

设计要点：
1. gate ③ 前置 `verdict=="REACHABLE"`；commit demote_to 清 claim + claim_nulled_by（与 collect 对称）
2. ③b 改读 R4 finding 结构字段（empirical_result/claim_type），强制范围收窄至 Medium+/forced-claim 类，Low 接受 source_fact/机制级（修订 W6 §18.9）；关键词匹配降为 fallback warn
3. r4_feedback 实现：读收缩后的 H7 结构化表与 R3 gate 证据 key:value 比对，产出 warn（消费者接线）

### 2.5 P-E：载体补全（全部挂在现有扩展点）

**为什么能解决**：这些义务都已设计（REQ/SW_DESIGN 文本在），缺的是工具链载体。每条都挂在现有扩展点上：gap 渲染挂 `_checklist_section` 同点位、coverage CLI 输出即 assert_ledger 的 surface_data、id 归一化为共享纯函数（不落盘，见 2.5.1）、grade-recheck 挂已设计的 grade_recomputed_by 标记机制、抽样落盘挂 export_script_resurrect 返回值。

**2.5.1 id 归一化为共享纯函数（非持久化）**：`norm_surface_id`（SURF- 前缀剥离+去空格）定义于 surface_mapper，batch_verify 复用——对账与校验即时计算。不把 aliases 持久化进 input_surface.json（可推导数据不落盘，防过设计）。

**遗留项（本版不立项）**：§27 B4（payload 内联 ~100KB）推迟至 v3.3.3——公共模板下沉改动 VERIFY_SCRIPT 模板，影响 resume 缓存键与 lint 契约（W6 §17.2），需单独验收；本版以「payload 精简为 id+prompt」维持。

### 2.6 P-F：义务裁剪 + 入库三问（防复发）

**为什么能解决**：过设计的根因是义务入库无门槛。裁剪四项义务（H7 表收缩为安全相关默认值清单、0.5 按型门控、PREC 精度门、签名 R2 降佐证器），并把判据制度化——**义务入库三问**写入 SKILL.md，此后所有 REQ 必须过：
1. **触发条件**是什么（什么目标/语言/场景才执行）？——无条件默认不建
2. **消费者**是谁（哪个 gate/工具/报告段落读它）？——无消费者不建，或先建消费者
3. **裁掉丢什么**（有可回溯的失误案例支撑吗）？——无案例支撑的防御性义务降为 checklist 提示

三问自检：复活攻击和 gate ②③ 过三问（有触发条件、有消费者、有 313 验收案例）；H7 五维表和 0.5 过不了第一问/第二问。

### 2.7 P-G：环境探针 + 文档对齐

环境陷阱自检清单扩为"环境能力探针"：机制所需 syscall 探针（io_uring_setup 等）、依赖存在性（头文件/库/子模块物化）、工具存在性及替代（ss→/proc/net/tcp、time→getrusage）、shell 陷阱（zsh 展开、pkill 自匹配）。SKILL.md 三处措辞修订（抽样口径、grade-recheck 命令引用、R6 幂等语义）。

---

## 3. 组件影响清单

| 组件 | 修改 |
|---|---|
| evidence_ledger.py | gate ③ verdict 条件；commit demote 清 claim；status 归一化；③b 结构化+收窄（捆绑）；复活改判检查；r4_feedback 消费者接线 |
| batch_verify.py | `--stage coverage`；`--stage grade-recheck`；`--stage r35-collect --from-journal`；`--from-journal --expect`；IMPORTABILITY_STEPS 按型门控；r4-collect unknown id 告警 |
| workflow_export.py | verify 模式读 re_verify_gap 渲染 gap 段；resurrect 抽样决策落盘；script 返回 project+dispatched_ids；self_refutation_hints 精度门 |
| surface_mapper.py | 定义共享 norm_surface_id 纯函数（不持久化 aliases） |
| task_templates/biz_hypothesis.md | H7 表收缩 schema；R4 finding +claim_type；义务入库三问说明段 |
| task_templates verifier 任务书 | claim 与实证自洽条款 |
| SKILL.md | wave registry 簿记条款；R3.5 触发条款补复活改判；抽样口径对齐；R2 签名降佐证器；R6 幂等语义；义务入库三问 |
| harness_manuals/ | 环境能力探针清单（syscall/依赖/工具替代/shell 陷阱） |
| REQ 修订 | REQ-V3.2-021 增补、REQ-V3.3 H7 收缩、W6 §18.9 收窄、REQ-V3.1-051 落盘位置收敛 |
| tests/ | ~12 新单测（见 §4） |

## 4. 验收方案（Phase 3.3.2.3）

1. 单测：~12 新测试全绿 + 现有 98 测试全绿
2. 三锚点回归：sinatra/lighttpd/actix-web fixture 复跑零回退
3. 新项目验收（第一原则）：1-2 个未审过的小项目全流程，验证 gap 渲染/wave registry/r35-collect/coverage CLI 实际走通
4. 裁剪可测量：H7 表行数 ≤10（对照本批 17/31/14）；静态语言候选 prompt 中 0.5 段消失；PREC 提示零"不适用"命中
5. 六门禁①-⑧判据语义不变，仅实现层补条件；新增检查沿用 resurrection_required 形态
