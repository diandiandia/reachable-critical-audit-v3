# v3.5 系统设计：三项体检修复（偏见 / 过设计 / 项目残留）

> 日期：2026-08-23。评估报告：`docs/history/HEALTHCHECK_EVAL_V3_5.md`（完整发现清单 + B 裁决 10 项 + 语言×资产矩阵）。
> 范围：rpcx 验收（v3.4.6）后对 skill 本体做三项体检；用户确认修复 = 高优先级发现（残留 3 + 偏见 5）+ 过设计 A 清单死资产 + 文档漂移；中低优先级与 B 裁决清单只记入评估报告不修复。
> 里程碑：M1 = 偏见 B1-B5（SWR-004/005/006/007/008/009），M2 = 残留 A1-A3（SWR-001/002/003），M3 = 过设计 A 清单（SWR-010~013），M4 = 文档+测试（SWR-014/015）。

## 1. 背景与动机

设计初衷：通用型代码审计 skill——Top15 语言 × 每语言 Top10 问题。迭代（v2.1→v3.4.6）中三条防线需要体检：

1. **偏见**：资产分布失衡、核心机制默认绑定某语言、任务书思维定式——通用 skill 不允许向任何语言收敛
2. **过设计**：义务棘轮堆出无消费者机制（REQ-V3.3.2-022 三问：触发条件/消费者/裁掉丢什么）
3. **项目残留**：第一原则三禁止——运行时资产不得携带具体项目名/目录结构/专属 API；允许位置仅 tests/fixtures 与 lessons 追溯字段

体检实测的**高优先级发现**（数字均由脚本实算）：
- 残留 3：precedent_library 五字段 ~60 处项目 CAND-id 运行时注入 verifier 任务书；xss_path_sim.pl 全文 AWStats 复刻；harness_manuals 指令性正文含项目名 + 6 处 /root/ 绝对路径
- 偏见 5：harness 模板硬编码 ktor/actix 端口；step 0.5 static_short 纯 C 系词汇；R0 形态分类双重语言门（扩展名白名单缺 7 语言 + Go/Java 独享无-main 特判）；7/20 签名零 fixture；覆盖账本 RESOURCE-DOS×go=55 单格饱和无提示
- 附带：multipart_align 悬空注册；SKILL.md 资产计数全面陈旧

## 2. 修复设计

### 2.1 M2 残留（A1-A3）

**A1 先例库形状抽象**（precedent_library.json）
- self_refutation_hints() 只渲染 name/criterion/applicability_scope 三字段——4 处项目名（PREC-ENGINE-MATRIX-001 scope=Netty 等）改机制形态描述
- applications ~60 处统一改写为「CAND-xxx (机制形态一句话)」格式；项目名只留 source_lessons 追溯字段
- 残留扫描（v3.5 实测）：PREC-TYPE-SYSTEM-001 counterexample 的 `checkAutoType` 一并抽象

**A2 xss_path_sim 去项目化**
- 整文件移入 `tests/fixtures/xss_path_sim_awstats_anchor.pl`（fixture 豁免区 + 溯源注释）
- `templates/harness/xss_path_sim.pl` 原位重写为参数化通用骨架（argv 读 JSON 链描述 decode_chain/sanitize_chain/sink，无行号/无项目名/无 CleanXSS）
- **模板名不变** → signature_library empirical_harness、harness_runner TEMPLATES、harness_coverage_matrix、SKILL.md 全部接线保持

