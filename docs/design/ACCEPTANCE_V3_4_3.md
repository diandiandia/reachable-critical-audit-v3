# v3.4.3 验收记录

- **日期**: 2026-08-20 ~ 2026-08-21
- **代码**: workspace main 84650c0（v3.4.3 十七缺陷闭环）
- **验收项目**: jsrsasign 11.1.5（CRYPTO × JavaScript 缺口格，未审计新项目，library）

## 验收判据

| 判据 | 结果 |
|---|---|
| ① 测试全绿 | **PASS** — install 时 157 passed / 2 skipped；workspace 159 全绿 |
| ② 三锚点零回归 | **PASS** — v3.4.3 开发期完成（sinatra/lighttpd/actix-web 对照归档基线零回退） |
| ③ 新项目完整 R0-R6 | **PASS** — jsrsasign 全流程：R0 target_kind=library 签收 → R1 17 surfaces → R2 17 假设（11 keep）→ R3 10 候选全 REACHABLE → R3.5 20 证伪者 0 证伪 → R3.5-N 复活池空（0 UNREACHABLE 合法豁免）→ R4 H1/H2/H3/H7 confirmed（13 findings）→ R5 强制实证 3 组主代理复验 → 六门禁 8/8 PASS → 报告 + R6 lessons |
| ④ 六门禁 | **PASS** — installed v3.4.3 assert_ledger exit 0，零违规零告警 |

## v3.4.3 新机制实测记录

| 机制 | 实测形态 |
|---|---|
| r4-collect 自适应归一化 | v3.4.3 代码重跑成功；本批次 R4 agents 已产出规范 schema（无漂移需归一化）——机制在位 |
| surface id 前缀映射 | _map_surface_id 运行，SURF-* 全标准无漂移 |
| resurrect CLI（--mode resurrect + --stage r35n-collect） | CLI 干净运行：0 UNREACHABLE → WORKFLOW_NOTHING_TO_DO（R3.5-N 合法不适用） |
| _truncate_evidence 800 预算 | 反证 prompt 证据截断标记可见（"[截断: 全文 N 字符, 见 verify_queue.json]"） |
| grade 机械重算 | CAND-004 self-reported static_only vs 机械 edge_proven 差异检出（call_chain 三路压平违反单线性链模型）→ 主代理重构修正 |
| 门禁③b 结构化判定 | 5 条 R4 findings 因 empirical_result 缺确认标记被机械拦截 → 主代理实测复验后标注 CONFIRMED 通过 |
| claim_type +leak | schema 枚举在位（本批次声称分布 crash/unbounded/other，无 leak 类） |
| BOUNDARY_KINDS +capi | 本批次无 capi 边界面（纯 JS 库）——单测覆盖 |
| checklist applicability_signals 门控 | CAND-002/008/009 正确绑定 CK-GENERIC-RESOURCE（signal-mismatch-fallback），CWE-338 族绑定 CK-CRYPTO-MISUSE |
| CK-GENERIC-RESOURCE | 3 候选绑定执行 |
| PREC 门控 | PREC-GATE-RATING-001 在 CAND-002/008/009 自证伪段生效 |

## 验收过程问题（记录型，不影响 PASS）

1. **版本来源不一致**（主代理流程缺陷）：compact 后误用 installed v3.4.2 路径跑 r4-collect/门禁，而 payload 由 workspace v3.4.3 导出——已用 workspace 重跑受影响阶段并最终以 installed v3.4.3 复断言。教训入 W6 候选。
2. **refutation batch_size 默认 4 静默截断**：9 个资格候选只导出 4 个，主代理显式 --batch-size 补救。v3.4.3 后候选改进项。
3. **kw:ws 子串误配**：CAND-001 的 "jws" 命中 "ws" 信号——词边界匹配为后候选改进项。

## 审计产出

- 10 REACHABLE（7 empirically_confirmed + 3 edge_proven），0 NEEDS_REVIEW，闭合率 100%
- R3.5 拦截率 0/20（自证伪机制持续有效）；证伪者将 CAND-007 从 edge_proven 升级 empirically_confirmed（反证波产粮新模式）
- R4 产粮 13 findings（H1-F1 High OOM 主代理复验 exit 134）
- 主代理裁决 4 项（CAND-004 链重构 / CAND-007 R5 升级 / H7-F5 部署布局 claim 置空 / R4 实证标记）
- 报告: /root/jsrsasign/.audit_results/reachable_vulnerabilities_report.md（已复制 scan-results）
- Lessons: SKILL_LESSONS_jsrsasign.md（4 机械 + 10 过程观察，5 条 W6 高价值候选）

## 结论

**v3.4.3 验收通过**，已 install 至 skill 目录（157 passed / 2 skipped）。
