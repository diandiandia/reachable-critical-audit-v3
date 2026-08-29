# SYSTEM_DESIGN_V3_13 — 错误路径处理族 + 数值语义族 + 账本锚点一致性修复

> 版本链：v3.12（2026-08-29，状态机分析能力补强）→ **v3.13（2026-08-29，错误路径处理族 + 数值语义族 + 账本锚点一致性修复）**。
> 能力增量版：不改变阶段骨架 R0-R6、不改变六门禁①-⑧判据语义、不改变队列数据模型。
> 背景动因：用户盘点「除复杂文件解析/协议分析/状态机分析之外还该关注什么」——
> 两个有实证支撑的空白维度（数值语义、错误/故障路径处理）+ 一个账本漂移修复
> （436/444/1333 清单/先例层已锚、账本层未锚）。评估：BIAS_EVAL_V3_13.md。

## 0. 第一原则自检（义务入库三问 + 去项目化）

本版所有新义务逐条过三问（见 §3）。全部案例支撑经实证队列（verify_queue.json）
与 lessons 原文逐字核验，不采信记忆转述（v3.12 评估教训）。新资产机制形态书写
（零项目专属 API 名；项目名仅 source_lessons 追溯列）。零代码路径新增于绑定/
聚合主链（账本 fam_map 数据驱动、清单走既有 binder、无新 PREC——既有 map 可达）。

## 1. 问题域（六缺口）

| 编号 | 问题 | 复盘案例（追溯） | 形态 |
|---|---|---|---|
| S-A | **账本无 NUMERIC 族**：191/369/681/697 不在任何族 cwe 集——打标后落 OTHER、无选题压力 | libvpx CAND-001 CWE-681 REACHABLE（截断死代码）；RFCOMM CWE-191 下溢 empirically_confirmed；media3 369 CONFIRMED | 账本缺口 |
| S-B | **账本无 ERROR-HANDLING 族**：457/665 落 OTHER | zookeeper 截断帧 457 CONFIRMED（SIGABRT）；gson 665 假说级 | 账本缺口 |
| S-C | **锚定一致性漂移**：436/444/1333 在清单层（CK-DUAL-PARSER/CK-HOST-AUTH-CONSISTENCY/CK-RUNTIME-RE）与先例层（CWE_FAMILY_MAP）已锚定，账本族 cwe 集缺这三码——覆盖账本与知识体系不同步 | aiohttp CAND-002 CWE-436 NEEDS_REVIEW 真实受影响；puma 444/elasticsearch 1333 假说级 | 一致性漂移 |
| S-D | **严重度表缺 9 码**：走 claim_type 回退或 medium 默认——1333+claim=other 误入中档 | 全族入表惯例被打破（v3.12 S-B 同形态） | 分级缺口 |
| S-E | **清单库无数值语义族级条目**：CK-SENTINEL-SEMANTICS 为默认值域 scope，截断/回绕/除零/不一致比较零覆盖 | 同 S-A 案例 | 知识供给缺口 |
| S-F | **错误路径族未制度化**：W6 §25.3 明示「缓存层条件反转写反=死代码——列为 CK 检查项」从未落实 | Lersosa 条件反转（证伪者发现）；zookeeper 457；Pillow H3 维度浮现候选全被证伪（诚实归档） | 知识供给缺口 |

## 2. 修复策略（5 项 REQ，详见 REQ_V3_13.md）

1. **覆盖账本族扩展与锚定修正**（S-A/B/C）：NUMERIC{191/369/681/697} +
   ERROR-HANDLING{457/665} + 空行；WEB += 436/444、RESOURCE-DOS += 1333
2. **严重程度映射**（S-D）：191→严重、369/457/444/1333→高、681/697/665/436→中
3. **数值语义族检查清单 2 条**（S-E）：截断先于检查/除零与比较计数语义
4. **错误路径处理族检查清单 2 条**（S-F）：错误分支方向与死代码/状态残留与清理
5. **版本链**（收口）：TOOLING 3.13 + 文档五件套 + test_v313

## 3. 义务入库三问（新义务逐条）

| 新义务 | ①触发条件 | ②消费者 | ③案例支撑 |
|---|---|---|---|
| NUMERIC 族 | 聚合/缺口读取（数据驱动） | 选题缺口格/报告 B.6/压力提示 | 191/369/681/697 全库零锚点（前瞻）；191 下溢与 681 截断各 1 REACHABLE 实证 |
| ERROR-HANDLING 族 | 同上 | 同上 | 457 截断帧 SIGABRT CONFIRMED；665 假说级（诚实标注） |
| 436/444/1333 锚定修正 | 同上 | 同上 | 清单/先例已锚而账本未锚的漂移实测；aiohttp 436 NEEDS_REVIEW 受影响 |
| 严重度 9 码 | `severity_for` cwe 命中 | 报告分组排序 | 191↔190 对称；457 SIGABRT 实证档；1333 族先例；436 双解析器前提依赖外部组件 |
| CK-NUMERIC-TRUNCATION | cwe 191/681 或截断类关键词 | verifier/refuter `_checklist_section` | libvpx 截断死代码 + RFCOMM 下溢 + GT-2 len+4 回绕 |
| CK-NUMERIC-SEMANTICS | cwe 369/697 或除零/比较类关键词 | 同上 | media3 除零 CONFIRMED + W6 §19.7/§21.3（§21.4 属网络阻断已自纠） |
| CK-ERROR-BRANCH | 错误分支/失败分支/条件反转/异常路径/error path/failure path | 同上 | W6 §25.3 列项由来（从未落实）+ §13.5 实证抽验 |
| CK-ERROR-CLEANUP | cwe 457/665 或 未初始化/清理类关键词 | 同上 | zookeeper 截断帧 SIGABRT + Pillow H3 诚实归档 |

## 4. 明确不做（义务棘轮防护）

- 不建 H8/H9（错误路径保持清单级——v3.12「不建 H8」先例，gate ④ 语义不变）。
- 不重归 190/129（MEMORY-SAFETY 既有锁）；不动 CK-SENTINEL-SEMANTICS/
  CK-SIBLING-LISTENERS 存量（共绑合法）。
- 无新 PREC（436/444/1333 既有 map 可达）；无新 harness；无新门禁；无新绑定维度。
- 时间/Unicode/侧信道维度无漏报支撑暂缓（义务三问③不成立——下一批对应形态
  目标自然触发后再议）。
- 不修复 README.md 清单计数存量漂移（v3.12 口径一致性，记入评估注记）。

## 5. 验收判据（Phase 3.13）

1. 全量回归全绿（315 基线 + test_v313 新增 14 用例）+ 旧队列复跑零新增告警
2. 去项目化扫描 0 命中（新 4 条清单机制形态）
3. 覆盖账本 dry-run 列出 NUMERIC/ERROR-HANDLING×16 缺口格 + 436/444/1333 归族
4. 绑定契约断言全绿（含限定形态负例：异常处理/error_handler/cleanup() 不误绑）
5. 未审计过的新项目验收：随下一在线项目自然触发（数值/错误路径清单绑定、
  新族格回填至少各真实命中一次）
6. 源仓库同步分 commit + install + 安装版测试全绿
