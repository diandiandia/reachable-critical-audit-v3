# REQ_V3_14 — 系统需求（v3.14 protobuf 复审计复盘缺陷修复）

> 对应设计文档：SYSTEM_DESIGN_V3_14.md。需求编号 REQ-V3.14-xxx。
> 每条含：语义 / 触发条件 / 消费者 / 案例支撑（三问已过，见设计文档 §3）。
> 本版不改变阶段骨架、六门禁判据语义、队列数据模型主体。
> 评估：BIAS_EVAL_V3_14.md（四缺陷评估随设计件）。

## 1. 收集链

### REQ-V3.14-001 journal 异常检测按 mode 形态区分（D-1）
- **语义**：`_detect_journal_anomaly` 增加 `max_distinct_per_id` 参数（默认 1）；
  r35-collect（refutation，N=2 证伪者同 id 多 result 是设计形态）传 2——
  仅当同 id 不同内容数 > 2 才判 anomaly；r35n-collect（resurrect，N=1）保持
  默认 1。verify 模式本就不跑该检查（现状保持）。
- **触发条件**：r35/r35n collect 时（恒）。
- **消费者**：collect 输出 journal_anomaly 告警（主代理据此裁决采信）。
- **案例支撑**：2026-08-29 protobuf 审计 2 次 r35-collect 均误报 journal_anomaly
  （"同 id 多 result 且内容各异"）——N=2 证伪者是设计形态，误报迫使主代理手工
  判「by-design」，告警可信度被稀释。

### REQ-V3.14-002 unknown_surface_ids 建议映射（D-4）
- **语义**：r4-collect 的 unknown_surface_ids 告警处，从归一化 known 集生成
  `suggested_corrections` 建议映射（后缀/词形最近匹配：S-DATA-001 ↔ SURF-DATA-001
  类跨前缀形态）——**仅提示，不自动改写** tracked_surfaces（误猜风险>收益，
  修正由主代理裁决）。
- **触发条件**：unknown_surface_ids 非空时（告警路径）。
- **消费者**：主代理 r4-collect 复核。
- **案例支撑**：protobuf 审计 H2×2 + H6×1 三处 SURF-DATA-* 前缀笔误，主代理
  逐条手工定位修复；既有前缀归一化（_map_surface_id）不覆盖 S- 前缀形态。

### REQ-V3.14-003 r3_link 值域校验（D-5）
- **语义**：`_adapt_r4_finding` 对非空且非 `CAND-*` 形态的 r3_link 写 flag
  （r3_link_invalid）+ collect 输出 warn 提示主代理裁决（置 null 或改指候选）。
  不阻断收集。
- **触发条件**：r4-collect 时 finding 带 r3_link（条件触发）。
- **消费者**：主代理 r4-collect 复核、报告渲染（无效 link 不参与同事实去重）。
- **案例支撑**：protobuf 审计 H2-F1 r3_link="HYP-001"（假设 id 误填为候选引用）
  静默落盘至报告，主代理事后手工置 null——gate ③d 只查非空不查值域。

### REQ-V3.14-004 R4 finding 终态表述与 r3_link 候选终态一致性检查（D-6）
- **语义**：r4-collect 合并后，finding 带 r3_link 时解析候选终态 verdict，与
  finding title/evidence 中的终态关键词（「维持 UNREACHABLE/NEEDS_REVIEW/
  REACHABLE」「demote」类）比对，矛盾输出 `r4_verdict_link_conflict` warn
  （字段级告警，非新门禁——六门禁判据语义不变）。
- **触发条件**：finding 带 r3_link 且 title/evidence 含终态关键词（条件触发）。
- **消费者**：主代理 r4-collect 复核、报告定稿前一致性核对。
- **案例支撑**：protobuf 审计 H4-F5（「维持 R3 UNREACHABLE」）与 CAND-009 终态
  （复活重验改判 NEEDS_REVIEW）矛盾——报告定稿前无任何机制拦截，靠主代理事后
  发现（工件修正随本版执行）。

