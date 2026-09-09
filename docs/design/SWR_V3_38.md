# SWR_V3_38: 模型能力利用五机制

## SWR-V3.38-001: 清单条目挂载修复 + CK-SIBLING-CONSISTENCY (D-0/D-1)

- **裁决**: (a) v3.37 两条目补 binding——CK-SLICE-CAPACITY {cwe:[CWE-125,
  CWE-787], keywords:["切片","slice","越界","out of range"]};
  CK-MAGNITUDE-OWNERSHIP {cwe:[], keywords:[], applies_to_phase:"R5"}
  (R5 语义空间挂载: claim 属实证集或 empirical dict 在位);
  (b) 新条目 CK-SIBLING-CONSISTENCY (family=sibling-consistency,
  binding: RESOURCE-DOS∪AUTHN∪WEB 族 cwe + keywords ["端点","endpoint"])
  ——同族多实例功能面的防御维度对比矩阵, 不一致即缺陷假设 (修复残留形态)。
- **义务三问**: ①触发条件——cwe 命中/关键词命中/实证语义空间 (结构化 binding,
  无条件类); ②消费者——verifier 任务书清单段 (binder 注入) + R2 假设条款;
  ③裁掉丢什么——CAND-001 差分定级形态的发现通道 + v3.37 条目从不挂载的静默空转。
- **测试守卫**: test_v338.py T-0/T-1。

## SWR-V3.38-002: 自证伪轮结构化 (D-2)

- **裁决**: VERDICT_SCHEMA 增可选 `self_refutations` (字符串数组); verify
  prompt 增自证伪轮条款 (≥2 条翻转点, REACHABLE 攻量级/主体/前提,
  UNREACHABLE 攻防御前提; 空数组须 evidence 说明理由); refute_prompt
  注入候选 self_refutations 为优先攻击面 (证伪者从"找角度"变"攻前提")。
- **义务三问**: ①触发条件——REACHABLE/UNREACHABLE 判定后 (提示级, 空容忍);
  ②消费者——refute_prompt 注入 + 报告佐证 (证伪轮聚焦); ③裁掉丢什么——
  CAND-002 前提幻觉在证伪轮 1/2 才暴露的轮次浪费。
- **测试守卫**: test_v338.py T-2。

## SWR-V3.38-003: 公开面关联检索前置 (D-3)

- **裁决**: SKILL.md R2 增条款——网络可用时假设生成前做公开面关联 (已知
  CVE/GHSA 检索 + 上游 master 对账, 落盘 .audit_results/upstream_recon.json):
  已修形态降级或改口径, 未修形态附佐证, 时间差假设 (上游后修=快照缺陷候选)
  直接进假设空间; 网络不可用零阻塞跳过。
- **义务三问**: ①触发条件——网络可用 (WebFetch/WebSearch 工具在); ②消费者
  ——假设生成输入 + 筛选判据 (提示级); ③裁掉丢什么——CAND-005 形态的重复
  验证成本 + 时间差假设通道 (召回)。
- **测试守卫**: test_v338.py T-3。

## SWR-V3.38-004: 实证机会条款 (D-4)

- **裁决**: verify prompt 增条款——目标可构建且 claim 属实证类时, 低成本实证
  路径建议实测并附数字/复现步骤; 无实证环境记录 blocker 证据。提示级
  (无环境不强制, 与 R5 强制实证判定不冲突——R3 实测数字是分级升档依据)。
- **义务三问**: ①触发条件——实证类声称 + 可构建目标 (提示级); ②消费者——
  evidence 数字 → 分级/证伪攻击面; ③裁掉丢什么——CAND-011 静态声称到 R5
  才拦截的轮次浪费 + H1 实测数字成报告核心的先例收益。
- **测试守卫**: test_v338.py T-2/T-3。

## SWR-V3.38-005: harness 回收条款 (D-5)

- **裁决**: SKILL.md R5 补一行——收官复盘对现场构造实证程序做通用化评审,
  跨项目可复用则去项目化入库 templates/harness/ (paired_control_probe 先例)。
- **义务三问**: ①触发条件——本批存在现场构造 harness (提示级); ②消费者——
  skill-optimizer 阶段 0 复盘输入; ③裁掉丢什么——实证能力复利通道。
- **测试守卫**: test_v338.py T-3。

## 兼容性不变式

- 全部提示级/清单级, 零新门禁/零新强制义务/零新阶段; 六门禁判据、队列数据
  模型、N=2 多数决、铁律零触碰;
- VERDICT_SCHEMA 只增可选字段 (旧 journal 零影响);
- 清单库只增条目与 binding (既有 47 条零改动);
- 旧队列复跑零新增告警 (验收判据)。
