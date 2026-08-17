# Reachable Critical Audit v3.2.1 — 系统需求规格书（System Requirements）

> 从 `SYSTEM_DESIGN_V3_2_1.md`（问题域 P-A~P-D）导出的系统开发需求。每条附来源追溯与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.2.1 段）。日期：2026-08-17
> 编号规则：REQ-V3.2.1-xxx；优先级：P0=影响结论正确性，P1=影响效率/文档一致性

## 1. target_kind 判定与按型装载（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.1-001 | R0 新增 target_kind 判定：机械信号（包清单/监听器/README/Dockerfile/发布物）→ {application, library, hybrid} 推荐值 + 证据，落盘 .audit_results/target_kind.json | 设计 §2.1 | P0 | fixture→library/hybrid、Lersosa→application，与人工结论一致 |
| REQ-V3.2.1-002 | 主代理签收 target_kind 并写入 verify_queue.target_kind；未签收 → R3 不得启动（门禁级） | 设计 §2.1 | P0 | 缺 target_kind 的队列被门禁拦截 |
| REQ-V3.2.1-003 | verifier 任务书按 target_kind 装载存在性规则段：application=三层默认检查含 shipped 配置实际值+运行时注册+platform_precondition；library=公共 API 即边界、仓内调用者缺失非阻断 | 设计 §2.1 矩阵 | P0 | 库型候选任务书含"公共 API 即边界"条款；应用型含"运行时注册核实"条款 |
| REQ-V3.2.1-004 | hybrid 目标按组件分别判定（component_hint → per-component target_kind），候选从所属组件继承 | 设计 §2.1 | P1 | 混合项目候选 target_kind 与组件一致 |
| REQ-V3.2.1-005 | precedent_library 新增 PREC-TARGET-KIND-001（存在性规则矩阵，Newtonsoft.Json 先例） | 设计 §3 | P1 | 库型候选装载该先例 |

## 2. verifier 两盲区制度化（P-B）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.1-010 | verifier 任务书新增必做步骤"模块可导入性预检"：顶层包解析（find_spec/构建包含）+ DI/扫描器吞错路径审查 + broken_edge 标记（NEEDS_REVIEW 条件候选） | 设计 §2.2 | P0 | 任务书含该步骤条款；复跑中 CAND-004/009 在 R3 即落条件候选 |
| REQ-V3.2.1-011 | checklist_library 新增 CK-IMPORT-REGISTRATION（可绑定 import/DI/注册类候选） | 设计 §2.2、§3 | P0 | 清单存在且绑定矩阵含测试用例 |
| REQ-V3.2.1-012 | verifier 任务书新增必做步骤"消费端中间层枚举"：adapter↔domain 间缓存/门闩/降级层逐层列出 + 缓存层三查（错误分支方向/写读形状一致/缓存键写路径） | 设计 §2.3 | P0 | 任务书含该步骤条款；复跑中 CAND-007 门闩在 R3 被捕获 |
| REQ-V3.2.1-013 | checklist_library 新增 CK-CACHE-GATE-LAYER（缓存/门闩/降级类候选绑定） | 设计 §2.3、§3 | P0 | 清单存在且含三查条款 |

## 3. 判据措辞与报告（P-C）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.1-020 | REQ-V3.2-100 判据①措辞修正：服务端组件语言 ≥1 surface 且非零候选；客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据 | 设计 §2.4 | P0 | Lersosa TS 组件按边界面判据 PASS，无需 qualification 补丁 |
| REQ-V3.2.1-021 | 语言覆盖表新增"组件角色"列（server-side/client-only/build-config），由 component_hint 派生 | 设计 §2.4 | P1 | 报告覆盖表含组件角色且 TS 行角色=client-only |

## 4. H-7 前置化与反哺（P-D）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.1-030 | R1.5 追加 shipped-config 实际值盘点子任务：监听地址/tls_enable/认证开关的提交值 → shipped_config.json | 设计 §2.5 | P0 | 含 config 组件的盘点文件存在且含 tls_enable 实际值 |
| REQ-V3.2.1-031 | r2_guard 对"默认可达/默认开启"gate 假设强制引用 shipped_config.json（存在时） | 设计 §2.5 | P1 | gate 假设提示含 shipped-config 条款 |
| REQ-V3.2.1-032 | evidence_ledger 新增 r4_feedback 断言（warn 级）：R4 H-7 findings 与 R3 REACHABLE gate 证据冲突告警 | 设计 §2.5 | P0 | 复跑中 CAND-001/008 的 tls 零值错误被断言捕获（历史队列回放验证） |

## 5. 验收需求（Phase 3.2.1.3）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.1-040 | target_kind 判定准确：fixture→library/hybrid、Lersosa→application | 设计 §4 | P0 | 两项目判定与人工结论一致 |
| REQ-V3.2.1-041 | Lersosa 复跑零回退：终态与 v3.2 验收一致（5 REACHABLE / 2 条件 / 4 UNREACHABLE），且 P-B1/P-B2 在 R3 即捕获 | 设计 §4 | P0 | 零回退 + 前置捕获 |
| REQ-V3.2.1-042 | 六门禁 PASS + r4_feedback 断言生效 + install 到 skill 目录 | 设计 §4 | P0 | 门禁 PASS、install 完成 |

---

## 附：v3.2.1 需求 ↔ 问题域覆盖矩阵

| 问题域 | 覆盖需求编号 | 实现状态（2026-08-17） |
|---|---|---|
| P-A target_kind | 001-005 | 未开发 |
| P-B verifier 两盲区 | 010-013 | 未开发 |
| P-C 判据措辞 | 020-021 | 未开发 |
| P-D H-7 前置化/反哺 | 030-032 | 未开发 |
| 验收 | 040-042 | 未开始 |
