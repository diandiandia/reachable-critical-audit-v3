# C# 实证工具链手册 (v3.1)

> 来源：W6_MORE_LANGS_FINDINGS.md（§13）。实证工件：审计项目内 `.audit_results/empirical_harness/`（Program.cs、harness.csproj、empirical_harness_run.txt）。

## 1. 工具链探测
- 审计现场可能**无 .NET 运行时**——.NET 批次从零构建：dotnet-install 脚本安装 SDK（记录 SDK 版本，批次为 8.0.4xx），**单 TFM 构建** `-p:LibraryFrameworks=net8.0`（W6 §13.3）——"无运行时"不得豁免实证（§13.3 先例），探测 = `dotnet --list-sdks` + 全盘核对安装路径（§16.2 路径遮蔽教训通用：勿假定单一安装）。
- harness 工程形态：`harness.csproj`（`<TargetFramework>net8.0</TargetFramework>` + `<Reference>` HintPath 直指审计源码构建出的 dll（审计项目内相对路径））——**构建审计版本源码而非引用 NuGet 包**（W6 §13.3）。
- 测试路径约定：`.Tests` 点前缀形态（审计目标测试工程名）须入 R1 过滤映射表（SKILL_LESSONS §1.2）。
- 反序列化类声称的依赖事实：Json.NET 零第三方依赖，restore 仅 SourceLink 需版本属性注入（W6 §13.3）——依赖面小是 C# 库审计的常态特征，实证成本集中在 SDK 安装。

## 2. 版本记录义务
- 记录四版本：**audited version**（11.0.1-beta2，基线 13.0.1——缺陷在两版本同时存在须并记，Program.cs 头注事实）、SDK 版本（8.0.4xx）、**TFM**（net8.0）、运行时行为。
- **代际陷阱**：TFM/运行时版本改变利用性——维护者自带灾难性 pattern（BacktrackingRegex_SingleMatch_TimeoutRespected 测试）在 net8 已被运行时优化（32ms 完成），旧 TFM 上才体现灾难性（W6 §13.4）；报告必须显式记录"运行时版本影响利用性"前提维度。
- 声称类先定类后实证：protocol_dos（声称类）→ gate ③ 强制实证，不得因环境无运行时改判 other 规避（W6 §13.9）。

## 3. 常见陷阱清单
- **签名库对 C# 反序列化语义族零覆盖**：22 签名命中 → 10 假设全 drop（固定常量 `StringBuilder(256)`/Tests 代码/MaxDepth 有界），sink_discovery_rate=0%；真实候选全部来自 LLM 假设路径——TypeNameHandling $type / Type.GetType 直通 / ISerializable ctor / Expression.Compile 放大器 / JPath ReDoS 五大家族（W6 §13.1）；签名词库应补 TypeNameHandling、BindToType、Assembly.Load*、`Type.GetType(s, true)`、ISerializableCreator、`Expression.*Compile`、`Regex.IsMatch`+InfiniteMatchTimeout。
- **反序列化 gate 语义族**：TypeNameHandling.Auto 读取端无特判（与 Objects/Arrays 一致）；binder 内置黑名单仅 3 类型名；`:819` 兼容检查只限族不限实例——gate 枚举值 × 读取/写入端矩阵必须全查（写入端差异 ≠ 读取端差异）（W6 §13.2）。
- **ReDoS 实证先做 pattern 搜索**：`^(a|a?)+$` 在 net8 仍 2^n（129ms→29.8s，n=20→28）但自动原子化会让灾难类 pattern 假阴性——先 patsearch 独立搜索确认回溯结构再测（W6 §13.4）。
- **语义前提假阴性**：JObject 根上的 `$[?()]` 过滤子节点而非对象本身——T1b 双侧树取向量在 JObject 根 0ms 假阴性，包数组后才触发（1865ms）——0ms 结果先怀疑语义前提而非结论（W6 §13.7）。
- **异常路径描述会被实证纠正**：BSON 预分配原证据"流提前结束抛 EndOfStreamException"——实测被 ReadType:221 catch 吞掉转干净 EOF（无异常传播、分配不回滚、调用方无感知），行为比原描述更隐蔽（W6 §13.5）——R4 finding 的异常路径描述必须实证抽验。
- **能力支配第 4 例**：CAND-006 缓冲倍增——宿主已物化输入（2x UTF-16）时库的 2x 常数因子不构成新能力 → NEEDS_REVIEW（W6 §13.8）——"线性常数因子放大+宿主前置持有"先例固化；main-agent 的 claim_type 裁决须与 R3.5 降级裁决共用同一论证链。
- **主代理修复脚本自伤**：批量重写逻辑把"本来就匹配"的 entry 也标了证据标记，窗口匹配误清空 snippet（W6 §9.5 同构）——实证 harness 相关文件的人工批量修改同样须逐 entry 对照。

