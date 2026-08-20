# SKILL Lessons — orjson（2026-08-20）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

### R3
- [grade_recomputed] CAND-001: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-002: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-003: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-004: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-006: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-007: 机械分级重算 (main-agent-mechanical-recheck)

## 主代理过程观察（人工补充）

- 混合语言旗舰: boundary 域 14 surfaces (手写 CPython C-API 胶水), 12 多域冲突 kept-first+11 mirror_pairs——v3.2 机制全链实战
- BOUNDARY_KINDS 词汇缺口: agent 自然产出 capi-* 词族被校验器全拒, 主代理归一化 ffi-other+保留 boundary_kind_raw (W6 §32 v3.4.3 候选: 词汇加 'capi')
- R5 环境: rustup 现装 (cargo 1.97.1) + maturin 1.14.1 + 系统 python3.14 头 → 自建 wheel → 独立 venv 崩溃隔离——计划中'离线 cargo 可用'假设错误被环境探针纠正
- 4 个崩溃原语全部实证 (tuple 堆越界写/enum 递归/dataclass 空串键 panic/numpy reserve 预算)——R3.5 证伪者深钻将 CAND-001 机制从'栈溢出'修正为'堆缓冲区越界写' (崩溃带容量模型 25 点全吻合)
- CAND-004/005 复活攻击五维全探均确认证伪——良好证伪 (指针相等门控+分配不变式+全局分配器) 经受对抗是防漏放机制的正向输出
- gate ③ 拦截了 collect 机械重算对实证级声称的降级——主代理 R5 实测 (CAND-002 12x) + evidence 文本回填 (001/003/006) 双路径解决

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
