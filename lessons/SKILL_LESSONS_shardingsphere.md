# SKILL_LESSONS_shardingsphere（2026-08-25，批次 #5）

Apache ShardingSphere 5.5.4-SNAPSHOT @6e3639ef5bc 审计实战教训（R0→R6 全流程，六门禁零违规）。批次收官项目。

## 1. git describe 标签对审计基线的误导（版本判定教训）
`git describe --tags` 返回 `4.0.0-RC2-29873-g6e3639ef5bc`——若直接采信会写错基线。
R1 network agent 经 pom.xml 核实实际为 **5.5.4-SNAPSHOT**（旧标签残留 + 大量 commit 后）。
**教训**：R0 基线必须 pom.xml/build 文件佐证，git describe 只作参考；任务书中的版本号
与 agent 核实不一致时以 agent 的 pom 核实为准并回填 R0 签收记录。

## 2. shipped 全注释 = 代码默认生效（最危险的 shipped 形态）
shardingsphere global.yaml 全部安全键为注释态 → 有效配置 100% 落到代码默认
（root/root + ALL_PERMITTED + 0.0.0.0:3307 + TLS 关 + 连接无上限）。
**教训**：shipped-config 三态盘点（active/comment/absent）中，「comment」不等于「不可达」——
missed-default 机制（GlobalRulesBuilder）使注释态必然激活代码默认。
批次 shipped 姿态排序：tomcat（收紧）＜ zookeeper/kafka（样例弱配置）＜ shardingsphere（注释=最弱）。

## 3. 复活攻击的正向价值：驳回也是收获
CAND-003 复活 agent 用 snakeyaml 2.2 字节码反汇编验证了覆写 getClassForName 的机械阻断
（Preconditions.checkArgument 仅接受 rootClass），驳回复活但提供了「白名单防御真实生效」的
最高强度证据（比静态 Read 更强）。**教训**：复活波对 UNREACHABLE 的复核成本低、信息量大，
即使不复活也产出防御机制的字节码级确认。

## 4. 协议层实证的分帧陷阱（MySQL codec 的 seq 字节）
实证攻击包三次未命中：MySQLPacketCodecEngine.decode 的 remainPayloadLength=SEQUENCE_LENGTH(4)
+payloadLength 要求 readable≥50 字节（46 字节包被卡在分帧等待）；且 createPacketPayload 不 skip
seq 字节导致字段解析整体偏移 1。最终以「多包聚合」面实证（16MB 声明包×24 连接 → RSS +1248MB，
~52MB/连接线性）绕过了字段级对齐问题。
**教训**：协议级实证先读 codec 的 framing 检查（isValidHeader/remainPayloadLength 的精确语义）
再构造包；字段级对齐难时优先选择不需要精确字段的攻击面（累积/聚合类）。

## 5. 主代理补边的合法性边界（机械边数规则 vs 合并边）
CAND-001（14 跳 12 边）/CAND-013（14 跳 10 边）被机械规则「edges ≥ chain-1」降级 static_only，
尽管合并边内 proof 文本覆盖全部相邻跳。主代理从 verifier evidence 文本拆分合并边补写
（by=main-agent-edge-split 标记），不伪造事实。
**教训**：合并边是 verifier 常见输出形态，机械数量规则会误伤；补边必须严格从 evidence
已有事实拆分并打标记，禁止新造调用关系。

## 6. 实证环境效率（构建时间账本）
- mvnw -T1C -pl distribution/proxy -am package 4.5min（无 tar）；assembly 在 release profile
  下才打 tar.gz（-Prelease 后 target/apache-shardingsphere-*-proxy-bin.tar.gz）
- 模块未 install 时 -pl 单独 package 报 DependencyResolutionException → 先 -am install
- RAT 检查会因 .audit_results 文件失败（-Drat.skip=true）
- JDK 25 构建 ShardingSphere 5.5.4 成功
- proxy 启动：bin/start.sh <port>（默认 0.0.0.0 绑定，start.sh 文档化）

## 7. R4 与 R3 的同事实双计（severity override 用例）
Groovy RCE 在 H4-F2（R4 finding, rce）与 CAND-009（R3 候选, rce）双报——同事实双计会把
CWE-94 机械映射为严重×2。主代理 severity_override=high + r3_link 同事实标注。
**教训**：R4 findings 与 R3 候选的同事实去重（r3_link + override 降档）是报告定级的必修步骤。

## 8. 目标形态教训（hybrid 签收的价值）
机械 target_kind 推荐 library（无监听器信号），主代理签收 hybrid（proxy=application +
jdbc=library）。H4-F4（MCP Class.forName 客户端可控）恰因 jdbc/host_api 边界与 MCP 组件
归属的区分被正确证伪（配置门控），而 proxy 面的 DistSQL 链按 application 规则全部成立。
**教训**：hybrid 签收 + 组件归属分层是「库形态误伤」与「服务器形态漏放」的双向防护。
