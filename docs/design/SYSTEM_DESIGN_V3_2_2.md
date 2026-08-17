# Reachable Critical Audit v3.2.2 — 系统设计

> **文档性质**：v3.2.2 系统设计。上游输入：mbedtls 4.2.0 审计复盘（2026-08-17）暴露的 8 个确定性工具缺陷 + 4 个设计盲区 + 资产通用性审计（签名库/先例库/检查清单库/harness/任务书取证）。
> **版本定位**：补丁版——不新增阶段、不改门禁语义（v3.2.1 同款约束）；本版以「通用型 Skill 第一原则」（SKILL.md 顶部 / SYSTEM_DESIGN_V3.md §0）为最高判据。
> **日期**：2026-08-17

---

## 1. 问题域（全部来自 mbedtls 审计真实失败 + 资产取证）

### P-A：知识资产携带项目残留（通用性破坏，最高优先）

**证据**（resources/signature_library.json 全量取证）：
- SIG-PY-PICKLE-001 grep = `['pickle.loads', 'get_host', 'read_body', 'safe_join', 'validate_host']`——Django 审计的整个攻击面披着 pickle 外衣；mbedtls（C）审计中靠 `get_host` 命中，产出"pickle 反序列化族 + get_host 采信 + ASGI read_body 无界循环"跨三项目拼贴假族
- SIG-TS-ACCUM-001 含 `'multer'`、`'replyTo'`（NestJS 专属）；SIG-KT-RECEIVE-001 含 `'maxFrameSize'`、`'maxDecodedContentLength'`（Ktor 专属）；SIG-AUTHZ-BOUND-007 含 `'good_origin'`、`'request_origin'`（lighttpd mod 变量）且 known_instances 目录名 `'XPC 鉴权'`；SIG-HEADER-INJ-006 known_instances 含 `'wp-admin'`、grep 含 `'CleanXSS'`（WordPress/AWStats）
- `known_instances` 全部锚定历史审计项目目录名（Sources/Src/lib/wwwroot/django）→ R0 冒烟自检对非 fixture 项目 testable=0 恒放行，自检形同虚设
- verifier 任务书步骤 0.5 是 Python 思维定式（find_spec/import/DI 扫描器，C 项目需主代理手工改写）；先例句证直接写"Lersosa required_args_constructor.py:39"
- 根因：经验入库是"发现→写入"两段式，缺"去项目化提炼 + 通用性验证"第三段

### P-B：harness 库按历史发现配备而非声称类别覆盖

证据：4 模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/multipart_align）全部来自特定战役；语言覆盖 6/15（缺 C/Java/Go/C#/JS 等 9 种）；声称类别覆盖 3/6（无 crash/fuzz、panic、protocol_dos、并发类）。mbedtls 审计中 C 解析器 ASan harness 是 verifier 现场自建——通用模板缺位靠 agent 即兴补位。

### P-C：文档↔代码↔模板三方契约漂移（8 个确定性缺陷中的 6 个）

1. R0 文档自检命令按 smoke_test 2 元组解包，实现返回 3 元组（v3.1 加 testable 后文档未同步）→ 照抄命令 ValueError
2. surface_mapper merge 只打印不落盘，文档写"merge → input_surface.json"→ 需手动重定向
3. r2_guard drops 读 `"dropped"` 键，filter 任务书模板产出 `"drop"`（单数）→ 静默报 kept=0 dropped=0，SWR-V3.1-072 全量落盘检查形同虚设
4. r2_guard anchor 读候选字段 source_file/source_line，R2 假设模型是 hit_sites 数组 → CLI 报"锚点缺 file/line"，主代理手写批量检查
5. r4-collect 落 "H1" 形态，r4-assert 期望 "H-1" → 手动归一化才 PASS
6. lessons_recorder 期望候选级 dict{revived,outcome}，str/list 形态落盘直接 AttributeError

### P-D：门禁语义与政策落地缺口

1. gate ③（empirical_required）对 UNREACHABLE 候选生效：verifier schema 允许 UNREACHABLE 填 claim_type=crash → 判为不可达的候选反触发强制实证。"声称"语义上只属于 REACHABLE
2. signature_matcher gen 产出 L1 通用词假设（pickle 族 ×3、get_host 族 ×3）——v3.1 已定"L1 通用危险词不生成假设"（W6 §14.1/§17.3），gen 实现未跟进；且 L2 词族未按 surface.lang 过滤（v3.2 已定规则未落地）

### P-E：scope 稳定性与覆盖传播

1. R4 H7 智能体为实证抽验自行 `git submodule update` 物化 tf-psa-crypto → R1"子模块空目录"scope 判定失效、R2 两个 drop 理由（"树外不可验证"）作废，靠主代理发现 + R3.5-N 复活补位。子模块型项目 + agent 有 shell = 可预期事件，需机制化
2. 门禁⑦ surface 覆盖：59 surfaces 中 16 个 relay/镜像面（merge 冲突镜像条目、套接字中继面）需主代理手写 coverage_bridge 才到 100%——镜像对在 merge 时已有信息（kept-first 冲突记录），未自动传播

