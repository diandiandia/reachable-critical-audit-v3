# W6 更多语言验证发现与修复（批次 1 起）

> **日期**：2026-08-16
> **阶段**：top15 语言全覆盖验证（批次 1：AWStats/Pester/ohmyzsh/Newtonsoft.Json）

## 1. surface_mapper：HTML 实体双态匹配（AWStats 首发现）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 1.1 | W5 加的 `html.unescape` 无条件解码 snippet——Perl 源码中的**字面实体**（`s/&/&amp;/g;` 这类 HTML 转义代码本身就是源码内容）被误解码为 `&` | 正确证据被误拒（AWStats 2 处） | normalize 保留原始 snippet + 存 `snippet_unescaped` 变体；匹配时双态尝试，任一命中即可 |
| 1.2 | 反向包含匹配对超短行（`(`、`#`、`)`）恒真——它们几乎总是任何 snippet 的子串 | suggested_lines 被噪声污染（111/117/182 等假候选） | 候选过滤 `len(fl) >= 10` |

测试固化：`test_source_literal_entities_match_dual_variant`（73 测试全绿）。

## 2. AWStats 流程观察

- 59 surfaces（4 域）全部验证通过；v2.2 基线面全覆盖
- 测绘 agent 产出的 downstream_hints 质量显著高于三锚点（含 v2.2 caveat 自查：
  data 域 agent 主动指出 v2.2 diricons harness 未模拟 quote-strip）
- R2: 3576 hits → 89 hypotheses（HEADER-INJ 3041 命中——HTML 输出编码家族密集属正常）

