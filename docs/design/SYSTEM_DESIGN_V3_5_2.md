# v3.5.2 系统设计：残留中项清零 + 过设计 B 裁决执行 + 偏见机械修复

> 日期：2026-08-23。评估报告：`docs/history/HEALTHCHECK_EVAL_V3_5.md`（v3.5 三项体检完整发现 + B 裁决 10 项）。
> 范围（用户 AskUserQuestion 确认）：①残留中项全部 ②过设计 B 裁决 10 项（按评估倾向执行）
> ③偏见中「机械可修」项。内容补全类（8 语言 harness 模板 / L2 词族 5 语言 /
> env 陷阱 9 语言 / 锚点 swift / L3 语义族脚本 token）明确留 v3.6。
> 验收（用户确认）：回归验收——phpseclib R0 复跑 + SRC/DST pytest 全绿，不新增完整项目验收。
> 基线：HEAD `1b7045d`（v3.5.1）。实现前两项探查（消费者核实 + 残留/偏见定位）完成，行号均为实况。

## 1. 背景与动机

v3.5 三项体检修复了高优先级发现（残留 3 高 / 偏见 5 高 / 过设计 A 清单 / 文档漂移），
v3.5.1 追加修复账本 sources 36 条 /root/ 路径 + rationale 漏网 + 自检 resources/ 盲区。
评估报告「未修」清单仍剩三类，本版本按用户确认的范围全部处理：

1. **残留中项**：anchor_registry CVE 描述 3 处、checklist_library 4+2 处、task_templates
   例证、templates/harness docstring、target_kind 启动链正则、SKILL.md 主文例证——
   第一原则三禁止的延伸（运行时资产不得携带项目信息）
2. **过设计 B 裁决 10 项**：评估报告的 B 清单（上轮因范围选择未裁决），本版本按
   评估倾向 + 探查证据执行
3. **偏见机械项**：语言词汇跨模块不一致（账本幻影列实害）、harness_runner 默认 rust、
   lang_pair 白名单、boundary 缺 cgo、步骤 5.5 Go 习语、形态双轨词汇

## 2. 修复设计

### 2.1 P1 残留中项（去项目化，全部清零）

| 资产 | 实况 | 修法 |
|---|---|---|
| anchor_registry.json | 32 entries，项目名仅在 `cve` 字段（fastjson2/Drupalgeddon2/tengine/xquic/actix-files/Newtonsoft/AWStats） | **随 B1 三联体裁除而消失**（见 2.2 B1） |
| checklist_library.json | 6 处命中，实际需修 4：:70 ktor+etdd（steps）、:174 "netty"（binding keywords 运行时匹配词）、:214 kses_init、:271 ETagHashes StorageKey；:736 uwebsockets/:781 hikaricp 在 `source_lessons` = 合法来源列**保留** | steps 正文 → 机制形态 + W6 § 引用；keywords "netty" 删除（运行时匹配词不得是生态名） |
| task_templates | hypothesis_filter.md:25 mbedtls tf-psa-crypto、:38 quic-go 41→31 | → 机制形态（"C 库审计子模块中途物化" / "成熟网络库 41→31 实录"）；**自检闭环**：`_scan_runtime_assets` 扫描范围补 task_templates/ |
| templates/harness/parser_fuzz_c.py | docstring "mbedtls 审计实战模板化" | → "C 库审计实战模板化" |
| target_kind.py | :191-194 正则含 BeanContainerManager(Dubbo)/ActixSystem::new(actix) | 删项目专属类名，补通用等价 SpringApplication.run；wire/kratos/tokio/app.run 为通用框架词保留（netty 未被审计过=生态词也保留） |
| SKILL.md 主文 | 5 处命中：:41/:44（来源 blockquote/历史验证叙述=追溯形态**保留**）、:73/:93/:140（指令正文例证） | :73 → "C 库审计实战形态: 子模块中途物化"；:93 → "库型先例"；:140 → "成熟网络库 28 条全防御实录" |

### 2.2 P2 过设计 B 裁决执行（探查已核实）

