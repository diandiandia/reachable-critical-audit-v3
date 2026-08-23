# 三项体检评估报告（v3.5 前置）——偏见 / 过设计 / 项目残留

- **日期**: 2026-08-23
- **基线**: v3.4.6（rpcx 验收后未提交）+ HEAD b2eb557（v3.4.5）
- **范围**: rpcx 审计完成后对 skill 本体的三项体检（第三轮健康检查——v3.3 做过偏见消除 10 项裁决、v3.3.2 做过义务裁剪 4 项裁撤）
- **方法**: 3 个 Explore agent 并行（残留评估 / 偏见评估 / 过设计评估），全部数字由脚本对资源文件实算，关键发现经主代理抽查核实
- **用户决策**: 本次（v3.5）修复范围 = 高优先级发现（残留 3 + 偏见 5）+ 过设计 A 清单死资产 + 文档漂移；中低优先级与 B 裁决清单只记入本报告，留待下一轮

---

## 一、项目信息残留评估（第一原则三禁止）

**第一原则**: 项目名/目录结构/专属 API 不得进入运行时资产；允许位置仅 tests/fixtures 与 lessons 追溯字段。

### 高（3 处，运行时机制携带项目专属内容）

1. **`resources/precedent_library.json`** — applications/counterexample 约 60 处项目 CAND-id（Pester/ohmyzsh/Newtonsoft/Vapor/Dubbo/Django/actix/sinatra/lighttpd/Ktor/Lersosa/Lua/PyJWT…），经 precedent_library.py→workflow_export.py:505-507 self_refutation_hints() **运行时注入 verifier 任务书** → 需抽象为形状描述，项目名只留 source_lessons
2. **`templates/harness/xss_path_sim.pl`** — 整文件 AWStats 复刻（awstats.pl/CleanXSS/硬编码行号），被 signature_library.json empirical_harness ×2、harness_runner.py TEMPLATES、harness_coverage_matrix xss 行接线 → 移入 tests/fixtures 或参数化抽象
3. **`harness_manuals/*.md`** — 指令性正文含项目名（java=Dubbo/fastjson2/HikariCP、kotlin=ktor/maxDecodedContentLength、python=Django get_host/read_body 等）+ 6 处 /root/xxx 绝对路径 → 抽象化保留机制形态 + W6 § 引用

### 中（12 处）
- signature_library.json:38,345 tier_note/semantic 项目名
- checklist_library.json:71,216,273,737,782（ktor/etdd 拼写错/kses_init/ETagHashes/uwebsockets/hikaricp）
- ~~issue_coverage_matrix.json sources 35 条 /root 路径~~ → **v3.5.1 已修**（sha256 摘要化, 见对照表）
- anchor_registry.json:36,64,72 fastjson2/tengine/xquic 审计产物锚点（CVE 描述字段）→ **v3.5.2 已修**（随 B1 三联体裁除而消失）
- task_templates 例证（biz_hypothesis/hypothesis_filter/verifier_edge_proof）→ **v3.5.2 已修**（mbedtls/quic-go → 机制形态; 自检扫描扩 task_templates 闭环）
- signature_lib.py DEPROJECT_BLACKLIST 项目名注释+token（token 保留=守卫弹药, 注释已剥离）
- ~~surface_mapper.py:698,707 rationale 运行时输出含项目名~~ → **v3.5 已修**; 漏网 :714 sinatra → **v3.5.1 已修**; tools/target_kind.py:192-193 Dubbo BeanContainerManager/actix ActixSystem 启动链正则 → **v3.5.2 已修**（删项目专属类名, 补 SpringApplication.run）
- SKILL.md:140 quic-go 实录 + :410-422 Lersosa（均处版本增量段=changelog 追溯, 判合法保留）

### 低（~50 处）
- 根模块/tools 溯源型注释 → 统一 W6 § 引用；anchor_registry CVE 括号名；SKILL.md changelog 段（允许）

