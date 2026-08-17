# Swift 实证工具链手册 (v3.1)

> 事实来源：W6_MORE_LANGS_FINDINGS.md §16（Vapor 批次，Swift 首审）与
> SKILL_LESSONS_SWIFT_VAPOR.md §1.4/§1.5/§3.1/§3.2（v2.1 实证抽验手册素材）。
> 战役战绩：17 候选 6 REACHABLE；实证抽验 3 候选 2 CONFIRMED 1 REFUTED（33% 误判率纠偏）。

## 1. 工具链探测

- swiftly 安装器在 Ubuntu 26.04 报 "Unsupported Linux platform" → 用官方 tarball 直装（SWIFT_VAPOR §3.1）。
- 下载 URL 命名含平台段：`ubuntu2404/swift-6.3-RELEASE/...` 404，正确路径含 `ubuntu2404-aarch64` 段；先 `curl -r 0-0` 探测 206 再下载（SWIFT_VAPOR §3.1）。
- R0 bootstrap 必须先读 `Package.swift` swift-tools-version + `Package.resolved` pins 再选工具链（§16.1）。
- find 全盘 swift 安装逐一核对版本（§16.2）；`swift-env.sh` 类脚本是线索。
- 缺失系统库（libxml2.so.16 / libncurses.so.6）→ compat 软链目录 + LD_LIBRARY_PATH（/opt/swift-compat-libs 模式，SWIFT_VAPOR §3.1）。

## 2. 版本记录义务

- harness 元数据必须记录精确 `swift --version`（§16.1）。
- 代际陷阱：vapor 5.0.0-alpha.2 依赖 swift-http-server 声明 tools 6.4（未发正式版），稳定目录只有 6.2/6.3；6.2 构建报 tools 版本墙；预编译 binary 在 6.2 runtime 符号不兼容（FoundationEssentials `_Representation`）（§16.1）。
- 多代工具链路径遮蔽：/opt/swift-6.4（6.4-dev 快照）被后解压的 /opt/swift（6.2）遮蔽，浪费整轮下载探测（§16.2）。
- 平台支持声明必须记录：Package.swift platforms、CI matrix（test.yml/codeql.yml 仅 ubuntu/macos）——Vapor 5 无 Windows（SWIFT_VAPOR §1.4）。

## 3. 常见陷阱清单

- 响应体不可达破坏实证设计：alpha 版流式响应体被直接丢弃（200+Content-Length+0 字节，连接挂起 ~30s），客户端永远收不到完成信号（§16.3）。
- **stale 进程 + 端口复用是最大陷阱**（两轮全零数据根源）：SIGTERM/SIGINT 被 Swift runtime 转 SIGTRAP，杀不死旧 App；新 App 绑定失败即崩，driver 请求全打到旧进程（§16.5/16.14）。
- `$!` 与后台复合命令陷阱：`cd x && VAR=v cmd &` 的 $! 是 bash 子 shell 而非 cmd，/proc/$P/environ 全是子 shell 环境（§16.6）。
- 采样线程非 daemon + 无 try/finally → 采样 fn 抛异常后死循环，进程卡死在解释器 shutdown（§16.3）。
- LD_LIBRARY_PATH 必须含 swift runtime 目录（§16.14）。
- 遗留服务占端口（lighttpd 实例占 8080/8081，curl 响应实为 lighttpd）——禁止仅凭 HTTP 码判断（SWIFT_VAPOR §3.1/3.2）。
- 多分支 getter 控制流推断错误：Request.swift:74-83 是 if/else-if 链，`try?` 失败返回 nil 终结，XFF 回退分支不可达（§16.9）。

## 4. 阳性模式（战役验证过的做法）

- 响应头时序作服务端完成信号：generateETagHash 在 Response 构造前 await → time-to-headers == hash 完成时间；ETag 头格式本身是模式自检（sha256 hex vs mtime-size）（§16.4）。
- 每阶段新 app 前 `pkill -9` 清理端口 + `/diag` 自检路由（echo 配置态）验证模式后才开始测量；诊断进程先 `comm` 验证 PID 身份（§16.5）。
- 后台启动服务用 `exec env ... cmd &` 或 Popen（§16.6）。
- 实证设计前先做 1 个冒烟请求验证响应可达性；测量点放服务端（CPU tick/VmHWM）而非客户端完成信号（§16.3）。
- 实测前 `ss -tlnp` + 带唯一标记响应（自定义 header）验证端口归属（SWIFT_VAPOR §3.1/3.2）。
- 崩溃/内存类测试同时记录 PID + `kill -0` 存活状态（SWIFT_VAPOR §3.2）。
- 代理/解析分歧类声称实测标准部署行为：证伪者跑真实 nginx 配置（error log + location 规则）实测 `//evil.com/admin`（§16.10）。
- 框架内完成信号检测先确认"昂贵操作在头之前还是之后"再定测量方案（§16.4 时间序技巧）。
- 同项目复审计时附旧 lessons 摘录：先例引用是 R3.5 最高效证伪武器（§16.8，§1.4 平台先例一击即中）。

## 5. 网络依赖

- download.swift.org 可达，但 6.4.x 目录全部 404（§16.1）。
- swiftly 对 Ubuntu 26.04 不支持（SWIFT_VAPOR §3.1）——tarball 直装路径必须走 curl 206 探测。
- 其余实证无网络依赖（本地构建 + 本地 harness）。

## 6. 实证范围建议

- **E2E 验证可行且产出高**：C1 内存 DoS 证实（200MB→+201MB 峰值）、M2 n² 放大证实、H3-L1 崩溃证伪（SWIFT_VAPOR §1.5）——DoS/崩溃类声称最容易实证也最容易失真，必须抽验。
- 平台依赖声称（Windows 穿越类）降为源事实级：查 Package.swift/CI matrix 即可判 platform_excluded（SWIFT_VAPOR §1.4）。
- 缓存/存储类放大声称的测量前检查：`storage[key]` 写必须查该 key 注册点（dead-cache 检查，§16.13——ETagHashes StorageKey 未注册是 CAND-006 放大关键）。
- 时间预算不要按 debug 慢假设（debug BoringSSL 哈希仍 ~1GB/s，128MB≈0.1s）；异常时长先怀疑 stale 进程/端口冲突再怀疑性能（§16.14）。
- 实证分级 scope_note 必须标注（机制级 vs 端到端，§17.7 跨语言纪律）。