## 2. 覆盖账本与复活抽样

### REQ-V3.14-005 复审计幂等分支增量指引（D-2）
- **语义**：coverage-ledger --write 的 LEDGER_IDEMPOTENT_SKIP 分支，在
  would_be_new_counts 非空时附结构化 manual-merge 指引：列出需合并的
  FAM×LANG 增量清单 + 手工合并协议（rows 合并 + sources 保持单条 + 注记
  manual_merge_note）。**不做自动 re-credit**（第二个复审计案例出现前不建
  自动语义——义务棘轮）。
- **触发条件**：幂等跳过且 would_be 增量非空（条件触发）。
- **消费者**：主代理收尾手工合并。
- **案例支撑**：protobuf 复审计 LEDGER_IDEMPOTENT_SKIP 后 STATExc=1 增量只能
  凭主代理摸索手工合并（manual_merge_note 事后补记），无协议可循。

### REQ-V3.14-006 复活抽样单真相（D-3）
- **语义**：`export_script_resurrect` 导出时先读 `_resurrect_sample.json`：
  文件存在且 selected/unselected 与当前候选集合一致（无已终态候选漂移）→
  以文件池为准；否则按内部抽样重新计算并写文件（现状）。文件保持**可选**——
  不存在时零新义务（内部抽样即默认路径）。
- **触发条件**：resurrect 导出时（恒检查，条件采用）。
- **消费者**：导出池、主代理抽样决策簿记。
- **案例支撑**：protobuf 审计主代理 sample selected=[004,009] vs 导出池
  [004,006,009] 冲突——文件 write-only 无人读，主代理被迫「以机械导出为准」
  改写自身决策；三权威（导出器/gate ③c/主代理文件）无单一事实源。

## 3. 提示资产

### REQ-V3.14-007 R1 派发写盘能力指引（D-7，一行指引非 SWR 机制）
- **语义**：SKILL.md R1 步骤 2 补一句——优先派发具备写盘能力的子智能体
  （允许写 `.audit_results/_r1_<域>.json`）；只读代理按落盘拦截契约 UNWRITTEN
  恢复（recovered_by）。
- **触发条件**：R1 派发时（指引性）。
- **消费者**：主代理编排。
- **案例支撑**：protobuf 审计 4/5 域 UNWRITTEN 转写 ~80KB 主代理上下文——
  根因是派发只读代理（编排选择），落盘拦截契约已覆盖失败形态，本项只补预防指引。

### REQ-V3.14-008 strengthen 签收指引文案（D-8）
- **语义**：strengthen_unverified gate note 与 SKILL.md 对应段补全字段名
  `strengthened_verified_by` / `attribution_correction_verified_by` 与层级
  （候选级 refutation dict 内，与 strengthened[] 平级，非 entry 内部）。
- **触发条件**：gate warn 触发时（文案）。
- **消费者**：主代理签收操作。
- **案例支撑**：protobuf 审计先签在 strengthened[] entry 内无效（gate 仍报），
  读 gate 代码才发现字段在 refutation dict 级——note 只写通配符 `*_verified_by`。

### REQ-V3.14-009 版本链
- **语义**：TOOLING_VERSION → "3.14"；SKILL.md v3.14 增量段；文档五件套；
  gen_tracking VERSIONS 登记 + REQUIREMENTS_TRACKING 手工段；既有守卫 5 处更新；
  新增 tests/test_v314.py。
- **触发条件**：版本发布（恒）。
- **消费者**：版本漂移守卫、test_doc_lint。
- **案例支撑**：v3.12/v3.13 同款先例。

## 4. 明确不做（义务棘轮防护）

- 不做自动 re-credit（D-2 第二案例再评）；不做 unknown_surface_ids 自动改写
  （D-4 误猜风险）；不加新门禁（D-6 为字段级 warn）；不把 D-7 升为 SWR 机制；
  不改六门禁判据语义；不触碰 revive/demote 裁决语义。
