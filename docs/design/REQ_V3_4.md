# Reachable Critical Audit v3.4 — 系统需求规格书（System Requirements）

> 从 `SYSTEM_DESIGN_V3_4.md`（问题域 P-A~P-B）导出的系统开发需求。每条附来源追溯与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.4 段）。日期：2026-08-19
> 编号规则：REQ-V3.4-xxx；优先级：P0=影响结论正确性，P1=影响效率/契约一致性
> 最高判据：SKILL.md「第一原则：通用型 Skill」+ 义务入库三问

## 1. 覆盖账本（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.4-001 | 覆盖账本资产 resources/issue_coverage_matrix.json：families 映射数据驱动（CWE 族 → cwe 列表）+ 15 语言清单（v3 战役覆盖集）+ rows 计数；初始值从历史审计项目回填（/root 下 30 个 .audit_results 队列聚合） | 设计 §2.1 | P1 | 资产存在；初始 rows 反映七项目批次偏向事实（crypto 族 × 多数语言 = 0） |
| REQ-V3.4-002 | `--stage coverage-ledger --write`：从 verify_queue 聚合候选级 cwe×lang（cwe 字段与 sink_type 双形态归一）+ R4 findings 按项目语言集近似计入，merge 语义写账本（计数累加幂等：按项目去重） | 设计 §2.1 | P1 | 七项目队列复跑 --write 后账本计数与队列 cwe 分布一致；重复 --write 幂等 |
| REQ-V3.4-003 | `--stage coverage-ledger` 无参：打印缺口格（0 覆盖 + 单项目低深度）与每族×语言计数表 | 设计 §2.1 | P1 | 输出含 crypto 族缺口格；exit 0 |
| REQ-V3.4-004 | 问题类清单 4 条入 checklist_library.json（CK-CRYPTO-MISUSE / CK-AUTHN-BYPASS / CK-BIZ-LOGIC / CK-DATA-INTEGRITY），结构化 binding（cwe 集合为主 + 关键词辅），checklist_binder 按既有机制绑定；内容去项目化 | 设计 §2.2 | P1 | cwe=CWE-327 候选 bind 出 CK-CRYPTO-MISUSE；grep 正文无项目名 |
| REQ-V3.4-005 | 设计约束：难实证类（crypto/authn/biz-logic/data-integrity）不进 gate ③ 强制实证枚举；claim_type 枚举不扩展（后果类语义不变） | 设计 §2.2/§2.4 | P0 | assert_ledger 的 EMPIRICAL_CLAIMS 与 claim_type enum 与 v3.3.2 完全一致 |
| REQ-V3.4-006 | SKILL.md 批次选题规则条款：选题先读覆盖账本缺口，优先未覆盖（语言 × CWE 族）格；可实证性降为可行性约束 | 设计 §2.3 | P1 | SKILL.md 含选题规则段 |
| REQ-V3.4-007 | 报告（stage_report）输出覆盖账本缺口段（机械渲染账本资产） | 设计 §2.1 | P1 | stage_report 输出含 coverage_ledger 段 |
| REQ-V3.4-008 | 第一原则"新项目验收"条款强化：验收项目优先选补缺口格项目，验收判据含"覆盖格 +1" | 设计 §2.3 | P1 | SKILL.md 第一原则验收条款更新 |

## 2. 约束（本版不做，防反向棘轮）

- 不扩展 claim_type 枚举、不给难实证类加强制实证、不新增候选数据模型字段、账本不设 gate
- （无编号条目——约束以设计 §2.4 为准，违规视为缺陷）
