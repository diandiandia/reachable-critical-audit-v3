# SWR V3.25 — 软件需求（MaintainWise 验收审计复盘）

修法形态纪律：提示级/warn 优先，禁止自动改写，无新门禁名/新阶段/新义务字段。

## 修复

### SWR-V3.25-001（D-1）verify 导出默认 taskFile 化

- **修复**：export_script verify 分支在 payload.append 前把 prompt 写入
  `.audit_results/_tasks/verify_<id>.md`，payload 条目改带 `taskFile` 引用
  （与 resurrect 分支同契约，v3.22 D-9 先例扩展）。
- **裁决理由**：v3.24 验收实测 111KB payload 超 Workflow args 上限（firefox
  教训 6 的 args 限额实录再现）；v3.22 D-9 只默认化 refutation/resurrect，
  verify 漏网。
- **义务三问**：① 触发：Mode W 派发导出（无条件, 机制默认形态）② 消费者：
  workflow JS（c.taskFile 分支已存在）与 Mode A' 主代理 ③ 裁掉丢什么：大
  批量 verify 波次再次超限。
- **测试守卫**：导出 payload 条目含 taskFile 且文件存在、不含内嵌 prompt
  全文；Workflow JS 兼容性断言（taskFile 分支保留）。

### SWR-V3.25-002（D-2）r35-collect A' 文件目录输入

- **修复**：stage_r35_collect 的决策装载双形态——journal.jsonl 优先；缺失时
  glob `<目录>/_refute_*.json`（schema: {id, refuted, reason, agent,
  strengthened?, attribution_correction?, note?}）按同一多数决路径落盘。
  CLI 增 `--from-refute-files <dir>`（与 --from-journal 并列）。
- **裁决理由**：A' 降级条款（v3.24 首次全程实战）的证伪侧无官方收集通道，
  主代理合成 journal 是手工簿记步骤（88 行实录）——降级路径的契约缺口。
- **义务三问**：① 触发：A' 降级模式证伪收波 ② 消费者：r35-collect 机械
  多数决 ③ 裁掉丢什么：A' 证伪收波依赖手工合成, 契约漂移风险。
- **测试守卫**：临时目录放两份 _refute_*.json（1 kill 1 不杀）→ 多数决
  survived；双杀 → demote；journal 路径回归不变。

### SWR-V3.25-003（D-3）verifier 路径穿越编码矩阵条款

- **修复**：_build_prompt 步骤 5（路径覆盖）补一条：路径穿越/路径拼接类
  候选的编码矩阵固定维度——裸 ../、%2e%2e 段、%2F 分隔符、混合编码、
  %252e 双编码逐形态实测或注明未测；单形态样本不得外推（框架/网关/应用
  三层解码行为分叉实录）。
- **裁决理由**：CAND-014 verifier「编码不穿越」被 refuter-1 与主代理实测
  双重推翻——验证侧缺该维度义务导致精度修正方向错误。
- **义务三问**：① 触发：候选涉及路径拼接/CWE-22 ② 消费者：verifier 子
  智能体 ③ 裁掉丢什么：穿越矩阵结论单形态外推的误判（1 例实录）。
- **测试守卫**：_build_prompt 输出含「编码矩阵」与「%252e」；零项目名。

### SWR-V3.25-004（D-4）r4-collect severity 传递 warn

- **修复**：stage_r4_collect 落盘时对 r3_link 非空的 High/Critical finding：
  查载体候选 `severity_for`，R4 申报值 > 候选机械值时输出 warn
  `severity_transfer_advisory`（建议主代理裁决 severity_override；不自动
  改写——误猜风险>收益纪律）。
- **裁决理由**：同事实去重后「主申报方承载 severity」在载体为候选侧时失效
  （CAND-018/014 两处手工 override 实录）。
- **义务三问**：① 触发：r3_link 映射 + severity 档差 ② 消费者：主代理
  collect 收波 ③ 裁掉丢什么：严重度系统性低估且无提示。
- **测试守卫**：构造 queue 快照（R4 High finding r3_link→候选机械 Medium）
  → collect 输出含 severity_transfer_advisory；无档差时不输出。

### SWR-V3.25-005（D-5）storage 域预置数据文件面指引

- **修复**：surface_map_domain.md 增条件段「预置数据文件面指引」（storage
  域注入）：仓库内 shipped 数据文件（预置数据库/种子文件/示例配置）的状态
  即攻击面——默认口令/默认关闭的安全开关/预置凭据与代码默认值的一致性
  逐项核对。
- **裁决理由**：预置 maintainwise.db（admin FCP=0+公开默认口令）成为
  linux_local 首启接管路径（H-7-F4 实测 checkpw=True）。
- **义务三问**：① 触发：storage 域且仓库含数据文件 ② 消费者：R1 测绘子
  智能体（主代理派发时注入）③ 裁掉丢什么：预置数据文件状态盲区。
- **测试守卫**：模板含「预置数据文件面」；零项目名。

### SWR-V3.25-006（D-6）R5 核取提示句

- **修复**：SKILL.md R5 回填规范段补一句（提示级）：补测前先核取 verifier/
  证伪者证据中已有实测数字——backfill 规范（v3.4.3-061）以证据文本实测为
  依据，同事实重复实证是执行层浪费。
- **裁决理由**：R5 核取代理复测大半已有数字（v3.24 验收实录）。
- **义务三问**：① 触发：R5 补测决策 ② 消费者：主代理 R5 执行 ③ 裁掉丢
  什么：重复实证成本（提示级, 无强制义务）。
- **测试守卫**：SKILL.md 含「先核取」与「已有实测数字」。

## 裁除（裁决记录）

- 用户追问四候选：实证自动传递（降级为 D-6）、CK 合并 / legacy 清理 /
  signature 降级（取证裁除, 理由见 REQ 裁决记录表）。
