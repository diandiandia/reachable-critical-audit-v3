# SWR V3.24 — 软件需求（三引擎全景召回评估驱动）

每条修复一条 SWR：裁决理由 + 测试守卫 + 义务三问。修法形态纪律：全部
提示级/warn 注记，禁止自动改写，无新门禁名/新阶段/新义务字段。

## 修复

### SWR-V3.24-001（D-1）H4 site-isolation/资源归因检查点

- **修复**：`biz_hypothesis.md` H4 补子条（提示级）：
  site-isolation/资源归因检查点——跨进程资源（纹理/缓存/下载/导航目标/
  worker 等）绑定到错误 origin 即信任边界破坏；检查资源创建与归因的
  origin 上下文一致性。
- **裁决理由**：三引擎 L0d 412 条为包络内第三大方向且 Firefox 侧已反超
  经典内存类成为最大单方向（97 条，2025H2 起每期固定产出，含 Graphics
  组件里的 site-isolation 新形态）；H4 现检查点（reply 通道族/初始化时序
  注入面/平台信任模型对照）无资源归因形态——假设生成对该方向缺锚点。
- **义务三问**：① 触发条件：H4 运行目标（多进程 application 形态）；
  ② 消费者：R4 H4 假说子智能体；③ 裁掉丢什么：site-isolation 类系统性
  盲（三引擎固定产出实录，D-1 案例支撑条）。
- **测试守卫**：biz_hypothesis.md 含「site-isolation」与「资源归因」；
  新子条零项目 token；反面分支：新文本不含「强制/必须」义务词（提示级）。

### SWR-V3.24-002（D-2）JIT 轴根因归属条款

- **修复**：`surface_map_domain.md` JIT 优化正确性层轴测绘段末补一条：
  根因归属条款——缺陷根因无法在 runtime 实现与编译器正确性之间归属时，
  标注归属未知并保持 [ambig]；不得默认归编译器正确性；CWE-843 映射仅
  适用于归属成立的候选。
- **裁决理由**：classify_chrome 47 条 V8 非 TC 内存缺陷（OOB/整数溢出）
  从公告无法区分 runtime/JIT 根因，全部 [ambig]；v3.23 轴未定义归属未知
  的处置，验证期有默认归编译器的误判风险（85046 与 runtime 类缺陷的
  族边界被稀释）；WebKit 侧 L1a 实证材料仅 2 条，同属归属通道缺失。
- **义务三问**：① 触发条件：generation_layers 含 jit 的目标；
  ② 消费者：R2 假设生成 + R3 验证判定（claim 归属影响 CWE 映射）；
  ③ 裁掉丢什么：L0/L1 族边界失真、回归集对照失效（Chrome 47 条实录）。
- **测试守卫**：SURFACE_TMPL JIT 轴段含「归属未知」与「[ambig]」；
  新条零项目 token。

### SWR-V3.24-003（D-3）发现包络边界声明补两族

- **修复**：SKILL.md 报告段「发现包络边界声明」不覆盖项补：
  （d）UI 信任指示层（地址栏/界面欺骗类——UI 信任逻辑非代码缺陷），
  （e）移动端平台集成层。保持「缺失 = warn 注记不阻断」原位。
- **裁决理由**：L2b 82（0 critical）+ L2c 125（8 critical）合计 9.0%，
  为每期固定低危产出；v3.23 声明三族（JIT/闭源/非目标平台）未覆盖——
  R2 假设生成对这两族无显式排除锚点，无效投入无边界。
- **义务三问**：① 触发条件：无条件（声明性文档，R2 提示级）；
  ② 消费者：R2 假设生成边界提示 + 报告边界段；③ 裁掉丢什么：两族 218
  条（9.0%）无排除锚点（三引擎实测每期固定产出）。
- **测试守卫**：SKILL.md 声明段含「(d)」+「UI 信任指示层」与「(e)」+
  「移动端平台集成层」；「warn 注记不阻断」保留；反面分支：声明段不含
  新义务词。

