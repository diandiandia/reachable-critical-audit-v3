# SYSTEM_DESIGN_V3_15 — 系统设计（2026-08-30）

## 变更边界（不变式）

- 阶段骨架（R0-R6）、六门禁判据语义、队列数据模型主体、signature/precedent/
  checklist 资产总体结构——**全部不变**。
- 变更是「判定函数一致化、模板/清单条款、告警结构化、消费契约」四类，全部
  落在既有模块内，无新模块、无新阶段、无新门禁名。

## 模块影响面

```
evidence_ledger.py   + is_claim_like()          (SWR-V3.15-002)
                     ③c 调用点改同函数
workflow_export.py   resurrect_pool 改同函数     (SWR-V3.15-002)
                     _TRUNC_KEY_HEAD 扩展        (SWR-V3.15-005)
                     refutation 资格分支 advisory(SWR-V3.15-004)
                     复活维度清单 +1 行           (SWR-V3.15-011)
                     PTM 注入块 +1 行             (SWR-V3.15-012)
                     TOOLING_VERSION → 3.15
batch_verify.py      报告守卫双形态 + 模板标记    (SWR-V3.15-001)
                     _tracked_ids dict 容忍(已热修,契约化) (SWR-V3.15-006)
                     scope_reopen_advice 优先 affected_dirs (SWR-V3.15-007)
                     R4_ENUM_WARNING 建议映射    (SWR-V3.15-003)
surface_mapper.py    scope_diff docstring 契约注 (SWR-V3.15-007)
resources/
  checklist_library.json  CK-EMPIRICAL-SCOPE +条目 (SWR-V3.15-009)
                          + CK-VENDORED-CONTRACT   (SWR-V3.15-011)
  precedent_library.json  + PREC-GUARD-SUBSET-001  (SWR-V3.15-010)
task_templates/
  biz_hypothesis.md   canonical 字段名条款        (SWR-V3.15-008)
  surface_map_domain.md 空域签收条款              (SWR-V3.15-008)
SKILL.md              v3.15 增量段 + R1 首行键/空域签收文案 (D-13/D-14)
tests/test_v315.py    新增（约 15 用例）
tests/test_v310/312/313/39.py  版本守卫 → "3.15"
```

## 数据流不变式

1. **claim 判定单真相**：`is_claim_like` 是「声称类」判定的唯一实现——
   复活池选样与门禁③c 义务判定从此同源（消除 v3.14 的双实现漂移）。
2. **截断语义**：关键段保留的语义不变；key 集扩展只增识别面；全 minor
   首尾拼接兜底保证证伪者/复活者永不再收 0 字证据。
3. **canonical 字段契约**：tracked_surfaces/hypothesis_tracked_surfaces=
   字符串 id 列表（消费：门禁⑦/报告渲染/_tracked_ids）；富形态证据改
   sweep_records（消费：人读追溯）。两形态在 _tracked_ids 等价。
4. **scope_diff 双通道**：affected_dirs=机器消费主通道；changes=人读描述。
   消费者不再解析人读形态（降级 fallback 保留）。

## 兼容性

- 旧队列复跑零新增告警：③c 与池判定统一后，旧队列（已有 resurrection_review
  或非声称类）行为不变；REPORT 守卫双形态对已编辑报告（含双形态任一标记）
  与未编辑模板（模板自带标记）均正确放行/拒绝；R4 告警仅增字段不改变告警
  语义；清单/先例新增条目对旧候选零绑定（词族未命中）。
- install 双副本同步：/root/reachable-critical-audit-v3（dev）与
  /root/.claude/skills/reachable-critical-audit（installed）同一变更集。