### 附带发现（非残留但相关）
- harness_runner.py:37-42 注册 multipart_align → templates/harness/multipart_align.py **不存在**（悬空引用）
- SKILL.md:282 "13 个签名" 文档漂移（现为 20 签名、known_instances 已退役）
- tests 防回退 lint 覆盖不足：test_doc_lint.py 仅覆盖 CK-PINNED-DEP 一条

---

## 二、偏见评估（通用性：Top15 语言 × 每语言 Top10 问题）

### 高（5 处）

1. **templates/harness 违反第一原则去项目化**（与残留高#2 同根）：xss_path_sim.pl 全文 AWStats 专属（CleanXSS 恰在 signature_lib.py:31 DEPROJECT_BLACKLIST 上，但黑名单只扫签名资产、未扫模板）；ws_frame_alloc.py 硬编码 ktor 端口 18083、ws_frame_accum.py 硬编码 actix 端口 18084——v3.2.2 P-A 改革漏掉模板目录
2. **step 0.5 static_short 语言错配**（batch_verify.py:99-106,1589-1591）：`IMPORTABILITY_FULL_LANGS={python,javascript,java}`，其余 13 语言在非 application 目标下全落 static_short，其措辞为「CMake 源列表/GOPATH/cargo 目标/Makefile」纯 C 系词汇——派发给 kotlin/scala/csharp/php/ruby/swift/perl/powershell/shell 的库型候选（脚本语言无构建系统、JVM/.NET 无 CMake/GOPATH）
3. **R0 形态分类双重语言门**：target_kind.py:69-73 扩展名白名单缺 .swift/.kt/.cs/.pl/.pm/.ps1/.sh → 6 语言「无源码文件 → 默认 application, confidence=low」（Swift 库与 C 库置信度不对称；pom.xml/composer.json/Gemfile 零解析、LISTEN_PATTERN 为 Go/Rust/Py/JS 词汇）；surface_mapper.py:160-167 Go/Java 独享「无 main→library」特判、:198-199 _SRC_EXTS 缺 .scala/.php/.pl/.pm/.ps1/.sh、:213-240 main 模式漏 Kotlin `fun main`/C# `static void Main`/Swift `@main`、listen 模式漏 C# HttpListener/Ruby TCPServer/PHP stream_socket_server/Perl IO::Socket
4. **R0 冒烟锚点盲区**：7/20 签名零 fixture（signature_lib.py:186-191「no confirmed fixture instance → skipped」）——c/cpp/go 三种账本最重语言在 tests/fixtures 零代表，R0 回归保护只覆盖 v3.1 时代 13 签名，扩军签名零保护
5. **覆盖账本集中度**：RESOURCE-DOS×go=55（rpcx 未提交波次 +14 至 55，占族行 24.7%）；矩阵 144 格 41 零格（28.5%，CRYPTO 11 零格 / DATA-INTEGRITY 8）；OTHER 无 CWE 归属桶占 35% 总候选——缺口格优先选题（REQ-V3.4-006）只在批次内生效，同形态项目（Go RPC server）重复灌满同一格

### 中（8 处）
- harness 模板 8/16 语言零覆盖，且 Go（账本被审计最多语言）零模板（v3.2.2 复盘承认「4 模板 6/15 语言偏历史战役」，修复后仍无 Go 模板）
- env 陷阱清单仅 7/16 语言（harness_runner.py:232-241）；L2 词族 5 语言缺失（ruby/php/perl/scala/swift，31%）
- L3 语义族 grep 词汇 C/Rust/Kotlin 系倾斜（SIG-BUFFER-ACCUM/PREALLOC-LEN/TRUNC-CAST/STATE-RACE/CRYPTO-WEAK 几乎无脚本语言 token）；签名库 CWE 分布向 RESOURCE-DOS 倾斜（7~9/20）
- Linux /proc VmRSS + kill -0 采样协议是 OS 平台偏见（empirical_test.md:4-9、harness_runner.py:62-67）
- anchor_registry.json swift=0（覆盖 15/16 语言）；harness_coverage_matrix crash 仅 c/cpp、panic/protocol_dos 无任何语言
- 形态双轨词汇：project_kind{frameworks,library,infra,app}（surface_mapper）vs target_kind{application,library,hybrid}（target_kind.py）两套并行
- harness_runner.py:37-42 注册 multipart_align → 文件不存在（悬空，与残留附带发现同条）
- checklist 分派机制语言无关（好），但关键词词汇自带 C 系/JVM 系偏向（脚本语言无对应清单条目）