| # | 项 | 探查证据 | 执行 |
|---|---|---|---|
| B1 | ast_scanner 三联体 | security_profiles 唯一读取方是 ast_scanner 自身（:928/:1186）；ast_scanner 零生产调用方（仅 test_tools_v3.py 2 个 helper 单测）；「按需使用」v3.1→v3.5 零触发 | **全裁**（ast_scanner.py 1212 行 + anchor_registry.json 32 条 + security_profiles.json 16123 行）。**与评估倾向差异见 §3** |
| B2 | r05_diff_archaeology.py | 仅测试消费（test_tools_v3.py:41,57）；R0.5 现役 = surface_mapper.py:940 scope_diff（调用方 batch_verify.py:1289） | 裁文件 + 2 子进程测试 + SKILL.md/README 引用 |
| B3 | grade-recheck | collect 内联重算 :431-448 已有且被 test_v343.py:105 测试；「collect 后强制」重复执行同一义务（三问①违规典型） | SKILL.md「collect 后强制」→ 可选维修工具；stage 处理器 :943 + CLI :1700 保留 |
| B4 | repair_surfaces | 零调用零测试 | 裁函数 :726-775 + CLI :978-984；size_tier 保留；tracking 虚假「已完成」→「已裁除」 |
| B5 | signature_tier/empirical_harness | 零机械读方（needs_harness :66-72 只读 claim_type+evidence_grade）；字段写入后无任何读方 | 裁字段（20 签名 + REQUIRED_FIELDS + matcher 输出 2 行）。**needs_harness 保留偏差见 §3** |
| B6 | harness_coverage_matrix.json | 零读者（REQ-V3.2.2-009「R5 引用矩阵缺口」无实现） | 裁文件；tracking「已完成」→「已裁除」 |
| B7 | parser_fuzz_c.py | harness_runner TEMPLATES :46-53（c/cpp）注册实存 | **保留**；SKILL.md R5 模板枚举补 parser_fuzz + 防回退测试 |
| B8 | 9/25 先例永不可达 | match() map（CWE_FAMILY/KEYWORD/MULTI-LANG）仅覆盖 16 条；按集合差确认 9 条永不可匹配 | 裁 9 条（PREC-ALLOC-VIRTUAL-001/BYDESIGN-001/CONSISTENCY-001/ENV-SAME-PRINCIPAL-001/FAMILY-CONSISTENCY-001/HARM-ABSORBED-001/IMPLICIT-SURFACE-001/IMPORT-BREAK-001/TARGET-KIND-001）；SKILL.md R0 主文 PREC id 引用同 commit 去悬空（规则文本保留）；计数 25→16 同步 SKILL.md:285 + test_doc_lint + README + HEALTHCHECK |
| B9 | CK-EMPIRICAL-SCOPE | checklist_binder.py:115-116 无条件 `matched=[]` + 声称「R5 显式绑定」无实现 | **实现真实绑定**：R5 语义空间（candidate 带 empirical dict 或 claim_type ∈ {crash,panic,oom,unbounded,xss,protocol_dos,rce,leak}）时绑定；tracking SWR-V3.1-020 改真实描述；加绑定测试 |
| B10 | 文档漂移 | v3.5 已修 | 无动作 |

**tracking 真话修复（同批）**：REQUIREMENTS_TRACKING.md REQ-V3-012~016（r05 已裁除）、
SWR-V3-040（needs_harness 已完成）、SWR-V3.1-002（repair 已裁除）、SWR-V3.1-020（B9 注）、
REQ-V3.2.2-009（矩阵已裁除）、REQ-V3-002（三联体已裁除）。评估报告行号陈旧记入 SWR_V3_5_2.md，
不改历史文档。

### 2.3 P3 偏见机械项

1. **语言词汇归一（canonical = 账本 16 名：perl/powershell/shell/csharp/python/javascript/
   java/kotlin/scala/go/c/cpp/rust/php/ruby/swift）**：
   - `batch_verify._LANG_ALIAS` 补 `"typescript": "javascript"`——否则 typescript 候选
     写入账本幻影列（账本 langs 无 typescript，实害）
   - `signature_matcher.EXT_LANG_ALIAS` 改 cs→csharp、ts/typescript/js→javascript（对齐
     batch_verify）；**L2 过滤双侧归一化**（`norm_lang(surface) == norm_lang(sig.lang)`）——
     签名标签 cs/typescript 是签名侧内部名，归一后等值比较，不破坏现役 L2 匹配
   - `signature_lib.VALID_LANGS` 保留 superset（签名标签内部名）
   - SKILL.md 数据模型段注两行：语言词汇两轴 + 形态判定两轴（project_kind vs target_kind）
   - harness_manuals/cs.md、typescript.md 文件名不动（手册命名沿用签名标签）
2. **harness_runner.py 默认 lang "rust"**（manual/traps CLI :286/:294）→ 缺参报 usage
   exit=2，不设默认（语言偏见）
