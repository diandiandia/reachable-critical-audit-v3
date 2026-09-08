# Reachable Critical Audit Skill — PHP 审计暴露的缺陷与改进建议

> **文档性质**：基于两次 PHP 实测审计对 `reachable-critical-audit` skill 的回顾性缺陷分析。
> 驱动 skill 规则库改进，非项目审计报告。
>
> **审计 #1（2026-08-13）**：phpMyAdmin 4.8.5 — ground truth = CVE-2018-12613（`index.php` LFI→RCE）。
> 结论：PHP 规则缺失（无 CWE-22/98）→ 已修复（CWE-98 LFI 规则与锚点已入库）。
>
> **审计 #2（2026-08-15）**：WordPress 7.0.4 core（1453 PHP + 206 JS 文件，54786 原始候选）。
> 结论：规则缺失问题已解决，但暴露**宽 regex 误报爆炸、队列规模失控、编排工具链缺陷**
> 三类新问题（见 §4-§6）。7 个 REACHABLE 全部为主 Agent 代码级复核确认。

---

## 0. 摘要

PHP 是 skill 规则库的**低覆盖语言**：7 条规则（CWE-502/78/79/89/918/94/95），全部来自
semgrep-registry 移植。实测暴露 3 类缺陷：

1. **无 CWE-22/98（路径遍历/LFI）PHP 规则，且 PHP 全部规则无 `include`/`require` sink**
   → 最高频的 PHP 漏洞类（LFI→RCE，CVE-2018-12613 即此类）**系统性漏检**
2. CWE-22 候选来自跨语言 fallback，命中 JS `window.open`/doc 配置行，**纯噪音**
3. R3 可达性回溯对 PHP 有效（`$_GET/$_POST/$_SERVER` source 可正确判定 UNREACHABLE），
   但候选质量被规则缺失拖累

---

## 1. 关键缺陷

### 1.1 CVE-2018-12613 LFI sink 完全漏检（最高优先级）

**现象**：phpMyAdmin 4.8.5 `index.php:62` 存在标准 LFI sink：
```php
if (! empty($_REQUEST['target'])
    && is_string($_REQUEST['target'])
    && ! preg_match('/^index/', $_REQUEST['target'])
    && ! in_array($_REQUEST['target'], $target_blacklist)
    && Core::checkPageValidity($_REQUEST['target'], [], true)   // 4.8.5 可用 %253f 双编码绕过
) {
    include $_REQUEST['target'];                                 // ← CVE-2018-12613 sink
}
```
扫描器对全库 739 个 PHP 文件产出 4981 候选，但**对该 sink 零命中**。

**根因**：PHP 规则集 sink 列表只覆盖 `exec/system/eval/assert/curl_exec/mysqli_query/unserialize`
等，**无 `include/include_once/require/require_once`**。CodeQL/semgrep 的 PHP LFI 规则
（`php.lang.security.tainted-path-concat` 等）未被收录。PHP 的 CWE-22 攻击面与 C 不同：
不是 `open()`，而是 `include`/`file_get_contents`/`fopen`。

### 1.2 PHP 无 CWE-22 规则，跨语言 fallback 产出纯噪音

**现象**：扫描产生 5 条 `CWE-22` 候选，全部为 JS `window.open`（`js/functions.js:4423`）、
`indexedDB.open`（designer）与 doc/conf.py 注释行——与 PHP 路径操作无关。

**根因**：PHP 规则表无 CWE-22；候选来自规则库对全语言的通用 CWE-22 兜底正则。PHP 应建立
**语言专属 CWE-22/98 规则**，sink 限定 `include/require/file_get_contents/fopen/readfile/
copy/unlink/rename/move_uploaded_file`。

### 1.3 R3 可达性回溯对 PHP 有效（正面结论）

**现象**：`CAND-975`（`libraries/classes/SysInfoSunOS.php:30` `shell_exec('kstat -p d ' . $key)`）
被 L0 命中为 CWE-78。R3 回溯发现 `_kstat()` 全部 9 个调用点的 `$key` 均为**硬编码字符串**
（`unix:0:system_misc:avenrun_1min` 等），无任何用户输入路径 → **UNREACHABLE**。

