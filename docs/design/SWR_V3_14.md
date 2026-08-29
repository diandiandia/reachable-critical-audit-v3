# SWR_V3_14 — 软件需求（v3.14 protobuf 复审计复盘缺陷修复）

> 对应文档：REQ_V3_14.md（需求语义）/ SOFTWARE_DESIGN_V3_14.md（改动点）。
> SWR 为可测契约：每条含断言式描述，测试实现见 test_v314.py。
> 原则：旧队列零行为变化；新增行为全部有触发条件。

## 1. 收集链（REQ-V3.14-001~004）

- **SWR-V3.14-001**：`_detect_journal_anomaly(transcript_dir, max_distinct_per_id=1)`
  默认行为与旧版一致；r35-collect 传 2 时同 id 2 个不同 result 不判 anomaly、
  3 个才判；r35n-collect 保持默认 1（同 id 2 个不同 result 判 anomaly）。
  既有测试 test_v3102.py:125-139（2 参调用）保持全绿。
- **SWR-V3.14-002**：unknown_surface_ids 非空时输出含 `suggested_corrections`
  映射（每 unknown id → 归一化 known 集最近匹配建议）；tracked_surfaces
  **不被自动改写**（收集后原样保留，主代理裁决）。
- **SWR-V3.14-003**：`_adapt_r4_finding` 对非空且非 `CAND-*` 形态的 r3_link
  写 `r3_link_invalid` flag；r4-collect 输出 warn；合法 CAND-* 与 null 零告警。
- **SWR-V3.14-004**：r4-collect 合并后，finding 带 r3_link 且 title/evidence
  含终态关键词（维持 UNREACHABLE/维持 NEEDS_REVIEW/维持 REACHABLE/demote）时，
  与候选当前 verdict 比对；矛盾输出 `r4_verdict_link_conflict` warn；一致零告警。
  不产生新 gate 名（test_evidence_ledger.py gate 套件零变化）。

## 2. 账本与复活抽样（REQ-V3.14-005/006）

- **SWR-V3.14-005**：coverage-ledger --write 幂等分支在 would_be_new_counts
  非空时输出 `manual_merge_guidance`（增量 FAM×LANG 清单 + 合并协议）；增量空时
  零输出；普通 --write 首次写入路径零变化（test_coverage_ledger_write_and_idempotent
  保持全绿）。
- **SWR-V3.14-006**：`export_script_resurrect` 先读 `_resurrect_sample.json`——
  文件存在且 selected/unselected 与当前 UNREACHABLE 候选集合一致 → 导出池以文件
  selected 为准；文件不存在或集合漂移 → 内部抽样并写文件（现状形态）。
  test_resurrect_sample_dump（selected 形态断言）保持全绿。

## 3. 提示资产与版本链（REQ-V3.14-007~009）

- **SWR-V3.14-007**：SKILL.md R1 步骤 2 含写盘能力指引句（「优先派发具备写盘
  能力的子智能体」+ UNWRITTEN 恢复引用）。
- **SWR-V3.14-008**：strengthen_unverified note 含字段名
  `strengthened_verified_by`/`attribution_correction_verified_by` 与层级描述
  （候选级 refutation dict 内，与 strengthened[] 平级）；SKILL.md 对应段同步。
- **SWR-V3.14-009**：TOOLING_VERSION == "3.14"；SKILL.md 含「🆕 v3.14 增量」段；
  test_v314 全绿且既有全量回归全绿（329 基线）；源仓库分 commit + install +
  安装版测试全绿。

## 4. 兼容与明确不建（回归护栏）

- 旧队列零行为变化（新行为全部条件触发：warn 仅在矛盾/异常形态出现时输出）。
- 不建自动 re-credit、不自动改写 tracked_surfaces、不加新门禁、不改裁决语义、
  sample 文件保持可选。
- ⚠️ 禁止运行 `tools/gen_tracking.py` 再生成 REQUIREMENTS_TRACKING.md（V3.14 段
  手工追加）。
