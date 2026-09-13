# SYSTEM_DESIGN_V3_43

版本: v3.43 | 机制冻结实验周期

## 变更边界不变式（冻结实验主体）

- **R0-R6 阶段骨架：零改动**
- **六门禁判据语义：零改动**
- **队列数据模型：零改动**
- **src/ tools/ 判定逻辑：零改动**（TOOLING 版本链机械步除外）
- 允许改动面：矩阵/inventory 资产（数据）、SKILL.md 内容条款（提示级文本）、
  R4/filter 任务书模板（提示级文本）、skill-optimizer SKILL.md（纪律/文档）、
  测试、设计件

## 模块影响面

| 模块 | 变更 | 性质 |
|---|---|---|
| assets/resources/language_issue_matrix.json + inventory | K-1/K-2 种格 | 知识数据 |
| SKILL.md | K-3（H7 段）/K-4（fixminer 段）/S-3（R6 段） | 提示级文本 |
| assets/task_templates/biz_hypothesis.md | K-5（H3 段） | 提示级文本 |
| skill-optimizer SKILL.md | S-1（第四问）/S-2（触发判据段） | 纪律/文档 |
| src/workflow_export.py | TOOLING 3.42→3.43 | 版本链机械步 |

## 兼容性

- 旧队列零行为变化（无判定逻辑改动）
- 矩阵种格只增不改——已种格条目零变化
- 提示级条款对已完成审计产物零影响

## 冻结实验验收判据（写死，供阶段 6 对照）

知识补种带来发现力提升的证据形态：kernel 类目标审计时 hitrate 查询
CWE-787/290 命中 PAGE-CACHE-OWNERSHIP 族条目，且 R2 假设空间包含该族
假设（H4 资源归因子条锚定）。若两周期内无 kernel 类目标，以矩阵查询
对照替代。
