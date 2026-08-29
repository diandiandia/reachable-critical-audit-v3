# SWR_V3_12 — 软件需求（v3.12 状态机分析能力补强）

> 对应文档：REQ_V3_12.md（需求语义）/ SOFTWARE_DESIGN_V3_12.md（改动点）。
> SWR 为可测契约：每条含断言式描述，测试实现见 test_v312.py。
> 原则：旧队列零行为变化；新增行为全部有触发条件（cwe/关键词/信号命中）。

## 1. 覆盖账本 STATE 族（REQ-V3.12-001）

- **SWR-V3.12-001**：`families["STATE"]` 存在且 cwe == [841, 696, 670]；
  `rows` 含 `{"family": "STATE", "langs": {}}` 行；`_aggregate_counts` 将
  cwe=["CWE-841"] 的候选归入 `STATE x <lang>`（非 OTHER）；无 STATE 行时
  缺口扫描输出 `STATE x <lang>` 缺口格（gap_cells 含之）。

## 2. 严重程度映射（REQ-V3.12-002）

- **SWR-V3.12-002**：`severity_for` 对 841/696 返回 `("high", "cwe:CWE-841")`/
  `("high", "cwe:CWE-696")`、对 670 返回 `("medium", "cwe:CWE-670")`；
  severity_override 优先级、claim_type 回退、default medium 语义不变
  （以既有 test_v37_report 锁为回归锚）。

## 3. 状态机族检查清单（REQ-V3.12-003）

- **SWR-V3.12-003**：4 条 CK-STATE-* 均经既有 binder 绑定（零代码改动）：
  - cwe 路径：cwe=["CWE-841"] 绑定 CK-STATE-TRANSITION（唯一 841 锚定条目，
    不与 CONFUSION 双锚共绑）；cwe=["CWE-696"] 绑定 CK-MULTISTEP-INVARIANT；
  - 关键词路径：summary 含 状态机 绑定 CK-STATE-TRANSITION（且与 CK-BIZ-LOGIC
    共绑定——合法，跨族强化）；summary 含 重入/复用/双解释/状态混淆 绑定
    CK-STATE-CONFUSION（无 CWE 锚定，关键词绑定为主——跨族语义形态）；
  - 信号门控：summary 含 状态机+逐帧+帧门禁 绑定 CK-FRAME-GATE-REENTRY；
    summary 含 状态机+模块化（无 frame/chunk/逐帧类信号）不绑定；
  - 误配防护：summary 含 framework/statement/裸 state（无多词短语）不绑定
    任何 CK-STATE-*（keywords 无裸 ASCII 单词；信号词边界匹配）。

## 4. 裁决先例（REQ-V3.12-004）

- **SWR-V3.12-004**：`pl.match` 经 CWE 元组（cwe=["CWE-841"]）与关键词
  （summary 含 状态机/state machine）双路径触达 PREC-STATE-GATE-REENTRY；
  test_precedents_all_matchable 的 reached==ids 断言保持成立；
  该先例 5 字段去项目化扫描 0 命中（机制形态）。

## 5. 去项目化与版本链（REQ-V3.12-003/005）

- **SWR-V3.12-005**：4 条新清单与新先例均无 DEPROJECT_BLACKLIST token、无
  /root/ 路径、零项目专属 API 名（项目名仅出现在 source_lessons 追溯字段）。
- **SWR-V3.12-006**：TOOLING_VERSION == "3.12"；SKILL.md 含「🆕 v3.12 增量」段
  且资产地图计数为 34 条检查清单/17 条裁决先例；严重度表含 841/670；
  test_v312 全绿且既有全量回归全绿（301 基线）；源仓库同步分 commit + install
  + 安装版测试全绿。

## 6. 兼容与明确不建（回归护栏）

- 旧队列复跑零新增 blocking（新增资产均为数据/映射层，无队列 schema 变更、
  无门禁语义变更；既有 CWE 归属锁 770/400→RESOURCE-DOS、327→CRYPTO、
  345→DATA-INTEGRITY 零碰撞）。
- 不建 H8 假说、不加通用状态序列 harness 模板、不加新门禁、不加新绑定维度、
  不注入 R4/Mode A'、不动 CK-BIZ-LOGIC 存量。
- ⚠️ 禁止运行 `tools/gen_tracking.py` 再生成 REQUIREMENTS_TRACKING.md
  （extract() 只解析表格行；V3.4.4-V3.7 为手工维护段且不在 VERSIONS——
  再生成会删除它们）。V3.12 段按手工追加方式维护。
