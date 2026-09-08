# Rust 实证工具链手册 (v3.1)

> 适用战役：Rust v3 首审（10 候选 1 REACHABLE、R3.5 拦截 66.7%，实证类 4/4 一次通过）。
> 事实来源：W6_MORE_LANGS_FINDINGS.md §23（主）、§21.4（网络交叉）、§19.2/§15.6/§20.2（跨语言先例）。

## 1. 工具链探测
- cargo 已安装但不在后台 shell 默认 PATH：位于 $HOME/.cargo/bin，需显式加入 PATH 或全路径调用（W6 §23.3a）
- 探测命令：`which cargo || ls $HOME/.cargo/bin/`；`rustc --version && cargo --version`
- cargo 测试 4/4 编译一次通过（修正三连后）——cargo test 是验证过的实证载体（W6 §23.3）
- 实证路径建议：在目标 crate 测试目录写 harness 编译运行；完整应用构建遇多平台墙（expect/actual 类）时降级（W6 §19.2 先例）

## 2. 版本记录义务
- 记录 rustc/cargo 精确版本（依 W6 §16.1 harness 元数据义务先例）
- 依赖锁定版本：Cargo.lock 锁定；transitive 依赖行为随版本变（bytes/flate2 可见性问题即版本绑定事实，W6 §23.3b）；锁版本 crate/jar 直取先例 kotlinx.io 0.9.1（W6 §19.2）
- 行为级事实绑定版本：多 member deflate 行为（flate2 单 member EOF）是版本级事实，记录 flate2 版本（W6 §23.8）
- feature 组合必须记录：http2 feature 在 Cargo 默认集但 bind() 运行时仅 h1——feature 配置与运行时可达性分开记录（W6 §23.2）

## 3. 常见陷阱清单
- cargo 不在后台 shell PATH（W6 §23.3a）
- transitive dev-dep 不可见：框架 HTTP 测试不能 import 底层依赖 crate（transitive 依赖不可用）→ 预计算 zlib 字节内嵌，或用 crate 重导出路径（W6 §23.3b）
- 编译器建议误导：Payload try_next 模式的编译器 help 文本（`Ok(Some(Ok(chunk)))`）反编译失败 → 用 StreamExt::next() 直解 Item=Result<Bytes,E>——不要盲从编译器提示，读源码 impl Stream 的 type Item（W6 §23.3c）
- WS 帧声称先问"框架是否物化整条消息"：Rust 生态答案通常是流式——64KB 帧上限逐帧强制（含 continuation）、WsStream 1:1 透传、ActorStream 逐项交付，累积只在用户 handler；"框架有整条消息缓冲区"的 OOM 前提不存在（W6 §23.1；与物化引擎 2GiB 对照 §20.2）
- feature 默认集 ≠ 运行时可达：http2 在 Cargo 默认集（代码层开）但 bind() 运行时仅 h1（运行时默认关）；TLS 部署 ALPN 自动注入 h2（部署层自动开）——按三层 gate 清单拆分裁决（W6 §23.2，源 §22.3）
- R2 假设锚点行可能是文档注释：CAND-007 退化候选 source_line=1 指向 //! module doc block——锚点行必须主代理 Read 验证非文档/注释行再入队，否则浪费 verifier slot（W6 §23.7）
- 解压放大只测单维度会被证伪：多 member deflate 首 member 全膨胀 780x、后续 member flate2 单 member EOF——必须同时测单 chunk ratio（真放大）与多 member 行为（真累积面）两维度（W6 §23.8）
- 反向核验：若框架确有物化点（如 toStrict），物化点即新 sink——"流式"结论必须同时确认无物化 API 被应用调用（W6 §20.2 跨语言对照）

## 4. 阳性模式（战役验证过的做法）
- cargo test 内嵌 harness 实证：在 crate 测试目录写测试编译运行，4/4 一次通过（W6 §23.3）
- 三层 gate 清单跨语言复用（W6 §23.2）：feature 默认集/运行时默认/部署层——裁决输出"gate 记录型 REACHABLE"而非二元
- Host 采信族裁决树：① 框架内建敏感消费者（密码重置/链接生成）→ REACHABLE；② 仅暴露 helper 供应用使用 → NEEDS_REVIEW；③ 有 Host↔authority 一致性校验 → 直接封口；跨框架 Host 采信三案并表统一判据（W6 §23.4）
- "框架硬化缺口"评级标准：gate 在部署者（symlink/开启选项）→ Medium 上限；无 gate 默认链路直接成立（如 Payload 无界 High）→ 可上 High（W6 §23.5）
- 成熟框架审计重心前移 R4：R4 输出 6 confirmed（Payload 无界/multipart 无总量/canonicalize 丢弃/listing XSS/解压放大/Display 泄露）> R3 输出 1 REACHABLE——H1-H7 对"默认上限缺失"类缺口敏感，R2 假设对显式 sink 敏感，两者互补且 R4 产率更高（W6 §23.6）
- 机制级实证必须标注 scope（机制 vs 全链）：函数体级实证（isPatternMatch 类）只证明函数体级机制，链可达性需另证（W6 §15.6 先例）
- 跨语言方案平移：Kotlin 的 verbatim 循环提取 + 锁版本依赖直取方案可平移到 Rust（W6 §19.2 先例）

## 5. 网络依赖
- crates.io 可达：cargo 测试依赖获取与编译成功的事实（W6 §23.3）——与 Go 的 proxy.golang.org 不可达形成对照（W6 §21.4）
- github.com 可达（W6 §21.4）
- 若 crates.io 不可达：锁版本源码/vendor 目录 + 函数体提取（W6 §19.2 先例）

## 6. 实证范围建议
- 机制级为主力：cargo test 内嵌 harness 可独立编译 crate 内部（W6 §23.3）；函数体级实证标注 scope（W6 §15.6）
- E2E 受依赖墙限制：完整应用构建遇 expect/actual 类多平台墙时降级（W6 §19.2 先例）
- 源事实级：框架流式语义、feature 可达性、三层 gate 均为源码论证（W6 §23.1/23.2）
