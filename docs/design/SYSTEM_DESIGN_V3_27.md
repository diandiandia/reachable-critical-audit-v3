# SYSTEM_DESIGN_V3.27 — 引擎形态知识基座补种

## 变更边界不变式

- 不改阶段骨架、六门禁判据语义、队列数据模型（与既往周期一致）
- **运行时模块业务逻辑零改动**（15 个运行时文件零触碰；workflow_export 仅
  TOOLING_VERSION 常量前进，属版本链）
- binder/loader 零改动——CK-LIMIT-BYPASS-ENUM 经既有 cwe/keywords 绑定管线
  自然生效（纯数据）

## 模块影响面

| 文件 | 改动 | 性质 |
|---|---|---|
| resources/language_issue_matrix.json | C×RESOURCE-DOS/C×MEMORY-SAFETY 两格补 patterns/pitfalls 三条 | 数据 |
| resources/checklist_library.json | 新增 CK-LIMIT-BYPASS-ENUM（44→45） | 数据 |
| task_templates/biz_hypothesis.md | 正向确认条目惯例段 | 任务书文本 |
| workflow_export.py | TOOLING_VERSION 3.26→3.27 | 版本链 |
| tests/test_v310/312/313/314/315/316/317/318/319/320/3210/322/323/324/325/326/39.py | 守卫 ×17 同步 | 版本链 |
| tests/test_v327.py | 新建 | 回归 |
| SKILL.md | 资产地图计数（清单 45）+ v3.27 增量段 | 版本链 |
| docs/design/REQUIREMENTS_TRACKING.md | V3.27 手工段 | 版本链 |
| tools/gen_tracking.py | VERSIONS 登记 | 版本链 |

## 兼容性

- 旧队列复跑零新增告警预期：新清单条目仅经绑定管线注入 verifier/refuter
  prompt——历史队列不重跑任务书，零影响；矩阵新条目仅 R2 提示级
- 资产计数守卫联动：SKILL.md 正文节与附录计数同步 44→45（test_doc_lint
  test_asset_counts_current 只守附录行，正文节手工同步——v3.15 实录纪律）
- 去项目化扫描：矩阵与清单均在 DEPROJECT_BLACKLIST 扫描范围，新条目必须过
