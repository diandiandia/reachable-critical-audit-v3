# SWR V3.18 — 设计规则（2026-09-01）

## SWR-V3.18-001（D-1 语言问题矩阵数据）

`resources/language_issue_matrix.json`：`{langs:[16], families:[12],
cells:[{lang, family, status, cwes[], patterns[], sinks[], pitfalls[],
source_lessons[]}]}`。langs/families 与 issue_coverage_matrix.json 逐位
一致（测试守卫双向断言）。cell 正文（patterns/sinks/pitfalls）机制形态
零项目名零框架名；项目归属只进 source_lessons。种格判据：每条格必须
有仓内案例支撑（L2 签名语义 / 清单与先例 source_lessons / SKILL.md
机制形态实录）——无支撑格 status=pending 且内容空（v3.6 confirmed:false
诚实占位先例）。测试：schema 合法 / langs、families 与账本一致 /
种格含 cwes+patterns+sinks+pitfalls+source_lessons 全字段 /
pending 格零内容 / DEPROJECT_BLACKLIST 扫描种格正文零命中。

## SWR-V3.18-002（D-2 加载器与消费端）

`language_issue_matrix.py`：`load()` / `cells_for(lang, family=None)`
（只返回 status=seeded；lang 归一化 cs↔csharp、ts/typescript↔javascript，
与 batch_verify._LANG_ALIAS 同规则）/ `stats()` / CLI `cells <lang>
[family]`、`stats`。SKILL.md R2 条款：主代理（或限时 agent）生成假设前
执行 `python3 <skill_dir>/language_issue_matrix.py cells <surface.lang>`
读取该语言已种格，作为假设空间提示（提示级，无强制义务）；pending 格
零注入零提示。测试：cells_for 只含 seeded / 别名归一 / 未知语言空列表 /
pending 零注入 / CLI cells 与 stats 输出形态。

## SWR-V3.18-003（D-3 回填纪律条款）

SKILL.md 验收判据与 R6 节条款：每版本验收审计收官时，主代理把验收项目
覆盖的语言×族格两段式回填进矩阵（去项目化提炼 → 入库，来源写
source_lessons 含日期）；与 coverage-ledger --write 时序互不依赖
（账本记覆盖计数，矩阵供知识）；无新门禁——回填是验收判据条款非 gate。
测试：SKILL.md 回填条款文本存在。

## 兼容性不变式

全量 392 基线零回退；六门禁①-⑧判据语义零改动；队列数据模型零改动；
旧队列复跑零新增告警（矩阵无队列消费端）；资产计数守卫零变化
（新资产不在现有计数断言集内）。
