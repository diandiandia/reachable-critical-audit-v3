# v3 编排架构评估：是否需要 Workflow + 如何保证候选完全验证

> **日期**：2026-08-16
> **问题 1**：对大型目标项目（万级候选/百级假设），skill 是否应使用 Workflow（确定性多智能体编排）？
> **问题 2**：如何保证每个待验证问题都得到完全验证（不遗漏、不静默丢失、不永久卡死）？

## 1. 实证背景：规模与失败模式

| 审计 | 候选规模 | 编排方式 | 暴露的问题 |
|---|---|---|---|
| WordPress | 54,786 → 932 验证 | 主代理手工 93 批循环 | 队列失控、JSON 损坏 1/4 批、API 中断 6 次 |
| Dubbo | 15,620 → 173 批 | 同上 | 1,124 条断言失败手工回填 |
| lighttpd | 10,097 → 200 簇 | 簇级手工 157 批 | 1 agent 失联（无心跳） |
| 10 语言战役 | 42,000+ | 手工家族复用 | 1 agent 60 分钟马拉松误判失联、双写竞态 |
| v3 集成测试 | 合成 1 候选 | 单进程函数调用 | — |

**共同模式**：批量验证是"确定性循环"（出队→验证→收集→再出队直到断言通过），而 v2.1 让
主代理（LLM，注意力会衰减）手工驱动这个循环——每批通知都进主代理上下文，42k 候选战役
的上下文压力与失联/损坏处理全部落在主代理身上。

## 2. 问题 1 评估：是否使用 Workflow

### 2.1 Workflow 能力与 skill 阶段的匹配度

| skill 阶段 | 形态 | Workflow 适配度 | 理由 |
|---|---|---|---|
| R1 输入面测绘 | 4 域并行 + 产出校验 + 合并 | **高** | 4 个 agent 并行（schema 产出 surface JSON）→ validate → merge，全确定性；背景注入由脚本参数传入 |
| R2 假设筛选 | 批量判定 keep/drop | **高** | 纯判定，schema 输出 `{keep, drop}`，pipeline 天然适配 |
| R3 批量验证 | 出队→验证→收集循环 | **最高** | 正是 Workflow 的 loop-until-dry + pipeline 模式；schema 校验自动重试替代手工"坏 verdict 重试" |
| R3 独立复核 | 对 REACHABLE 做对抗性证伪 | **高** | 文档化的 adversarial verify 模式（N 个证伪者多数决） |
| R4 假说 | 6-7 个并行 + 三选一 verdict | 中 | 可并行；但 H7 需要项目背景注入，参数化即可 |
| R5 实证 | harness 执行 + 结果写回 | 低 | harness 是外部进程操作（启动服务器/采样），脚本内 agent 不适合执行；实证编排留在主代理/工具层 |
| 裁决/迭代 | 复核冲突、追补、降级 | **不适用** | 需要 LLM 判断与上下文，留在主代理 |

### 2.2 结论：**是，但分层使用——Workflow 管"确定性的验证批处理"，主代理管"裁决与迭代"**

```
主代理（裁决层）: 输入面复核 / 冲突裁决 / 实证执行 / 报告
        │ 任务书 + 队列
        ▼
Workflow（执行层）: R1 测绘 fan-out → R2 筛选 pipeline → R3 验证 loop-until-dry
        │ schema 校验 + 自动重试 + 断点续传 + journal 记账
        ▼
结果回主代理（只读结论，不读过程）
```

**收益**（对照 §1 失败模式）：
1. **上下文隔离**：Workflow 结果落 journal 文件，主代理只读结论——42k 候选战役的上下文压力消失
2. **schema 强校验**：verifier JSON 经 StructuredOutput 工具层校验，不匹配自动重试——替代手工重试循环
3. **断点续传**：resumeFromRunId + agent 调用缓存（同 prompt 同 args 命中缓存）——队列的断点续传从"主代理手工维护"升级为"框架级"
4. **并发上限**：min(16, CPU-2) 并行验证——batch 效率问题（C5）从根源解决
5. **失败可见**：journal.jsonl 记录每个 agent 的实际返回值——失联/异常可事后审计

**代价与约束**（必须诚实）：
1. 脚本无 Date.now/Math.random——时间戳需 args 传入（小约束）
2. 脚本是固定模板——验证过程中的自适应追问（verifier 发现意外 → 主代理追补）不能发生在 workflow 内；异常候选升级回主代理处理
3. Workflow 是 Claude Code 原生——平台兼容层需新增 Mode W（opencode/Antigravity 降级回 Mode A' 手工循环）
4. 嵌套一层限制——R3 内再嵌 workflow 不行（也不需要）

