# Reachable Critical Audit Skill v3.2 — 系统架构设计文档

> **文档性质**：v3.2 架构设计（v3.1 的增量升级设计）。上游输入：
> ① 用户问题驱动的能力边界分析（混合语言项目审计能力，2026-08-17）
> ② v3.1 Phase 3.1.3 验收暴露的流程盲区（UNREACHABLE 无对抗复核、verifier 自我分级过低、
> 绑定关键词缺口——见 `ACCEPTANCE_V3_1.md`）
> ③ 15 语言战役 lessons（`lessons/W6_MORE_LANGS_FINDINGS.md` §1-24）
> v3.1 现行设计见 `SYSTEM_DESIGN_V3_1.md`；v3.1 已发布（运行时权威）。
> **日期**：2026-08-17
> **设计目标**：把 skill 从"单语言主导审计器"升级为"多语言复合项目审计器"，
> 同时补上验收暴露的防漏放缺口。v3.1 的骨架（输入面 → 假设 → 证据链 → 证伪 → 实证）不动。

---

## 0. 事实基础（v3.2 的问题证据）

| 维度 | 实测数据 | 结论 |
|---|---|---|
| 语言检测 | `_detect_lang` 扩展名计数取多数语言；`context` 输出单值 lang | WordPress 的 JS、etcd 的 shell、lighttpd 的脚本面在战役中被整体忽略 |
| FFI 边界 | v2.1 "边界即 sink"仅覆盖进程/IPC 边界；R1 四域无语言间边界域 | C 核心+Python 绑定类项目的最高危面（ctypes 所有权/unsafe 桥）无测绘点 |
| UNREACHABLE 对抗 | R3.5 只复核 REACHABLE 且 grade≥edge_proven | etcd 3 个基线被错误降级的发现在 313 复跑中被救回——单次审计内防漏放靠复跑兜底而非流程保证 |
| 签名匹配 | CODE_EXTENSIONS 索引本身多语言，但 L2 词族匹配无 lang 维度 | C 的 grep 词打到 Rust 代码=全噪音 |
| 清单/手册 | checklist_binder 语言无关 ✓；harness_manuals 按 lang 装载但取项目单值 | 混合项目实证按错语言手册选工具链 |

---

## 1. 三大问题域与 v3.2 对策

### P-A 语言维度缺失 → 语言成为候选级属性

**现象**：`surface_mapper._detect_lang` 输出多数语言；R1 任务书携带单一 architecture_context
（lang 单值）；`harness_runner.load_manual(lang)` 单值；verifier prompt 的 language 字段
取自项目多数语言。混合项目（C 核心 + Python 绑定 + Rust 扩展 + JS 前端）中，
少数语言的攻击面整体消失，且主导语言的词族/手册被错误套用到其他语言的代码上。

**V3.2 设计变更**：

1. **语言清单（language_inventory）**：`build_architecture_context` 输出
   `language_inventory: [{lang, file_count, component_hint}]`（组件归属提示：绑定层/核心/前端）。
2. **候选级 lang**：`input_surface.json` 的 surface 与 entry_point 增加 `lang` 字段；
   verify_queue 候选增加 `lang` 字段（从所属 entry_point 继承，LLM 假设直接标注）。
3. **上下文按语言分片**：R1 任务书架构背景按语言清单分片（每语言一段组件摘要），
   测绘 agent 按组件边界找 surface——同一 4 域框架不变，但每域任务书携带全部语言背景。
4. **按 lang 选择资源**：signature_matcher 的 L2 词族按 surface.lang 选择；
   harness_runner.load_manual 按候选.lang 装载；checklist_binder 语言无关（保持）。

**为什么能解决**：混合项目的问题不是"4 域不够"而是"所有代码被当作一种语言看"。
语言降级为候选/surface 的属性后，测绘、词族、手册、verifier 上下文全部按组件实际语言
工作——C 代码按 C 语义审、Python 绑定按 Python 生态审，互不污染。

### P-B 跨语言边界（FFI）盲区 → 边界升格为第一等 surface

**现象**：v2.1 REQ-19 的"边界即 sink"覆盖进程/IPC/DSO 边界，但**语言间 FFI 边界**
（extern "C" / ctypes / cffi / N-API / CPython 嵌入 / JNI）没有测绘点——它既不是网络面
也不是数据面，四域 agent 都看不见。混合项目的真实高危缺陷（所有权转移、ABI 不匹配、
跨语言内存释放、引用计数对称性、unsafe 桥不变量）全部集中在这个盲区。

**V3.2 设计变更**：