### SWR-V3.24-004（D-4）召回率回归集扩三类样本

- **修复**：`tests/fixtures/recall_regression_set.json` 追加（去项目化形态，
  归属仅进 case_source 追溯字段）：
  - RECALL-002 L0b 生命周期 UAF：defect_class 异步对象生命周期竞态（回调
    持引用跨任务/跨进程释放），cwe ["CWE-416"]，expected_hypothesis
    H3 异步生命周期竞态 → 回调持引用释放竞态；
  - RECALL-003 L0d site-isolation：defect_class 跨进程资源 origin 归因错误
    （纹理/缓存/下载/导航目标绑定错误 origin），cwe ["CWE-863"]，
    expected_hypothesis H4 跨进程信任边界 → 资源归因错误 origin；
  - RECALL-004 L0c 图形边界：defect_class GPU 命令缓冲/着色器校验整数溢出
    导致越界写，cwe ["CWE-787","CWE-190"]，expected_hypothesis H2 远端控制
    解引用长度 + H4 跨进程信任边界 → GPU 命令缓冲越界。
- **裁决理由**：critical 188 条中 57% 落 L0b、L0d 为包络内最大单方向、
  L0c 为图形边界族——现有 RECALL-001 仅覆盖 L1a，阶段 0/6 验收对照力不足。
- **义务三问**：① 触发条件：仅测试/评估引用（与 RECALL-001 同契约，
  不进运行时）；② 消费者：test_v323 形态守卫 + 阶段 0/6 发现力对照；
  ③ 裁掉丢什么：L0b/L0d/L0c 三族验收无对照样本。
- **测试守卫**：fixture entries ≥4；RECALL-002..004 必填字段齐（id/
  defect_class/family/cwe/profile_signals/expected_hypothesis/case_source）；
  新条目除 case_source 外零项目 token；运行时路径文件不引用该 fixture
  （既有守卫覆盖）。

### SWR-V3.24-005（D-5）equivalent 档 real-target 抽验提示

- **修复**：SKILL.md R5 保真度判定段补提示级句子：equivalent 档结论强度
  低于 real_target——真实目标环境可及时，对 equivalent 实证候选做抽验
  （建模失真曾致等价实证结论被真实目标推翻的实录）；不强制不阻断。
- **裁决理由**：firefox lessons §三.2 DDL 未消化项——H3-F1 等价 harness
  实证被真实目标反证（四取三，1/4 推翻）；v3.23 D-1（所有权模型核实）
  覆盖了「如何写 harness」，未承载「结论强度分级 + 抽验建议」。
- **义务三问**：① 触发条件：candidate empirical.fidelity=equivalent 且
  真实目标环境可及；② 消费者：R5 实证阶段主代理 + 报告 fidelity 呈现；
  ③ 裁掉丢什么：该教训零机制承载（DDL 断链）。
- **测试守卫**：SKILL.md R5 段含「抽验」与「equivalent」；该句零项目 token；
  反面分支：该句不含「必须/强制」（提示级）。

## 裁除（裁决记录，本轮不实现）

- **SWR-V3.24-C-1** H3 义务化深耕 → 裁除：无新触发条件；H3 要点已覆盖
  L0b 全部机制形态（Chrome 106 条 critical UAF desc 形态无一超出）。
- **SWR-V3.24-C-2** L2a 度量改进 → 裁除：公告粒度问题，修复路径为外部
  数据工程，非 skill 机制；契约禁猜条款保留。
- **SWR-V3.24-C-3** 内部组件 escape 专项（L2d 263）→ 裁除：攻击面分类非
  机制缺口，R1 表面测绘天然覆盖协议端点；实践注记入 recall_eval §4。
- **SWR-V3.24-C-4** 移动平台分支 → 裁除（本次）：使命外，占比 4.3% 低危；
  产品线扩展另议。
