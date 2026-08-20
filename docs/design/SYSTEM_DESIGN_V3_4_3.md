# Reachable Critical Audit v3.4.3 — 系统设计

> 日期：2026-08-20
> 定位：P0/P1/P2 三阶段验收（三锚点复跑 + PyJWT/jsonwebtoken/orjson + cpp-httplib/devise/cosign/java-jwt）暴露缺陷的修复版。
> 教训回填：lessons/W6 §32（P1 八项）+ §33（P2 九项）。验收记录：`ACCEPTANCE_V3_4_3.md`（待验收后落盘）。
> v3.4.3 是缺陷修复版：**不新增阶段、不改六门禁①-⑧判据语义、不重排流水线**——把三阶段暴露的 17 项缺陷就地制度化（12 项代码修复 + 5 项制度沉淀）。

## 1. 问题域（全部来自真实验收失败）

### P-A：R4 收集链数据完整性（4 项——agent 产出形态不可信）

| 证据（项目） | 缺陷 | 后果 |
|---|---|---|
| cpp-httplib R4 H1-H4 agent 产出 hypotheses 对象键 + findings 顶层数组（id=FX）+ evidence 数组 + r3_link 嵌套 dict | 任务书 canonical schema 无约束力，agent 自定形态 | r4-collect 0 提取（仅告警），主代理手工转换，门禁④ 依赖手工正确性 |
| 同 agent tracked_surfaces 用 SURF-DATA-00X（实际测绘为 SURF-DAT-00X 混合前缀） | SWR-V3.3.2-015 再违反；R1 merge 层自身前缀不一致是上游根因 | 覆盖率簿记失真，r4-collect unknown_surface_ids 告警 |
| P0-P2 全部证伪/复活波由主代理重建完整证据 args | refute_prompt 800 字符有标记截断、resurrect_prompt 1200 字符**静默**截断 | Mode W 任务书自包含性被削弱；静默截断致复活者误读证据中段（Lua 教训原文） |
| P0/P1 共 9 候选 + P2 多处 verifier 自报 empirically_confirmed 但无结构化 empirical dict | collect 存 verifier 自报 grade，SKILL.md 却声称 collect 自动重算 | 机械重算降级后主代理需按证据文本回填——回填依据真实性靠主代理裁决，无机制保障 |

### P-B：门禁判定链正确性（4 项——机器判定不可信）

| 证据 | 缺陷 | 后果 |
|---|---|---|
| R4 H-5 Medium finding（cpp-httplib 遮蔽型鉴权）empirical_result 含真实 g++ 实测（route_calls=0 三次复跑），gate ③b 仍报 empirical_required_r4 | 关键词表只认「实证/已实证/confirmed」，不认「实测」；关键词门控代替结构判定 | 真实实证被误报，主代理被迫改 evidence 文本加「实证确认」前缀——污染证据字段 |
| cosign CAND-002 env 反射泄露只能 claim_type=other | 枚举缺 "leak" | 信息泄露类失去结构化表达，报告分级/同族一致性断言用不上 |
| P2 两次 `batch_verify --mode resurrect` 报错，需 workflow_export 直调 + 主代理手工落盘 | resurrect 模式无 CLI 入口 | 手工落盘若遗漏会静默绕过六门禁的 resurrection_review 检查 |
| orjson boundary surface 的 capi-* 词族被 BOUNDARY_KINDS 校验器全拒 | 12 词词汇表无 C-API 扩展模块词 | FFI 边界测绘被迫归一化 ffi-other，信息丢失 |

### P-C：提示资产链质量（4 项——提示器产生误导）