## 4. 阳性模式（战役验证过的做法）
- **实证 harness 从零构建模板**（可复制）：dotnet-install → 单 TFM 构建审计源码 → csproj HintPath 引用 dll → `dotnet run`——.NET 批次 5 REACHABLE 全实证（$type 家族 + JPath ReDoS 2^n），T1a/T1b/T1c/T1d/T2/T3 六测试一次跑通（empirical_harness_run.txt）。
- **对照矩阵**：T2 $type 激活——`TypeNameHandling.Objects` marker=True vs 默认设置 marker=False（gate 默认关闭）——默认拒绝/配置接受双侧对照（§24.4 模式）；T1d benign n=28 0ms（无害输入零耗时）作为缩放实证的同图对照，证明耗时只随攻击输入结构增长（empirical_harness_run.txt）。
- **refuter 补强向量**：CAND-008 证伪者 #1 发现 ParseSide 允许 =~ 两侧任一为路径表达式——固定 path 下 pattern 亦来自攻击者 JSON 树（比 verifier 场景更强的 pattern 控制向量）——refutation.strengthened 字段落盘进报告（W6 §13.6）。
- **声明长度先分配后校验**（T3）：BSON 16 字节 payload 声明 32M chars → tokens=2、private delta ~64MB——解码器/解析器类声称用"真实类 + 最小输入"实证（§18.5 模式）。
- **真实解码器实证优先**：不要手写复刻解析逻辑——直接调库真实类（JPath SelectToken/BSON reader），实证与库行为一一对应（§18.5 通用）。
- **负结论 surface 签收**：29 surface 中 18 覆盖映射 + 11 负结论签名（reviewed_by + empty_domain_reason），零手工补缺——C# 批次的门禁 ⑦ 标准操作（W6 §13.10）。

## 5. 网络依赖
- dotnet-install 脚本下载 SDK（须先探测安装源可达性）；NuGet restore 面极小（仅 SourceLink，注入版本属性即可）。
- 审计源码本地构建后实证**完全离线**（HintPath 引用本地 dll）——网络阻断时 SDK 安装是唯一阻塞点，阻断则按 §21.4 降级并记录 blocker（先例：Go 项目构建失败即网络阻断案例）。
- lessons 未记录 C# 批次的其它网络阻断；NuGet 包源不需要（构建按审计版本源码而非 NuGet 包，W6 §13.3）。

## 6. 实证范围建议
- **声称类一律实证**（§13.9 强制）：protocol_dos（JPath ReDoS）/任意类型激活/预分配放大全部走真实类实证——本批次 4 REACHABLE 全实证级证明成本可控。
- **E2E**：库审计的 E2E = 真实 sink 类 + 攻击者输入最小形态（T1 pattern、T2 JSON 载荷、T3 BSON 头）——无需进程级 E2E。
- **机制级**：函数体提取实证（§15.6 模式）仅依赖墙时用；C# 无依赖墙（零第三方依赖 + 单 TFM），不应降级。
- 运行时版本矩阵（net8 vs 旧 TFM）作为实证维度必带——利用性依赖运行时优化（W6 §13.4）。
