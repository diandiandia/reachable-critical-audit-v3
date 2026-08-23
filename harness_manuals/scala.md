# Scala 实证工具链手册 (v3.1)

> 适用战役：Scala 首审（10 候选 1 REACHABLE、3 裁决降级，R3.5 拦截率 75% 历批次最高）。
> 事实来源：W6_MORE_LANGS_FINDINGS.md §20（主）、§21.4/§21.5（网络与拦截率交叉）、§19.4/§19.8（jar 核验与引擎矩阵先例）。

## 1. 工具链探测
- Scala 首审批次的判定全程未依赖框架全量构建：R3.5 结论由源码机制级深钻达成（帧解析器逐 chunk 流式、HttpMessage Host↔authority 一致性 400、filename* RFC 5987 合规性），无 sbt 全量编译 harness 记录（W6 §20.1/20.3/20.4）
- 依赖 jar 可从 Maven Central 直取：repo1.maven.org 已证实可达（W6 §21.4 交叉事实）；同源 jar 直取先例为 kotlinx.io 0.9.1 锁版本下载（W6 §19.2）
- 探测命令：`which sbt scala java cs`；本地缓存查 `~/.cache/coursier`、`~/.ivy2`
- 代码库规模 495 文件是 R1 agent 舒适区：~500 文件以下无需限时令，证据质量高（仅 1 JSON 语法错误 + 24 行号漂移自动修复，未出现超大规模项目级 agent 失控）（W6 §20.5）
- 若走 jar 机制实证：引用外部 jar 前做字节码与树源码一致性比对（服务器框架 jar 先例，W6 §19.4）

## 2. 版本记录义务
- 依 W6 §16.1 先例：harness 元数据必须记录工具链精确版本——Scala 侧记录 scalaVersion、sbt 版本与框架版本（目标框架具体版本号）
- 防御默认值矩阵是版本级事实（max-content-length 8m / max-header-count 64 / enable-http2 false / request-timeout 20s 随版本漂移），引用时必须绑定版本（W6 §20.6）
- 多引擎框架的版本/引擎矩阵（内置引擎 vs 第三方引擎类实现差异）与"文档默认引擎"必须显式标注（W6 §19.8 先例）

## 3. 常见陷阱清单
- 成熟框架上"机制真 ≠ 危害真"：verifier 的 REACHABLE 集中于机制真实但危害未建立的声称（W6 §20.1）
- WS 帧声称先分"引擎流式 vs 应用物化"：流式引擎逐 chunk 交付（背压约束）vs 物化引擎头部解析即 allocate 2GiB——同族声称跨框架结论相反；且"应用侧 toStrict 与 HTTP 路径限额的不对称性"本身是独立 finding（NEEDS_REVIEW 级）（W6 §20.2）
- CWE-436 双解析器前提显式化：浏览器是请求头生成方而非二次解析器；"与浏览器不一致"默认不成立，必须枚举对同一字节流做安全判定的两个解析器并证明分歧（W6 §20.3）
- RFC 5987 规定的百分号解码是合规非分歧——filename* 类声称必须先查规范合规性（W6 §20.3）
- absolute-form/请求走私家族：检查第一步是目标框架是否校验 Host↔authority 一致性，有则核心形态直接封口（目标框架拒绝不一致返回 400）（W6 §20.4）
- 成熟基础设施项目的 REACHABLE 判定高概率被证伪者机制级深钻降级——verifier 对"默认值=无防护"类假设系统性偏乐观（W6 §21.5 三连统计）

## 4. 阳性模式（战役验证过的做法）
- 配置默认值矩阵盘点作为固定审查项：max-content-length 8m / max-header-count 64 / enable-http2 false / Host 一致性 / request-timeout 20s——目标框架是各批次中防御默认最完整的框架（W6 §20.6）
- 证伪者机制级深钻模板：逐 chunk 流式语义核验（FrameEventParser）、Host 一致性 400 行为、RFC 5987 合规性（W6 §20.1/20.3/20.4）
- verifier 对 CWE-436/601 类必须要求危害场景实例化（第二解析器/受害者流程）后再判 REACHABLE（W6 §20.1）
- 报告显式列出防御面——对使用方是选型信息，与 finding 并列输出（W6 §20.6）
- 拦截率校准表：75% / 66.7% / 50%——成熟框架的 REACHABLE 判定先按此预设"可能被降级"（W6 §21.5）

## 5. 网络依赖
- repo1.maven.org（Maven Central）可达（W6 §21.4）——sbt/coursier 依赖主源；首次解析需联网，~/.cache/coursier 可离线复用
- github.com 可达（W6 §21.4）
- 对照：proxy.golang.org 不可达仅影响 Go 生态，不波及 Scala 构建（W6 §21.4）

## 6. 实证范围建议
- 机制级为主：本批判定全部由源码级/机制级论证达成，无 E2E harness 必要（W6 §20.1/20.4/20.6）
- E2E 可行但非必需：需框架运行时才上 E2E，依赖 Maven Central 可达（W6 §21.4）
- 源事实级（框架默认值表、一致性校验存在性、流式语义）在本语言是强论证形态（W6 §20.2/20.6）
- 未来 E2E 参考 Swift 服务端测量纪律：先做冒烟请求验证响应可达性、测量点放服务端而非客户端完成信号、每阶段 pkill 清理端口防 stale 进程（W6 §16.3/16.5 跨语言先例）
