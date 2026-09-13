# SWR_V3_41 — 修复裁决理由 + 测试守卫（v3.41）

来源: /root/hibernate-orm/.audit_results/lessons.md（2026-09-12 审计实录）

## SWR-V3.41-001（D-1, P1）: 复活 gap 渲染字段契约分离

**裁决**: `re_verify_gap` 语义为「复活重验标志」（bool，被 export 资格排除与 advisory 消费），gap 文本为另一契约字段 `resurrect_gap`（字符串，复活者 gap 原文）。渲染段误把 bool 当文本拼接是字段契约混淆——修复方向是分离而非改语义（bool 仍作条件）。
**理由**: 主代理已在本次审计中把 gap 文本写入 re_verify_gap 作工作区绕过，证明「文本字段 + bool 标志」分离契约是自然形态。
**测试守卫**: 见 REQ 表。

## SWR-V3.41-002（D-2, P1）: 报告段 import 路径对齐 src

**裁决**: `_gates_for_report` 与 `_render_appendix_b_process` 的 sys.path.insert 与同文件其余 5 处不一致（缺 `/src`），证据是本次报告 B.2/B.5 两处降级文案。修复为机械对齐，不改导入语义。
**理由**: 其余 5 处双插形态已运行多版本无回退，无新机制。
**测试守卫**: 见 REQ 表。

## SWR-V3.41-003（D-3, P2）: r4-collect claim_type 枚举告警

**裁决**: `_warn_r4_enums` 增补 claim_type 检查——非法值 warn + 建议映射（`source_fact`/`empirical_mechanism` → `other`；空串 → `null`），**只建议不自动改写**（纪律 #4：误猜风险>收益，v3.14 D-3/D-4 先例）。
**理由**: 与既有 verdict/severity 告警同形态（SWR-V3.8-003/004/005），消费者是主代理收尾归一；本次审计中 2 处非法枚举 + 2 处空串均靠主代理手工发现，机械告警可前置。
**测试守卫**: 见 REQ 表（含合法枚举零新增反面分支）。

## SWR-V3.41-004（D-4, P3）: verifier 任务书方言/平台语义矩阵条款

**裁决**: 步骤 4 阻断检测段增补提示级条款：「阻断论证引用单一方言/平台实测时，须逐格核实同族方言/平台的语义差异（转义字符/引号/空值语义等）——单格实测不得外推到语义相异方言族；同库对照证据（各方言自身实现，如 appendLiteral 系）是逐格核实的廉价锚点；外推必须显式标注覆盖格数」。
**理由**: CAND-006 复活翻转的根因是 verifier 把 H2 实测外推到 MySQL/Spanner 族。提示级不设强制义务（三问：触发条件=渲染类阻断论证时；消费者=verifier 判定质量；案例=CAND-006 复活 gap 原文）。与既有「步骤 5.2 编码矩阵单形态不得外推」（SWR-V3.25-003）同原则不同域，不重造。
**测试守卫**: 任务书含关键词字符串断言。

## SWR-V3.41-005（D-5, P3）: 清单 +1 CK-CHANNEL-ESCAPE-LEDGER

**裁决**: 转义责任下沉型设计（渲染器无转义、责任在上游）的全通道对账条目——同一函数族全部文本通道（注释/提示/字面量/标识符/格式模式类）逐条列渲染点与转义点，单通道防御 ≠ 全族防御。family=injection，keywords 绑定转义/append/comment/hint/literal/format 类端关键词。
**理由**: 本次审计同批三例（comment 有转义/hint 无/format 绕过闸门）。提示级清单条目，消费者=R2/R4 检查清单绑定机制（既有）。
**测试守卫**: 计数 50 + id 存在 + 追溯字段。

## SWR-V3.41-006（D-6, P3）: 先例 +1 逃生舱等价性

**裁决**: 「逃生舱类 sink 与既有无校验通道（如 native SQL 透传）等价 = 零能力增量 → 不立候选/归边界」裁决先例，附 CAND-005 复活实录为案例。
**理由**: 复活失败但产出边界论证是申报材料，先例化供主代理裁决复用。消费者=precedent_library 消费端（既有）。
**测试守卫**: 计数 19 + id 存在。

## SWR-V3.41-007（D-7, P3）: java 矩阵回填两格

**裁决**: seed java×MEMORY-SAFETY（Java 形态：越界索引/截断 cast——ArrayJavaType 枚举 ordinal、EnumJavaType fromLong 截断、SparseByteVector 文本构造器绕过门禁三例）与 java×TRUST-BOUNDARY（白名单 fail-open——JNDI URI 解析失败放行、字符串拆分路径绕过门禁两例），source_lessons 带日期与审计项目追溯（去项目化提炼：项目名只进追溯字段）。
**理由**: 命中率 5/10，两族形态本批确认问题密集且无格可查。
**测试守卫**: 两格存在 + 档位正确。
