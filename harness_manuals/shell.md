# Shell 实证工具链手册 (v3.1)

> 来源：W6_MORE_LANGS_FINDINGS.md（§11-§12）与 SKILL_LESSONS_10LANG_CAMPAIGN.md（§1.4）。实证工件：审计项目内 `.audit_results/`（refute_sf6.py、reachable_vulnerabilities_report.md）。

## 1. 工具链探测
- 目标运行时是 **zsh**（shell 框架载体）：实证用 zsh 5.9（refute_sf6.py 运行事实）；zsh 5.8.1（2021-12）已被批次记为废止版本——探测 `zsh --version` 并核对与目标项目声明的兼容 zsh 版本（结果文件记录 zsh 5.x 全谱系行为差异）。
- 无本地 zsh 或需特定版本时**从源码构建 zsh**（SKILL_LESSONS §1.4：git.zsh/vcs_info verifier 构建 zsh 5.8 源码 + CVE-2021-45444 PWN 标记法实证矩阵，耗时 3595s 产出质量极高）——构建产物路径记录进 harness 元数据。
- 实证 driver 用 Python 起 pty 驱动交互式 zsh（refute_sf6.py 模式：`ZDOTDIR/.zshrc` 启用目标插件 → compinit + 插件加载 → pty 键入行**不带换行** → TAB 触发补全 eval），`python3` 是 Shell 实证工具链的一级成员。
- 测试路径约定：shell 批次未暴露新测试形态（SKILL_LESSONS §1.2 语言映射表无 shell 条目）——按仓库实际目录人工确认。

## 2. 版本记录义务
- 记录三元组：zsh 精确版本（5.9 vs 5.8 行为可完全不同——原生 expand-or-complete 在无插件 `zsh -f -i` 同样执行，W6 §12.5）、oh-my-zsh checkout 的 commit/tag、driver 的 python3 版本。
- **shell 版本 = 利用性前提**：CVE-2021-45444 的 PWN 标记法经验矩阵按 zsh 版本分别验证（SKILL_LESSONS §1.4）——报告显式记录"版本影响利用性"维度（§13.4 同构）。
- 框架版本（oh-my-zsh）与 shell 版本分开记录：trap 注入/缓存投毒行为由插件框架层决定，expand-or-complete 行为由 zsh 层决定（W6 §12.4-12.5）。

## 3. 常见陷阱清单
- **签名词库零覆盖**（与 PowerShell 同构）：Shell 签名零命中 → 走 LLM 假设生成路径（50 假设、env-injection-eval/cache-poison/remote-exec 四大家族质量高）；签名词库应补 trap/eval/source env 路径/`curl|sh` 词族（W6 §12.1）。
- **agent snippet 保真三连败**：`\)` 转义丢失（DATA-008:349）、JSON 转义层级错（DATA-009:814 三层反斜杠）、**幻觉行号**（upgrade.sh:229 实际在 231）——主代理修复时直接读源行字符级重写，幻觉行号须 grep 定位真实行（W6 §12.2）。
- **refutation 多波出队缺陷**：pool 无"已复核排除"条件时 12 个 REACHABLE 反复出队前 4 个——已加 `and "refutation" not in c`（W6 §12.3）。
- **snippet 内的裸引号破坏 JSON**：backtick 代码段内裸 `"`（LLM 假设 JSON 裸引号第 4 次重现）——代码段转义契约（W6 §15.8）。
- **默认配置 ≠ 无平台证据**：compdump 候选被 verifier 自标无平台证据（W6 §12.4）——"默认开启"三层语义（代码默认/模块默认加载/部署前提）清单照用（§22.3 通用）。
- **共享缓存场景残余**：lwd 级联降级时对"共享组可写缓存目录跨用户增量"显式记录保留意见（W6 §12.4）。
- **`$!` 后台复合命令陷阱**（§16.6 通用）：`VAR=v cmd &` 的 `$!` 是子 shell；用 `exec env ... cmd &` 或 Popen。
- **surface 合并映射第二次重现**：假设生成 agent "10 surfaces merged into shared hypotheses" 未写映射字段 → 门禁 ⑦ 报 50/60——按 entry_points (file,line±2) 内容级映射补 secondary_surface_ids（W6 §12.6）——假设生成任务书必须要求 surface_ids 数组。
- **长跑 verifier 无心跳误判失联**：git.zsh/vcs_info 簇 verifier 构建 zsh 5.8 + CVE-2021-45444 实证矩阵耗时 3595s，主代理误判失联手工补写——任务书强制第一步写 `_rX_<id>.json.pending` 心跳物证，落盘加冲突检测（SKILL_LESSONS §1.4）。

