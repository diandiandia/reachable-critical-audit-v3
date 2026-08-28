# SYSTEM DESIGN V3.9 — 缺陷修复版：R4 收集守卫 / 报告渲染 / 门禁收口（Pillow 审计复盘）

> 版本基线：v3.8（任务书已含 v3.8 条款）→ **v3.9**。来源：Pillow 审计运行复盘
> （lessons/SKILL_LESSONS_Pillow.md「Skill 缺陷清单」段，10 条原始发现）。
> 本版不改变阶段骨架，不改变门禁①-⑧判据语义（③ 新增子判据 ③d，见 D8）。

## 1. 问题域（P0/P1/P2 原始发现 → 逐项复查结论）

| # | 原始发现 | 代码复查结论 | 处置 |
|---|---|---|---|
| P0-1 | R4 schema 漂移超出 r4-collect 自适应范围 | **属实**。`_adapt_r4_finding` 只覆盖 evidence-array/r3-link-dict/severity/recommendation 四类；Pillow 实测漂移为 cwe 字符串、call_chain 字符串、location 别名、surfaces 别名、tracked_surfaces 整体缺失五类，全部不在覆盖集。无 r4_guard 等价物（R2 有 r2_guard） | 修复 D1 |
| P0-2a | 附录 A 渲染"无 NEEDS_REVIEW 候选"而队列有 1 条 | **属实，根因精确定位**：`_render_appendix_a_needs_review` 按 `status == "NEEDS_REVIEW"` 过滤，但 collect 终态写 `status=VERIFIED` + `verdict=NEEDS_REVIEW`——语义错位 | 修复 D2a |
| P0-2b | B.2 语言覆盖表 surfaces/候选全 0 | **属实，根因精确定位**：表内 join 用原始字符串键——surface.lang 是 "python"/"c"（R1 归一化后），language_inventory 行 lang 是 ".py"/".c"（扩展名形态），两侧词汇不匹配致计数恒 0 | 修复 D2b |
| P0-2c | R4 finding 位置列恒 "-" | **属实**：`_render_problem_list` R4 行硬编码 "-"，不消费 call_chain[0]/location | 修复 D2c |
| P0-3 | SKILL.md 记载已裁除的 `surface_mapper.py repair` | **属实**：SKILL.md:346 无裁除注记。**姊妹缺陷**：workflow_export.TOOLING_VERSION="3.7" 落后两版（实际 v3.8） | 修复 D9 |
| P1-4 | R1 任务书缺双向核实条款（B-001/S-CDEC-008 两次误报） | **属实**。均被 R2 filter 拦截但各浪费一轮 | 修复 D6 |
| P1-5 | tracked_ids 无机械支持 | **部分属实，收窄**：`_tracked_ids` 内部函数已存在（B.3/B.5 消费），但 ①读 hypotheses.json 而非 r2_filter_result.json——drop/bc 条目的 surface_ids 不进入覆盖集（SWR-V3.4.6-002 契约被静默违背，假缺口风险）；②无 CLI stage，门禁⑦ 准备靠主代理手写 union 脚本 | 修复 D3 |
| P1-6 | assert_ledger 失败输出只报一行 | **撤销**（防义务棘轮）：代码复查显示 assert_ledger 返回全部 blocking 违规列表，Pillow 那次确实只有 ⑦ 违规。无缺陷，不修 | 记录 |
| P1-7 | workflow-script export 不落盘 payload | **属实**：next_step 指示"从落盘文件整读整传"但导出只打 stdout | 修复 D5 |
| P2-8 | "check-after-op + 循环不变量"被两 agent 误判为缺陷 | **属实**（BcnDecode put_block 两轮误判） | 修复 D7（新清单） |
| P2-9 | R4 confirmed finding 无内建独立复核 | **属实**：R3.5 不覆盖 R4 通道；Pillow H-1/H-4 全靠主代理自发从零复现兜底，且兜底抓到 H4-1 假阴性陷阱（symlink 目录位置）。放行方向必须对抗复核（REQ-V3.2-021 精神）在 R4 通道缺位 | 修复 D8（门禁③d） |
| P2-10 | cve-ghsa-draft 零中文自检无脚本 | **属实** | 修复 D10 |

## 2. 方案决策（逐项）

### D1. R4 收集前置守卫（r4-guard）
- 位置：`tools/batch_verify.py` `_adapt_r4_finding` 扩展 + `stage_r4_collect` 前置校验段。
- 归一化扩展（自动，写 flags）：cwe 字符串→列表（按 "CWE-\d+" 与 "A / B" 分隔拆分）；
  call_chain 字符串→单元素列表；location 列表（dict 有 file/line）→ call_chain 字符串列表
  （仅当 call_chain 缺失）；`surfaces` 别名→tracked_surfaces（记 `mapped_surface_ids` 溯源）。
- 硬失败语义（阻断合并，exit 1）：input_surface.json 存在时，finding 无 tracked_surfaces
  且无任何可恢复别名 → 打印 `R4_TRACKED_MISSING` 诊断（含 hypothesis/title/有效 id 前缀示例），
  **该 hypothesis 整体不合并**——静默缺簿记比拒收更贵（门禁⑦ 假失败会反向制造手工补救）。
- 义务入库三问：①触发=每次 r4-collect；②消费者=门禁⑦ 覆盖率簿记、主代理收尾；
  ③裁掉丢什么=Pillow 实测 H7 13 面缺失、主代理手写 normalizer。

### D2. 报告渲染三修
- D2a：附录 A 过滤改为 `status == "VERIFIED" and verdict == "NEEDS_REVIEW"`
  （旧队列 status=="NEEDS_REVIEW" 亦匹配——双语义容忍，同 load_lenient 先例）。
