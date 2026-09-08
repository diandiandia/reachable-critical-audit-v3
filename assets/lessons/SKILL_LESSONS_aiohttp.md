# SKILL Lessons — aiohttp（2026-08-24）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = hybrid

### R3
- [grade_recomputed] CAND-003: 机械分级重算 (main-agent (R3.5 后实证回填, SWR-V3.4.3-061))
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-005: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-006: 机械分级重算 (collect-mechanical-recompute)

### R3.5
- [verdict_correction] CAND-001: {'note': '主代理裁决 (2026-08-24): 证据不足——TOCTOU 机制已实证确认 (stat 门->open 绕过, 盲 fstat 覆盖) 但触发前提 (docroot 可写) 在库型部署中无法取证/无法静态排除; 默认部署不可远程触发', 'by': 'main-agent'}
- [verdict_correction] CAND-002: {'note': '主代理裁决 (2026-08-24): 证据不足——吞并/伪造机制可达且实证, 但 CWE-436 双解析器前提在仓库内不成立, 漏洞显著性依赖部署中外部第二解析器, 无法取证', 'by': 'main-agent'}

### R3.5-N
- [resurrection] CAND-003: 攻击路径（已实证复现，真实 aiohttp web 服务器返回 500）：1) 攻击者 POST `Content-Type: multipart/form-data; boundary=<31-70 字符>`（边界经 multipart.py:862-867 `_get_boundary` 的 70 字符上限校验，31+ 字符合法），首 part 为 `Content-Disposition: 

## 主代理过程观察（人工补充）

- 目标项目观察: aiohttp 的 THREAT_MODEL.md 是罕见的高质量威胁模型资产 (19 子系统 STRIDE + 历史 CVE 修复追溯), R2 的 23 条 boundary_confirmations 大量受益于此; 建议把'项目自带威胁模型'纳入 R1 context 采集

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
