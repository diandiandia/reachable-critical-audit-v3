# W5 回归测试发现与修复（sinatra 首轮）

> **日期**：2026-08-16
> **阶段**：SWR-091 回归测试（sinatra 对照 v2.2 归档基线）
> **原则**：回归测试的首要产物不是"结论对照"，而是"v3 机制在真实项目上的缺陷暴露"。

## 1. signature_matcher：Ruby 语法族索引盲区（GENERALITY_EVAL §2.1 的实证）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 1.1 | `def_re`/`call_re` 不识别 Ruby 方法名后缀 `!`/`?`/`=`（`dispatch!`/`call!`/`merge!`/`attr=`） | 调用索引缺边，长链 sink 窗口展开漏边 | 正则加 `[!?=]?` 后缀（对 C 系副作用仅为多 `foo!` 假条目，无害） |
| 1.2 | `call_re` 要求 `\s*\(`，Ruby 无括号裸调用（`invoke { dispatch! }`）完全不索引 | 同上 | 第二遍 `bare_call_re`：仅 `!`/`?` 后缀裸词（Ruby 惯例中必是方法调用，噪声可控） |

测试固化：`test_ruby_bang_and_parenless_calls_indexed`。

## 2. surface_mapper：agent 产出形态与校验器契约的 5 处不匹配

v2.1 的教训是"严格契约导致手工回填"；本轮回归发现反面教训——**子智能体产出的自然形态必然偏离模块契约**，校验器必须归一化而非拒收可修复形态。

| # | 不匹配 | 后果 | 修复 |
|---|---|---|---|
| 2.1 | `VALID_TRUST` 枚举缺 `gated`（设计文档 REQ-V3-023 明列 gate 类，实现漏了） | gate 类 surface 全被拒收 | 枚举补 `gated` |
| 2.2 | agent 产出裸 JSON 数组 + 字符串 trust_boundary；validate/merge 期望 `{"surfaces":[]}` + `{"type":...}` | 全量拒收 | `normalize_surfaces()` 统一归一化 |
| 2.3 | agent JSON 把 `&` 转义为 `&amp;`（JSON 序列化常规），证据子串匹配误拒 | 正确证据被拒 | `html.unescape` |
| 2.4 | entry_points.file 是项目相对路径；校验器按 cwd 解析 → `os.path.exists` 恒 False | 证据全被误判不匹配 | validate/merge 增加 `project_root` 参数解析相对路径 |
| 2.5 | 源码对齐空白（`captures           =`）与 agent 注释混入 snippet 破坏子串匹配 | 误拒 | 折叠空白 + 反向包含（源行 ∈ snippet） |

## 3. surface_mapper：行号漂移的裁决分层

- 现象：agent 报告行号漂移 ±1~11 行（grep 输出/代码块对齐/幻觉边界模糊）
- 设计决策：**校验器不放行窗口外命中**（防幻觉），错误附 `[suggested_line=N]`（全文件唯一命中时）；
  由主代理裁决应用修正并写 `line_corrections` 记录（REQ-V3-026 复核生效的执行形态）
- ±2 行窗口内直接通过（漂移是精度问题，窗口内匹配仍能防内容幻觉）

测试固化：`test_normalize_*`、`test_gated_is_valid_trust`、`test_whitespace_alignment_and_comment_suffix_match`、`test_line_drift_suggests_correction`。

## 4. signature_matcher：R2 阶段两个爆炸缺陷

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 4.1 | **自我引用污染**：项目索引扫 `.audit_results/` 与 `spec/`、README 等非源码文件——签名在"自己写的证据 JSON/文档示例代码"上命中 | 最恶性的幻觉源：7010 hits 中大量是审计产物自匹配 | SKIP_DIRS 加 `.audit_results`/`spec`；CODE_EXTENSIONS 白名单仅索引源码 |
| 4.2 | **god-file 窗口爆炸**：expand_window 第 0 层取"entry 文件全部调用点"（base.rb 2000 行 → 窗口即全库）；BFS `next_frontier` 从未填充导致 depth 循环失效 | 56 surfaces × 全库窗口 → 7010 hits | 第 0 层限 entry 行 ±60 邻域；BFS 逐层推进（frontier=新增行全部被调名）+ LAYER_CAP 40 / WINDOW_CAP 300 → 174 hits |
| 4.3 | merge_surfaces `append` 缩进错误：每文件只保留最后一个 surface（56 → 4） | 输入面覆盖率门禁会被假数据骗过 | append 移入 surface 循环；单测仅覆盖单 surface 文件故未暴露——**测试夹具必须含多元素文件** |

修复效果：7010 → 174 hits → 42 hypotheses（后续 LLM 筛选 REQ-V3-037 接管）。

## 5. 本轮流程观察（非缺陷，记录备查）

