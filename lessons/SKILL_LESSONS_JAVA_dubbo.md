# Reachable Critical Audit Skill — Java (Dubbo 3.3) 审计暴露的缺陷与改进建议

> **文档性质**：基于 Apache Dubbo 3.3（branch 3.3，HEAD `3a3043227f`）实测审计对
> `reachable-critical-audit` skill 的回顾性缺陷分析。与仓库根目录 `SKILL_LESSONS_JAVA.md`
> （fastjson2 AutoType 教训）互为姊妹篇：fastjson2 篇暴露"语义逻辑缺陷不可表达"，
> 本篇暴露"大规模 Java 工程的规则误标与受信边界假设"。
>
> **审计日期**：2026-08-15
> **测试目标**：/root/dubbo（Apache Dubbo 3.3，15,620 候选全量验证，173 个验证批次）
> **执行模式**：Mode A'（batch_verify.py 状态机 + 通用子智能体）
> **原始复盘**：项目 `.audit_results/audit_retrospective_and_skill_feedback.md`（本文为其
> skill 部分的沉淀版）

---

## 0. 摘要

Dubbo 3.3 是 skill 迄今审计过的最大 Java 工程（15,620 候选）。实测暴露 5 类缺陷：

1. **L0 规则 CWE 标签语义性不足，误标率极高（最严重）**：NEEDS_REVIEW 占 89.15%，
   噪声率与 lighttpd C 审计的 89% 高度一致——两门语言、同一种病：规则匹配"关键字/结构
   形态"，不匹配"语义"。
2. **源模型与目标项目输入面不匹配**：sources 只有 Web 注解，Dubbo 的真实输入面（Netty
   协议解码、registry/config-center 通道、泛化调用、QoS 端口）全靠 L1/人工兜住。
3. **R3 verifier 对"配置门控/受信边界"裁决不一致**：同型 gate 候选在不同批次出现
   REACHABLE/UNREACHABLE 分歧；"operator 配置按受信处理"的惯例在 R4 被推翻
   （configurators 通道 → accesslog 任意文件写入）。
4. **正则兜底无家族聚类**：363 个 `.remove()`、170 个 `write()` 同族候选逐条验证，
   浪费大量批次；同一行被多 CWE 标签重复入队。
5. **工具链缺口**：blocking_point null 断言失败（1,124 个）、batch size 不可配置、
   R4 无 collect/assert、无报告生成 stage。

---

## 1. 关键缺陷

### 1.1 L0 规则库 CWE 标签误标（最严重）

| CWE | 命中 | 误标形态 |
|---|---|---|
| CWE-918 SSRF | 3,703 | `@RequestBody`/`HttpServletRequest` 源正则误匹配 RPC 方法名/URL 处理代码 |
| CWE-285 越权 | 428 | 一切 `.remove()` 被当"不当授权"——363 个 remove 族逐一轮证为进程内簿记清理 |
| CWE-79/434 XSS/上传 | 691 | 一切 `write(...)` 语句被当 XSS/上传 sink |
| CWE-643 XPath 注入 | 497 | 一切 `Pattern.compile(...)`（含静态常量声明）被当 XPath |
| CWE-611 XXE | 788 | 一切反射调用（`Array.newInstance`/`getDeclaredConstructor().newInstance()`）被当 XXE |
| CWE-601/927/501/74/78/89 | — | 同型关键字误标 |

**根因**：规则以"关键字/sink 名称"匹配，缺少语义上下文（该调用是否在鉴权路径上、是否
处理 XML、输出方向是否 HTML）。数据流/污点分析没有真正参与初筛。与 fastjson2 篇 §1.3
（CWE-78 命中 ASM Frame.execute）和 C 篇 §1.1（CWE-476 命中每个解引用）同构。

### 1.2 源模型与目标项目输入面不匹配

- `sources_regex` 只有 Web 注解（@RequestBody、HttpServletRequest 等），而 Dubbo 的真实
  输入面是：Netty 协议解码（ExchangeCodec/Decodeable*）、registry/config-center 数据通道、
  泛化调用（generic=true）、QoS 端口、triple/http12 REST。
- **后果**：真正的漏洞全部来自这些非 Web 输入面——靠 L1/锚点/人工判断兜住，而非 L0 规则。
  L0 命中率 99.92% 但有效命中率极低，Sink Discovery Rate 指标不反映误标率
  （C 篇 §0 的 95.77% 是同一问题的镜像）。

### 1.3 R3 verifier 对"配置门控/受信边界"裁决不一致

- DefaultSerializeClassChecker 三态门控的 sink：GenericFilter/JavaBeanSerializeUtil 判
  REACHABLE（记 gate），同类情形在别的批次出现 UNREACHABLE 倾向。
- "operator 配置/registry 数据按受信处理"的惯例在 R4-H4 被推翻：传统注册表 configurators
  通道无 securityKey 过滤，远端数据可注入 accesslog/dump.directory 路径参数 →
  任意文件写入。**R3→R4 发生了一次结论翻转，靠报告里手工标注修正。**
- **根因**：R3 任务书没有固化"门控/受信边界"判定准则；R4 推翻 R3 后没有回写机制。

### 1.4 正则兜底无家族聚类 + 同行多标签

- 同文件同语义家族（363 个 remove、170 个 write、Pattern 常量族）逐条验证浪费大量批次
  （173 批）。skill 无"同族聚类 + 结论传播"机制。
- 同一行被不同 CWE 标签生成多个候选（`FileUtils.write` 同时 CWE-79 与 CWE-434；
  `file.delete()` 同时 CWE-285/CWE-20），应同 file:line 去重保留最高优先级。

### 1.5 工具链缺口（与 C 篇 §1.4 交叉印证）

