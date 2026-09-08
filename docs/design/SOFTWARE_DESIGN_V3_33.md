# SOFTWARE_DESIGN_V3_33

函数级设计。P1 先行, P3 条款随后, P4 版本链收尾。

## P1-1 (D-1): surface_mapper merge 同 id 碰撞标注

- 位置: `surface_mapper.py` merge 函数 (dedup 块, ~860-868)。
- 设计: 构建 `id_source: {id: (file_tag, first_anchor)}` 映射 (遍历时记录);
  dedup 时若 id 已在 seen_ids 且来源文件不同 → append 到
  `merged["conflicts"]`:
  ```python
  {"entry": [existing_anchor, s_anchor],
   "surfaces": [existing_id, s_id],   # 同 id 时两者相同
   "resolution": "kept-first-same-id",
   "note": "跨文件同 id 静默覆盖形态; 主代理按组件前缀纪律改名后重 merge"}
  ```
- 同文件内重复 id 由 validate 拦截 (duplicate id error), merge 侧只处理跨文件。
- 输出合并后 conflicts 排序稳定 (按 id)。

## P1-2 (D-2): merge 域覆盖 warn

- 位置: `surface_mapper.py` merge 尾部。
- 设计:
  ```python
  def _domain_coverage_warn(merged_surfaces, domain_files, project_root):
      per_domain = {d: 0 for d in DOMAINS}
      for s in merged_surfaces: per_domain[s["type"]] += 1
      signed_empty = 从各域文件读取 reviewed_by+empty_domain_reason 的域集合
      warn = [d for d in DOMAINS if per_domain[d] == 0 and d not in signed_empty]
  ```
  - merge 已接收全部 _r1_*.json 文件路径参数, 空域签收从这些文件读取
    (validate 时落盘的文件形态: dict with reviewed_by+empty_domain_reason)。
  - warn 输出到 merged["domain_unmapped"] (列表), stderr 一行提示。
  - 不阻断 (提示级; 主代理裁决重派或补签收)。

## P1-3 (D-3): r2_guard fidelity focus_sink 路径存在性

- 位置: `r2_guard.py` restore_surface_ids / fidelity 主流程。
- 设计: fidelity 增加:
  ```python
  def _check_focus_sinks(data, project_root):
      errs = []
      for grp in ("keep", "drop", "boundary_confirmations"):
          for e in data.get(grp, []):
              fs = e.get("focus_sink")
              if not fs: continue
              path = fs.rsplit(":", 1)[0]
              if not os.path.exists(path if os.path.isabs(path) else os.path.join(project_root, path)):
                  errs.append(f"{e['id']}: focus_sink 路径不存在: {path}")
      return errs
  ```
  - CLI: fidelity 接受 --root (项目根; 缺省从输入文件路径上溯 .audit_results 的父目录)。
  - error 输出 → 主代理拒收补查 (filter 任务书已有 Read 义务, 本条是机械面)。

## P1-4 (D-4): fidelity surface_ids 一致性

- 位置: `r2_guard.py` restore_surface_ids。
- 设计: 在 restore (缺失补回) 之前先做一致性校验:
  ```python
  mismatches = []
  for grp in (...): for e in data[grp]:
      orig = hyps.get(e["id"], {}).get("surface_ids")
      if orig and list(e.get("surface_ids") or []) != list(orig):
          mismatches.append({"id": e["id"], "got": ..., "expected": orig})
  ```
  - mismatch → error 输出 (含 "原样继承" 规则说明); restore 通道保留 (旧形态缺省补回, 补回也记 restored_from_hypotheses)。

## P1-5 (D-5): r4-collect reviewed_clean Medium+ warn

- 位置: `batch_verify.py` stage_r4_collect 尾部 (severity_advisories 块后)。
- 设计:
  ```python
  for h in items:
      if h.get("verdict") != "reviewed_clean": continue
      for fi in (h.get("findings") or []):
          if (fi.get("severity") or "").lower() in ("medium", "high", "critical"):
              result.setdefault("reviewed_clean_medium_plus", []).append({
                  "hypothesis": h.get("hypothesis_id"),
                  "finding": fi.get("title", "")[:80],
                  "severity": fi.get("severity"),
                  "action": "主代理裁决归位: 升 confirmed 承载 / 主代理段补报 / 明确留档"})
  ```
  - 不自动改写 verdict (修法形态纪律)。
  - SKILL.md R4 段同文条款 (P3)。

## P1-6 (D-6): 报告去重终态检查

- 位置: `batch_verify.py` _confirmed_issues (r3_link dedup 块, ~2224-2232)。
- 设计: 去重前查承载候选:
  ```python
  cand = next((x for x in queue["candidates"] if x["id"] == link.split()[0]), None)
  if cand and cand.get("verdict") == "REACHABLE":
      dupes.append(...); continue
  issues.append({..., "note": "同事实候选非 REACHABLE (见附录 A), finding 自列"})
  ```
  - 候选不存在时按现状去重 (保守)。

## P1-7 (D-7): hints lessons_refs 种格通道

- 位置: `language_issue_matrix.py` hints (~199-214)。
- 设计: refs 收集后追加:
  ```python
  for c in cells_for(lg):
      for sl in c.get("source_lessons", []):
          ref = "matrix/" + sl.split(" (")[0][:80]
          if ref not in refs: refs.append(ref)
  ```
  - 顺序: lessons/ 文件名命中在前, matrix/ 在后; 去重保序。
  - 上限: 每格最多 5 条 (防全量膨胀)。

## P1-8 (D-8): fixminer 文件路径信号

- 位置: `fixminer.py`。
- 设计:
  ```python
  _PATH_SIGNAL_PATTERNS = ("crypto", "crypt", "tls", "ssl", "auth", "permission",
      "parser", "decode", "deserialize", "memory", "alloc", "unsafe", "secure",
      "sanitize", "validate", "bounds")
  def _path_score(files):
      return 1 if any(p in f.lower() for f in files for p in _PATH_SIGNAL_PATTERNS) else 0
  ```
  - 入选判据: `_security_score(subject) + _path_score(files) > 0` (净分>0 门槛不变);
  - 输出 `path_signal` 计数与 per-commit `path_signal` 布尔; usage 不变。

## P3 (D-9/D-10/D-11): SKILL.md 三条款

- 报告段包络声明增 (f) 生成码类 (SWR-V3.33-009 文本)。
- R1 段漂移裁决条款 (SWR-V3.33-010 文本)。
- R5 段 harness 条款 (SWR-V3.33-011 文本: 钉版本/lib 名/git 依赖)。

## P4 版本链五件

1. `workflow_export.py:TOOLING_VERSION` → "3.33"
2. 版本守卫测试行 ×22 处 sed → "3.33" (test_v310/v312/v313/v39/v314/v315/v317/v318/v319/v320/v321/v322/v323/v324/v325/v326/v329/v330/v331/v332 等含 TOOLING_VERSION 断言处)
3. SKILL.md 增量段 (列 SWR 号 + 验收判据)
4. `REQUIREMENTS_TRACKING.md` 手工追加段 + gen_tracking VERSIONS 登记
5. 资产计数守卫同步 (先例/清单条数多处)