### 低（5 处）
- 资产计数全面陈旧：SKILL.md:282-283「13 签名/19 清单/19 先例/3 模板/15 手册」实际 20/29/25/4/16（+cpp.md 增量）；README.md:64,131,188-190 同病
- 跨模块语言词汇不统一：cs/csharp、js/javascript/typescript、ps/powershell 在 signature_lib.py:20、signature_matcher.py:20-28、batch_verify.py:124-127、issue_coverage_matrix.json:4 各自为政
- harness_runner.py:286-295 无 lang 默认 "rust"；mixed_build_hint lang_pair 只认 {c,py,rust,js,ts}
- batch_verify.py:1638-1639 任务书步骤 5.5 全库唯一语言习语示例是 Go（`if err == nil` 块）——其余步骤语言无关
- surface_mapper boundary 指南枚举 extern "C"/ctypes/cffi/N-API/JNI/CPython/JS addon——无 cgo 提及

### 正面确认（修复验证属实）
- find_spec 修复真实（v3.2.2 声明属实，IMPORTABILITY_STEPS 按 lang 分派且 python 版实际导入验证）
- r2_guard.py 与 workflow_export.py 无语言默认绑定
- 先例库 25 条跨 16 语言是全库最均衡资产
- checklist 分派机制本身语言无关
- docs/history/GENERALITY_EVAL.md:15,65 早已自认「域与假说清单仍偏 Web-内存家族」与本评估互相印证

### 语言 × 资产矩阵（16 语言 × 9 类资产）

✓=有，✗=无，△=部分/间接，数字=数量。

| 语言 | L2 词族 | 手册 | 锚点 | harness 模板 | env 陷阱 | step0.5 模板 | target_kind 识别 | R0 fixture | 账本计数 | 资产分 |
|---|---|---|---|---|---|---|---|---|---|---|
| python | ✓ | ✓ | 3 | ✓(xss+悬空multipart) | ✓ | ✓(完整) | ✓(清单解析+listen+startup) | ✓(django) | 95 | 9/9 |
| rust | ✓ | ✓ | 2 | ✓(ws×2) | ✓ | ✓ | ✓(Cargo 解析+listen+startup) | ✓(actix) | 90 | 9/9 |
| java | ✓ | ✓ | 3 | ✗ | ✓ | ✓(完整) | ✓(.java+listen) | ✓(fastjson2) | 67 | 8/9 |
| c | ✓ | ✓ | 1 | ✓(parser_fuzz) | ✓ | ✓ | ✓(.c+listen) | ✗ | 156 | 8/9 |
| cpp | ✓ | ✓(增量) | 1 | ✓ | ✗ | ✓ | ✓(.cpp) | ✗ | 18 | 7/9 |
| go | ✓ | ✓ | 1 | ✗ | ✓ | ✓ | ✓(.go+listen+startup) | ✗ | 153 | 7/9 |
| ts/javascript | ✓ | ✓ | 1 | ✗ | ✗ | △(default 文案) | ✓(.js/.ts+package.json) | ✓(nest) | 77 | 7/9 |
| kotlin | ✓ | ✓ | 2 | ✓(ws×2) | ✗ | ✗(static_short) | ✗(.kt 不扫) | ✓(ktor) | 38 | 6/9 |
| scala | ✗ | ✓ | 2 | ✓(ws_accum) | ✗ | ✗(static_short) | △(.scala 仅 listen 扫) | ✓(akka) | 20 | 6/9 |
| perl | ✗ | ✓ | 3 | ✓(xss) | ✗ | ✗(static_short) | ✗(.pl 不扫) | ✓(AWStats) | 38 | 5/9 |
| php | ✗ | ✓ | 4 | ✓(xss) | ✗ | ✗(static_short) | △(.php 扫但 composer 零解析) | ✓(WordPress) | 26 | 5/9 |
| powershell | ✓ | ✓ | 2 | ✗ | ✗ | ✗(static_short) | ✗(.ps1 不扫) | ✓(Pester) | 24 | 5/9 |
| ruby | ✗ | ✓ | 3 | ✗ | ✓ | ✗(static_short) | △(.rb 扫但 Gemfile 零解析) | ✓(sinatra) | 14 | 5/9 |
| csharp | ✓ | ✓ | 2 | ✗ | ✗ | ✗(static_short) | ✗(.cs 不扫) | ✓(Newtonsoft.Json) | 41 | 5/9 |
| shell | ✓ | ✓ | 2 | ✗ | ✗ | ✗(static_short) | ✗(.sh 不扫) | ✓(ohmyzsh) | 8 | 5/9 |
| swift | ✗ | ✓ | **0** | ✗ | ✓ | ✗(static_short) | ✗(.swift 不扫) | ✓(vapor) | 67 | **4/9** |

