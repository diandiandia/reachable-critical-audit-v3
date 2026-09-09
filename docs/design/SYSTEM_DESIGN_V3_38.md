# SYSTEM_DESIGN_V3_38: 模型能力利用五机制

## 变更动机

用户裁定执行 MODEL_LEVERAGE_EVAL_V3_37 评估件的 A-E 五候选——模型能力利用
的最大缺口在"对抗与实证的耦合"(发现增量价值几乎全部来自对抗与实证, 而非
生成量)。另修复 v3.37 两条目缺 binding 从不挂载的隐性欠账 (本批取证发现)。

## 变更边界不变式

**提示级/清单级五机制 + 一处 schema 可选字段**: 零新门禁、零新强制义务、
零新阶段; 六门禁判据/队列数据模型/N=2 多数决/铁律零触碰; 旧队列零新增告警。

## 模块影响面

| 文件 | 变更 |
|---|---|
| assets/resources/checklist_library.json | v3.37 两条目补 binding (D-0) + 新条目 CK-SIBLING-CONSISTENCY (D-1) |
| src/workflow_export.py | VERDICT_SCHEMA +self_refutations 可选字段 (D-2); verify prompt 自证伪轮条款 (D-2) + 实证机会条款 (D-4); refute_prompt 注入 self_refutations (D-2) |
| SKILL.md | R2 同族不一致条款 (D-1) + 公开面关联检索条款 (D-3); R5 harness 回收条款 (D-5) |
| tests/test_v338.py | 新增 5 用例 |
| 版本链五件 | TOOLING 3.38; 守卫×24; 版本表行; 增量段; tracking; gen_tracking; 计数 47→48 |

## 兼容性

- 旧 journal/旧 payload 零影响 (schema 只增可选字段);
- 清单库既有 47 条零改动 (只增 binding/新条目);
- 安装副本同构 (install.sh 无需改动)。

## 版本链

TOOLING_VERSION → 3.38; 测试守卫 ×24 → 3.38; SKILL.md 版本历史表新行;
docs/history/SKILL_INCREMENTS.md v3.38 增量段; REQUIREMENTS_TRACKING 手工段;
gen_tracking VERSIONS 登记。