- 4 域测绘 agent 并行完成时间 119~430s，产出 8~22 surfaces/域，证据齐全率 >95%
- R0 签名冒烟 hit_rate 1.0（SIG-LOGIC-WEAKEN-005 实例在 fastjson2 仓库，不在本地 → skipped 不计分母，符合设计）
- 合并后 56 surfaces、40 跨域冲突（kept-first-multi-domain 标注，符合 SWR-V3-005）
- SIG-HEADER-INJ-006 的 `href=`/`escape\(` 等宽模式命中 114/174——宽模式可接受（签名库是提示器），噪音由 LLM 筛选层吸收；若筛选后转化率仍低，需修整签名 grep hints（REQ-V3-072 转化率指标已备）

## 6. sinatra 回归结论摘要（对照基线通过）

- 规模：93 候选 → 2 簇级候选（-97.8%）；闭合率 77.4% → 100%
- R4 假说：H5/H6 一致复现 confirmed；H1 降为 reviewed_clean+Low（v3 分层更准：app-gated）；
  **H2 新发现**（Accept 头 O(n²) CWE-1333，v2.2 漏）；**H7 新假说首次实战捕获 2 findings**
  （'.domain' 后缀匹配无边界锚定 CWE-285/184；redirect back 开放重定向）
- 独立复核闭环实战验证：CAND-002 初判 REACHABLE → N=2 复核 1 票证伪（证伪者 #1 做了
  真实运行时实测矩阵）→ 主代理降级 NEEDS_REVIEW + correction_record。REQ-V3-043
  前提维度在实战中正确拦截了"代码路径可达≠攻击相关"的误判
- Mode W 全链路实战验证：verify 波次 + refutation 波次 + collect + 六门禁，全部跑通