## 3. R4 产出 JSON 非法转义（AWStats 收尾发现）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 3.1 | R4 agent 在 JSON 证据文本中写出**未转义反斜杠**（`\d`/`\w`/`\s` 正则片段、`\\s` 奇数串） | `json.load` 严格模式失败，r4-collect 无法落盘 | 主代理单遍扫描修复（见下） |
| 3.2 | 正则迭代修复会**振荡不收敛**：`\d`→`\\d` 后，第二个 `\` 后跟 `d` 又被下轮再双写→`\\\d` 再次非法 | 修复循环永远失败 | 必须**单遍扫描**：字符串内 `\` 后接合法转义（含 `\u`+4hex）原样保留，否则只双写该 `\` 并跳过下一字符（不重审） |
| 3.3 | `\u` 前缀陷阱：`\user`（Windows 路径）被"合法转义前缀"误放行，JSON 仍失败 | 常规"合法转义字符集"判定不够 | `\u` 仅当后接 4 个 hex 才合法 |

**skill 侧修复方向**：`stage_r4_collect`（及 collect 全家族）应内建 lenient load + 单遍转义修复；任务书应显式要求"JSON 证据文本中的反斜杠必须双写"。

## 4. surface 覆盖率簿记缺口（门禁 ⑦ 误报）

**现象**：4 个 surface（LoadPlugin eval ×2、history 文件读写 ×2）R2 零假设（窗口匹配无命中）且 R4 findings 未输出 `surface_id` 字段 → 门禁 ⑦ 报 55/59 未覆盖。
**真相**：R4 agent 已实质审查这些路径——H4 coverage_note 逐一点名 SURF-PROC-AW-005（LoadPlugin Init eval 净化阻断），H1 锚定 Read_History_With_TmpUpdate 读+写机制——只是没把 surface id 写进结构化字段。
**裁决**：主代理按 coverage_note/锚点/call_chain 内容实证映射，补 `tracked_surfaces` 字段（59/59 PASS）。
**skill 侧修复方向**：
- `task_templates/biz_hypothesis.md` 增加输出字段 `tracked_surfaces: [surface_id...]`（锚点之外的扩展审查面也要回填）；
- r4-collect 后主代理必须核对覆盖率——缺口时先查 coverage_note 内容映射（证据存在）而非盲目重审。

## 5. refutation resume 契约（Mode W）

- `Workflow({scriptPath, resumeFromRunId})` 未传 `args` → 脚本内 `args.candidates` undefined 崩溃。
  **resume 必须携带与首次运行一致的 args**（存档于 /tmp/refute_args_aw.json 模式；或脚本内 `args ?? {}` 防御）。
- agent 级 API Connection lost（mid-response）→ resumeFromRunId 只重跑 errored agents，已完成者缓存命中——3 个失败证伪者补齐后 4/4 候选全票存活。
- CAND-002 前一轮"1 票 refute"实为 refuter 中途结论；resume 补全后最终 2/2 存活——**refuter 半程输出不可作为裁决依据**，以 schema-validated 最终返回为准。

## 6. 条件式 REACHABLE 的 blocking_point 语义（先例固化）

AWStats 4 个候选中有 3 个带部署前提：CAND-001（AWSTATS_ENABLE_CONFIG_DIR 已设）、CAND-002（LoadPlugin=rawlog 启用）、CAND-003（key 机制可移除/白名单）。N=2 复核全票存活的关键：**verifier 在 blocking_point 显式记录了前提，判定从未主张默认可达**（refuter #1 实测默认配置 die 行为后仍投"不证伪"，理由即此）。与 sinatra/lighttpd config-gated 先例的区别：那些案例 refuter 投 refute（前提被默认当开），本例前提透明。
**固化规则**：条件式 REACHABLE 可在 blocking_point 显式记录前提后保留 verdict；报告必须逐条列出前提；前提被"默认当开"则按 config-gated 先例降级 NEEDS_REVIEW。

## 7. R0 smoke 全 skipped 边界（Pester 发现）

**现象**：`smoke_test` 的 7 个 known_instances 全部锚定在其他仓库（actix-web/AWStats/ktor/fastjson2/django），Pester 仓库内 testable=0 → hit_rate=0.0。按 R0 门禁字面 `hit_rate < 1.0` 会**阻止启动**——误伤。
**裁决**：testable=0 时所有项 skipped（分母为空）= 无失败项 → 放行；validate=True 且无 `hit=False, skipped=False` 项即可。R0 门禁意图是"签名库在能测的地方必须命中"，跨仓库锚点库下单一仓库审计必然全 skipped。
**skill 侧修复方向**：SKILL.md R0 门禁条件改为 `hit_rate < 1.0 AND testable > 0 → 阻止`；或 smoke_test 接受多仓库路径（把锚点仓库一并传入）。

## 8. surface_mapper tasks 命令 set 序列化 bug（Pester 发现）

`gen_surface_tasks` 的 `output_schema` 用 **set 字面量**（`{"id","type",...}`）→ `json.dumps` TypeError → `tasks` 子命令全崩。AWStats 时主代理手工绕过了该命令，bug 一直潜伏。
**修复**：set → list（v3 workspace 已改，16 测试全绿，已安装到 skill 目录）。
**教训**：`output_schema` 是给 agent 看的文档字段，不该用 set 表达；main() 的 tasks 子命令输出是多 JSON 文档拼接（每 task 一个 dumps），下游消费须按行/分块解析——文档化此契约或改成单数组输出。
**测试缺口**：`test_tasks_4_domains` 只断言字段存在，未走 main() 序列化路径——CLI 子命令无测试覆盖。给 main() 加薄测试或把生成逻辑与打印分离。

## 9. PowerShell 语言盲区（Pester 发现，top15 验证核心发现）

| # | 缺陷 | 后果 | 处置 |
|---|---|---|---|
| 9.1 | **7 个语义签名对 PowerShell 零覆盖**：grep 词库全是 C/Rust/Java/PHP/JS 系（extend_from_slice/with_capacity/checkAutoType/set-cookie），PS sink 形态（`[ScriptBlock]::Create`、dot-source、`& $SafeCommands['...']`、`ParseInput`、`iex`）全无 | R2 match 0 hits，签名匹配对 .ps1 形同虚设 | 走 LLM 假设生成路径（surface hints → agent 验证 → hypotheses）；签名库补 PowerShell 词族（scriptblock-injection/dynamic-exec 家族） |
| 9.2 | **空域产出无签收机制**：network 域 0 surface（本地测试框架无网络端点，真实结论）被 validate 拒收 | 合法空域无法闭合 R1 | validate 空数组 + `reviewed_by`/`empty_domain_reason` 签收放行（已改+安装）；normalize 必须透传非 surfaces 字段否则签收字段被丢弃（已修） |
| 9.3 | **schema 契约违约**：storage 域 agent 全部 8 条 surface 漏 `confidence` 字段 | 校验拒收整域 | 主代理按 trust_boundary 补填并标 `confidence_added_by`；任务书 schema 已含该字段，agent 未遵守——复核阶段必须逐字段断言 |
| 9.4 | **行号漂移 pattern 化**：data/process 各 1 处漂移 + 1 处文件标错（Get-TempRegistry 函数体在 Environment.ps1 被标成 TestRegistry.ps1） | 证据校验拒收 | suggested_line 裁决 + snippet 重定位（line_corrections 落盘）——现有机制足够，主代理裁决时间可接受 |
| 9.5 | **主代理修复脚本自身引入假标记**：批量重写逻辑把"本来就匹配"的 entry 也标了 evidence_rewritten_by，且窗口匹配误清空了 snippet | 二次污染 | 教训：主代理批量修复也要逐 entry 对照源码验证；修复脚本 best-match 必须保证非空回滚 |
| 9.6 | **假设生成的 surface 归属合并丢失**：agent 把同链 surface 合并进主假设时只在最终回复里说明映射（"5 surfaces are same-chain variants merged by design"），未写进 hypotheses.json 的 surface_id | 门禁 ⑦ 报 27/32 覆盖缺口 | 主代理按 agent 回复中的明示映射补 `secondary_surface_ids` 字段（32/32 PASS）；假设生成任务书应要求输出 `surface_ids` 数组而非单值 |
| 9.7 | **R4 agent 的 tracked_surfaces 用 file:line 而非 surface id** | 覆盖率统计漏算 | 主代理只认 SURF- 前缀 id；biz_hypothesis 任务书应明确 tracked_surfaces 填 surface id |

## 10. workflow_export prompt 模板缺陷（Pester 发现，已修复）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 10.1 | v3 候选无 `sink_content`/`source_pattern` 字段 → `_build_context` 回落到 sink_type → prompt "Sink 代码: `CWE-94`" | verifier 拿不到真实 sink 行内容 | sink 缺失时读源文件 source_line 行内容兜底（**相对路径必须 project_root 解析**——初版修复仍漏，cwd 漂移使 open 失败） |
| 10.2 | `language` 字段缺失 → prompt "语言: ?" | verifier 无语言上下文 | `_EXT_LANG` 按扩展名回退 |
| 10.3 | **主代理手工传 Workflow args 截断 prompt**（复制 80 字符预览而非完整 payload）→ agent 拿到残缺任务书 | 产出垃圾 verdict | 教训：Workflow args 必须从落盘 payload 文件整读整传；发现后立即 TaskStop 重跑（截断 prompt 与完整 prompt 缓存键不同，重跑不命中坏缓存） |
| 10.4 | journal.jsonl 的 result 字段名不统一（波次 1 用 `value`、波次 2 用 `result`） | collect 提取为空 | 提取脚本同时兼容两字段 |

## 11. R3.5 裁决先例扩展（Pester）

- **"capability 已被前置持有"模式第三次实战拦截**：CAND-008（$PesterPreference 静默合并）——污染充分条件 = 攻击者代码已在会话执行，此时任意文件写/更强持久化已被持有 → sink 零能力增量 → NEEDS_REVIEW + correction_record（残余为 defense-in-depth：无 opt-out 参数）。
- **同轮第一次区分出"无代码执行前提的隐式行为面"**：CAND-002（约定文件自动执行）与 CAND-005（symlink 截断向量）不依赖攻击者运行任何代码——repo 内容本身是输入（克隆即执行面）。refuter 的"零增量"论证只适用于攻击者已跑测试代码的场景，对隐式行为面不成立 → 保留 REACHABLE 但收敛前提与严重度。
- **裁决操作化**：1/2 票 refute 时主代理逐条分析 refute 论据的适用前提范围，区分"能力支配"（降级）与"信任模型重构"（保留+前提收敛），correction_record 落盘。

## 12. Shell 语言盲区与 ohmyzsh 批次（Shell 首审，15 候选 4 裁决拦截）

| # | 发现 | 处置/教训 |
|---|---|---|
| 12.1 | Shell 签名同样零覆盖（与 PowerShell 同）→ LLM 假设生成路径产出 50 假设质量高（env-injection-eval/cache-poison/remote-exec 四大家族） | 签名库应补 shell/zsh 词族（trap/eval/source env 路径/curl\|sh）；LLM 路径已验证可独立运行 |
| 12.2 | **agent snippet 保真失败模式**：`\)` 转义丢失（DATA-008:349）、JSON 转义层级出错（DATA-009:814 三层反斜杠）、**幻觉行号**（upgrade.sh:229 实际在 231，该行 agent 完全没找到） | 主代理修复时直接读源行字符级重写（不再做窗口匹配猜测）；幻觉行号需 grep 定位真实行 |
| 12.3 | **refutation 多波出队缺陷**：pool 无"已复核排除"条件，12 个 REACHABLE 反复出队前 4 个 | workflow_export refutation pool 加 `and "refutation" not in c`（已修） |
| 12.4 | **裁决模式齐现**（15 候选 4 拦截 = 27%）：能力支配（CAND-001 trap ZSH 注入——默认 .zshrc export 覆盖 env + 放置能力=写框架文件能力）、by-design 用户中介（CAND-013 custom 目录——框架无自动写入机制）、opt-in+能力支配（CAND-014 lwd 级联——refuter 三维度论证）、verifier 自标无平台证据（CAND-005 compdump） | 每类 correction_record 落盘；主代理裁决时对"共享缓存场景残余"显式记录保留意见（CAND-014 共享组可写缓存目录跨用户增量未被 refuter 覆盖） |
| 12.5 | **refuter 更正 verifier 归因**：CAND-007 symfony6 的 `console $(...)+TAB` 在无插件 zsh -f -i 同样执行（zsh 原生 expand-or-complete）——verifier 的实证归因部分错误，但 refuter 独立实验确认 plugin eval 注入仍成立 | 复核价值实证：即使不推翻结论，归因更正也进入 refutation.note 与报告 |
| 12.6 | **surface 合并映射重现**（§9.6 同构）：假设生成 agent "10 surfaces merged into shared hypotheses" 未写映射字段 → 门禁 ⑦ 报 50/60 | 主代理按 entry_points (file,line±2) 内容级映射补 secondary_surface_ids（60/60）；假设生成任务书必须要求 surface_ids 数组（两次重现 → 必须进模板） |
| 12.7 | **新家族产出**：R4-H4-01 env GIT_CONFIG_* 重定向 git pull（实证、无痕、适用于已有安装——供应链攻击的第二通道）；R4-H4-02 cwd 目录名控制字节穿透 `:q` 进窗口标题；H7-B3 sed 替换串未转义 | GIT_CONFIG env 家族值得作为 H4 检查清单条目固化（git 调用前未清 env 的项目普遍存在） |


## 13. C# 语言盲区与 Newtonsoft.Json 批次（C# 首审，8 候选 1 裁决降级）

| # | 发现 | 处置/教训 |
|---|---|---|
| 13.1 | **签名库对 C# 反序列化语义族零覆盖**：22 签名命中 → 10 假设全 drop（固定常量 StringBuilder(256)/Tests 代码/MaxDepth 有界），sink_discovery_rate=0%；8 候选全部来自 LLM 假设生成路径，产出 TypeNameHandling $type / Type.GetType 直通 / ISerializable ctor / Expression.Compile 放大器 / JPath ReDoS 五大家族（4 REACHABLE 实证级） | 签名库应补：`TypeNameHandling`、`BindToType`、`Assembly.Load*`、`Type.GetType(s, true)`、`ISerializableCreator`、`Expression.*Compile`、`Regex.IsMatch`+`InfiniteMatchTimeout`；LLM 路径对本语言质量已充分 |
| 13.2 | **反序列化 gate 语义族**：TypeNameHandling.Auto 读取端无特判（与 Objects/Arrays 行为一致）；binder 内置黑名单仅 3 类型名；`:819` 兼容检查只限族不限实例 | 反序列化框架的 gate 审计模板化：gate 枚举值×读取/写入端矩阵必须全查（写入端差异≠读取端差异） |
| 13.3 | **实证环境从零构建**：审计现场无 .NET 运行时 → dotnet-install 脚本 + `-p:LibraryFrameworks=net8.0` 单 TFM 构建（Json.NET 零第三方依赖，restore 仅 SourceLink 需版本属性注入） | 实证类声称不可因"无运行时"豁免——优先现场装 SDK；构建库按审计版本源码而非 NuGet 包 |
| 13.4 | **运行时版本改变利用性（平台维度实证）**：维护者自带灾难性 pattern（BacktrackingRegex_SingleMatch_TimeoutRespected 测试）在 net8 上已被运行时优化（32ms 完成）——该测试在旧 TFM 上才体现灾难性；经 patsearch 独立搜索确认 `^(a|a?)+$` 在 net8 仍 2^n（129ms→29.8s，n=20→28） | ReDoS 实证前必须先做 pattern 搜索（自动原子化会假阴性）；报告显式记录"运行时版本影响利用性"这一前提维度 |
| 13.5 | **R4 agent 证据机制误描述被实证纠正**：H1-F2 BSON 预分配原证据"流提前结束仅抛 EndOfStreamException"——实测该异常被 ReadType:221 catch 吞掉转干净 EOF（无异常传播、分配不回滚、调用方无感知），行为比原描述更隐蔽 | R4 findings 中的异常路径描述必须实证抽验（本例反而坐实+加强 finding）；实证结果写 finding.empirical_result + mechanism_correction |
| 13.6 | **refuter 发现更强向量**：CAND-008 证伪者 #1 发现 ParseSide 允许 =~ 两侧任一为路径表达式——固定 path 下 pattern 亦来自攻击者 JSON 树（比 verifier 场景 (a) 更强的 pattern 控制向量） | 证伪者不只证伪，会补强向量；refutation.strengthened 字段落盘进报告 |
| 13.7 | **JObject 根上的 `$[?()]` 过滤子节点而非对象本身**：T1b 双侧树取向量在 JObject 根 0ms 假阴性，包数组后才触发（1865ms） | JsonPath 语义前提（filter 作用对象）必须在实证前验证，0ms 结果先怀疑语义前提而非结论 |
| 13.8 | **第 4 次能力支配裁决拦截**（CAND-006 缓冲倍增）：宿主在库调用前已物化输入（2x UTF-16），库的 2x 常数因子不构成新能力；claim_type=other 的"解析器通用性质"裁决与降级裁决同源——先例已四连（Pester CAND-008、ohmyzsh CAND-001、ohmyzsh CAND-014、本批 CAND-006） | 裁决先例固化为："线性常数因子放大+宿主前置持有" → 能力支配 → NEEDS_REVIEW 保留意见（informational）；main-agent claim_type 裁决须与 R3.5 降级裁决共用同一论证链，避免自相矛盾 |
| 13.9 | **claim_type 诚实性代价**：CAND-008 实证后定 protocol_dos（声称类）→ gate ③ 强制实证——即便环境无运行时也不得改判 other 规避门禁 | gate ③ 的声称类分类必须按攻击影响定，不得因实证成本降级 claim；先实证后分类的顺序记录 |
| 13.10 | **surface 签收模式定型**（第三次）：29 surface 中 18 覆盖映射 + 11 负结论签名（reviewed_by=main-agent + empty_domain_reason），零手工补缺 | 与 §4/§9.6/§12.6 合并为门禁 ⑦ 标准操作：负结论 surface 签收算覆盖，不需凑假设 |

## 14. Python 语言盲区与 Django 批次（Python 首审，10 候选 2 REACHABLE 1 降级）

| # | 发现 | 处置/教训 |
|---|---|---|
| 14.1 | **Python 签名库（11 规则）1784 命中 → 81 假设 0 keep**：规则为通用 regex 模式（append/encode/join 类），命中集全是防御性转义（escape/re.escape/base64）、框架自配置（validators.append/locales）、有界结构；Django 真实 sink（asgi read_body 无界循环、RequestSite.get_host、pickle.loads 三后端族、safe_join）**零签名覆盖** | 签名库需补框架语义族：asgi receive 循环落盘、get_host/validate_host、pickle.loads+cache/session 后端矩阵、tag_re 类正则、import_string 配置族；通用 regex 规则（append/encode）对本语言无区分度应降权或退役 |
| 14.2 | **LLM 假设生成器的防御性偏差**：23 假设中 13 条是"防御验证签收"（gate 已 Read 验证后建议不投入）——Django 成熟度高所以合理，但注意 LLM 生成的假设自带 gate_observation 预判，可能诱导 verifier 复读而非独立验证 | 假设生成任务书应要求"假设必须指向残余面/未决面，已防御面标注 boundary-confirmation 单独归类"；签收类假设不占 R3 队列 |
| 14.3 | **"检查点晚于累积点"模式第三次复现**（Vapor C1 → Json.NET 无 → Django CAND-001）：ASGI read_body 全量落盘后 _check_data_too_big 才可触发 + body_receive_timeout 死代码；T1 实证 10,000× 超额 | 该模式已固化为 H1 检查清单第一条："限制检查点与累积点的先后"——三个框架（Vapor/Django）同构，值得进 signature_matcher 的 LOGIC_PATTERN 族（写循环内无预算检查） |
| 14.4 | **R3.5 拦截模式第 5 例**："开发专用面+后果有界"（CAND-009 runserver）：默认回环绑定 + 模块自述非生产 + 启动 WARNING + 414/close 全有界 → 证伪者三向论证（平台前提/信任边界惯例假设/gate 当默认开）→ 降级 NEEDS_REVIEW | 与 by-design 先例合并为"显式警告的开发/非生产组件"子类；T2 实证证明残留字节仅同连接自混淆——**证伪者论点需要实证闭环**（协议走私声称必须实测跨请求边界） |
| 14.5 | **verifier 用现场实证完成 UNREACHABLE**（CAND-010 邮件头 CRLF：跑真实 Django checkout 验证 stdlib policy fail-closed）+ **R4 agent 实证了 O(n²)**（H1-F3 模板 tag_re 60KB>60s）——subagent 自发跑实证的倾向增强 | 正向信号：verifier/R4 任务书应显式鼓励小实证；实证结果落 verdict.empirical 字段（即使 UNREACHABLE） |
| 14.6 | **agent 转写防护成功**：4 个测绘 agent 的 46 surface 全部证据行号经 validate 器校验（仅 3 处行号漂移被 suggested_line 捕获）；H5/H6/H7 agent 报告"所有 file:line 均为实际 Read 行" | surface_mapper validate 的逐行证据校验是有效防线；行号漂移修复后重验形成闭环 |
| 14.7 | **Django 特有裁决记录**：ALLOWED_HOSTS gate 矩阵（默认全锁=退化阻断 vs '*'=零阻断）——CAND-002 按"gate 可降级配置+文档支持翻转"保留 REACHABLE 并显式记录矩阵（区别于 CAND-009 的"无部署必须满足"） | 裁决先例新增：**"必然翻转的配置 gate"（保留 REACHABLE+记录矩阵）vs "被警告的非默认操作"（降级）**——区分标准=是否存在任何可用部署必须翻转该 gate |
| 14.8 | **纯 Python 项目实证环境成本低**：venv + sys.path 导入审计源码即可跑全链路（asgiref 用 skill venv 补齐）；subprocess 起 runserver 可测协议面 | Python 项目声称类应一律实证（成本接近零）；无 pip 环境下用 skill venv 或手下载纯 Python 依赖 |

## 15. TypeScript 语言盲区与 NestJS 批次（TS 首审，15 候选 6 REACHABLE 7 裁决降级）

| # | 发现 | 处置/教训 |
|---|---|---|
| 15.1 | **TS 签名库 3 族 95 命中 → 12 假设 0 keep**：路径白名单族（85 命中）全为路由注册期变换（Nest 无运行期远端驱动的路径门禁）、buffer 族的 append 匹配为响应头 API、logic 族命中全在 test/。**系统性误报签名族**（与 §14 Python 同构） | TS/JS 签名需按"运行期 vs 构建期"区分：路由注册期代码应排除；补框架语义族（socket.on('data') 累积、JSON.stringify 无 catch、reply channel 拼接、multer 无 limits 默认） |
| 15.2 | **verifier 自主编译源码跑实证成为常态**（6 个候选 verifier 自己装依赖/编译/跑 harness：tsc 编译 JsonSocket、真实 aedes broker + mqtt 客户端、express 复刻 adapter、kafkajs 源码核验）——subagent 实证能力显著高于早期批次 | verifier 任务书应显式允许并鼓励小实证；实证结果必须落 empirical 字段（本次 CAND-001/012 的 empirical 未结构化导致门禁 ③ 假 FAIL，主代理补录——**collect 脚本应自动从 evidence 提取实证标记**） |
| 15.3 | **R3.5 拦截率 54%（历次最高）**：7 个降级全部来自证伪者的深度实证（CAND-002 基准压测 2.00x、CAND-005 kafkajs 订阅期过滤核验、CAND-006 broker 默认值事实核验、CAND-010 Object.assign 不污染实测、CAND-011 4.43ms vs 1.29ms 实测） | 证伪者现在自带实证工具链——**R3 verifier 的 gate 声明（"默认开"/"常见配置"）是证伪者首要攻击面**；"常见配置≠默认"论证模板固化（§14.7 先例的第三例） |
| 15.4 | **microservices 传输族成为新攻击面家族**：reply 通道可预测（`.reply`/`/reply` 后缀）+ 头驱动回复目标（Kafka REPLY_TOPIC 最强）+ broker 认证默认矩阵——5 传输同构缺陷一次审计全暴露 | H4 检查清单新增"reply 通道族"：消息型框架必查 reply-to/回复通道的可预测性与头驱动目标 |
| 15.5 | **同一 sink 家族内防护不对称**：CAND-003 RpcProxy 有异常防护判 UNREACHABLE，但 R4 H3-F1 发现原始 message 监听器路径（TCP/Redis/MQTT/NATS/RMQ 五个 server）无 catch → unhandledRejection 崩溃（Node 22 实测）——**verifier 只查了防护覆盖的一条路径** | 路径覆盖纪律强化：判 UNREACHABLE 的"异常处理链存在"必须枚举全部同族监听点（5 传输 × message 事件）；R4 与 R3 互为兜底的价值实证 |
| 15.6 | **TS 编译实证的依赖墙**：esbuild 全量 bundle 受 @nestjs 内部 import 阻碍 → 改用"逐字符提取真实函数体 + 剥 TS 类型标注"方案（isPatternMatch 实证）——但该方案只证明函数体级机制，链可达性被 R3.5 用 kafkajs 订阅期行为证伪 | 函数体级实证必须明确标注 scope（机制 vs 全链）；依赖墙时优先 npx esbuild --external 逐层降级，再退函数体提取 |
| 15.7 | **Refutation workflow 单候选双条目问题**：主代理手写 inline args 时把 CAND-011 拆成两条单证伪者条目（votes 语义破碎） | 证伪 args 必须每候选恰好一个 entry 含 2 prompts；collect 阶段对同 id 多 entry 合并投票 |
| 15.8 | **LLM 假设 JSON 裸引号第 4 次重现**（AWStats §3 → nest LLM-006/013）：backtick 代码段内裸 `"` 破坏 JSON | 已在主代理侧固化修复脚本（backtick 段内仅转义无反斜杠前置的引号）；**根修：LLM 假设生成任务书要求代码段用单引号或转义** |