---

## 三、过设计评估（三问框架 × 六项扫描）

判据：① 触发条件是否有无条件默认/强制；② 读方是否存在（无消费者即不建）；③ 裁掉后损失什么（有实战案例支撑的防御义务不得降级为 checklist 提示）。

### A. 确凿死资产清单（零消费者，可安全删除——v3.5 已删）

1. **字段（13）**：paths_analyzed、path_count、coverage_note、schema_normalized_by、verified_at、escalation_log、checklist_ids、checklist_bindings、coverage_bridge、candidate.members、mechanism_correction、obligation_feedback、schema_version（无校验读方）
2. **函数（5）**：checklist_binder.h7_template_bind（:159-161）、checklist_binder.bind_all（:144-174 含 bind-all CLI）、precedent_library.record_application（:168-186）、precedent_library.add_precedent（:189-203）、signature_matcher.emit_filter_tasks（:268-291）
3. **stage（4）**：batch_verify next-cluster（:555-609）、cluster-collect（:722-761）、coverage（:1031-1100）、r15 分支（:1771-1773）
4. **模板（4）**：task_templates/empirical_test.md、self_json_guard.md、verifier_refutation.md、verifier_edge_proof.md（真实 prompt 由 workflow_export.refute_prompt:306-343 / batch_verify._build_prompt:1536-1680 代码生成）
5. **注册残留**：harness_runner.py:44-50 multipart_align 条目（文件缺失）
6. **死读**：lessons_recorder.py:76 读 repair_stats.json（零写方）

### B. 裁决清单（10 项，v3.5 未修，下轮定夺）

| # | 资产 | 现状 | 推荐倾向 |
|---|---|---|---|
| B1 | ast_scanner.py（1212 行）+ anchor_registry.json + security_profiles.json（16124 行）三联体 | SKILL.md:281「按需使用」无触发点 | 保留 ast_scanner、裁 security_profiles（内容可由 signature_library 覆盖） |
| B2 | r05_diff_archaeology.py | R0.5 已被 surface_mapper.scope_diff（batch_verify.py:1404-1416）机械取代，只剩测试消费者 | 裁 |
| B3 | grade-recheck「collect 后强制」（SKILL.md:370-372） | 与 collect 内联重算（:399-403）重复执行同一义务（①问违规典型） | 删「强制」措辞保留维修工具 |
| B4 | repair（surface_mapper.py:710-759） | 无任何工作流调用 | 裁或降级按需 |
| B5 | signature_tier/empirical_harness 字段 | R2 可选路径产物，机械读方未证实 | 确认 needs_harness 后裁决 |
| B6 | harness_coverage_matrix.json | 零读者（REQ-V3.2.2-009「R5 引用矩阵缺口」无代码实现，tracking 标「已完成」与实况不符） | 实现缺口引用 or 裁 |
| B7 | parser_fuzz_c.py | 已注册但 SKILL.md R5 未列 | 补文档 |
| B8 | 9/25 条 precedent 永不被 match（map 仅 16 条） | PREC-ALLOC-VIRTUAL-001、PREC-BYDESIGN-001、PREC-CONSISTENCY-001、PREC-ENV-SAME-PRINCIPAL-001、PREC-FAMILY-CONSISTENCY-001、PREC-HARM-ABSORBED-001、PREC-IMPLICIT-SURFACE-001、PREC-IMPORT-BREAK-001、PREC-TARGET-KIND-001 | 补 CWE/keyword map or 裁（先例库 16 条已覆盖匹配面） |
| B9 | CK-EMPIRICAL-SCOPE（第 19 条） | binder:116-117 强制 matched=[] + 声称「R5 显式绑定」无实现 | 实现显式绑定（有实战支撑——实证范围分级）or 裁 |
| B10 | 文档漂移 | SKILL.md 资产地图「19 检查/19 先例/13 签名」vs 实际 29/25/20 | v3.5 已修（随文档漂移修订） |

