# Reachable Critical Audit v3.4 — 系统设计

> **文档性质**：v3.4 系统设计。上游输入：七项目批次复盘后的目标校准审计（2026-08-19）——
> 原始目标"top-15 语言 × 每语言 Top-10 信息安全问题"在 v3 战役达成一轮覆盖后再无机制守护；
> 七项目批次 0 新语言、0 新问题类，35 REACHABLE ~90% 为 DoS/内存类。
> **版本定位**：范围守护批次——不新增阶段、不改六门禁①-⑧判据、不加数据模型字段
> （覆盖账本从现有 cwe 字段聚合）。主题：**把审计范围决策从主代理临场判断变为机制守护**。
> **最高判据**：SKILL.md「第一原则：通用型 Skill」+ 义务入库三问（REQ-V3.3.2-022）。
> **日期**：2026-08-19

---

## 1. 问题域

### P-A：范围决策无机制守护（覆盖账本缺失）

**证据**：
- v3 战役 14 项目达成 15/15 语言覆盖（AWStats-Perl/Pester-PowerShell/ohmyzsh-Shell/
  Newtonsoft-C#/Django-Python/NestJS-TS/Vapor-Swift/WordPress-PHP/Dubbo-Java/Ktor-Kotlin/
  Akka-Scala/etcd-Go/lighttpd-C/actix-Rust/sinatra-Ruby）——之后无任何机制守护该覆盖
- 七项目批次（tiny_http/uwebsockets/libuv/hikaricp/fasthttp/node-sqlite3/cjson）6 语言
  全部为已覆盖语言、0 新语言、0 新问题类；35 REACHABLE 中 oom/unbounded/crash/
  protocol_dos 占 ~90%，crypto 误用/认证绕过/业务逻辑/数据完整性为 0
- 根因：批次选题的第一判据实际是"容器内可构建、可实证"，而不是覆盖缺口——
  机制偏向驱动选题偏向（库型项目复审计，移动/桌面/嵌入式/浏览器端为零）

### P-B：问题类维度未形式化 + 深度资产偏向

**证据**：
- "每语言 Top-10 信息安全问题"从未成为可追踪资产——无"CWE 族 × 语言"矩阵
- claim_type 枚举 7/8 为可用性/内存类；gate ③ 强制实证类全部是"可测量类"；
  难实证类归 `other` 后无任何审计深度要求
- checklist_library 19 条全部从战役提取的 DoS/累积/解析类——crypto 误用/
  认证绕过/业务逻辑/数据完整性类清单为零；H1-H7 中 4 个假说是内存/资源面

---

## 2. 设计方案（每域论证"为什么能解决"）

### 2.1 P-A：覆盖账本（issue_coverage_matrix）

**为什么能解决**：偏向的根源是选题无机械依据。建立"CWE 族 × 15 语言"覆盖账本，
数据源 = **现有 cwe 字段聚合**（候选 cwe + R4 findings cwe），零数据模型变更；
消费者 = 批次选题（读缺口）+ 报告尾注 + R6 闭合回填。

设计要点：
1. 资产 `resources/issue_coverage_matrix.json`：`{schema_version, families: {fam: {cwe:[...]}},
   langs: [15 语言], rows: [{family, langs: {lang: count}}], updated_at}`——CWE 族映射
   数据驱动（资产化，可扩展），15 语言清单 = v3 战役覆盖集
2. 写入：`batch_verify --stage coverage-ledger --write`（R6 闭合时调用）——统计口径：
   候选级 cwe × 候选 lang 为主；R4 findings 按项目语言集近似计入（findings 无 lang 字段，
   口径在账本头部声明）
3. 读取：同命令无参 = 打印缺口格（0 覆盖格 + 单项目低深度格）+ 每族每语言计数
4. 与 gate ⑦ 正交：⑦ 管**输入面**覆盖（surface 维度），账本管**问题类 × 语言**
   （issue 维度）——两个账本不冲突，报告分别呈现

### 2.2 P-B：难实证类深度要求（清单资产补齐，不进实证门禁）

**为什么能解决**：claim_type 是"后果类"（实证门禁维度），crypto 误用是"缺陷类"——
**不扩展 claim_type**（会污染 gate ③ 语义），**不给难实证类加强制实证**（漏斗只是反向）——
而是复用 checklist_binder 的 cwe 绑定机制，新增问题类清单条目：verifier 遇到对应
cwe 时强制执行清单，获得与 DoS 类同等的审计深度，而不承担实证义务。

新增清单（去项目化，从既有发现抽象）：
- CK-CRYPTO-MISUSE（密钥管理/算法选择/随机源状态——hikaricp rand() 未播种类发现的可泛化形式）
- CK-AUTHN-BYPASS（鉴权谓词强度/会话令牌校验/绕过路径枚举）
- CK-BIZ-LOGIC（多步流程不变式/状态机越权/限额与金额校验）
- CK-DATA-INTEGRITY（哈希/签名/校验语义误用）

### 2.3 选题规则条款（编排层，纯条款无工具）

SKILL.md 批次选题流程：读覆盖账本缺口 → 优先"未覆盖语言 × 未覆盖 CWE 族"格 →
可实证性降为**可行性约束**（而非第一判据）。第一原则"新项目验收"条款同步强化：
验收项目优先选补缺口格的新项目。

### 2.4 明确不做的事（防反向棘轮）

1. 不扩展 claim_type 枚举（后果类门禁维度不变）
2. 不给难实证类加强制实证（source_fact/机制级通道已够）
3. 不新增数据模型字段（账本从 cwe 聚合，零迁移）
4. 账本不设 gate（无 gate 消费它——它是选题依据 + 报告尾注，记录型义务）

---

## 3. 组件影响清单

| 组件 | 修改 |
|---|---|
| tools/batch_verify.py | 新命令 `--stage coverage-ledger`（--write 聚合写账本 / 无参打印缺口）；stage_report 加覆盖账本缺口段 |
| resources/issue_coverage_matrix.json | 新资产（families 映射 + 15 语言 + 历史审计回填初始值） |
| resources/checklist_library.json | +4 条问题类清单（cwe 结构化 binding） |
| SKILL.md | ①批次选题规则条款 ②报告覆盖账本尾注 ③第一原则新项目验收条款强化（补缺口格优先） |
| tests/ | 账本聚合（cwe 归一/merge 幂等）、缺口打印、清单绑定（crypto cwe 候选绑定新清单） |

## 4. 验收方案（Phase 3.4.3）

1. 历史账本回填后缺口格显式可见（crypto 类 × 15 语言全 0 的偏向事实可见化）
2. 新项目验收选题 = 缺口格项目，验收判据含"覆盖格 +1"
3. 新清单绑定可测：cwe=CWE-327 候选任务书含 CK-CRYPTO-MISUSE
4. 六门禁①-⑧判据不变；138 测试全绿
