# SYSTEM_DESIGN_V3_36: trust_boundary 规范枚举透传

## 变更动机

Caddy 阶段 6 验收审计 (v3.35 安装副本) R1 合并现场: 70 面中 35 面 trust_boundary
被 normalize 的关键词映射器静默改写 (18× trusted_channel→environment,
14× local→environment, 3× environment→local)。根因: 关键词映射器 (v3.2,
REQ-V3.3-008) 为自由文本设计, 未对规范枚举短路; 既往审计 agent 写自由文本
恰好命中关键词, Caddy 批按任务书 canonical schema 写规范枚举首次暴露。
规范输入是精确值, 映射纯属误伤——违反"不自动改写"纪律。

## 变更边界不变式

**只改 normalize 的映射语义**: 规范值 (含大小写变体) 透传; 自由文本关键词
映射零变化。阶段骨架、六门禁判据、队列数据模型、merge/validate/report
零改动。

## 模块影响面

| 文件 | 变更 |
|---|---|
| src/surface_mapper.py | normalize_surfaces str 分支 + dict 遗留分支各加 canonical 短路 (首步) |
| tests/test_v336.py | 新增 5 用例 (T-1..T-5) |
| 版本链五件 | TOOLING_VERSION→3.36; 版本守卫×24; SKILL.md 版本历史表; SKILL_INCREMENTS; REQUIREMENTS_TRACKING + gen_tracking VERSIONS |

## 兼容性

- 旧产物 (servo/firefox 规范 dict) 两分支不触发, 零行为变化;
- 旧队列复跑零新增告警 (验收判据);
- Caddy 域文件 (_r1_*.json 原始串未被动) 修复后重合并即可无损恢复。

## 版本链

TOOLING_VERSION → 3.36; 测试守卫 ×24 → 3.36; SKILL.md 版本历史表新行;
docs/history/SKILL_INCREMENTS.md v3.36 增量段; REQUIREMENTS_TRACKING 手工段;
gen_tracking VERSIONS 登记。
