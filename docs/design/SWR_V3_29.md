# SWR_V3.29 — 闭环接线

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.29-001 | goal 输出增 priority 段:per_lang 按 gap 降序排列 + top_gap_languages 选题建议(前 3) | D-1。控制器消费端;gap 即误差信号 | test_v329: 排序断言(gap 大者在前) |
| SWR-V3.29-002 | hitrate CLI:`hitrate <lang> <cwe,...>` → {total, hits:[条目 id]} | D-3。输出反馈度量;只读零改写 | test_v329: 数学断言(命中/未命中/未知语言) |
| SWR-V3.29-003 | seed 双写矩阵:入库 inventory 同时更新 cells(缺格建格 status=seeded/补 pattern 去重/并 cwe/补 source_lessons) | D-5。传感器一致性;cwe→family 映射与账本同口径(表在模块内) | test_v329: inventory 条目 ⊆ 矩阵格 pattern 一致性断言 |
| SWR-V3.29-004 | 试点种格数据:2025 CWE Top 25 真实源,16 语言 × 映射,156 条目,origin 带 URL+rank | D-2。执行器内容;诚实纪律全过 | test_v329: 192 总数 + K1 16/16 + 条目 origin 含 cwe.mitre.org |
| SWR-V3.29-005 | SKILL.md 条款:R2 假设生成读 cells + inventory 排序条目(P3 提示级);R6 收官记录命中率(P3 提示级) | D-4/D-3。接通与反馈的条款载体 | test_v329: SKILL.md 含两条款文本 |

## 四缺陷评估

- ①盲目带入：试点条目全部来自 WebFetch 取证的真实榜单,title=CWE 官方名,
  origin 带 URL+rank;语言映射为设计件记录的保守判定,零项目名 ✓
- ②设计偏见：hitrate 只读;seed 幂等;条款提示级不建义务 ✓
- ③死代码：priority/hitrate 消费者=主代理选题/收官复盘;双写消费者=一致性测试 ✓
- ④过设计：零新门禁;K1 达标不设自动阻断;映射表只做数据不做机制 ✓

## 实现期重跑（阶段 7 义务）

- 试点条目正文键(title/pattern/pitfall)零项目名(grep 断言)
- origin 全带 URL;verify 全 unverified(不伪造 battle_confirmed)
- 双写后矩阵与 inventory 一致性测试过;守卫 ×19 全同步