1. **assert 要求 UNREACHABLE blocking_point 非空**：1,124 个候选以 null 落盘 → 断言失败，
   主代理写脚本补录。**与 C 篇 §1.4.3 完全同源，两次审计都踩中 → v2.2 必改。**
2. **batch size 不可配置**：`--stage next` 固定 3~4 个/批；要求提速到 12/批时无参数可用。
3. **R4 无内置 collect/assert**：r4_findings 写回与 H1–H6 断言靠主代理手写脚本。
4. **无报告生成 stage**：量化报告（NEEDS_REVIEW 全量清单、家族归并）全部手工生成。
5. **call_chain_depth<3 自动降级与死代码冲突**：死代码的合法阻断点（无调用者）被迫补链
   凑数。与 C 篇 §1.4.4 同源。
6. **R0.5 guard 提取噪声**：added_guards 解析不准，7 个候选全靠主代理人工复核。

### 1.6 锚点召回机制的实战检验（正面 + 负面）

- **正面**：anchor recall 100% 门槛真实生效——本次 cpp CWE-787 锚点 0/1 命中直接阻止启动，
  逼出规则库补丁（2 条 tree-sitter patterns）。机制设计正确。
- **负面**：锚点只覆盖 15 种预设语言的已知 CVE 形态，对"框架特有 sink"（registry 数据
  通道、checker 门控）无表达——恰是 §1.2 的另一面。

---

## 2. 改进建议（按优先级）

### P0 —— 影响结论正确性
1. **规则语义化与误标排除层**：CWE-285 要求"鉴权上下文"而非裸 `.remove()`；CWE-79 要求
   输出方向含 HTML 渲染；CWE-643 排除静态常量 Pattern；CWE-611 排除无 XML 语义的反射。
   对通用工具/数据结构方法（集合 remove、流拷贝 write、缓存操作）建立白名单排除层，
   从源头砍掉 ~89% 噪声。
2. **源模型可插拔平台 profile**：除 Web 注解外，增加 RPC/微服务输入面 profile（Netty
   解码入口、registry/config-center 通道、泛化调用、QoS/管理端口、消息队列消费者）；
   按项目类型自动选择 profile。
3. **R3 任务书固化"门控/受信边界"判定准则**：① 存在可降级配置门控（checker
   STRICT/WARN/DISABLE）→ REACHABLE 且必须记录 gate；② "受信边界"必须逐通道验证"远端
   数据确实无法流入"，禁止按惯例假设——R4-H4-② 就是惯例假设的代价。
4. **R4 回写机制**：R4 发现推翻 R3 结论时，对相关候选 verdict 标记回写
   （`superseded_by: R4-H4-2`），报告自动带出修正记录。
5. **Java 反序列化 allowlist 绕过专项规则**：checker/allowlist 类安全控制的
   LOGIC_PATTERN 专项（类名混淆、hash 白名单碰撞、allowlist 内危险类枚举、前缀校验替代
   全名校验）——V-1/V-2 家族真正的 CVE 金矿（与 fastjson2 篇 §1.1 呼应）。

### P1 —— 影响效率
6. **家族聚类与结论传播**：入队时按 file+语义模式聚类（同族只验证一个代表样本，结论
   传播到家族成员），预计压缩 5~10 倍验证量。
7. **同行多标签去重**：同 file:line 只保留最高优先级 CWE 候选（P0>P1>P2）。
8. **batch size 参数化**：`--stage next --batch-size N`。
9. **collect 前置校验**：verdict 必需字段（含 blocking_point 非空）在 collect 时校验并
   给出修复提示；assert 与 collect 校验规则统一。
10. **死代码/工具方法链路规则放宽**："无调用者"作为合法阻断点
    （`blocking_point="no production callers"`），不再强制 3 层链。

### P2 —— 可用性与文档
11. **内置 r4-collect / r4-assert / report stage**：`--stage r4-collect --file f.json`、
    `--stage r4-assert`（H1–H6 检查）、`--stage report`（按 REQ-10 模板生成 JSON/MD）。
12. **文档一致性**：README/SKILL.md 阶段命名与版本统一；Mode A' 执行描述直接以 Agent
    原语书写；REQ-10 报告模板与实际工具输出字段对齐。
13. **R0.5 提取质量**：added_guards/removed_paths 结构化解析（guard 的 if 条件/校验函数名/
    调用点三元组）。
14. **锚点注册表扩展指引**：提供"为项目类型添加锚点"的规范，让 anchor recall 从"看门"
    升级为"引导规则库补齐"。

---

## 3. 本次审计中 skill 表现良好的部分（保持）

1. **串行漏斗与断言门禁**：R0 anchor recall、R3 assert（PENDING 清零 + blocking_point
   校验）、R4 H1–H6 assert——三处硬门禁都真实拦住了问题。
2. **优先级出队**：P0（反序列化/注入）先验证，高危候选在审计前半段完成。
3. **子智能体验证质量**：3 层链/多态穿透/路径覆盖要求产出真实价值——多态穿透找出
   ScriptStateRouter 默认注册、configurators 双通道等主代理易漏点。
4. **Mode A' 适配可行**：batch_verify 状态机 173 批次无丢失，BATCH_COLLECTED_WITH_ERRORS
   的部分落盘语义正确。
5. **R0.5 差异考古价值**：7 个历史安全修复全部确认在 3.3 HEAD 生效（0 疑似未修复）。

---

*本 lesson 与 `SKILL_LESSONS_JAVA.md`（fastjson2）、`lessons/SKILL_LESSONS_C.md`（lighttpd）
共同构成 v2.1 → v2.2 改进输入。原始复盘见
`/root/dubbo/.audit_results/audit_retrospective_and_skill_feedback.md`。*
