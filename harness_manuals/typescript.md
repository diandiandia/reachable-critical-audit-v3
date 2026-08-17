# TypeScript 实证工具链手册 (v3.1)

> 事实来源：W6_MORE_LANGS_FINDINGS.md §15（NestJS 批次，TS 首审）与 §21.4（网络可达性）。
> 战役战绩：15 候选 6 REACHABLE，R3.5 拦截率 54%（历批次最高）。

## 1. 工具链探测

- `node --version` / `npm` 现场可用；实证跑在 Node 22 上（§15.5 unhandledRejection 崩溃实测）。
- `tsc` 可用：verifier 自主编译审计源码跑实证（tsc 编译 JsonSocket，§15.2）。
- `npx esbuild` 可用：bundle 实证尝试（§15.6）；依赖墙时 `npx esbuild --external` 逐层降级。
- npm 依赖现场安装成功：aedes broker + mqtt 客户端、express 复刻 adapter 均落地（§15.2）。
- 目标框架需探测其运行期 vs 构建期（路由注册期）代码边界（§15.1）。

## 2. 版本记录义务

- 记录精确 `node --version`：Node 22 的 unhandledRejection 默认崩溃语义是实证结论的承重前提（§15.5）。
- 记录依赖锁定版本：kafkajs 订阅期过滤行为按版本核验（§15.3 证伪者源码核验）。
- 记录 tsc/esbuild 版本与编译目标；编译产物行为差异影响 harness 有效性（§15.2/15.6）。
- 跨语言通则（§13.4）：运行时版本改变利用性——实证报告必须显式记录该维度。

## 3. 常见陷阱清单

- 签名库系统性误报：路径白名单族 85 命中全是路由注册期变换（Nest 无运行期远端驱动的路径门禁）、buffer 族 append 匹配到响应头 API、logic 族命中全在 test/（§15.1）。
- esbuild 全量 bundle 被 @nestjs 内部 import 阻断（§15.6）。
- 函数体级实证被误当全链可达：isPatternMatch 机制实证后被 kafkajs 订阅期行为证伪（§15.6）。
- 只查防护覆盖的一条路径：RpcProxy 有 catch 判 UNREACHABLE，同族 5 个传输（TCP/Redis/MQTT/NATS/RMQ）的 message 监听器全无 catch（§15.5）。
- verifier 的 empirical 结果未结构化 → 门禁 ③ 假 FAIL，collect 需从 evidence 自动提取实证标记（§15.2）。
- 证伪 args 手写时把单候选拆成两条单证伪者条目，votes 语义破碎（§15.7）。
- LLM 假设 JSON 裸引号第 4 次重现（§15.8）：backtick 代码段内裸 `"` 破坏 JSON——主代理侧固化修复脚本（backtick 段内仅转义无反斜杠前置的引号）。
- verifier 只查防护覆盖的一条路径的变体：判 UNREACHABLE 的"异常处理链存在"必须枚举全部同族监听点（§15.5 同条）。

## 4. 阳性模式（战役验证过的做法）

- verifier 自主编译源码跑实证成为常态：tsc 编译 JsonSocket、真实 aedes broker + mqtt 客户端、express 复刻 adapter、kafkajs 源码核验（§15.2）。
- esbuild 依赖墙降级链：先 `npx esbuild --external` 逐层降级，再退"逐字符提取真实函数体 + 剥 TS 类型标注"（isPatternMatch 实证，§15.6）。
- 证伪者基准压测实证：CAND-002 基准压测 2.00x、CAND-010 Object.assign 不污染实测、CAND-011 4.43ms vs 1.29ms 实测（§15.3）——"常见配置≠默认"论证模板，R3 verifier 的 gate 声明（"默认开"/"常见配置"）是证伪者首要攻击面。
- Node 进程崩溃类声称直接起真实服务器实测（§15.5，Node 22 unhandledRejection）。
- H4 检查清单："reply 通道族"——消息型框架必查 reply-to/回复通道可预测性与头驱动目标；5 传输同构缺陷一次审计全暴露（§15.4）。
- 签名库应补框架语义族：socket.on('data') 累积、JSON.stringify 无 catch、reply channel 拼接、multer 无 limits 默认（§15.1）。

## 5. 网络依赖

- npm registry 可达：aedes/mqtt/express 等依赖现场安装成功（§15.2）。
- github.com 可达（§21.4）——kafkajs 等源码核验路径可用。
- 无已知阻断记录（对比 Go 的 proxy.golang.org 双不可达，§21.4）。

## 6. 实证范围建议

- **E2E/机制级均验证可行**：依赖可现场安装，服务器类框架可直接起真实 broker/服务器（aedes、express 复刻，§15.2）；机制级（tsc 编译 + 函数体提取）已验证（§15.6）。
- 函数体级实证必须显式标注 scope（机制 vs 全链，§15.6）；链可达性判定交给 R3.5 证伪者（kafkajs 订阅期行为）。
- 成熟框架（Nest）R2 假设应预设"机制真≠危害真"——R3.5 拦截 54% 全来自证伪者深度实证（§15.3）。
- 多引擎/多传输框架的"任一成立"结论必须枚举全部同族路径（§15.5 纪律）。
