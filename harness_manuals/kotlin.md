# Kotlin 实证工具链手册 (v3.1)

> 事实来源：W6_MORE_LANGS_FINDINGS.md §19（Ktor 批次，Kotlin 首审）与 §21.4（网络可达性）。
> 战役战绩：10 候选 5 REACHABLE；T1b 100MB 物化实证、T6 解压炸弹实证、真实 jar 对抗实证（0/35 触发）。

## 1. 工具链探测

- `kotlinc` 现场可用（§21.4：kotlinc/kotlinx-io 下载与运行成功）。
- gradle/expect-actual 构建墙：KMP 全量编译失败（`kotlinc -Xmulti-platform` + atomicfu 仍失败）——实证不依赖 gradle 全编译（§19.2）。
- 依赖 jar 从 Maven Central 直取：kotlinx.io 0.9.1、ktor-http-jvm-3.5.1.jar（§19.2/19.4/21.4）。
- 目标 jar 与树源码字节码一致性核验是标准步骤（§19.4）。
- JDK 版本探测：解压/压缩类实证先读目标代码的 Inflater 参数再定 harness（§19.3）。

## 2. 版本记录义务

- 依赖锁版本精确记录：kotlinx.io 0.9.1（项目锁定版本，§19.2）、ktor-http-jvm-3.5.1.jar（§19.4）。
- jar 版本与源码树一致性核验记录（§19.4：字节码确认与树源码一致）。
- **JDK 代际陷阱**：JDK 25 `Inflater(false)` 不做 gzip（"incorrect header check"）——T6 实证首次失败即此；JDK 22+ zip 实现变更（JEP 505 系）使旧 harness 假设失效（§19.3）。
- 多引擎版本差异记录：CIO vs Netty（Netty 用 ServerCookieDecoder.LAX 重写）——REACHABLE 需在文档默认引擎（Netty）成立（§19.8）。

## 3. 常见陷阱清单

- 签名惯用法噪音：header_inject 2013 命中全为 StringBuilder.append、reflect 1718 全为 `::class`、url_open 1357 全为 HttpClient（客户端侧）——通用 regex 对 Kotlin 零区分度（§19.1）；签名需重写为框架语义族（receive/readRemaining、respondRedirect、Cookie parse、XForwarded 写入点），`::class`/`append(` 类模式直接退役。
- `Inflater(false)` gzip 语义陷阱（§19.3）。
- 边真实 ≠ 分支可达：verifier 验证了调用边但未验证分支可达性（默认配置下 encode 参数恒 URI_ENCODING）——"sink 分支行为死代码"证伪模板（§19.5）。
- 多引擎"任一引擎成立"误判：PATH A 仅 CIO 执行；按旗舰引擎（Netty）复核才定（§19.8）。
- 默认值=无防护族收割：maxFrameSize Long.MAX / maxDecodedContentLength -1 / cookie secure false / 客户端 cookie 无签名 / 异常回显（§19.7）。

## 4. 阳性模式（战役验证过的做法）

- **verbatim 循环提取实证 + 真实依赖 jar**（T1b）：ktor-io readBuffer 循环逐字符提取 + kotlinx.io 0.9.1 真实 Buffer——100MB 物化实证，绕开 gradle/expect-actual 构建墙（§19.2）。
- **真实 jar 对抗实证**（CAND-003 证伪）：下载 ktor-http-jvm-3.5.1.jar 跑 29 种畸形头 35 条目，0/35 触发——"sink 分支是行为死代码"一击致命（§19.4）。
- 解压实证先读目标代码 Inflater 参数：ktor 源码用 `Inflater(true)` + 手动 GZIP_HEADER_SIZE 跳过（§19.3）。
- 类型系统先于配置检查：receiveType 编译期静态 + kotlinx 多态仅开发者注册类集 → 比运行时白名单更强的阻断（§19.6）。
- H7 数值上限类默认值专项：MAX_VALUE/-1/0 三值即红旗（对照正向例 vapor URLEncodedForm maxRecursionDepth 100，§19.7）；H7 9 findings 全部"默认值=无防护"族（maxFrameSize Long.MAX / maxDecodedContentLength -1 / cookie secure false / 客户端 cookie 无签名 / 异常回显）。
- 对照 check：同一个"框架流式 vs 应用物化"区分在 ktor 与 akka 结论相反（ktor 头部解析即 allocate 2GiB vs akka 逐 chunk 流式，§20.2 跨语言对照）。

## 5. 网络依赖

- repo1.maven.org 可达（§21.4）——kotlinx.io 0.9.1、ktor-http-jvm jar 直取成功。
- github.com 可达（§21.4）。
- 无已知阻断记录（对比 Go 的 proxy.golang.org 双不可达，§21.4）。

## 6. 实证范围建议

- **机制级是标准层级**：jar + verbatim 函数提取（§19.2）；对抗性验证走真实 jar + 畸形输入矩阵 + 计数触发（§19.4）。
- E2E（完整 KMP 构建）当前环境不可行——KMP 全量编译有 build 墙（§19.2）；E2E 需求降级为"真实 jar + 最小输入"的机制级并显式标注 scope。
- 解压/压缩类实证前置条件：先验证 JDK 语义（Inflater 参数、JDK 22+ 变更）再写 harness（§19.3）。
- 多引擎框架声明必须标注引擎矩阵；REACHABLE 以文档默认引擎为准（§19.8）。
- verifier 任务书强制项：sink 的每个条件分支给出"攻击者输入到达该分支的具体配置/输入"证据，默认路径参数逐一对照默认值（§19.5）。
