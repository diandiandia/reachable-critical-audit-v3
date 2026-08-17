# Reachable Critical Audit v3.2 — 系统需求规格书（System Requirements）

> **文档性质**：从 `SYSTEM_DESIGN_V3_2.md`（三大问题域 P-A~P-D）导出的系统开发需求。
> 每条附来源追溯（设计章节/组件 ID/lesson 出处）与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.2 段）。
> **日期**：2026-08-17
> **优先级定义**：P0 = 影响结论正确性/可问责性；P1 = 影响效率/可用性；P2 = 增强项
> **编号规则**：REQ-V3.2-xxx

## 1. 总体与语言维度需求（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-001 | 系统上下文输出 language_inventory：每语言 {lang, file_count, component_hint}（组件归属提示） | 设计 §1 P-A、SW_DESIGN_V3_2 M1 | P0 | 混合项目 context 含 ≥2 语言且各带组件提示 |
| REQ-V3.2-002 | 语言成为候选级属性：surface/entry_point/假设/候选均带 lang 字段，从所属组件继承 | 设计 §3、P-A | P0 | 混合项目队列中候选 lang 与所属组件一致 |
| REQ-V3.2-003 | R1 任务书架构背景按语言清单分片（每语言一段组件摘要），同一 4 域框架不变 | 设计 §1 P-A、§5 | P0 | 任务书含语言分片背景且非空 |
| REQ-V3.2-004 | L2 词族匹配按 surface.lang 选择；verifier 上下文语言按候选.lang 取 | 设计 P-A、M3+ | P0 | C 词族命中不出现在 Rust surface 上 |
| REQ-V3.2-005 | harness 手册按候选.lang 装载（混合项目按组件分别选择） | 设计 P-A、M5+ | P1 | 混合项目实证任务书引用两侧语言手册 |

## 2. FFI 边界域需求（P-B）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-010 | R1 新增第五域 boundary：测绘跨语言调用表 {调用方向, 语言对, 桥接文件:行, 边界类型 extern/ctypes/cffi/N-API/JNI/embed, 数据流方向} | 设计 §1 P-B | P0 | 混合项目全部 FFI 边界被枚举为 boundary surface |
| REQ-V3.2-011 | boundary surface 的可达性判定采用双侧证据链 + cross_evidence 落盘（边界调用点为对接点） | 设计 P-B | P0 | 每个 boundary 候选含两侧证据链与对接点 |
| REQ-V3.2-012 | checklist_library 新增 CK-FFI-BOUNDARY（第 21 条）：所有权转移方向/unsafe 桥不变量/ABI 布局一致性/跨语言释放责任/引用计数对称/序列化格式一致性 | 设计 P-B | P0 | 清单存在且 binding 可命中 ffi/ctypes/extern 类候选 |
| REQ-V3.2-013 | precedent_library 新增 PREC-MULTI-LANG-001：同 sink 家族一致性断言按 lang 维度分组，跨语言组不强制一致 | 设计 P-B | P0 | 跨语言同 sink 形态不触发一致性告警；同 lang 组保持断言 |
| REQ-V3.2-014 | R4 H4 检查清单引用 CK-FFI-BOUNDARY（跨语言信任边界破坏） | 设计 §5 | P1 | biz_hypothesis 模板 H4 段含 FFI 引用 |

## 3. R3.5-N 复活攻击需求（P-C）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-020 | UNREACHABLE 候选按 claim_type 抽样做 N=1 复活攻击（尽力复活立场）：crash/panic/oom/unbounded/xss/protocol_dos 类全量；其他类 20% 抽样（最少 2 个，上限 8 个/项目） | 设计 §1 P-C | P0 | 声称类 UNREACHABLE 全部有复活复核记录 |
| REQ-V3.2-021 | 复活成功（清除判定被推翻）→ 候选回 R3 重验（附复活者证据），不直接改 verdict；复活失败 → 保持 UNREACHABLE 附 resurrection_review 记录 | 设计 §1 P-C、§7 权衡 | P0 | 复活路径裁决权在主代理且全程可追溯 |
| REQ-V3.2-022 | workflow_export 新增 refutation-resurrect 模式（N=1、尽力复活任务书、复活裁决 schema） | 设计 M4+/W1+ | P0 | 模式可导出且 lint 干净 |
| REQ-V3.2-023 | evidence_ledger 门禁新增 R3.5-N 完成度检查：声称类 UNREACHABLE 无 resurrection_review → 违规 | 设计 M4+ | P0 | 缺复活记录的声称类候选被门禁拦截 |
| REQ-V3.2-024 | 复活攻击任务书措辞方向为"尽力复活"（枚举 verifier 未覆盖的阻断缺口/错误前提），证据要求轻量 | 设计 §7 权衡 3 | P0 | 模板含复活者视角条款 |