## 4. 阳性模式（战役验证过的做法）
- **pty 驱动的真实框架 E2E**（黄金实证）：refute_sf6.py——真实 oh-my-zsh 配置 + pty 键入无换行行 + TAB 触发补全 eval，保证 payload 只在补全 eval 内执行（行级永不接受/执行）——"补全时执行"类声称的标准 harness 形态。
- **原生行为归因修正**：CAND-007 的 `console $(...)+TAB` 在无插件 `zsh -f -i` 同样执行（zsh 原生 expand-or-complete）——refuter 独立实验区分"原生行为"与"插件注入"，归因更正入 refutation.note（W6 §12.5）。
- **供应链持久化实证**：env GIT_CONFIG_COUNT/KEY/VALUE 重定向 `git pull`——实测供应链替换、`.git/config` 无痕迹、适用于已有安装（W6 §12.7，F1 High）——`git -c`/env 注入家族可直接复现；该家族值得固化进 H4 检查清单条目（git 调用前未清 env 的项目普遍存在，W6 §12.7）。
- **裁决模式四连模板**：能力支配（CAND-001 trap ZSH 注入——默认 .zshrc export 覆盖 env 时攻击者已持有写框架文件能力）、by-design 用户中介（CAND-013 custom 目录）、opt-in+能力支配（CAND-014 lwd 级联）、verifier 自标无平台证据（CAND-005 compdump）——每类 correction_record 落盘，共享缓存场景残余显式记录保留意见（W6 §12.4）。
- **控制字节穿透实证**：cwd 目录名 ESC 经 `:q` 进窗口标题（W6 §12.7 F2，实测）——显示层控制字节用真实终端语义验证。
- **隐式行为面优先**：trap/eval 注入与约定文件自动执行不依赖攻击者运行代码——repo 内容本身是输入（克隆即执行面，W6 §11）——实证 harness 从"克隆后首次交互"起算。

## 5. 网络依赖
- **核心实证零网络**：本地 zsh + 本地 checkout 即完成（refute_sf6.py/GIT_CONFIG 实证均在本地）；GIT_CONFIG 重定向用 `file://` URL 可完全离线。
- zsh 源码构建需下载 tarball（SKILL_LESSONS §1.4 构建事实）；github.com 实测可达（§21.4 网络表：github.com 可达、proxy.golang.org 不可达）——oh-my-zsh 克隆无阻碍。
- 网络阻断时降源事实级 + 记录 blocker（§21.4 规则）；env 注入类声称（哨兵语义/环境变量处理）源事实级可接受。

## 6. 实证范围建议
- **E2E 首选**：zsh 解释型 + 本地可跑，pty 驱动真实框架的 E2E 成本低且是"补全时执行"类声称的唯一可信形态（refute_sf6.py 先例）。
- **机制级**：sed 替换串未转义（H7-B3）类函数体缺陷——函数体级实证必须标注 scope（机制 vs 全链，§15.6 规则）。
- **源事实级**：env 传播/哨兵值类（GIT_CONFIG 族）在代码态即可论证，配合一次实证即可确认（W6 §12.7 实证 + 无痕属性）。
- 版本矩阵维度必带：zsh 版本跨 5.x 谱系的行为差异（expand-or-complete/Oniguruma 类优化）要求实证矩阵记录版本列（W6 §12.5、§13.4 同构）。
