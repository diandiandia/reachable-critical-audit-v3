# SKILL Lessons — kafka（2026-08-25）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = hybrid

### R3
- [grade_recomputed] CAND-001: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-002: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-006: 机械分级重算 (main-agent-after-top-up)
- [grade_recomputed] CAND-007: 机械分级重算 (collect-mechanical-recompute)

### R3.5
- [verdict_correction] CAND-004: {'at': 'R3.5', 'from': 'REACHABLE', 'demote_to': 'UNREACHABLE', 'decided_by': 'main-agent', 'rule': 'R3.5 1/2 分歧 → 主代理裁决，采纳证伪方 #1', 'reason': '威胁模型级裁决：注入路径唯一前提是 Byzantine/被攻陷 leader 或元数据日志目录写权限，而 Apache Kafka 官方安全模型(security-model.md:33,155)明确把 trusted peer controller 列为 out-of-scope adversary，quoru

### R3.5-N
- [resurrection] CAND-001: 复活成功：verifier 判定 UNREACHABLE 的承重前提全部为假，网络可达链完整闭合。(1) 前提"本检出 broker 运行时缺失(全树无 KafkaRaftServer/BrokerServer/KafkaConfig/main 入口)"为假——检出即完整 Apache Kafka trunk @3e0bc2801e，core/src/main/scala/kafka/server
- [resurrection] CAND-002: 复活成立（维度2+3）。逐条核实：技术前提全部为真（RestServerConfig.java:56 LISTENERS_DEFAULT=http://:8083、shipped_config.json 行73 listeners 注释→代码默认生效、RestServer.java:189-190 空 hostname 不调 setHost→Jetty INADDR_ANY、rest.extens
- [resurrection] CAND-004: 攻击维度逐条核验:维度2(承重前提)大部分成立——生成代码 MetadataRecordType.java:122-123 switch default throw UnsupportedVersionException,apiKey≤32767(AbstractApiMessageSerde.java:54-57),数组分配有守卫(ClientQuotaRecord.java:102-104,a

## 主代理过程观察（人工补充）

- 【机制价值·本批最重要】R3.5-N 复活波 3/3 成功推翻首次 verifier 的 UNREACHABLE——且每条的推翻都基于 verifier 的事实错误而非观点分歧：(a) CAND-001：verifier 称「检出无 broker 运行时」+「resolveVariableConfigs 无生产调用者」，实际 core/src/main/scala/kafka/server/ 完整存在、DynamicBrokerConfig.scala:350 的 Scala 别名调用点被漏检；(b) CAND-004：verifier 称「serde 无 raft/生产引用」，实际 SharedServer.scala:297 注入 MetadataRecordSerde.INSTANCE 进 KafkaRaftManager；(c) CAND-002：verifier 把文档化设计 null 化，与审计自身 R4 H5 对同一面的 confirmed/High 裁决直接矛盾。教训：①UNREACHABLE 判定的『承重前提』必须由主代理抽查，不能全信；②verifier 的 grep 容易漏 Scala 别名/JAVA 桥接调用点；③复活者的 gap 字段质量决定了重验质量。
- 【裁决实录】CAND-004 的 1/2 分歧终裁 UNREACHABLE（威胁模型外）——但与 zookeeper CAND-006/007 不同，它的链是复活者纠正事实错误后重建的真链：崩溃机制真实（MetadataLoader.handleCommit catch 到 ProcessTerminatingFaultHandler 到 Exit.halt），但注入前提等于 Byzantine leader/日志目录写权限，Kafka 官方安全模型（security-model.md:33,155）明确把 trusted peer controller 列为 out-of-scope。裁决公式：代码链真实 + 攻击者在官方模型外 = UNREACHABLE(模型外) + 代码缺口进修复建议。
- 【实证形态】三探针全部 E2E：CAND-003 的 90 字节毒批次让真实 broker OOM；CAND-008 的 72 字节 VOTE 让 controller 每次约 2s 无主；CAND-001 用 shipped 的 FileConfigProvider 做确定性类实例化目标 + no.such.Class 对照组——『禁止构造恶意 gadget 但允许用 classpath 上真实类做机制实证』是 rce 类声称的可行实证模板。
- 【skill 缺陷·已暴露】①R3 verifier 漏检 Scala 到 Java 别名调用点（JDynamicBrokerConfig 形态）导致 UNREACHABLE 误判——verifier 任务书应提示混合语言项目的跨语言调用点搜索。②grade 机械重算会把『有 12 边但 14 跳』的候选降级 static_only，门禁② 阻断后需补边波次（本次 CAND-004/006 两次）——建议导出阶段就校验 len(edges)>=len(chain)-1 并在任务书中明示。③复活重验改判 REACHABLE 后强制入证伪池的规则（SWR-V3.3.2-051）执行正确。
- 【降噪实测·第三次】kafka 佐证器 137+2 条，keep 5 条（其中 3 条与 LLM 主路径同 sink 收敛）——三次观察一致：佐证器在成熟项目上边际价值低但同 sink 收敛是可靠信号。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