## 16. Swift 语言盲区与 Vapor 批次（Swift 首审，17 候选 6 REACHABLE 5 裁决降级 3 实证）

| # | 发现 | 处置/教训 |
|---|---|---|
| 16.1 | **Swift 工具链代际偏移**：vapor 5.0.0-alpha.2 依赖 swift-http-server 声明 `swift-tools-version:6.4`（6.4 未发正式版），稳定版目录只有 6.2/6.3；用 6.2 构建报 tools 版本墙，预编译 binary 在 6.2 runtime 下符号不兼容（FoundationEssentials `_Representation`）。反复探测 download.swift.org 6.4.x 目录全部 404 | R0 bootstrap 必须先读 Package.swift swift-tools-version + Package.resolved 的 pins 再选工具链；实证 harness 元数据必须记录 `swift --version` 精确版本号 |
| 16.2 | **多代工具链路径遮蔽**：/opt/swift-6.4（6.4-dev 快照）一直在盘上且就是 Aug 15 构建 harness 的原工具链，被后解压的 /opt/swift（6.2）遮蔽，浪费了整轮下载探测 | 工具链探测应 find 全盘 swift 安装逐一核对版本，不要假定单一安装路径；swift-env.sh 类脚本是线索 |
| 16.3 | **响应体不可达破坏实证设计**：T6 首版以客户端收完 body 为完成信号——该 alpha 的流式响应体被直接丢弃（R4 H1-F5 实证：200+Content-Length+0 字节，连接挂起 ~30s），客户端永远收不到完成信号；首版 driver 还因非 daemon 采样线程在 fn() 抛异常后死循环，进程卡死在解释器 shutdown | 实证设计前先做 1 个冒烟请求验证响应可达性；测量点放在服务端（CPU tick/VmHWM）而非客户端完成信号；driver 采样线程必须 daemon + try/finally |
| 16.4 | **响应头时序作为服务端完成信号**：advanced ETag 的 generateETagHash 在 Response 构造前 await → time-to-headers == hash 完成时间；且 ETag 头格式本身是模式自检（sha256 hex vs mtime-size） | 利用框架内部时序做无侵入完成检测是通用技巧：先在代码里确认"昂贵操作在头之前还是之后"再定测量方案 |
| 16.5 | **stale 进程 + 端口复用是实证最大陷阱**（本轮两轮全零数据根源）：SIGINT 未杀死旧 App（Swift runtime 把 SIGTERM/SIGINT 转 SIGTRAP），新 App 绑定 18082 失败即崩，driver 全部请求打到旧进程的旧模式 | 每阶段新 app 前 pkill -9 清理端口 + `/diag` 自检路由（echo 配置态）验证模式后才开始测量；诊断进程先 `comm` 验证 PID 身份 |
| 16.6 | **`$!` 与后台复合命令陷阱**：`cd x && VAR=v cmd &` 的 $! 是 bash 子 shell 而非 cmd——/proc/$P/environ 查到的全是子 shell 环境，两次误判"env 没传进去" | 后台启动服务用 `exec env ... cmd &` 或 Popen；env 传播问题先看 comm 再下结论 |
| 16.7 | **R2 候选队列丢失 surface 关联**：candidates 的 hypothesis_id 用 "SIG-SINK-1+LLM-001+002" 命名空间，与 hypotheses.json 的 HYP-xxx、input_surface.json 的 SURF-xxx 无机械映射；140 假设的 keep/drop 决定未落盘（37 dropped 无持久理由）→ 门禁 ⑦ 覆盖映射被迫主代理语义重建（file+line 距离匹配 + 17 条手工补全） | 入队时必须写 `surface_ids: [...]`；R2 filter 的 keep/drop 必须落盘（dropped_by + reason）——这是 v3 流程的持久化缺口，同 Django/Nest 批次也存在 |
| 16.8 | **R3.5 证伪者引用旧 lessons 先例一击即中**（CAND-002 platform_excluded）：证伪者读到 SKILL_LESSONS_SWIFT_VAPOR §1.4 的用户复核先例（同缺陷已被降级 + 立规"前提平台不在支持范围→UNREACHABLE"），引用 Package.swift:7-12 无 Windows 平台直接证伪 | 同项目复审计时，verifier/证伪者任务书应附该项目旧 lessons 摘录；先例复用是 R3.5 最高效的证伪武器 |
| 16.9 | **R3.5 证伪者揪出 verifier 机制事实错误**（CAND-016）：Request.swift:74-83 是 if/else-if getter 链，`try?` 失败返回 nil 直接终结——XFF 回退分支在 Forwarded.for 解析失败时不可达，verifier 推断的回退语义是错的 | verifier 任务书强制"读完整函数/属性体，勿推断控制流回退语义"；多分支 getter 是事实错误高发区 |
| 16.10 | **证伪者自带实证成常规**（CAND-014）：证伪者跑真实 nginx 配置（error log + location 规则）实测 `//evil.com/admin` 在标准部署下前端规则面先归一、无分歧 | 与 nest §15.3 合并定式："代理/解析分歧"类声称必须实测标准部署行为——证伪者 lens 2 应包含标准基础设施（nginx/HAProxy）配置片段 |
| 16.11 | **等价能力支配第 6 例**（CAND-013 逗号拆分 ≡ 重复键）：URLEncodedFormData.set 对重复键追加多值，`arr=a,b` 与 `arr=a&arr=b` 解码结果完全等价——"绕过应用数组校验"的能力框架基线就有 | 能力支配先例库固化检查项：解析器"特性"声称的新能力必须先与框架基线编码能力（重复键/双形态）对比，等价即证伪 |
| 16.12 | **R4 与 R3.5 判定框架不一致**：R4 H5-F1/H7-F2 把 ErrorMiddleware 泄露判 High（存在性导向）而 R3.5 降级 NEEDS_REVIEW（前提维度导向：-c release 官方路径 + 默认回环绑定） | R4 confirmed 与 R3.5 降级重叠时，严重度以 R3.5 correction_record 为准，合并时强制 r3_link 引用（本次已做）；R4 任务书应声明"confirmed=模式存在，严重度另由 R3.5 前提维度裁定" |
| 16.13 | **Dead-cache 检查成为 verifier 标准动作**：ETagHashes StorageKey 从未注册被发现是 CAND-006 放大关键（每请求全量重读）；verifier 见到 `storage[key]` 写必须查该 key 注册点 | 该检查点纳入 verifier 任务书步骤 2（多态穿透旁）：“storage/缓存写点的 key 注册存在性” |
| 16.14 | **Swift runtime 特性陷阱**：SIGTERM/SIGINT → SIGTRAP 转译；LD_LIBRARY_PATH 必须含 swift runtime 目录；debug 构建 BoringSSL 哈希仍 ~1GB/s（128MB ≈ 0.1s）——早期 30s 观测全是 stale 进程假象 | Swift 项目的实证时间预算不要按 debug 慢假设；异常时长先怀疑 stale 进程/端口冲突再怀疑性能 |

