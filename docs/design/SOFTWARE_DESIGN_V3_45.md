# SOFTWARE_DESIGN V3.45 — 函数级设计

## P1 机械 (D-1..D-8)

### D-1 surface_mapper.py
- `merge()` 内 per_domain 计数 (line 931-936): `t = s.get("type"); for d in DOMAINS: if t == d or (t or "").startswith(d + "_"): per_domain[d] += 1`
- `validate_surfaces()` (line 629 起): 必填字段检查段后追加 —
  ```python
  VALID_SURF_TYPES = {"network", "data", "process", "storage", "boundary"}
  for i, s in enumerate(data or []):
      t = s.get("type")
      if t and t not in VALID_SURF_TYPES:
          errors.append(f"[{i}]: type={t!r} 非枚举值 (建议归一到 network|data|process|storage|boundary; 全名形态按前缀匹配计数, SWR-V3.45-001)")
  ```
  (errors 是否阻断取决于 validate 现有语义 — 保持 warn 不阻断, 与现有 error 收集形态一致)

### D-2 batch_verify.py stage_r4_collect
- `_normalize_r4_payload` list 分支后, 在 collect 循环前:
  ```python
  no_hid = [i for i, f in enumerate(items) if not (f.get("hypothesis_id") or f.get("hypothesis"))]
  for f in items:
      if not f.get("hypothesis_id") and f.get("hypothesis"):
          f["hypothesis_id"] = f.pop("hypothesis")
  if no_hid:
      print(json.dumps({"status": "R4_ENUM_WARNING", "warning": {
          "kind": "missing_hypothesis_id",
          "hint": f"输入含 {len(no_hid)} 条无 hypothesis_id/hypothesis 的假说条目 (索引 {no_hid}), 静默跳过会丢失假说 — 核实任务书输出契约 (SWR-V3.45-002)"}},
          ensure_ascii=False), file=sys.stderr)
  ```

### D-3 batch_verify.py stage_r35n_collect
- auto_bookkept 写入处 (~:88): `c["resurrection_review"] = {"revived": False, "outcome": "复活抽样未选中 (auto_bookkept)", "auto_bookkept": True}`
- skip 条件 (~:50): `if c.get("resurrection_review") and not c["resurrection_review"].get("auto_bookkept"): skip`
- 覆写时 (updated 分支): `c["resurrection_review"].pop("auto_bookkept", None)`

### D-4 batch_verify.py _render_appendix_b_process
- :2592 改:
  ```python
  hd = json.load(open(hyp_path))
  n_hyp = len(hd) if isinstance(hd, list) else len(hd.get("hypotheses", []))
  out.append(f"- 假设: {n_hyp}")
  ```

### D-5 batch_verify.py _warn_r4_enums
- :1160-1164 改:
  ```python
  if "[refuted]" in title or "informational" in title:
      compliant = (sev == "low" and "[refuted]" in title)
      if not compliant:
          warnings.append(...)  # hint 尾附 "已合规形态 (severity=Low + [refuted] 标题) 不再告警 (SWR-V3.45-005)"
  ```

### D-6 target_profile.py
- 新探针函数 `_empirical_boot_signals(root)`:
  ```python
  BOOT_GLOBS = ("arch/*/boot/Image", "arch/*/boot/bzImage", "arch/*/boot/zImage",
                "vmlinuz", "vmlinux")
  boot_hits = glob.glob(os.path.join(root, "arch/*/boot/Image")) + [p for p in
              (os.path.join(root, "vmlinux"),) if os.path.isfile(p)]
  qemu = shutil.which("qemu-system-aarch64") or shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-riscv64")
  xgcc = shutil.which("aarch64-linux-gnu-gcc") or shutil.which("x86_64-linux-gnu-gcc")
  ```
- `recommend()`: 三信号齐 (boot_hits 且 (qemu 或 xgcc)) → `recommended["empirical_modes"] = ["real-target"]` + signals S7; 否则现状 []。
- 文档注记: 提示级建议, 主代理签收 (signed_by/overrides) 后消费者才装载。

### D-7 batch_verify.py collect (line 505-512)
- 改:
  ```python
  if v.get("claim_type") and v["verdict"] == "REACHABLE":
      entry["claim_type"] = v["claim_type"]
  elif v.get("claim_type") and v["verdict"] != "REACHABLE":
      entry["claim_type"] = None
      entry["claim_self_reported"] = v["claim_type"]  # SWR-V3.45-007 追溯归档
  ```
- verifier 任务书步骤 4 增一行文本 (见 D-10)。

