# SWR-V3.5.2 修复记录（残留中项清零 + 过设计 B 裁决执行 + 偏见机械修复）

> 设计: SYSTEM_DESIGN_V3_5_2.md。来源: HEALTHCHECK_EVAL_V3_5.md 未修清单。
> 版本链: 本文件 + SKILL.md「🆕 v3.5.2 增量」段 + TOOLING_VERSION "3.5.2"。
> 基线: `1b7045d`（v3.5.1）→ P1 `0ff669b` → P2 `48df95f` → P3 `1c6a670` → P4 `6f1cf04` → P5-P6。

---

## 一、P1 残留中项（去项目化，全部清零）

### 1.1 checklist_library steps 去项目化（4 处）

- CK-UNBOUNDED-HOPS steps「ktor CAND-001 对照 etdd CAND-004」→「框架 CAND-001 对照
  etcd CAND-004 双实测量级对照法」（等量级框架对照语义保留，项目名清除）
- CK-DYNAMIC-DEFENSE「kses_init 类」→「脚本语言过滤回调类」
- CK-DEAD-CACHE「ETagHashes StorageKey 先例」→「哈希缓存键未注册先例」
- CK-… :174 binding keywords `"netty"` 删除（**binding keywords 是运行时匹配词**，
  生态框架词不得作匹配触发词）
- 保留：:736 uwebsockets / :781 hikaricp 位于 `source_lessons` 字段 = 合法来源列
  （第一原则：项目名只允许出现在追溯字段）

### 1.2 task_templates 例证去项目化（2 处）

- hypothesis_filter.md:25「mbedtls 审计: tf-psa-crypto 中途物化…」→「C 库审计实战
  形态: 子模块中途物化 使"树外不可验证"drop 作废」
- hypothesis_filter.md:38「quic-go 41→31 实录」→「成熟网络库 41→31 实录」

**自检闭环（REQ-V3.2.2-005 延伸）**：`signature_lib._scan_runtime_assets` 扫描范围
补 `task_templates/`（黑名单 + /root/ 全扫）——任务书模板同 templates/harness 义务。
防回退测试：注入项目 token 的任务书模板必须被拦截。

### 1.3 templates/harness/parser_fuzz_c.py docstring

「通用形态 (mbedtls 审计实战模板化)」→「通用形态 (C 库审计实战模板化)」

### 1.4 target_kind.py 启动链正则（:191-194）

- 删项目专属类名：`BeanContainerManager`（Dubbo）、`ActixSystem::new`（actix）
- 补通用等价：`SpringApplication\.run`（Java 应用启动通用形态）
- 保留通用框架词：`wire.Build` / `kratos.New` / `#[tokio::main]` / `app.run()`；
  及 netty 类生态词（未被审计过，无残留语义）

### 1.5 SKILL.md 主文（3 处例证 → 机制形态；2 处追溯保留）

- :73「mbedtls 审计实战形态」→「C 库审计实战形态: 子模块中途物化」
- :93「Newtonsoft.Json 先例」→「库型先例」
- :140「quic-go 28 条全防御」→「成熟网络库 28 条全防御实录」
- 保留：:41（第一原则来源 blockquote）/ :44（v3 验证叙述）= 来源/历史验证叙述形态

---

## 二、P2 过设计 B 裁决执行（10 项）

| # | 执行 | 验收 |
|---|---|---|
| B1 | 裁 ast_scanner.py（1212 行）+ anchor_registry.json（32 条）+ security_profiles.json（16123 行）。REQ-V3-002 tracking → 已裁除。SKILL.md 资产地图/README 1.3 节同步 | 无任何模块 import 悬空；R0/R2/R3 链路不引用 |
| B2 | 裁 tools/r05_diff_archaeology.py + tests/test_tools_v3.py:41,57（2 子进程测试）+ SKILL.md/README 引用。R0.5 现役 = surface_mapper.scope_diff（batch_verify.py:1289 消费） | scope_diff 测试全绿 |
| B3 | SKILL.md「collect 后强制机械复核」→「collect 内联重算为默认, grade-recheck 降为可选维修工具」。stage 处理器 :943 + CLI :1700 保留 | test_v343.py:105（内联重算）全绿 |
| B4 | 裁 surface_mapper.repair_surfaces（:726-775）+ CLI repair（:978-984）。size_tier 保留。SWR-V3.1-002 tracking「已完成（测试通过）」→「已裁除」 | 零 import 悬空 |
| B5 | 裁 signature_library.json 20 签名 `empirical_harness` 字段 + signature_lib.REQUIRED_FIELDS + signature_matcher gen 输出 2 行（empirical_harness/signature_tier）。**needs_harness 保留**（test_integration.py:82 消费，R5 步骤 6 触发判定）——仅裁 harness_runner `check` CLI（:312）。SWR-V3-040 tracking「未开发」→「已完成（保留）」。list_templates 保留（SKILL.md R0 消费） | needs_harness 3 单测 + 集成测试全绿 |
| B6 | 裁 resources/harness_coverage_matrix.json（零读者）。REQ-V3.2.2-009 tracking「已完成」→「已裁除：R5 引用矩阵缺口无实现」 | 零引用 |
| B7 | parser_fuzz_c.py **保留**（TEMPLATES :46-53 注册 c/cpp）。SKILL.md R5 模板枚举补 parser_fuzz（:222） | test_sk_parser_fuzz_listed 全绿 |
| B8 | 裁 9 条永不可达先例：PREC-ALLOC-VIRTUAL-001 / PREC-BYDESIGN-001 / PREC-CONSISTENCY-001 / PREC-ENV-SAME-PRINCIPAL-001 / PREC-FAMILY-CONSISTENCY-001 / PREC-HARM-ABSORBED-001 / PREC-IMPLICIT-SURFACE-001 / PREC-IMPORT-BREAK-001 / PREC-TARGET-KIND-001（25→16）。SKILL.md:91 PREC-TARGET-KIND-001 引用 → 「先例规则文本，v3.5.2 起不设 PREC id」；SKILL.md:285/README/tracking 计数同步 | test_precedents_all_matchable（可达集 == 库 id 集，双向）全绿 |
| B9 | checklist_binder.py:115-116 删 `matched=[]` 特判 → R5 语义空间触发绑定：candidate 带 empirical dict **或** claim_type ∈ {crash,panic,oom,unbounded,xss,protocol_dos,rce,leak}（与 SKILL R5 强制声称集一致）时绑定，否则不绑定。SWR-V3.1-020 tracking 注 B9 | test_ck_empirical_scope_binds 全绿 |
| B10 | 文档漂移 v3.5 已修，无动作 | — |