## 17. PHP 语言盲区与 WordPress 批次（PHP 首审，10 候选 2 REACHABLE 2 裁决降级 1 机制实证）

| # | 发现 | 处置/教训 |
|---|---|---|
| 17.1 | **LLM 假设生成 agent 失控（2.5 小时无产出）**：R2 LLM agent 在 48 面 WordPress 大代码库上无限扩张验证范围，被我杀死时仍在"验证锚点"；主代理接手后 20 分钟产出 10 条假设（全部真实行号） | 大代码库（>200k 行）的 LLM 假设生成必须限时限额（≤30 分钟或 N 条硬上限）；agent 失控判据=超时+无中间产物落盘；主代理兜底生成假设是可行退路（有 surface 图时效率高得多） |
| 17.2 | **workflow 模板参数化的新陷阱**：把 `${c.file}` 塞进模块顶层 const STEPS 模板字面量 → 模块加载时求值 ReferenceError → 两个 workflow 波次 8ms 内全崩 | workflow 脚本里模板字面量的插值时机要逐个检查：const 定义处的 `${}` 在加载时求值；agent() 回调内的 `${}` 在运行时求值。修法：顶层 const 里禁插值，把变量引用移进 agent 回调的模板 |
| 17.3 | **mature-framework 签名零转化第三例**（PHP 910 hits 0 keep）：$wpdb->prepare 全参数化 + 操作符白名单（class-wp-query.php:2456-2459）+ intval 强制 + wp_safe_remote_get 全路径验证——filter agent 的 drop 理由全部落到具体防御点 | 与 §14/§15 合并定型："通用 regex 签名对成熟框架零区分度"；false_negative_risk 100% 时 LLM 假设 + R4 是唯一有效面 |
| 17.4 | **verifier 端到端双端验证完胜假设**（CAND-002/006）：我假设 feed CDATA `]]>` 突破（"仅 strip_tags"），verifier 找到 default-filters.php:32-36 的 _wp_specialchars 链杀掉 `>`；display_name 假设被 sanitize_text_field 的 wp_pre_kses_less_than 三个子防线逐条拆解 | 假设生成者必须查"该字段的全部过滤链注册"（default-filters + init 期动态注册），不能只看单一 sanitize 调用点——WordPress 的防御是分层且动态注册的（kses_init） |
| 17.5 | **动态注册防御被 verifier 漏掉、被证伪者找回**（CAND-001）：verifier 判"title_save_pre 仅 trim"，漏了 kses_init 对非 unfiltered_html 用户的 wp_filter_kses 动态注册（kses.php:2468）；证伪者用真实 WP_Hook 复测完整写链 3 载荷全杀 | 验证任务书必须包含"搜索该 filter 名的全部 add_filter 注册点（含 init 回调内动态注册）"；WordPress 的 kses_init/capability 条件注册是漏判高发区 |
| 17.6 | **裁决先例新增"矩阵保留"**：CAND-001 证伪者的两点均属实（author 级被杀、块主题默认路径不可达），但 Editor+经典主题矩阵是一线支持配置（theme-compat fallback 正是核心为此类主题维护的）→ 保留 REACHABLE + 端到端矩阵记录 + 实证降级为机制级 | 与 Django ALLOWED_HOSTS 矩阵先例（§14.7）合并："前提成立与否取决于部署矩阵时，按矩阵中最常见成立格裁决，矩阵显式记录" |
| 17.7 | **机制级实证的范围纪律**（CAND-001）：我的 harness 只跑了真实过滤链+sink 行（未跑 wp_insert_post/comments_template/主题加载）却被标 empirically_confirmed——证伪者指出后降级 edge_proven + scope_note | 实证分级必须区分：机制级（过滤链/函数体）vs 端到端（完整运行时）；机制级实证只能支撑 edge_proven 的边证据，不能直接升 empirically_confirmed |
| 17.8 | **PHP harness 依赖链构建模式**：WP_Hook/plugin.php/formatting.php 需要 l10n+pomo+$shortcode_tags 全局；define ABSPATH 后 require_once 路径一致性解决 WP_Hook 双声明 | PHP 项目的最小真实运行环境 = define 常量 + 按 include 图补全局变量；此模式可复用（后续 PHP 审计直接套） |
| 17.9 | **证伪者跑真实 WP_Hook 复测 + 真实路径解析测试**（CAND-003：实测 id 编码形态、realpath+file_exists 验证可达 .html；CAND-008：复算 host 真值表） | 证伪者实证能力已常态化的第四例——"static 推理判定 + 无实证"在证伪者眼中是首要攻击面 |
| 17.10 | **R3.5 拦截 50%（2/4）**：CAND-003 前提事实错误（严格相等门控漏看）、CAND-008 危害维度阻断（host 钳制闭环）——两个都是"verifier 沿假设惯性向前推，未回头验证承重前提" | verifier 任务书应增加步骤 0："先验证假设中的承重前提（grep 一句话能证实/证伪的），前提断裂立即终止回溯" |