| 证据 | 缺陷 | 后果 |
|---|---|---|
| CK-WS-MATERIALIZE（WS 专属）经 cwe-match:['CWE-400'] 绑到纯 JWT 库/密码比对候选（P1 三项目 + P2 四项目全部出现）；PREC-STREAM-MATERIALIZE/ENGINE-MATRIX 注入 java-jwt 无适用性过滤 | 清单与 PREC 提示无适用性门控 | 消耗 verifier 预算 + 注入不相关证伪论据；P2 verifier 普遍自行判 N/A 未造成误判，但「狼来了」效应风险（agent 学会无视清单） |
| java-jwt/cpp-httplib 两 agent 各自卡 783/796 字极限压缩 H7 默认值表 | 800 字预算过紧 | 五维描述被迫砍损，信息密度受损 |
| cpp-httplib（C++）export lang 推断 unknown | 推断只看构建文件，忽略队列已有 lang 字段 | 任务书语言分片失效 |

### P-D：制度项（5 项——不改代码，写进资产）

| 证据 | 项 | 处置位置 |
|---|---|---|
| java-jwt H2/H7 两 agent 各自独立发现同一 DateTimeException 逃逸 | 跨假说同事实重复 | SKILL.md R4 收集段加同事实去重流程（r3_link 标共享实证） |
| P2 R5 实证: pgrep -f 自匹配 sh 进程致 fd 计数错读；本机无 ss 命令 | 环境陷阱 | harness_manuals/go.md + c.md 陷阱清单 |
| P0/P1 实证回填做法（backfilled_by + 真实数字依据）已成事实规范 | 回填规范未文档化 | SKILL.md 兼容回填条款 |
| PyJWT CAND-002 REACHABLE vs jsonwebtoken CAND-001 UNREACHABLE 同类事实两种裁决 | 跨项目同族裁决分歧 | 先例库新增判据条目（放大比常数因子 × 物化责任归属） |

## 2. 设计方案（每域论证「为什么能解决」）

### 2.1 P-A：收集链自适应 + 任务书约束

**修复策略：双管**——收集侧自适应（机器兜底）+ 任务书侧约束（源头治理）：

- **收集侧**：stage_r4_collect 增加 schema 自适应解包（hypotheses 对象形态 / findings 顶层数组 / evidence 数组 join / r3_link dict 展平 / severity capitalize），归一化后写 `schema_normalized_by` 标记。原则：**先探测形态再归一化，归一化结果显式标记，不静默改写**（与 P0 旧队列兼容路径同构）。
- **任务书侧**：R4 任务书**注入实际 surface id 清单**（取代「原样引用」指令——指令无约束力，注入有）；附 canonical 输出示例段。surface id 上游归一化由 surface_mapper merge 完成（SURF-DAT-* → 统一前缀），一次修复覆盖下游全部对照误配。
- **截断协议统一**：resurrect_prompt 与 refute_prompt 共用同一截断标记协议（有标记 + 指向 verify_queue.json）；截断策略按段分级——承重前提/实证数字/阻断点关键段必保留，只截清单执行记录等次要段。
- **grade 口径对齐**：collect 直接机械重算（对齐 SKILL.md 原意），verifier 自报值存 `grade_self_reported` 保留追溯；主代理回填只发生在 verifier 证据文本含真实实测的场景，回填必须带 `backfilled_by` + 实测数字（文档化现有做法）。

### 2.2 P-B：结构判定优先于文本关键词

- **gate ③b**：`empirical_result` 非空 + 字段结构（含实测数字/命令输出/exit code 特征）判定为有实证，关键词仅作降级 fallback。关键词表补「实测/measured」。
- **claim_type 加 "leak"**：verifier schema、证伪者工具箱、报告分级三处同步；同族一致性断言纳入 leak。
- **resurrect CLI**：batch_verify 加 `--mode resurrect`（转调 export_script_resurrect）+ `--stage r35n-collect --from-journal` 落盘候选级 resurrection_review dict（对齐 REQ-V3.2.2-015 落盘契约）。
- **boundary_kind 加 "capi"**：通用词覆盖 Python C-API / Lua C-API / N-API 家族，lang_pair 仍由测绘提供。

### 2.3 P-C：适用性门控复用既有机制