**结论**：PHP source 模型（`$_GET/$_POST/$_REQUEST/$_COOKIE/$_SERVER`）配合跨函数回溯可
正确过滤常量拼接的伪候选，这是 skill 在 PHP 上可复用的能力。

---

## 2. 建议改进

### P0：新增 PHP CWE-22/98（LFI）规则

```json
{
  "cwe_id": "CWE-98",
  "category": "LocalFileInclusion",
  "sinks": {
    "ast_patterns": [
      "(include_expression) @sink",
      "(require_expression) @sink",
      "(function_call_expression function: (name) @fn (#match? @fn \"^(include|include_once|require|require_once|file_get_contents|fopen|readfile)$\"))"
    ],
    "regex": ["(^|[^a-zA-Z_])(include|include_once|require|require_once)\\s*\\(?\\s*\\$"]
  },
  "sources": {
    "regex": ["\\$_?(GET|POST|REQUEST|COOKIE|SERVER|FILES)\\s*\\["]
  }
}
```

### P1：PHP source 模型结构化

- 内置 `$_GET/$_POST/$_REQUEST/$_COOKIE/$_SERVER['HTTP_*']/$_FILES/$argv` 为 taint source，
  供 R3 回溯统一使用（当前依赖正则零散命中）。

### P1：PHP sink 去噪

- CWE-78/94 的 `ast_patterns` 用 `function_call_expression` 已正确；regex 兜底需排除
  `shell_exec('硬编码')` 常量场景（与 1.3 结论一致）。

---

## 3. 建议后续验证目标

| 项目 | 版本 | Ground truth CVE | 规则面 |
|---|---|---|---|
| phpMyAdmin | 4.8.5 | CVE-2018-12613 (LFI→RCE) | CWE-98/22, 94 |
| Drupal 8.3.x | <8.3.9 | CVE-2018-7600 Drupalgeddon2 (unserialize RCE) | CWE-502 |
| PrestaShop 1.7.7.x | <1.7.7.7 | CVE-2021-4048 (SQLi) | CWE-89 |
| SuiteCRM 7.11.x | <7.11.20 | CVE-2020-28020 (include RCE) | CWE-94/98 |

---

# 第二次审计：WordPress 7.0.4（2026-08-15）暴露的缺陷

> 环境：skill venv（补装 tree-sitter-perl/bash 后 self-check PASS，锚点召回 100%）。
> 规模：ast_scanner 全量扫描产出 **54786** L0 候选（php 18460 / js 36326）。
> 关键数字：F1 第三方丢弃 25126 → F2 机械非-sink 27141 → F3 硬编码参数 374 → 2145 入队
> （1213 为扫描器 regex-only 降级）→ 932 经 93 批子智能体验证 → 7 REACHABLE。

## 4. 规则库宽 regex 误报爆炸 + 真 sink 漏检（最高优先级）

### 4.1 CWE-89 规则是 Laravel QueryBuilder 专属，对非 Laravel 框架全误报

**现象**：CWE-89 的 regex 是 90+ 个 Laravel QueryBuilder 方法名（`where(`/`select(`/`delete(`/
`insert(`/`sprintf(`/`count(`/`max(`/`min(`/`get(`…）。WordPress 不用 Laravel，**14452 个命中
几乎全部是 `array->get()`/`sprintf()` 之类的误报**；而 WordPress 真正的 DB sink
`$wpdb->query()/get_results()/get_row()/get_col()/get_var()` **完全不在规则内**——
AST pattern 只匹配裸函数调用 `^(mysqli_query|query|mysql_query|pg_query)$`，
成员调用 `$wpdb->query(` 是 member_call_expression，AST 不匹配、regex 也覆盖不到。
真 sink 最后靠 R1.5 L1 wrapper（framework-sink-extractor）补全。

**根因**：semgrep-registry 的 `php.lang.security` 规则是**框架绑定**的（Laravel/Doctrine），
清洗入库时未标注适用框架，也未区分裸函数调用与成员方法调用两个层面。

**修复建议（P0）**：
1. `security_profiles.json` 的每条规则增加 `framework_scope` 字段（如
   `"framework_scope": "laravel-querybuilder"`），扫描时对不匹配框架的项目降低该规则
   regex 命中的优先级（正则命中降 NEEDS_REVIEW，AST 命中才入 PENDING）。
