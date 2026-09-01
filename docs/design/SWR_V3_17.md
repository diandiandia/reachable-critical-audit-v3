# SWR V3.17 — 设计规则（2026-09-01）

## SWR-V3.17-001（D-1 生成层注册表）

`resources/generation_registry.json`：`{defaults_extensions: [...],
dsl_entries: [{ext, role, generates, lang_family}]}`。默认条目 = 现
CODE_EXTENSIONS 全集语义（零行为变化）；dsl_entries 只收多项目通用 DSL 族
（.proto→.pb.cc/.pb.h、.y/.l→.c、.fbs、.rl、.asn1、.idl），禁项目专属 DSL。
surface_mapper language_inventory / signature_matcher CODE_EXTENSIONS /
batch_verify _EXT_LANG 三消费端改为「注册表 ∪ target_profile.generation_layers」
合并视图（无 profile 时 = 现状）。生成物文件计入其 `lang_family` 语言组且带
provenance（generated_from）。测试：注册表默认视图与现状扩展名集一致 /
generation_layers 生效 / .tq 不入默认注册表（去项目化断言）/
_pb.cc 计入 cpp 组 / 旧 fixture 全绿。

## SWR-V3.17-002（D-2 super-large 档与两阶段测绘）

size_tier 档位扩展：<=500 medium / 501-2000 large（现状）/ **>2000
super-large**：agent 预算建议不变（4+1 组件清单 phase），输出增加
`components`（顶层模块目录清单：排除 SKIP_DIRS 后深度 1 目录，含文件计数与
构建清单信号 hits）与 `two_phase: true`。SKILL.md R1 与 surface_map_domain.md
模板：two_phase 时先 A 阶段机械组件清单落盘（components.json），后 B 阶段
按（组件 × 域）派发，45min 硬时限按组件给。旧三档阈值行为不变。测试：
1500 文件 → large 无 components / 2500 文件 → super-large 含 components 与
two_phase / 旧档位 fixture 输出零变化。

## SWR-V3.17-003（D-3 containment 维度）

候选 `containment ∈ {none, language, process_sandbox, hardware_isolated}`
（缺省 none）。severity 调整：process_sandbox → critical→high、
high→medium（medium 不再降）；language → 仅 critical→high；
hardware_isolated → 两档降（critical→medium 封底）。调整仅作用于机械映射
（override 仍绝对优先）；severity 来源串写 `containment:xxx`。collect 落盘
`containment`（显式或 `_derive_containment` 缺省推导：verifier 未给 → none
+ 无告警）；报告问题清单行渲染 `[沙箱收敛]`/`[语言防护]`/`[硬件隔离]` 标记。
测试：无 containment 字段候选 severity 与现状逐位一致（零回退）/
process_sandbox 787 → high / language 787 → high 且 89 → high 不变 /
hardware_isolated 787 → medium / override 优先 / collect 推导 none /
报告标记渲染。

## SWR-V3.17-004（D-4 差分执行实证模式）

`templates/harness/differential_probe.py`（langs:["any"]）：argv 驱动——
`--configs`（N 组运行命令，如优化层级/特性开关/GC 模式/编译旗标变体）、
`--corpus`（共享输入语料目录或生成器脚本）、`--compare`（exit_code|
output_hash|stderr_hash|rss_delta，可多选）、`--rounds`。判定：任一输入在
配置间结果分歧（exit 不同 / 输出 hash 不同 / RSS 单调性分歧）→ 分歧确认；
零分歧 → 防御/一致性确认。模板 docstring 含差分实证的边界（结果分歧 ≠
漏洞成立——供 verifier 定级，R5 采样协议沿用）。mixed_build.md 补章节：
gn/ninja/bazel/meson/depot_tools 类通用构建流程探测（工具存在性/生成物位置/
增量构建计时/目标产物路径），零项目名。测试：模板注册存在 langs any /
argv 必传契约（缺 --configs 报 usage exit 2）/ mixed_build 章节关键词存在 /
去项目化扫描零命中。

## SWR-V3.17-005（D-5 语义面投影）

`target_profile.surface_model ∈ {entry, semantic, hybrid}`（缺省 entry）。
semantic 模式：R1 增派语义轴测绘子智能体（surface_map_domain.md 新段）——
轴 = {id, 语义命名空间（语言特性族/字节码族/语法产生式族），anchor_files
[file:line], cardinality}；surface schema 增可选 `semantic_axis`（validate/
merge 容忍透传，旧形态零变化）。R2 假设生成沿轴采样（SKILL.md 条款：一轴
一族的假设义务）；门禁⑦ tracked_ids 语义轴当面计数（tracked-ids 命令读
input_surface 时轴并入）。hybrid = entry + semantic 双形态。测试：
validate 透传 semantic_axis 不 FAIL / 旧 fixture 面零变化 /
profile 签收 surface_model 落盘 / tracked-ids 轴计数。

## SWR-V3.17-006（D-6 运行时内存模型清单族）

checklist_library 新增族：
- `runtime-memory-model`（applies_to verifier/refuter，applicability_signals
  text 多词短语 "write barrier"/"generational collector"/"managed heap"/
  "gc root"/"tier transition"，禁裸词）：
  - CK-GC-WRITE-BARRIER（CWE-416/415 锚定：屏障缺失/乱序/生成代写路径）
  - CK-GC-ROOT-SCAN（CWE-416：根枚举遗漏/保守扫描假根/宿主栈扫描）
  - CK-TIER-TRANSITION（CWE-696：优化层级间状态不一致/去优化点假设）
  - CK-ALLOC-ESCAPE（CWE-787/125：托管分配逃逸 native 层/未检查尺寸）
- `generated-code`：CK-GENERATED-CODE（生成物 bug 的根在生成器源；生成
  文件不是可审计单元，必须沿 provenance 上溯到 DSL/生成器源行）。
纯数据，零 binder 代码改动（v3.12 先例）。测试：5 条新清单 schema 合法 /
applicability_signals 无裸词 gc/barrier/collector / 计数断言 39→44 同步。

## SWR-V3.17-007（D-7 佐证器 cap 缩放）

`scaled_caps(file_count)`：file_count<=2000 → 现状常量（60/40/300）；
>2000 → (120, 60, 600)；>8000 → (180, 80, 900)（上限常数化，不无限放大）。
expand_window/build 路径接受 caps 参数，缺省 = 现状常量（调用方零变化）。
测试：阈值边界三档 / 缺省调用零变化 / 300 常量仍在旧路径。

## SWR-V3.17-008（横切 target_profile 签收工件）

`tools/target_profile.py`（mirror target_kind.py）：信号（源文件数/扩展名
普查/构建清单 hits/README 关键词/GC-JIT 目录信号——全部机制形态）→
推荐 `{surface_model, generation_layers, scale_class, containment_default,
empirical_modes}` + 证据行；`--write` 落盘 `.audit_results/target_profile.json`；
主代理复核签收（`signed_by` + 手动覆盖）。消费者装载规则：文件不存在或未
签收 → 全默认（现状）。测试：默认信号推荐 smoke / --write 落盘与签收字段 /
未签收装载 = 默认 / 去项目化扫描零命中。

## 兼容性不变式

旧队列复跑零新增告警：所有新字段缺省 = 现状；新告警仅在被签收 profile 激活
后出现；六门禁①-⑧判据语义零改动；旧 fixture 全绿。
