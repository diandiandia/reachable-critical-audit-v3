# SYSTEM_DESIGN V3.45 — 变更边界不变式

## 不变式 (本周期不触碰)

1. **阶段骨架零改动**: R0-R6、六门禁判据语义、R3.5/R3.5-N/R4/R5 流程形态不变。
2. **队列数据模型主体不变**: verify_queue 候选字段集不变 (D-7 只新增
   claim_self_reported 追溯字段, 无消费端语义变化; D-3 只新增 resurrection_review
   的标记字段)。
3. **零新门禁名、零新强制义务**: 全部修复为 warn 级/提示级/容错级。
4. **零自动改写**: D-1/D-8 只 warn; D-4/D-2 归一化仅限形态别名 (hypothesis 键
   与 canonical 同权), 与 SWR-V3.4.3-001 四类漂移自适应同形态。
5. **旧队列复跑零新增告警**: 所有 warn 的触发条件为新形态输入才成立; 旧队列
   (quickjs/servo/haproxy/gpac) 无该形态 → 零变化。

## 模块影响面

| 模块 | 变更 | 影响 |
|---|---|---|
| src/surface_mapper.py | D-1 merge 计数前缀匹配 + validate type warn | merge/validate 输出 +1 warn 类型 |
| tools/batch_verify.py | D-2/D-3/D-4/D-5/D-7/D-8/D-10 | collect 告警/容错/归档 + verifier 任务书文本 |
| tools/target_profile.py | D-6 新探针 S7 | 推荐 empirical_modes 非空 (主代理签收后生效, 零强制) |
| src/workflow_export.py | D-11 resurrect_prompt 文本 | 任务书文本 |
| assets/task_templates/biz_hypothesis.md | D-9 三条款 | R4 任务书文本 |
| assets/task_templates/hypothesis_filter.md | D-12 | 筛选任务书文本 |
| SKILL.md | D-13/D-14/D-15/D-16 四条款 | 提示级条款 (正文节 + 附录资产计数) |

## 兼容性

- Python 3 标准库 only; 无新依赖。
- 回归锚点 (tests/fixtures/known_instances.json) 零改动。
- canonical 输入零变化: 所有归一化/容错仅在漂移形态输入时激活
  (SWR-V3.4.3-001 同先例: "canonical 输入零变化 (回归锚)")。
- 版本守卫测试行 (test_v314/v315/v310 等含 "3.44" 断言) 逐处同步为 3.45。

## 风险与对策

- D-5 告警收窄可能漏掉"informational 标题 + Low" 形态: hint 已要求 [refuted]
  标记, 非合规形态仍告警 → 无漏。
- D-6 探针误报 (树内 Image 存在但不可引导): 提示级建议 + 主代理签收, 零强制
  消费 → 无风险。
- D-3 覆写语义: 仅 journal 真决策可覆写 auto_bookkept 占位; 旧记录 (无标记)
  保持跳过 → 幂等语义不回归。
