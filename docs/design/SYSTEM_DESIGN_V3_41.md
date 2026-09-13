# SYSTEM_DESIGN_V3_41 — 变更边界不变式 + 影响面（v3.41）

## 变更边界不变式（本周期不触碰）

- 阶段骨架（R0-R6）与六门禁判据语义不变
- 队列数据模型主体不变（candidate 字段集零新增——D-1 只是渲染层读取既有字段 `resurrect_gap`，该字段在本次审计中已由主代理写入队列，非新模型义务）
- 自动改写禁令维持：D-3 只告警不归一化
- 目标形态四轴与门禁承载不变

## 模块影响面

| 变更 | 模块 | 影响 |
|---|---|---|
| D-1 | src/workflow_export.py（export_script verify 分支 gap 渲染） | 复活重验轮 prompt 组装；Mode W/A' 共享 |
| D-2 | tools/batch_verify.py（`_gates_for_report`、`_render_appendix_b_process`） | 报告机械渲染 B.5/B.2 段恢复机械产出 |
| D-3 | tools/batch_verify.py（常量区 + `_warn_r4_enums`） | r4-collect 告警输出（stderr warn 级，不阻断） |
| D-4 | tools/batch_verify.py（verifier 任务书步骤 4 段） | verify 波任务书文本（提示级） |
| D-5 | assets/resources/checklist_library.json | 计数 49→50；SKILL.md 附录计数行 + 正文引用同步 |
| D-6 | assets/resources/precedent_library.json | 计数 18→19；SKILL.md 附录计数行同步 |
| D-7 | assets/resources/issue_coverage_matrix.json（经 seed 命令） | java 行新增两格；hitrate 记账 |

## 兼容性

- 旧队列复跑零新增告警不变式：D-1/D-2 修复崩溃与降级路径（无告警面变化）；D-3 只对**非法 claim_type** 产出新 warn——旧队列若含非法值（本批 H-4 两条例外已在主代理裁决中归一化）会新告警，属告警面恢复而非漂移；代表队列复跑验证
- 双副本同步：install.sh 官方路径
- 去项目化：D-5/D-6/D-7 资产正文零项目名（追溯字段除外），机器守卫 test_deproject_assets.py 扩展同步核对
