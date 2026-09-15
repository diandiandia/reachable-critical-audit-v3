# BIAS_EVAL V3.45 — 四缺陷评估

> 设计期评估; 实现期须重跑 (v3.16 教训: 设计期零违规不保证实现期)。

## ① 盲目带入历史审计信息

- **案例支撑**: 每条 SWR 的 source 均指向 batch_K*/lessons.md 具体条目号
  (D-1←K2-9, D-2←K3-7, D-3←K5-11, D-4←K5-8, D-5←K4-13, D-6←K2-7,
  D-7←K2-8, D-8←K1-4, D-9←K3-8/K4-11/K4-14, D-10←K2-4/K2-5/K3-10,
  D-11←K2-10/K3-9, D-12←K4-10, D-13←K5-7, D-14←K4-15, D-15←K5-3, D-16←K5-6)。
- **去项目化**: 全部修复正文零项目名 (linux/kernel 只出现在追溯字段与
  source_lessons); 任务书文本注入的实录形态均为"K4 批次"/"K5 实录"级批号
  而非项目名——与既有先例条款 (W6 §/验收批次实录) 同口径。
- **机器守卫**: test_deproject_assets.py PROJECT_TOKENS 扫描必须 0 命中
  (D-9/D-10/D-11/D-12 注入文本新增后重跑确认)。
- **回归集语料不得入运行时**: D-6 的探针 glob 为通用形态 (arch/*/boot/Image),
  非 kernel 专属路径 → 通用性成立。

## ② 设计偏见

- **编排便利当义务**: D-13 (分片落盘) 的消费者是主代理派发动作, 条款为提示级
  (派发时建议), 不构成 skill 硬义务 — 与 v3.14 D-7 裁除先例对照, 本项有
  一死一活对照实录支撑, 保留提示级。
- **自动改写**: 零自动改写 (D-1/D-8 只 warn; D-2/D-4 归一化仅形态别名;
  D-3 覆写仅限占位→真决策方向)。severity 裁决不自动改 (D-16 提示走 override)。
- **层级正确**: 全部落在机械/任务书/提示级 — 无新门禁、无新阶段、无强制义务。

## ③ 死代码

- 每个新字段/函数的消费者: claim_self_reported → 追溯归档 (R3.5-N 抽样单真相
  已是 is_claim_like, 本字段消费者 = 报告渲染追溯 + 主代理收尾) —
  **实现时若报告渲染不消费则降级为纯归档字段并在测试断言注明**;
  resurrection_review.auto_bookkept → collect skip 判定 (D-3 唯一消费者);
  target_profile S7 → empirical_modes 推荐 (主代理签收后 profile 消费者);
  _empirical_boot_signals → recommend() 单调用点。
- 附带裁决: 无待清理死函数 (D-1 区域现有代码全有消费者)。

## ④ 过设计

- 无新门禁名、无新阶段、无新强制义务 — 16 SWR 全部 warn/提示/容错级。
- 义务三问逐项过: 每条 SWR 的触发条件 (新形态输入才触发)、消费者 (主代理/
  collect/渲染)、案例支撑 (lessons 条目) 已在 SWR 文件列示。
- 取证裁除已存在机制: K2-11 taskFile (已修) — 见 REQ 裁除表。
- 边界: D-16 若发现 severity_override 已在 SKILL.md R4 节有提示, 则降级为
  文案位置调整 (取证时已核实 R4 节无此提示, 仅 render 优先级条款)。

## 实现期重跑记录 (实现后填写, 2026-09-15)

- [x] test_deproject_assets.py 0 命中 (635 全绿含 deproject 10 用例)
- [x] 注入文本无项目名/机器路径 — **实现期抓出 1 处违规并修正**: D-14/D-15/D-10
  初版注入含 kernel 专属标识符 (act_skbmod.c/failfs/LOOKUP_MOUNTPOINT/READ_ONCE/
  extract-ikconfig), 已去项目化为机制描述 (拒绝屏障×历史查找模式清位/原子快照读/
  配置提取工具); 检测关键词族 (softirq/kthread 等内核上下文信号) 属域词汇
  非项目名, 保留为 D-8 判定逻辑本体
- [x] 旧队列复跑 warn 零新增 (haproxy/caddy/hadoop/keycloak/hibernate-orm 5/5
  ASSERT_PASSED, warn 与变更前一致 = skipped_gates 三条)
- [x] 兼容性: v3.42 近似键诊断机制与 D-2 冲突已裁 (别名归一撤销, 只补混合形态
  告警); v322 簿记形状测试同步新标记 (意向语义变更); legacy 全名 type
  (network_endpoint) 纳入容忍集