- **清单/PREC 门控**：先例库 applicability_signals 机制（text/requires_lang/requires_claim 形态）复用为 checklist_binder 与 _self_refutation_section 的过滤层；不匹配时绑定通用资源类清单（如 CK-GENERIC-RESOURCE）或空。PREC 提示与清单共用同一 signals 字段，避免两套机制。
- **H7 表预算**：800 → 1200 字（或「≤10 行 + risk_dimensions 折叠」形态），任务书同步。
- **export lang**：优先读队列候选 lang 字段，无则回退 language_inventory。

### 2.4 P-D：制度项就地沉淀

SKILL.md 四处 + harness_manuals 两处 + 先例库一条（见 SW_DESIGN M7/M8/M5）。

## 3. 系统需求（REQ-V3.4.3）

| 编号 | 需求 | 承载缺陷 |
|---|---|---|
| REQ-V3.4.3-001 | r4-collect schema 自适应：hypotheses 对象形态/findings 顶层数组/evidence 数组/r3_link dict 四类漂移自动归一，写 schema_normalized_by 标记，0 提取场景告警含形态诊断 | P-A 漂移 |
| REQ-V3.4.3-002 | R4 任务书注入实际 surface id 清单 + canonical 示例段；surface_mapper merge 前缀归一化（SURF-DAT-* 等混用前缀统一） | P-A 自造 id + 前缀不一致 |
| REQ-V3.4.3-003 | prompt 截断标记协议统一：resurrect/refute 共用；关键段（承重前提/实证/阻断）必保留，次要段可截且必带标记 | P-A 截断 |
| REQ-V3.4.3-004 | collect grade 机械重算对齐 SKILL.md，verifier 自报值存 grade_self_reported；主代理回填规范文档化（backfilled_by + 实测数字） | P-A grade 口径 |
| REQ-V3.4.3-005 | gate ③b 结构判定优先：empirical_result 非空+实证特征（数字/输出/exit code）判定；关键词表补 实测/measured 作降级 fallback | P-B 关键词表 |
| REQ-V3.4.3-006 | claim_type 枚举加 "leak"：verifier schema/证伪者工具箱/报告分级/同族断言四处同步 | P-B leak |
| REQ-V3.4.3-007 | batch_verify `--mode resurrect` 导出 + `--stage r35n-collect --from-journal` 落盘候选级 resurrection_review | P-B resurrect CLI |
| REQ-V3.4.3-008 | boundary_kind 词汇表加 "capi"（通用 C-API 扩展词） | P-B capi |
| REQ-V3.4.3-009 | checklist_binder 与 PREC 提示共用 applicability_signals 适用性门控；不匹配绑通用资源类清单或空 | P-C 门控 |
| REQ-V3.4.3-010 | H7 默认值全表预算 800→1200 字（任务书同步） | P-C 预算 |
| REQ-V3.4.3-011 | export lang 推断优先读队列候选 lang 字段，回退 language_inventory | P-C lang |
| REQ-V3.4.3-012 | 制度四项：R4 同事实去重流程（SKILL.md）；go/c 手册环境陷阱；兼容回填规范条款（SKILL.md）；同族裁决判据先例（先例库） | P-D 全部 |

## 4. 验收判据（Phase 3.4.3）

三条件同时满足才合并 main + install：

1. **三锚点复跑零回退**：sinatra/lighttpd1.4/actix-web 旧队列 × v3.4.3 工具链，六门禁全 PASS 且 REACHABLE 结论零变化（require_target_kind/require_resurrection=False 豁免路径不变）
2. **缺陷闭环回归**：17 项缺陷各自的可测验收（见 SW_DESIGN 兼容性表）——如「含实测字样的 finding 不再误报」「SURF-DAT-* 前缀对照不再误配」「resurrect 全 CLI 路径走通」
3. **新项目全流程**：一个未审过的新项目走 R0-R6（选题优先 coverage-ledger 缺口格），重点设计成能触发 r4-collect 自适应、leak claim_type、resurrect CLI 的场景；六门禁全 PASS
