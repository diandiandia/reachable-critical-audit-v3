# Reachable Critical Audit Skill — Swift/Vapor 审计暴露的缺陷与改进建议

> **文档性质**：基于 Vapor 5.0.0-alpha.2 (c6818be2) 真实审计（R0~R4 全流程 + 3 候选实证抽验）对
> `reachable-critical-audit` skill v2.1 的回顾性缺陷分析。驱动 skill v2.2 设计，非项目审计报告。
>
> **审计日期**：2026-08-15
> **关联审计归档**：`/root/vapor/.audit_results/`（report、verify_queue、empirical/EMPIRICAL_REPORT.md、cve_draft.md）
> **交叉引用**：[SKILL_LESSONS_SWIFT_GO.md](SKILL_LESSONS_SWIFT_GO.md)（L0 Swift 盲区的先例）、[SKILL_LESSONS_C.md](SKILL_LESSONS_C.md)（工具链同源缺陷）、[SKILL_LESSONS_JAVA_dubbo.md](SKILL_LESSONS_JAVA_dubbo.md)（受信边界假设）

---

## 0. 量化背景

| 指标 | 值 | 说明 |
|---|---|---|
| 总候选 | 29（L0=0 / L1=25 / R05=4 / R4 假说=6） | L0 静态规则**零命中** |
| Sink Discovery Rate | **0%** | L0 规则库对 swift-server 生态完全盲区 |
| False Negative Risk | 86.2% | 纯 L0 审计将漏掉全部 4 个漏洞家族 |
| 验证规模 | 15 verifier，29/29 VERIFIED，avg call_chain_depth 6.66 | 流程机械指标全部达标 |
| 实证抽验 | 3 候选 → 2 CONFIRMED，**1 REFUTED** | 33% 误判率（小样本）暴露验证质量问题 |
| 用户复核纠偏 | 1 次（H1 平台判定） | 见缺陷 #4 |

**本次审计的三个关键事件**：
1. L0 全盲 → 全部发现依赖 R1.5 手工增强的 extractor（规则库缺口）
2. R4 verifier 断言"空 body 崩溃"→ 实证证伪，`checkBodyStorage()` 是死代码（调用边幻觉）
3. R3 判定 FileMiddleware Windows 穿越 REACHABLE → 用户指出 Vapor 5 不支持 Windows（平台维度缺失）

---

## 1. P0 缺陷（规则库/验证方法论级）

### 1.1 L0 Swift 规则对 swift-server 生态全盲（Sink Discovery Rate 0%）

**现象**：`security_profiles.json` 的 `rules.swift` 段 49 条 CWE-22 regex + `swift_models[]`
全部来自 CodeQL Swift `PathInjectionExtensions.qll`——**Apple Foundation 平台 API**
（`Data(contentsOf:)`、`NSFileManager.contentsOfDirectory` 等）。Vapor 使用 `_NIOFileSystem`
（`FileSystem.shared.info(forFileAt:)/withFileHandle/readChunks`）、NIOHTTPServer、
`ByteBufferAllocator`。197 个 Swift 源文件 **0 命中**，`ast_scanner.py` 的 regex 兜底同样无命中。

**根因**：
- CodeQL 官方 Swift 模型面向 Apple SDK 应用开发，不覆盖 swift-server 服务端栈（NIO、
  swift-http-server、FileSystem 模块、body collect 语义）
- `wrapper_detection.swift` 仅含 `ipc_sinks`（URLSession.dataTask/Process.run）与
  `db_wrappers`（sqlite3_exec/NSPredicate）——服务端框架的真实 sink 家族（文件流、请求体
  收集、响应序列化、重定向/cookie 写入、模板渲染）全部缺失（见 3.1）
- self-check 的"AST pattern 覆盖率"度量的是模式字符串存在性，不是对目标生态的召回能力

**证据**：本次 4 个 REACHABLE 家族（服务器预收集无上限、FileMiddleware 拼接、URLEncodedForm
解析、Multipart 边界）无一条来自 L0。

**改进建议**（v2.2）：
1. `sinks.swift_models[]` 增加 swift-server 生态族（附录 A 给出候选清单，可先用
   regex+AST 双确认形式落地）
