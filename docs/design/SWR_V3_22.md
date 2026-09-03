# SWR V3.22 — 设计规则（2026-09-04）

## SWR-V3.22-001（D-1 size_tier 分支调序）

`size_tier`（surface_mapper.py:787-815）把 `if count > 2000`（super-large）
分支移到 `if n_langs > 2`（large 保底）之前。super-large 分支的
`domains_split` 已用 mixed_domains 变量（多语言兼容），调序零语义损失；
`n_langs > 2` 分支语义不变（仅作用于 ≤2000 文件的仓）。测试：构造
3+ 语言 + >2000 文件 fixture → tier 返回 super-large 且 two_phase=True
components 非空；2 语言 ≤2000 → 原行为不变（medium/large）；n_langs>2
且 ≤2000 → 仍 large（保底分支不受影响）。

## SWR-V3.22-002（D-2 claim=other 严重度封顶）

`_mechanical_severity`（tools/batch_verify.py:1798）cwe 命中分支内加：
`claim_type == 'other'` → 返回 `("medium", "claim_type(other) 结构性可达封顶;cwe:...")`。
`severity_override` 仍绝对优先（severity_for 先查 override）；R4 finding
走申报值归一化不经本函数——不受影响。containment 降档链不参与（medium
已是封底）。测试：claim=other + CWE-125 → medium；claim=crash + CWE-125
→ 严重（不变）；claim=other + override=high → high（override 优先反面）。

## SWR-V3.22-003（D-3 裁除记录）

取证裁定：SKILL.md 与 r35-collect 存储键一致用单数 `attribution_correction`
（SKILL.md:425/1055-1057）；主代理签写脚本误用复数属操作失误；warn 检查
代码（batch_verify.py:2246-2249）已双形态容忍。**无代码修复**；数据模型
速查补注记「attribution_correction（单数, r35-collect 存储键）」。

## SWR-V3.22-004（D-4 复活未选中自动簿记）

`stage_r35n_collect`（tools/batch_verify.py:609）落盘 dispatched 决策后：
扫描队列 UNREACHABLE 且无 `resurrection_review` 的候选——该候选在
`_resurrect_sample.json` 的 selected 集中则跳过（journal 缺失=异常, 交
主代理）；否则写 `{"revived": false, "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}`。
幂等：已有簿记跳过。不改写任何既有字段。测试：未选中候选自动簿记 +
幂等重跑零变化 + selected-无-journal-记录不写 + 已有簿记不覆盖。

## SWR-V3.22-005（D-5 refutation 证据预算与链阈值）

workflow_export.py:379-384：evidence budget 800→3000（边真实性证伪者的
核心输入是全链细节——3 例截断自愈实录）；chain 截断阈值 8→12，注记
（"见 verify_queue.json"）保留。resurrect 预算不变（budget=None 全关键段）。
测试：构造 >3000 字符 evidence + 12+ 跳链的 refutation prompt → evidence
不被 800 截断、chain 保留 12 跳 + 注记。

## SWR-V3.22-006（D-6 R4 落盘契约）

biz_hypothesis.md 增：产出 JSON 同时写入 `.audit_results/_r4_hN.json`
（N=分配假说号）; 环境阻止写文件时最终回复末尾附 `UNWRITTEN: <原因>`
（R1/R2 同形契约）; 主代理 merge 条款——default_value_table 全量保留,
禁止精简（H4 15 行/H5 11 项/H6 8 域表丢失实录）。测试：模板含落盘路径
与 UNWRITTEN 条款。

## SWR-V3.22-007（D-7 决策签入工件）

SKILL.md R5 变更节 v3.21 D-1 条款增：empirical_feasibility 表落盘形态含
`decision {by, date, choice}`——用户决策必须签入工件, 主代理不得代选;
未签入即审计记录不完整（问责链）。测试：SKILL.md 条款存在。

## SWR-V3.22-008（D-8 裁除记录）

取证裁定：biz_hypothesis.md 前缀契约段已有 severity 分派（High/Medium/
Critical 声称类 → 填 null; 机制级文本仅 Low）——H3 写 SOURCE_FACT 源于
主代理派发简写提示词与模板不一致（操作失误, 非模板缺陷）。无代码修复;
失败模式「派发简写与模板不一致」并入 SWR-V3.22-011 蒸馏清单。

## SWR-V3.22-009（D-9 taskFile 薄封装默认化）

workflow_export refutation/resurrect 导出：prompts/taskFiles 同形
taskFile 化——每候选每视角任务书落盘 `.audit_results/_tasks/<mode>_<id>_<i>.md`,
payload 用 taskFiles 数组 + 一行 prompt（verify 已同形, 本版补齐对称）;
内联 prompts 保留为回退形态。SKILL.md workflow 规范条款明示：Mode W
派发默认薄封装（payload 104KB→8KB 实测）。测试：refutation/resurrect
导出 payload 含 taskFiles 且文件已落盘; 内联 prompt 回退仍工作。

## SWR-V3.22-010（D-10 R2 面覆盖前置核对）

SKILL.md R2 节（:148-150 后）增条款：假设生成完成后机械核对
`hypotheses[].surface_ids` 集合 ⊇ input_surface 全集——缺面即补生成假设
（门禁⑦ 前置化; 111/111 零缺口闭合轮 vs 缺口闭合三连重派对照）。
测试：SKILL.md 条款存在。

## SWR-V3.22-011（D-11 R6 蒸馏失败模式清单）

SKILL.md R6 节增条款：收官蒸馏必须逐项过已知失败模式 checklist——
截断自愈 / 契约漂移 / 簿记缺位 / 签收错名 / 落盘契约 / 决策记录 /
严重度映射。测试：SKILL.md 条款存在。

## 通用约束（本版全部 SWR 适用）

- 零改写（不自动修改 verifier/证伪者输出字段值）、零新门禁、零新阶段。
- 去项目化：运行时正文零项目名/零候选 id（案例只进设计件与追溯字段）。