1. **R1 新增第五域：边界域（boundary）**：测绘任务书新增 boundary 域，探测
   **跨语言调用表**：每个 FFI 边界的 {调用方向, 语言对, 桥接文件:行, 边界类型
   （extern/ctypes/cffi/N-API/JNI/嵌入）, 数据流方向}。
2. **新检查清单 CK-FFI-BOUNDARY**（checklist_library 第 21 条）：所有权转移方向、
   unsafe 桥不变量、ABI/结构体布局一致性、跨语言释放责任、引用计数对称、
   序列化格式一致性（跨语言处统一约定）。
3. **新先例 PREC-MULTI-LANG-001**：同 sink 家族一致性断言按 **lang 维度分组**——
   裁决按每个组件所属语言的生态惯例分别进行（Rust 侧按内存安全先例、C 侧按缓冲区先例、
   动态语言侧按注入先例），同族一致性只在同 lang 组内强制。
4. **boundary surface 的可达性判定**：边界两侧分别做证据链，交叉验证在
   `cross_evidence` 字段落盘（两侧证据链的对接点即边界调用点）。

**为什么能解决**：把"语言间边界"从规则的注释里升格为测绘的第一等对象后，
(a) 边界两侧各自按母语语义验证，(b) 边界本身（所有权/ABI/序列化）成为独立候选，
(c) 交叉证据让"Rust 安全但 C 侧越界"这类复合缺陷可表达。

### P-C UNREACHABLE 无对抗复核 → R3.5-N 复活攻击

**现象**（313 验收实据）：R3.5 只复核 REACHABLE 且 grade≥edge_proven——防漏杀无防漏放。
etcd 3 个基线被错误降级 NEEDS_REVIEW 的发现（`\x00` 区间语义分歧、syncWatchers 物化、
lease quota 转换点）在复跑中被更深验证救回——证明单次审计内 UNREACHABLE 侧缺乏对抗压力。

**V3.2 设计变更**：

1. **R3.5-N 复活攻击**：对 UNREACHABLE 候选按 claim_type 严重度抽样做 N=1 反向复核
   （"尽力复活"证伪者：默认立场 refuted=true 意为"该清除判定被推翻"）。
   抽样规则：crash/oom/unbounded/xss 类 UNREACHABLE **全量**复核（与 gate ③ 声称类
   同权重）；其他类按 20% 抽样（最少 2 个）。
2. **复活裁决**：复活攻击成功（清除判定被推翻）→ 候选回 R3 重验（带复活者证据）；
   失败 → verdict 保持 UNREACHABLE，附 `resurrection_review: {refuter, outcome}` 记录。
3. **成本控制**：复活攻击单证伪者、证据要求轻量（找到一条 verifier 未枚举的阻断缺口
   或错误前提即可），与 REACHABLE 的 N=2 深度复核不对称——防漏放的成本远低于防漏杀。

**为什么能解决**：etcd 三连救回的本质是"错误降级只有靠复跑才发现"。
R3.5-N 把复跑才能获得的对立视角内建到单次审计流程中，用 1 个轻量 agent 换
"防漏放"覆盖，成本/收益不对称地划算。

### P-D 验收暴露的流程缺陷制度化（v3.1 遗留）

| 缺陷 | 313 验收处置 | v3.2 制度化 |
|---|---|---|
| verifier 自我分级过低（有完整边证据自标 static_only，akka CAND-004/etcd CAND-002） | 机械分级复核手工兜底 | **分级机械复核条款化**：collect 后必须对全部 REACHABLE 跑 `grade_verdict` 重算，差异写 `grade_recomputed_by`；verifier 任务书加注"evidence_grade 是证据的机械函数" |
| CK-UNBOUNDED-HOPS 绑定关键词缺口（"缓冲上限"表述未命中） | 313 中已补关键词 | 关键词回填流程化：每次复跑后发现绑定缺口 → 当日回填 + 绑定矩阵回归测试追加用例 |
| gate ③b 两缺陷 | 已修复 | 已在 v3.1 代码中，无额外动作 |

---

## 2. V3.2 总体架构（相对 v3.1 的增量）

