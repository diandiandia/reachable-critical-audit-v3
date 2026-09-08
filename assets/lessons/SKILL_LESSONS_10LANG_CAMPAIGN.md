# Reachable Critical Audit Skill — 10 语言补齐战役暴露的缺陷与改进建议

> **文档性质**：基于 2026-08-15 单日 10 项目战役（sinatra/ohmyzsh/actix-web/Newtonsoft.Json/AWStats/Pester/akka-http/nest/ktor/django，覆盖 Ruby/Shell/Rust/C#/Perl/PowerShell/Scala/TS/Kotlin/Python）对 skill v2.1 的回顾性缺陷分析。驱动 v2.2 设计。
>
> **关联归档**：各项目 `.audit_results/`；汇总 `/root/10LANG_AUDIT_SUMMARY.md`
> **交叉引用**：本战役是 [README 跨语言收敛清单](README.md) 的规模化验证——"89% 噪音诅咒"升级为"95%+ 噪音诅咒"。

## 0. 量化背景

| 指标 | 值 |
|---|---|
| 项目/语言 | 10 项目 / 10 语言（补齐后 15/15 全覆盖） |
| 子智能体 | 42+（extractor 21 / verifier 簇 12 / R4 9） |
| R1 原始候选 | ~42,000 条（ktor 11,058 / nest 14,677 / actix 7,468 / akka 4,100 / django 3,705…） |
| 过滤+聚类后验证 | ~180 簇/候选 |
| 真实 REACHABLE 家族 | ~33 个（Tier 1 CVE 候选 10 个） |
| L0 Sink Discovery Rate | 全语言趋 0（perl 除外），全部真实发现来自 R1.5 |
| 噪音率 | ≥95%（10/10 语言复现） |

## 1. P0 缺陷

### 1.1 L0 规则库对 10 语言全线失效（噪音诅咒规模化确认）

**现象**：Rust/Scala/Kotlin 的 L0 规则是 Java 方法名 regex 的移植（`_store_mask32\(`、`AtomicFileWriter\(`、`ANTLRFileStream\(`），命中 Rust/Scala 代码中恰好同名的普通方法；`new\s*\(`（CWE-918 Ruby/TS）命中每个构造调用；`post|put|delete` 子串命中 `Out**put**`。单项目 3k-15k 候选，验证后真实 sink 命中率 <0.5%。

**根因**：规则以"方法名字符串"为语义，跨语言移植后语义归零。10/10 语言复现，README 的"89% 噪音"实为下限。

**改进建议（v2.2 最高优先级）**：
1. **废除跨语言方法名移植**：非 CodeQL 结构化模型的语言，规则必须是"本语言真实 sink 签名"（人工维护的生态列表，如 swift-server/rust-nio/kotlin-ktor），否则宁可空规则+L1 兜底（空规则诚实，噪音规则有毒）
2. R1 增加**噪音自检**：扫描后按 sink_type 抽样 10 条人工判误报率，>80% 的规则自动降权/禁用并提示
3. 候选量预算（SWIFT_GO lesson 已有提议）：按项目规模封顶，超出即强制聚类

### 1.2 测试路径过滤缺语言约定（5 种新命名形态漏网）

**现象**：skill 过滤列表（test/tests/mock/build…）漏掉：`spec/`（Ruby，sinatra 348/439 候选在 spec）、`tst/`（PowerShell，Pester 1147/1853）、`*_tests.rs`（Rust，actix）、`Newtonsoft.Json.Tests`（.Tests 点前缀形态）、`*.spec.ts`（TS，需手工排除）。

**改进建议**：过滤规则改为**按语言映射表**（lang → 测试路径形态），如 ruby→`/spec/`、powershell→`tst/`+`*.Tests.*`、rust→`*_tests.rs`+`/benches/`、ts→`*.spec.*`+`*.test.*`。表随新语言审计增量补全（本战役已产出 5 条）。

### 1.3 R4 六假说配置不具可扩展性（REQ-16 修订需求）

**现象**：REQ-16 要求 H1-H6 并发深钻。10 项目战役若按"每假说一 agent"需 60 个 agent，实际采用 3×2（小项目）与 1×6（大项目）压缩配置。压缩后单 agent 覆盖 6 假说的深钻质量低于专精配置（H 级 finding 的调用链证据更薄）。

**改进建议**：REQ-16 增加**规模自适应档位**：小项目（<500 文件）3 agent×2 假说；大项目 6 agent 专精；战役模式（≥5 项目）允许 1×6 快档但必须在报告标注 `r4_consolidated: true`。R4 assert 保持 H1-H6 全 verdict 检查不变。

### 1.4 子智能体长跑无中间心跳（ohmyzsh git 簇"失联"实为 60 分钟马拉松）

