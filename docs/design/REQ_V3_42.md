# REQ_V3_42 — Keycloak 复盘缺陷修复需求

版本: v3.42 | 来源: Keycloak 审计复盘（v3.41 首战，阶段 0 缺陷清单，用户裁定开工）

## 缺陷清单

| # | 缺陷 | 代码核实（取证实测） | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | refutation 资格判定「键存在即已复核」语义脆弱：主代理对未复核候选写空 refutation dict（签收字段）后键存在 → 资格排除 → qualified_total=0 静默空转 | `workflow_export.py:703` `"refutation" not in c`（取证确认）；本次审计实录：签收脚本 setdefault 后两次导出 WORKFLOW_NOTHING_TO_DO，手工清理 12 个空 dict 恢复 | 判定健壮化：refutation 存在且含 votes 或 summary 才视为已复核；空转时 advisory 提示「N 个候选带空 refutation 键」 | workflow_export.py:700-710 |
| D-2 | r4-collect 诊断只报包裹形态不报字段名错误：H1/H2 用 "hypothesis" 而非 "hypothesis_id" 时零提取，diagnosis 输出键清单无字段名映射提示 | `batch_verify.py:1313` R4_COLLECT_WARNING（取证确认 diagnosis 只含顶层 keys/hypotheses 类型） | diagnosis 追加近似键映射提示（顶层含 hypothesis/hypothesisId 等时输出「字段名应为 hypothesis_id」） | batch_verify.py:1308-1321 |
| D-3 | verifier 任务书缺「分支级声称」标注提示 | CAND-010 isAbsolute 分支断言被 real-target 实证证伪（Keycloak lessons.md 教训 1） | verifier 任务书加提示：分支级声称（isAbsolute/fallback/else-branch）标注为待实证子断言 | 任务书生成处（_build_prompt verifier 段） |
| D-4 | upstream「已修」结论缺树内核实明示 | CVE-2026-1180 公开声称已修而树内无修复（Keycloak lessons.md 教训 2，H-4-F1） | SKILL.md 公开面关联条款补：已修结论须附树内 commit 佐证，否则按未修处理 | SKILL.md（公开面关联检索段） |
| D-5 | filter drop 判据缺信息暴露/跨信任域完整性维度 | HYP-009 filter drop（无越权）后 R4 H5 从用户 oracle 维度重发现 High（Keycloak lessons.md 教训 3） | filter 任务书 drop 判据补提示 | assets/task_templates/hypothesis_filter.md |
| D-6 | SKILL.md 实证回填缺前缀级联语义 | CONFIRMED 前缀触发 ③d（本次回填后补 independent_review 才过门禁），SOURCE_FACT 不触发（Keycloak lessons.md 教训 4） | SKILL.md 回填规范补：前缀级联提示 | SKILL.md（R5 实证回填规范段） |

## 测试守卫约束

- D-1 反面分支：`{"refutation": {}}`（空 dict）与 `{"refutation": {"strengthened_verified_by": "x"}}`（仅签收字段）不视为已复核 → 仍进 qualified；`{"refutation": {"votes": 2}}` 视为已复核 → 排除；全排除时 advisory 含带空 refutation 键候选清单
- D-2 反面分支：输入 `{"hypothesis": "H1", ...}`（近似键）→ diagnosis 含映射提示；正输入零变化
- D-3..D-6 内容条款：SKILL.md/task_templates 的文本 diff 测试（测试守卫断言关键提示句在位）

## 开发序列

1. P1: D-1 + D-2（workflow_export.py / batch_verify.py）
2. P3: D-3（任务书生成）+ D-4/D-6（SKILL.md）+ D-5（filter 模板）
3. P4: 版本链五件
4. 测试: tests/test_v342.py + 全量回归 + 旧队列复跑

## 验证命令

```bash
cd /root/reachable-critical-audit-v3 && python3 -m pytest tests/test_v342.py -x -q
python3 -m pytest tests/ -x -q
# 旧队列复跑（代表项目）:
python3 tools/batch_verify.py /root/haproxy --stage assert --require_target_kind=False --require_resurrection=False
python3 /root/.claude/skills/reachable-critical-audit/src/signature_lib.py selfcheck /root/keycloak
```
