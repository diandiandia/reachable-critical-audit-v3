# SWR_V3_23 — 每条修复一条 SWR（含裁决理由 + 测试守卫）

## SWR-V3.23-001（D-1）: fidelity=equivalent 所有权模型核实条款

**裁决理由**: H3-F1 实案证明"机制复刻"与"生命周期复刻"是两个独立保真维度——
pmce/fontentry harness 通过了函数形态复刻、门禁与复核，但所有权模型（家族强引用层）
缺失导致人为释放时序在真实代码不可达。条款形态：**提示级**——在 fidelity 三档条款
（SKILL.md:1051）补一段：`equivalent` 档 harness 的 fidelity 判定必须含**所有权模型
核实**——列出目标对象在真实代码中的引用持有图（谁 AddRef/谁释放/释放时机），harness
的交错时序必须能映射到真实持有图的某条释放路径；无法映射的释放时序不得作为缺陷前提。
不自动改写、不新增门禁（六门禁 ③ 仍按实证键判级，此条款约束"equivalent 证据能否支撑
REACHABLE 前提"的裁决质量，违规表现为 warn 提示）。

**测试守卫**: test_v323 断言 SKILL.md 含该条款关键词（所有权模型/引用持有图）+
harness_manuals 中核对步骤存在；反面：条款不出现"自动改写/门禁名新增"字样（修法形态
纪律守卫）。

## SWR-V3.23-002（D-2）: 发现包络边界声明条款

**裁决理由**: 85046 实案证明包络外区域（JIT 优化正确性层）真实存在且会造成隐含
"全覆盖"误导；CFNetwork/libsoup 证明闭源依赖边界同样需要声明。条款形态：R6 报告层
**提示级**条款——报告「修复建议与结论」段须附「发现包络边界声明」：本审计覆盖
[输入面→语义轴→sink] 的输入处理缺陷；**不覆盖**（a）JIT/编译器优化正确性层
（类型追踪/去优化正确性——需差分/模糊测试通道），（b）闭源依赖内部实现，
（c）非目标平台变体。无新门禁名、无新强制义务（缺失声明 = warn 注记不阻断，
与既有"报告防覆盖"等 warn 形态一致）。

**测试守卫**: 渲染器/报告模板含边界声明段的默认文案（零项目名）；SKILL.md 含条款；
反面断言无新 gate 名。

## SWR-V3.23-003（D-3）: JIT 正确性假设族 + CWE-843 入表 + profile jit 信号

**裁决理由**: 假设空间缺"编译器类型追踪不一致"族 → 85046 类缺陷无法被生成。三处修复：
1. 严重度机械映射表：`严重` 档 MEMORY-SAFETY 括号补 `843`（类型混淆与 787/125/416 同档——
   类型混淆的直接后果即内存破坏）；
2. surface_map_domain.md 语义轴测绘段补「JIT 优化正确性层轴」（提示级，profile 门控：
   仅 generation_layers 含 jit 时注入）——轴内容：编译器 map/类型追踪、去优化帧正确性、
   归约内联的 elements-kind 假设；假设义务：该轴一轴一族假设（如"归约/内联改变
   elements-kind 假设 → 类型混淆 CWE-843"）；
3. target_profile.py: generation_layers 建议逻辑补 jit 信号——信号源（去项目化）：
   源码树含 `src/compiler/maglev`、`src/compiler/turbofan`、`src/jit` 或
   `*jit*compiler*` 目录/文件。**不自动改写**：信号只进 `recommends`，主代理签收。

**测试守卫**: 严重度表含 843；surface_map_domain.md 含 jit 轴段且段内零项目名
（无 "v8"/"maglev 项目名"——maglev 是技术名允许？——纪律：技术名允许、项目名禁止；
守卫断言段内无 CAND- 形态与项目 token）；target_profile.py 对含 `src/compiler/maglev`
目录的 fixture 建议含 jit（fixture 构造临时目录树）。

## SWR-V3.23-004（D-4）: differential 通道发现化（提示级）

**裁决理由**: differential 模板（v3.17）只服务实证（"配置轴类声称首选"）；85046 的
发现通道是差分执行——把同一工具前移到 R2 假设生成作补充扫描（引擎类目标）。
条款形态：SKILL.md R2 假设生成段补提示——surface_model=semantic/hybrid 且
generation_layers 含 jit 的目标，R2 可对语义轴关键操作跑 differential 探针
（解释器 vs JIT / 多 JIT 层 / 元素类型变体）比对分歧，分歧即假设；**提示级、可选、
无新义务**（义务三问：触发条件=profile 信号；消费者=R2 假设生成；案例=85046）。
differential_probe.py 头部说明同步更新（不改探针逻辑）。

**测试守卫**: SKILL.md R2 段含该提示且带 profile 门控表述；differential_probe.py
docstring 含"discovery"用途说明；反面：条款不含"必须/强制"字样（无新义务）。

## SWR-V3.23-005（D-5）: 召回率回归集（fixture，无运行时机制）

**裁决理由**: 发现力无基线是阶段 6 验收的结构性缺口；回归集作为 fixture（第一原则：
回归锚点仅限测试）提供"已知缺陷→预期假设族"语料，阶段 0 复盘评估与 skill-optimizer
阶段 0 引用为评估输入。**不建运行时度量工具、不建新命令**（过设计防线：消费者不足，
先语料后工具）。
fixture 形态：`tests/fixtures/recall_regression_set.json`，条目：
`{id, defect_class, family, profile_signals, expected_hypothesis, case_source}`
（首样本: CVE-2026-85046——defect_class=JIT map-transition type confusion,
family=MEMORY-SAFETY/CWE-843, profile_signals={surface_model:semantic,
generation_layers:[jit]}, expected_hypothesis="归约内联改变 elements-kind 假设",
case_source=v8 lessons 召回复盘 1）。case_source 允许项目名（追溯字段纪律）。

**测试守卫**: test_v323 断言 fixture 可加载、首样本字段齐全、且**不被运行时路径
引用**（grep 运行时代码无 recall_regression_set——第一原则守卫）。

## SWR-V3.23-006（D-6）: R4 任务书注入 R2 进行中结论

**裁决理由**: WebKit 二.1 实案——R4/R2 并行时结论冲突至 gate ③b 才暴露。
条款形态：biz_hypothesis.md 补注入条款：主代理派发 R4 时须在任务书附带「R2 进行中
结论」段（与本假说 surface 相关的 keep/drop 条目+理由；R2 未完成则标注"R2 未出结论"）。
提示级：无 R2 结论时任务书不 fail。

**测试守卫**: biz_hypothesis.md 含注入条款段；零项目名。

---

## 共性约束

- 全部条款零新门禁名、零新强制义务、零自动改写（修法形态纪律）
- 运行时正文零项目名（maglev/turbofan 为通用技术名，保留）
- 版本链五件（TOOLING_VERSION→3.23、版本守卫、SKILL.md 增量段、
  REQUIREMENTS_TRACKING 手工段、资产计数守卫）