- D2b：B.2 两侧 lang 经 `_norm_lang` 归一后 join（".py"→python、"c"→c），
  缺失/unknown 归 "unknown" 桶。判据①列语义不变。
- D2c：问题清单/详情 R4 行位置列取 `call_chain[0]`（D1 归一化后恒为 file:line 形态）
  或 `location` 字段；皆缺 → "-"（降级占位铁律不变）。
- 三问：①触发=每次 --stage report；②消费者=报告读者（清单/覆盖表/附录）；
  ③裁掉丢什么=Pillow 三处手工编辑（违反"队列唯一事实源"）。

### D3. tracked-ids 机械化
- `_tracked_ids` 改读 r2_filter_result.json（keep/drop/boundary_confirmations 三组
  surface_ids，缺失字段自动从 hypotheses.json 反查——SWR-V3.4.6-002 语义）∪
  hypotheses.json 兜底 ∪ queue.r4_findings.tracked_surfaces ∪ coverage_bridge。
- 新 stage `--stage tracked-ids`：打印 `{total, tracked, missing[]}` 并写
  `_tracked_ids.json`——主代理可直接喂 assert_ledger surface_data。
- 三问：①触发=门禁⑦ 前；②消费者=assert_ledger/B.3/B.5 渲染；③裁掉=每次手写 union 脚本。

### D4（撤销）— assert_ledger 逐门输出
- 复查结论：现有契约 `(ok, violations)` 已枚举全部 blocking 违规（Pillow 单⑦失败时
  输出即单行）。**不做修改**——义务棘轮警示（无失误案例支撑的输出增强不做）。

### D5. export 落盘 payload
- `stage_workflow_script` 将 result.payload 落盘 `.audit_results/<mode>_payload.json`
  （写入状态走 stderr，stdout 纯 JSON 契约不变）；next_step 文本引用该路径。

### D6. R1 任务书双向核实条款
- `task_templates/surface_map_domain.md` 强制要求段新增通用条款（机制形态描述，
  零项目名）：命中共享 helper/allocator/工厂时，边界声称必须沿调用链双向核实——
  "被调函数内有检查" ≠ "调用者未挡"，反之"被调函数缺检查" ≠ "调用者未校验"；
  判"缺检查"前须 Read 调用者与被调者两侧并各引证据行。

### D7. 新检查清单 CK-POSTOP-INVARIANT
- 通用条目：危险操作**之后**的边界检查可能安全——判缺陷前必须证明保护性循环
  不变量不成立（步进对齐/上界预约束/首块特例）。binding.cwe=[787,125]，
  keywords 中英双形态；applies_to=[verifier, refuter]。库 29→30。

### D8. 门禁 ③d — R4 confirmed 独立复核
- 判据：confirmed 假说的 finding 满足 `severity ∈ {high, medium, critical}` 且
  empirical_result 以 CONFIRMED 开头 → 必须有 `independent_review`
  （{by, method, artifacts}）或非空 `r3_link`（已过 R3.5 通道）。缺 → blocking 违规。
- 豁免：`require_r4_independent=False` 仅复跑旧队列（同 ⑧/③c 豁免先例，产出 warn 注记）。
- B.5 增行；问题详情 R4 段渲染 independent_review。
- 三问：①触发=R4 confirmed High/Medium/Critical + CONFIRMED 实证；②消费者=门禁③d
  行、报告详情段；③裁掉丢什么=Pillow H-1-F1/F2、H-4-F1 无对抗复核，主代理 ad-hoc
  兜底才抓到 H4-1 假阴性陷阱。

### D9. 文档漂移修复
- SKILL.md:346 repair 描述追加"（v3.5.2 已裁除；行号裁决为 R1.3 主代理手工职责）"。
- workflow_export.TOOLING_VERSION "3.7"→"3.9"（SWR-V3.4.4-008 版本守卫数据本身漂移）。

### D10. cve-ghsa-draft 零中文检查脚本
- 新 `tools/check_no_cjk.py`（该 skill 目录内）：统计 CJK 字符，逐行报告，
  `--max <n>` 阈值默认 0，exit 1 超限；支持 `--ignore-blocks 'Step 4'` 排除
  目标系统原始日志块（唯一例外条款的机械载体）。SKILL.md 自查清单引用。

## 3. 通用性自检（第一原则三禁止 × 每项）

| 项 | 三禁止①无项目名 | 三禁止②语言通用 | 三禁止③无路径锚定 |
|---|---|---|---|
| D1 | 归一化规则全机制形态 | 与语言无关（纯 schema） | 无 |
| D2 | 渲染逻辑零项目 token | B.2 经共享 alias map 任意语言 | 无 |
| D3 | 无 | 无 | 无 |
| D5 | 无 | 无 | 无 |
| D6 | 条款写机制形态（helper/allocator），不含 BcnDecode/TgaRle 例证 | 语言无关措辞 | 无 |
| D7 | 清单正文机制形态（步进对齐/不变量），例证留在 source_lessons | 语言无关 | 无 |
| D8 | 无 | 无 | 无 |
| D9/D10 | 无 | 无 | 无 |

## 4. 验收判据（Phase 3.9）

1. 全量回归绿（243 基线 + 新增 test_v39 ≥ 12 用例）。
2. `signature_lib.py selfcheck /root/Pillow` exit 0（含去项目化运行时资产扫描）。
3. **Pillow 真实队列复跑**：门禁含 ③d 全 PASS（backfill independent_review 后）；
   重跑 `--stage report` 后：附录 A 渲染 CAND-001、B.2 计数非零、R4 位置列非 "-"，
   主代理**零手工编辑**渲染产物（仅保留三、修复建议与结论段）。
4. 一个未审计新项目的完整流程验收另行安排（非本版阻断项，同 v3.5.2 先例）。