**现象**：1 个簇 verifier（git.zsh/vcs_info）启动后 1 小时无任何产出/通知，主 agent 判为失联并手工核验补写 verdict。随后该 agent 才完成（耗时 3,595s——它做了 zsh 5.8 源码构建 + CVE-2021-45444 的 PWN 标记法经验验证矩阵，产出质量极高），覆盖了手工补写版本。两版判定一致（UNREACHABLE），但过程浪费且存在**双写竞态**：若两版判定不一致，后到者静默覆盖先到者，无冲突检测。

**改进建议**：① 任务书强制"第一步先写占位文件 `_rX_<id>.json.pending`"（心跳物证，含 started_at）；② 主 agent 定期检查 pending 文件判定"在跑"vs"丢失"（本役误判为丢失）；③ 落盘规则加冲突检测：目标文件已存在且非本人 pending 时，追加 `.agent-<id>` 后缀而非覆盖；④ 对长跑 agent 设中途产出节（每 15 分钟写 progress 片段）。

## 2. P1 缺陷

### 2.1 簇验证（cluster verdict）是事实标准但无规范支撑

**现象**：42k 候选下，逐候选验证不可能。本战役自创 `verdict_map: "all"` + `exceptions: []` 的簇验证协议，效果良好，但 skill 无此概念：batch_verify 的 collect 要求每候选独立 verdict；`--stage assert` 检查每候选字段。

**改进建议**：v2.2 正式引入**候选聚类**：入队时支持 `cluster_id`；collect 支持簇级 verdict 广播（`--cluster <id> --verdict ...` 自动展开到成员候选并标记 `clustered_verified`）；assert 接受簇成员共享证据。聚类标准：同文件+同 sink 族+同判定预期。

### 2.2 跨项目 CWE 家族同源（模式复用的机会）

**现象**：同一缺陷形态跨项目复现：**"未完成 WS 帧无界缓冲"**在 actix（frame.rs）、akka（Message.toStrict）、ktor（SimpleFrameCollector）三家同时存在；**"先分配后校验"**（akka h2 头、ktor ws 帧、Newtonsoft BSON）跨四家；**"修复-再暴露"**（AWStats configdir、actix CVE-2026-72814 空路径、django CVE-2026-33033 残留）三家。

**改进建议**：新增**战役模式家族复用**：同一战役中，前一个项目确认的缺陷形态（家族签名）自动注入后续项目 extractor 的任务书（"检查本项目是否存在 X 形态"）。本战役手动做了这件事（actix 的 ws 发现指导了 akka/ktor 的 ws 检查），证明有效——django/akka/ktor 的新发现中 4 个来自此复用。

### 2.3 R0.5 多 tag 交叉是最高价值阶段，应设为可选模式

**现象**：AWStats 三 tag 交叉（7.6/7.7/7.8）产出本战役最高价值发现（修复残留绕过 + 7.8 tag 未含修复的发行版缺口）。actix 修复核验、Newtonsoft CVE 核验同样高价值。但 r05_diff_archaeology.py 无 tag 交叉模式，全靠 ad-hoc。

**改进建议**：R0.5 增加 `--cross-tags <tag1>,<tag2>...` 模式：对每个 tag 输出"目标修复 commit 是否在该 tag"的矩阵（git merge-base 判定），自动识别"发行版未含修复"与"修复-再暴露"。

## 3. 表现良好的部分（保持）

1. **R1.5 三域 extractor 在 10 语言全线扛起真实发现**（33 个家族全部来自 L1/R4）——v2 架构的核心正确性再次验证
2. **R0.5 修复核验模式**：actix 5 项/CVE 双锚点、Newtonsoft 2 项 CVE、AWStats 3 版本——"修复完整性核验"是当前 skill 性价比最高的阶段
3. **锚点自检机制顺利扩展**：9 新语言锚点一次通过（模式取自规则 regex 保证命中）；PowerShell 无 grammar 优雅跳过
4. **REQ-19 跨边界终结**在 multipart/plugin/重定向边界上判定准确
5. **量化指标诚实性**：SDR 全线 0 如实报告，支撑了"规则库无效"的结论（若美化指标将掩盖 1.1 缺陷）

## 4. 改进优先级总表

| # | 缺陷 | 等级 | 动作 | 先例 |
|---|---|---|---|---|
| 1.1 | L0 规则跨语言失效/噪音 95%+ | P0 | 废方法名移植+噪音自检+候选量预算 | 跨语言 #1 |
| 1.2 | 测试路径过滤缺语言约定 | P0 | 语言映射表（本役已产出 5 条形态） | C lesson |
| 1.3 | R4 六假说不具扩展性 | P0 | 规模自适应档位 + r4_consolidated 标注 | 新 |
| 1.4 | 子智能体长跑无心跳（1h 马拉松误判失联） | P0 | pending 心跳 + 落盘冲突检测 + 中途产出节 | 新 |
| 2.1 | 簇验证无规范 | P1 | cluster_id + 簇级 collect/assert | 新 |
| 2.2 | 跨项目家族同源 | P1 | 战役模式家族签名复用 | 新 |
| 2.3 | R0.5 无 tag 交叉模式 | P1 | --cross-tags 矩阵 | 新 |
