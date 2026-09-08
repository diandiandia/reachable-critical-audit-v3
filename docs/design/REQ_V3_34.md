# REQ_V3_34: 文件分层重构需求

来源: 用户裁定 (2026-09-08) —— 20+ 版本周期后仓库平铺结构职责不可读,
按逻辑分层重组文件夹/文件, 并刷新设计文档写清文件上下层关系。

## 需求清单

| # | 需求 | 状态 | 证据 |
|---|---|---|---|
| REQ-V3.34-001 | 五层结构: L0 契约 (SKILL/README/install) / L1 运行时 (src/) / L2 编排 (tools/) / L3 资产 (assets/) / L4 验证 (tests/) / L5 文档 (docs/) | 已完成 | git mv 全量迁移 + FILE_LAYOUT_V3_34.md |
| REQ-V3.34-002 | 依赖方向铁律: L2→L1 单向; L1/L2 只读 L3; L4 不改运行时; 唯一例外 workflow_export→batch_verify (BIAS_EVAL 注明) | 已完成 | src/_paths.py + SYSTEM_DESIGN_V3_34 |
| REQ-V3.34-003 | 路径派生单一事实源 src/_paths.py (ASSETS_DIR/RESOURCES_DIR/SKILL_ROOT), 运行时零硬编码层位 | 已完成 | 7 个 L1 模块改经 _paths |
| REQ-V3.34-004 | 纯移动零语义变化: 550 用例全绿 + servo 旧队列复跑 blocking=0 | 已完成 | pytest 550 passed |
| REQ-V3.34-005 | 四处同步义务 (FILE_LAYOUT/_paths/SKILL.md 引用/install.sh 清单 同一提交) | 已完成 | v3.34 提交含四处 |
| REQ-V3.34-006 | 设计文档刷新: FILE_LAYOUT_V3_34.md (层级权威参考) + SYSTEM_DESIGN_V3_34 (分层架构) | 已完成 | 本目录两文件 |

## 验证命令

```bash
python3 -m pytest tests/ -q                      # 550 passed
bash install.sh                                   # 安装 + 冒烟
python3 src/language_issue_matrix.py stats        # 资产读取 OK
python3 tools/batch_verify.py /root/servo --stage status   # 旧队列 OK
```
