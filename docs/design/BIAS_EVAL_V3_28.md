# BIAS_EVAL_V3.28 — 四缺陷评估（设计期）

## ① 盲目带入历史审计信息

- 34 条目派生自矩阵已种格——source_lessons 原样引用，零新增知识、零臆造
- verify 升档仅限本会话可证条目（QuickJS 候选 id 逐条核对：CAND-001/003
  为 worker/SAB 限额绕过、H-1-F1 消息队列、H-2-F1/F2 反序列化、H-7-F2
  哨兵 fail-open——全部指向 C×RESOURCE-DOS/C×MEMORY-SAFETY 格，归属正确）
- 旧战役条目 verify=unverified（候选 id 不可溯），不伪造 battle_confirmed
- seed 输入去项目化扫描（黑名单 token 同 test_deproject 口径）

## ② 设计偏见

- 无自动改写：seed 显式命令、幂等拒绝重复、失败条目明确报错
- rank 机械计算不落盘：排序是视图，不做"排序权威"义务
- 回填升档是提示级条款，不建自动升档机制（误匹配风险>收益，同 v3.14 D-4 裁除先例）

## ③ 死代码

- load_inventory 消费者：inventory_for/goal_progress/seed_entries 三命令 + test_v328
- goal 视图消费者：主代理战略盘点、验收报告；K1/K2 无自动阻断（纯显示）

## ④ 过设计

- 零新门禁、零新强制义务、流水线零改动、裁决层零改动
- K1/K2 不设自动阻断（里程碑是显示不是门禁——义务三问②无机械消费者）
- seed 不建"外部来源白名单"（来源标注由条目自带，白名单会成为新维护面）

## 实现期重跑（阶段 7 义务）

- inventory 条目正文零项目名（grep 断言）
- seed 校验对项目名 token 拒绝（测试反面分支）
- 守卫 ×18 全同步、计数守卫不误伤（inventory 独立资产不入计数断言）
