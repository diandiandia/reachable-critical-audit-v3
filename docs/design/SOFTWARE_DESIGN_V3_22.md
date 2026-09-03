# SOFTWARE DESIGN V3.22 — 函数级设计与分层序列（2026-09-04）

## P1 机械（先做——独立可测）

### 1. size_tier 分支调序（D-1）

surface_mapper.py:787-815 当前顺序：`n_langs > 2` → `count < 100` →
`count <= 500` → `count > 2000`（super-large）→ large。将 super-large
块（:804-815）整块上移到 :787 之前。super-large 分支内部 domains_split
已引用 mixed_domains（:806 区域）——多语言语义无损。

### 2. _mechanical_severity claim=other 封顶（D-2）

tools/batch_verify.py:1798-1827，cwe 命中分支（`if hits:`）内、containment
调整之前插入：
```python
if (candidate.get("claim_type") or "").strip().lower() == "other":
    return "medium", "claim_type(other) 结构性可达封顶;cwe:" + ",".join(
        f"CWE-{n}" for n in hits)
```
位置在 `by_cwe` 计算之前（省去无用计算）。

### 3. r35n-collect 未选中自动簿记（D-4）

tools/batch_verify.py stage_r35n_collect 落盘循环之后、返回之前：
```python
sample_file = os.path.join(project_root, ".audit_results", "_resurrect_sample.json")
selected = set()
if os.path.exists(sample_file):
    try:
        selected = set(json.load(open(sample_file)).get("selected", []))
    except ValueError:
        pass
auto_written = []
for c in queue["candidates"]:
    if c.get("verdict") == "UNREACHABLE" and not c.get("resurrection_review"):
        if c["id"] in selected:
            continue  # journal 缺失=异常, 交主代理
        c["resurrection_review"] = {"revived": False,
                                    "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}
        auto_written.append(c["id"])
save_queue(project_root, queue)
```
结果 JSON 增 `auto_bookkept: [...]`。

### 4. refutation budget/阈值（D-5）

workflow_export.py:379 `budget=800` → `budget=3000`；:382 `len(chain) > 8`
→ `> 12`、`chain[:8]` → `chain[:12]`。

## P2 结构（次做）

### 5. refutation/resurrect 导出 taskFile 化（D-9）

workflow_export.py refutation 导出函数：对每候选每视角（i in 0..1），
任务书文本写入 `{project}/.audit_results/_tasks/refute_{id}_{i}.md`，
payload 条目改 `{"id": ..., "taskFiles": [tf0, tf1]}`（脚本 :20-26 已支持
taskFiles 优先）；resurrect 同形（单视角 `_tasks/resurrect_{id}.md`）。
内联 prompts 保留为回退（taskFiles 写入失败时）。slim payload 落盘
`refutation_payload_slim.json` / `resurrect_payload_slim.json`。

## P3 内容（三做）

### 6. biz_hypothesis.md 两处（D-6/D-8）

- 产出段加：写入 `.audit_results/_r4_hN.json`（N=假说号）+ 落盘拦截
  UNWRITTEN 契约 + 「default_value_table 全量保留, 禁止精简」；
- empirical_result 前缀契约段（:98-103）补 severity 分派：High/Critical+
  声称类 → null + 「待主代理 R5 实证」注记；机制级文本仅 Low 适用。

### 7. SKILL.md 五处条款（D-7/D-10/D-11/D-3/D-9）

- R5 变更节 D-1 条款尾加 decision 签入义务（D-7）；
- R2 节（:148-150 后）加面覆盖前置核对条款（D-10）；
- R6 节加蒸馏失败模式 checklist 条款（D-11）；
- 数据模型速查 refutation 键名注记「单数」存储键（D-3 注记）；
- workflow 规范条款段加薄封装默认派发条款（D-9）。

## P4 版本链（四做）

1. workflow_export.py:22 TOOLING_VERSION → "3.22"。
2. 版本守卫 ×12（test_v310/312/313/39/314/315/316/317/318/319/320/3210）→ "3.22"。
3. SKILL.md v3.22 增量段（列 SWR 号 + 验收判据）。
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking.py VERSIONS 登记。

## tests/test_v322.py（约 12 用例）

- D-1: 3+ 语言 >2000 文件 → super-large（two_phase/components）；n_langs>2
  且 ≤2000 → large 不变（反面）
- D-2: claim=other+CWE-125 → medium；claim=crash+CWE-125 → critical；
  claim=other+override=high → high（override 优先反面）
- D-4: 未选中自动簿记 + 幂等重跑 + selected-无记录不写 + 已有不覆盖
- D-5: >3000 字符 evidence 不截于 800；12+ 跳链保留 12 + 注记
- D-9: refutation 导出 payload 含 taskFiles 且文件落盘；resurrect 同形；
  内联回退仍工作
- D-6/D-8: 模板含落盘契约 + severity 分派
- D-7/D-10/D-11: SKILL.md 条款存在
- TOOLING == "3.22"
