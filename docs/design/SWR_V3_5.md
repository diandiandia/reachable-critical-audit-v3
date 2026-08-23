# SWR-V3.5 需求（15 条）

> 设计: SYSTEM_DESIGN_V3_5.md。来源: v3.5 三项体检（偏见 / 过设计 / 项目残留），
> 完整发现见 `docs/history/HEALTHCHECK_EVAL_V3_5.md`。
> 里程碑: M2 = 残留（001/002/003），M1 = 偏见（004~009），M3 = 死资产（010~013），
> M4 = 文档+测试（014/015）。

---

## SWR-V3.5-001: 先例库形状抽象（M2，A1）

**缺陷**: precedent_library.json 的 name/criterion/counterexample/applicability_scope/
applications 五字段携带 ~60 处项目 CAND-id（Pester/ohmyzsh/Newtonsoft/Vapor/Dubbo/
Django/actix/sinatra/lighttpd/Ktor/Lersosa/Lua/PyJWT…），经 self_refutation_hints()
**运行时注入 verifier 任务书**——违反第一原则三禁止①（项目名进运行时资产）。
实测含 `checkAutoType`（大小写混合命中 DEPROJECT_BLACKLIST）等专属 API 名。

**修复**:
- 4 处项目名（PREC-ENGINE-MATRIX-001 scope=Netty 等）→ 机制形态描述
- applications ~60 处统一改写为「CAND-xxx (机制形态一句话)」格式；项目名只留
  source_lessons 追溯字段
- counterexample 的 `checkAutoType` → 「Java 反序列化自动类型解析」

**验收**:
- test_precedent_library_fields_generic 全绿（五字段零 token 零 /root/）
- R0 selfcheck 完整性分支零违规

---

## SWR-V3.5-002: xss_path_sim 去项目化（M2，A2）

**缺陷**: templates/harness/xss_path_sim.pl 整文件为 AWStats 复刻（awstats.pl/
CleanXSS/硬编码行号），被 signature_library.json empirical_harness ×2 与
harness_runner TEMPLATES 运行时接线——CleanXSS 恰在 DEPROJECT_BLACKLIST 上
（黑名单只扫签名资产、未扫模板，属覆盖盲区）。

**修复**:
- 整文件移入 `tests/fixtures/xss_path_sim_awstats_anchor.pl`（fixture 豁免区 +
  溯源注释）
- `templates/harness/xss_path_sim.pl` 原位重写为参数化通用骨架（argv 读 JSON
  链描述 decode_chain/sanitize_chain/sink，无行号/无项目名/无 CleanXSS）
- **模板名不变** → 全部接线保持（empirical_harness/harness_runner/
  harness_coverage_matrix/SKILL.md）

**验收**:
- test_fixture_anchor_compliant 全绿（fixture 含 CleanXSS，live 模板不含、
  awstats 不出现）
- selfcheck 完整性分支零违规

---

## SWR-V3.5-003: 手册抽象（M2，A3）

