# Java 实证工具链手册 (v3.1)

> 事实来源：W6_MORE_LANGS_FINDINGS.md §18（Java 首审批次）与 §21.4（网络可达性）、
> JVM 审计 lessons（反序列化 allowlist 三版本交叉复核、RPC 框架输入面）。
> 战役战绩：10 候选 2 REACHABLE；T1 解码器实证（请求 1.87GB 无上限 vs 响应 8MB cap）。

## 1. 工具链探测

- `javac` + maven 现场可用：`mvn -pl` 单模块编译（§18.5）。
- `mvn dependency:build-classpath` 生成运行 classpath（§18.5）。
- 依赖库 sources jar 可获取：按审计目标锁定版本取 sources jar 验证反序列化接线（§18.2）。
- 真实解码器实证模式：匿名子类调用真实 `ExchangeCodec.decode`（§18.5）。
- 审计目标版本/HEAD 记录：多分支框架需锁定 branch HEAD（对应 lessons §0）。

## 2. 版本记录义务

- 依赖库语义必须落到版本级验证：三版本交叉复核（对应 lessons §0）；反序列化 allowlist 接线位置（多处解析点）按锁定版本核验（§18.2）。
- 内建 deny list 内容按版本记录：autoType 检查 denyList 仅 ClassLoader 子类 + SQL DataSource/RowSet，TemplatesImpl/c3p0/spring/连接池 不在 deny 内（SKILL_LESSONS_JAVA §1.4）。
- JDK 版本影响标准库语义（zip/Inflater 行为 JDK 22+ 变更 JEP 505，§19.3 跨语言事实）——解压/压缩类实证记录 `java -version`。
- 安全状态为全局共享属性时（DefaultSerializeClassChecker），结论与版本/全局态绑定（§18.3）。

## 3. 常见陷阱清单

- CWE-78 伪通用噪音：`exec`/`execute` 命中 ASM `Frame.execute`、javac `JCTree.exec` 等字节码/编译器内部类——规则必须接收者限定 `Runtime.exec`/`ProcessBuilder`（SKILL_LESSONS_JAVA §1.3）。
- 反序列化授权逻辑跨文件分布：`@type` → 白名单 → `loadClass` → `newInstance` 不在单文件（SKILL_LESSONS_JAVA §1.2）。
- sources_regex 只覆盖 Web 注解（@RequestBody/HttpServletRequest）时，RPC 框架真实输入面在网络层——源模型与项目输入面不匹配（对应 lessons §2）。
- 同族判定一致性：CAND-007 与 CAND-002 共享同一 Hessian2SerializerFactory.loadSerializedClass → DefaultSerializeClassChecker 阻断点，无法区分 → 按最严格者统一降级（§18.3）。
- R1 大代码库超时第二例：RPC 框架 2400 文件 4 域测绘总耗时 2 小时+（§18.6）。
- 行号漂移量大：30+ 漂移（§18.7，对比 Swift 批次 3 处手修）。
- 反序列化 gate 枚举不全：Redis 反序列化器无参构造仍默认 autoType 开启——默认框架配置无白名单 + autoType 开（SKILL_LESSONS_JAVA §1.4）。
- 规模管理：RPC 框架万级候选/百级验证批次；sources_regex 只覆盖 Web 注解导致源模型与真实输入面（网络层）不匹配（对应 lessons §0/§2）。

## 4. 阳性模式（战役验证过的做法）

- 真实解码器实证模式（T1）：maven -pl 单模块编译 + dependency:build-classpath + 匿名子类调用真实 ExchangeCodec.decode；16 字节头部声明 1.87GB → REQUEST 全 NEED_MORE_INPUT（无上限）vs RESPONSE 8MB cap 截断——不对称性一行实证（§18.5）。
- 解码器/解析器类声称优先走"真实类 + 最小输入"实证，勿手写复刻（§18.5）。
- 反序列化 allowlist/checker 三态门控审计：默认序列化类检查器的 checker/allowlist 类安全控制按三态（allow/deny/未知）核验（对应 lessons §5）。
- LOGIC_PATTERN 危险谓词规则：类型映射路径无 deny 检查、autoType 检查 hash 白名单绕过（SKILL_LESSONS_JAVA §1.4/§2）。
- 反序列化类假设的前提必须落到依赖库版本级验证（sources jar 核验，§18.2）。
- 主代理直接生成 R2 假设（30 分钟 vs 2.5 小时，§18.1）。
- 行号漂移自动修复器成型：±30 行内首行 snippet 匹配 + suggested_line 记录（含多行 snippet 取首行）（§18.7）。
- "危害被前提吸收"对照模板：持前提（ZK 写）时更简路径（CAND-006）等效 → 无边际能力增量（§18.4）。

## 5. 网络依赖

- repo1.maven.org 可达（§21.4）——maven 依赖解析、sources jar 获取均走通。
- github.com 可达（§21.4）。
- 无已知阻断记录（对比 Go 的 proxy.golang.org + google.golang.org 双不可达，§21.4）。

## 6. 实证范围建议

- **E2E/机制级成本低**：javac+maven 单模块即可跑真实类——解码器/解析器/反序列化类声称一律实证（§18.5）。
- 依赖库安全语义（autoType 回调接线/内建名单）属于"多态穿透"范围，必须版本级验证（§18.2）。
- 源事实级用于纯语义声称（无运行时不确定性类），需记录阻断原因（§21.4 跨语言纪律）。
- 双轨记录合法：R3 判"默认不可达"（QOS 命令 PROTECTED）与 R4 记"配置漂移面"（匿名 PUBLIC 面 + ForeignHostPermitHandler 短路）可共存，报告必须同时呈现（§18.8）。
- 门禁 ③ 的实证义务同样适用于 R4 confirmed 的 oom/unbounded 类 findings（§18.9）。
