# BIAS_EVAL_V3_41 — 四缺陷评估（v3.41，设计期）

## ① 盲目带入历史审计信息

- 案例支撑全部指向本会话产物：/root/hibernate-orm/.audit_results/lessons.md（「对 skill 的教训」#1-#5 与命中率段）、报告工件原文（B.2/B.5 降级文案两行）、会话 TypeError traceback、CAND-005/006 复活实录
- D-1 编辑点行号（workflow_export.py:810-818）为设计前取证实测，非记忆转述
- 去项目化：D-5/D-6/D-7 资产正文零项目名/框架名，追溯只进 source_lessons 字段
- 实现期重跑：新资产正文若带项目名，test_deproject_assets.py 扫描必须同步扩展

## ② 设计偏见

- 无编排便利型义务：D-1/D-2 是崩溃与降级路径修复，非主代理便利
- 无自动改写：D-3 只 warn + 建议映射（suggestion 字段），主代理裁决归一
- 修法层级正确：agent 行为偏差（方言外推、claim_type 逃逸）以任务书提示级 + collect 告警承载，不升格为硬义务/新门禁

## ③ 死代码

- 零新函数/零新字段——D-1 只改渲染层字段读取（resurrect_gap 为本次审计中主代理已写入队列的既有数据契约）；D-2 改 2 行 import；D-3 在既有函数内扩展；D-4 任务书文本；D-5/D-6 资产条目（消费者=既有绑定/裁决机制）；D-7 seed 数据（消费者=既有 hints/inventory 机制）
- 顺手清理裁决：无新死代码引入，无既有死代码待清（本周期不扩大范围）

## ④ 过设计

- 零新门禁名、零新强制义务、零新阶段——D-3/D-4 提示级，D-5/D-6 资产条目，D-7 知识数据
- 义务三问逐项：
  - D-3 告警：触发=非法 claim_type 出现；消费者=主代理收尾归一；案例=本批 2+2 处手工发现
  - D-4 条款：触发=渲染类阻断论证；消费者=verifier 判定；案例=CAND-006 复活 gap
  - D-5 清单：触发=转义责任下沉型 sink 家族；消费者=checklist_binder；案例=同批三通道
  - D-6 先例：触发=逃生舱类裁决；消费者=precedent 消费端；案例=CAND-005
  - D-7 seed：触发=java 目标假设生成提示；消费者=hints/inventory；案例=命中率 5/10
- 已存在机制裁除核查：步骤 5.2 编码矩阵（SWR-V3.25-003）已覆盖「单形态不得外推」的编码域——D-4 是其方言/平台域的互补扩展，不重造；_warn_r4_enums 既有 verdict/severity 告警形态为 D-3 的扩展基座

## 实现期重跑记录（阶段 3 完成后填写）

- [x] ① 资产正文去项目化扫描（test_deproject_assets, 589 全绿含该守卫）通过
- [x] ② 无自动改写（D-3 只产 suggestion 映射, _warn_r4_enums 不改写 items）
- [x] ③ 无死代码（R4_CLAIM_TYPES 消费者=_warn_r4_enums; gap_text 消费者=prompt 渲染; 资产条目消费者=既有绑定/裁决机制）
- [x] ④ 无新门禁/新阶段（4 旧队列 assert_ledger 零新增告警, violations 类型集合不变）
