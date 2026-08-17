# Ruby 实证工具链手册 (v3.1)

> 适用战役：sinatra（Ruby v3 首审，10 候选 2 REACHABLE、R3.5 拦截 50%，top-15 战役收官）。
> 事实来源：W6_MORE_LANGS_FINDINGS.md §24（主）、§21.4（网络交叉）。

## 1. 工具链探测
- ruby 可用且实测运行时为 Ruby 3.3（Oniguruma 线性化实证在同一环境完成，W6 §24.3）
- 探测命令：`ruby --version && gem --version && which bundle`
- 实证探针零依赖：`ruby -Ilib` + Rack::MockRequest 即可跑真实 App.call——Ruby 是实证成本最低语言之一（W6 §24.8）
- R1 小项目适配：<100 文件的 Ruby 项目用 2 agents（A=net+data / B=proc+storage）分工无冲突，20 surfaces 证据质量高（W6 §24.7）

## 2. 版本记录义务
- Ruby 运行时精确版本是判定前置：ReDoS 结论依赖版本（Ruby 3.3 Oniguruma 线性化 vs 旧版灾难性回溯）（W6 §24.3）
- 框架与依赖版本必须落版本：mustermann 3.0.3 编译正则结构线性（22 模式×对抗输入比率 ~2.0）为版本级事实（W6 §24.3）
- 安全修复版本与意图成对记录：CVE-2024-21510 官方修复有意选择 opt-in，意图记载于 CHANGELOG（W6 §24.2）

## 3. 常见陷阱清单
- ReDoS 假设在 Ruby 3.2+ 环境的先验应下调：Oniguruma 线性化全部经典灾难类（(a+)+$、(a|aa)+$、(x+x+)+y、(a*)*b 等实测线性）——"正则回溯灾难"类假设入队前先问运行时版本是否线性化（Onigmo/Oniguruma 的优化在 3.2+ 默认启用）（W6 §24.3）
- "默认防护失效"判定前必须查三处文档：README 对默认值的声明（empty=permit-all 明文）、CHANGELOG 中安全修复的意图（CVE-2024-21510 有意 opt-in）、防护库自身 README 装载说明——三者任一表明"有意 opt-in"即 CWE-693 不成立，降级为 defense-in-depth gap（W6 §24.2）
- 头注入四级残余面：CR/LF（响应拆分）→ quote（属性逃逸）→ 全 C0 控制字符（0x0B/0x1B/0x7F 仍透传，RFC 9110 field-content 违规）→ NUL（崩溃）——"头注入已封堵"断言必须扩展到全 C0 字符集而非仅 CR/LF（W6 §24.5）
- NUL→500 本身是独立 DoS 面，与注入分开记录（W6 §24.5）
- Host 投毒/开放重定向族的受害方可触发性：referer 由受害者浏览器设置（攻击者布置入口页即控制）→ 可受害方触发；Host/X-Forwarded-Host 无法由浏览器导航携带 → 被投毒的 Location 只出现在攻击者自身请求的响应中（W6 §24.1）
- 行号漂移/相对路径：13 行漂移 + 相对路径均被修复器处理；相对路径修复器逻辑=非绝对路径拼项目根（W6 §24.7）

## 4. 阳性模式（战役验证过的做法）
- 全 payload 矩阵实证：CAND-001 static! 23 种穿越 payload 全 404 + symlink 预置 200 LEAKED 对照——"守卫链封死"类结论必须有至少一维实测 payload 矩阵支撑（W6 §24.8）
- E2E 伪造对照矩阵：默认 secret 时 crafted Marshal cookie 被 HMAC 拒绝 vs `set :session_secret, nil` 后同一 cookie 被接受——同一 payload 的接受/拒绝对照比单侧攻击演示强一个量级；反序列化/签名类实证的标准动作（W6 §24.4）
- MockRequest 探针：ruby -Ilib + Rack::MockRequest 零依赖跑真实 App.call——verifier 任务书对 Ruby 项目可显式允许轻量探针；verifier 自主实证趋势第三次验证（W6 §24.8）
- R4 默认值全表 + 三层语义盘点（HostAuthorization 空名单/CSRF drop_session/environment 默认 development/整栈无上限）升级为成熟框架固定深钻重点；R4 产率第三次超 R3（9 confirmed vs 2 REACHABLE 全 Low）（W6 §24.6）
- 裁决树第四维"受害方可触发性"：referer > Host > X-Forwarded-Host；"仅 helper"降级论据对 referer 类不适用（框架文档化 back+redirect 模式即完整脆弱流）（W6 §24.1，源 §23.4 裁决树扩展）
- NEEDS_REVIEW 与 R4 confirmed 同事实共存规范化：候选分类（可达性口径）与 finding 评级（硬化缺口口径）是两套口径，报告输出交叉引用映射表（W6 §24.9）
- 反向核验"文档化有意设计"：防护缺失≠防护失效——先查三处文档再判 CWE-693（W6 §24.2）

## 5. 网络依赖
- 本批实证零网络依赖：Rack::MockRequest 零依赖可跑（W6 §24.8）
- gem 安装场景未记录阻断；github.com 可达（W6 §21.4）可用于源码获取

## 6. 实证范围建议
- E2E 级完全可行且成本最低：App.call + MockRequest 即全链路（W6 §24.8）；E2E 对照矩阵（默认拒绝 vs 弱化配置接受）是黄金证据形态，'gate=应用显式弱化配置'类 finding 用对照实证支撑评级（W6 §24.4）
- 机制级：正则结构分析（mustermann 编译结构线性核验，W6 §24.3）
- ReDoS 类实证必须先确认运行时版本再做结论（W6 §24.3）
