# SYSTEM_DESIGN_V3_37: 验收复盘三修复

## 变更动机

Caddy 验收审计暴露三条可入库教训: (1) refutation/resurrect 导出的 taskFiles
相对路径与 Workflow agent cwd 不匹配 (主代理手工补绝对路径绕开); (2) verifier
对 Go 切片边界语义 (cap vs len) 误判致整候选误报 (CAND-011, R5 实证拦截);
(3) 资源类声称的量级驱动权未核 (CAND-002 量级前提幻觉, 证伪 1/2 → 降级)。

## 变更边界不变式

**P1 数据正确性 + P3 提示级清单条目**: 无新阶段、无新门禁、无新强制义务;
队列数据模型/门禁判据零变化; 旧队列零新增告警。

## 模块影响面

| 文件 | 变更 |
|---|---|
| src/workflow_export.py | 三处 taskFile/taskFiles 落盘字段绝对化 (:599/:811/:854) |
| assets/resources/checklist_library.json | +2 条目 (CK-SLICE-CAPACITY/CK-MAGNITUDE-OWNERSHIP) |
| tests/test_v337.py | 新增 4 用例 |
| 版本链五件 | TOOLING 3.37; 守卫×24; SKILL.md 版本表+增量段; tracking; gen_tracking; 资产计数 45→47 |

## 兼容性

- 历史 payload (相对路径) 不重写——新导出全绝对; 已派发波次零影响;
- 清单库新增条目按 family 派发 (memory-safety/empirical), 既有条目零改动。

## 版本链

TOOLING_VERSION → 3.37; 测试守卫 ×24 → 3.37; SKILL.md 版本历史表新行;
docs/history/SKILL_INCREMENTS.md v3.37 增量段; REQUIREMENTS_TRACKING 手工段;
gen_tracking VERSIONS 登记。