### P-F：机械信号与摩擦

1. target_kind 推荐 application：listener 命中 library/net_sockets.c（库内 socket 辅助函数）、startup-chain 命中 scripts/analyze_outcomes.py（测试脚本）——信号无路径分域
2. tier 把 .sh/.py/.pl 构建脚本计为"4 语言混合"→ large 档 5 agents（无害过配但归类缺运行时语义）
3. batch_verify collect 与 workflow 结果无桥接——主代理手工从 journal.jsonl 提取再拼 --cand-XXX 参数（W6 §10.3 有规则但未机械化）

---

## 2. 设计方案（每域论证"为什么能解决"）

### 2.1 P-A：资产去项目化 + lang 维度落地（REQ-001~007）

**为什么能解决**：污染根源是资产无 schema 约束（无 lang、无 CWE 锚定要求）且 match/gen 不做语言过滤。给签名数据模型加 `lang` 必填 + `cwe` 锚定，把语言过滤做成 match 阶段的机械规则，把"项目专属 API 名"做成资产入库检查器的黑名单检查——约束前置到写入时，而非审计时靠主代理识别。

设计要点：
1. **签名数据模型 v2**：`{sig_id, level, lang(必填), cwe[], semantic_family(必填, 抽象形态), detection_hints, known_instances}`。validate() 增加 lang 必填 + semantic_family 非空 + cwe 非空检查（L3 语义族 cwe 必填；L2 词族 lang 必填）
2. **污染签名重构**：PY-PICKLE 拆为纯 pickle 反序列化（lang=python）；get_host/read_body/safe_join/validate_host 从签名移除（Host 信任族归 SIG-AUTHZ-BOUND-007 抽象化）；TS-ACCUM 去 multer/replyTo；KT-RECEIVE 去 Ktor 配置名；AUTHZ-BOUND 去 good_origin/request_origin；HEADER-INJ 去 CleanXSS；known_instances 目录名 'XPC 鉴权' 移除
3. **match 阶段 lang 过滤**：签名 lang ∩ surface lang = ∅ → 跳过（缺失 lang 的签名 validate 即拒绝，不进入 match）
4. **gen 只消费 L3 命中**；L1/L2 命中仅记录为佐证（hits.json 保留，gen 忽略）
5. **R0 冒烟语义修正**：fixture 仓库（known_instances 可定位）保持 hit_rate 检查；非 fixture 仓库改为**签名库完整性自检**（validate + lang 完备 + 项目专属名扫描 0 命中）
6. **verifier 步骤 0.5 按 lang 分派**：`_build_prompt` 按候选 lang 装载 per-language 模板（c=构建包含/符号引用；python=import 图；java/go/rust 各自机制；无模板时装载通用版）。例证去项目名（"Lersosa required_args_constructor.py:39" → "某模块体顶层裸导入断裂"）
7. **先例/清单正文脱敏**：正文项目名 → 抽象形态描述；项目名仅存追溯字段（source 列引用 lessons）

### 2.2 P-B：harness 按声称类别覆盖（REQ-008/009）

设计要点：harness_runner 新增 parser-fuzz 模板（C：ASan+UBSan harness 骨架 + 编译/运行流程，直接取自 mbedtls 实战——该模板对任意 C 解析器候选通用）；覆盖矩阵文件 `resources/harness_coverage_matrix.json`（claim × lang 二维，标注有/无模板），R5 现场构造时引用矩阵缺口（缺口本身是记录而非阻断）。

### 2.3 P-C：单一事实源 + 入口归一化（REQ-010~015）

**为什么能解决**：6 个缺陷的共同根因是"文档内嵌命令/模板键名/工具字段契约"三方各自漂移。设计要点：
1. **单一事实源**：signature_lib 增加 `selfcheck <project>` CLI 子命令（内部 3 元组解包）；SKILL.md R0 只保留一条 `selfcheck` 命令。新增 **doc-lint 测试**：从 SKILL.md 抽取全部代码块在 fixture 上真实执行——文档漂移从此由测试捕获，而非审计现场发现
2. **入口归一化**（复用 normalize_surfaces 既有模式）：merge 默认落盘；drops 双键归一；anchor 识别 hit_sites 形态；r4 id 双向归一（H1↔H-1，内部统一 H-1）；lessons_recorder resurrection_review lenient 包装（str→dict）+ R3.5-N 落盘契约写入 SKILL.md

### 2.4 P-D：语义收敛（REQ-016/017）

1. **claim 只属 REACHABLE**：collect 阶段机械规则 `verdict != REACHABLE → claim_type = null` + `grade_recomputed_by=collect-claim-null` 标记；门禁③逻辑不变（它检查的数据从此正确）
2. VERDICT_SCHEMA 说明与任务书文本声明 claim_type 仅 REACHABLE 有意义

