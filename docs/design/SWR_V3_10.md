# SWR_V3_10 — 软件需求（v3.10 缺陷修复版）

每条 SWR = 实现文件 + 行为契约 + 测试判据。测试集中在 tests/test_v310.py，全量回归不破坏 243 基线。

| SWR | REQ | 实现文件 | 行为契约 | 测试判据 |
|---|---|---|---|---|
| SWR-V3.10-001 | 001 | tools/batch_verify.py `_tracked_ids` | ①`glob(r2_filter_result*.json)` 合并三组 surface_ids（主文件与分波文件同权）②`logic_hypotheses[].surface_ids` 恒并入③无分波/无 logic 的旧队列 tracked 结果与 v3.9 完全一致 | 构造多波 fixture：主+2 分波 filter 文件 + logic 组 → tracked 为三源并集；旧形态 fixture → 零变化 |
| SWR-V3.10-002 | 002 | task_templates/biz_hypothesis.md | canonical 示例与字段义务段新增假说级 `tracked_surfaces`（条件触发措辞：非 confirmed 或 findings 空时填写；有 finding 载体时省略） | 模板文本断言：字段名与触发条件措辞存在；`_scan_runtime_assets` 扫描绿 |
| SWR-V3.10-003 | 003 | tools/batch_verify.py r4-collect 路径 | 假说级 tracked_surfaces 幂等合并进 r4_findings 条目（追加去重，不覆盖 finding 级）；形态漂移（字符串/缺失）归一；不可恢复 → 该假说不合并 + `R4_TRACKED_MISSING` 语义 | 构造含假说级 tracked 的 R4 文件 → collect 后队列条目含并集；重复 collect 幂等；缺字段条目不合并且报错 |
| SWR-V3.10-004 | 004 | r2_guard.py fidelity | 主 hypotheses.json 缺失 → glob `_r2_hypotheses_*.json` 合并反查；全部缺失才 WARN | fixture：仅分波文件存在 → 反查修复成功无 WARN；全缺失 → WARN |
| SWR-V3.10-005 | 005 | tools/batch_verify.py render_report_md + SKILL.md R5 回填规范 | 渲染读键顺序：outcome/evidence_numbers/report → 回退 harness/method/input/result/verdict → 占位；SKILL.md 回填规范列 canonical 键集 | 构造 empirical dict（仅标准键）→ 渲染含实测文本；双形态缺 → 占位不抛异常 |
| SWR-V3.10-006 | 006 | tools/batch_verify.py stage_collect | 重算 static_only 且自报更高 → 输出 `edge_gap` 提示含边数/跳数差与补拆指引（写入 stderr 或返回 dict，不阻塞） | 构造自报 edge_proven + 边数不足的 journal → collect 返回含 edge_gap 字段 |
| SWR-V3.10-007 | 007 | task_templates/biz_hypothesis.md | empirical_result 指引四态化（前缀契约 + Low 声称类机制级描述要求 + 无实证环境措辞），与 gate ③ 豁免逻辑一致 | 模板文本断言；对照 gate 豁免代码路径人工核对 |
| SWR-V3.10-008 | 008 | task_templates/biz_hypothesis.md | 部署布局义务措辞：包清单类/编译开关面两分派，通用语义（发布面三查 + 提交值 vs 代码默认值），无项目专属名 | 模板文本断言 + 去项目化扫描绿 |
| SWR-V3.10-009 | 009 | workflow_export.py shipped_config_prompt | 键语义段补编译开关/特性键通用形态（config/features/开关类，提交值含显式关闭语义），与服务端框架键清单并列按形态分派 | prompt 生成产物断言（构造 config 形态组件 → prompt 含编译开关键段；构造服务端组件 → 含框架键段） |
| SWR-V3.10-010 | 010 | task_templates/hypothesis_filter.md | focus_sink 格式段：纯 `path:line`（相对项目根）+ 正反例 | 模板文本断言 |
| SWR-V3.10-011 | 011 | workflow_export.py verifier/refuter prompt 模板 | 两步补丁：路径格式统一条款 + upstream 修复搜索步骤（git log -S / CVE 补丁核对 / 前后窗口语义） | 导出产物断言（export 一个候选 → prompt 含两段文本）；去项目化扫描绿 |
| SWR-V3.10-012 | 012 | templates/harness/parser_fuzz_c.py docstring + harness_manuals/c.md | "有状态 sink 最小 stub 复刻法"小节：无符号下溢语义、边界指针语义、分配布局模拟、逐字提取纪律——机制形态 | 文本断言（两文件均含小节标题与关键措辞）；去项目化扫描绿 |
| SWR-V3.10-013 | 013 | workflow_export.py TOOLING_VERSION + SKILL.md + tests/test_v310.py | 版本 "3.10"；SKILL.md v3.10 增量段（设计/需求/软件需求链接 + 验收判据 + 撤销记录）；test_v310 全绿并入回归 | 版本守卫比对；测试全绿；`signature_lib.py selfcheck` 非 fixture 路径 exit 0 |
