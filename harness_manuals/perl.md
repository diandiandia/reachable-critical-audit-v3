# Perl 实证工具链手册 (v3.1)

> 来源：W6_MORE_LANGS_FINDINGS.md（AWStats 批次，§1-§6）与 SKILL_LESSONS_10LANG_CAMPAIGN.md（§1.1/§1.2/§2.3）。实证工件：`/root/AWStats/.audit_results/empirical/rawlog_xss/EMPIRICAL_REPORT.md`。

## 1. 工具链探测
- 审计目标为纯 Perl 项目（AWStats 7.7）时**无构建步骤**，直接 `perl` 解释器运行即实证；AWStats 实证报告记录的探测事实为"工具链: perl (系统)"——须 `perl -v` 记录精确版本（W6 §2 批次事实，§16.1 版本记录义务通用于全语言）。
- 实证方式 = 运行真实 `awstats.pl` 脚本（refuter 实测默认配置下 die 行为，W6 §6）或以 config + 注入日志喂真实插件模块（rawlog.pm:99-107 / awstats.pl:8029-8040 逻辑复刻，EMPIRICAL_REPORT）。
- R0.5 考古用本地 git：AWStats 三 tag 交叉（7.6/7.7/7.8）产出战役最高价值发现（修复残留绕过 + 7.8 tag 未含修复的发行版缺口）——`git` 是 Perl 项目审计的一级探测工具（SKILL_LESSONS §2.3）。
- 测试路径约定：Perl 生态测试目录形态为 `t/`（与 `test/` 同族，默认过滤已覆盖；SKILL_LESSONS §1.2 语言映射表机制照用）。

## 2. 版本记录义务
- 记录三版本：审计 tag（AWStats 7.7）、perl 解释器精确版本、web 日志样本来源形态——rawlog XSS 的利用前提之一是"Web 服务器 %r 原样记录请求行"，日志形态差异直接影响存储型 XSS 成立性（EMPIRICAL_REPORT 前置条件 2）。
- **tag 级版本义务**：7.6/7.7/7.8 三 tag 行为必须分别记录（SKILL_LESSONS §2.3——7.8 未含修复即为版本记录缺失的教训）；假设生成前先读该仓库旧审计终稿（§22.2 通用规则）。

## 3. 常见陷阱清单
- **Perl 源码含字面 HTML 实体**：`s/&/&amp;/g;` 这类 HTML 转义代码本身就是源码内容，无脑 `html.unescape` 会误解码并把正确证据误拒（W6 §1.1，AWStats 2 处）——snippet 处理必须双态匹配。
- **短行子串恒真误报**：`(`、`#`、`)` 反向包含匹配几乎恒真，候选过滤须 `len(fl) >= 10`（W6 §1.2）。
- **HEADER-INJ 家族密集属正常**：AWStats R2 3576 hits → 89 假设，其中 HEADER-INJ 3041 命中——HTML 输出编码家族密集不是异常信号（W6 §2）。
- **R4 证据 JSON 反斜杠逃逸**：`\d`/`\w`/`\s` 片段写出未转义反斜杠；修复必须单遍扫描（迭代修复振荡不收敛）；`\u` 仅当后接 4 hex 才合法（`\user` Windows 路径陷阱）（W6 §3.1-3.3）。
- **条件式 REACHABLE 的部署前提**：AWStats 4 候选 3 个带前提——AWSTATS_ENABLE_CONFIG_DIR 已设、LoadPlugin=rawlog 启用、key 机制可移除/白名单；verifier 必须在 blocking_point 显式记录前提，前提被"默认当开"则降级 NEEDS_REVIEW（W6 §6）。
- **配置键 = 攻击面**：AWStats 的 config 键（LoadPlugin、key、ENABLE_CONFIG_DIR）本身是 sink 形态——config 驱动的 Perl CGI 程序把攻击面集中在键解析上，surface 测绘须覆盖 config 读取路径（W6 §6 前置条件清单）。
- **零假设 surface 不等于未覆盖**：LoadPlugin eval ×2、history 文件读写 ×2 曾 R2 零命中，实质已被 R4 审查——按 coverage_note 内容映射回填，勿盲目重审（W6 §4）。
- **refutation resume 契约**（AWStats 批次暴露）：resumeFromRunId 必须携带与首次运行一致的 args（脚本内 `args ?? {}` 防御，或按 /tmp/refute_args_aw.json 模式存档）；refuter 半程输出不可作为裁决依据，以 schema-validated 最终返回为准（W6 §5）。
- **harness 保真自检**：data 域测绘 agent 主动指出 v2.2 diricons harness 未模拟 quote-strip——上游 harness 未模拟的行为要在实证前核对真实代码再定测量方案（W6 §2）。

## 4. 阳性模式（战役验证过的做法）
- **L0 签名库唯一生效语言**：15 语言中仅 Perl 的 L0 Sink Discovery Rate 非零（SKILL_LESSONS §0）——Perl 的 sink 形态（open/print/eval/config 键）与签名词库匹配良好，Perl 项目应保留 L0 通道而其余语言改走 LLM 假设路径。
- **最小真实运行环境**：define 常量 + 按 include 图补全局变量的模式（PHP §17.8 同构）对 Perl 同样成立——AWStats 实证直接跑 rawlog.pm 插件 + 投毒日志行（`GET /<script>...</script> HTTP/1.1`）验证 `<script>` 完整存活于 `<pre>` 块（EMPIRICAL_REPORT）。
- **默认配置实证**：refuter 实测默认配置 die 行为后仍投"不证伪"——"默认配置下的实际行为"是条件式 REACHABLE 裁决的必需证据（W6 §6）。
- **tag 交叉考古**：`git` 三 tag 矩阵找"修复残留绕过 / 发行版未含修复"（SKILL_LESSONS §2.3），是 Perl 项目 R0.5 的最高价值动作。

## 5. 网络依赖
- lessons 未记录 Perl 实证的网络阻断；AWStats 本地实证（perl + config + 投毒日志文件）零网络依赖。
- 真实部署面（攻击者向 Web 服务器发请求投毒日志）属于 E2E 场景前置条件而非 harness 网络依赖；不可达时按 §21.4 降源事实级并记录 blocker。
- R0.5 依赖本地 git 仓库，无需远端。

## 6. 实证范围建议
- **机制级 + E2E 皆可行且成本低**（纯解释型无构建）：存储型 XSS 家族（rawlog html 模式）用机制级（真实插件函数 + 投毒日志行）即构成实证（EMPIRICAL_REPORT 完成形态）；config-gated 家族（AWSTATS_ENABLE_CONFIG_DIR/LoadPlugin）补 E2E 默认配置运行确认 die/拒绝行为（W6 §6）。
- **范围纪律**：机制级实证只能支撑 edge_proven，不得直接升 empirically_confirmed（§17.7 通用规则）；empirically_confirmed 需真实完整路径。
- 网络阻断时源事实级可接受（§21.4 通用规则），但 Perl 无构建墙，阻断场景罕见。