2. `wrapper_detection` 增加按"项目类型 profile"的分发：检测到 `Package.swift` 依赖
   swift-nio/async-http-client 时自动启用 http-server profile（见 3.1）
3. R1 输出 `sink_discovery_rate` 实时预警：L0 命中 0 且项目 ≥100 源文件时，明确提示
   "规则库对该生态可能盲区，R1.5 需加派 extractor 域"

### 1.2 anchor_registry 无 Swift 锚点（召回有效性无约束）

**现象**：`anchor_registry.json` 有 java/cpp/c/go/javascript/php 锚点，**Swift 为零**。
self-check 输出 `anchor_recall_by_lang.swift = null`。REQ-24 规定 <100% 阻止启动——但对
"无锚点语言"该约束形同虚设，报告被迫声明"Swift 覆盖率有效性不由锚点召回支撑"。

**根因**：v2.1 引入锚点机制时按此前审计过的语言回填，Swift 从未有 ground-truth 锚点。

**改进建议**：
1. 补 Swift 锚点（附录 B 列出 3 个现成候选：CVE-2020-15230 FileMiddleware 编码穿越、
   CVE-2024-21631 URI 解析溢出、GHSA-rj37-6j9x-74q6 header DoS）
2. self-check 对"目标语言无锚点"输出显式 `WARNING: no anchor for <lang>` 并记入
   `quantified_metrics.anchor_recall_note`（当前是静默 null，报告作者需自行发现）
3. 锚点不限于 CVE：项目内历史修复 commit 的"修复断言"（如 `guard !path.contains("../")`
   应对应 CVE-2020-15230 的回归测试锚点）同样可作 ground-truth

### 1.3 verifier 调用边幻觉：函数存在 ≠ 被调用（H3-L1 实证证伪）

**现象**：R4 H3 verifier 输出"Remote-triggerable trap: `Request.Body.makeAsyncIterator()`
calls `checkBodyStorage()` which runs `preconditionFailure` for the `.none` case
（RequestBody+Concurrency.swift:115-118）"——标注了精确行号、给出 6 层调用链、通过 depth
门禁、判定 Low 级远端进程崩溃。**实证抽验证伪**：空 body POST 返回 200 `total = 0` 无
崩溃；代码复核 `checkBodyStorage()` 在整棵树**无任何调用点**（`makeAsyncIterator` 直接
`self.drain {}`），是死代码。该 verifier 验证了"危险代码存在"，但没有验证"危险代码被
调用"这条边。

**根因**：
- A.1 任务书要求"回溯调用链 ≥3 层"，但**不要求每跳给出调用点证据**（grep 调用方）；深度
  门禁只能防"链太短"，不能防"链是编的"
- 对 R4 假说（业务深钻），任务书同样只要求"给出完整调用链(file:line)"，未要求调用边验证
- REACHABLE/confirmed 结论没有任何独立复核环节；实证抽验不在流程内（见 1.5）

**改进建议**：
1. A.1/A.2 任务书加"调用边验证"硬性要求：`call_chain` 每相邻两跳必须附调用点证据
   （`grep -n "fnName(" caller_file` 的命中行），输出格式增加 `call_edges_verified: bool`
2. 对"进程崩溃/死循环/无限分配"类**极端声称**（crash/hang/OOM），verifier 必须区分
   "代码存在"与"调用可达"，二者缺一自动降级 NEEDS_REVIEW
3. 采集阶段（`--stage collect`）对 REACHABLE 且 claim 极端后果的候选打
   `requires_empirical_spot_check` 标记，进入 1.5 的抽验池

### 1.4 R3 判定缺"平台支持性"维度（H1 Windows 穿越误判）

