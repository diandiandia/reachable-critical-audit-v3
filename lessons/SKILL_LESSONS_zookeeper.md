# SKILL Lessons — zookeeper（2026-08-25）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = hybrid

### R3
- [grade_recomputed] CAND-002: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-003: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-006: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-007: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-010: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-011: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-012: 机械分级重算 (collect-mechanical-recompute)

### R3.5
- [verdict_correction] CAND-006: {'at': 'R3.5', 'from': 'REACHABLE', 'demote_to': 'NEEDS_REVIEW', 'decided_by': 'main-agent', 'rule': 'R3.5 多数决 1/2 分歧 -> 主代理裁决（skill: 保留但记录分歧理由，主代理裁决）', 'reason': 'R3.5 1/2 分歧，主代理采纳证伪方。结构性论证：follower 为 TCP 发起方，connectToLeader 只连静态配置视图(QuorumVerifier.getAllMembers)解析的地址；leaderIs 全库仅 Learner.java:356 
- [verdict_correction] CAND-007: {'at': 'R3.5', 'from': 'REACHABLE', 'demote_to': 'NEEDS_REVIEW', 'decided_by': 'main-agent', 'rule': 'R3.5 多数决 1/2 分歧 -> 主代理裁决（skill: 保留但记录分歧理由，主代理裁决）', 'reason': 'R3.5 1/2 分歧，主代理采纳证伪方，前提维度与 CAND-006 同一（leaderIs 注入面结构性封闭 + 文档化可信 quorum 前提）。**保留的实质**：TRUNC 分支对 leader 提供的 zxid 无单调性/合理性校验即 setLength 并删
- [verdict_correction] CAND-008: {'at': 'R5', 'field': 'claim_type', 'from': 'oom', 'to': 'other', 'decided_by': 'main-agent', 'reason': "R5 探针 C 实测后果不是内存耗尽（Xmx256m 下堆仅 26,423/20,366 KB，内存与快照大小成比例）。真实后果是数据完整性/孤儿节点污染：畸形 NUL 路径节点加载无错、可被裸协议 getData 读出(err=0 data='poisoned')、合法 API 因 validatePath 全部拒绝故无法删除、且跨新快照与重启持久。实证 agent 主动报告该偏差并建
- [verdict_correction] CAND-008: {'at': 'R5', 'field': 'cwe', 'from': '[CWE-20, CWE-400]', 'to': '[CWE-20]', 'decided_by': 'main-agent', 'reason': 'R5 探针 C 实测证伪资源耗尽后果（Xmx256m 下堆仅 26MB，内存与快照大小成比例），CWE-400(资源消耗不受控) 不再适用；真实后果为数据完整性/孤儿节点污染，CWE-20(输入校验不当) 保留。若保留 CWE-400 会使机械分级误判为『高』。'}
- [verdict_correction] CAND-011: {'at': 'R3.5', 'from': 'REACHABLE', 'demote_to': 'UNREACHABLE', 'decided_by': 'main-agent', 'rule': 'R3.5 多数决 1/2 分歧 -> 主代理裁决（skill: 保留但记录分歧理由，主代理裁决）', 'reason': 'R3.5 1/2 分歧，主代理采纳证伪方——证伪方提供实测，未证伪方自认『库内崩溃为机制级推断』，实测胜过推断。实测：对系统实装 Cyrus SASL 2.1.28 建 ASan harness 逐字复刻 zk_sasl.c:366 参数形态，核心断言 (NULL, -1→

## 主代理过程观察（人工补充）

- 【skill 缺陷·已修·最高优先】v3.7 报告渲染器静默丢弃 R4 申报 Critical 的 finding。根因两处：① `_r4_severity` 白名单 `("high","medium","low")` 漏 critical，申报值 Critical 落到机械映射兜底；② `_confirmed_issues` 过滤 `if sev not in ("high","medium")` 直接 continue。铁证是同函数内 `_render_problem_list` 的 `grouped = {"critical":[], ...}` 给 R4 条目留了**永不可达**的 critical 桶。实录：本次审计严重程度最高的一条（C 客户端 jute vector 反序列化 calloc 无判空，实测 SIGSEGV 139 / OOM-kill 137）差点不进问题清单。已修两处白名单并跑 tests/ 全绿（216 passed, 2 skipped）。教训：机械渲染层的『过滤白名单』与『分组桶』必须有一致性测试，否则整档严重度会静默消失。
- 【skill 缺陷·未修】`assert_ledger` 的 r4_feedback key:value 冲突检测产生系统性伪报。它把证据文本里的 `<文件名>.java:<行号>` 后缀误切成 key="ava"、value=行号，于是不同文件的行号在互相比对（本次报出 CAND-005/008 与 H7 在 key='ava' 上 50/32/42/658 vs 37 的『冲突』）。任何遵守『每条论断带 file:line 取证』纪律的审计都必然触发。建议 key 提取排除 `\.(java|c|h|py|go|rs|kt|scala|ts)\:\d+` 形态。
- 【skill 缺陷·未修】R1 `surface_mapper.py validate` 对含 HTML 实体转义的 C 文件比对退化。`_r1_boundary.json` 通过了 validate，但其 `ia_deserialize_buffer` 的三个锚点行号整体偏移 1（243/247/251 应为 244/248/252，其中 247 是注释行 `// set the buffer to null`）。该错误直到 R2 阶段 `r2_guard.anchor_check` 才暴露（锚点行是注释→退化候选）。同一份产物里 zookeeper.c 与 ia_deserialize_string 的行号却是对的，说明退化只发生在 snippet 含大量 `-&gt;`/`&lt;` 实体的条目。建议 validate 在实体反转义失败时降级为『拒收』而非『放行』。
- 【编排模式·可复用】薄封装 fileref 模式解决 Mode W 的 payload 上下文开销。导出脚本要求 `args={"candidates": <payload>}` 整传，12 候选的 payload 达 24.8KB；跨『验证波+证伪波+复活波』× 多项目批次，payload 会成为编排层上下文的主导开销。做法：把逐候选任务书落盘为 `_verify_task_<ID>.md`，另写一个薄封装 workflow 脚本（**原样复用导出脚本的 SCHEMA 常量与返回契约、tooling_version**），agent prompt 只说『第一步用 Read 读取 <taskFile> 全文并严格执行』，args 只传 `{id, taskFile}`。实测 args 24.8KB→1.2KB（-95%），schema 强校验与 collect 契约完全不变。注意：这依赖 workflow 内 agent 有 Read 工具（skill 原文『workflow 内 agent 无文件系统』指的是不能写心跳文件，不是不能读）。
- 【机制价值·意外收获】证伪者可能反过来补强候选。CAND-001 的证伪者 #1（视角=前提维度与阻断幻觉）未能证伪，却自行构建真实 3.10.0 C 客户端 + 伪造服务器做了 E2E 实证（VmSize→2.15GiB, RSS 10MB→270MB 持续 >9s），把候选从 static_only 抬到 empirically_confirmed，并给出归因修正（握手 primer 阶段有界，触发窗口严格在握手完成后）。说明 N=2 差异化视角的产出不限于 kill/keep 二元，`strengthened` 与 `attribution_correction` 字段承载了真实增量。
- 【机制价值】两次 R3.5-N 均为『诚实的失败复活』，但价值不在复活本身：① CAND-012 的复活者**证伪了 R4 H5 的机制描述**——H5 称 root 节点 ACL 为 null 使 checkACL 空表短路，实际 root 的 acl=-1L 是 OPEN_UNSAFE_ACL_ID，convertLong 返回 world:anyone:ALL（非空表），放行发生在 world:anyone 精确匹配。后果相同但定性从『鉴权门失效』改为『默认开放语义』。② CAND-011 的复活者发现 `len<-1` 会触发 ASan allocation-size-too-big abort，但**主动标注这是插桩策略产物而非生产行为**（allocator_may_return_null=1 下全干净），拒绝拿它凑复活。任务书里『不得伪造复活，诚实的失败复活与成功复活同等有价值』这句话有实效。
- 【裁决实录】实证驱动的 claim_type 修正必须允许。R5 探针 C 实测后主动报告『CAND-008 的后果不是内存耗尽』（Xmx256m 下堆仅 26MB，内存与快照大小成比例），真实后果是数据完整性/孤儿节点污染（畸形 NUL 路径节点可被裸协议 getData 读出 err=0，合法 API 因 validatePath 全部拒绝故无法删除，跨新快照与重启持久）。主代理据此把 claim_type oom→other 并移除 CWE-400——**若不移除，机械分级会经 RESOURCE-DOS 族把它误判为『高』**。任务书里预先写入『如果实测表明后果不是 X，请如实说明并建议修正 claim_type，不要为迎合 claim_type 编造数字』是这条能发生的前提。
- 【方法论】跨 agent 冲突是质量信号而非噪音。本次登记 4 条 r4_feedback 冲突：3 条经主代理逐行核实后判定『后来者正确』（H5 的 CommandListener 通配绑定推翻 R2 筛选 agent 的 drop 理由；复活者推翻 H5 的 root ACL 机制；R3 CAND-002 与 R4 H2 对负长度路径各自成立一半），1 条为机械误报。单一 agent 的自洽远不如多 agent 独立作业产生的冲突有信息量——但前提是主代理必须**逐条回到源码裁决**，不能按『谁后说谁对』或『取交集』处理。
- 【降噪实测】签名佐证器在服务端 Java 项目上的表现：228 条签名假设 → 14 条 keep（94% 降噪），且 keep 全部收敛到 3 个真实 sink，与 LLM 主路径（20 条假设）**独立收敛到同一组 sink**，构成交叉印证。但 L1 通用词噪音仍是主要成本：C++ `<<` ostream 流插入被判『无界累积』、`Thread.getName()` 的 `read` 子串撞词、`load_gen.c` 里名为 realpath 的**局部缓冲区变量**被判『路径白名单』。建议 L1 词族对 `.cc/.cpp` 排除 `<<`、对 Java 排除 `getName/setName/currentThread` 上下文。
- 【形态判定】target_kind 机械推荐需要主代理实质复核而非橡皮图章。本项目机械推荐 application（app 3.8 / lib 0），但其证据引用的是 C 客户端 `mt_adaptor.c` 的监听与一个 GUI 面板类，未命中真实服务端入口。复核后签收 hybrid：`zookeeper-server` 是 application 组件，`zookeeper-client-c`（zookeeper.h 有 114 个 ZOOAPI 公共符号 + CMakeLists/Makefile.am）是 library 组件。若按 application 装载，C 客户端候选会被『仓内无调用者』错误阻断——而本次严重度最高的 3 条全部在 C 客户端。同理 maturity 机械值 unknown 是标签格式误判（release-3.9.5 非 vX.Y.Z），实际 184 个 tag，覆盖为 mature 后才触发 R4 与 R3 并行 + H1/H7 深度上调。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