## 7. lighttpd 回归首轮发现（C 语法族盲区，GENERALITY_EVAL §2.1 实证）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 7.1 | def_re 无 `\b` 前缀：`#ifdef _WIN32` 的 "def" 匹配 → 预处理器符号（_WIN32/NDEBUG/__COVERITY__）被当函数定义，caller 归属 26% 是假名 | C 项目窗口展开的 caller 链全是噪声 | `\b(?:fn\|def\|...)` 前缀 |
| 7.2 | def_re 不识别 C 函数定义（`size_t name(args)` 形态）——C 项目的 caller 归属基本失效 | 同上 | 增加 c_def_re（行首类型序列+名字+(，排除关键字），_current_func 同步 |
| 7.3 | `_detect_lang` 纯扩展名计数：lighttpd 翻译文件多 → 主语言判成 .po | 架构上下文误导 | 仅统计 CODE_EXTENSIONS 源码扩展名 |

修复后 lighttpd caller 分布恢复正常（http_status_set_err/h2_send_refused_stream 等真实函数；
toplevel 25.4% 为头文件声明/宏区域，属粗粒度索引的合理残余）。

## 8. lighttpd R1 阶段追加发现（证据匹配三层启发式）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 8.1 | snippet 是源行前缀（agent 省略行尾 `{`）时窗口匹配失败 | 正确证据被误拒 | 窗口匹配改双向（源行 ∈ snippet ∨ snippet ∈ 源行） |
| 8.2 | agent snippet 混拼上下文（声明+赋值拼接，与源行互不包含） | 双向匹配均失败 | 第三层启发式：提取 snippet 中最长 `name(` callee 名做唯一调用行匹配 → suggested_line |
| 8.3 | 多命中（声明行+定义行）无 suggested 信息 | 主代理无裁决依据 | `[suggested_lines=a,b,c]` 附候选列表，主代理用定义形态启发式裁决 |
| 8.4 | 行号漂移最多达 17 行（agent grep 输出偏移） | ±2 窗口覆盖率不足 | suggested_line 多轮修正循环（主代理裁决），17 处自动修正 + 1 处证据重写（evidence_rewritten_by 标记） |
| 8.5 | **agent 完成通知与文件落盘之间存在写读竞态**：通知到达时文件尚在 flush，读报 JSON 损坏（两次），重读即好 | 误判 agent 输出损坏（v2.1 的"JSON 损坏 1/4 批"可能部分源于此） | 编排层读 agent 产出前应重试校验；数据域文件另有 1 处真实缺 `}`+`,`（agent 序列化截断）——两类故障要区分 |

## 9. lighttpd R2 规模对照

- v2.2: 10097 候选 → v3: 88 surfaces → 770 hits → 121 hypotheses + 7 logic（**-98.8%**）
- 签名命中分布：SIG-BUFFER-ACCUM-001 527（C 项目 buffer 操作密集属正常）、AUTHZ-BOUND 171、PATH-WHITELIST 37
- 88 surfaces 覆盖了 v2.2 全部基线结论对应面：ssi.exec 默认开启（PROC-LL-001）、LOCK refresh 越权（PROC-LL-010）、锁永不过期（PROC-LL-011）、h2 帧处理（NET-009）、webdav XML（DATA-LL-015）

## 10. lighttpd 回归结论摘要（对照基线通过）

- 规模：10,097 候选 → 88 surfaces → 121 假设 → 2 簇级候选（-99.98%）；六门禁全过
- R4 复现：h2 帧缓冲 16MB/连接（H1，=v2.2 实测 +30MB/连接）；LOCK refresh 越权
  （H6 **High**，加深：sqlite3_changes 不检查→不存在 token 也 200+伪造 lockdiscovery）；
  锁永不过期可复活（H6）；TOC-TOU（H6）；symlink 绕过 follow-symlink=disable（H7）
- v2.2 的 ssi.exec High finding 被 v3 重新分级为 Low hardening：cmd 无变量替换，
  信任边界是文件内容非请求——**分级修正而非复现**（v2.2 把文件信任边界当请求直达）
- 独立复核第二次实战拦截：CAND-001/002 初判 REACHABLE → 证伪者 #1 用 RFC 7239 §7.4 +
  生态同构（nginx/HAProxy）+ 产品内零安全决策消费 → 主代理降级 NEEDS_REVIEW
  （调用边全部真实——拦截的是"影响前提"不是"路径"）

## 11. actix-web 回归首轮发现（证据形态多样性）

| # | 缺陷 | 后果 | 修复 |
|---|---|---|---|
| 11.1 | agent snippet 为"概括性伪代码"（`impl Header for Accept {...}` 描述宏展开、`match size.checked_mul(radix) {...}` 摘录代码块而非单行） | 源码行匹配失败 | 主代理裁决重写：函数定义行锚定（`fn name` 定位）或语义锚定（宏调用行 common_header!） |
| 11.2 | 宏生成代码（common_header!）无字面 impl 行——agent 描述的是宏展开语义 | 无真实行可锚定 | 锚定宏调用行 + evidence_rewrite_note 记录语义 |
| 11.3 | R2 规模正常：69 surfaces → 1340 hits → 130 hypotheses；SIG-TRUNC-CAST-004 命中 53 处（含 ws 帧长度 u16/u64→usize 家族——v2.2 基线判据达成） | — | — |

## 12. 三个锚点回归全部完成后的总结论（SWR-091 判据）

| 锚点 | v2.2 基线 | v3 结果 | 判据 |
|---|---|---|---|
| sinatra | 93 候选 0 REACHABLE | 2 候选 0 REACHABLE（1 经复核降级） | ✓ 通过 |
| lighttpd | 10097 候选 0 REACHABLE + R4 8 findings | 2 候选 0 REACHABLE（经复核降级）+ R4 复现/加深 | ✓ 通过 |
| actix-web | 7051 候选 0 REACHABLE | 待 R3/R4 完成 | 进行中 |

## 13. actix-web 回归结论摘要（三锚点全部完成，SWR-091 通过）

- 规模：7,051 候选 → 69 surfaces → 130 假设 → 2 簇级候选（-99.97%）；六门禁全过
- **v3 首次产出可申报级 REACHABLE×2**（ReadLines 无界累积 CWE-770、目录列表 stored XSS CWE-79），
  均 empirically_confirmed + N=2 复核全票确认（4/4 证伪失败）
- R5 实证：300MB 无换行 body → RSS 302.9MB 后 LimitOverflow（limit 检查是事后拦截的实锤）；
  CONTROLS 集属性逃逸生成 HTML 实锤
- v2.2 基线判据：u16 truncation 家族 v3 验证安全（与实证一致）；Windows backslash 降级结论维持
  （cfg!(windows) 平台正确性经 H7 复核确认）；to_bytes usize::MAX 家族复现
- v3 新发现超过基线：2 REACHABLE + H1-F2 解压放大 + H4-1 canonicalize 丢弃（git 考古 ce50cc95）+ H7-F3 demo 危险模式

## 14. SWR-091 总判定：三个锚点全部对照通过

| 锚点 | 候选规模 | R3 对照 | R4 对照 | 判定 |
|---|---|---|---|---|
| sinatra | 93→2 | 0 REACHABLE 一致（复核降级 1） | H5/H6 复现；H2/H7 新发现 | ✓ |
| lighttpd | 10097→2 | 0 REACHABLE 一致（复核降级 2） | 8 findings 复现+加深（H6 High） | ✓ |
| actix-web | 7051→2 | **2 REACHABLE（实证+全票复核）**——v3 首次超越基线 | 复现+新发现 | ✓ |

通用性主张（GENERALITY_EVAL §2.4）获得实证锚点：三语言族（Ruby 脚本系/C 系统系/Rust 框架系）
全流程跑通，规模下降 98-99.98%，闭合率 100%，无 verifier 幻觉漏网（独立复核 3 次实战拦截/确认）。