```
                        ┌─────────────────────────────────────────────────────┐
                        │            审计编排器 Orchestrator v3.2              │
                        │  + language_inventory 装载 + lang 维度账本字段        │
                        └─────────────────────────────────────────────────────┘
                          ↑ 产出回写            │ 任务书下发（按语言分片的背景）
        ┌─────────────────┴──────────┐   ┌─────┴──────────────────────────────┐
        │  R1 输入面测绘层 v3.2       │   │  R2 假设层                          │
        │  4 域 + 新增 boundary 域    │   │  L2 词族按 surface.lang 选择        │
        │  surface/entry 带 lang      │ → │  假设带 lang                        │
        └────────────────────────────┘   └────────────────────────────────────┘
                          ↓
        ┌───────────────────────────────────────────────────────────────────────┐
        │  R3 证据链回溯 (verifier 按候选.lang 上下文) + 分级机械复核条款化       │
        └───────────────────────────────────────────────────────────────────────┘
                          ↓                              ↓
        ┌───────────────────────────────────┐  ┌────────────────────────────────┐
        │ R3.5 证伪 (REACHABLE, N=2)         │  │ 新增: R3.5-N 复活攻击            │
        │ 同族一致性按 lang 分组             │  │ (UNREACHABLE 声称类全量/N=1)     │
        └───────────────────────────────────┘  └────────────────────────────────┘
                          ↓
        ┌───────────────────────────────────────────────────────────────────────┐
        │  R5 实证抽验 (手册按候选.lang 装载; 混合项目按组件分别构建)              │
        └───────────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型变更（相对 v3.1）

| 文件 | v3.1 → v3.2 变更 |
|---|---|
| `architecture_context` | +`language_inventory: [{lang, file_count, component_hint}]` |
| `input_surface.json` | surface/entry_point +`lang`；surface +`boundary_kind`（boundary 域专用: extern/ctypes/cffi/N-API/JNI/embed） |
| `verify_queue.json` | 候选 +`lang`；+`resurrection_review` 字段；boundary 候选 +`cross_evidence` |
| `checklist_library.json` | +CK-FFI-BOUNDARY（第 21 条） |
| `precedent_library.json` | +PREC-MULTI-LANG-001（同族一致性按 lang 分组） |
| `signature_matcher` 输出 | 命中 +`lang`；L2 词族选择按 surface.lang |
| `r35_adjudication` | +`resurrection` 段（R3.5-N 结果） |

## 4. 组件变更清单（相对 v3.1）

| 组件 | 变更 |
|---|---|
| M1+ surface_mapper.py | `build_architecture_context` +language_inventory；`gen_surface_tasks` +boundary 域；normalize/validate +lang 字段 |
| M3+ signature_matcher.py | L2 词族按 surface.lang 过滤（词族表已有 per-lang 组织，加 lang 绑定） |
| M10 checklist_binder.py | 语言无关保持；CK-FFI-BOUNDARY 绑定规则（keywords: ffi/ctypes/extern/jni/n-api/绑定/所有权） |
| W1+ workflow_export.py | +R3.5-N 复活攻击模式（refutation-resurrect：N=1、抽样规则、复活裁决字段） |
| M4+ evidence_ledger.py | assert 门禁 +R3.5-N 完成度检查（声称类 UNREACHABLE 必须有 resurrection_review）；一致性断言按 lang 分组 |
| M5+ harness_runner.py | `load_manual` 按候选.lang（已在参数层支持）；混合项目多组件构建提示 |
| M11 precedent_library.py | +PREC-MULTI-LANG-001；match 加 lang 维度 |
| M12 r2_guard.py | 假设 schema +lang 字段 |
| 资产 | checklist 第 21 条 + precedent 第 21 条；harness_manuals +`mixed_build.md`（混合项目构建总纲） |

## 5. 阶段流程变更表（相对 v3.1）

| 阶段 | v3.2 变更 |
|---|---|
| R0 | +language_inventory 装载与校验（每语言组件摘要非空） |
| R1 | 4 域 → **5 域**（+boundary）；任务书按语言分片背景；surface 带 lang |
| R2 | L2 词族按 surface.lang；假设带 lang；boundary surface 生成跨语言假设 |
| R3 | verifier 上下文按候选.lang；collect 后分级机械复核（条款化） |
| R3.5 | REACHABLE N=2 不变；一致性断言按 lang 分组 |
| **R3.5-N（新）** | UNREACHABLE 复活攻击：声称类全量 N=1 + 其他 20% 抽样（最少 2）；复活成功回 R3 重验 |
| R4 | H4 检查清单 +CK-FFI-BOUNDARY 引用（跨语言信任边界破坏） |
| R5 | 手册按候选.lang；混合项目按组件分别构建 + mixed_build.md 总纲 |
| 报告 | +语言覆盖表（每语言 surface 数/候选数/结论）；FFI 边界表 |

## 6. 为什么能解决——根因→机制→因果链

| 问题域 | 根因 | V3.2 机制 | 因果论证 |
|---|---|---|---|
| P-A 语言维度缺失 | 多数语言检测 + 单值 lang 贯穿全流程 | language_inventory + 候选级 lang + 按 lang 选择词族/手册/上下文 | 混合项目的少数语言从"被忽略"变"按自身语义审"——语言属性化后每个组件获得与单语言项目同等的审计深度 |
| P-B FFI 盲区 | 边界即 sink 只覆盖进程/IPC；语言间边界无测绘点 | boundary 第五域 + CK-FFI-BOUNDARY + cross_evidence + PREC-MULTI-LANG | 混合项目最高危面从盲区变第一等 surface；边界两侧按母语语义交叉验证，复合缺陷（单侧安全+对侧越界）可表达 |
| P-C 防漏放缺口 | R3.5 只复核 REACHABLE | R3.5-N 复活攻击（声称类全量 N=1 + 抽样） | 错误降级在单次审计内获得对立视角；etcd 三连救回的成本从"一次完整复跑"降为"每候选 1 个轻量 agent" |
| P-D 流程缺陷 | 验收暴露的 4 缺陷 | 分级机械复核条款化 + 关键词回填流程化 | 手工兜底动作转为流程强制条款，缺陷不再靠复跑暴露 |

## 7. 关键设计决策与权衡

1. **boundary 域不拆分语言域**：保持 4+1 域（而非 per-lang 域）——语言是属性不是域，
   拆分会导致测绘 agent 数量随语言数爆炸；boundary 域专职跨界，4 域按语言分片背景。
2. **R3.5-N 抽样基线**：声称类全量 + 其他 20%（最少 2）——声称类与 gate ③ 同权重
   （错误清除的危害与错误申报对称）；抽样上限 8 个/项目防成本失控。
3. **复活攻击默认立场**：复活者"尽力复活"而非"尽力证伪"——任务书措辞方向决定产出质量
   （313 实测：证伪者以对抗立场产出补强向量；复活者以对抗立场产出缺口枚举）。
4. **同族一致性按 lang 分组**：跨语言同 sink 形态（如都叫 get_host）不强制一致——
   裁决生态不同；同 lang 组内保持 v3.1 一致性断言。
5. **不重跑 15 语言战役**：v3.2 是对混合项目能力的增量——单语言项目的 v3.1 结论不回退；
   验收用真实混合项目试审 + 单语言回归（任选 1 个 313 项目重跑确认零回退）。

## 8. 实施路线图

**Phase 3.2.1（数据层，1 周）**：language_inventory + surface/候选 lang 字段 +
boundary 域任务书 + CK-FFI-BOUNDARY + PREC-MULTI-LANG + mixed_build.md。
**Phase 3.2.2（流程层，1 周）**：R3.5-N 复活攻击（workflow_export 新模式 +
evidence_ledger 门禁 + 抽样规则）+ 分级机械复核条款化 + 词族 lang 过滤 + 一致性按 lang 分组。
**Phase 3.2.3（验收，1 周）**：混合项目试审（选型判据：≥3 语言组件 + 存在 FFI 边界 +
无 skill 相关先验的公开项目）+ 单语言回归（akka-http 重跑对照零回退）。
验收判据：① 语言覆盖表每语言 ≥1 surface 且非零候选 ② 全部 FFI 边界有 cross_evidence
③ 单语言回归结论与 313 一致（零回退）④ 六门禁 PASS。

## 9. 风险与缓解

| 风险 | 缓解 |
|---|---|
| boundary 域测绘 agent 对语言对不熟 | 任务书附语言对的两侧手册要点（harness_manuals 交叉引用） |
| R3.5-N 复活攻击误复活（把正确清除翻案） | 复活成功只回 R3 重验，不直接改 verdict；重验裁决权在主代理 |
| 混合项目验收选型难 | 选型判据写死（≥3 语言 + FFI 边界 + 公开项目）；备选：自造最小混合 fixture（C 核心 + Python ctypes + Rust cdylib） |
| 一致性按 lang 分组削弱同族一致性价值 | 分组只放宽跨语言组；同 lang 组断言强度不变（v3.1 先例继续生效） |

---

## 附录：v3.1 → v3.2 差异速查

| 维度 | v3.1 | v3.2 |
|---|---|---|
| 语言 | 项目级单值 | 候选级属性 + language_inventory |
| 测绘域 | 4 域 | 4+1 域（+boundary FFI 专项） |
| FFI 边界 | 规则注释级 | 第一等 surface + cross_evidence |
| 对抗复核 | R3.5 仅 REACHABLE | +R3.5-N UNREACHABLE 复活攻击 |
| 同族一致性 | 全项目断言 | 按 lang 分组断言 |
| 分级 | 机械复核手工 | 流程条款化（collect 后强制重算） |
| 验收 | 单语言三项目 | 混合项目试审 + 单语言零回退回归 |