**缺陷**: harness_manuals/*.md 指令性正文含项目名（java=Dubbo/fastjson2/HikariCP、
kotlin=ktor/maxDecodedContentLength、python=Django get_host/read_body 等）+ 6 处
/root/ 绝对路径（ENVIRONMENT_PROBES/rust/cs/shell/perl/powershell/python）——
违反三禁止①③。

**修复**: 项目名 → 机制形态 + W6 § 引用（「WS 帧长上限配置项定位与验证法」类）；
6 处 /root/ 绝对路径 → $HOME/环境变量占位；改写清零 DEPROJECT_BLACKLIST token
（get_host/read_body/maxdecodedcontentlength/cleanxss 等，否则 R0 selfcheck 自伤）。

**验收**:
- test_runtime_assets_zero_project_tokens 全绿（templates/harness + harness_manuals
  零 token 零 /root/）

---

## SWR-V3.5-004: harness 端口参数化（M1，B1）

**缺陷**: ws_frame_alloc.py 硬编码 ktor 端口 18083、ws_frame_accum.py 硬编码
actix 端口 18084——v3.2.2 P-A 改革漏掉模板目录，历史战役专属值进入运行时模板
（偏见 + 残留同根）。

**修复**: `python3 ws_frame_*.py <host> <port>` 必传参数，缺参报错（不设默认
端口）；docstring 去 ktor/actix。

**验收**:
- test_harness_templates_no_hardcoded_ports 全绿（模板零 18083/18084，argv
  必传形态在位）

---

## SWR-V3.5-005: step 0.5 static_short 按语言家族分派（M1，B2）

**缺陷**: batch_verify.py step 0.5 static_short 措辞为「CMake 源列表/GOPATH/
cargo 目标/Makefile」纯 C 系词汇——IMPORTABILITY_FULL_LANGS={python,javascript,
java} 之外的 13 语言在非 application 目标下全落该措辞，派发给 kotlin/scala/
csharp/php/ruby/swift/perl/powershell/shell 的库型候选语义错配（脚本语言无构建
系统、JVM/.NET 无 CMake/GOPATH）。

**修复**: STATIC_SHORT_BY_FAMILY 按 lang 家族分派——c/cpp 现措辞保留；
go（go.mod 依赖树）/rust（cargo 目标）/kotlin+scala（sourceSet/Maven module）/
csharp（.csproj/.sln）/swift（Package.swift）/script 族（php require/include、
ruby require、perl use/require、powershell Import-Module、shell source）。
通用语义不变：链首模块在部署布局下能否被构建/加载（模块存在 ≠ 被包含）；
未知语言回退旧措辞；全检条件不变。

**验收**:
- test_step05_dispatch_family_wording（go.mod/sourceSet/.csproj/Package.swift/
  require 措辞抽样）+ test_step05_dispatch_script_family_no_c_words（script 族
  零 CMake/GOPATH/cargo/Makefile）全绿

---

## SWR-V3.5-006: R0 形态分类扩展名/包清单/listen 语言门补全（M1，B3a）

**缺陷**: target_kind.py 扩展名白名单缺 .swift/.kt/.cs/.pl/.pm/.ps1/.sh → 6 语言
「无源码文件 → 默认 application, confidence=low」（Swift 库与 C 库置信度不对称）；
pom.xml/composer.json/Gemfile 零解析；LISTEN_PATTERN 为 Go/Rust/Py/JS 词汇。

**修复**: 白名单补 7 扩展名；包清单解析补 pom.xml（packaging/mainClass/
spring-boot 信号）、composer.json（bin→app）、Gemfile/*.gemspec
（executables→app）；LISTEN_PATTERN 补 HttpListener/TCPServer/
stream_socket_server/IO::Socket::INET。

**验收**:
- test_target_kind_scans_new_extensions（.kt/.cs/.swift/.pl/.ps1/.sh 入扫）
  + test_target_kind_manifest_signals（spring-boot pom→app、composer bin→app、
  gemspec executables→app）全绿

---

## SWR-V3.5-007: surface_mapper 语言门补全 + 无-main 泛化（M1，B3b）

**缺陷**: surface_mapper.py Go/Java 独享「无 main→library」特判；_SRC_EXTS 缺
.scala/.php/.pl/.pm/.ps1/.sh；main 模式漏 Kotlin `fun main(`/C# `static void Main`/
Swift `@main`（re.MULTILINE 被当 pos 传，短文件行首锚定失效）；listen 模式漏
C# HttpListener/Ruby TCPServer/PHP stream_socket_server/Perl IO::Socket。

**修复**: _SRC_EXTS 补 6 扩展名；main_pat 补三模式（MULTILINE 移入 compile）；
listen_pat 补四词汇；Go/Java 独享特判 → LANG_NO_MAIN_LIBRARY = {go,java,kotlin,
scala,csharp,swift,php,ruby,perl,powershell,typescript}（排除 shell/c/cpp 保持
保守）；go/java 行为不变。

**验收**:
- test_exec_entry_kotlin_csharp_swift / test_listen_new_vocab /
  test_src_exts_covers_16_langs / test_no_main_generalized 全绿
- test_classify_four_values 零回退（go/java 判据不变）

---

## SWR-V3.5-008: 签名 fixture 全覆盖 + smoke 多实例回退 + 正则转义（M1，B4）

**缺陷**: 7/20 签名零 confirmed fixture（c/cpp/go 账本最重语言零代表，扩军签名
零回归保护）；6 个 L2 词族签名只有 v3.1 时代 line=1 假占位（confirmed=false，
无防回退价值）；4 条 v3.1 锚点因 master 内容漂移永不可命中；smoke_test 只试
第一个 confirmed 实例（不在传入 repos 时错误跳过）；`[ScriptBlock]::Create`
grep 模式未转义（字符类语义，真实代码从不匹配——旧占位 fixture 从未 smoke 过
因此潜伏）。

**修复**:
- 补 13 个 confirmed 实例（L3 系 7 + L2 词族 6 换真锚：mbedtls/libuv/uWebSockets/
  quic-go/orjson/dubbo/pyjwt/Pester/ohmyzsh/Newtonsoft.Json/django/ws/ktor）
- 漂移锚点重定位到 master 可命中行（sinatra host_authorization.rb:15、
  django validators.py:234）；无法重定位的删除
- smoke_test 多实例回退：某签名第一个 confirmed 不在传入 repos 时继续尝试
  其余实例
- hints 模式 `[ScriptBlock]::Create` → `\[ScriptBlock\]::Create`（真实缺陷修复）

**验收**:
- test_all_signatures_have_confirmed_fixture 全绿（每 sig_id ≥1 confirmed）
- `signature_lib.py selfcheck` 对 18 个锚点项目 → `hit_rate=100% testable=20`

---

## SWR-V3.5-009: 覆盖账本格压力提示（M1，B5）

**缺陷**: 覆盖账本无集中度提示——RESOURCE-DOS×go=55（占族行 24.7%），矩阵 144 格
41 零格，无选题引导；同形态项目（Go RPC server）波次式重复灌满同一格。

**修复**: _ledger_pressure 输出 pressure_cells（降序，count≥15 标 saturated）+
family_skew（top_share 降序）；LEDGER_GAPS 与 stage_report 各加选题提示「优先
补零格；saturated 格不建议再选题」。**无新门禁/无新持久字段/无新强制义务**
（三问：触发=ledger 读取/选题时；消费者=主代理；裁掉丢什么=rpcx 波次式同格
灌水 +14→55 无提示）。

**验收**:
- test_coverage_ledger_pressure 全绿（pressure_cells[0]=RESOURCE-DOS×go 55
  saturated；family_skew CRYPTO 1.0 第一）

---

## SWR-V3.5-010: 死 stage 删除（M3）

**缺陷**: batch_verify.py 三个死 stage 零派发方——next-cluster（:555-609）、
cluster-collect（:722-761，连 CLI）、coverage（:1031-1100，连 CLI）；r15 分支
（:1771-1773）同属死路径；4 个 CLI 参数随删。next 存活分支保留。

**修复**: 删死 stage + _build_cluster_prompt/_safe_name + 对应 CLI 参数；
删对应旧测试（test_batch_verify_v3.py:49-75,183-200）。

**验收**: 删除后 pytest 全绿（190 全绿内）＋ `--stage next` 行为不变（A' 降级链
存活）。

---

## SWR-V3.5-011: 死函数删除（M3）

**缺陷**: checklist_binder.bind_all/h7_template_bind（:144-174,159-161）、
precedent_library.record_application/add_precedent（:168-203）、
signature_matcher.emit_filter_tasks（:268-291）——零调用方（bind():88-141 存活），
各带专属 CLI。

**修复**: 删函数 + CLI 注册 + 对应测试（test_signature_matcher.py:60-67）。

**验收**: 删除后 pytest 全绿；`--stage bind-all` 等 CLI 不再存在。

---

## SWR-V3.5-012: 死字段 13 删除 + 门禁⑦ 语义保留（M3）

**缺陷**: 13 个死字段（paths_analyzed/path_count/verified_at/coverage_note/
schema_normalized_by/escalation_log/checklist_ids/checklist_bindings/
coverage_bridge/candidate.members/mechanism_correction/obligation_feedback/
schema_version）零读方（loaders 容忍未知键）；但 coverage_bridge 载体删除若
顺带删门禁⑦ 覆盖率簿记语义 = 功能回退（风险 1）。

**修复**: 删全部写方 + 任务书输出格式行 + 文档引用；**门禁⑦ 语义保留**——
SKILL.md 门禁代码块改传 `tracked_ids` + `mirror_pairs`（assert_ledger 自动镜像
传播，此前文档路径只传计数导致镜像传播被静默跳过）；:240-243 改写为「relay
中继面直接并入 tracked_ids，覆盖依据写入 R4 finding evidence 文本」。测试构造
键不清理（兼容旧队列）。

**验收**:
- 全库 grep 零写方；SKILL.md 门禁代码块含 tracked_ids+mirror_pairs
- pytest 全绿（test_v343.py:52,62 改断言、test_workflow_export.py:106 改断
  escalated_reason）

---

## SWR-V3.5-013: 死模板/悬空注册/死读删除（M3）

**缺陷**: 死模板 4/7（empirical_test/self_json_guard/verifier_refutation/
verifier_edge_proof——真实 prompt 由 workflow_export.refute_prompt /
batch_verify._build_prompt 代码生成，模板零派发方）；harness_runner multipart_align
注册条目指向不存在的文件（悬空引用）；harness_coverage_matrix unbounded×python
cell 指同文件；lessons_recorder 读 repair_stats.json（零写方）。

**修复**: 删 4 模板文件（task_templates 7→3）；删 multipart_align 注册 +
matrix cell 清空；删 repair_stats 死读块并重新编号段落。

**验收**:
- test_templates_registered_no_dangling 全绿（"multipart_align" not in
  TEMPLATES + 注册名↔磁盘文件一一对应）
- pytest 全绿

---

## SWR-V3.5-014: 文档修订（M4）

**缺陷**: SKILL.md 资产地图/README 计数全面陈旧（「13 签名/19 清单/19 先例/
3 模板/15 手册」实际 20/29/25/4/3/18；「73 个测试」实际 190；README 「期望 18」）。

**修复**: SKILL.md 资产地图 → 20 签名（9 L3 + 11 L2；回归锚点库在
tests/fixtures/known_instances.json，R0 完整性自检 + fixture 仓库 anchor recall）、
25 先例、29 清单、4 实证模板、3 任务书、18 手册（16 语言 + ENVIRONMENT_PROBES +
mixed_build）、190 测试；README 同步（:131 期望 18、:170-172、:175、:188-190）；
TOOLING_VERSION → "3.5"（workflow_export.py:22）。

**验收**:
- test_asset_counts_current（SKILL.md 计数 = 磁盘实况）+ test_readme_wc_line
  （「期望 18」）全绿

---

## SWR-V3.5-015: 运行时资产残留扫描 + 防回退测试体系（M4）

**缺陷**: DEPROJECT_BLACKLIST 只扫签名资产，模板/手册/先例库是覆盖盲区（001-003
根因）；tests 防回退 lint 仅覆盖 CK-PINNED-DEP 一条——残留回退无机器守卫。

**修复**:
- signature_lib `_scan_runtime_assets()`：遍历 templates/ + harness_manuals/
  （跳过 __pycache__），检查黑名单 token（大小写不敏感）+ /root/ 绝对路径，
  返回 [(relpath, hit)]；挂入 integrity_selfcheck（l2_manual_alignment 之后）
- 新增 tests/test_deproject_assets.py（5 用例：运行时资产零残留/先例库五字段/
  fixture 合规/known_instances 仅 fixtures/零硬编码端口）
- 追加防回退测试：test_selfcheck_flags_template_residue、test_all_signatures_
  have_confirmed_fixture、test_doc_lint 计数×2、test_batch_verify 分派×2 +
  ledger_pressure、test_surface_mapper 语言门×4、test_v321 扩展名/信号×2、
  test_harness_runner 注册断言加强

**验收**:
- 190 测试全绿（172 + 18 新增/改写）
- `signature_lib.py selfcheck` 自身仓库完整性分支零违规

---

## 验收总判据

1. 单测 190 全绿（172 + 18 新增/改写）
2. R0 锚点: `signature_lib.py selfcheck` 对 18 个锚点项目 → `hit_rate=100%
   testable=20`；自身仓库完整性零违规
3. 去项目化: test_deproject_assets.py 全绿（第一原则三禁止机器守卫）
4. phpseclib 新项目验收（P7）: 完整六门禁 + coverage-ledger --write 回填
   php×CRYPTO 零格 + install + 提交
