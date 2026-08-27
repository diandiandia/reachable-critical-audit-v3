# 语言偏向性评估 — Top15 语言 × 10 维度（2026-08-27）

> 目标：通用代码审计 skill。评估口径按四条纪律执行——
> ① 无语言偏向 ② 审计史不带入设计 ③ 不做单项目适配 ④ 后期修改不引入死代码/无用逻辑/过设计。
> 评估对象：skill 运行时资产（签名库/任务书/手册/模板/识别层/形态判定），
> 不含 lessons/ 与 docs/history/（历史归档区）。

## 一、口径

**Top15 语言**（TIOBE 2026-08 ∪ GitHub Octoverse 合并口径，剔除 VB/Assembly/Fortran 等
非通用开发语言）：Python、C++、C、Java、C#、JavaScript、Go、Rust、PHP、Swift、
Kotlin、Ruby、TypeScript、Scala、SQL。

**10 个偏向性维度**（每维对应一个运行时资产面）：

| 维度 | 对应资产 | 偏向性含义 |
|---|---|---|
| D1 签名库 L2 词族 | resources/signature_library.json | 候选提取佐证词族有无该语言条目 |
| D2 语言识别与扩展名 | CODE_EXTENSIONS / _EXT_LANG / EXT_LANG_ALIAS | 源码能否被盘点/识别 |
| D3 构建清单识别 | BUILD_FILES (surface_mapper) | R0/R1 能否识别该语言项目形态 |
| D4 R1 测绘任务书 | surface_map_domain + domain_guides | 测绘指引是否语言中立 |
| D5 R3 验证任务书语言段 | IMPORTABILITY_STEPS / STATIC_SHORT_BY_FAMILY / FULL_LANGS | 预检段覆盖深度 |
| D6 R4 假说任务书中立性 | biz_hypothesis.md | 是否语言中立 |
| D7 R5 实证资产 | templates/harness + harness_manuals | 实证模板/手册覆盖 |
| D8 裁决资产中立性 | checklist_library / precedent_library | 29 清单 / 16 先例是否语言中立 |
| D9 形态判定 token | LISTEN_PATTERN (target_kind) | 服务器形态识别有无该语言 token |
| D10 历史残留 | deproject 扫描 / 黑名单 / 资产全文 | 行为层是否携带审计史项目名 |

**判定符号**：● 充分 / ◐ 部分（代理覆盖或仅短段） / ○ 盲区 / — 不适用。

## 二、资产数据底座（评估事实）

| 资产 | 实测分布 |
|---|---|
| L2 词族 | 16 语言各 1 族 + any×9：c/cpp/cs/go/java/kotlin/perl/php/powershell/python/ruby/rust/scala/shell/swift/typescript（typescript 族经双侧归一覆盖 js/ts） |
| 语言识别 | CODE_EXTENSIONS 23 项（含 .m/.mm）；batch_verify _EXT_LANG 25 项（**缺 .m/.mm/.sql**）；alias 表映射 objc/lua |
| 构建清单 | 12 项：Package.swift/Cargo.toml/pom.xml/build.gradle/CMakeLists.txt/package.json/go.mod/pyproject.toml/requirements.txt/Gemfile/composer.json/Makefile |
| R3 语言段 | bespoke 6（python/c/cpp/go/rust/java）+ short 11（go/rust/kotlin/scala/csharp/swift/php/ruby/perl/powershell/shell）+ 中立 default/static_short；FULL_LANGS={python,javascript,java} |
| R5 模板 | 5 件 = 通用 3（resource_rate/ws×2）+ 语言专属 2（parser_fuzz_c.py、xss_path_sim.pl） |
| R5 手册 | 16 语言 + ENVIRONMENT_PROBES + mixed_build（**无 javascript.md**，由 typescript.md 代理） |
| 裁决资产 | 29 清单 / 16 先例：零 lang 字段，全语言中立 |
| 形态判定 | LISTEN_PATTERN 17 token（v3.8 已补 Java NIO 2 项） |
| 历史残留 | 行为层（detection_hints/触发条件）零项目名；tier_note/手册例证/代码注释/SKILL.md 含审计史引用（traceability，非行为） |

## 三、15×10 评估矩阵

| 语言 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Python | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| C++ | ● | ● | ● | ● | ● | ● | ● | ● | ◐ | ● |
| C | ● | ● | ● | ● | ● | ● | ● | ● | ◐ | ● |
| Java | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| C# | ● | ● | ○ | ● | ● | ● | ● | ● | ● | ● |
| JavaScript | ● | ● | ● | ● | ● | ● | ◐ | ● | ◐ | ● |
| Go | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| Rust | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| PHP | ● | ● | ● | ● | ◐ | ● | ● | ● | ◐ | ● |
| Swift | ● | ● | ● | ● | ◐ | ● | ● | ● | ○ | ● |
| Kotlin | ● | ● | ◐ | ● | ● | ● | ● | ● | ○ | ● |
| Ruby | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● |
| TypeScript | ● | ● | ◐ | ● | ● | ● | ● | ● | ◐ | ● |
| Scala | ● | ● | ○ | ● | ● | ● | ● | ● | ○ | ● |
| SQL | ○ | ○ | ○ | ◐ | ○ | ● | ○ | ● | — | ● |

