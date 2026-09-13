# SWR_V3_43 — 机制冻结实验 + 知识补种 + 架构体检 SWR

## SWR-V3.43-001（K-1 c 矩阵 TRUST-BOUNDARY/PAGE-CACHE-OWNERSHIP 族）

- 裁决：c 语言矩阵新增 TRUST-BOUNDARY 族条目「零拷贝/in-place 优化所有权」，
  tier=external_seeded（origin=2026 年 Linux kernel CVE 公开披露族分析，
  date=2026-09-13）。patterns 覆盖 splice 植入页/skb fragment/scatterlist
  外部支撑内存的 in-place 写；sinks 锚定 splice/vmsplice/pipe_buffer/skb
  frag 槽/scatterlist 写点；pitfalls 含「外部支撑页 in-place 写 = 越权写」
  判定要点与「优化路径所有权建模对比矩阵」检查项。
- 理由：2026 年 9+ kernel LPE CVE 的共性根因，矩阵零种子 = 发现纯靠碰运气。
  该族与 H4 site-isolation 资源归因子条形成「假设空间种子 × 深挖通道」互补。
- 测试守卫：tests/test_v343.py::test_matrix_pagecache_seeded +
  ::test_hitrate_pagecache_query（hitrate 查询 CWE-787 应命中新条目）。

## SWR-V3.43-002（K-2 java 矩阵 10 格补种）

- 裁决：Keycloak hitrate 未种的 10 个 CWE 按族归并补种（battle_verified，
  source=Keycloak lessons）。归并形态：CWE-117+532→INJECTION 族日志注入条目；
  CWE-290+287→AUTHN 族信任代理欺骗条目；CWE-367+362+613+294→RACE 族
  时序窗口条目（367 TOCTOU/362 竞态窗口/613 会话过期/294 重放归一族）；
  CWE-476→ERROR-HANDLING 族；CWE-704→NUMERIC 族类型混淆；CWE-789→
  RESOURCE-DOS 族（java 形态无界集合累积）；CWE-303→AUTHN 族撤销策略
  未生效条目。不逐 CWE 单开条目（族归并纪律——矩阵是假设空间提示器不是
  CWE 索引）。
- 理由：hitrate 7/18 的 10 格缺口是本审计过程观察 7 的显式待办。
- 测试守卫：tests/test_v343.py::test_matrix_java_seeded_10。

## SWR-V3.43-003（K-3 H7 鉴权谓词逻辑错误形态）

- 裁决：SKILL.md H7 检测要点 ③ 从「鉴权谓词弱化（前缀/子串/hash 替代全名）」
  扩为「鉴权谓词弱化或逻辑错误（前缀/子串/hash 替代全名；条件写错/比较
  对象错位——谓词本身错误而非被弱化，潜伏长周期形态）」。
- 理由：ptrace_may_access 2016 引入 10 年潜伏的形态不在任何检测要点里，
  且「逻辑错误」与「弱化」的发现路径不同（前者靠谓词逐分支语义复核，
  后者靠形态对比）。
- 测试守卫：tests/test_v343.py::test_skillmd_h7_logic_error_hint。

## SWR-V3.43-004（K-4 fixminer 跨多年窗口提示）

- 裁决：SKILL.md 修复驱动假设条款补句：「同形态修复族间隔 >1 年时
  （如 page cache 写越权族 Dirty Pipe 2022 → 2026 变体潮），--since 默认
  窗口挖不到 ground truth——族信号驱动的假设需长窗口（--since 1500+）或
  手工指定修复 commit」。
- 理由：2026 页缓存族发现的 ground truth 修复在 2022，默认 12 天窗口
  无法命中——这是假设空间完整性缺口而非机制缺口。
- 测试守卫：tests/test_v343.py::test_skillmd_fixminer_window_hint。

## SWR-V3.43-005（K-5 H3 kernel 锚点示例）

- 裁决：biz_hypothesis.md H3 检测要点补 kernel 形态锚点提示：「任务退出
  竞态（退出路径与回调并发）、timer/延迟回调持引用、调度器状态复用
  （RBTree 双插入形态）、异步子系统对象生命周期（io_uring 形态）——2025
  年 UAF 族六大 CVE 与 H3 检测要点的对应形态」。提示级，不增义务。
- 理由：H3 语义已覆盖这批 UAF，补锚点降低「检测要点→目标形态」翻译损耗。
- 测试守卫：tests/test_v343.py::test_h3_kernel_anchor_hint。

## SWR-V3.43-006（S-1 第四问）

- 裁决：skill-optimizer 义务入库三问扩为四问，追加第 ④ 问：「该知识是否
  已在主代理可推导的范围内」——可推导知识默认不入库（入库成本是条款密度
  与遵守率的负相关代价，需权衡而非默认）。
- 理由：v3.42 D-6 前缀级联类知识的入库成本反思——条款密度上升使遵守率
  下降，推导成本与条款密度的权衡必须显式化。
- 测试守卫：tests/test_v343.py::test_optimizer_fourth_question。

## SWR-V3.43-007（S-2 重设计触发判据）

- 裁决：skill-optimizer SKILL.md 新增「架构重设计触发判据」段，五信号：
  ① 修复互相冲突（修 A 坏 B）② 新能力无法用现有骨架表达（特例化累积）
  ③ 门禁形同虚设 ④ 知识复用率趋零 ⑤ 旧队列兼容性债务累积——任一信号
  出现才启动重设计，禁止情绪化重构。
- 理由：用户架构评估裁定——把「何时重设计」从主观判断变为文档判据。
- 测试守卫：tests/test_v343.py::test_optimizer_redesign_triggers。

## SWR-V3.43-008（S-3 条款消费度量）

- 裁决：SKILL.md R6 段补提示级义务（无门禁承载）：「审计收官时主代理在
  lessons.md 记录本轮实际被装载/消费的 SKILL.md 条款清单（提示级，
  无强制）——两周期后按消费记录批量裁除死条款」。
- 理由：条款密度与遵守率负相关的矛盾目前无度量；消费记录是裁除的
  证据基础（四缺陷纪律：无案例不入库，无消费即裁除）。
- 测试守卫：tests/test_v343.py::test_skillmd_consumption_metric_hint。

## 机制冻结守卫

- 本周期 src/ 与 tools/ 的判定逻辑零改动（版本链机械步除外）——
  tests/test_v343.py::test_mechanism_freeze_scope 断言：git diff 范围
  仅限 SKILL.md/任务书模板/矩阵资产/测试/设计件。
