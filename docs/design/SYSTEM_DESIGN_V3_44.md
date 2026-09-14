# SYSTEM_DESIGN_V3_44 — 变更边界与模块影响面

## 变更边界不变式 (守住, 与 v3.42/v3.43 同形)

- **阶段骨架零改动**: R0-R6 阶段顺序/触发条件不变
- **六门禁判据语义零改动**: gate ③c 的 presence 判据不动 (D-1a 修的是簿记
  写入侧, 不触碰 gate 判定); gate ③ 触发集不变
- **队列数据模型主体零改动**: 候选字段/VERDICT_SCHEMA/REFUTATION_SCHEMA/
  RESURRECT_SCHEMA 均不动
- **判定逻辑零改动**: assert_ledger/severity_for/grade_verdict/is_claim_like/
  resurrect_pool 本体不动 (冻结守卫 hunk 检查锚定, SWR-V3.44-008)

## 变更清单与影响面

| 变更 | 文件 | 影响面 |
|---|---|---|
| D-1a auto-bookkeep 跳过声称类 + warn | tools/batch_verify.py stage_r35n_collect | 只影响「声称类未选中」路径的输出: 不写簿记 → gate ③c 持续违规 (预期行为); 非声称类零变化 |
| D-2/D-6 verifier prompt 三句 | tools/batch_verify.py _build_prompt | 提示级文本, 不改变输出 schema 与裁决规则 |
| D-1b/D-3/D-4/D-7 SKILL.md 四处条款 | SKILL.md | 提示级条款, 无新强制义务/无新门禁 |
| D-8 版本链 + 冻结守卫基线 | src/workflow_export.py (TOOLING) / tests/ | 机械步 |

## 兼容性

- 旧队列复跑: r35n-collect 对旧队列的声称类候选行为变化 = 不再写「未选中」
  簿记 → 旧队列若从未跑复活 (v3.2 机制发布前产物, require_resurrection=False
  豁免) 不受影响 (豁免路径不查簿记); v3.2 后队列的声称类候选本就应已复核。
  非声称类簿记照旧 → 代表项目队列 (gpac/freetype/av) 复跑零新增告警预期成立。
- 断言输出结构: R35N_COLLECTED JSON 增 claim_like_unreviewed 字段 (附加字段,
  消费端容忍)。
- workflow 脚本产物: 零改动 (RESURRECT_SCRIPT 模板不动)。

## 依赖与次序

P1 (D-1a) 独立; P3 prompt (D-2/D-6) 独立; SKILL.md 四处条款独立;
P4 版本链最后 (依赖前两者完成)。无跨项耦合。
