# PHP 实证工具链手册 (v3.1)

> 事实来源：W6_MORE_LANGS_FINDINGS.md §17（PHP 首审批次）与
> SKILL_LESSONS_PHP.md（phpMyAdmin CVE-2018-12613 锚点审计 + WP 规则噪声分析）。
> 战役战绩：10 候选 2 REACHABLE 2 裁决降级 1 机制实证，R3.5 拦截 50%。

## 1. 工具链探测

- `php` CLI 现场可用：证伪者跑真实 WP_Hook 复测（§17.5）、realpath+file_exists 路径测试（§17.9）。
- PHP harness 依赖链构建模式（§17.8）：WP_Hook/plugin.php/formatting.php 需要 l10n + pomo + `$shortcode_tags` 全局；`define('ABSPATH', ...)` 后 require_once 路径一致性解决 WP_Hook 双声明。
- 最小真实运行环境 = define 常量 + 按 include 图补全局变量（§17.8）——后续 PHP 审计直接套用。
- PHP source 模型（`$_GET/$_POST/$_REQUEST/$_COOKIE/$_SERVER`）配合跨函数回溯对 PHP 有效（SKILL_LESSONS_PHP §1.3）。

## 2. 版本记录义务

- 记录审计目标精确版本（§17；历史锚点审计 ground truth=CVE-2018-12613，SKILL_LESSONS_PHP §1.1）。
- 矩阵型前提必须随版本记录：theme-compat 的"Editor 角色 + 经典主题"是核心一线支持配置（§17.6）。
- 分层防御是动态注册的（kses_init / capability 条件注册）——防御链结论必须落到当前版本的实际注册点（§17.5）。

## 3. 常见陷阱清单

- LLM 假设生成 agent 失控：CMS 类项目（>200k 行、48 面）上无限扩张验证范围 2.5 小时无产出；主代理接手 20 分钟产出 10 条真实行号假设（§17.1）。
- workflow 模板字面量顶层求值：把 `${c.file}` 塞进模块顶层 const STEPS → 模块加载时求值 ReferenceError，两波次 8ms 内全崩（§17.2）。
- 只查单一 sanitize 调用点漏掉动态注册防御：title_save_pre "仅 trim" 漏了 kses_init 对非 unfiltered_html 用户的 wp_filter_kses 动态注册（kses.php:2468）（§17.5）。
- 机制级实证标 empirically_confirmed 过度升级：harness 只跑真实过滤链+sink 行（未跑 wp_insert_post/comments_template/主题加载）被证伪者纠正降级 edge_proven + scope_note（§17.7）。
- mature-framework 签名零转化第三例：910 hits 0 keep（$wpdb->prepare 全参数化、操作符白名单、intval 强制、wp_safe_remote_get 全路径验证）（§17.3）。
- 承重前提未回头验证：CAND-003 严格相等门控漏看、CAND-008 host 钳制闭环——两个都是"沿假设惯性向前推"（§17.10）。
- 过滤器假设只查单调用点：必须搜索该 filter 名的全部 add_filter 注册点（含 init 回调内动态注册）（§17.4/17.5）。
- 签名规则框架绑定噪声：CWE-918 regex 把全部 PHP 文件系统函数当 SSRF（目标项目命中 1246 个）；semgrep-registry 的 php.lang.security 规则绑定框架全家桶，对 PHP 数组访问链/格式化函数误报 14452 个（SKILL_LESSONS_PHP §4）。
- 大代码库第三方库排除：WP 的 tinymce/codemirror/jquery/plupload/PHPMailer/SimplePie 等目录（SKILL_LESSONS_PHP §5）。

## 4. 阳性模式（战役验证过的做法）

- 最小真实运行环境 harness：define ABSPATH + require_once 按 include 图补全局，直接跑真实过滤链 + sink 行（§17.8）。
- 完整写链复测：证伪者用真实 WP_Hook 复测 title 写链 3 载荷全杀（§17.5）；id 编码形态实测 + realpath+file_exists 验证 .html 可达；host 真值表复算（§17.9）。
- 矩阵类裁决按"最常见成立格"裁决：Editor+经典主题矩阵保留 REACHABLE 且端到端矩阵记录（§17.6，与 Host 白名单先例 §14.7 合并）。
- 假设生成者必查"该字段的全部过滤链注册"（default-filters + init 期动态注册，§17.4）。
- verifier 步骤 0：先验证假设中的承重前提（grep 一句话能证实/证伪的），前提断裂立即终止回溯（§17.10）。
- 大代码库 R2 标准操作定型：主代理直接生成假设 + 签名 hits 供证（§17.1→§18.1 跨语言复用）。

## 5. 网络依赖

- 本战役 harness 全部本地运行（源码 checkout + php CLI），无网络依赖记录。
- PHP 规则/锚点资产为本地（SKILL_LESSONS_PHP：CWE-98 LFI 规则与 CVE-2018-12613 锚点已入库）。

## 6. 实证范围建议

- **机制级是 PHP 标准层级**：最小真实环境跑过滤链+sink 行，成本低、可复用（§17.8）；端到端（完整 wp_insert_post/comments_template/主题加载）代价高，仅关键候选做。
- 实证分级纪律（§17.7）：机制级只能支撑 edge_proven 边证据，升 empirically_confirmed 必须有完整运行时的端到端证据。
- 矩阵类裁决按"最常见成立格"裁决并显式记录矩阵（theme-compat Editor+经典主题，§17.6；与 Host 白名单先例 §14.7 合并）。
- 分层动态防御框架的 UNREACHABLE 判定必须过一遍动态注册搜索（§17.5）。
