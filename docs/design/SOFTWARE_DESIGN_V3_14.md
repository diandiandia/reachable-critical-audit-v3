# SOFTWARE_DESIGN_V3_14 — 软件方案（v3.14 protobuf 复审计复盘缺陷修复）

> 对应需求文档：REQ_V3_14.md（9 条 REQ）。只增改不重写：模块改动点、数据模型变更、测试计划。
> 原则：改动最小面；旧队列零告警；新增行为全部有触发条件。
> 评估：BIAS_EVAL_V3_14.md（2 处初稿纠正 + 3 项偏见裁决随本方案落实）。

## 1. 模块改动点

### 1.1 `tools/batch_verify.py`（D-1/D-2/D-4/D-5/D-6）
- `_detect_journal_anomaly(transcript_dir, max_distinct_per_id=1)`（L379 签名加
  默认参数）；r35-collect 调用点（L1282-1288）传 2；r35n-collect（L557-563）
  保持默认 1。
- r4-collect 的 unknown_surface_ids 告警构建（L1214-1222）：从归一化 `known`
  集生成 `suggested_corrections`（后缀/词形最近匹配），不自动改写。
- `_adapt_r4_finding`（L786-791）：非空且非 CAND-* 的 r3_link 写
  `r3_link_invalid` flag；r4-collect 输出 warn。
- r4-collect 合并后（~L1203）：finding 带 r3_link 且含终态关键词时比对候选
  终态 verdict，矛盾输出 `r4_verdict_link_conflict` warn（字段级，非新门禁）。
- coverage-ledger 幂等分支（L1493-1503）：would_be_new_counts 非空时附
  `manual_merge_guidance`（增量清单 + 合并协议 + manual_merge_note 模板）。

### 1.2 `workflow_export.py`（D-3）
- `export_script_resurrect`（L483-551）：导出前读 `.audit_results/_resurrect_sample.json`
  ——文件存在且 selected/unselected 与当前无 resurrection_review 的 UNREACHABLE
  候选集合一致 → 池以文件 selected 为准（unselected 排除）；文件不存在或漂移 →
  内部 `resurrect_pool` 抽样并写文件（现状）。文件保持可选。

### 1.3 `evidence_ledger.py`（D-8）
- strengthen_unverified note（L437-438）文案补全字段名与层级。

### 1.4 `SKILL.md`（D-7 + D-8 同步 + v3.14 段）
- R1 步骤 2（L103-115）加写盘能力指引一句。
- L974-975 strengthen 签收段同步字段名。
- 文末追加「🆕 v3.14 增量」段。

### 1.5 审计工件收尾修正（非 skill 缺陷，随 P23）
- /root/protobuf/.audit_results/verify_queue.json 的 H4-F5（title/evidence 含
  「维持 R3 UNREACHABLE」）改为与 CAND-009 终态（NEEDS_REVIEW 证据不足）一致；
  定稿报告 `.audit_results/reachable_vulnerabilities_report.md` 对应段落文本
  手工修正（报告防覆盖已生效，不重跑 --stage report）。

### 1.6 版本链
- `workflow_export.py:22` TOOLING_VERSION → "3.14"；gen_tracking VERSIONS 登记
  V3.14；REQUIREMENTS_TRACKING.md 手工追加段（禁再生成）；既有守卫 5 处更新
  （test_v310:276 / test_v312:178 / test_v313:191+193 / test_v39:266）。

## 2. 数据模型变更（向后兼容）

```
全部为输出/告警层增强, 无 schema 变更:
- r4-collect 输出: +suggested_corrections / +r3_link_invalid warn / +r4_verdict_link_conflict warn
- coverage-ledger 幂等分支: +manual_merge_guidance
- resurrect 导出: 读 _resurrect_sample.json (可选, 零新义务)
- finding 落盘: +r3_link_invalid flag (可选字段)
```

## 3. 测试计划（tests/test_v314.py，约 8 用例）

| 测试 | 断言 |
|---|---|
| test_anomaly_mode_aware_threshold | 默认 1：同 id 2 结果判 anomaly；传 2：2 结果不判、3 结果判 |
| test_ledger_idempotent_merge_guidance | 幂等分支增量非空输出 manual_merge_guidance 含 FAM×LANG 清单；增量空零输出 |
| test_resurrect_sample_file_authority | 三分支：文件一致→池=文件 selected；文件缺失→内部抽样写文件；集合漂移→重算写文件 |
| test_unknown_surface_suggestions | SURF-DATA-001 vs known S-DATA-001 生成建议映射；tracked_surfaces 不被改写 |
| test_r3_link_domain_warn | HYP-001 写 flag+warn；CAND-* 与 null 零告警 |
| test_r4_verdict_link_conflict | 「维持 UNREACHABLE」vs 候选 NEEDS_REVIEW 矛盾 warn；一致零告警 |
| test_skillmd_guidance_texts | SKILL.md R1 写盘指引句 + strengthen 字段名文案存在 |
| test_tooling_version_v314 | TOOLING=="3.14" +「🆕 v3.14 增量」段 |

## 4. 开发顺序（C0 + P22-P25 提交序列，延续 P21 惯例）

- **C0 设计件**：REQ/SWR/SYSTEM_DESIGN/SOFTWARE_DESIGN_V3_14 + BIAS_EVAL_V3_14
- **P22 机械小修**：D-1 + D-4 + D-5 + D-7 + D-8
- **P23 结构性修复**：D-2 + D-3 + D-6 + 审计工件收尾修正
- **P24 版本链**：TOOLING 3.14 + SKILL.md 增量段 + 守卫 5 处 + tracking
- **P25 测试与验收**：test_v314.py + 全量回归 + 旧队列复跑 + protobuf 复跑 + install

## 5. 验证

```bash
python3 -m pytest tests/ -q            # 329 基线 + test_v314 全绿
python3 signature_lib.py selfcheck /root/phpseclib
# protobuf 复跑: r35-collect 无 anomaly 误报 / coverage-ledger 幂等分支输出指引
# 禁止: python3 tools/gen_tracking.py
```
