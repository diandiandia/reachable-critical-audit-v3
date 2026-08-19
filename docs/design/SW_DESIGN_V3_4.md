# Reachable Critical Audit v3.4 — 软件设计（组件级）

> 从 `SYSTEM_DESIGN_V3_4.md` 导出的组件修改设计。日期：2026-08-19
> 最高判据：SKILL.md「第一原则：通用型 Skill」——本版全部组件修改都必须通过
> 自检四问（去项目名 / 语言无关或按 lang 分派 / 无具体项目路径 / 新项目验收）。
> 版本主题：**范围守护**——审计范围决策（选题）从主代理临场判断变为机制守护。

## 组件影响清单

| 组件 | 修改点 | 承载 REQ |
|---|---|---|
| M1 tools/batch_verify.py | ①新命令 `--stage coverage-ledger`：`--write` 聚合写账本（候选级 cwe×lang + R4 findings 项目语言集近似；cwe 双形态归一：cwe 数组 + sink_type 字符串；项目级去重幂等）；无参打印缺口格与计数表 ②stage_report 加 coverage_ledger 缺口段 | REQ-V3.4-002/003/007 |
| M2 resources/issue_coverage_matrix.json | 新资产：{schema_version, langs[15], families{fam:{cwe:[...], name}}, rows[{family, langs:{lang:count}}], updated_at}；初始值=历史 30 项目队列聚合回填 | REQ-V3.4-001 |
| M3 resources/checklist_library.json | +4 条清单（结构化 binding：cwe 集合 + 关键词辅）：CK-CRYPTO-MISUSE（cwe: 327/326/338/347/330/310/311/295）、CK-AUTHN-BYPASS（287/862/863/285/639/926/306）、CK-BIZ-LOGIC（关键词：越权/状态机/限额/金额/流程不变式）、CK-DATA-INTEGRITY（345/351/829/347）；内容去项目化 | REQ-V3.4-004 |
| M4 SKILL.md | ①批次选题规则条款（缺口格优先，可实证性=可行性约束）②报告覆盖账本尾注 ③第一原则新项目验收条款强化（补缺口格优先，判据含覆盖格+1） | REQ-V3.4-006/008 |
| M5 tests/ | 账本聚合（cwe 双形态归一/merge 幂等/项目去重）、缺口打印、清单绑定（CWE-327 候选 → CK-CRYPTO-MISUSE） | REQ-V3.4-001/002/004 |

## 数据模型变更

1. 新资产 `resources/issue_coverage_matrix.json`（见 M2）——**verify_queue/input_surface 零变更**
2. checklist_library 仅新增条目（数据模型不变）
3. 无 schema_version 变更

## 兼容性

- 六门禁①-⑧判据不变；assert_ledger 签名不变
- 账本为记录型资产：不存在时 coverage-ledger 命令报缺资产并 exit≠0（不阻断其他阶段）
- checklist_binder 既有绑定机制不变，仅新增条目——旧候选绑定结果不变（新 cwe 命中才会新增绑定）
- 138 测试全绿 + 新测试

## 实施顺序

| 步骤 | 内容 | 依赖 |
|---|---|---|
| 1 | M2 账本资产（families 映射 + 历史回填） | 无 |
| 2 | M1 coverage-ledger 命令 + stage_report 段 | 1 |
| 3 | M3 清单 4 条 | 无（与 2 并行） |
| 4 | M4 SKILL.md 三处 | 1-3 |
| 5 | M5 测试 + 全量回归 + install | 1-4 |
