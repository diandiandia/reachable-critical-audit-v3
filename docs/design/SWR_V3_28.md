# SWR_V3.28 — Top15×Top10 目标物化

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.28-001 | inventory 资产：每语言排序问题清单条目 {id, lang, title, family, cwe, pattern, sink_hint, pitfall, source{tier, origin, date}, verify{status, battles, candidates, date}} | D-1。Top10 的单位承载；rank 机械计算不落盘 | test_v328: 加载/字段完备/lang 枚举校验 |
| SWR-V3.28-002 | 加载器 `inventory <lang>` 命令：按 (族严重度档, cwe 最大严重度, id) 机械排序输出 | D-1。排序确定性、零落盘 rank 漂移 | test_v328: 排序断言（MEMORY-SAFETY 先于 CRYPTO 等） |
| SWR-V3.28-003 | 加载器 `goal` 命令：每语言 {entries, gap_to_10, tier 分布, battle_confirmed 数} + K1/K2 里程碑进度 | D-3。闭环设定值视图 | test_v328: 数学断言（gap=10-entries、进度分母 16） |
| SWR-V3.28-004 | 加载器 `seed <file>` 命令：外部种格——强制 source.tier/origin/date、lang 枚举校验、cwe 格式校验、去项目化扫描、幂等拒绝（lang+title 重复） | D-2。第二通道；来源标注=诚实性保证 | test_v328: 合法种子入库 + 四个反面分支（缺出处/项目名/坏 lang/重复） |
| SWR-V3.28-005 | 回填升档条款（P3 提示级）：验收收官把确认问题 cwe 命中条目 verify 升档 battle_confirmed（battles/candidates/date 落盘） | D-4。条目级验证追溯；提示级不建机制 | SKILL.md 增量段含条款文本 |

## 裁决层边界声明（SYSTEM 层,非 SWR）

inventory 是**提示层资产**：external_seeded 条目不得进入先例库/清单库等裁决
资产（现状已如此——裁决资产只从战役 lessons 两段式提炼收，无需新机制；
本声明为显式边界，防未来误操作）。矩阵 cells 路径与 R2 消费契约零变化。

## 四缺陷评估

- ①盲目带入：34 条目全部派生自已种格真实溯源（source_lessons 原样引用）；
  QuickJS 实证候选 id 只写本会话可证条目；旧战役不可溯条目 verify=unverified
  （诚实）✓
- ②设计偏见：无自动改写；seed 显式命令 + 幂等 ✓
- ③死代码：新命令消费者=主代理战略盘点/验收报告；inventory 视图消费者=goal ✓
- ④过设计：零新门禁、零流水线改动、rank 不落盘、K1/K2 不设自动阻断 ✓
