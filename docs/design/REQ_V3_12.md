# REQ_V3_12 — 系统需求（v3.12 状态机分析能力补强）

> 对应设计文档：SYSTEM_DESIGN_V3_12.md。需求编号 REQ-V3.12-xxx。
> 每条含：语义 / 触发条件 / 消费者 / 案例支撑（三问已过，见设计文档 §3）。
> 本版不改变阶段骨架、六门禁判据语义、队列数据模型。

## 1. 覆盖账本层

### REQ-V3.12-001 覆盖账本 STATE 族
- **语义**：issue_coverage_matrix `families` 新增 `STATE` 族（CWE-841 行为工作流
  强制 / CWE-696 行为顺序错误 / CWE-670 恒错控制流），`rows` 同步新增空行
  （families 有族而 rows 无行时缺口扫描不可见）。CWE→族映射为数据驱动
  （fam_map 由 families 构造），未知 CWE 落 OTHER 的既有语义不变。
- **触发条件**：聚合/缺口读取时（恒，纯数据变更零代码路径新增）。
- **消费者**：批次选题缺口格（STATE×16 语言零格）、报告 B.6 覆盖账本、
  `_ledger_pressure` 压力提示。
- **案例支撑**：CWE-841/696/670 全库零出现且不在任何族的 cwe 集——若 verifier
  打标这三类状态机 CWE，聚合落 OTHER、无族级选题提示（前瞻性锚点缺口）。
  注：历史状态机机制类 finding（Pillow DCX/MPO 门禁时序 vs 状态机重入）实际
  以资源维 CWE 落 RESOURCE-DOS（实证队列 CWE-789）——其「机制维度」由本版
  清单族承载（REQ-V3.12-003），非账本族承载。

## 2. 分级层

### REQ-V3.12-002 严重程度映射扩展
- **语义**：SEVERITY_BY_CWE 补 841/696→高（状态机序对/协议绕过类，与 RACE
  362/366/367 同档）、670→中（恒错控制流逻辑缺陷默认档）。SKILL.md 严重度表同步。
  override 优先级、claim_type 回退链、default medium 语义不变。
- **触发条件**：`severity_for` 机械分级时（cwe 命中才生效）。
- **消费者**：报告问题清单分组排序、R4 申报归一化参照。
- **案例支撑**：误分级路径论证——841 类候选若 claim_type=other（无回退映射），
  现状走 medium 默认档，行为工作流绕过类误入中档；补齐映射后入高。同时保持
  「families 全族 CWE 与 SEVERITY_BY_CWE 全族对齐」的库内惯例（MEMORY-SAFETY/
  RACE/RESOURCE-DOS 等族均全族入表）。历史状态机机制 finding（Pillow DCX/MPO）
  经 CWE-789 已正确得 High，本项非其纠正手段。

## 3. 知识资产层

### REQ-V3.12-003 状态机族检查清单（4 条）
- **语义**：checklist_library `checklists` 新增 state-machine 族 4 条：
  - **CK-STATE-TRANSITION**（CWE-841 锚定）：非法/未定义状态转移是显式拒绝
    （错误码/会话重置/回滚）还是静默通过（沿默认分支继续）；守卫与状态持久化
    时序（检查在状态写回前还是后）；非法转移触发面是否由外部输入驱动。
  - **CK-STATE-CONFUSION**（无 CWE 锚定——问题域语义，关键词绑定；避免与
    TRANSITION 双锚 841 的机械共绑）：同一输入/对象被两条状态机路径解释
    （重入/并发请求/对象复用/双解释器）；多路径状态字段共享污染；复用后状态残留
    （连接池/缓存/对象池）。
  - **CK-MULTISTEP-INVARIANT**（CWE-696 锚定）：多步流程每步前置独立校验（跳步）；
    重放/乱序副作用重复；序对依赖在第 N 步入口重验。
  - **CK-FRAME-GATE-REENTRY**（无 CWE 锚定——跨族语义，关键词+信号门控）：
    容器级一次性门禁 vs 逐帧/逐块/逐条状态机重入路径的对账；重入路径全枚举
    （首/尾/零尺寸特例）；状态更新先于门禁检查=检查被绕过。
