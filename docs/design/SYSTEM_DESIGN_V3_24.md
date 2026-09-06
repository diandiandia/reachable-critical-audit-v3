# SYSTEM DESIGN V3.24 — 三引擎全景召回评估驱动缺陷修复

## 变更边界不变式（与前版一致，本轮不触碰）

1. **不改阶段骨架**：R0-R6 流程、R4 H1-H7 假说编号与检测要点主体不变
   （D-1 为 H4 新增提示级子条，不删改既有要点）；
2. **不改六门禁判据语义**：①-⑧+③c 的触发条件/放行逻辑零变更，本轮无
   新门禁名、无新 warn 级别定义；
3. **不改队列数据模型主体**：verify_queue.json/input_surface.json/
   hypotheses.json 字段集零变更（D-5 为流程提示，不引入新字段）；
4. **不改严重度映射表结构**：CWE-843 已入 MEMORY-SAFETY（v3.23），
   RECALL-003 用 CWE-863（鉴权主体，high 档已有）——均无需改表。

## 模块影响面（逐文件）

| 文件 | 变更 | 性质 |
|---|---|---|
| `task_templates/biz_hypothesis.md` | H4 补 site-isolation/资源归因子条（40 行后） | P3 内容，提示级 |
| `task_templates/surface_map_domain.md` | JIT 轴段补根因归属条款（90 行后） | P3 内容，提示级 |
| `SKILL.md` | ① 报告段边界声明补 (d)(e)（343-344）；② R5 保真段补抽验提示句（281 后）；③ 增量段新增 v3.24 节（v3.23 节上方） | P3 内容 + P4 版本链 |
| `tests/fixtures/recall_regression_set.json` | 追加 RECALL-002..004 | fixture，仅测试引用 |
| `tests/test_v324.py` | 新增（五 SWR 各一用例含反面分支 + 版本断言 + 去项目化扫描） | P3 测试 |
| `workflow_export.py` | TOOLING_VERSION "3.24"（22 行） | P4 |
| 14 个测试文件 | 版本断言行 3.23→3.24（仅 `TOOLING_VERSION ==` 行；SWR-V3.23 历史 ID 字符串不动） | P4 |
| `docs/design/REQUIREMENTS_TRACKING.md` | 手工追加 V3.24 段 | P4 |
| `tools/gen_tracking.py` | VERSIONS 登记 ("V3.24", REQ/SWR 路径) | P4 |

## 兼容性分析

- **提示级条款零行为变化**：D-1/D-2/D-3/D-5 全部为提示级/warn 注记文本，
  对既有队列（v8/WebKit/firefox）的 assert_ledger 零新增告警——阶段 4 复跑
  验证；D-3 修改的是 v3.23 已发布文本（边界声明段），历史增量段
  （v3.23 节）保持不动，新 v3.24 增量段声明扩展内容；
- **fixture 追加非替换**：RECALL-001 结构零改动，test_v323 既有断言
  （entries[0].id == RECALL-001、运行时路径不引用 fixture）继续全绿；
- **版本链双副本**：dev == installed 同步由 install.sh 保证（阶段 5 diff 核验）。

## 风险与对策

| 风险 | 对策 |
|---|---|
| D-3 编辑 v3.23 已发布文本，若误改历史增量段致追溯断裂 | 仅改 341-344 行声明正文；v3.23 增量节（1582 行区）零触碰；test 断言声明段五族齐全 |
| 版本断言批量 sed 误伤 SWR 历史 ID（"SWR-V3.23-xxx" 含 "3.23"） | sed 目标限定 `TOOLING_VERSION == "3.23"` 整行模式；改后 grep 核对 SWR-V3.23 ID 串零变化 |
| fixture 新条目带项目名回退（第一原则） | test_v324 内置 PROJECT_TOKENS 扫描新条目（除 case_source 字段外） |
