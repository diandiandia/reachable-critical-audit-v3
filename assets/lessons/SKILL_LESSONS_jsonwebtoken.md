# SKILL Lessons — jsonwebtoken（2026-08-20）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

### R3.5-N
- [resurrection] CAND-001: revived: verifier 漏内存放大维度+瞬态释放前提伪 (GC 痕迹实证), 回 R3 重验附 gap

## 主代理过程观察（人工补充）

- R3.5-N 复活攻击教科书案例: verifier 以'时间线性+瞬态释放'判 UNREACHABLE, 复活者抓到内存放大维度+GC 痕迹证伪 → revived=true → gap 渲染重验 → 改判 REACHABLE → 复活改判 gate 强制 R3.5 → 0/2 证伪放行——SWR-020/005/011 全链真实数据闭环
- 教训: 线性时间成本 ≠ 无 DoS——内存维度与 GC 生命周期才是 V8 库的资源面; '瞬态' 需 GC 痕迹实证而非直觉
- 部署层前提 (body 限额) 被当默认阻断的又一实例——有界堆宿主形态下死亡阈值 ~1/10 堆上限
- CAND-001 判 UNREACHABLE 后 H1 coverage_note 引用该裁决——复活改判后主代理需调和 R4 引用 (报告已注明)
- 机械假设 4 条全为路径白名单族噪音 (verify.js:148 误匹配)——签名佐证器对本库零贡献, LLM 主路径承载 R2 (v3.1 设计预期)

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
