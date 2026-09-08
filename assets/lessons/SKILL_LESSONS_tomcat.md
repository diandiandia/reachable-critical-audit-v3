# SKILL Lessons — tomcat（2026-08-25）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = hybrid

### R3
- [grade_recomputed] CAND-002: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-003: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-005: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-007: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-008: 机械分级重算 (collect-mechanical-recompute)

## 主代理过程观察（人工补充）

- 【韧性教训】API 连接中断导致 agent failed 不等于产出丢失。tomcat 一役 4 个 agent 因 Connection lost mid-response 报 failed，但 3 个在断线前已完成落盘（A_llm 14/14、C_len 51/51、D_misc 34/34 全部完整），真正丢失的只有 1 个（H1）。处理规程：先按铁律 1 重试 json.load 查磁盘，完整则直接采用，不完整才重派。重派时任务书加【每 2-3 条 finding 就覆盖写盘一次，不要等全部做完才写】。
- 【skill 缺陷·未修】R4 agent 产出非枚举 verdict（PARTIAL/REFUTED/REFUTED_HIGH/整句散文），r4-collect 不拦截，主代理需人工归一化。建议：r4-collect 对 verdict 做白名单校验，非法值输出 warn 并强制主代理填归一化值，或直接把部分证伪但仍有 confirmed finding 的语义写进任务书（当前任务书只写了三选一，agent 会自行发明第四值）。
- 【skill 缺陷·未修】R4 假说内部的自证伪条目会污染问题清单。H5 的 findings 里混入了 agent 自己的 [refuted]/[informational] 条目，且 severity 用了非法枚举 informational——渲染器把 Medium 的 refuted 条目当确认问题列进清单。主代理手工把自证伪条目 severity 降为 Low（进附录）并归一化 informational→Low。建议：任务书明确【证伪的断言不要写进 findings 数组，或写进 findings 时必须 severity=Low 并在 title 标 [refuted]】。
- 【裁决实录】severity 申报值偏高需要主代理校准。H7 的 F1(rejectSuspiciousURIs 默认 false)与 F2(encodedReverseSolidusHandling 不对称)申报 medium，但复活复核与筛选都证明 canonical 兜底使两者无实际绕过——校准为 Low（纵深防御硬化项）。H7-F3(版本指纹)保持 medium。校准依据是有无已知绕过，而非有没有缺口。
- 【降噪实测】签名佐证器在防御完备的成熟项目上边际价值趋零：tomcat 147 条签名假设仅 1 条 keep（94% 以上为噪音），且该 keep 与 LLM 主路径独立收敛。累积族/长度族全军覆没的原因是 tomcat 对每个远端驱动累积点都有 shipped 上限且均为分配前检查。启示：对 shipped 默认值收紧的项目，签名佐证器产出可预期地低，R2 预算应优先保证 LLM 主路径与 logic 假设的质量。
- 【证据形态】被复核的否定结论经得起更严的复核是高质量信号。3 个复活攻击全部诚实失败，但复活者纠正了 verifier 的多处定量错误（HPACK 续八位组 4→5、上限 2.68e8→2.147e9、ByteChunk 实例 10→15、漏列第三处安全修复 b33c09fd4c）——且每处纠正都让原判定更牢。诚实失败复活的产出不只是 revived 布尔值，attack/gap 字段里的定量纠正本身就是审计证据。
- 【形态判定】mechanical target_kind 在以库分发但本质是服务器的项目上系统性误判为 library（tomcat：app 0/lib 1.0）。根因：监听模式只匹配 new ServerSocket 而 miss 了 ServerSocketChannel.open()+bind。签收 hybrid 的证据链：NioEndpoint.java:491/494（application 侧）+ res/maven/tomcat-embed-core.pom（library 侧）。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
