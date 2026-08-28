# REQ V3.9 — 系统需求（Pillow 审计复盘缺陷修复）

> 上游：SYSTEM_DESIGN_V3_9.md。编号规则：REQ-V3.9-NNN。
> 每个义务入库项过三问（触发条件/消费者/裁掉丢什么）——见方案 D1-D10。

## 功能性需求

- **REQ-V3.9-001** r4-collect 前置守卫：`_adapt_r4_finding` 归一化覆盖
  cwe 字符串→列表、call_chain 字符串→列表、location 别名→call_chain、
  `surfaces` 别名→tracked_surfaces（记 mapped_surface_ids 溯源）。
- **REQ-V3.9-002** r4-collect 硬失败语义：input_surface.json 存在且 finding 的
  tracked_surfaces 缺失且不可恢复 → 该 hypothesis 不合并、exit 1、
  输出 R4_TRACKED_MISSING 诊断（含有效 id 前缀示例）；canonical 输入零变化。
- **REQ-V3.9-003** 报告附录 A：按 `status==VERIFIED 且 verdict==NEEDS_REVIEW`
  （或旧队列 `status==NEEDS_REVIEW`）渲染候选行 + 成因双分 + 同事实映射。
- **REQ-V3.9-004** 报告 B.2：surface.lang 与 language_inventory.lang 双侧经
  共享别名归一后 join；归一失败归 unknown 桶；计数从 input_surface.json 现场重算。
- **REQ-V3.9-005** 报告问题清单/详情 R4 行位置列：取 call_chain[0]（file:line 形态）
  或 location 字段；皆缺降级 "-"。
- **REQ-V3.9-006** `--stage tracked-ids`：机械计算（r2_filter_result.json 三组
  surface_ids 优先 ∪ hypotheses.json 兜底 ∪ R4 tracked_surfaces ∪ coverage_bridge）
  ∩ input_surface ids，输出 {total, tracked, missing[]} 并落盘 _tracked_ids.json。
- **REQ-V3.9-007** export 落盘 payload：stage_workflow_script 写
  `.audit_results/<mode>_payload.json`，next_step 引用该路径；stdout JSON 契约不变。
- **REQ-V3.9-008** R1 任务书双向核实条款（机制形态，零项目名）：
  命中共享 helper/allocator/工厂时边界声称须沿调用链双向核实，判"缺检查"前
  Read 调用者与被调者两侧并各引证据行。
- **REQ-V3.9-009** 新检查清单 CK-POSTOP-INVARIANT（checklist_library 29→30）：
  危险操作后置检查 + 循环不变量论证；判缺陷前须证明不变量破坏。
- **REQ-V3.9-010** 门禁 ③d：confirmed finding（severity∈{high,medium,critical} 且
  empirical_result 以 CONFIRMED 开头）必须有 independent_review {by,method,artifacts}
  或非空 r3_link；缺失 = blocking 违规；`require_r4_independent=False` 豁免旧队列
  复跑（warn 注记）；B.5 增行、问题详情 R4 段渲染该字段。
- **REQ-V3.9-011** 文档漂移修复：SKILL.md repair 描述加裁除注记；
  workflow_export.TOOLING_VERSION 升至 "3.9"。
- **REQ-V3.9-012** cve-ghsa-draft 增 tools/check_no_cjk.py（CJK 计数逐行报告、
  --max 阈值默认 0、--ignore-blocks 排除原始日志块、exit 1 超限），SKILL.md 自查清单引用。

## 非功能性需求

- **REQ-V3.9-013** 通用性：所有运行时资产（模板/清单/代码/脚本）零项目名、
  零 /root/ 绝对路径、语言无关或按 lang 分派——signature_lib 去项目化扫描须绿。
- **REQ-V3.9-014** 回归零回退：243 基线测试全绿；canonical 输入行为不变
  （r4-collect canonical 零变化、render 铁律"可选输入缺失降级占位不抛异常"保持）。
- **REQ-V3.9-015** 验收：Pillow 真实队列复跑——六门禁（含 ③d）全 PASS，
  报告渲染三处缺陷消失且主代理零手工编辑（修复建议段除外）；
  新增 test_v39 ≥ 12 用例。

## 撤销记录（防义务棘轮）

- **REQ-V3.9-NONE（原 P1-6）**：assert_ledger 逐门输出——代码复查确认现有
  `(ok, violations)` 契约已枚举全部 blocking 违规，无失误案例支撑，不做修改。
