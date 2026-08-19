# Reachable Critical Audit v3.3.2 — 软件设计（组件级）

> 从 `SYSTEM_DESIGN_V3_3_2.md` 导出的组件修改设计。日期：2026-08-19
> 最高判据：SKILL.md「第一原则：通用型 Skill」——本版全部组件修改都必须通过
> 自检四问（去项目名 / 语言无关或按 lang 分派 / 无具体项目路径 / 新项目验收）。
> 版本主题：**先裁后接**——修复载体时不得把过设计坐实（③b 结构化与收窄捆绑、
> H7 收缩先于 r4_feedback 接线）。

## 组件影响清单

| 组件 | 修改点 | 承载 REQ |
|---|---|---|
| M1 evidence_ledger.py | ①assert_ledger gate ③ 前置 `verdict=="REACHABLE"` ②commit 的 demote_to 分支清 claim_type + claim_nulled_by ③grade_verdict 的 empirical status `.lower()` 归一化 + 不一致告警 ④③b 改读 R4 finding 结构字段（empirical_result/claim_type），强制范围收窄至 Medium+/forced-claim 类，Low 接受 source_fact/机制级，关键词匹配降 fallback warn ⑤新增复活改判检查：候选带 re_verify_gap 且 verdict=REACHABLE 且无 refutation 字段 → 违规 ⑥r4_feedback 消费者接线：读收缩后的 H7 结构化表与 R3 gate 证据 key:value 比对产出 warn | REQ-V3.3.2-010/011/009/012/006/013 |
| M2 batch_verify.py | ①`--from-journal` 增 `--expect <ids>` 全集校验（不足/多余报错不落盘）②新命令 `--stage r35-collect --from-journal`：refutation decisions → evidence_ledger.commit 落候选 refutation 字段 ③新命令 `--stage coverage`：tracked 计算 + id 归一化 + unknown 告警，输出即 assert_ledger 的 surface_data ④新命令 `--stage grade-recheck`：批量逐候选 grade_verdict，差异写 grade_recomputed_by ⑤IMPORTABILITY_STEPS 按 target_kind/语言门控（动态导入风险语言或 application 注入完整预检；静态编译语言降为 build 列表一行核对）⑥r4-collect 对 tracked_surfaces 经 norm_surface_id 归一化后未知 id 告警 | REQ-V3.3.2-002/007/015/017/019/016 |
| M3 workflow_export.py | ①verify 模式读候选 re_verify_gap 自动渲染「复活复核 gap」段（挂 _checklist_section 同扩展点，无 gap 不渲染）②resurrect 模式落盘抽样决策（selected/unselected/rule）③三模式 script 返回补 project + dispatched_ids 字段 ④self_refutation_hints 精度门：cwe/语言/sink 类三重过滤，匹配不足不注入 | REQ-V3.3.2-014/004/003/020 |
| M4 task_templates/ | ①biz_hypothesis.md：H7 default_value_table 收缩 schema（安全相关默认值 ≤10 项，{name, default, code_point, source_control, risk_dimensions(仅风险行), disposition}）+ R4 finding 增可选 claim_type + 义务入库三问说明段 ②verifier 任务书输出格式段加 claim 与实证自洽条款 | REQ-V3.3.2-018/012/022/008 |
| M5 surface_mapper.py | 定义共享 norm_surface_id 纯函数（SURF- 前缀剥离+去空格）；不产出/不持久化 id_aliases（可推导数据不落盘） | REQ-V3.3.2-016 |
| M6 SKILL.md | ①编排条款：每波派发后登记 wave_registry.jsonl（run_id/mode/project/dispatched/payload_hash）②R3.5 触发条款补「复活重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 池」③复活抽样口径对齐 REQ-V3.2-020/023 ④R2 签名 index/match 降为可选佐证器 ⑤R6 写明 write_lesson 幂等语义 ⑥「义务入库三问」写入 REQ 门槛节 | REQ-V3.3.2-001/005/024/021/022 |
| M7 harness_manuals/（环境陷阱节） | 环境能力探针清单：机制所需 syscall 探针（io_uring_setup 等）、依赖存在性（头/库/子模块物化）、工具存在性及替代（ss→/proc/net/tcp、time→getrusage）、shell 陷阱（zsh 展开、pkill 自匹配） | REQ-V3.3.2-023 |
| M8 REQ 修订表 | ①REQ-V3.2-021 增补「重验改判 REACHABLE 且 grade≥edge_proven → 强制入 R3.5 池」②REQ-V3.3 H7 表义务收缩 ③W6 §18.9（gate ③ 扩展 R4）收窄：Medium+/forced-claim 类强制，Low 接受 source_fact/机制级 ④REQ-V3.1-051 落盘位置收敛：候选 refutation 字段为权威，报告从队列派生 | REQ-V3.3.2-005/018/012/007 |
| M9 tests/ | 12 新单测：gate ③ verdict 条件 / demote 清 claim / status 大小写 / ③b 结构化与收窄 / 复活改判检查 / coverage 归一化 / gap 渲染 / 抽样决策落盘 / journal 全集校验 / 0.5 门控注入 / PREC 精度门 / r4_feedback 比对 | 全部 |

## 数据模型变更

1. **verify_queue 候选新增字段**（全部可选、lenient load 兼容旧队列）：
   `re_verify_gap`（正式化，复活 gap 文本）、`refutation: {by, demote?, strengthened?, poc_evidence?, note}`
2. **wave_registry.jsonl**（新文件，.audit_results/ 下 append-only）：`{run_id, mode, project, dispatched: [cand_id], payload_hash}`
3. **R4 finding**：+`claim_type`（可选）；`default_value_table` 收缩 schema（M4①）
4. **input_surface.json**：无新增字段（归一化为共享纯函数，不持久化）
5. schema_version 不动（增量字段走现有「只增改不覆写」merge 语义）

## 兼容性

- 旧队列（无新字段）全部路径行为不变；lenient load 与 merge 语义天然兼容
- assert_ledger 计数型 surface_data 调用（无 tracked_ids）保持原语义
- R0 selfcheck 语义不变（fixture 锚点召回 + 去项目化扫描不动——第一原则守卫）
- 0.5 门控后静态语言候选 prompt 变短 → resume 缓存键随 prompt 变化，跨版本边界可接受（W6 §5 resume 契约不变）
- 三锚点 fixture 回归 + 现有 98 测试全绿

## 实施批次（依赖顺序，对齐系统设计 §4）

| 批次 | 内容 | 依赖 |
|---|---|---|
| P1 正确性先行 | M1①②③、M4②——gate ③ 条件、demote 清 claim、status 归一化、claim 自洽条款（不依赖裁剪决策） | 无 |
| P2 裁剪 | M4①、M2⑤、M3④、M6④、M8②③——H7 收缩、0.5 门控、PREC 精度门、签名 R2 降佐证器 | P1 |
| P3 捆绑接线 | M1④⑤⑥——③b 结构化+收窄（捆绑）、复活改判检查、r4_feedback 消费者接线 | P2（先裁后接） |
| P4 载体 | M2①②③④⑥、M3①②③、M5、M6①②③⑤⑥、M8①④——wave registry、gap 渲染、抽样落盘、coverage/grade-recheck/r35-collect/--expect、SKILL.md 全修订 | P1（与 P3 并行可） |
| P5 验收 | M7、M9、三锚点复跑、新项目验收 | P1-P4 |
