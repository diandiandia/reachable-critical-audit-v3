# SWR V3.19 — 设计规则（2026-09-02）

## SWR-V3.19-001（D-1 correction_record 双形态 lenient）

`assert_ledger` 的 adjudication_verification 检查（evidence_ledger.py:436-437）
对 `correction_record` 条目按形态分派：dict 条目走 demote_to/adjudication_verification
检查（现状语义零变化）；str 条目 lenient 跳过（注记形态, 非裁决形态）。
**不改写任何字段**。数据模型速查补双形态注记。测试：纯 str 队列零崩溃 +
warn 语义不变 / 纯 dict 条目检查照常触发 warn / 混形态队列 lenient 且零改写。

## SWR-V3.19-002（D-2 步骤 0 缺陷可达性区分）

`_build_prompt` 步骤 0 块尾增提示级一句（库型目标适用）：
"库型目标（target_kind=library）下公共 API 静态存在即攻击面只解决『面存在』；
sink 可达 ≠ 缺陷可达——claim 声明（crash/oom/rce 等）之前必须给出具体缺陷
机制的静态证据（无门校验/回绕算术/越界写窗等 file:line），证据不足时
claim_type=other 并在 evidence 写明『结构性可达, 缺陷未确证』。"
测试：导出 verify payload 的 prompt 含该句（库型目标）；非库型目标不强制
（本句为通用提示, 不按 target_kind 条件渲染——措辞自身含条件语义）。

## SWR-V3.19-003（D-3 claim=other 实质机制优先实证提示）

SKILL.md R3.5-N 抽样条款与 R5 裁决条款各增一句（提示级）：
复活波抽样与实证裁决时，claim=other 但携带"机制静态确证"信号（证伪 0 票 +
证伪者补强 strengthened 非空 / 双证伪者确认机制属实）的候选，优先纳入实证池
——claim=other 的实证豁免不遮蔽已静态确证的实质机制。测试：SKILL.md 条款文本存在。

## SWR-V3.19-004（D-4 实证降级簿记契约明示）

SKILL.md R5 实证证伪条款与数据模型速查增明示：主代理把候选从 NEEDS_REVIEW/
REACHABLE 实证降级为 UNREACHABLE 时，必须同步写候选级
`resurrection_review {revived: false, outcome: "实证证伪原因"}`（gate ③c
簿记契约; 机制 v3.2.2 已存在, 本条只明示裁决动作与簿记字段的对应关系）。
测试：SKILL.md 两处文本存在。

## SWR-V3.19-005（D-5 ASan-dcheck 探针条目）

ENVIRONMENT_PROBES.md 增条目（sanitizer 构建变体）：
"sanitizer 实证变体必须关闭 dcheck（is_asan + dcheck_always_on=false）——
dcheck 开启时 DEBUG 层不变量（DCHECK/DEBUG-only 校验）会在畸形输入到达
目标 sink 之前前置拦截, ASan 精确定位被阻（快照 blob 实证实录）; 若只有
dcheck 开启的 sanitizer 变体, 实证结论须注明前置拦截点与未到达 sink 的
事实。" 测试：条目文本存在 + 去项目化（DEPROJECT_BLACKLIST 零命中）。

## SWR-V3.19-006（D-6 复活第 9 维：构建配置矩阵）

resurrect_prompt 复活维度清单新增第 9 条（提示级）：
"9. 构建配置前提是否已枚举（指针压缩/sandbox/特性开关/GC 模式等 build-config
维度）——默认构建可能把内存破坏路径变成 OOM/拒绝路径, verifier 未按配置矩阵
陈述影响的阻断论证不完整（noPC 变体实证实录）"
测试：resurrect_prompt 输出含第 9 条文本；既有 8 条零变化。

## 兼容性不变式

全量 400 基线零回退；六门禁①-⑧判据语义零改动；队列数据模型零改动（D-1 为
读取侧 lenient）；旧队列复跑零新增告警（V8 真实队列复跑为验收对象——其
correction_record 为 str+dict 混形态, lenient 后 assert_ledger 零崩溃零新增 warn）。
