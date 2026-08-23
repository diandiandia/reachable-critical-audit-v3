# PowerShell 实证工具链手册 (v3.1)

> 来源：W6_MORE_LANGS_FINDINGS.md（§9-§11）与 SKILL_LESSONS_10LANG_CAMPAIGN.md（§1.2/§3.3）。实证工件：审计项目内 `.audit_results/reachable_vulnerabilities_report.md`。

## 1. 工具链探测
- 探测 `pwsh`（PowerShell Core 7.x，审计实证用 7.5.2）与 `powershell`（Windows PowerShell 5.1）；**环境可能未预置 pwsh**——批次初判"无 pwsh 可用、verifier 判定 static_only"，后由 verifier 自行安装 pwsh 完成 E2E（W6 §9 批事实 + 批次报告）。工具链探测 = `which pwsh; pwsh --version`，缺失时先装再实证，不得以"无运行时"豁免实证（§13.3 先例）。
- 测试路径约定：PowerShell 生态为 **`tst/` 目录 + `*.Tests.*` 文件形态**（该批次 1147/1853 候选在 tst/ 被默认过滤漏掉）——R1 过滤语言映射表必须含 `powershell→tst/+*.Tests.*`（SKILL_LESSONS §1.2）。
- 锚点自检：PowerShell 无 grammar 时优雅跳过（SKILL_LESSONS §3.3），不阻塞 R0。
- PS 模块/包版本事实：E2E 使用 PSGallery 的模块包（锁定版本，报告标注 PSGallery E2E）——包版本与源码树版本须分别记录。

## 2. 版本记录义务
- 记录 pwsh 精确版本（7.5.2）与模块包版本（锁定版本 6.1.0）；`$PSVersionTable` 输出应入 harness 元数据。
- **运行时是否预置**本身是审计事实：无 pwsh 时证据分级只能是 static_only/edge_proven，安装后再跑 E2E 升级为 empirically_confirmed（批次报告 CAND-004 即此路径）。
- 模块加载路径记录：`Import-Module`/dot-source 的路径解析依赖 cwd 与 PSModulePath，实证脚本须固化相对路径（§10.1 的 project_root 解析教训同构）。

## 3. 常见陷阱清单
- **签名词库零覆盖 PowerShell 语义族**：7 个语义签名全是 C/Rust/Java/PHP/JS 形态（extend_from_slice/with_capacity/autoType 检查/set-cookie），PS sink 形态——`[ScriptBlock]::Create`、dot-source、`& $SafeCommands['...']`、`ParseInput`、`iex`——全无命中，R2 零 hits 属预期而非失败（W6 §9.1）；须补 scriptblock-injection/dynamic-exec 词族或直接走 LLM 假设路径。
- **空域无签收机制**：本地测试框架无网络端点 → network 域 0 surface 是真实结论，validate 拒收合法空域；须空数组 + `reviewed_by`/`empty_domain_reason` 签收（W6 §9.2）。
- **schema 违约**：storage 域 8 条 surface 全漏 `confidence` 字段被整域拒收（W6 §9.3）——复核逐字段断言。
- **行号漂移**：Get-TempRegistry 函数体在 Environment.ps1 被标成 TestRegistry.ps1（W6 §9.4）——suggested_line 裁决 + snippet 重定位落盘。
- **主代理批量修复二次污染**：把本来匹配的 entry 也标 evidence_rewritten_by，窗口匹配误清空 snippet——修复须逐 entry 对照源码，best-match 非空回滚（W6 §9.5）。
- **`$!` 后台复合命令陷阱**：`cd x && VAR=v cmd &` 的 `$!` 是 bash 子 shell 而非 cmd（§16.6 通用）——PS 服务型实证同样适用。
- **workflow_export 上下文缺字段**：v3 候选无 sink_content/source_pattern 时 prompt 回落到 sink_type（"Sink 代码: CWE-94"）——sink 缺失时读源文件 source_line 行内容兜底，**相对路径必须 project_root 解析**（cwd 漂移使 open 失败）；language 缺失按扩展名回退（.ps1→powershell）（W6 §10.1-10.2）。
- **主代理手工传 Workflow args 截断 prompt**（复制 80 字符预览而非完整 payload）——args 必须从落盘 payload 文件整读整传；journal.jsonl 的 result 字段名不统一（`value` vs `result`），collect 提取须兼容两字段（W6 §10.3-10.4）。
- **surface 归属合并丢失**：agent 把同链 surface 合并进主假设时只在回复里说明映射，未写进 hypotheses.json 的 surface_id → 门禁 ⑦ 假缺口；须补 secondary_surface_ids 字段，任务书要求输出 surface_ids 数组（W6 §9.6）；tracked_surfaces 必须填 SURF- 前缀 id 而非 file:line（W6 §9.7）。

## 4. 阳性模式（战役验证过的做法）
- **E2E + 对照组矩阵**（黄金实证）：CAND-004 verifier 自装 pwsh 后跑锁定版本模块包 PSGallery E2E——Describe/It/skipped 三种 name 模板注入全部执行 `touch` 标记文件（run 报告 Passed、静默代码执行），对照组 -ForEach 值注入无执行（批次报告）——同一 sink 的注入/对照双侧对比是 PS 代码注入面最强实证形态（§24.4 对照矩阵模式）。
- **PowerShell 批次实证产出**：3 REACHABLE（1 empirically_confirmed + 2 edge_proven，批次报告）——name 模板注入 RCE 以 E2E 定谳，其余调用边证据支撑 edge_proven，分级与证据严格对应。
- **LLM 假设生成路径独立可用**：签名零覆盖时 surface hints → agent 验证 → hypotheses 全链路已跑通（W6 §9.1）。
- **能力支配裁决模板**：CAND-008 框架偏好对象静默合并——攻击者代码已在会话执行即"前置持有任意文件写"，sink 零能力增量 → NEEDS_REVIEW + correction_record（W6 §11）；PS 的 `$SafeCommands` 白名单设计本身就是能力支配的判定依据。
- **隐式行为面识别**：约定文件自动执行 / symlink 截断向量不依赖攻击者运行代码——repo 内容本身是输入（W6 §11）——PS 模块约定（psd1/psm1 自动加载）是同类面。
- **测试路径过滤先行**：R1 前把 `tst/`、`*.Tests.*` 形态加入过滤，该批次批量 1853→有效候选（SKILL_LESSONS §1.2）。

## 5. 网络依赖
- **PSGallery 可达性**：锁定版本模块包从 PSGallery 下载用于 E2E（报告标注）；pwsh 安装器下载亦需网络——首次实证前须探测 gallery/pwsh 安装源可达性，阻断则降 edge_proven 并记录 blocker（§21.4 分级规则）。
- lessons 未记录 PowerShell 实证的其它网络阻断；纯源码级验证（grep 调用链）零网络依赖。

## 6. 实证范围建议
- **E2E 首选**（条件：pwsh 已装）：PS 是解释型语言，安装 pwsh 后 E2E 成本极低（模块包 E2E 一次通过）——代码执行类声称（`[ScriptBlock]::Create`/iex/dot-source 链）一律 E2E + 对照组。
- **机制级**：无 pwsh 或网络阻断时的兜底——调用边 + 分支可达性证据，只能支撑 edge_proven。
- **源事实级**：仅静态-only 声称（如报告插件路径、ci 场景）可接受，须显式标注 `static_only`（批次报告分级先例）。
- 所有实证分级与 claim_type 绑定：声称类按攻击影响定类（protocol_dos 等），不得因实证成本降级（§13.9 通用规则）。