### 2.5 P-E：scope guard + 覆盖传播（REQ-018~021）

1. **scope_snapshot**：R0 落盘 `.audit_results/scope_snapshot.json`（`git submodule status` + 关键目录存在性清单）；batch_verify 入队（workflow-script 阶段）前 diff 现状 vs snapshot → 差异写 `scope_changed` 提示并附受影响 drop 列表
2. **scope_dependent drop 标记**：R2 drop 条目支持 `scope_dependent: true`（"树外不可验证"类理由自动携带）；scope 变更时批量提示复活流程
3. **mirror_pairs 传播**：merge 落盘 mirror_pairs（kept-first 冲突对）；assert_ledger 的 tracked 计算自动并入镜像面（gate ⑦ 不再要求主代理手写镜像桥）
4. **coverage_bridge 正式化**：SKILL.md 门禁⑦写明 relay 面（无镜像对的中继面）由主代理签收 coverage_bridge，属正式通道而非临时补救

### 2.6 P-F：机械信号修正（REQ-022~024）

1. **target_kind 信号路径分域**：listener 信号排除 library/（库内 socket 辅助函数）与 tests/、scripts/（测试工具）路径；startup-chain 排除 scripts/、tests/。product 程序目录（programs/ 等含监听循环的示例/工具目录）保留
2. **tier 语言计数**：混合度只计 component_role=server-side 的语言（构建脚本不计）
3. **collect 桥接**：batch_verify `--stage collect --from-journal <transcript_dir>` 自动提取 schema-validated 结果（result/value 双字段，W6 §10.3）落盘

### 2.7 附带项：r4_feedback resolved 标记位（v3.2.2 候选遗留）

evidence_ledger 的 r4_feedback 冲突告警支持主代理裁决后写 `resolved` 标记 + 理由，已 resolved 的冲突不再重复告警（W6 §25.6 遗留）。

---

## 3. 组件影响清单

| 组件 | 修改 |
|---|---|
| signature_lib.py | validate() lang/cwe/semantic_family 必填检查；`selfcheck` CLI 子命令（fixture 命中率 / 非 fixture 完整性自检）；项目专属名黑名单扫描 |
| resources/signature_library.json | 13 签名重构（拆分/删词/加 lang/cwe/语义族抽象化）；known_instances 仅保留 fixture 可定位实例 |
| signature_matcher.py | match() lang 交集过滤 + tests/ 排除；gen() 只消费 L3 命中 |
| surface_mapper.py | merge 默认落盘 + mirror_pairs 输出；tier server-side 语言计数；scope_snapshot 产出 + `scope diff` 子命令 |
| r2_guard.py | drops 双键归一；anchor hit_sites 模式；drop scope_dependent 字段 |
| batch_verify.py | collect：claim null 机械规则 + --from-journal + r4 id 归一；_build_prompt 步骤 0.5 lang 分派 + 例证脱敏；入队前 scope diff |
| evidence_ledger.py | assert_ledger mirror_pairs 传播；r4_feedback resolved 标记位 |
| lessons_recorder.py | resurrection_review lenient 包装 |
| harness_runner.py | parser-fuzz 模板注册；覆盖矩阵加载 |
| resources/harness_coverage_matrix.json | 新增（claim × lang） |
| target_kind.py | listener/startup-chain 信号路径分域 |
| resources/precedent_library.json / checklist_library.json | 正文去项目名（追溯字段保留） |
| SKILL.md | R0 selfcheck 命令替换；门禁⑦ coverage_bridge 正式化；R3.5-N 落盘契约；第一原则已在位 |
| tests/ | doc-lint 测试 + 契约测试（drops 归一/anchor hit_sites/claim null/mirror 传播/tier 分域/scope diff/lang 过滤）+ mbedtls 回归 fixture 固化 |

## 4. 验收方案（Phase 3.2.2.3）

判据① **mbedtls 本树机械复跑**（使用 .audit_results/ 现有产物）——8 个缺陷对应的手工绕过动作全部消失：selfcheck 一条命令跑通 / merge 后 input_surface.json 自动存在 / r2_guard drops 报 dropped=3 / anchor 直接过 hypotheses.json / r4-collect 后直接 r4-assert PASS / lessons_recorder 不再崩溃 / UNREACHABLE 不再触发 empirical_required / assert_ledger 无需镜像手工桥。且结论零丢失（0 REACHABLE / 6 R4 findings / 4 UNREACHABLE 复活未复活）。
判据② 三锚点之一（akka-http）回归零回退（tests 覆盖）。
判据③ 资产通用性检查全绿：13 签名 lang/cwe 完备、项目专属名扫描 0 命中、match 无跨语言命中。
判据④ 现有 90 测试 + 新增测试全绿；install.sh 安装完成。
判据⑤ 新项目验收条款（第一原则）：本版验收对象 mbedtls 为 v3 首审 C 库项目（此前无 C 库先例），天然满足"未审计过的新项目"约束，并在 ACCEPTANCE 中明示。