2. PHP AST pattern 增加成员调用形态：
   `(member_call_expression object: (_) @obj name: (name) @fn (#match? @fn "^(query|get_results|get_row|get_col|get_var|prepare)$"))`
3. 真 DB sink 的 regex 兜底应含 `->query(` / `->get_results(` 形式。

### 4.2 CWE-918 的 regex 把"全部 PHP 文件系统函数"当 SSRF

**现象**：CWE-918 regex 含 100+ 个文件函数（`file_exists`/`is_dir`/`stat`/`chmod`/
`xattr_*`/`touch`/`unlink`/`md5_file`/`getimagesize`…）。WordPress 命中 1246 个，
绝大多数是本地文件元数据检查，与 SSRF 无关；真正的网络 sink
（`wp_remote_*`/`curl_exec`/`fsockopen`）混在其中难以分离。

**修复建议**：按 sink 语义拆分子类——本地文件系统函数（CWE-22/59 面）与网络请求函数
（CWE-918 面）分属不同规则；CWE-918 regex 只保留网络 URL 维度 sink。

### 4.3 CWE-94 的 regex 把"全部回调注册函数"当代码执行

**现象**：CWE-94 regex 含 `register_shutdown_function`/`set_error_handler`/
`array_map`/`usort`/`array_filter`/`ob_start` 等 60+ 回调注册函数，1263 个命中中
绝大多数回调名是字符串字面量（无攻击者可控的代码维度）。

**教训**：回调注册类 sink 的"攻击者可控维度"是**回调名**而非被处理数据——
硬编码回调名 + 外部数据（`array_map('esc_html', $user_input)`）不是漏洞。
这条"维度判定"可直接机械化（F3：第一参为字面量 → UNREACHABLE），
本次已用脚本验证可行，应内建为规则级的快速通道。

## 5. 队列规模失控：skill 缺"确定性降噪层"（mechanical triage）

**现象**：54786 候选 × batch_verify 固定每批 4 个 = 13700 批，物理不可执行。
skill 的 R1→R3 之间没有任何候选规模控制机制，主 Agent 被迫自建三层确定性过滤：

| 层 | 规则（全部确定性、可审计） | 本次效果 |
|---|---|---|
| F1 | vendored 第三方路径 + `.min.*` 构建产物 → 移出队列 | 25126 |
| F2 | 调用名 ∉ 该 CWE 的 sink 集合（如 `sprintf` ∉ DB API）→ 机械 UNREACHABLE | 27141 |
| F3 | 硬编码参数（回调名字面量 / include 路径无 `$` 变量）→ 机械 UNREACHABLE | 374 |

**F1 的教训**：`_IGNORE_PATH_PARTS` 关键词法（vendor/third_party/libs）对"内嵌第三方"失效：
WordPress 的第三方库位于 `wp-includes/js/tinymce|codemirror|jquery|plupload|mediaelement`、
`wp-includes/Requests|PHPMailer|SimplePie|ID3|Text|sodium_compat|random_compat`、
`wp-includes/atomlib.php`、`wp-admin/includes/class-pclzip.php`、`wp-content/themes/twentytwenty*`。
需增加**知名第三方清单**（按目录名/文件名精确匹配）+ `.min.` 构建产物过滤
（batch_verify 的 R15 有 `.min.` 跳过逻辑而 ast_scanner 没有——工具间不一致）。

**修复建议（P0）**：
1. ast_scanner 增加 `--mechanical-filter` 阶段（或独立 `triage.py`），F1/F2/F3 判定
   证据写回候选的 `evidence`/`blocking_point` 字段（保持"每个 verdict 有依据"的可问责性）。
2. `_IGNORE_PATH_PARTS` 升级为 vendored 清单：目录名精确匹配 + 文件名精确匹配 + 前缀匹配。
3. 宽 regex 规则（framework_scope 不匹配时）的命中直接入 mechanical filter 而非队列。

## 6. 编排工具链缺陷（batch_verify.py / ast_scanner.py）

