# SYSTEM_DESIGN_V3.28 — Top15×Top10 目标物化

## 变更边界不变式

- 阶段骨架/六门禁判据语义/队列数据模型/运行时模块业务逻辑：**零改动**
- 裁决层（先例库/清单库/signature 库/harness 模板）：**零改动**——
  inventory 的 external_seeded 档是提示层资产，不得进裁决层（显式边界声明）
- 矩阵 cells 既有路径与 R2 消费契约：零变化（inventory 是叠加视图）

## 模块影响面

| 文件 | 改动 | 性质 |
|---|---|---|
| resources/language_issue_inventory.json | 新建（34 条目派生自矩阵格） | 数据 |
| language_issue_matrix.py | 增 inventory/goal/seed 三命令 + load_inventory/goal_progress/seed_entries 三函数 | 加载器增量 |
| SKILL.md | v3.28 增量段（含回填升档条款） | 版本链 |
| workflow_export.py | TOOLING_VERSION 3.27→3.28 | 版本链 |
| tests/test_v310~327/39.py | 守卫 ×18 同步 | 版本链 |
| tests/test_v328.py | 新建 | 回归 |
| docs/design/REQUIREMENTS_TRACKING.md | V3.28 手工段 | 版本链 |
| tools/gen_tracking.py | VERSIONS 登记 | 版本链 |

## 兼容性

- 旧队列复跑零影响预期：加载器新命令与审计管线零交集
- 去项目化：inventory 条目与 seed 输入在 DEPROJECT 扫描范围（新测试显式断言）
- 资产计数守卫：矩阵/清单计数不变（inventory 为独立资产，不并入既有计数断言）

## 回退路径

- 新命令与文件单点可删，零运行时耦合；矩阵 cells 路径原样保留
