# BIAS_EVAL_V3_46 — 四缺陷评估（设计期，实现期必须重跑）

## ① 盲目带入历史审计信息

- 案例支撑全部指向 K6-K9 lessons.md 具体条目（REQ_V3_46 表已列条目号），
  实现期对照 lessons 原文重核。
- 去项目化：D-5 手册零项目名（dummy/usb-storage/nciemp/RPC responder 均为
  机制描述，归属进 source 注记）；D-1 fixture 免责句改写为通用形态；
  新增/修改资产正文均过 test_deproject_assets.py。
- D-4 条款文本不出现 HID/NFS 等项目名。

## ② 设计偏见

- D-1 明确**不自动改写**：全免责返回 None + warn，主代理裁决——避免
  反方向误标（设计偏见检查点：未把"纠偏"当自动纠偏）。
- D-2 键名归一属建议映射级（不删字段、warn 可追责）。
- D-3 预检是机械事实检查（fs.existsSync），非语义裁决——编排便利仅落为
  快失败提示，未升格为门禁义务。

## ③ 死代码

- `_split_sentences`/`_is_disclaimer_sentence` 消费者 = `_derive_attacker_tier`
  （唯一调用点，测试直接覆盖）。
- `norm_flags` 消费者 = r4-collect warn 输出行。
- JS 预检段消费者 = 每次 workflow 运行（verify/refutation 两导出路径）。
- 无新字段落队列（norm_flags 不持久化）——不产生存储侧死字段。

## ④ 过设计

- 零新门禁、零新强制义务、零新阶段（见 SYSTEM_DESIGN 不变式）。
- 义务三问逐项过：D-4 触发条件=写 local 前（有条件）、消费者=测绘子智能体
  （有消费者）、裁掉丢 K6/K8 两类面前提失实拦截（有案例）。
- D-2 归一器**不**做宽泛前缀模糊匹配（K9 实测只两种别名形态，扩到模糊匹配
  是过设计——留到形态出现再扩）。
- D-5 只收四条已实证通道，不臆造"常见模式清单"。