## 18. Java 语言盲区与 Dubbo 批次（Java 首审，10 候选 2 REACHABLE 2 裁决降级 1 解码器实证）

| # | 发现 | 处置/教训 |
|---|---|---|
| 18.1 | **R2 agent 模式弃用生效**：按 §17.1 教训主代理直接生成 10 条假设（30 分钟 vs 2.5 小时），全部 file:line 真实 | 大代码库审计的 R2 标准操作定型：主代理生成假设 + 签名 hits 供证，不再拉 LLM agent |
| 18.2 | **verifier 深钻 fastjson2 依赖库内部**（CAND-001）：从 sources jar 验证 2.0.62 的 autoTypeBeforeHandler 接线（JSONReader.Context.config:5996-6001、JSONReaderJSONB:755-764 等三处解析点）+ "无内建 deny list" 事实 → 证伪我的前提（STRICT 是 throw 不是 warn-and-allow） | 依赖库安全语义（autoType 回调接线/内建名单）属于 verifier 必须追的"多态穿透"范围——反序列化类假设的前提必须落到依赖库版本级验证 |
| 18.3 | **同族判定一致性成为证伪武器**（CAND-007）：证伪者指出 CAND-007 与 CAND-002（UNREACHABLE）共享同一 Hessian2SerializerFactory.loadSerializedClass → DefaultSerializeClassChecker 阻断点，且安全状态为全局共享属性——两路径不可区分 → 一致性裁决降级 | 裁决先例新增：**同族一致性规则**——同一 sink 家族不同路径的 verdict 必须可比；无法区分 → 按最严格者统一 |
| 18.4 | **"危害被前提吸收"证伪模板**（CAND-004）：router 仅过滤现有 invoker（removeIf/remove 已验证），规则无法注入地址；持前提（ZK 写）时更简路径（CAND-006）等效 → 无边际能力增量 | 与 §16.11 能力支配合并：能力支配检查从"框架基线能力"扩展到"同前提下的其他路径能力"——"攻击者持此前提能做什么"是最强对照 |
| 18.5 | **真实解码器实证模式**（T1）：maven -pl 单模块编译 + dependency:build-classpath + 匿名子类调用真实 ExchangeCodec.decode；16 字节头部声明 1.87GB → REQUEST 全 NEED_MORE_INPUT（无上限）vs RESPONSE 8MB cap 截断——不对称性一行实证 | Java 项目实证成本低（javac+maven 单模块）；解码器/解析器类声称优先走"真实类 + 最小输入"实证，勿手写复刻 |
| 18.6 | **R1 大代码库 agent 超时第二例**（network/process 各 ~12 分钟 + 收尾消息后完成）：Dubbo 2400 文件 4 域测绘总耗时 2 小时+ | R1 agent 也应设硬时限（≤45 分钟）+ 中间产物落盘；surface 数量 12 恒定但证据验证深度需与代码库规模解耦 |
| 18.7 | **行号漂移自动修复器成型**：30+ 漂移经"±30 行内首行 snippet 匹配 + suggested_line 记录"全修（含多行 snippet 取首行） | 该修复器固化为 R1 验证标准件（vapor 3 处手修 → dubbo 30 处自动） |
| 18.8 | **QOS 面 R3/R4 交叉结论**：verifier 判 CAND-005 UNREACHABLE（危险命令 PROTECTED 默认），R4 H4-F2/H5-F1 确认匿名 PUBLIC 面与 ForeignHostPermitHandler 短路——两层结论互补不冲突 | R3 判"默认不可达"与 R4 记"配置漂移面"是合法的双轨记录；报告中必须同时呈现 |
| 18.9 | **H1-F1 的 claim 迁移**：无上限 body 从 R4 finding 而非队列候选出现——verifier 队列假设（10 条）未覆盖该面，R4 H1 假说抓住 | 门禁 ③ 的实证义务同样适用于 R4 confirmed 的 oom/unbounded 类 findings（本次 T1 实证满足） |

## 19. Kotlin 语言盲区与 Ktor 批次（Kotlin 首审，10 候选 5 REACHABLE 2 证伪降级 2 机制实证）

| # | 发现 | 处置/教训 |
|---|---|---|
| 19.1 | **Kotlin 签名惯用法噪音**：header_inject 2013 命中全为 StringBuilder.append、reflect 1718 全为 `::class`、url_open 1357 全为 HttpClient（客户端侧）——通用 regex 对 Kotlin 零区分度 | Kotlin 签名需重写为框架语义族（receive/readRemaining、respondRedirect、Cookie parse、XForwarded 写入点）；`::class`/`append(` 类模式直接退役 |
| 19.2 | **verbatim 循环提取实证 + 真实依赖 jar**（T1b）：ktor-io readBuffer 循环逐字符提取 + kotlinx.io 0.9.1（项目锁定版本）真实 Buffer —— 100MB 物化实证，绕开 gradle/expect-actual 构建墙 | multiplatform Kotlin 项目的实证路径：锁版本 jar 从 Maven Central 直取 + verbatim 函数提取；expect/actual 全量编译需要完整 KMP 构建（kotlinc -Xmulti-platform + atomicfu 仍失败） |
| 19.3 | **JDK 25 Inflater(false) 不做 gzip**（"incorrect header check"）——T6 实证首次失败即此；ktor 源码用 Inflater(true)+手动 GZIP_HEADER_SIZE 跳过正是这个原因 | 解压/压缩类实证先读目标代码的 Inflater 参数；JDK 22+ zip 实现变更（JEP 505 系）使旧 harness 假设失效 |
| 19.4 | **证伪者用真实编译产物做对抗实证**（CAND-003）：下载 ktor-http-jvm-3.5.1.jar（字节码确认与树源码一致）跑 29 种畸形头 35 条目 0/35 触发——"sink 分支是行为死代码"一击致命 | 解析类声称的证伪标准动作：真实 jar + 畸形输入矩阵 + 计数触发；与 §16.10/§18.2 合并为证伪者实证工具箱第三件 |
| 19.5 | **"sink 分支行为死代码"证伪模板**（CAND-003 2/2 杀）：verifier 验证了调用边（真实）但未验证分支可达性（默认配置下 encode 参数恒 URI_ENCODING）→ 边真实 ≠ 分支可达 | verifier 任务书补强制项：sink 的每个条件分支都必须给出"攻击者输入到达该分支的具体配置/输入"证据，默认路径参数（encoding/mode 类）逐一对照默认值 |
| 19.6 | **by-design 多态反序列化裁决**（CAND-009）：receiveType 编译期静态 + kotlinx 多态仅开发者注册类集 + gson/jackson 默认静态类型 → "攻击者从白名单选类"= 文档化特性 | 与 §16.11 能力支配先例合并：类型系统强约束（编译期静态类型）是比运行时白名单更强的阻断——先查类型系统再查配置 |
| 19.7 | **默认值家族收割**（H7 9 findings）：maxFrameSize Long.MAX / maxDecodedContentLength -1 / cookie secure false / 客户端 cookie 无签名 / 异常回显——全部"默认值=无防护"族 | H7 检查清单扩展："数值上限类默认值"专项——MAX_VALUE/-1/0 三值即红旗（vapor URLEncodedForm maxRecursionDepth 100 为对照正向例） |
| 19.8 | **CIO/Netty 引擎差异面成为证伪武器**（CAND-003 PATH A 仅 CIO 执行；Netty 用 ServerCookieDecoder.LAX 重写）——verifier 按"任一引擎"判 REACHABLE 而证伪者按"旗舰引擎"复核 | 多引擎框架的判定规则：REACHABLE 需在文档默认引擎（Netty）成立；"某引擎成立"必须显式标注引擎矩阵 |

## 20. Scala 语言盲区与 Akka HTTP 批次（Scala 首审，10 候选 1 REACHABLE 3 裁决降级 R3.5 拦截 75%）

| # | 发现 | 处置/教训 |
|---|---|---|
| 20.1 | **R3.5 拦截率 75% 历批次最高**：3/4 降级全部来自证伪者的机制级深钻（FrameEventParser 逐 chunk 流式、HttpMessage Host 一致性 400、filename* RFC 5987 合规性）——verifier 的 REACHABLE 在成熟框架上集中于"机制真但危害未建立"类 | 成熟框架（防御默认完整）的 R3 假设应预设"机制真≠危害真"；verifier 任务书对 CWE-436/601 类必须要求危害场景实例化（第二解析器/受害者流程） |
| 20.2 | **"引擎流式 vs 应用物化"区分成为裁决关键**（CAND-003）：akka WS 引擎逐 chunk 流式（背压约束）vs ktor 引擎头部解析即 allocate 2GiB——同族声称（WS 帧 OOM）在两个框架结论相反 | WS 帧声称的检查清单：先分"引擎是否流式/物化"，再查"应用侧 toStrict 与 HTTP 路径限额的不对称性"——不对称性本身是独立 finding（NEEDS_REVIEW 级） |
| 20.3 | **CWE-436 双解析器前提显式化**（CAND-005）：浏览器是请求头生成方而非二次解析器；RFC 5987 规定的百分号解码是合规非分歧 | CWE-436 判定必须枚举"对同一字节流做安全判定的两个解析器"并证明分歧；"与浏览器不一致"默认不成立 |
| 20.4 | **Host↔authority 一致性校验是 absolute-form 家族的封口**（CAND-008）：akka-http 拒绝不一致（400）恰是该攻击家族的前提破坏 | absolute-form/请求走私类假设的检查第一步：目标框架是否校验 Host↔authority 一致性——有则核心形态直接封死 |
| 20.5 | **Scala 项目 R1 证据质量高**（仅 1 JSON 语法错误 + 24 行号漂移自动修复；未出现 WP/Dubbo 级的 agent 失控） | 495 文件规模是 R1 agent 的舒适区；~500 文件以下无需限时令 |
| 20.6 | **配置默认值矩阵成为完整防御体系**（max-content-length 8m / max-header-count 64 / enable-http2 false / Host 一致性 / request-timeout 20s）——akka-http 是 4 批次中防御默认最完整的框架 | H7 审查对防御完整框架的价值：输出"正向默认确认"而非漏洞；报告应显式列出防御面（对使用方是选型信息） |

