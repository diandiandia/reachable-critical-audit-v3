# REQ_V3_10 — 系统需求（v3.10 缺陷修复版）

背景：kernel 级项目首例审计复盘（SYSTEM_DESIGN_V3_10.md）。12 条系统需求，全部有失误案例支撑；撤销项见设计文档 §4。

## 覆盖率簿记（P-A）

**REQ-V3.10-001 tracked 提取源扩展（多波批次形态）**
`_tracked_ids` 提取源：
1. 全部波次 filter 文件——`r2_filter_result*.json` glob（含主文件与 `_r2_filter_result_{wave}.json` 分波文件），逐文件合并 keep/drop/boundary_confirmations 三组 surface_ids；
2. `hypotheses.json` 的 `logic_hypotheses[].surface_ids` 恒计入（与 SKILL.md 门禁⑦语义对齐："R2 假设 surface_ids" 含 logic 组）；
3. 兜底路径不变（无任何 filter 文件时读 `hypotheses[].surface_ids`）。
无分波文件、无 logic 组的旧队列行为零变化（向后兼容）。

**REQ-V3.10-002 R4 假说级 tracked_surfaces**
biz_hypothesis 任务书新增**假说级**可选字段 `tracked_surfaces`：
- 触发条件：该假说 verdict 非 confirmed，或 verdict=confirmed 但 findings 为空（有 finding 级 tracked_surfaces 载体时不重复收集）；
- 语义：本假说审查过程中实际触及（Read/Grep 核实）的 surface id 清单——原样引用 input_surface.json 的 id；
- 消费者：r4-collect 合并进队列 r4_findings 条目，供 gate⑦ 覆盖率簿记。

**REQ-V3.10-003 r4-collect 假说级 tracked 合并**
r4-collect 对含假说级 tracked_surfaces 的条目幂等合并（追加去重），不覆盖 finding 级 tracked_surfaces；形态漂移（字符串/缺字段）按 v3.9 归一化规则处理，不可恢复时该假说不合并（原子性，沿 R4_TRACKED_MISSING 语义）。

**REQ-V3.10-004 r2_guard fidelity 波次回退**
fidelity 的反查修复源：主 `hypotheses.json` 缺失时，glob `_r2_hypotheses_*.json` 合并反查（追加去重），仍缺失才输出 WARN。

## 实证回填契约（P-B）

**REQ-V3.10-005 empirical dict 键名规范化**
回填规范（SKILL.md R5）明确 canonical 键集：
- 保留键：`outcome` / `evidence_numbers` / `report`（渲染器既有消费键）；
- 标准键：`harness` / `method` / `input` / `result` / `verdict` / `backfilled_by`；
- 渲染器容错：优先读保留键；保留键缺失时回退标准键（result→实测文本、input→输入矩阵、harness→实证资产路径）；双形态都缺时渲染占位不变（绝不抛异常）。

## 边证据检测（P-C）

**REQ-V3.10-006 collect 边缺口显式信号**
collect 时 grade 机械重算为 static_only 且 `grade_self_reported` 为 edge_proven/empirically_confirmed 的候选：输出显式 `edge_gap` 提示（edge_evidence 条数 N vs call_chain 跳数-1，标注"疑似合并边（v3.8 契约：逐跳一条），补拆后重 collect"）。不改动降级行为本身，只补显式信号与 reason。

## 任务书与门禁一致性（P-E）

**REQ-V3.10-007 R4 empirical_result 指引与 gate 豁免一致**
biz_hypothesis 任务书 empirical_result 指引改为：
- 无实证环境 + 非声称类或 High/Medium 声称类 → 沿用"不实证不申报"路径（主代理裁决 NEEDS_REVIEW 或 claim 修正）；
- **Low + 声称类 claim_type → empirical_result 必须填机制级描述文本**（含"静态/机制级/源码级"措辞 + "无运行时测量"声明），这是 gate ③ Low+机制级豁免的判据；填 null 会触发违规；
- CONFIRMED:/REFUTED:/SOURCE_FACT: 前缀契约不变。

## 任务书资产中立化（P-F）

**REQ-V3.10-008 部署布局义务生态中立化**
biz_hypothesis 任务书部署布局义务改为按构建系统/语言分派的通用表述：
- 包清单类（files/发布面三查：包清单 files 字段、构建产物清单、发布面入口导出）；
- 编译开关面查询（Kconfig 提交值、Cargo features、CMake 选项、Gradle buildTypes 等——"提交值 vs 代码默认值"为通用语义）；
- 分派例不出现任何项目专属名；不在发布产物/编译面 → 不构成可达声称（语义不变）。

**REQ-V3.10-009 shipped-config 编译开关键通用形态**
shipped_config_prompt 的键语义补充通用形态：安全相关**编译开关/特性键**（config/features/开关类，提交值 vs 代码默认值，含"显式关闭 # ... is not set"为提交值的语义）与既有服务端框架键清单并列，按组件 lang/config 形态分派。CONFIG_* 仅作分派例（与 Cargo features 等并列），不进入键清单正文。

**REQ-V3.10-010 focus_sink 纯格式契约**
hypothesis_filter 任务书 focus_sink 格式强制为纯 `path:line`（相对项目根），说明性文字一律放 note 字段；示例给出正反例。

**REQ-V3.10-011 verifier/refuter 任务书补两步**
workflow_export 的 verifier/refuter 任务书：
1. 路径格式统一条款：call_chain/edge_evidence/hit_sites 的 file 一律相对项目根路径；
2. upstream 修复搜索步骤：对 sink 搜索 upstream 修复/已知缺陷报告（git log --all --oneline -S 关键标识、公开 CVE/补丁列表），命中时引用 commit hash 并核对本树是否已含（"快照落于修复前/后窗口"写进证据）。

## 提示资产（P-G）

**REQ-V3.10-012 parser_fuzz 有状态 stub 指引**
parser_fuzz_c.py docstring + harness_manuals/c.md 增补"有状态 sink 的最小 stub 复刻法"小节：无符号下溢语义保留、边界指针语义、分配布局模拟、逐字提取纪律——机制形态描述，不出现任何项目专属名。

## 版本链（收尾）

**REQ-V3.10-013 版本链与文档漂移**
TOOLING_VERSION → "3.10"；SKILL.md 增 v3.10 增量段（与既有版本段同构）；assets 计数更新；tests/test_v310.py 覆盖上述全部可测需求；验收判据按 SYSTEM_DESIGN §5 执行。