### 6.1 BATCH_SIZE=4 逐候选出队，无按文件聚合模式
大项目每个子智能体只验证 1 个候选点，效率极低（13700 批）。本次自建
`build_r3_batches.py`（按文件聚合，每任务 8-20 候选）+ `collect_r3_batch.py`（批量落盘），
93 批 + 6 个 L1 批即覆盖 1002 个候选。**建议**：batch_verify 增加
`--stage next --group-by-file` 模式，或内置"文件聚合批"生成器。

### 6.2 子智能体输出 JSON 频繁损坏，collect 无容错
实测约 1/4 的批次 result 文件含非法 JSON 转义（evidence 里的 `\x`、`\a` 等），
`json.load` 直接抛 `Invalid \escape`。batch_verify 的 CLI `--cand-XXX='{...}'` 传参方式
还有 shell 转义问题。**建议**：collect 路径增加容错加载（无效反斜杠转义转 `\\` 字面量
后重试），子智能体任务书强制要求"evidence 中不要出现反斜杠字符"。

### 6.3 子智能体 API 中断需恢复机制
本次 6 个子智能体因 "Connection lost mid-response" 中断（多在写完分析、落盘前一刻）。
SendMessage 恢复后均能完成。**建议**：skill 附录增加"子智能体中断恢复"指引——
用 SendMessage 重发落盘指令，其上下文仍在；若彻底失败则保持 PENDING 由
`--stage next` 自动重试（现有机制可用，但 batch_verify 每批 4 个的粒度使重试代价高）。

### 6.4 assert 与 collect 的校验规则不一致
`--stage collect` 不强制 `blocking_point`，但 `--stage assert` 要求 UNREACHABLE 必须有
`blocking_point` → 本次 74 条 ASSERT_FAILED_INVALID_VERIFIED，需手工从 call_chain 回填。
**建议**：collect 校验时就要求 UNREACHABLE 带 blocking_point（缺省从 call_chain[1] 回填），
或 assert 对缺失项自动回填并计数告警。

### 6.5 L0 候选关键字段缺失
ast_scanner 入队的候选 `source_pattern` 与 `language` 字段全为 `'?'`：
- `source_pattern='?'` 使 r15-collect 的去重键（file+line+wrapper）无法与 L0 交叉去重；
- `language='?'` 使队列无法按语言统计、报告无法按语言拆分。
**建议**：ast_scanner 入队时填充实际 pattern 与按扩展名推断的语言。

### 6.6 L1 候选并入后无自动批次
`--stage r15-collect` 并入的 L1 候选不会自动进入文件聚合批次，本次手工生成
`batch_l1_cwe89/cwe79/other` 6 批。**建议**：r15-collect 后自动触发批次重建，或
`--stage next --group-by-file` 天然覆盖（见 6.1）。

### 6.7 R0 依赖清单缺 perl/bash grammar
self-check 因 `grammar_missing: [perl, shell]` FAIL；SKILL.md 的 pip 安装列表没有
`tree-sitter-perl`/`tree-sitter-bash`。**修复**：依赖 bootstrap 清单补上这两个包
（本次补装后 PASS，锚点召回 100%）。

### 6.8 R0.5 无 git 历史时工具输出误导
`r05_diff_archaeology.py` 对无 `.git` 目录输出"无匹配安全关键词的 commit"，
而非明确的 no-git 状态；主 Agent 需手工写 skipped_reason。
**建议**：工具探测 `.git` 缺失时输出 `{"status": "NO_GIT", ...}`。

### 6.9 指标缺陷：avg_call_chain_depth 被无深度候选拉低
1247 个 NEEDS_REVIEW（depth=0）把平均链深拉到 1.72，与真实验证子集 3.81 混淆。
**建议**：指标只统计"有验证深度的候选"，NEEDS_REVIEW 单独计数。

## 7. 同点跨 CWE 重复判定（维度拆分）

**现象**：`wp-includes/template.php:795 extract($wp_query->query_vars, EXTR_SKIP)`
同一代码点被两次判定且结论冲突：
- CAND-17242（CWE-502 变量**覆盖**维度）→ UNREACHABLE（EXTR_SKIP 阻断覆盖）
- CAND-54822（CWE-621 变量**值注入**维度）→ REACHABLE_ACROSS_BOUNDARY（值无净化跨主题边界）