## 21. Go 语言盲区与 etcd 批次（Go 首审，10 候选 2 REACHABLE 4 裁决降级 R3.5 拦截 66.7%）

| # | 发现 | 处置/教训 |
|---|---|---|
| 21.1 | **证伪者跑 106 万随机用例对拍**（CAND-003）：adt.Contains 与朴素并集覆盖模型差分零失配——区间语义类声称的最强证伪武器是差分测试而非推理 | 区间/边界类声称的证伪标准动作：小规模实现参照模型 + 百万级随机对拍；该模式应进 refutation 工作流模板 |
| 21.2 | **"无上限"声称的分布验证**（CAND-004）：verifier 判"事件缓冲无上限"，证伪者找到 chanBufLen=128 + victim 每 watcher ≤1 批 + ctrlStreamBufLen=16 逐级背压——"无上限"常是"未找到上限" | verifier 对"无上限"声称必须枚举队列/通道的每一跳容量常量；"未找到"≠"不存在"（与 ktor CAND-001 的全树 grep 形成对照：那里是真无 RequestLimit 插件，这里是真有限制） |
| 21.3 | **哨兵值语义**（CAND-002）：MaxUint32 是 grpc-go 的显式"无限制"哨兵（SETTINGS 不通告 + 拒绝检查 4.29e9）——默认值审计必须查依赖库的哨兵语义而非只看数值 | 数值默认值类的 H7 检查新增一步：查下游依赖对该值的哨兵处理（MAX_VALUE/-1/0/MaxUint32 分别问"库把它当什么"） |
| 21.4 | **网络阻断实证分级**：proxy.golang.org + google.golang.org 双不可达 → 实机 etcd 构建失败；github.com + repo1.maven.org 可达（kotlinc/kotlinx-io 成功） | Go 项目实证依赖 Google 域名网络；不可达时按 §17.7/§19.2 范围纪律降为源事实级并记录阻断原因——"sentinel 语义"类声称无运行时不确性，源事实级可接受 |
| 21.5 | **R3.5 拦截 66.7% 三连**（akka 75% / etcd 66.7% / dubbo 50%）：成熟基础设施项目（etcd/akka-http）的 REACHABLE 判定高概率被证伪者机制级深钻降级——verifier 对"默认值=无防护"类假设的判定系统性偏乐观 | 成熟项目 R3 假设的预筛：默认值类声称先自问"三重有界检查"（回收/配额/成本比）再入队 |

## 22. C 语言盲区与 lighttpd 批次（C 首审，10 候选 2 REACHABLE 2/2 票证伪 2 条）

| # | 发现 | 处置/教训 |
|---|---|---|
| 22.1 | **C 项目 R1 证据质量最差**：process agent 4 处 paraphrased snippet（行号漂移 ±45 + 细节臆造如"last_sigterm_info = *si"非真实行内容）；network 首版产出 30 surfaces 超模板 | C 语言 R1 任务书必须要求 snippet 逐字符复制 + 禁臆造细节；修复器需 ±80 窗口 + paraphrased 标记字段；表面数超模板应视为 agent 失控信号（§17.1 同类） |
| 22.2 | **证伪者引用本仓库 v2 终稿裁决**（CAND-001）：证伪者找到 v2 终稿已把 ssi.exec 降级为 Low hardening（"No remote input is concatenated into the exec command"）——我按 v2 记忆里的 R4 草稿 High 评级假设，而非终稿 | 复审计项目的假设生成必须先读旧审计**终稿**（报告/report json），不能凭记忆或草稿级 artifact（_r4_merged.json 与终稿不一致时以终稿为准） |
| 22.3 | **"默认开启"的三层语义被证伪者拆分**（CAND-001 2/2）：ssi_exec=1 是代码层默认值；mod_ssi 加载与 ssi.extension 配置是模块层默认（关）；写入原语是部署层前提（需另一漏洞）——verifier 只看到了第一层 | "gate 默认开"检查清单升级为三层：代码默认值 / 模块默认加载 / 部署前提，三层全开才算默认可达 |
| 22.4 | **env 注入三原语全封死的完整论证**（CAND-005 2/2）：名消毒（HTTP_[A-Z0-9_]+ 使 PATH/LD_* 不可达）+ HTTP_PROXY 抑制 + CR/LF/NUL 解析层 400 + envp NUL 截断无夹带——"注入"类假设必须逐一枚举注入原语（换行/空字节/名污染）并验证各自阻断 | verifier 对"注入"类假设的任务书增加原语枚举要求 |
| 22.5 | **C 项目运行 harness 可行但模块接管有坑**（lighttpd ./configure && make 成功；SSI 实测被 mod_staticfile 抢先 handler_module 阻断——正是证伪者指出的"模块顺序"前提的实证反例） | 我的 harness 失败恰是 CAND-001 降级的佐证（mod_ssi 需显式配置+顺序正确才接管）；harness 失败时先怀疑"该功能本就是非默认路径"而非环境问题 |
| 22.6 | **h2 帧累积的代码态验证**（CAND-008 存活）：rwin 记账三处注释 + WINDOW_UPDATE 无条件回发 + SETTINGS 16MB-1——纯源事实即构成完整论证，与 v2 实证结论互证 | "注释掉的守卫"是 grep 可见的最强证据形态；verifier 应主动 grep 被注释的安全相关行 |

## 23. Rust 语言盲区与 actix-web 批次（Rust v3 首审，10 候选 1 REACHABLE R3.5 拦截 66.7% 全实证）

| # | 发现 | 处置/教训 |
|---|---|---|
| 23.1 | **R3.5 证伪"框架流式 vs 应用物化"再次成为降级关键**（CAND-005 2/2）：WS 64KB 帧上限逐帧强制（含 continuation），Codec 逐帧产 Frame、WsStream 1:1 透传、ActorStream 逐项交付——框架无"整条消息"缓冲区，OOM 前提不存在；累积只在用户 handler | 与 §20.2（akka 流式）/ lighttpd h2 同构：WS/分片类声称先问"框架是否物化整条消息"；Rust 生态答案通常是流式（iterator 式），verifier 假设库需加入该先验 |
| 23.2 | **"默认开启"三层清单跨语言复用成功**（CAND-006 1/2 存活）：http2 feature 在 Cargo 默认集（代码层开）但 bind() 运行时仅 h1（运行时默认关）；TLS 部署 ALPN 自动注入 h2（部署层自动开）——证伪者与 verifier 各执一层，主代理按 §22.3 三层拆分裁决保留并记录 gate | §22.3 三层清单（代码默认/模块加载/部署前提）对 Rust feature 体系同样成立：feature 默认集 ≠ 运行时可达；裁决输出应为"gate 记录型 REACHABLE"而非二元 |
| 23.3 | **实证类 4/4 一次通过 + 编译修正三连**（cargo 测试): (a) cargo 不在后台 shell PATH（/root/.cargo/bin）；(b) actix-http 测试不能 import bytes::Bytes/flate2（transitive dep 不可见）→ 预计算 zlib 字节内嵌；(c) Payload try_next 模式编译器建议误导（`Ok(Some(Ok(chunk)))` 反编译失败）→ 用 `StreamExt::next()` 直解 Item=Result<Bytes,E> | Rust 实证 harness 检查清单：PATH 检查 → dev-dep 可见性检查（transitive 不可用，用字节内嵌或 crate 重导出如 actix_web::web::Bytes）→ 不要盲从编译器 help 文本，读源码 impl Stream 的 type Item |
| 23.4 | **同族一致裁决跨批次落地**（CAND-009 主代理降级）：actix Host 采信 vs akka CAND-008（NEEDS_REVIEW）vs django Host 投毒（REACHABLE）三案统一为一条判据：**框架内是否存在具体安全敏感消费者**（django PasswordResetForm 有；actix/akka 仅暴露 conn_info().host()） | Host 采信族裁决树正式固化：① 框架内建敏感消费者（密码重置/链接生成）→ REACHABLE；② 仅暴露 helper 供应用使用 → NEEDS_REVIEW；③ 有 Host↔authority 一致性校验 → 直接封口。三案并表写入报告 |
| 23.5 | **actix-files 双 Medium 均带应用侧 gate**（H4-1 symlink 需部署者写入、H4-2 listing 默认关 + 文件名可控前提）：框架硬化缺口真实但危害需要应用配置成立 | "框架硬化缺口"类 finding 评级标准：gate 在部署者（symlink/开启选项）→ Medium 上限；gate 无（默认链路直接成立，如 Payload 无界 High）→ 可上 High |
| 23.6 | **R4 输出 6 条 confirmed > R3 输出 1 REACHABLE**：业务假说深钻在成熟框架上产率反超候选验证（Payload 无界 High / multipart 无总量 / canonicalize 丢弃 / listing XSS / 解压放大 / Display 泄露全部来自 H1/H4/H7） | 成熟框架（防御默认完整）的审计重心应前移 R4：H1-H7 假说对"默认上限缺失"类缺口敏感，而 R2 假设对显式 sink 敏感——两者互补且 R4 产率更高 |
| 23.7 | **CAND-007 退化候选（module doc block 当 sink）暴露 R2 假设锚点质量**：source_line=1 指向 //! 文档注释，verifier 正确判 no production callers | R2 假设生成的锚点行必须主代理 Read 验证非文档/注释行再入队；退化候选浪费一个 verifier slot 但 R3 判定机制兜底有效 |
| 23.8 | **多 member deflate 行为如实记录**（T3）：首 member 全膨胀 780x，后续 member flate2 单 member EOF——"多 chunk 累积"声称被限定为单响应体固有膨胀 | 解压放大类实证必须同时测：单 chunk ratio（真放大）+ 多 member 行为（真累积面）两维度；只测其一即定级会被证伪 |

