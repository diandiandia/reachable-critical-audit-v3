# SOFTWARE DESIGN V3.19 — 函数级设计与开发序列（2026-09-02）

## P1 机械（D-1）

evidence_ledger.py assert_ledger 的 adjudication_verification 检查块
（:436-437）改为：

```python
        if require_adjudication_verify:
            unverified_demotes = []
            for c in cands:
                for cr in c.get("correction_record") or []:
                    # v3.19 (SWR-V3.19-001): 双形态 lenient——str 为注记形态
                    # (主代理自然写法), dict 为 demote 裁决形态 (v3.10.2 契约)。
                    # 只检查 dict 条目; str 条目跳过, 不改写任何字段。
                    if isinstance(cr, str):
                        continue
                    if cr.get("demote_to") and not cr.get("adjudication_verification"):
                        unverified_demotes.append(c.get("id"))
                        break
```

## P3 内容（D-2/D-5/D-6）

- D-2: tools/batch_verify.py `_build_prompt` 步骤 0 块尾（"verifier 最常犯的
  错误…"段之后、`{step05}` 之前）插入提示句（SWR-V3.19-002 措辞）。
- D-5: harness_manuals/ENVIRONMENT_PROBES.md 末尾新增 `## 6. sanitizer 构建
  变体与 dcheck 交互`（条目文本见 SWR-V3.19-005）。
- D-6: workflow_export.py resurrect_prompt 维度 8 之后追加维度 9
  （SWR-V3.19-006 措辞, 提示级）。

## P4 文档 + 版本链（D-3/D-4 + 五件）

- SKILL.md：R3.5-N 抽样条款 + R5 实证裁决条款各插入 D-3/D-4 明示句；
  数据模型速查 correction_record/resurrection_review 双形态注记；
  v3.19 增量段。
- TOOLING_VERSION "3.18"→"3.19"（workflow_export.py:22）；守卫 9 处
  test_v310.py:276、test_v312.py:180、test_v313.py:191、test_v39.py:266、
  test_v314.py:219、test_v315.py:253、test_v316.py:120、test_v317.py:347、
  test_v318.py:132（P4 实测行号逐处核对后 sed）。
- REQUIREMENTS_TRACKING.md 手工段 + gen_tracking VERSIONS 登记。
- tests/test_v319.py（约 8 用例，见 SWR 各条测试约束 + 反面分支
  "lenient 零改写断言"）。

## 验收

- 全量回归全绿；V8 真实队列复跑 assert_ledger 零崩溃零新增 warn；
  signature_lib selfcheck /root/v8；install.sh 双副本 diff 干净。