### 三问结论
- ①问（无条件强制）违规：grade-recheck「collect 后强制」（collect 已做）——B3
- ②问（无消费者）违规最多（~20 项）：A 清单全部 + B1/B2/B4/B6/B8/B9
- ③问（裁掉损失）保留项均有实战案例：grade_self_reported（分歧追溯）、escalated_signed_off（签收门禁）、target_kind、wave_registry（对账）、default_value_table（r4_feedback）

### 保留确认（存活，未误杀）
字段：verdict/reachability_type/call_chain/call_chain_depth/edge_evidence/evidence_grade/attempt/status/empirical/claim_type/correction_record/resurrection_review/escalated_signed_off/target_kind/r4_findings/default_value_table/grade_self_reported/r3_link；机制：bump-attempt、R3.5 refutation、wave_registry、scope_diff、r3_link 去重、target_kind.py、gen_tracking.py、六门禁全部

---

## 四、v3.5 已修 / 未修对照

### 已修（v3.5）
| 项 | 修复 |
|---|---|
| 残留高 1 | precedent_library.json 形状抽象（5 字段项目 token 清零，项目名只留 source_lessons） |
| 残留高 2 | xss_path_sim.pl → tests/fixtures/xss_path_sim_awstats_anchor.pl + 原位参数化骨架 |
| 残留高 3 | harness_manuals 项目名→机制形态 + 6 处 /root 路径→$HOME 占位 |
| 偏见高 1 | ws_frame_alloc/accum 端口参数化（18083/18084 删除，host/port 必传） |
| 偏见高 2 | STATIC_SHORT_BY_FAMILY 按语言家族分派（c/go/rust/jvm/dotnet/script/swift） |
| 偏见高 3 | target_kind 扩展名白名单 + 3 格式包清单解析 + LISTEN_PATTERN + surface_mapper _SRC_EXTS/main/listen/无 main→library 泛化 |
| 偏见高 4 | known_instances.json 补 7 签名 confirmed fixture（selfcheck 窗口验证） |
| 偏见高 5 | coverage-ledger 输出 pressure_cells + saturated 标记 + 选题提示（无新义务） |
| 过设计 A | 死字段 13 / 死函数 5 / 死 stage 4 / 死模板 4 / multipart_align 注册 / repair_stats 死读 全部删除 |
| 文档漂移 | SKILL.md 资产地图 20/29/25/4/3/18 + README 计数 + 门禁⑦ 代码块 tracked_ids+mirror_pairs |
| 防回退 | test_deproject_assets.py + selfcheck _scan_runtime_assets + 资产计数 lint + fixture 完整性测试 |
| 附加 | target_kind/surface_mapper 路径遍历子串匹配 bug（路径含 target/build 子串漏扫）修复（测试基线暴露） |