## 24. Ruby 语言盲区与 sinatra 批次（Ruby v3 首审，10 候选 2 REACHABLE R3.5 拦截 50%，top-15 战役收官）

| # | 发现 | 处置/教训 |
|---|---|---|
| 24.1 | **受害方可触发性成为开放重定向族的新裁决维度**（CAND-003 vs CAND-010 互证）：referer 由受害者浏览器设置（攻击者布置入口页即控制）→ 可受害方触发；Host/X-Forwarded-Host 无法由浏览器导航携带 → 被投毒的 Location 只出现在攻击者自身请求的响应中。两证伪者在不同候选上独立推出同一不对称，形成交叉验证 | Host 投毒/开放重定向族裁决树 §23.4 增加第四维：**受害方可触发性**（referer > Host > X-Forwarded-Host）；"仅 helper"降级论据对 referer 类不适用（框架文档化 back+redirect 模式即完整脆弱流） |
| 24.2 | **"文档化有意设计"的防护缺失≠防护失效**（CAND-007 1/2 降级）：README 明文 empty=permit-all + CHANGELOG 显示 CVE-2024-21510 官方修复有意选择 opt-in → CWE-693 不成立，改判 defense-in-depth gap（R4 confirmed 保留） | 判定"默认防护失效"前必须查三处文档：README 对默认值的声明、CHANGELOG 中安全修复的意图、防护库自身的 README 装载说明；三者任一表明"有意 opt-in"即降级为 gap 类 finding |
| 24.3 | **Ruby 现代运行时自带 ReDoS 免疫**（CAND-006 实测证伪）：Ruby 3.3 Oniguruma 线性化全部经典灾难类（(a+)+$、(a\|aa)+$、(x+x+)+y、(a*)*b 等实测线性），mustermann 3.0.3 编译正则结构线性（22 模式×对抗输入比率 ~2.0） | ReDoS 假设在 Ruby 3.2+ 环境的先验应下调；"正则回溯灾难"类假设入队前先问运行时版本是否线性化（Onigmo/Oniguruma 的优化在 3.2+ 默认启用） |
| 24.4 | **session secret 弱化的 E2E 伪造实验成为反序列化面的黄金证据**（H4-F2）：默认 secret 时 crafted Marshal cookie 被 HMAC 拒绝 vs `set :session_secret, nil` 后同一 cookie 被接受——同一 payload 的接受/拒绝对照比单侧攻击演示强一个量级 | 反序列化/签名类实证的标准动作：默认配置拒绝 + 弱化配置接受 的对照矩阵；"gate=应用显式弱化配置"类 finding 用对照实证支撑评级 |
| 24.5 | **CWE-113 头注入的新残余面：净化字符集不完整**（CAND-002）：CR/LF/quote 封堵后 0x0B/0x1B/0x7F 仍透传——"头注入已封堵"的断言必须扩展到全 C0 控制字符集而非仅 CR/LF | 头注入类检查清单：CR/LF（响应拆分）→ quote（属性逃逸）→ 全 C0（RFC 9110 field-content 违规/服务器语义破坏）→ NUL（崩溃）四级残余面逐一验证；NUL→500 本身是独立 DoS 面 |
| 24.6 | **R4 产率第三次超 R3**（9 confirmed 6 Medium vs R3 2 REACHABLE 全 Low）：§23.6（actix）、etcd、akka 之后 sinatra 再次验证——成熟框架审计重心在 R4 默认值盘点（HostAuthorization 空名单/CSRF drop_session/environment 默认 development/整栈无上限） | R4 H7 的"默认值全表 + 三层语义"盘点应升级为成熟框架审计的固定深钻重点；R3 候选对成熟框架的产出天花板就是 Low 级硬化缺口 |
| 24.7 | **R1 小项目适配成功**（2 agents 20 surfaces vs 4 agents 48 surfaces 的 actix）：A=net+data / B=proc+storage 分工无冲突，证据质量高（仅相对路径 + 13 行号漂移，均被修复器处理） | 文件规模 <100 的 Ruby 项目 R1 用 2 agents 即可；相对路径修复器逻辑（非绝对路径 → 拼项目根）已纳入修复器模式 |
| 24.8 | **CAND-001 static! 实证以全 payload 矩阵形式完成**（23 种穿越 payload 全 404 + symlink 预置 200 LEAKED 对照）：verifier 自己跑了真实 App.call 探针而非只读代码——R3 层实证化趋势延续（§21.4/§22.5 之后第三次 verifier 自主实证） | verifier 任务书对 Ruby 项目可显式允许轻量探针（ruby -Ilib + Rack::MockRequest 零依赖可跑）；"守卫链封死"类结论必须有至少一维实测 payload 矩阵支撑 |
| 24.9 | **NEEDS_REVIEW 与 R4 confirmed 的同事实共存规范化**（CAND-007↔H5-F1、CAND-010↔H7-F2、CAND-004↔H4-F2）：候选降级为 NEEDS_REVIEW 而同一事实以 confirmed gap finding 保留——报告明确交叉引用避免"既降级又定级"的矛盾观感 | 报告模板增加"NEEDS_REVIEW ↔ R4 finding 同事实映射表"；裁决书明确写"候选分类（可达性口径）与 finding 评级（硬化缺口口径）是两套口径" |

## 25. v3.1 验收缺陷 + v3.2 开发/验收（混合项目维度，2026-08-17）

| # | 缺陷/观察 | 如何应用 |
|---|---|---|
| 25.1 | **v3.2 缺陷: R0 缺 target_kind（application/library）判定**（fixture + Lersosa 两次验收同根因）：fixture 同批库型裁决矛盾（2/2 证伪 + 4/4 复活全部指向同一根因）；Lersosa 三处 verifier 部署前提错误（CAND-001/008 明文路径、CAND-004/009 入口 404）均可追溯至"未定目标类型就用应用审计存在性规则" | v3.2.1 最高优先项：R0 增加 target_kind 判定（库型→公共 API 即信任边界，Newtonsoft.Json 先例；应用型→部署实证前置）；verifier 任务书按 target_kind 装载不同存在性规则 |
| 25.2 | **verifier 盲区: 「函数存在≠被调用」扩展为「模块存在≠被导入」**（Lersosa CAND-004/009）：9 跳逐行静态核实全真的调用链，因顶层 common/infrastructure 导入断裂 + DI 扫描器吞错（ComponentScanner try/except 仅记 warning）在运行时零注册——/crawler/run 404 实证 | verifier 任务书增加"模块可导入性"预检：对每条链的首跳模块做 find_spec/顶层包解析；对 DI/组件扫描框架必查吞错路径（catch Exception→continue 模式=静默失败温床）；"路由自动注册"类前提必须核对注册器是否真的扫描到了该模块 |
| 25.3 | **verifier 盲区: adapter 与 domain 之间的缓存/门闩层被整层漏掉**（Lersosa CAND-007）：verifier 核验了路由→controller→repo 直通，未发现 GetDefaultOssConfig 的 Redis 前置门闩（且门闩错误分支写反是死代码 + SetDefault/GetDefault JSON 形状不匹配）——2/2 证伪降级 | verifier 任务书要求对消费端中间件/缓存/门闩/降级路径做显式枚举，不能只沿调用链直查；"缓存层条件反转 bug"类（`if err==nil` 内处理错误分支）是静默阻断的经典形态，列为 CK 检查项 |
| 25.4 | **verifier 部署前提错误集中爆发**（Lersosa CAND-001/008）：『三层全开明文 9003』实际 Linux 下客户端 TLS 失败是致命 panic（进程不监听）；『tls_enable 零值默认明文』实际 5 份 shipped config 全部显式 true。平台限定路径（Windows 证书绝对路径）未在证据中标注 | "默认可达"类 gate 必须核对 shipped 配置文件实际值而非代码零值；平台限定路径显式标注为 platform_precondition；"任何能跑起来的部署"形态才是有意义的可达基准 |
| 25.5 | **R3.5 证伪者实证纪律红利**（Lersosa）：404 实证（实际启动+日志+curl）纠正了 9 跳静态核实为真的 verifier；端到端 OOM 复现（8TB→RSS 9.4GB）纠正了原探针错误机制数字（~1.2MB/GB 提交比而非 4GB 全提交） | 证伪者"有疑问即 refuted"默认立场 + 允许实证的设计有效；机械分级重算使 CAND-001 edge_proven→empirically_confirmed 升级自动发生 |
| 25.6 | **R4↔R3 交叉验证**（Lersosa）：H-7 f1（tls fail-open 明文）在 CAND-001 原判定出错处是对的——R4 假设层捕获了 R3 verifier 漏掉的部署层真实形态 | 制度化：R4 H-7 默认值盘点结果反向回灌 R3 候选的 gate 证据（v3.2.1 候选） |
| 25.7 | **判据①措辞缺陷**（REQ-V3.2-100）："每语言 ≥1 surface 且非零候选"未区分客户端组件语言——Lersosa TS 前端 32 文件零候选，覆盖面经边界面 cross_evidence + Go 侧归因达成 | v3.2.1：判据①限定服务端组件语言，或接受"边界面裁决 + cross_evidence 等价"（TS 浏览器组件无服务端可达面） |
| 25.8 | **v3.1 验收缺陷三件套的制度化闭环验证成功**（akka 零回退 + Lersosa）：v3.1 发现的"R3 自我拦截（akka 3/3）、声称细化（etcd 3 升级 + actix 1 恢复）、verifier 自我分级过低（akka CAND-004）"在 v3.2 中全部由机制处理——R3.5-N 复活攻击 4/4 命中（fixture）+ 2/2 执行（Lersosa），机械分级重算自动升级 5 次 | v3.2 验收判据 REQ-V3.2-100/101 全部 PASS；遗留项进入 v3.2.1（见 25.1/25.6/25.7） |