**教训**：skill 的阻断检测原则"阻断必须覆盖所有攻击者可控制维度"是对的，但同一 sink
的多维度攻击面往往由**不同 CWE 规则**分别命中，两次独立判定会得出看似矛盾的结论。
**建议**：R3 结论落盘时按 (file, line) 做跨 CWE 关联标注（`related_candidates`），
主 Agent 复核时按维度拆分裁决并在 evidence 中互相引用（本次已手工执行）。

## 8. WordPress 特定检测模式（对 PHP 规则库/verifier 提示词的补充）

以下模式全部产出了 REACHABLE finding，建议固化进规则或 verifier 提示词：

1. **Adjacent-escape-miss（相邻转义遗漏）**——同文件/同函数对同一变量有的消费点
   转义、有的不转义。本次 3 个 XSS 全是此模式：
   - `wp-admin/user-edit.php:782` 裸输出 `$profile_user->display_name`，同文件 746 行有 `esc_html`；
   - `wp-includes/post-template.php` 附件链接文本回退分支有 `esc_html(pathinfo(...))`，
     post_title 分支没有；
   - `wp-includes/theme-compat/comments.php` 两个 printf 分支均无转义。
   verifier 提示词应显式要求"对比同变量其他消费点的转义"。
2. **urldecode 绕过路由正则**——REST 路由正则先匹配（`[\/\w%-]+` 允许 `%`），
   `sanitize_callback` 才 `urldecode` → `%2e`/`%2f` 还原为 `../` 穿越（CAND-23585）。
   PHP 规则应关注"正则先匹配、urldecode 后拼路径"的顺序缺陷。
3. **wp_mail header CRLF**——`wp_kses($data, 'strip')` 只剥 HTML 标签**保留换行**，
   存储字段（comment_author）进 `wp_mail` header → `explode("\n")` 拆头 → Bcc 注入（R4 H4）。
   CWE-93 邮件注入规则应覆盖 wp_mail/mail 的 header 拼接点 + 未 strip `\r\n` 的存储字段。
4. **XML-RPC 无 HTML 净化写入**——`wp_editProfile` 的 display_name 仅 `wp_slash` 落库
   （wp_insert_user 不 kses display_name），多个 admin 消费点未转义 → 存储 XSS 家族
   （CAND-988/1091 同根双 sink）。
5. **theme-compat 回退模板**——主题缺 comments.php 时 core 回退模板消费点
   （`wp-includes/theme-compat/`）也是攻击面，路径过滤不能排除。
6. **PHP 阻断清单（verifier 提示词已验证有效）**：
   esc_html/esc_attr/esc_url/esc_js/esc_textarea（输出）、wp_kses/sanitize_*（输入）、
   absint/(int)（类型）、`$wpdb->prepare`/esc_like/esc_sql（SQL）、
   wp_verify_nonce/check_ajax_referer（CSRF）、current_user_can（鉴权）、
   ABSPATH/WP_CONTENT_DIR 常量拼接（路径）。

## 9. 第二次审计后建议的规则库改动清单（按优先级）

| 优先级 | 改动 | 来源 |
|---|---|---|
| P0 | 规则增加 `framework_scope` 字段；不匹配框架时 regex 命中降级 NEEDS_REVIEW | §4.1 |
| P0 | PHP CWE-89 AST 增加成员调用形态（`->query(`/`->get_results(` 等） | §4.1 |
| P0 | 内建 mechanical triage 层（F1 vendored 清单+F2 非-sink+F3 硬编码参数） | §5 |
| P0 | batch_verify 增加按文件聚合批次模式 | §6.1 |
| P1 | CWE-918 拆分本地文件系统函数与网络请求 sink | §4.2 |
| P1 | collect 容错 JSON + UNREACHABLE blocking_point 自动回填 | §6.2/6.4 |
| P1 | ast_scanner 填充 source_pattern/language 字段 | §6.5 |
| P1 | R0 依赖清单补 tree-sitter-perl/tree-sitter-bash | §6.7 |
| P2 | r05 工具输出 NO_GIT 状态 | §6.8 |
| P2 | R3 同点跨 CWE 关联标注 | §7 |
| P2 | verifier 提示词固化 adjacent-escape-miss 与 urldecode-绕过模式 | §8 |