### 已修（v3.5.1 追加, 2026-08-23）
| 项 | 修复 |
|---|---|
| 残留中: issue_coverage_matrix sources | 36 条历史项目绝对路径 → 项目路径 sha256 前 16 hex（幂等身份去项目化; 读端/写端同步 hash 化 + 旧数据同函数迁移; 追溯由 docs/design/ACCEPTANCE_* 承担） |
| 残留中: rationale 漏网 :714 | size_tier 运行时输出 `(sinatra 20 surfaces 2 agents)` → `(成熟框架 20 surfaces 2 agents 档位校准)`（保留 W6 §24.7 教训引用） |
| 自检盲区 | `_scan_runtime_assets` 扫描范围补 resources/（仅拦 /root/ 绝对路径; source_lessons/cve 描述等合法追溯字段豁免黑名单）——修复 36 条 /root/ 曾通过 R0 的盲区 |
| 防回退追加 | test_selfcheck_flags_resources_root_residue + test_ledger_sources_hashed（192 passed） |

### 已修（v3.5.2 追加, 2026-08-23）
| 项 | 修复 |
|---|---|
| 残留中（P1） | checklist_library steps 4 处 → 机制形态（ktor+etdd→框架 CAND 对照法/kses_init→脚本过滤回调/ETagHashes→哈希缓存键; :174 binding keywords "netty" 删; uwebsockets/hikaricp 在 source_lessons=合法来源列保留）; task_templates 2 处 → 机制形态 + `_scan_runtime_assets` 扫 task_templates（注入违规测试闭环）; parser_fuzz_c.py docstring → 通用形态; target_kind.py 正则删 BeanContainerManager/ActixSystem::new 补 SpringApplication.run; SKILL.md 主文 :73/:93/:140 → 机制形态（:41/:44 来源/历史验证叙述保留） |
| 过设计 B（P2） | B1 **全裁** ast_scanner 三联体（与评估「保留 ast_scanner」倾向的差异见 SWR_V3_5_2.md——security_profiles 唯一读者是 ast_scanner 自身, 保扫描器裁其唯一输入=保空壳）; B2 裁 r05_diff_archaeology; B3 grade-recheck 降可选维修工具; B4 裁 repair_surfaces; B5 裁 signature_tier/empirical_harness 字段（needs_harness 保留——test_integration 消费, 仅裁 check CLI）; B6 裁 harness_coverage_matrix; B7 parser_fuzz 补 SKILL.md R5 枚举; B8 裁 9 条永不可达先例（25→16, 全部可 match 触达有测试）; B9 CK-EMPIRICAL-SCOPE 真实绑定（R5 语义空间触发, 删 matched=[] 特判）; B10 无动作 |
| 偏见机械（P3） | 语言词汇归一（_LANG_ALIAS 补 typescript→javascript; EXT_LANG_ALIAS cs→csharp/ts/typescript/js→javascript; L2 过滤双侧归一化; 跨模块一致性测试）; harness_runner manual/traps 缺 lang 报 usage（删默认 rust）; lang_pair 白名单删除; boundary +cgo（描述文补 cgo/capi）; 步骤 5.5 Go 习语中立化; 双轨词汇文档（project_kind vs target_kind 两轴注） |
| 防回退 | test_precedents_all_matchable / test_ck_empirical_scope_binds / test_lang_alias_consistency / test_harness_cli_requires_lang / test_sk_parser_fuzz_listed / task_templates 注入违规测试（193 passed）; tracking 六处状态真话修复 |

### 未修（留 v3.6，内容补全类，非缺陷）
- 8 语言 harness 模板补全（L2 词族语言实证模板缺口）
- L2 词族 5 语言签名缺（swift/ps/objc/lua/cs 词族扩充）
- env 陷阱 9 语言补全（harness_manuals 陷阱清单 7/16）
- swift 回归锚点缺失（known_instances）
- L3 语义族脚本 token 补全

---

## 五、验收对照（v3.5）

- 验收项目: phpseclib/phpseclib（PHP composer 纯密码学库）→ 补 php×CRYPTO 零格
- 检验点: B3 全链（.php 白名单 + _SRC_EXTS + composer.json 新解析 + 无 main→library 泛化）、B2 script 族措辞、B4 CRYPTO-WEAK 对 PHP 的可用性
- 退候选: jose-jwt（csharp×CRYPTO）、Template::Toolkit（perl×INJECTION）
