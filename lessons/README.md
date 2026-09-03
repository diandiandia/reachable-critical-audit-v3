# Lessons — 按语言归档的 skill 实测缺陷记录

每份 lesson 记录一次真实项目审计中暴露的 `reachable-critical-audit` skill 缺陷与改进建议
（按语言归档，多项目同语言经验会交叉引用）。

| 文件 | 语言 | 审计项目 | 日期 | 核心缺陷 |
|---|---|---|---|---|
| [SKILL_LESSONS_C.md](SKILL_LESSONS_C.md) | C | lighttpd 1.4.85 | 2026-08-15 | L0 AST pattern 伪影（89% 噪声）、路径过滤 4 个漏网、wrapper_detection 平台错配、collect 不支持非 CAND- 前缀 id、queue 覆写 |
| [SKILL_LESSONS_JAVA_dubbo.md](SKILL_LESSONS_JAVA_dubbo.md) | Java | Apache Dubbo 3.3 | 2026-08-15 | L0 CWE 标签语义误标（89% 噪声）、源模型与 RPC 输入面不匹配、受信边界惯例被 R4 推翻、无家族聚类 |
| [SKILL_LESSONS_JAVA.md](SKILL_LESSONS_JAVA.md) | Java | fastjson2 2.0.62 | 2026-08-13 | AutoType hash 白名单绕过不可表达（催生 LOGIC_PATTERN + R0.5）、CWE-78 伪通用噪音、"修复-再暴露"循环 |
| [SKILL_LESSONS_PHP.md](SKILL_LESSONS_PHP.md) | PHP | phpMyAdmin 4.8.5 + WordPress 7.0.4 | 2026-08-13 / 08-15 | phpMyAdmin: CVE-2018-12613 LFI 漏报（催生 CWE-98 规则 + 锚点召回）。WordPress: 宽 regex 误报爆炸（CWE-89 Laravel 绑定/918 文件函数/94 回调注册）、队列规模失控缺机械降噪层、编排工具链 9 缺陷、同点跨 CWE 维度拆分 |
| [SKILL_LESSONS_SWIFT_GO.md](SKILL_LESSONS_SWIFT_GO.md) | Swift/Go | — | (v2 驱动) | Go/Swift 结构化模型（CodeQL MaD / SinkModelCsv） |
| [SKILL_LESSONS_SWIFT_VAPOR.md](SKILL_LESSONS_SWIFT_VAPOR.md) | Swift | Vapor 5.0.0-alpha.2 | 2026-08-15 | L0 对 swift-server 生态全盲（SDR 0%）、无 Swift 锚点、verifier 调用边幻觉（H3-L1 实证证伪）、R3 缺平台支持维度（H1 Windows 误判）、无实证抽验阶段（33% 抽验误判率）；工具链坑（--cand- 前缀/R05 "?" 模板/blocking_point 断言）、Swift 环境坑手册 |
| [SKILL_LESSONS_10LANG_CAMPAIGN.md](SKILL_LESSONS_10LANG_CAMPAIGN.md) | 10 语言 | sinatra/ohmyzsh/actix-web/Newtonsoft/AWStats/Pester/akka-http/nest/ktor/django | 2026-08-15 | L0 规则 10 语言全线失效（42k 候选、噪音 95%+、废 Java 方法名移植）；测试路径过滤缺 5 种语言约定（spec/tst/*_tests.rs/.Tests/*.spec.ts）；R4 六假说不可扩展（战役模式 1×6 压缩）；子智能体失联无检测；簇验证无规范；跨项目 CWE 家族同源（ws 帧缓冲三家同现）→ 家族复用；R0.5 多 tag 交叉为最高价值阶段。15/15 语言覆盖达成 |
| [SKILL_LESSONS_mixed-fixture.md](SKILL_LESSONS_mixed-fixture.md) | 自动 | mixed-fixture | 2026-08-17 | R6 机械生成: 13 条问题证据 |
| [SKILL_LESSONS_Lersosa.md](SKILL_LESSONS_Lersosa.md) | 自动 | Lersosa | 2026-08-17 | R6 机械生成: 36 条问题证据 |
| [SKILL_LESSONS_mbedtls.md](SKILL_LESSONS_mbedtls.md) | 自动 | mbedtls | 2026-08-17 | R6 机械生成: 1 条问题证据 |
| [SKILL_LESSONS_lua.md](SKILL_LESSONS_lua.md) | 自动 | lua | 2026-08-19 | R6 机械生成: 1 条问题证据 |
| [SKILL_LESSONS_pyjwt.md](SKILL_LESSONS_pyjwt.md) | 自动 | pyjwt | 2026-08-20 | R6 机械生成: 6 条问题证据 |
| [SKILL_LESSONS_jsonwebtoken.md](SKILL_LESSONS_jsonwebtoken.md) | 自动 | jsonwebtoken | 2026-08-20 | R6 机械生成: 2 条问题证据 |
| [SKILL_LESSONS_orjson.md](SKILL_LESSONS_orjson.md) | 自动 | orjson | 2026-08-20 | R6 机械生成: 7 条问题证据 |
| [SKILL_LESSONS_..md](SKILL_LESSONS_..md) | 自动 | . | 2026-08-21 | R6 机械生成: 4 条问题证据 |
| [SKILL_LESSONS_jsrsasign.md](SKILL_LESSONS_jsrsasign.md) | 自动 | jsrsasign | 2026-08-21 | R6 机械生成: 4 条问题证据 |
| [SKILL_LESSONS_aiohttp.md](SKILL_LESSONS_aiohttp.md) | 自动 | aiohttp | 2026-08-24 | R6 机械生成: 8 条问题证据 |
| [SKILL_LESSONS_zookeeper.md](SKILL_LESSONS_zookeeper.md) | C/Java 混合 | zookeeper | 2026-08-25 | 渲染器静默丢弃 R4 Critical（已修 SWR-V3.7-009/010）、assert_ledger key:value 伪冲突（已修）、surface_mapper 实体锚点退化（v3.8 SWR-V3.8-008）、target_kind/maturity 机械误判（v3.8 SWR-V3.8-001/002）；编排模式：薄封装 fileref -95% args |
| [SKILL_LESSONS_tomcat.md](SKILL_LESSONS_tomcat.md) | Java | tomcat | 2026-08-25 | R4 非枚举 verdict/非法 severity 污染清单（v3.8 SWR-V3.8-003~005）、LISTEN_PATTERN 漏 NIO 形态（v3.8 SWR-V3.8-001）、R4 增量落盘（v3.8 SWR-V3.8-013） |
| [SKILL_LESSONS_kafka.md](SKILL_LESSONS_kafka.md) | Java/Scala 混合 | kafka | 2026-08-25 | verifier 漏跨语言调用点致 3 条 UNREACHABLE 误判（复活波 3/3 推翻）、edge 数规则误降级合并边（v3.8 SWR-V3.8-006/007） |
| [SKILL_LESSONS_nacos.md](SKILL_LESSONS_nacos.md) | Java | nacos | 2026-08-25 | 五域 schema 不统一（v3.8 SWR-V3.8-009）、路径白名单 '.' 漏查（v3.8 SWR-V3.8-009）、refutation 契约机械落盘（r35-collect 已通）、复活波 2/2 证伪 |
| [SKILL_LESSONS_shardingsphere.md](SKILL_LESSONS_shardingsphere.md) | Java | shardingsphere | 2026-08-25 | git describe 基线误导（v3.8 SWR-V3.8-014）、合并边误降级、同事实双计 severity override、hybrid 签收价值 |
| [SKILL_LESSONS_elasticsearch.md](SKILL_LESSONS_elasticsearch.md) | Java(+cpp/rs) | elasticsearch | 2026-08-27 | target_kind 大仓库 listener 假阴性（v3.8 SWR-V3.8-030）、r35-collect 契约缺 survived/votes（v3.8 SWR-V3.8-031）、BOUNDARY_KINDS 无 panama（v3.8 SWR-V3.8-032）、锚点同分取首缺陷（v3.8 SWR-V3.8-033）；复活波 3/3 系列第 4 例 |
| [SKILL_LESSONS_quarkus.md](SKILL_LESSONS_quarkus.md) | Java | quarkus | 2026-08-27 | v3.8 验证审计: keep=0 抽样复核条款实战; Host 头谓词缺陷通用形态; %2e%2e decode-after-normalize 发现由路径 checklist 驱动 |

## 跨语言收敛的模式（v2.1 → v2.2 改进输入）

> 全量盘点与架构评估见 [../docs/history/ARCHITECTURE_EVAL_v3.md](../docs/history/ARCHITECTURE_EVAL_v3.md)（2026-08-16）：
> 8 份 lesson 去重后 **31 类缺陷**（数据层 8 / 方法论 10 / 工具链 12 / 编排 1）；
> ~18 类可通过 v2.2 工程修改解决，7 类只能缓解，3 类为架构级根因
> （规则库-输入面匹配矛盾、"验证信任"缺独立证据源、指标体系建立在错误假设上）→
> v3 方向：攻击面测绘先行 + 签名提示库 + 实证证据分级。

1. **噪声率 89% 的诅咒**：Java 误标与 C 伪影形态不同、根因相同——规则匹配"关键字/结构形态"
   而非语义。两门语言独立实测都落在 ~89% 噪声率。
2. **平台错配**：Java 源模型只有 Web 注解（漏 Netty/registry/QoS），C 的 wrapper_detection
   只有 Android Bluetooth 生态（漏服务端协议/spawn）。→ 需要可插拔平台 profile。
3. **受信边界假设是最贵的错误**：Dubbo 审计中"operator 配置按受信处理"的惯例被 R4 推翻
   （configurators → 任意文件写入）；R3 任务书必须固化"逐通道验证"准则。
4. **工具链同源缺陷跨语言复现**：blocking_point null 断言失败（Java 1,124 个 / C 69 个 / Swift 3 个）、
   depth<3 门禁与死代码冲突、batch size 不可配置——三次审计独立踩中同一组坑。
5. **verifier 调用边幻觉（Swift/Vapor 新增）**：函数存在 ≠ 被调用——H3-L1 带精确行号与
   6 层链的崩溃声称被实测证伪（`checkBodyStorage()` 无调用点）。REACHABLE 的极端声称
   （crash/hang/OOM）必须附调用边 grep 证据，并由实证抽验兜底。
6. **判定缺平台/受信前提维度（Swift/Vapor 新增，与 dubbo 同源）**：Windows 反斜杠穿越
   被两个 verifier 判 REACHABLE，但目标项目不支持 Windows——R3 需先核实项目平台支持
   声明（CI matrix/平台声明）再判可达性。
7. **噪音诅咒规模化确认（10 语言战役）**：42k 候选、噪音率 ≥95%、SDR 全线趋 0——"89%
   噪音"是下限而非峰值；L0 规则的方法名移植语义在跨语言时归零，需废除或加噪音自检。
8. **同一缺陷形态跨项目复现（10 语言战役）**："未完成 WS 帧无界缓冲"同现 actix/akka/ktor
   三家；"先分配后校验"同现四家；"修复-再暴露"同现 AWStats/actix/django——战役模式应
   把已确认的家族签名注入后续项目 extractor 任务书（本役手动复用产出 4 个新发现）。

## 约定

- 每份 lesson 必须包含：量化背景（候选数/噪声率）、逐缺陷的现象-根因-改进建议、按
  P0/P1/P2 分级的建议清单、"表现良好的部分（保持）"。
- 与项目审计报告的关系：lesson 只沉淀 skill 缺陷，不重复项目漏洞细节（引用项目
  `.audit_results/` 归档）。
| [SKILL_LESSONS_firefox.md](SKILL_LESSONS_firefox.md) | 自动 | firefox | 2026-09-04 | R6 机械生成: 26 条问题证据 |