## 4. 验收暴露缺陷的制度化（P-D）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-030 | 分级机械复核条款化：collect 后对全部 REACHABLE 强制跑 grade_verdict 重算，差异写 grade_recomputed_by；verifier 任务书加注"evidence_grade 是证据的机械函数，非自我评估" | ACCEPTANCE_V3_1 §判据③、设计 P-D | P0 | 复跑中 verifier 自标 static_only 而证据齐全的候选被机械升级 |
| REQ-V3.2-031 | 绑定关键词回填流程化：复跑/验收发现的清单绑定缺口当日回填 + 绑定矩阵回归测试追加用例 | ACCEPTANCE_V3_1、设计 P-D | P1 | 缺口回填有测试用例固化 |

## 4.5 R6 lessons 回写需求（v3.2 新增，2026-08-17）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-060 | 审计六门禁通过后强制 R6 lessons 回写：生成 lessons/SKILL_LESSONS_<project>.md 描述遇到的问题 | 用户需求（审计后 lessons 问题文档）+ 战役教训（§1-24 手工回写） | P0 | 未执行 R6 审计不得闭合 |
| REQ-V3.2-061 | lessons 文档证据必须机械提取（裁决纠正/降级/复活/分级重算/paraphrased/验收记录），过程观察由主代理补充并区分标注 | R6 设计 | P0 | 文档含自动提取段与人工补充段分明 |

## 5. 门禁与报告需求

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-040 | 报告新增语言覆盖表（每语言 surface 数/候选数/REACHABLE 数/结论） | 设计 §5 | P0 | 混合项目报告含全部组件语言的覆盖行 |
| REQ-V3.2-041 | 报告新增 FFI 边界表（语言对/边界类型/裁决/cross_evidence 摘要） | 设计 §5 | P1 | 混合项目报告含边界表 |

## 6. 验收需求（Phase 3.2.3）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2-100 | 混合项目试审验收：选型判据 = ≥3 语言组件 + 存在 FFI 边界 + 公开项目（备选自造最小 fixture：C 核心 + Python ctypes + Rust cdylib）。判据：① 语言覆盖表每语言 ≥1 surface 且非零候选 ② 全部 FFI 边界有 cross_evidence ③ 六门禁 PASS | 设计 §8 | P0 | 三判据同时满足 |
| REQ-V3.2-101 | 单语言零回退回归：任选 1 个 313 项目（akka-http）重跑，结论与 313 验收一致 | 设计 §7 权衡 5 | P0 | 零回退 |
| REQ-V3.2-102 | 验收通过后合并 main + install 到 skill 目录 | 设计 §8 | P0 | 运行时权威切换有验收背书 |

---

## 附：v3.2 需求 ↔ 问题域覆盖矩阵

| 问题域 | 覆盖需求编号 | 实现状态（2026-08-17） |
|---|---|---|
| P-A 语言维度缺失 | 001-005 | 未开发 |
| P-B FFI 边界盲区 | 010-014 | 未开发 |
| P-C 防漏放缺口 | 020-024 | 未开发 |
| P-D 验收缺陷制度化 | 030-031 | 部分（030 的 grade_verdict 重算逻辑已在 v3.1 实现，条款化未做；031 未开发） |
| 门禁/报告 | 040-041 | 未开发 |
| 验收 | 100-102 | 未开始 |
