# P1 机制追踪矩阵（验收判据③证据载体）

> 判据：10 项机制修改全部在真实波次中至少使用一次（无单测-only 项）。
> 每次真实使用后在此记录证据位置（项目 + 产物文件 + 内容摘要）。

| # | 机制 | PyJWT | jsonwebtoken | orjson |
|---|---|---|---|---|
| 1 | wave registry 簿记 (SWR-050) | ✅ wf_ff6627ac-1ed + wf_fd1350dc-bca 共 5 条登记 (verify/refutation 各波) | ✅ wf_4e576d70 + wf_af14022b + wf_b1f90ddd + wf_7b249b54 (verify/resurrect/re-verify/refutation 4 波全登记) | ✅ wf_3e73e1fb + wf_609f48c9 + wf_53d987c5 + wf_89d00cf8 (4 波) |
| 2 | collect --expect 全集对账 (SWR-010) | ✅ 每波 collect 均带 --expect, 零张冠李戴 | ✅ 同左 (含 re-verify 波) | ✅ 同左 (双波) |
| 3 | gap 渲染 (SWR-020, 复活重验) | — (无复活流, 合法) | ✅ CAND-001 re-verify prompt 含「复活复核 gap」段 (SWR-020 实测渲染) | — (复活 0 revived, gap 未触发, 合法) |
| 4 | r35-collect refutation 落盘 (SWR-011) | ✅ 4 候选 refutation 字段落盘 | ✅ 2 轮 r35-collect (复活后补证伪) | ✅ 4 候选 |
| 5 | 复活改判 gate 触发+复核放行 (SWR-005) | — | ✅ 真实触发: re_verify_gap+REACHABLE+无 refutation → post_resurrect_refutation 违规 → 补 R3.5 0/2 存活 → 放行 | — (revived=false×2, gate 未触发, 合法) |
| 6 | coverage CLI surface_data (SWR-012) | ✅ 20/20 (4 PROC 面 bridge) | ✅ 6/6 | ✅ 19/19 (3 面 bridge) |
| 7 | coverage-ledger 回填+幂等 (SWR-001/002) | ✅ 写入 sources | ✅ 写入 sources | ✅ 写入 sources |
| 8 | 0.5 门控双形态 (SWR-014) | ✅ py 完整段 (IMPORTABILITY_FULL_LANGS) | ✅ js 完整段 (构建包含性变体) | ✅ rust 短段「构建包含性一行核对」双形态对照成立 |
| 9 | PREC 精度门 (SWR-023) | ✅ 自证伪提示注入 (适用前提标注) | ✅ 同左 | ✅ 同左 (含 PREC-GATE-RATING-001 实际用于评级) |
| 10 | 4 条新清单绑定 (SWR-020/021) | ✅ CK-CHECKPOINT-AFTER-ACCUM/CK-DYNAMIC-DEFENSE/CK-SENTINEL-SEMANTICS 绑定实证; ⚠️ CK-WS-MATERIALIZE 误绑 (缺陷#1) | ✅ 同左 | ✅ CK-CHECKPOINT-AFTER-ACCUM/CK-SENTINEL-SEMANTICS (kw:-1) |

## P1 过程中发现的 skill 缺陷（→ W6 §32 / v3.4.3 候选）

1. **清单绑定缺适用性门控**：CK-WS-MATERIALIZE（WS 分片物化清单）经 `cwe-match:['CWE-400']`
   绑定到纯 JWT 库（PyJWT CAND-001/002/004 + jsonwebtoken CAND-001）——CWE-400 是通用码但清单是 WS 专属问题域。
   先例库已有 applicability_signals 机制，checklist_binder 未复用。
   候选修复：checklist_library 条目加 applicability_signals（text/requires_lang 形态），
   binder 按候选 evidence/sink 上下文过滤；不匹配时绑定"通用资源类清单"或空。
2. **boundary_kind 词汇缺口**：BOUNDARY_KINDS 12 词无 C-API 扩展模块词汇（orjson 手写
   CPython C-API 胶水形态），agent 自然产出 capi-* 词族被校验器全拒。P1 裁决：归一化
   ffi-other + 保留 boundary_kind_raw 字段。候选修复：词汇表加 "capi"（通用, 覆盖
   Python C-API/Lua C-API 等）或按 lang_pair 细分。
3. **refutation/verify prompt 证据截断**：workflow_export 对 prompt 内 evidence 做
   长度截断并写 "[截断: 全文 N 字符, 见 verify_queue.json]"——Mode W agent 无文件系统
   假设下该指引失效（实测 agent 可 Read 磁盘文件补齐，但自包含任务书设计被削弱）。
   候选修复：截断时附完整证据的关键段（调用链+阻断点摘要已含），或按候选类型只截
   清单执行记录等次要段。
4. **跨项目同族裁决分歧（主代理终裁项）**：PyJWT CAND-002（未认证 header JSON 解析，
   4.5x 线性放大）判 REACHABLE；jsonwebtoken CAND-001（未认证 split/parse，~13x 常数）
   判 UNREACHABLE（"线性 1:1 无渐近放大 + 累积在宿主"）。同类事实两种裁决——同族一致性
   断言只覆盖同项目；跨项目校准差异需主代理在报告阶段统一（判据：放大比是否常数因子
   × 物化责任在库侧还是宿主侧）。

## 判据⑤（覆盖格 +3）跟踪

- PyJWT 闭合后：CRYPTO×python？——注意：PyJWT 候选为 SSRF/资源类，CRYPTO 家族由
  CAND-003 (CWE-20 key 解析) 支撑有限；最终由 coverage-ledger --write 实际聚合为准。
