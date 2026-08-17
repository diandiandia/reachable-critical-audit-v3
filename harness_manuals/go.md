# Go 实证工具链手册 (v3.1)

> 适用战役：etcd（Go 首审，10 候选 2 REACHABLE、4 裁决降级，R3.5 拦截率 66.7%）；gvisor（v2 期 Go 对照组）。
> 事实来源：W6_MORE_LANGS_FINDINGS.md §21（主）；SKILL_LESSONS_SWIFT_GO.md §1.2/§2.1/§3/§4.1/§5.1/§7/§9.1/§10.1（gvisor）。

## 1. 工具链探测
- Go 工具链在本机存在：etcd 批次尝试过实机构建，失败于网络而非工具链缺失（W6 §21.4）
- 探测命令：`go version`、`go env GOPROXY GOMODCACHE GONOSUMDB`、`ls $(go env GOMODCACHE)`
- 模块下载依赖 proxy.golang.org——已证实不可达，实机 etcd 构建因此失败；降级路径为模块缓存预填充或 vendor，本批未走通（W6 §21.4）
- 平台可构建性预检：R0 必须探测项目目标平台/构建可行性，不可构建项目明确"验证降级策略"（源码确证 + 最小环境隔离测试）（SKILL_LESSONS_SWIFT_GO §10.1）
- 语义层面（非工具链）先验：Go 是方法调用语言，通用 regex 命中任意方法名/标识符——gvisor 先例 `.Add(` 误报 atomicbitops.Add/time.Add（974 条）、`.Exec(` 误报 bpf.Exec（48 条）、CWE-352 的 post|put|delete 无 web 场景（2498 条）（SKILL_LESSONS_SWIFT_GO §1.2）

## 2. 版本记录义务
- 记录 go 工具链精确版本（依 W6 §16.1 harness 元数据义务先例）
- 依赖库版本必须落版本：哨兵值语义是版本级事实——MaxUint32 是 grpc-go 的显式"无限制"哨兵（SETTINGS 不通告 + 拒绝检查 4.29e9）（W6 §21.3），依赖升级/降级可能改变结论
- 网络阻断时的降级依据必须落盘：阻断域名 + 降级层级 + 理由（W6 §21.4）
- R0 平台/构建可行性预检结果与降级策略落盘（SKILL_LESSONS_SWIFT_GO §10.1）

## 3. 常见陷阱清单
- proxy.golang.org + google.golang.org 双不可达 → 实机 etcd 构建失败（W6 §21.4）
- "无上限"声称常是"未找到上限"：CAND-004 的"事件缓冲无上限"被证伪——chanBufLen=128 + victim 每 watcher ≤1 批 + ctrlStreamBufLen=16 逐级背压；"无上限"必须枚举队列/通道的每一跳容量常量，"未找到"≠"不存在"（W6 §21.2）
- 哨兵值陷阱：数值默认值审计必须查下游依赖对该值的哨兵处理（MAX_VALUE/-1/0/MaxUint32 分别问"库把它当什么"），不能只看数值（W6 §21.3）
- verifier 对"默认值=无防护"类假设系统性偏乐观（R3.5 拦截 66.7% 三连：akka 75%/etcd 66.7%/dubbo 50%）（W6 §21.5）
- unsafe.Pointer/syscall 互操作被泛化规则当 CWE-119 候选：gvisor 563 条全为规范封装（unsafe.Pointer 系统调用封装），需"unsafe 精确模式"而非泛化 CWE-119（SKILL_LESSONS_SWIFT_GO §7/§5.1）
- 成熟安全项目规则命中≈噪音：有 CVE 流程/OSS-Fuzz 的项目直接威胁模型驱动深钻，规则扫描仅作广度兜底（SKILL_LESSONS_SWIFT_GO §5.1）
- 规则库与指标失真：self-check 的覆盖率度量"字符串存在性"而非"模式有效性"，AST pattern 需冒烟匹配测试；sink_discovery_rate 99.5% 实际 99% 候选是误报（SKILL_LESSONS_SWIFT_GO §2.1/§8.1）
- CWE 领域不适用：gvisor 被打 2498 条 CWE-352（CSRF）、44 条 CWE-643（XPath）——按项目领域过滤 CWE 而非事后人工（SKILL_LESSONS_SWIFT_GO §3）
- 候选量爆炸：gvisor 15157 候选（P0=7693）超出逐条验证能力，需按攻击面聚类测绘 + 手工验证高价值点，剩余批量标注 NEEDS_REVIEW（SKILL_LESSONS_SWIFT_GO §4.1）

## 4. 阳性模式（战役验证过的做法）
- 百万级随机差分对拍：证伪者跑 106 万随机用例对拍 adt.Contains vs 朴素并集覆盖模型，零失配——区间/边界语义类声称的最强证伪武器是差分测试而非推理（W6 §21.1）
- "无上限"声称的逐跳容量枚举法（W6 §21.2）
- 默认值类假设入队前自问"三重有界检查"（回收/配额/成本比）预筛（W6 §21.5）
- 路径语义用独立 Go 测试验证：gvisor 最有价值发现（cgroup 路径穿越）来自对 filepath.Join 语义的独立 Go 测试而非规则命中（SKILL_LESSONS_SWIFT_GO §9.1）
- unsafe 精确模式清单：unsafe.Pointer→uintptr 保留、Syscall6 长度参数、切片头重建后无界索引（SKILL_LESSONS_SWIFT_GO §7）
- 源事实级论证可接受："sentinel 语义"类声称无运行时不确性，源事实级即可定谳并记录阻断原因（W6 §21.4）

## 5. 网络依赖
- 不可达：proxy.golang.org、google.golang.org（W6 §21.4）
- 可达：github.com、repo1.maven.org（W6 §21.4）
- 对策：vendor 目录或本地 module cache；不可达时按范围纪律（W6 §17.7/§19.2 先例）降为源事实级并记录阻断原因（W6 §21.4）

## 6. 实证范围建议
- E2E（实机构建）受 Google 域名网络阻断——除非 vendor/缓存可用，否则不承诺 E2E（W6 §21.4）
- 机制级可行：单文件 go run/go test 纯 stdlib harness（差分对拍类，W6 §21.1）
- 源事实级为主力：容量常量、哨兵语义、背压链均无运行时不确性（W6 §21.2/21.3/21.4）
- 平台维度：macOS 专属项目在 Linux 不可编译时全部退化为源码级确认，不得默认假设可构建（SKILL_LESSONS_SWIFT_GO §10.1）
