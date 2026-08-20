# SKILL Lessons — pyjwt（2026-08-20）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

### R3
- [grade_recomputed] CAND-001: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-002: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-003: 机械分级重算 (main-agent-mechanical-recheck)
- [grade_recomputed] CAND-004: 机械分级重算 (main-agent-mechanical-recheck)

### R3.5
- [verdict_correction] CAND-001: {'target': 'CAND-001', 'demote_to': 'UNREACHABLE', 'reason': 'R3.5 1/2 证伪, 主代理裁决采信证伪方: 库内无 jku 解析 (grep 1 处=防御性注释 jwks_client.py:73-76), uri 在 __init__ 由宿主一次固定, token 内容不流向请求目的地; 攻击者 kid 仅控制触发 (每 300s cache 窗口一次对已配置端点的 GET, 设计内密钥轮换), 不控制目的地 → CWE-918 SSRF 前提断裂。防御注释倒读为攻击模型属归因倒置; 公共 API 静态存在即攻击面若扩展至 U

## 主代理过程观察（人工补充）

- P1 首个项目 (模板): R1 双 agent 均修正父代理前提 (jwks_client 有出站网络面/CLI 已移除), REQ-V3.3-009 空域映射指引实战有效
- R3 verifier 自报 empirically_confirmed 但无结构化 empirical dict → collect 机械重算降级; 主代理逐候选回填 (P0 同型问题, 回填依据=evidence 文本真实测量)
- CAND-001 SSRF 被 1/2 证伪并主代理采信: 防御性注释倒读为攻击模型属归因倒置——'公共 API 静态存在即攻击面' 若扩展至构造参数则 urllib 自身即 SSRF
- R4 产粮 5 Low findings 全实证 (异常契约族/重定向降级/缓存竞态)——成熟库的 R4 产率 > R3 重演 (v3.1 maturity 判定正确)
- CK-WS-MATERIALIZE 清单经 cwe-match CWE-400 误绑纯 JWT 库 (3 个候选任务书含 WS 问题域清单)——checklist binder 缺 applicability 门控 (W6 §32)

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
