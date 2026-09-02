# SYSTEM DESIGN V3.19 — 变更边界不变式与模块影响面（2026-09-02）

## 变更边界不变式

1. **阶段骨架不变**：R0-R6 零改动。
2. **六门禁①-⑧判据语义不变**：D-1 是检查路径的读取侧 lenient（放宽兼容），
   不改变任何门禁的阻断判据；无新门禁名。
3. **队列数据模型零改动**：无新字段、无字段语义变化；correction_record 双形态
   是既有事实（主代理自然写法 vs v3.10.2 dict 契约），本版只让读取侧容忍。
4. **零新机制**：D-2~D-6 全部为提示级/内容级/明示级。

## 模块影响面

| 模块 | 改动 | 性质 |
|---|---|---|
| evidence_ledger.py | assert_ledger correction_record lenient（:436-437） | P1 机械 |
| tools/batch_verify.py | _build_prompt 步骤 0 块 + 一句提示 | P3 内容 |
| workflow_export.py | resurrect_prompt 第 9 维 | P3 内容 |
| harness_manuals/ENVIRONMENT_PROBES.md | sanitizer-dcheck 条目 | P3 内容 |
| SKILL.md | R3.5-N/R5/数据模型速查条款 + v3.19 增量段 | P4 文档 |
| workflow_export.py:22 + tests 守卫 ×9 | TOOLING 3.19 | P4 版本链 |
| tools/gen_tracking.py / REQUIREMENTS_TRACKING.md | VERSIONS 登记 + 手工段 | P4 版本链 |

## 兼容性矩阵

- V8 真实队列复跑：correction_record 为 str+dict 混形态——lenient 后
  assert_ledger 零崩溃、warn 集与补记前逐条一致（验收对象）。
- 全量 400 基线零回退；资产计数守卫零变化（无新计数资产）。
- installed 副本 install.sh 同步后 diff 干净。
