# SYSTEM DESIGN V3.18 — 变更边界不变式与模块影响面（2026-09-01）

## 变更边界不变式

1. **阶段骨架不变**：R0-R6 零改动。
2. **六门禁①-⑧判据语义不变**：矩阵不参与任何门禁输入。
3. **队列/账本数据模型零改动**：新资产独立于 verify_queue 与
   issue_coverage_matrix（两矩阵互补：账本记覆盖计数，问题矩阵供知识）。
4. **零新机制**：无新门禁名、无新强制义务、无新阶段、binder 零改动；
   SKILL.md 仅新增提示级条款 + 验收判据条款。

## 数据流

```
R2: 主代理/限时 agent ──python3 language_issue_matrix.py cells <lang>──→
    该语言已种格条目 (patterns/sinks/pitfalls) ──→ 假设空间提示 (提示级)
R6: 验收收官 ──主代理两段式回填──→ language_issue_matrix.json cells
    (去项目化提炼 + source_lessons 追溯)
coverage-ledger --write ──互不依赖──→ issue_coverage_matrix.json
```

## 模块影响面

| 模块 | 改动 | 性质 |
|---|---|---|
| resources/language_issue_matrix.json（新） | 16×12 格，首版种 ~28 | 数据 |
| language_issue_matrix.py（新） | 加载器 + cells/stats CLI | 机械 |
| SKILL.md | R2 条款 + 验收判据回填条款 + v3.18 增量段 | 文档 |
| install.sh | 模块清单 + language_issue_matrix.py | 机械 |
| workflow_export.py / tests 守卫 ×7 | TOOLING 3.18 | 版本链 |
| tools/gen_tracking.py | VERSIONS 登记 | 版本链 |
| REQUIREMENTS_TRACKING.md | 手工段 | 版本链 |

## 兼容性矩阵

- 旧队列复跑零新增告警：矩阵无队列消费端，零告警路径。
- 全量 392 基线零回退；资产计数守卫零变化。
- installed 副本 install.sh 同步后 diff 干净（含账本双副本稳定复验）。