**A3 手册抽象**（harness_manuals/*.md）
- java/kotlin/python/php 等手册项目名 → 机制形态 + W6 § 引用；6 处 /root/ 绝对路径 → $HOME/环境变量占位
- 改写必须清零 DEPROJECT_BLACKLIST token（否则 R0 selfcheck 自伤）

### 2.2 M1 偏见（B1-B5）

**B1 harness 端口参数化**：ws_frame_alloc.py/ws_frame_accum.py 的 18083/18084 → `python3 ws_frame_*.py <host> <port>` 必传参数，缺参报错不设默认端口；docstring 去 ktor/actix

**B2 static_short 按语言家族分派**（batch_verify.py STATIC_SHORT_BY_FAMILY）
- c/cpp 现措辞保留；go（go.mod 依赖树）/rust（cargo 目标）/kotlin+scala（sourceSet/Maven module）/csharp（.csproj/.sln）/swift（Package.swift）/script 族（php require/include、ruby require、perl use/require、powershell Import-Module、shell source）
- 通用语义不变：链首模块在部署布局下能否被构建/加载（模块存在 ≠ 被包含）；未知语言回退旧措辞；全检条件不变

**B3 语言门补全**
- target_kind.py：扩展名白名单补 .swift/.kt/.cs/.pl/.pm/.ps1/.sh；包清单解析补 pom.xml（spring-boot/mainClass/war）、composer.json（bin）、Gemfile（服务器 gem）、*.gemspec（executables）；LISTEN_PATTERN 补 HttpListener/TCPServer/stream_socket_server/IO::Socket::INET
- surface_mapper.py：_SRC_EXTS 补 .scala/.php/.pl/.pm/.ps1/.sh；main_pat 补 Kotlin `fun main(`/C# `static void Main`/Swift `@main`（re.MULTILINE 移入 compile 修复短文件行首锚定失效）；listen_pat 补同四词汇
- Go/Java 独享无-main 特判 → LANG_NO_MAIN_LIBRARY = {go,java,kotlin,scala,csharp,swift,php,ruby,perl,powershell,typescript}（排除 shell/c/cpp 保持保守）；go/java 行为不变（test_classify_four_values 判据）

**B4 签名 fixture 全覆盖**（tests/fixtures/known_instances.json）
- 7 个 L3 系签名补 confirmed 实例（mbedtls/uWebSockets/quic-go/orjson/dubbo/libuv/mbedtls-crypto）
- **扩军至 20/20**：6 个 L2 词族签名（PS/SH/CS/PY/TS/KT）删除 v3.1 时代 line=1 假占位，换真实项目锚点（Pester/ohmyzsh/Newtonsoft.Json/django/ws/ktor）
- 4 条 v3.1 漂移锚点（awstats.pl:18062、django csrf.py:282 等）重定位到 master 可命中行
- smoke_test 多实例回退：某签名第一个 confirmed 不在传入 repos 时继续尝试其余实例
- 存量缺陷修复：`[ScriptBlock]::Create` grep 模式未转义（字符类语义，真实代码从不匹配——旧占位 fixture 从未 smoke 过因此潜伏）
- 验收口径：selfcheck 传全部 18 个锚点项目 → hit_rate=100% testable=20

**B5 账本格压力**（batch_verify.py _ledger_pressure）
- pressure_cells（降序，count≥15 标 saturated）+ family_skew（top_share 降序）
- LEDGER_GAPS 与 stage_report 各加选题提示「优先补零格；saturated 格不建议再选题」
- 无新门禁/无新持久字段/无新强制义务（三问：触发=ledger 读取/选题时；消费者=主代理；裁掉丢什么=rpcx 波次式同格灌水 +14→55 无提示）

### 2.3 M3 过设计 A 清单死资产

| 资产 | 动作 |
|---|---|
| 死 stage：next-cluster/cluster-collect/coverage + r15 分支 + 4 个 CLI 参数 | 删（next 存活分支保留） |
| 死函数：checklist_binder.bind_all/h7_template_bind、precedent_library.record_application/add_precedent、signature_matcher.emit_filter_tasks + 对应 CLI | 删 |
| 死字段 13：paths_analyzed/path_count/verified_at/coverage_note/schema_normalized_by/escalation_log/checklist_ids/checklist_bindings/coverage_bridge/candidate.members/mechanism_correction/obligation_feedback/schema_version | 删写方+文档+测试断言（loaders 容忍未知键，旧队列兼容） |
| 死模板 4/7：empirical_test/self_json_guard/verifier_refutation/verifier_edge_proof | 删文件（真实 prompt 由代码生成） |
| 悬空注册：harness_runner multipart_align（文件缺失）+ harness_coverage_matrix unbounded×python cell | 删 |
| 死读：lessons_recorder repair_stats.json（零写方） | 删 |

**门禁⑦ 语义保留（风险 1 对策）**：coverage_bridge 字段载体删除但覆盖率簿记语义保留——
SKILL.md 门禁代码块改传 `tracked_ids` + `mirror_pairs`（assert_ledger 自动镜像传播，此前文档路径只传计数导致镜像传播被静默跳过）；relay 中继面直接并入 tracked_ids，覆盖依据写入 R4 finding evidence 文本

### 2.4 M4 文档 + 防回退测试

- SKILL.md 资产地图 13/19/19/3/15 → 20/29/25/4/3/18；README 同步
- 新增 tests/test_deproject_assets.py（运行时资产零 token 零 /root/、先例库五字段、fixture 合规、零硬编码端口）
- signature_lib `_scan_runtime_assets()` 挂入 integrity_selfcheck——R0 selfcheck 完整性分支拦截模板/手册残留回退
- test_doc_lint 资产计数防漂移；test_step05_dispatch_*（家族措辞 + script 族零 C 系词）；test_coverage_ledger_pressure；test_surface_mapper 语言门（exec/listen/_SRC_EXTS/无-main 泛化）；test_v321 manifest 信号；test_all_signatures_have_confirmed_fixture

## 3. 验收

1. **单测**：190 全绿（172 + 18 新增/改写）
2. **R0 锚点**：`signature_lib.py selfcheck` 对 18 个锚点项目 → hit_rate=100% testable=20
3. **去项目化**：test_deproject_assets.py 全绿 + skill 自身 R0 完整性零违规
4. **新项目验收（P7）**：phpseclib（php×CRYPTO 零格）完整六门禁 + coverage-ledger --write 回填 + install + 提交