**现象**：两个 verifier 一致判定 FileMiddleware 反斜杠 `..\` 穿越 REACHABLE（High），
调用链、编码解码路径、NIOFileSystem Windows 语义论证完备。**用户复核指出**：Vapor 5 不
支持 Windows——CI 无 Windows runner（test.yml/codeql.yml 仅 ubuntu/macos）、Package.swift
平台声明仅 Apple 平台、`os(Windows)` 分支仅为 CRT 导入样板。支持平台（Linux/macOS）上
`\` 是字面文件名字符，穿越不成立 → 降级为 hardening 备注。

**根因**：R3 的判定维度只有"数据流可达 + 阻断检测"，REQ-19 跨边界规则也没有"目标平台"
维度。verifier 论证的是"某平台上的可达性"，而 skill 没有要求先回答"该平台是否在项目支
持范围内"。这与 [SKILL_LESSONS_JAVA_dubbo.md] 的"受信边界假设"同类——**判定规则漏掉了一
个现实前提维度**。

**改进建议**：
1. 候选入队时增加 `platform_precondition` 字段（Linux/macOS/Windows/Android/无），
   R3 任务书增加第一步："核实目标项目的平台支持声明（CI matrix、Package.swift platforms、
   README），若 sink 的利用前提平台不在支持范围 → 判 UNREACHABLE 并记 platform_excluded"
2. 同一缺陷在不同平台行为不同时，verdict 按"支持平台集合"判定而非按"任一平台"判定

### 1.5 无实证抽验阶段：33% 误判率靠人工兜底才发现

**现象**：lighttpd（C 审计）与 vapor（本次）连续两次都在流程外**手动**搭建实测环境验证
关键 REACHABLE 声称。本次抽验 3 个候选：C1 内存 DoS 证实（200MB→+201MB 峰值）、M2 二次方
放大证实（n² 曲线）、H3-L1 崩溃**证伪**。若无抽验，H3-L1 会带着精确行号与 6 层调用链
进入 CVE 申报清单。

**根因**：五阶段漏斗以"静态可达性判定"为终点，REACHABLE 的置信度没有实证分级。DoS/崩溃
类声称恰恰最容易实证（搭最小 app 发请求即可），也最容易因调用边幻觉而失真。

**改进建议**：
1. 新增可选阶段 **R5 实证抽验**：对 Top-N REACHABLE（尤其 claim 为 crash/hang/OOM 的）
   搭建最小 harness 验证；结果写回 `verify_queue.json`（`empirical` 字段），
   证伪项按 1.3 的规则回溯修正 verifier 错误并记录
2. 抽验成本有上限（N 默认 3~5，只抽 P0 候选），预期收益已被两次审计证明（各纠出一个
   高置信幻觉/误判）

---

## 2. P1 缺陷（工具与配置级）

### 2.1 R0.5 考古工具噪音过滤缺失

**现象**：`r05_diff_archaeology.py` 扫出 1234 个 commit，其中 477 个含 added_guards/
removed_paths——绝大多数是"linux fixes"、文档、重构。主 Agent 手工过滤后才得到 ~30 条
安全相关。工具输出的 `hint` 字段只回显 commit 标题，无任何噪声分类。

**改进建议**：默认排除仅触碰 Tests/、docs/、README 的 commit；按文件路径对
security-sensitive 模块（如 `*Middleware*`、`*Auth*`、`*Parser*`）加权排序；`--grep`
默认词中 `fix` 过于宽泛，拆为 `fix(security|auth|cookie|session|...)` 或排除
`linux fixes` 这类高频噪音。

### 2.2 batch_verify 对 R05 手写候选生成 "?" 模板

**现象**：主 Agent 手工写入的 R05 候选（含 sink_type/source_pattern/note）经
`--stage next` 出队时，生成的 verifier 任务书所有上下文字段为 "?"（file "?"、cwe "?"、
sink 代码为空）——因为手写候选缺 `cwe/category/language` 字段，模板构建无降级逻辑。

**改进建议**：`stage_next` 对缺字段候选从 `sink_type`（"CWE-22 PathTraversal"）解析
cwe/category 兜底，或校验队列 schema 并在缺失时拒绝入队（报错优于静默 "?"）。

### 2.3 `--cand-` 参数前缀双重拼接陷阱

**现象**：文档示例 `--cand-001='...'`，解析器将 `--cand-` 后的部分再拼回 `CAND-` 前缀。
对自定义 id（CAND-R05-001）正确写法是 `--cand-R05-001`，照文档直觉写 `--cand-CAND-R05-001`
会得到 "Unknown candidate: CAND-CAND-R05-001" 静默更新 0 条。第一次 collect 8 条全部落空。

**改进建议**：解析器接受两种形式（带或不带 CAND- 前缀），文档写明映射规则。与
[SKILL_LESSONS_C.md] 的"collect 不支持非 CAND- 前缀 id"同属工具链 id 契约问题，建议
统一为"候选 id 全字符匹配，不做前缀拼接"。

### 2.4 assert 的 blocking_point 校验比 A.1 模板更严格

**现象**：A.1 输出格式允许 `"blocking_point": "file:line / null"`，但 `--stage assert`
要求 UNREACHABLE 必须有 truthy 的 blocking_point。本次 3 个候选（会话、cookie、锁重入）
的 UNREACHABLE 依据是"无调用点存在/多层纵深防御"，没有单一阻断点，被断言拦下后只能手工
补写说明性字符串。该问题与 README「跨语言收敛」第 4 条（Java 1,124 个 / C 69 个）同源，
在 Swift 第三次复现。

**改进建议**：UNREACHABLE 接受 `blocking_point: null` 但要求 `evidence` 明确说明阻断
形态（"无调用点"/"协议层阻断"/"纵深防御链"），或将断言放宽为
`blocking_point != null OR evidence 含阻断说明关键词`。

### 2.5 verifier 输出 JSON 转义不合规

**现象**：verifier 在 JSON 字符串中写裸反斜杠（`..\..\secret`），产出非法 JSON，采集脚本
需 lenient 修复（正则转义）才能解析。

**改进建议**：任务书输出格式说明加一条"JSON 中反斜杠必须转义为 `\\`"；collect 阶段对
非法 JSON 先做一次自动修复（当前直接 `json.loads` 抛错退出）。

---

## 3. 执行面经验（R5 实证抽验手册素材）

### 3.1 Swift 工具链与依赖环境坑（实证环境 bootstrap）

| 坑 | 现象 | 解法 |
|---|---|---|
| swiftly 平台支持滞后 | Ubuntu 26.04 报 "Unsupported Linux platform" | 用官方 tarball 直装 |
| 下载 URL 命名 | `ubuntu2404/swift-6.3-RELEASE/...` 404；正确路径含 `ubuntu2404-aarch64` 段 | 先 `curl -r 0-0` 探测 206 再下载 |
| 工具链版本墙 | vapor 锁定的 swift-http-server rev 要求 tools 6.4，6.3 报错 | 按依赖的 tools-version 选工具链 |
| 运行库 soname 变更 | 26.04 的 libxml2.so.16 / 缺 libncurses.so.6 | compat 软链目录 + LD_LIBRARY_PATH（/opt/swift-compat-libs 模式） |
| 遗留服务占端口 | 上一场 lighttpd 审计的测试实例仍占 8080/8081，curl 响应实为 lighttpd | 实测前 `ss -tlnp` + 用带标记响应（自定义 header）验证端口归属，禁止仅凭 HTTP 码判断 |

### 3.2 实测响应归属验证原则

**现象**：vapor App 因端口冲突启动即崩，但 curl 仍收到 200/404——响应来自沙箱/遗留服务，
一度把测试结果引向错误结论（"路由 404、无崩溃"）。

**原则**：任何实测前，先向目标端口发一个**带唯一标记**的请求（如 curl 一个会返回服务
自身标识的端点，或起一个返回 `X-MARKER` 的探针服务）确认响应归属；崩溃/内存类测试必须
同时记录进程 PID 与 `kill -0` 存活状态，不能只看 HTTP 层。

---

## 4. 表现良好的部分（保持）

1. **R1.5 框架扩展在 L0 全盲时扛起全部发现**：3 域 extractor（IO/内存/解析）产出 25 条
   L1 候选，全部 4 个 REACHABLE 家族源自 L1——证明"规则盲区 → L1 兜底"的架构设计成立，
   前提是 extractor 任务书有足够的域定制（本次靠主 Agent 手工增强，见 1.1）
2. **R3 批量状态机与容错语义**：`collect` 的部分成功（坏 verdict 不丢批）、PENDING 重试、
   depth 门禁降级 NEEDS_REVIEW 均按设计工作
3. **量化指标诚实暴露盲区**：Sink Discovery Rate 0% + False Negative Risk 86.2% 如实报告，
   没有美化——这是 v2 指标设计优于 pre-v2 的地方
4. **REQ-19 跨边界终结**：multipart boundary 直入外部解析器按"边界即 sink"正确判定
5. **R0.5 考古**：确认上游 HEAD = 本地 HEAD 后正确判定历史修复全部已应用，并把观察面
   转为 R3 候选而非误报"疑似未修复"

---

## 5. 改进优先级总表

| # | 缺陷 | 等级 | 建议动作 | 关联先例 |
|---|---|---|---|---|
| 1.1 | L0 Swift 规则对 swift-server 全盲 | P0 | 补 swift-server sink 族 + 项目类型 profile | SWIFT_GO 1.1 |
| 1.2 | 无 Swift 锚点 | P0 | 补 3 个 CVE 锚点 + 无锚点显式 WARNING | PHP（锚点机制起源） |
| 1.3 | verifier 调用边幻觉 | P0 | 任务书加调用边证据要求 + 极端声称降级规则 | 本次新发现 |
| 1.4 | 判定缺平台支持维度 | P0 | platform_precondition 字段 + CI 证据检查 | 同 dubbo"受信边界"类 |
| 1.5 | 无实证抽验阶段 | P0 | 新增 R5 实证抽验（Top-N REACHABLE） | lighttpd + vapor 两次人工兜底 |
| 2.1 | R0.5 噪音 | P1 | 排除 docs/tests commit + 安全模块加权 | — |
| 2.2 | next 阶段 "?" 模板 | P1 | 队列 schema 校验/字段兜底 | — |
| 2.3 | --cand- 前缀陷阱 | P1 | 接受双形式 + 文档写明 | C lesson |
| 2.4 | blocking_point 断言过严 | P1 | 接受"无调用点"形态 | 跨语言第 4 条 |
| 2.5 | JSON 转义 | P1 | 任务书加转义说明 + collect 自动修复 | — |
| 3.1/3.2 | 环境坑手册 | P2 | 沉淀为 R5 实证手册 | — |

---

## 附录 A：建议补充的 swift-server L0 sink 族（regex + 结构化上下文双确认）

```
文件系统: FileSystem.shared.info(forFileAt:)|withFileHandle(forReadingAt:)|withFileHandle(forWritingAt:)|readChunks|readChunk|readToEnd(maximumSizeAllowed:)|write(contentsOf:)
请求体收集: body.collect(max:)|collect(upTo:)|readableBytes > 0 ? bodyBuffer : nil|writeBytes(chunk.span.bytes)
分配/缓冲: ByteBufferAllocator.buffer(capacity:)|ByteBuffer(repeating:count:)|Array(repeating:count:)|reserveCapacity|readToEnd(maximumSizeAllowed: .bytes(.max))
响应/头: headers[.location]|headers.setCookie|serialize(name:)|redirect(to:)
模板/视图: ViewRenderer.render|PlaintextRenderer.render|viewsDirectory +
解析: URLEncodedFormParser.parse|MultipartParser(boundary:)|DirectiveParser.nextDirectives
进程/环境: Process.run|setenv
日志注入: withLogger(mergingMetadata:)|Logger.current[metadataKey:]
```

## 附录 B：建议补充的 Swift 锚点（anchor_registry.json）

```json
"swift": [
  {"cve": "CVE-2020-15230", "title": "FileMiddleware percent-encoded ../ traversal (fixed 4.29.4)",
   "pattern": "removingPercentEncoding", "target": "FileMiddleware.swift", "expect": "guard + contains(\"../\")"},
  {"cve": "CVE-2024-21631", "title": "vapor_urlparser_parse integer overflow / host spoofing (fixed 4.90.0)",
   "pattern": "urlparser|hostname parsing", "target": "URI/urlparser"},
  {"cve": "GHSA-rj37-6j9x-74q6", "title": "NIOHTTP1 unbounded header blocks (fixed swift-nio 2.100.0)",
   "pattern": "HTTPDecoder|configureHTTPServerPipeline", "target": "dependency pinning"}
]
```

> 注：CVE-2020-15230 锚点若在本次审计前入库，R0 自检即可把 FileMiddleware 标记为锚点
> 命中区，R3 对 FileMiddleware 的分析会直接对照已知 CVE 的修复形态（guard 存在性），
> H1 的"平台可利用性"问题也会更早暴露。