## 3. 问题 2 评估：完全验证的保证机制

"完全验证"拆解为三个正交要求：**闭环**（无 PENDING 残留）、**无静默丢失**（每个任务有明确终态）、**质量**（verified ≠ 随便验证过）。

### 3.1 已有机制（v3 已实现）

| 机制 | 覆盖要求 | 状态 |
|---|---|---|
| 队列状态机 PENDING→VERIFIED + no_pending 断言 | 闭环 | ✅ 已实现（assert_ledger） |
| 优先级出队（P0 先验） | 闭环（高价值优先） | ✅ 已实现 |
| 部分成功落盘（坏 verdict 不丢批） | 无静默丢失 | ✅ 已实现 |
| NEEDS_REVIEW 显式列出 | 无静默丢失 | ✅ 已实现 |
| evidence_grade 分级 + 边证据强制 | 质量 | ✅ 已实现 |
| 心跳 pending 文件 + 落盘冲突检测 | 无静默丢失 | ✅ 已实现 |
| 簇级广播 + exceptions 覆盖 | 闭环（成员逐一有终态） | ✅ 已实现 |

### 3.2 缺口与补强设计（需要新增的保证）

| 缺口 | 后果 | 补强机制 |
|---|---|---|
| **G1 失联无超时**：agent 60 分钟马拉松/永久挂起，候选卡 PENDING | 闭环破口（主代理不发现则永久卡死） | 任务书携带 deadline 约定（如 30 分钟）；workflow 层 agent 调用有完成通知；**对账阶段**：任务清单 vs 产出文件，未产出 → 自动重派（重派次数上限后升级主代理） |
| **G2 重试风暴**：坏任务书导致同一候选无限重试 | 资源浪费 + 队列永不收敛 | 每候选 attempt 计数（队列字段），≥3 次失败自动升级主代理手工裁决并记录 `escalated`——"显式未决"优于"静默重试" |
| **G3 verified ≠ 验证质量**：弱 verifier 草率判 UNREACHABLE | 漏报（最危险的"完全验证"假象） | **独立复核**：REACHABLE（edge_proven+）判罚金标准——workflow 内 N=2 证伪者对抗验证（多数决）；critical 声称强制实证（已有 empirical_required 门禁） |
| **G4 覆盖完整性**：队列本身不完整（surface 未全测） | 队列验证 100% 但审计不完整 | 输入面覆盖率门禁（REQ-V3-071 设计已有，需在 workflow 闭环中执行：surface 数 vs 已追踪 surface 数 =100% 才允许关闭队列） |
| **G5 workflow 中断**：kill/崩溃时已发任务丢失 | 进度丢失 | resumeFromRunId + agent 缓存（框架级）；队列本身是唯一事实源（workflow 崩溃不影响 queue 已落盘部分） |

### 3.3 完整保证链（终态设计）

```
候选生命周期（每个候选必经以下之一，无一例外）:
  PENDING ──验证──▶ VERIFIED{REACHABLE|UNREACHABLE} [evidence_grade≥edge_proven]
                 │   └─ REACHABLE → 独立复核(N 证伪) → 通过/降级
                 ├─▶ NEEDS_REVIEW  → 报告显式列出（人工裁决）
                 ├─▶ escalated     → 主代理手工处理（attempt≥3 后强制）
                 └─▶ (对账) 任务有产出文件 + journal 有记录 = 有终态
关闭判据（assert_ledger 扩展）:
  ① no_pending        ② REACHABLE 无 static_only
  ③ 实证类声称 100% empirically_confirmed
  ④ 对账零差异（任务清单 == 产出清单）
  ⑤ surface 覆盖率 =100%（G4）
  ⑥ escalated 计数 =0（或主代理显式签收）
```

## 4. 落地建议

1. **平台兼容层新增 Mode W**：`Workflow` 工具可用时，R1/R2/R3 的批处理生成 workflow 脚本
   （`batch_verify.py --stage workflow-script` 从队列导出 loop-until-dry 脚本）；
   Mode A'（手工循环）保留为降级路径
2. **队列 schema 扩展**：候选增加 `attempt` 计数与 `escalated` 状态；assert 扩展 ④⑤⑥ 门禁
3. **独立复核模板**：task_templates 增加 `verifier_refutation.md`（N=2 证伪者多数决）
4. **新增需求**：REQ-V3-090~095（编排与完整性），追踪矩阵同步
