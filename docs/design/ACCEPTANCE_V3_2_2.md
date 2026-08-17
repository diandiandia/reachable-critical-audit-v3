# Reachable Critical Audit v3.2.2 — 验收文档（Phase 3.2.2.3）

> 日期：2026-08-17。上游：REQ_V3_2_2.md §8。最高判据：SKILL.md「第一原则：通用型 Skill」。

## 验收判据

| # | 判据 | 方法 | 通过条件 |
|---|---|---|---|
| ① | mbedtls 本树机械复跑：8 缺陷对应手工绕过全部消失 | 用 .audit_results/ 现有产物逐条重放 CLI | selfcheck 一条命令 exit 0 / merge 自动落盘 / drops 报 dropped=3 / anchor 直过 hypotheses.json / r4-collect 后直接 r4-assert PASS / lessons_recorder str 形态不崩 / UNREACHABLE 无 empirical_required 违规 / 门禁⑦ 镜像自动传播（无需手写镜像 bridge） |
| ② | 复跑结论零丢失 | 对照 2026-08-17 审计终态 | 0 REACHABLE / 6 R4 findings / 4 UNREACHABLE 复活未复活 / H6 High→Low 裁决可机械重放 |
| ③ | 资产通用性检查全绿 | selfcheck 完整性自检 + 资产脱敏复查 | 13 签名 lang/cwe 完备、去项目化 0 命中；先例/清单运行时字段无项目名 |
| ④ | 回归 + 新增测试全绿 | workspace tests（skill .venv） | 全部 PASS；doc-lint 入套件 |
| ⑤ | install 完成 | ./install.sh | 安装完成 + 测试全绿 |
| ⑥ | 第一原则新项目条款 | 声明 | 本版验收对象 mbedtls 为 v3 首审 C 库项目（此前 15 语言战役与三锚点均无 C 库先例），满足"每版本至少一个未审计过的新项目验收"约束 |

## 执行记录

（验收执行时回填：各判据实测输出摘录）

---

## 执行记录（2026-08-17）

| # | 判据 | 实测输出 | 结论 |
|---|---|---|---|
| ① | 8 绕过消失 | selfcheck exit 0（"integrity OK: 13 signatures (lang/cwe/deproject 完备)"）；merge 自动落盘 140658B；drops 报 `kept=0 dropped=3`；anchor 直过 hypotheses.json（批量 OK）；r4-collect(H1 形态) 后 r4-assert 直连 `R4_ASSERT_PASSED`；lessons_recorder 正常（+str 形态单测）；collect --from-journal 后 CAND-001/002/004 `claim_nulled_by=collect-claim-null-v3.2.2`；六门禁 tracked 59/59 | PASS |
| ② | 结论零丢失 | 队列 4/4 UNREACHABLE（复活未复活记录保留）；r4_findings H-1~H-7 全 VERIFIED（H3×2 Medium/H6×1 Low 裁决/H7×3）；六门禁 `gates: True, []` | PASS |
| ③ | 资产通用性 | selfcheck 完整性自检通过；先例/清单运行时字段复查 leftover=NONE；mbedtls 复跑 hits 36→7（零跨语言、tests/ sites=0）、gen 20→2（纯 L3） | PASS |
| ④ | 测试 | 98 passed（新增 doc-lint×4 + signature 契约×5 + lessons lenient×1） | PASS |
| ⑤ | install | 见下（install.sh 输出） | 执行 |
| ⑥ | 新项目条款 | mbedtls = v3 首审 C 库项目（此前 top-15 语言战役与三锚点均无 C 库先例） | PASS |

**验收事件记录**：P-A 验证期间 gen 重跑曾覆盖 mbedtls hypotheses.json（L3-only 2 条）——已按审计原版恢复 20 条 LLM 假设并附 archive_note；input_surface.json 重跑 merge 后已重新签收。
