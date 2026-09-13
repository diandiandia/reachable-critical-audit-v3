# REQ_V3_41 — hibernate-orm 审计复盘缺陷修复需求（v3.41）

来源: /root/hibernate-orm/.audit_results/lessons.md「对 skill 的教训」6 条 + 过程观察 2 条（2026-09-12, TOOLING 3.40 下执行）

## 缺陷清单表（# / 缺陷（代码核实） / 修复 / 编辑点 / 分层）

| # | 缺陷（取证核实） | 修复 | 编辑点（实测） | 分层 |
|---|---|---|---|---|
| D-1 | workflow_export.py:810-818 复活 gap 渲染把 `re_verify_gap` (bool) 直接字符串拼接 → `TypeError: can only concatenate str (not bool) to str`——复活重验轮首跑即触发（主代理以 gap 文本写入 re_verify_gap 绕过） | gap 文本改读 `c.get("resurrect_gap") or ""`，`re_verify_gap` 仅作条件布尔；两者皆缺失时不渲染该段 | src/workflow_export.py:810-818 | P1 机械 |
| D-2 | batch_verify.py 报告段两处 sys.path.insert 只插 skill 根**缺 `/src`**（2210/2553；对照 5 处正确形态 545/1189/1458/1490/1724 均双插 `_parent` + `_parent/src`）→ 报告 B.5 渲染「evidence_ledger 不可导入」、B.2 渲染「language_inventory 现场重算失败」，两段主代理手工补写 | 两处补 `os.path.join(_parent, "src")` 双插，与其余 5 处同形 | tools/batch_verify.py:2210, 2553 | P1 机械 |
| D-3 | `_warn_r4_enums` 校验 verdict/severity/refuted-in-list，**不校验 claim_type 枚举** → H-4 两条 `source_fact`/`empirical_mechanism` 静默流入、H-6 两条空串触发 gate ③b 被迫事后补 SOURCE_FACT | claim_type 检查增补：非法值 warn + 建议映射（source_fact/empirical_mechanism → other；空串 → null）——**只告警不自动改写**（纪律 #4） | tools/batch_verify.py:1071 常量区 + 1075-1115 `_warn_r4_enums` 循环体 | P2 结构 |
| D-4 | verifier 任务书无「方言/平台语义矩阵」条款 → verifier 在 H2（无反斜杠转义语义）唯一实测被外推到 MySQL/Spanner 族 → CAND-006 复活翻转（同库 appendLiteral 已证反斜杠语义而 appendFormat 无中和分支） | 步骤 4 阻断检测段增补提示级条款：单一方言/平台实测不得外推到语义相异方言族；同库对照证据（各方言自身实现）是逐格核实廉价锚点；外推须显式标注覆盖格 | tools/batch_verify.py 任务书步骤 4 段（~3104-3119 运行时版本条件 bullet 后） | P3 内容 |
| D-5 | 检查清单缺「转义责任下沉型设计全通道对账」条目——同批 comment 通道有转义/hint 通道无/format 通道绕过闸门三处命中 | checklist +1 `CK-CHANNEL-ESCAPE-LEDGER`（49→50） | assets/resources/checklist_library.json 尾部 | P3 内容 |
| D-6 | 先例库缺「逃生舱等价性」裁决先例——CAND-005 复活失败但产出「function('sql') 等价 createNativeQuery 零能力增量」边界论证 | precedent +1（18→19）：逃生舱类 sink 与既有无校验通道等价 → 不立候选/归边界 | assets/resources/precedent_library.json 尾部 | P3 内容 |
| D-7 | java 矩阵 5/10 命中，CWE-470/416/611/74/116 无格可查 | seed java×MEMORY-SAFETY（越界索引/截断 cast 形态）与 java×TRUST-BOUNDARY（白名单 fail-open 形态）两格，source_lessons 带日期追溯 | assets/resources/issue_coverage_matrix.json（经 `language_issue_matrix.py seed`） | P3 知识基座 |

## 测试守卫约束（每 SWR ≥1 用例，含反面分支）

- SWR-V3.41-001: {re_verify_gap: True, resurrect_gap: "文本"} → export 成功且 prompt 含 gap 文本；{re_verify_gap: True, 无 resurrect_gap} → 不抛 TypeError 且不渲染 gap 段（反面分支）
- SWR-V3.41-002: stage_report 门禁段渲染 PASS/FAIL 行而非「evidence_ledger 不可导入」；B.2 渲染行存在（fixture 项目）
- SWR-V3.41-003: 非法 claim_type fixture → R4_ENUM_WARNING 含 illegal_claim_type + suggestion；合法枚举零新增告警（反面分支）
- SWR-V3.41-004: 任务书步骤 4 含「方言/平台」矩阵条款关键词（字符串断言）
- SWR-V3.41-005: checklist 50 条 + 新 id 存在 + source_lessons 追溯字段格式
- SWR-V3.41-006: precedent 19 条 + 新 id 存在
- SWR-V3.41-007: java×MEMORY-SAFETY 与 java×TRUST-BOUNDARY 两格存在且 external/source_seeded 档位正确

## 开发序列

P1 (D-1/D-2) → P2 (D-3) → P3 (D-4/D-5/D-6/D-7) → P4 版本链五件

## 验证命令

```bash
cd /root/reachable-critical-audit-v3 && python3 -m pytest tests/ -x -q   # 全量回归
python3 -m pytest tests/test_v341.py -v                                  # 新守卫
python3 src/signature_lib.py selfcheck /root/hibernate-orm               # 资产通用性
python3 tools/batch_verify.py /root/hibernate-orm --stage assert         # 本批队列复跑零新增告警
# 代表旧队列 (hadoop/servo/caddy/haproxy 等按存在性) 复跑 assert_ledger 零新增告警
```