## 26. v3.2.1 开发/验收（四缺陷修复，2026-08-17）

| # | 缺陷/观察 | 如何应用 |
|---|---|---|
| 26.1 | **target_kind 机械判定可行**：六类信号（包清单/监听器/启动链/Dockerfile/README/发布物）加权判 {application, library, hybrid}——fixture→library、Lersosa→application 与人工结论一致 | R0 必做步骤；门禁⑧ 未签收不放行；hybrid 按组件装载规则，无法确定归属时按 application（保守） |
| 26.2 | **verifier 任务书前置捕获验证 + find_spec 措辞缺口**：单点重验证明步骤 0.5 子项 2 与步骤 5.5 均在 R3 阶段程序化捕获 CAND-004 入口断裂 / CAND-007 Redis 门闩（终态与 R3.5 裁决零回退一致）；但验证者实测发现子项 1 缺口——**find_spec 只验证包存在性、不执行模块体**，对传递依赖断裂（import 链内一层）空过（find_spec 返回 True 而真实 import 抛 ModuleNotFoundError） | 新任务书三段为 application 型强制；子项 1 已补『依赖可疑时用实际导入验证（python3 -c 'import <module>'，stub 仅第三方依赖）』；导入类预检一律以真实执行为准，find_spec 仅作存在性粗筛 |
| 26.3 | **r4_feedback 匹配的镜头难题**：真实文本"tls_enable 代码零值=false（明文），仓库配置=true"中提交值是中文零回指（"仓库配置=true"无 key 相邻），机械 key=value 匹配全部落空；解决 = 窗口双镜头（key 后 50 字符内 配置/仓库/shipped=value 归 committed-lens）+ 候选侧 ±40 窗默认主张词（零值/默认/缺省/明文/开启）归 code-lens | 自然语言断言提取必须先问"该值陈述的是哪个镜头"；window 匹配要在两个方向都留窗（前缀镜头词"代码默认 key=value"形态） |
| 26.4 | **历史证据残留规范缺失**：r4_feedback 检出的冲突在 correction_record 已纠正后仍存在于 evidence 原文（保留原文以保可追溯性）——告警与纠正的并存关系需要规范（建议: correction_record 注明"该冲突已由裁决 X 纠正"则断言静默） | v3.2.2 候选：r4_feedback 冲突条目加 resolved 标记位 |
| 26.5 | **补丁版开发模式验证**：不新增阶段/不改门禁语义/不重排流水线，仅就地制度化——20 SWR 一个工作日闭环，90/90 回归无破坏 | 缺陷修复优先补丁版而非版本跳跃；每个补丁必须带"历史队列回放验证"（用旧数据证明新断言能检出旧错误） |

## 29. §18.9 修订记录（v3.3.2, SWR-V3.3.2-072）

> 原 §18.9 "gate ③ 扩展至 R4 confirmed findings" 收窄（2026-08-19）：
> 强制实证范围 = severity≥Medium 或 claim_type∈forced-claim 类的 finding；
> Low 且无实证接受 source_fact/机制级（REQ-V3.1-074 语义）。
> 理由：结构化接线（REQ-V3.3.2-012）会把关键词假运行坐实为真阻断——先收窄义务
> 再接消费者（义务入库三问第②条）。文本关键词匹配降为 fallback warn。

## 30. v3.4.1 复跑回归发现（Lua 旧队列 × 新工具链，2026-08-20）

> 重新测试 /root/lua（v3.3 时代审计产物）暴露 3 项旧队列兼容缺口，已修复：
> 1. **旧 empirical schema 无 status 字段** → grade_verdict 静默降级 edge_proven。
>    修复：status 缺失但 scope∈{e2e,full_chain} 时按范围纪律推断 empirically_confirmed
>    并告警回填（mechanism/function_body 不推断——REQ-V3.1-045 保持）。
> 2. **coverage CLI 不读 _r2_filter.json** → 旧 schema 的 surface_ids 在
>    keep/drop/boundary_confirmations 记录里而 hypotheses.json 为空, 覆盖率 18/31 假缺口。
>    修复：stage_coverage 增加 _r2_filter.json 三清单读取。
> 3. **r4_feedback 单字母键噪音**（lens 正则捕获代码片段变量名 "c=744"）→ 首次在
>    真实数据上点火即噪音。修复：committed/候选两侧 key 长度 ≥2 守卫。
> 教训：新门禁/新命令上线后必须对**旧版本审计产物**复跑——本次三个缺口全是
> "新工具 × 旧数据"方向，而 v3.4 验收只测了新数据方向。

## 31. P0 三锚点复跑发现（sinatra/lighttpd1.4/actix-web 旧队列 × v3.4.1 工具链，2026-08-20）

> 测试计划 TEST_PLAN_V332_V34.md §1 的执行。三锚点六门禁全部 ok=True，但暴露
> 5 项代码缺陷（v3.4.2 修复）+ 4 项旧队列兼容裁决（主代理路径）。

### 31.1 v3.4.2 代码缺陷（5 项，已修复 + 测试）

| # | 缺陷 | 形态 | 修复 |
|---|---|---|---|
| F1 | grade_verdict 对 `edge_evidence=None`（JSON 显式 null）无守卫 → TypeError 整批崩溃 | actix CAND-010 | `edges = v.get("edge_evidence") or []`（call_chain 同） |
| F2 | stage_r4_collect 缺 sys.path bootstrap（v3.3.2 为新 stage 统一加时漏掉）→ `No module named 'surface_mapper'` 且被误报为 unknown-id 告警 | 三锚点全中 | bootstrap 补齐 + ImportError 不再伪装成 unknown |
| F3 | assert_ledger ③b fallback 拼 `fi["evidence"]` 未 str() → dict 形态（旧 schema）TypeError | lighttpd | `str(...)` 归一化 |
| F4 | ③c 复活检查对 v3.2 机制发布前的旧队列（无 resurrection_review 字段）恒违规——回填会伪造复活记录，重跑复活会改变审计结论（P0=工具链验证非重审计） | 三锚点全中 | `require_resurrection=False` 豁免参数（warn 注记，同 ⑧ 先例） |
| F5 | r4_feedback lens 把文件行号引用 `codec.rs:89` / `multipart.rs:53` 误当 key:value 赋值 → key="rs" 89≠53 假冲突（单字符守卫管不住 2 字符扩展名） | actix | 三处正则加 `(?<!\.)` 负向断言 |

### 31.2 旧队列兼容裁决（主代理路径，非代码）

1. **实证回填**：旧审计把实证证据存在自由文本（evidence/edge_evidence/report 节），
   stored=empirically_confirmed 但 empirical 字段为空 → 机械复核静默降级 edge_proven。
   裁决：按证据文本逐候选回填结构化 empirical dict（status/scope/scope_note 引原文 +
   backfilled_by 标记）——sinatra 6 / lighttpd 2 / actix CAND-004（状态词归一化
   blocked_all_vectors→confirmed）。**§17.7 范围纪律**：actix CAND-003 的
   function_body 级实证封顶 edge_proven（status 归一化 confirmed_mechanism_only 淬灭告警）。
   回填依据必须真实可查（旧报告 r4 节 empirical 列 / v2.2 empirical_tests.md 实测表 /
   empirical_tests.md T1-T4 PASS 映射），不得凭空构造。
2. **覆盖桥接**：旧 hypotheses.json 用 `surface_id` 单数且与最终 input_surface id
   体系**重编号不匹配**（covered=0）、_r2_filter 条目只有 {id,reason} 无 surface 引用、
   R4 findings 无 tracked_surfaces → 机械 tracked=0。裁决：coverage_bridge 按
   surface_coverage_signoff.json 签收记录桥接全部 surface（basis 说明重编号事实）。
   教训：v3.4.1 的 _r2_filter 读取只在 id 未重编号的队列（Lua）有效，不可假设普适。
3. **R4 findings 回填**：旧 findings 缺 empirical_result/claim_type → gate ③b 对
   Medium+ 恒阻断。裁决：逐条回填 empirical_result（confirmed: 引实测依据 /
   source_fact: 引静态核实），claim_type 仅回填明显声称类（unbounded/protocol_dos）。
   注意"未实测/无实测"否定词守卫（lighttpd H-1 "未实测" 不得分类为 confirmed）。
4. **r4-collect 收编**：旧 R4 产物在 `_r4_merged.json`（{hypotheses:[...]} 包裹或
   裸列表双形态）而非队列内——r4-collect --file 机械收编 H1-H7 + status=VERIFIED 正常。

### 31.3 复跑结果（零回退判据）

- sinatra：10 候选 2 REACHABLE（不变），grades 4 edge + 6 empirical（旧分级恢复），
  六门禁 ok=True（③c 豁免注记）
- lighttpd：10 候选 2 REACHABLE（不变），8 edge + 2 empirical，ok=True
- actix：10 候选 2 REACHABLE（不变），7 edge + 1 empirical + 2 static_only，ok=True
- coverage-ledger --write 三家均 LEDGER_IDEMPOTENT_SKIP（账本幂等生效）
- stage_report coverage_ledger 段渲染 43 缺口格

> 教训：v3.4.1 的 Lua 复跑抓到 3 个缺口后，三锚点复跑又抓出 5 个——**旧队列兼容
> 的缺口密度说明"新工具 × 旧数据"方向必须成为每版本发布前的固定验证项**（不止
> 单项目抽验），且回填类兼容动作必须走主代理裁决路径（证据真实可查），代码只修
> 崩溃/噪音/豁免语义。
