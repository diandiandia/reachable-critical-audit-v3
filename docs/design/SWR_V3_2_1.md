# Reachable Critical Audit v3.2.1 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_2_1.md` 组件 M1~M9 导出的软件开发需求。
> 编号规则：SWR-V3.2.1-xxx；状态：未开发 / 开发中 / 已经完成开发。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.2.1 段）。日期：2026-08-17

## M1: target_kind 判定器（REQ-V3.2.1-001/002/004）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-001 | tools/target_kind.py：determine_target_kind() 六类信号（包清单/监听器/启动链/Dockerfile/README/发布物）+ 推荐值 + 证据 + 置信度 | 已经完成开发 |
| SWR-V3.2.1-002 | hybrid 判定：多组件信号相斥时按 component_hint 输出 component_kinds | 已经完成开发 |
| SWR-V3.2.1-003 | CLI：`--write` 落盘 .audit_results/target_kind.json；无参数时仅打印推荐 | 已经完成开发 |
| SWR-V3.2.1-004 | 主代理签收契约：verify_queue.target_kind 写入 + evidence_ledger 门禁⑧ target_kind_required（缺失→violation；--legacy-no-target-kind 仅复跑兼容） | 已经完成开发 |

## M2: verifier 任务书三段扩展（REQ-V3.2.1-003/010/012）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-010 | _build_prompt 步骤 0.5 模块可导入性预检（顶层包解析/扫描器吞错路径审查/broken_edge→NEEDS_REVIEW；application 强制、library 记录型） | 已经完成开发 |
| SWR-V3.2.1-011 | _build_prompt 步骤 5.5 消费端中间层枚举（write→read 注入族触发：缓存/门闩/降级层逐层列出 + 三查） | 已经完成开发 |
| SWR-V3.2.1-012 | target_kind 存在性规则段装载（application/library 两版，由 verify_queue.target_kind 选择；缺省读 target_kind.json；均缺不注入兼容旧队列） | 已经完成开发 |

## M3: shipped-config 盘点 workflow（REQ-V3.2.1-030）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-020 | workflow_export：SHIPPED_CONFIG_SCHEMA + export_script_shipped_config()（每含 config 组件 1 agent，提交值 vs 代码零值对照），脚本 lint 干净 | 已经完成开发 |
| SWR-V3.2.1-021 | 主代理收集流程：落盘 .audit_results/shipped_config.json {component, items[{file,key,committed_value,code_default,mismatched}]} | 已经完成开发 |

## M4: 清单库/先例库增补（REQ-V3.2.1-005/011/013）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-030 | checklist_library 新增 CK-IMPORT-REGISTRATION（4 步：顶层包解析/构建包含/扫描器吞错路径/扫描日志核对） | 已经完成开发 |
| SWR-V3.2.1-031 | checklist_library 新增 CK-CACHE-GATE-LAYER（4 步：中间层横向枚举/错误分支方向/写读形状/缓存键写路径） | 已经完成开发 |
| SWR-V3.2.1-032 | precedent_library 新增 PREC-TARGET-KIND-001（存在性规则矩阵，Newtonsoft.Json 先例）+ PREC-IMPORT-BREAK-001（导入断裂→条件候选，Lersosa CAND-004/009 先例） | 已经完成开发 |
| SWR-V3.2.1-033 | 绑定测试用例固化：import/DI/缓存/门闩类候选命中两条新清单 | 已经完成开发 |

## M5: evidence_ledger 扩展（REQ-V3.2.1-032）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-040 | r4_feedback 断言：H-7 findings 的 key:value 断言与 R3 REACHABLE 候选 gate 证据关键词冲突检测 → r4_feedback_conflicts[]（warn 级，不阻断 PASS） | 已经完成开发 |

## M6: r2_guard 扩展（REQ-V3.2.1-031）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-050 | gate 语义含"默认可达/默认开启"时，shipped_config.json 存在 → 提示强制追加第三层检查引用条款 | 已经完成开发 |

## M7: 组件角色派生（REQ-V3.2.1-021）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-060 | language_inventory 输出 component_role（frontend→client-only；scripts/headers→build-config；其余→server-side） | 已经完成开发 |

## M8: SKILL.md / 报告 / 判据措辞（REQ-V3.2.1-020/021）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-070 | SKILL.md：R0 target_kind 步骤 + 签收条款；R1.5 shipped-config 子任务；R3 三段扩展说明；门禁⑧ | 已经完成开发 |
| SWR-V3.2.1-071 | REQ_V3_2.md 判据①措辞修正（服务端组件语言判据 + 客户端组件边界面等价判据）；报告语言覆盖表组件角色列 | 已经完成开发 |

## M9: 测试（全部条目回归）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.1-080 | tests：target_kind（fixture→hybrid/Lersosa→application/单库→library）+ batch_verify 三段注入 + 门禁⑧ + r4_feedback 冲突 fixture + component_role + r2_guard 引用 + shipped-config 导出 lint | 已经完成开发 |
| SWR-V3.2.1-081 | 全量回归：既有 73 测试全绿 + 新用例通过 | 已经完成开发 |

## 附：SWR 状态汇总

| 模块 | 条目数 | 状态 |
|---|---|---|
| M1 | 4 | 全部已经完成开发 |
| M2 | 3 | 全部已经完成开发 |
| M3 | 2 | 全部已经完成开发 |
| M4 | 4 | 全部已经完成开发 |
| M5 | 1 | 已经完成开发 |
| M6 | 1 | 已经完成开发 |
| M7 | 1 | 已经完成开发 |
| M8 | 2 | 全部已经完成开发 |
| M9 | 2 | 全部已经完成开发 |
| **合计** | **20** | **全部已经完成开发** |
