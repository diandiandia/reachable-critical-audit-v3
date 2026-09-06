# SYSTEM DESIGN V3.25 — MaintainWise 验收审计复盘

## 变更边界不变式（与前版一致）

1. 不改阶段骨架与六门禁①-⑧+③c 判据语义；零新门禁名；
2. 不改队列数据模型主体（D-2 的 A' 决策文件为 r35-collect 输入形态扩展，
   队列内 refutation 字段结构零变化）；
3. 不改 workflow JS 的 schema 契约（D-1 走既有 c.taskFile 分支）；
4. 不自动改写：D-4 只 warn 提示，severity_override 仍由主代理裁决。

## 模块影响面（逐文件）

| 文件 | 变更 | 性质 |
|---|---|---|
| `workflow_export.py` | export_script verify 分支 taskFile 化（683-129） | P1 |
| `tools/batch_verify.py` | stage_r35_collect 双形态决策装载（1416）+ CLI --from-refute-files（3220）+ _build_prompt 编码矩阵条款（2877+）+ stage_r4_collect severity_transfer_advisory（1158+） | P2/P3 |
| `task_templates/surface_map_domain.md` | 预置数据文件面指引段 | P3 |
| `SKILL.md` | R5 核取提示句 + v3.25 增量段 | P3/P4 |
| `tests/test_v325.py` | 新增（六 SWR 各一用例含反面分支） | P3 |
| 版本链五件 | TOOLING 3.25 / 15 测试文件版本断言 / tracking 手工段 / gen_tracking VERSIONS | P4 |

## 兼容性分析

- D-1：payload 形态从 {prompt} → {taskFile}——workflow JS 双分支已存在
  （v3.10.2-005 fail-fast 兼容）；Mode A' 不受影响（自行 build_prompt）；
  旧项目重导出产生 taskFile 引用, resume 语义不变（args 变化属新波次）。
- D-2：journal 路径优先, 行为零变化；A' 目录输入为新增分支, 无既有调用者。
- D-3：verifier prompt 纯增量文本。
- D-4：warn 级新增, 不阻断（同 r4_feedback 先例）；旧队列复跑 collect 时
  若其 r3_link 已存在可能新增 warn——复跑口径以 assert_ledger 为准
  （r4-collect 重跑不触发）。
- D-5/D-6：模板/文档文本, 零行为变化。

## 风险与对策

| 风险 | 对策 |
|---|---|
| D-1 破坏 Workflow resume 缓存（args 变化） | resume 按新 args 重跑（缓存 key 含 args）——新波次语义正确, 无数据风险 |
| D-4 warn 噪音（档差常见） | warn 仅在 r4-collect 落盘时输出一次, 不随 assert 复报 |
| D-2 目录误传（journal 目录 vs refute 文件目录） | journal.jsonl 优先; 两形态都不存在才报错（既有报错文案保留） |