3. **lang_pair 白名单**（:241-243 硬编码 {c,py,rust,js,ts}）→ 删白名单，任意 token
   小写接受（kotlin/go 等混合对曾不触发混合实证提示）
4. **boundary 补 cgo**：BOUNDARY_KINDS + "cgo"；:452-453 描述文 + cgo + capi
   （capi 已在 changelog 但未传播主文——一并修）；SKILL.md v3.2 增量段同步
5. **步骤 5.5 Go 习语**（`if err == nil` / "空实体+nil error"）→ 语言中立措辞
   （Go 习语作为示例附注保留一处）
6. **形态双轨词汇**：SKILL.md 数据模型段注明两轴（project_kind=R1 上下文信号 4 值 /
   target_kind=R0 门禁 3 值）；surface_mapper.py docstring 交叉引用。不合并代码语义

### 2.4 P4 文档 + 防回退测试

- SKILL.md 资产地图：删 r05/ast_scanner/security_profiles/harness_coverage_matrix 引用；
  先例 25→16；R5 模板枚举补 parser_fuzz；测试计数按实况回填（193）
- REQUIREMENTS_TRACKING.md 六处修正（见 2.2）
- 新测试 6 个：test_precedents_all_matchable（match() 可达集 == 库 id 集，双向）/
  test_ck_empirical_scope_binds / test_lang_alias_consistency（共享键取值一致 +
  账本 16 名归一保持 + L2 双侧归一化命中）/ test_harness_cli_requires_lang /
  test_sk_parser_fuzz_listed / task_templates 注入违规拦截
- 删测试：test_tools_v3.py 整文件（r05×2 + ast_scanner helper×2）
- HEALTHCHECK_EVAL_V3_5.md：未修清单移入「v3.5.2 已修」+ B1 全裁记录 + 留 v3.6 清单

### 2.5 P5 版本链

SWR_V3_5_2.md + SYSTEM_DESIGN_V3_5_2.md + SKILL.md「## 🆕 v3.5.2 增量」段
+ workflow_export.py TOOLING_VERSION "3.5"→"3.5.2"

## 3. 与评估倾向的差异（两处，批准本方案即同意）

1. **B1 全裁 vs 评估倾向「保留 ast_scanner、裁 security_profiles」**：
   探查证据——security_profiles.json 唯一读取方是 ast_scanner 自身，ast_scanner 零生产
   调用方；「按需使用」v3.1→v3.5 零触发。**保扫描器裁其唯一功能输入 = 保空壳**。
   实际执行：三联体全裁。
2. **B5 needs_harness 保留 vs 计划初稿「连带一并裁」**：
   探查代理曾报告「零调用方」，但 grep 复核发现 tests/test_integration.py:82 将
   needs_harness 用作 R5 触发判定（步骤 6）——计划表「连带：needs_harness + check CLI
   一并裁」据此修正为：保留 needs_harness + 3 个单元测试 + 集成测试，仅裁 `check` CLI。

## 4. 验收（回归，用户确认）

1. `python3 -m pytest tests/ -q` 全绿（193：删 4 增 6 后回填 SKILL.md 计数）
2. `python3 signature_lib.py selfcheck /root/phpseclib` exit 0（R0 复跑）
3. `./install.sh`（sync-delete :29-38 自动清 DST 已删资产）→ DST pytest 全绿
4. 分阶段 commit：P1（残留）→ P2（过设计 B）→ P3-P4（偏见机械 + 文档测试）→ P5-P6（版本 + 验收）

## 5. 风险与注意点

1. **B1 全裁与评估倾向的差异**是本版本唯一的范围偏离项——证据在 2.2，批准即同意
2. 先例裁 9 条：precedent_library.py 的 map 不含被裁 ID（已核实不可达），但 SKILL.md
   主文 PREC id 引用须同 commit 去悬空（:91 已处理）
3. target_kind 正则改动：确认无测试 fixture 依赖 Dubbo/actix token（实现前跑基线全绿确认）
4. `_scan_runtime_assets` 扩 task_templates：先清零模板内项目名，否则 selfcheck 自伤
5. `_LANG_ALIAS` 补 typescript→javascript：账本历史行不动（幂等身份 + rows 累加不受影响），
   仅未来写入归一
6. 黑名单 token（lersosa/checkautotype 等）保留——守卫弹药不裁；source_lessons 字段
   项目名保留——合法来源列
7. harness_manuals 文件名不改名（cs.md/typescript.md 保留），避免 churn；归一规则文档化
