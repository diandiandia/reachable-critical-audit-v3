# v3.3.2 实施计划（P1-P5）

> 依据 SW_DESIGN_V3_3_2.md §实施批次 + SWR_V3_3_2.md（43 条）。开发在 workspace（/root/reachable-critical-audit-v3），测试全绿后 install.sh 安装到 skill 目录。

## P1 正确性先行（SWR-001/002/003/033，无依赖）

| 步骤 | 内容 | 验证 |
|---|---|---|
| 1.1 | evidence_ledger: gate ③ 前置 verdict==REACHABLE（SWR-001） | test_evidence_ledger 新用例 |
| 1.2 | evidence_ledger: commit demote_to 清 claim + claim_nulled_by（SWR-002） | 同上 |
| 1.3 | evidence_ledger: status .lower() 归一化 + 不一致告警（SWR-003） | 同上 |
| 1.4 | batch_verify _build_prompt 输出段加 claim 自洽条款（SWR-033） | prompt 快照断言 |

## P2 裁剪（SWR-030/014/023/053/071/072）

| 步骤 | 内容 | 验证 |
|---|---|---|
| 2.1 | biz_hypothesis.md H7 表收缩 schema + finding claim_type + 三问说明段（SWR-030/031/032） | 模板文本检查 |
| 2.2 | batch_verify IMPORTABILITY_STEPS 按型门控（SWR-014） | prompt 快照断言（C/Go 无完整段） |
| 2.3 | precedent_library self_refutation_hints 精度门（SWR-023） | 单测：Host 先例不注入 Java 配置候选 |
| 2.4 | SKILL.md R2 签名降佐证器（SWR-053） | doc-lint 通过 |
| 2.5 | REQ_V3_3.md / W6 修订记录（SWR-071/072） | 文档存在 |

## P3 捆绑接线（SWR-004/005/006，依赖 P2）

| 步骤 | 内容 | 验证 |
|---|---|---|
| 3.1 | ③b 结构化+收窄（SWR-004） | 单测：Low 无实证不阻断；Medium+ forced-claim 阻断 |
| 3.2 | 复活改判检查（SWR-005） | 单测：re_verify_gap+REACHABLE+无 refutation → 违规 |
| 3.3 | r4_feedback 消费者（SWR-006） | 单测：构造冲突队列 → warn |

## P4 载体（SWR-010~015/020~023/040/050~052/054/070/073，与 P3 可并行）

| 步骤 | 内容 | 验证 |
|---|---|---|
| 4.1 | batch_verify --expect + --stage coverage + --stage grade-recheck + --stage r35-collect + r4-collect id 校验（SWR-010/012/013/011/015） | 各命令 CLI 冒烟 + 单测 |
| 4.2 | workflow_export gap 渲染 + 抽样落盘 + project/dispatched_ids（SWR-020/021/022） | 导出产物断言 |
| 4.3 | surface_mapper norm_surface_id（SWR-040） | 单测 |
| 4.4 | SKILL.md wave registry / R3.5 触发 / 抽样口径 / R6 幂等 / 三问（SWR-050/051/052/054） | doc-lint |
| 4.5 | REQ_V3_2.md / REQ_V3_1.md 修订记录（SWR-070/073） | 文档存在 |

## P5 验收（SWR-060/080~091）

| 步骤 | 内容 | 验证 |
|---|---|---|
| 5.1 | harness_manuals 环境能力探针清单（SWR-060） | 文本检查 |
| 5.2 | 12 个新单测（SWR-080~091） | 全绿 |
| 5.3 | 现有测试回归（98+）+ doc-lint | 全绿 |
| 5.4 | 三锚点 fixture 复跑 | 零回退 |
| 5.5 | 新项目验收 + install.sh 安装 | 六门禁全 PASS |