- **绑定规则**：`binding.keywords` 为纯子串匹配→只放 CJK 关键词与多词 ASCII 短语
  （state machine/state transition，禁裸 state/frame——子串会中 statement/framework）；
  词边界敏感 ASCII 术语（frame/chunk/handshake/renegotiation/transition/fsm）放
  `applicability_signals.text`（词边界匹配）；禁裸「块」（CJK 子串会中「模块」），
  用 分块/逐块。
- **触发条件**：候选 cwe 命中 841/696 或 keywords 命中（CK-FRAME-GATE-REENTRY 与
  CK-STATE-CONFUSION 另需信号/关键词门控——无对应形态信号不绑定）。
- **消费者**：verifier/refuter 任务书 `_checklist_section`（既有管线零代码改动）。
- **案例支撑**：Pillow DCX/MPO 多帧 seek 逐帧改 _size 无逐帧 bomb 检查（open 一次性
  检查覆盖不到 per-frame _open 重跑，实证队列 CWE-789/RESOURCE-DOS）→
  CK-FRAME-GATE-REENTRY 机制化；CK-BIZ-LOGIC 既有「状态机越权/多步流程不变式」
  步骤（v3.4，业务逻辑信号驱动）→ CK-STATE-TRANSITION / CK-MULTISTEP-INVARIANT
  升级为族；复用/双解释形态为 H3 相邻族的静态侧补充。

### REQ-V3.12-004 裁决先例 PREC-STATE-GATE-REENTRY
- **语义**：precedent_library 新增先例「一次性门禁 vs 状态机重入」：门禁在 open/
  加载时执行一次而逐项处理重跑状态机→门禁被绕过（缺陷成立）；门禁在每次重入
  路径独立执行（含首/尾/零尺寸特例）→门禁成立。counterexample 声明单块/单记录
  目标不适用。CWE_FAMILY_MAP 加 ("CWE-841","CWE-696","CWE-670") 元组、
  KEYWORD_MAP 加 状态机/state machine 双键（test_precedents_all_matchable
  强制触达）。不加 applicability_signals（CWE 锚点已窄，避免门控掉无帧词汇的
  841 候选——先例库「无 signals 不拦截」教义）。
- **触发条件**：候选 cwe 命中元组或 summary 命中关键词。
- **消费者**：自证伪提示段（workflow_export `_self_refutation_section`）。
- **案例支撑**：Pillow DCX/MPO 同一缺陷家族两实例——发现方式为「门禁时序 vs
  状态机重入」，非新 sink；先例库此前零状态机条目，同类裁决靠现场发挥。

### REQ-V3.12-005 版本链
- **语义**：TOOLING_VERSION → "3.12"（v3.11 增量段声称 3.11 但未落码的既有漂移
  一并收口）；SKILL.md v3.12 增量段 + 资产地图计数（34 清单/17 先例）+ 存量
  漂移文本修正（「29 条 CK-*」「25 条先例」「243+ 个单测」）；gen_tracking VERSIONS
  登记 + REQUIREMENTS_TRACKING 手工追加段；test_v39/test_v310 既有守卫更新；
  新增 tests/test_v312.py。
- **触发条件**：版本发布时（恒）。
- **消费者**：SWR-V3.4.4-008 版本漂移守卫、test_doc_lint 资产计数守卫。
- **案例支撑**：TOOLING_VERSION 实际值（3.10.2）与 v3.11 文档声称值（3.11）漂移
  两版未收口——本版以代码实值为准收口。

## 4. 明确不做（义务棘轮防护）

- 不建 H8 状态机假说（gate ④ H1-H7 语义不变）。
- 不加通用状态序列 fuzz harness 模板（v3.6 B 裁决先例：通用语言模板已裁除——
  状态机为项目专属形态，遵循「无匹配模板时现场构造」条款）。
- 不加新门禁、不加新绑定维度、不注入 R4 biz_hypothesis 与 Mode A' 任务书
  （与 v3.11 同款最小面原则）。
- 不动 CK-BIZ-LOGIC 存量（状态机/多步/流程不变式关键词共绑定=跨族强化，合法）。
- 不将 CWE-799 入 STATE 族（语义属交互频率→RESOURCE-DOS 侧）。