### D-8 batch_verify.py _derive_containment
- profile 派生分支命中时:
  ```python
  if derived and derived == "process_sandbox":
      ev = (v.get("evidence") or "").lower()
      if any(k in ev for k in ("softirq", "kthread", "workqueue", "软中断", "中断上下文", "kernel thread")):
          print(f"Warning (SWR-V3.45-008): {c.get('id')} containment=process_sandbox 为 profile 派生值, 证据含内核上下文信号 — 一致性待主代理复核 (K1-4 实录)", file=sys.stderr)
  ```

## P3 内容 (D-9..D-16)

### D-9 biz_hypothesis.md 三条款
- claim_type 条款 (line 140 附近) 后追加反例表:
  ```
  **非法值反例 (v3.45, SWR-V3.45-009)**: static_verified / self_refuted /
  sibling_differential / empirical_mechanism 等描述词不是声称枚举 —
  机制确认写 empirical_result 的 SOURCE_FACT 前缀, claim_type 归一 other;
  证伪条目 claim_type=null。非法值会在 collect 告警并要求归一。
  ```
- verdict 条款 (line 69-72 附近) 追加意图映射:
  ```
  **散文意图映射 (v3.45)**: "部分证伪但无 confirmed finding" → reviewed_clean
  (证伪断言留在 findings 须 severity=Low + title 标 [refuted]);
  "有 confirmed finding" → confirmed。
  ```
- tracked_surfaces 条款 (line 81 附近) 追加面桥接条款:
  ```
  **面桥接 (v3.45)**: finding 落在本清单外的新面时, tracked_surfaces 不填该面,
  在 coverage_note 声明新面 file:line 证据 — 由主代理回填 input_surface.json
  后重跑 r4-collect (R4_TRACKED_MISSING 是原子性阻断, 不桥接不合并)。
  ```

### D-10 verifier 任务书步骤 0 (batch_verify.py ~:3081 段)
- 追加三条:
  ```
  （v3.45, SWR-V3.45-010）同一字段多处读取的**快照读/活体读**区分: 守卫与消费
  读取序不一致时, 枚举 [快照值,活体值) 窗口内的语义后果; 未初始化窗口不得
  以"同一次读取"口径带过。
  （v3.45, SWR-V3.45-010）UNREACHABLE 阻断论证必须枚举**生命周期/提交期 GC**
  维度: 写点在元素自身分配内 ≠ 写入时刻元素仍在世 (提交期回收可先于消费)。
  （v3.45, SWR-V3.45-010, 可选维度）交付二进制核查: extract-ikconfig / nm /
  objdump 实证配置与修复进入交付物 — 比 .config 源码面更强的证据层。
  ```
- 步骤 4 增: "UNREACHABLE 时 claim_type 按声称分析填写 (collect 归档
  claim_self_reported, SWR-V3.45-007)"。

### D-11 resurrect_prompt (workflow_export.py:494)
- 维度 8 后追加:
  ```
  f"  10. 实证通道已开时 (qemu 真实内核引导形态), 优先自建 harness 补测 "
  f"verifier 未实测维度 (SWR-V3.45-011)\n"
  f"  11. gap 引用行号 ±5 容差, 以定义形态为准; 重验者逐字核对 (SWR-V3.45-011)\n"
  ```

### D-12 hypothesis_filter.md 首部 (标题后)
- 追加:
  ```
  **进度摘要 (v3.45, SWR-V3.45-012)**: 每完成 4-5 条输出一行进度摘要
  (filtered N/M: k=x d=y bc=z), 严禁长时间静默 — 静默会被 stream watchdog
  判定停滞 (K4 批次 7/7 筛选 agent 停滞实录; 加本条款后 K5 三组零停滞)。
  ```

### D-13..D-16 SKILL.md 四条款
- R2 假设生成段 (主路径后): 派发条款 (分片落盘 + 回复只给统计, K5-7 实录)。
- 开题四步 (line 238): ① 前加工作区卫生检查条目 (K4-15 实录)。
- 对抗枚举段 (line 173): 追加新机制×旧机制组合窗口维度 (K5-3 实录)。
- R4/R6 severity 裁决处: override 通道提示 (K5-6 实录)。

## P4 版本链五件
1. src/workflow_export.py:22 TOOLING_VERSION "3.44" → "3.45"
2. 版本守卫测试行同步 (grep "3.44" tests/test_v*.py 逐处)
3. SKILL.md 增量段 (SWR-V3.45-001..016 列示 + 验收判据)
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking VERSIONS 登记 (禁再生成)
5. SKILL.md 附录资产计数守卫同步 (D-9 三条款不新增计数, 若条款清单条数变化则同步)
