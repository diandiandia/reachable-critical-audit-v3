# SYSTEM_DESIGN_V3_16 — 系统设计（2026-08-30）

## 变更边界（不变式）

- 阶段骨架、六门禁判据语义、队列数据模型主体——**全部不变**。
- 变更落在四类：告警/建议输出（D-1/D-5）、模板文案（D-2/D-4）、清单条目
  （D-3）。无新模块、无新门禁名、无新强制义务。

## 模块影响面

```
evidence_ledger.py     gate ③ + audit_constraint 建议条目   (SWR-V3.16-001)
task_templates/
  biz_hypothesis.md    verdict 枚举加粗 + 反面示例           (SWR-V3.16-002)
resources/
  checklist_library.json  CK-CHECKPOINT-AFTER-ACCUM + 条目   (SWR-V3.16-003)
workflow_export.py     PTM 块后 + 树外层清单条款 + TOOLING 3.16
                       (SWR-V3.16-004)
tools/batch_verify.py  coverage-ledger 写入后副本漂移 warn   (SWR-V3.16-005)
SKILL.md               v3.16 增量段
tests/test_v316.py     新增（约 7 用例）
tests/test_v310/312/313/39/314.py  版本守卫 → "3.16"
```

## 兼容性

- 旧队列复跑零新增告警：audit_constraint 字段缺省（旧队列无此字段）→ 建议
  零输出；D-2 模板变更不影响既有队列；D-3/D-4 为增量文本；D-5 warn 仅在
  双副本 sources 不一致时触发（修复后一致 → 零 warn）。
- 门禁判据不变：D-1 的建议条目为 warn 级附项，violations 主条目（阻断）
  语义与 v3.15 完全一致。