格注（关键判定依据）：
- **D1 JavaScript ●**：typescript 词族经 `norm_lang` 双侧归一（js/ts/typescript→javascript）
  实际覆盖 .js/.ts/.tsx surface——不是盲区，是代理覆盖，判充分。
- **D2/D5 附注**：`size_tier` 内联扩展名集合与 CODE_EXTENSIONS 不一致
  （缺 .cpp/.cc/.hpp/.m/.mm），**C++（top-2）源码不计入规模档位**——一致性 bug，见 F1。
- **D3 C# ○**：无 .csproj/.sln；**D3 Scala ○**：无 build.sbt；Kotlin ◐：build.gradle 有、
  .kts 变体缺；TypeScript ◐：package.json 间接、tsconfig.json 缺。
- **D5 PHP/Ruby ◐**：short 段含「加载闭包核对」语义适配，缺口有限；不升级 FULL（见 N3）。
- **D7 JavaScript ◐**：无独立手册，typescript.md 代理（JS/TS 环境陷阱高度重叠，见 N1）。
- **D7 形态注记 ▲**：模板库 5 件中 2 件语言专属（C fuzz / Perl XSS），由 lighttpd/AWStats
  审计史驱动；但机制通用、非项目专属（见 N4，不修）。
- **D9 Swift/Kotlin/Scala ○**：无任何服务器形态 token；PHP ◐ 靠通用 0.0.0.0 token 可达。
- **D10 全部 ●**：行为层（detection_hints/触发条件/steps 主体）零审计史项目名；
  黑名单 + deproject 扫描机制已在 R0 强制执行。

## 四、偏向热点与裁决

| id | 发现 | 裁决 |
|---|---|---|
| F1 | size_tier 扩展名集合与 CODE_EXTENSIONS 不一致，C++/objc 文件不计档 | **修**（一致性 bug，复用 CODE_EXTENSIONS） |
| F2 | SQL（top-15 唯一全盲）：.sql 不进识别层 | **修**（仅识别层 2 处，不加深度资产） |
| F3 | .m/.mm 在 CODE_EXTENSIONS/alias 有、_EXT_LANG 无（内部矛盾） | **修**（对齐 2 项） |
| F4 | 构建清单 5 缺口：.csproj/.sln/build.sbt/build.gradle.kts/tsconfig.json | **修**（文件名清单 5 项） |
| F5 | LISTEN_PATTERN 3 缺口：swift-nio/ktor/akka-http | **修**（框架通用 token 3 项） |
| N1 | JS 独立 L2 词族/独立手册 | 不修——ts 代理已充分，新增属冗余 |
| N2 | SQL 深度资产（L2 词族/手册/验证段） | 不修——SQLi 由宿主语言面 + CK 资产覆盖；识别层通了之后按需增长，硬凑违反「无用逻辑」纪律 |
| N3 | PHP/Ruby 进 FULL_LANGS | 不修——short 段已含动态加载语义适配，升级 = 重复机制 |
| N4 | C/Perl 专属实证模板 | 不修——机制通用（参数化骨架）、非项目专属，有回归价值 |
| N5 | 注释/手册/SKILL.md 中的审计史引用 | 不修——traceability；行为层零残留由 deproject 扫描持续守护 |

**审计史偏向性总体结论**：L2 词族/手册/验证段的 16 语言集合覆盖了 top-15 中 14 种
（SQL 除外），且 Perl/PowerShell/Shell 三个非 top-15 语言的存在不影响 top-15 覆盖完整性；
真正的偏向形态是 **D7 模板库的语言专属件（C/Perl）由审计史驱动**（形态级，机制通用）
与 **SQL 全盲**（历史从未审计过 SQL 项目）。行为层无项目专属适配——四条纪律中
「不做单项目适配」现状达标，「无语言偏向」有 5 处可修缺口。

## 五、最小修复清单（待批准落地）

| SWR | 文件 → 改动 | 测试 |
|---|---|---|
| SWR-V3.8-020 | surface_mapper.py `size_tier`：内联扩展名集合 → 复用 `CODE_EXTENSIONS` | .cpp 文件计入 medium/large 档回归 |
| SWR-V3.8-021 | signature_matcher.py `CODE_EXTENSIONS` + tools/batch_verify.py `_EXT_LANG`：补 `.sql`（仅识别层） | language_inventory 识别 .sql |
| SWR-V3.8-022 | tools/batch_verify.py `_EXT_LANG`：补 `.m`/`.mm`→objc（与 alias 表对齐） | 映射断言 |
| SWR-V3.8-023 | surface_mapper.py `BUILD_FILES`：补 `.csproj/.sln/build.sbt/build.gradle.kts/tsconfig.json` | 按 test_build_files_lowercase_variant 模式 |
| SWR-V3.8-024 | tools/target_kind.py `LISTEN_PATTERN`：补 `ServerBootstrap`(swift-nio)/`embeddedServer`(ktor)/`bindAndHandle`(akka-http) | test_v38 listen 断言 3 条 |

合计：5 文件 11 行级改动 + 5 组测试，零删除、零新机制、零语言专属逻辑新增。