**偏差说明（写入 SKILL.md 增量段 + 本文件）**：
1. **B1**：评估倾向「保留 ast_scanner、裁 security_profiles」；探查证据推翻（security_profiles
   唯一读者 = ast_scanner 自身；ast_scanner 零生产调用方；按需使用 v3.1→v3.5 零触发）。
   **执行：三联体全裁**——保扫描器裁其唯一功能输入 = 保空壳。计划批准即同意。
2. **B5**：计划初稿「连带 needs_harness + check CLI 一并裁」；探查复核发现
   tests/test_integration.py:82 消费 needs_harness（R5 触发判定步骤 6）。
   **执行：保留 needs_harness + 3 单测 + 集成测试；仅裁 check CLI**。

---

## 三、P3 偏见机械修复

| # | 修复 | 验收 |
|---|---|---|
| 1a | batch_verify._LANG_ALIAS 补 `"typescript": "javascript"`（账本幻影列实害：账本 langs 无 typescript） | test_lang_alias_consistency |
| 1b | signature_matcher.EXT_LANG_ALIAS：cs→csharp、ts/typescript→javascript、js→javascript（对齐 batch_verify；共享键取值一致） | 同上 |
| 1c | L2 过滤双侧归一化：`norm_lang(surface) == norm_lang(sig.lang)`——签名标签 cs/typescript 属内部名，归一后等值匹配（不破坏 SIG-CS-DESER-001/SIG-TS-ACCUM-001 现役 L2 命中） | test_lang_alias_consistency 的 L2 命中断言 |
| 1d | signature_lib.VALID_LANGS 保留 superset（签名标签内部名）；SKILL.md 数据模型段注语言词汇两轴（cs↔csharp、ts/typescript↔javascript、ps↔powershell） | validate 全绿 |
| 2 | harness_runner manual/traps CLI 缺 lang → usage exit=2（删默认 "rust"） | test_harness_cli_requires_lang |
| 3 | lang_pair 白名单 {c,py,rust,js,ts} 删除 → 任意 token 小写接受（mixed_build_hint） | 行为测试 + 无回归 |
| 4 | BOUNDARY_KINDS + "cgo"；R1 域描述文 + cgo + capi；SKILL.md v3.2 增量段同步 | validate 枚举校验全绿 |
| 5 | 步骤 5.5「if err == nil 块内处理错误分支 / 空实体+nil error」→ 语言中立（Go 习语作示例附注一处） | 文案审查 |
| 6 | 形态双轨词汇：SKILL.md 数据模型段注两轴（project_kind=R1 上下文 4 值 / target_kind=R0 门禁 3 值）；surface_mapper docstring 交叉引用 | 文案审查 |

---

## 四、P4 文档 + 防回退测试

- REQUIREMENTS_TRACKING.md 六处真话修复：REQ-V3-012~016（r05 已裁除）、SWR-V3-040
  （needs_harness 已完成）、SWR-V3.1-002（repair 已裁除）、SWR-V3.1-020（B9 注）、
  REQ-V3.2.2-009（矩阵已裁除）、REQ-V3-002（三联体已裁除）
- SKILL.md 资产地图：删 r05/ast_scanner/security_profiles/harness_coverage_matrix；
  先例 25→16（:285）；R5 模板枚举 + parser_fuzz（:222）；测试计数 190→193
- HEALTHCHECK_EVAL_V3_5.md：未修清单 → v3.5.2 已修全表（P1/P2/P3 + B1 全裁记录）；
  留 v3.6 内容补全清单（8 语言 harness 模板 / L2 词族 5 语言 / env 陷阱 9 语言 /
  锚点 swift / L3 语义族脚本 token）
- 新测试 6 个：test_precedents_all_matchable / test_ck_empirical_scope_binds /
  test_lang_alias_consistency / test_harness_cli_requires_lang /
  test_sk_parser_fuzz_listed / task_templates 注入违规拦截
- 删测试：tests/test_tools_v3.py（r05×2 + ast_scanner helper×2）

---

## 五、P5-P6 版本与验收

- TOOLING_VERSION "3.5" → "3.5.2"（workflow_export.py:22，导出/收集两侧版本一致性守卫）
- 验收（回归，用户确认）：
  1. SRC `python3 -m pytest tests/ -q` → 193 passed
  2. `python3 signature_lib.py selfcheck /root/phpseclib` → exit 0（phpseclib R0 复跑）
  3. `./install.sh` → DST pytest 全绿（sync-delete 自动清 DST 已删资产）
  4. 分阶段 commit 落地
- 内容补全类（8 语言 harness 模板 / L2 词族 5 语言 / env 陷阱 9 语言 / 锚点 swift /
  L3 语义族脚本 token）明确留 v3.6，不在本版本范围
