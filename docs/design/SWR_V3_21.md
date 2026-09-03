# SWR V3.21 — 设计规则（2026-09-03）

## SWR-V3.21-001（D-1 探针→可行性路由前移）

SKILL.md R0 探针条款段后增三句（条款级，无新工具）：
1. 探针落盘后、R3 派发前，主代理输出 empirical_feasibility 表——每候选
   三轨（real-target / equivalent-harness / static-only），R3 任务书按轨
   注入实证路径预期；R5 的 harness 目标清单在 R3 定，不在 R5 现找。
2. 探针含 no-* 关键运行面缺失项时，R3 派发前向用户报预期 NEEDS_REVIEW
   占比并给三选一决策点（补装运行库 / 借运行面 / 接受上限）——决策权在
   用户，主代理不得代选。
3. static-only 轨候选的证伪票价值=机制静态确证（非浪费），派发时明示。
测试：SKILL.md 含三句关键词；反面分支（条款不要求机械强制——表为笔记级
产物，不落 schema）。

## SWR-V3.21-002（D-2 R1 谓词矛盾扫描）

SKILL.md 报告定稿前条款（六门禁前）：
- 对每个 REACHABLE finding，检查其是否否定任一 R1 surface 条目的阻断
  谓词（拒绝/拦截/白名单/过滤/仅允许/不允许类结论）。命中即生成
  contradiction record（surface id + 被否定谓词 + finding 证据引用），
  并按缺口闭合流程反向测绘该面。
- 机械辅助清单（固定 grep 命令形态，文本级）：谓词关键词
  `拒绝|拦截|白名单|过滤|仅允许|不允许|禁止` × 每个 REACHABLE finding 的
  sink 文件与调用链文件，逐对复核——语义判定由主代理裁决，不做自动改写。
测试：SKILL.md 含条款与 grep 关键词清单；反面分支（无"自动改写/自动降级"
字样）。

## SWR-V3.21-003（D-3 lessons 回填断链三连修）

1. **P1 recorder**：`lessons_recorder.render` 的"待回填"段改写——价值判定
   必须在审计收官落盘 `<project>/.audit_results/lessons.md` 时同步完成：
   高价值条目去项目化后并入「对 skill 的教训」节（skill-optimizer 唯一读
   入口），低价值条目保留本文件作审计轨迹；本文件不承载待办。移除
   W6_MORE_LANGS_FINDINGS.md 指向（v3.16.1 已冻结的历史档案不可写）。
   测试：render 产物无"待回填"字样、无 W6_MORE_LANGS_FINDINGS 字符串、
   含"审计轨迹"与 lessons.md 落盘位措辞。
2. **P3 SKILL.md R6**：蒸馏与收官同周期绑定——价值判定必须在报告闭合前
   完成，禁止悬空待回填；SKILL_LESSONS_*.md 只作机械证据，不承载待办。
3. **P3 skill-optimizer 阶段 0**：DDL 消化条款——机械清单每份 lessons.md
   的「对 skill 的教训」条目，必须在本次启动的缺陷清单中出现或显式裁除
   （附理由），不得静默跳过。测试：skill-optimizer SKILL.md 含该条款
   （测试经 $HOME 探测路径，不入运行时正文）。

## 通用约束（本版全部 SWR 适用）

- 零新工具/零新阶段/零新门禁/零新强制 schema/零自动改写——全部条款级。
- 去项目化：运行时正文零项目名/零候选 id（"CAND-019 形态"不入 SKILL.md，
  以"实战已发生"形态承载；案例归属进 source_lessons 追溯与设计件）。
- 跨 skill 修改仅限 skill-optimizer SKILL.md 阶段 0 一段（其唯一读入口
  语义的 DDL 强化，不改变既有枚举义务）。
