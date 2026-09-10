# SYSTEM_DESIGN_V3_39: haproxy 验收复盘四修复

## 变更动机

haproxy 阶段 6 验收暴露四欠账: normalize 关键词子串匹配缺陷 (v3.36 修复的
同族第二实例)、seed 双写覆盖不全、计数守卫散落 (R6 失同步两次复发)、
severity_override 形态未文档化。

## 变更边界不变式

**P1 数据正确性 + P2 守卫集中 + P3 文档/容忍归一化**: 零新门禁、零新强制
义务、零新阶段; 六门禁判据/队列模型/N=2/铁律零触碰; 旧队列零新增告警。

## 模块影响面

| 文件 | 变更 |
|---|---|
| src/surface_mapper.py | 两分支关键词匹配改词边界辅助函数 (D-1) |
| src/language_issue_matrix.py | seed_entries 双写覆盖全部条目 + 缺格自动建 (D-2) |
| tests/asset_guards.py (新) | 资产计数常量集中 (D-3) |
| tests/test_v328/v329/v337 | 计数断言改 import 常量 |
| tools/batch_verify.py | severity_override dict 形态容忍归一化 + warn (D-4) |
| SKILL.md | severity_override 形态契约一句 + 版本表 |
| tests/test_v339.py | 新增 5 用例 |
| 版本链 | TOOLING 3.39; 守卫×24; 增量段; tracking; gen_tracking |

## 兼容性

- normalize 行为变化仅限 ASCII 关键词词边界 (自由文本映射更精确; 规范枚举
  canonical 短路不变);
- seed 双写幂等 (已补数据的格不重复);
- 旧队列 (servo/haproxy) 复跑零新增告警。

## 版本链

TOOLING_VERSION → 3.39; 测试守卫 ×24 → 3.39; SKILL.md 版本历史表新行;
docs/history/SKILL_INCREMENTS.md v3.39 增量段; REQUIREMENTS_TRACKING 手工段;
gen_tracking VERSIONS 登记。
