# SOFTWARE DESIGN V3.25 — 函数/文本级设计 + P 分层序列

## D-1（SWR-V3.25-001）verify 导出 taskFile 化

- 文件：`workflow_export.py` export_script verify 分支
- 实测锚点：`pool = qualified[:batch_size]` 后的 payload 构建循环
  （`payload.append({"id": ..., "prompt": prompt})` 段, ~125-129 行区）
- 改法：循环内 build prompt 后：
  ```python
  _tasks_dir = os.path.join(project_root, ".audit_results", "_tasks")
  os.makedirs(_tasks_dir, exist_ok=True)
  tf = os.path.join(_tasks_dir, f"verify_{c['id']}.md")
  with open(tf, "w", encoding="utf-8") as fh:
      fh.write(prompt)
  payload.append({..., "taskFile": f".audit_results/_tasks/verify_{c['id']}.md"})
  ```
  （与 export_script_resurrect:593-599 同契约；workflow JS c.taskFile 分支
  已存在, 零改动）
- 反面分支守卫：payload 条目不再含内嵌 prompt 全文。

## D-2（SWR-V3.25-002）r35-collect A' 文件目录输入

- 文件：`tools/batch_verify.py:1416` stage_r35_collect
- 改法：决策装载段改双形态——
  ```python
  files = _glob.glob(os.path.join(transcript_dir, "journal.jsonl"))
  if files:
      decisions = _journal_decisions(files[0])   # 既有逻辑原位
  else:
      refute_files = sorted(_glob.glob(os.path.join(transcript_dir, "_refute_*.json")))
      if not refute_files:
          print("Error: journal.jsonl 与 _refute_*.json 均不存在 (A' 目录或 workflow transcript 目录)", file=sys.stderr)
          return 1
      decisions = [json.load(open(fp)) for fp in refute_files]  # A' 形态
  ```
  A' 文件 schema 断言：{id, refuted(bool), reason} 必填; agent 可选;
  strengthened/attribution_correction/note 可选（多数决段已按键读取, 零改动）
- CLI：`--from-refute-files <dir>` 解析后走同 stage_r35_collect；
  r35-collect 的 `--from-journal` 报错文案改双形态提示。

## D-3（SWR-V3.25-003）verifier 编码矩阵条款

- 文件：`tools/batch_verify.py` _build_prompt 步骤 5 段（2965 行区）
- 改法：步骤 5 输出后追加一行条件段：
  ```python
  if _is_path_family(cand):   # cwe 含 22 或 sink/evidence 含路径拼接信号
      prompt += """### 步骤 5.2（v3.25, SWR-V3.25-003）: 路径穿越编码矩阵
  路径穿越/路径拼接类候选的编码矩阵固定维度: 裸 ../、%2e%2e 段、%2F 分隔符、
  混合编码（..%2f）、%252e 双编码——逐形态实测或注明未测; 单形态样本不得
  外推（框架/网关/应用三层解码行为分叉实录）。"""
  ```
- `_is_path_family` 判据：`cand.get("sink_type")` 含 "22" 或 candidate cwe
  列表含 CWE-22（无独立 helper 则内联判断, 避免死函数——义务三问③）。

## D-4（SWR-V3.25-004）severity_transfer_advisory

- 文件：`tools/batch_verify.py` stage_r4_collect 落盘段（1200-1230 区,
  existing 映射之前）
- 改法：对每条 finding：
  ```python
  r3 = fi.get("r3_link")
  cand_id = r3.split(" ")[0] if isinstance(r3, str) and r3.startswith("CAND-") else None
  if cand_id and (fi.get("severity") or "").capitalize() in ("High", "Critical"):
      tc = next((x for x in queue["candidates"] if x.get("id") == cand_id), None)
      if tc and severity_for(tc).capitalize() in ("Medium", "Low", "High"):
          if _sev_rank(fi["severity"]) > _sev_rank(severity_for(tc)):
              warns.append({"kind": "severity_transfer_advisory",
                            "finding": (fi.get("title") or "")[:60],
                            "r4_severity": fi["severity"].capitalize(),
                            "candidate_mechanical": severity_for(tc),
                            "hint": "同事实去重后载体候选机械严重度低于 R4 申报——"
                                    "主代理裁决 severity_override（不自动改写）"})
  ```
- `_sev_rank`：Critical 3 > High 2 > Medium 1 > Low 0（内联 dict, 不建函数）。
- 输出：warn 列表并入 R4_COLLECTED 结果（warn 级不阻断）。

## D-5（SWR-V3.25-005）预置数据文件面指引

- 文件：`task_templates/surface_map_domain.md` 生成器/模板产物面指引之后
- 新条件段（storage 域注入, 主代理派发时按域附加）：
  ```
  ## 预置数据文件面指引（v3.25, SWR-V3.25-005 —— 仅 storage 域注入）
  仓库内 shipped 数据文件（预置数据库/种子文件/示例配置）的状态即攻击面——
  默认口令/默认关闭的安全开关/预置凭据与代码默认值的一致性逐项核对;
  面登记时 type 用 storage_input, entry_points 指向该数据文件内容证据行。
  ```

## D-6（SWR-V3.25-006）R5 核取提示句

- 文件：`SKILL.md` R5 回填规范段（v3.24 equivalent 抽验句之后）
- 文本（提示级）：
  ```
  补测前先核取 verifier/证伪者证据中已有实测数字——backfill 规范
  （v3.4.3-061）以证据文本实测为依据, 同事实重复实证是执行层浪费。
  ```

## P 分层序列

- **P1**：D-1（workflow_export verify 分支）
- **P2**：D-2（r35-collect + CLI）→ D-4（r4-collect warn）
- **P3**：D-3（_build_prompt）→ D-5（surface 模板）→ D-6（SKILL.md）→
  tests/test_v325.py（六 SWR 各一用例含反面分支）
- **P4 版本链五件**：workflow_export.py:22 TOOLING "3.25"；15 测试文件版本
  断言行 sed（仅 TOOLING_VERSION == 行, SWR-V3.24 历史 ID 不动）；
  SKILL.md v3.25 增量段（六 SWR + 验收判据）；REQUIREMENTS_TRACKING.md
  手工追加 V3.25 段（禁 gen_tracking 再生成）；gen_tracking VERSIONS 登记
  ("V3.25", REQ/SWR 路径)。
