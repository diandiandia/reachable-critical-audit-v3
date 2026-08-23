import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import batch_verify as bv

def _mk_project():
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    q = {"schema_version": "2.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.rs", "source_line": 1, "status": "PENDING", "priority": 0},
        {"id": "R05-abc123", "source_file": "b.rs", "source_line": 2, "status": "PENDING", "priority": 1},
    ]}
    bv.save_queue(tmp, q)
    return tmp

def test_collect_literal_r05_id():
    tmp = _mk_project()
    v = {"verdict": "UNREACHABLE", "reachability_type": "INDIRECT",
         "call_chain": ["a:1:f", "b:2:g"], "call_chain_depth": 2,
         "evidence": "no callers", "blocking_point": "no production callers"}
    bv.stage_collect(tmp, 1, {"R05-abc123": v})
    q = bv.load_queue(tmp)
    c = [c for c in q["candidates"] if c["id"] == "R05-abc123"][0]
    assert c["status"] == "VERIFIED" and c["verdict"] == "UNREACHABLE"

def test_collect_blocking_point_autofill():
    tmp = _mk_project()
    v = {"verdict": "UNREACHABLE", "reachability_type": "INDIRECT",
         "call_chain": ["a:1:f", "b:2:g", "c:3:h"], "call_chain_depth": 3,
         "evidence": "x"}
    bv.stage_collect(tmp, 1, {"CAND-001": v})
    q = bv.load_queue(tmp)
    c = q["candidates"][0]
    assert c["blocking_point"] == "b:2:g" and c.get("blocking_point_autofilled")

def test_collect_dead_code_depth_exempt():
    tmp = _mk_project()
    v = {"verdict": "UNREACHABLE", "reachability_type": "INDIRECT",
         "call_chain": ["a:1:f"], "call_chain_depth": 1,
         "evidence": "no callers", "blocking_point": "no production callers"}
    bv.stage_collect(tmp, 1, {"CAND-001": v})
    q = bv.load_queue(tmp)
    c = q["candidates"][0]
    assert c["verdict"] == "UNREACHABLE"   # 不降级 NEEDS_REVIEW

def test_lenient_json():
    assert bv._load_lenient_json('{"a": "c:\\x"}')["a"] == "c:\\x"

def test_r4_collect_assert():
    tmp = _mk_project()
    findings = [{"hypothesis_id": f"H-{i}", "verdict": "reviewed_clean", "findings": []}
                for i in range(1, 8)]
    f = os.path.join(tmp, "_r4.json")
    json.dump(findings, open(f, "w"))
    bv.stage_r4_collect(tmp, f)
    q = bv.load_queue(tmp)
    assert len(q["r4_findings"]) == 7
    assert bv.stage_r4_assert(tmp) == 0

def test_report_outputs():
    tmp = _mk_project()
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_report(tmp)
    r = json.loads(buf.getvalue())
    assert r["total_candidates"] == 2 and "evidence_grade_distribution" in r

def test_next_batch_size():
    tmp = _mk_project()
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_next(tmp, batch_size=1)
    info = json.loads(buf.getvalue())
    assert info["count"] == 1


def test_r4_collect_unwraps_hypotheses_dict():
    """v3.2.3 (Lua 审计): 任务书模板产出 {"hypotheses":[...]} 包裹时自动解包,
    不再静默空收 (此前 top-level dict 无 hypothesis_id → 收集 0 条无告警)。"""
    tmp = _mk_project()
    wrapped = {"hypotheses": [
        {"hypothesis_id": "H-1", "verdict": "reviewed_clean", "findings": []},
        {"hypothesis_id": "H-2", "verdict": "reviewed_clean", "findings": []}]}
    f = os.path.join(tmp, "_r4_wrapped.json")
    json.dump(wrapped, open(f, "w"))
    bv.stage_r4_collect(tmp, f)
    q = bv.load_queue(tmp)
    assert len(q["r4_findings"]) == 2
    assert {x["hypothesis_id"] for x in q["r4_findings"]} == {"H-1", "H-2"}


def test_r4_collect_warns_on_zero_extraction():
    """v3.2.3 (Lua 审计): 输入非空但 0 hypothesis_id → stderr 告警。"""
    tmp = _mk_project()
    f = os.path.join(tmp, "_r4_bad.json")
    json.dump([{"verdict": "reviewed_clean", "findings": []}], open(f, "w"))
    import io, contextlib
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        bv.stage_r4_collect(tmp, f)
    q = bv.load_queue(tmp)
    assert q["r4_findings"] == []
    assert "R4_COLLECT_WARNING" in err.getvalue()

# ---- SWR-V3.3.2-033: verifier 任务书 claim 与实证自洽条款 ----
def test_prompt_claim_empirical_consistency_clause():
    import tempfile
    tmp = tempfile.mkdtemp()
    cand = {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
            "sink_type": "CWE-770", "language": "c"}
    ctx = bv._build_context(cand, tmp)
    prompt = bv._build_prompt(cand, ctx, tmp)
    assert "claim 与实证自洽" in prompt
    assert "SWR-V3.3.2-033" in prompt

# ---- SWR-V3.3.2-014: 步骤 0.5 按型门控 ----
def test_step05_gating_static_lang_short():
    import tempfile
    tmp = tempfile.mkdtemp()
    cand = {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
            "sink_type": "CWE-770", "language": "c"}
    ctx = bv._build_context(cand, tmp)
    prompt = bv._build_prompt(cand, ctx, tmp)
    assert "build 列表核对" in prompt            # 短段注入
    assert "模块可导入性预检" not in prompt        # 完整段不注入
    assert "顶层包解析" not in prompt

def test_step05_gating_dynamic_lang_full():
    import tempfile
    tmp = tempfile.mkdtemp()
    cand = {"id": "CAND-002", "source_file": "a.py", "source_line": 1,
            "sink_type": "CWE-502", "language": "python"}
    ctx = bv._build_context(cand, tmp)
    prompt = bv._build_prompt(cand, ctx, tmp)
    assert "模块可导入性预检" in prompt            # 完整段保留

def test_step05_gating_application_full_even_static():
    import tempfile, json, os
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": [],
               "target_kind": "application"},
              open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    cand = {"id": "CAND-003", "source_file": "a.c", "source_line": 1,
            "sink_type": "CWE-770", "language": "c"}
    ctx = bv._build_context(cand, tmp)
    prompt = bv._build_prompt(cand, ctx, tmp)
    assert "模块构建包含性预检" in prompt          # application 目标保留完整段

# ---- SWR-V3.3.2-085/088: coverage 归一化 + journal --expect ----
import os as _os
WORK = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
def test_journal_expect_full_set_enforced():
    import tempfile, subprocess, sys, os
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "status": "PENDING"}]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    jdir = tempfile.mkdtemp()
    # journal 只含 CAND-002 → --expect CAND-001,CAND-002 应报错不落盘
    with open(os.path.join(jdir, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result",
                            "result": {"id": "CAND-002", "verdict": "UNREACHABLE",
                                       "reachability_type": "DIRECT",
                                       "call_chain": ["a", "b", "c"],
                                       "call_chain_depth": 3, "evidence": "e"}}) + "\n")
    r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                        tmp, "--stage", "collect", "--from-journal", jdir,
                        "--expect", "CAND-001,CAND-002"],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "全集校验失败" in r.stderr

# ---- SWR-V3.3.2-086/087: gap 渲染 + 抽样落盘 ----
def test_gap_rendered_in_verify_payload():
    import tempfile, sys, os
    sys.path.insert(0, WORK)
    import workflow_export as we
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
         "sink_type": "CWE-770", "status": "PENDING", "language": "c",
         "re_verify_gap": "遗漏 multipart 预解析分支"},
        {"id": "CAND-002", "source_file": "b.c", "source_line": 1,
         "sink_type": "CWE-400", "status": "PENDING", "language": "c"}]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = we.export_script(tmp, mode="verify")
    by_id = {p["id"]: p["prompt"] for p in r["payload"]}
    assert "复活复核 gap" in by_id["CAND-001"]
    assert "multipart" in by_id["CAND-001"]
    assert "复活复核 gap" not in by_id["CAND-002"]

def test_resurrect_sample_dump():
    import tempfile, sys, os
    sys.path.insert(0, WORK)
    import workflow_export as we
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "claim_type": "crash", "evidence": "x"},
        {"id": "CAND-002", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "evidence": "管道语义, 无实证类声称"}]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = we.export_script_resurrect(tmp, batch_size=8)
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    doc = json.load(open(os.path.join(tmp, ".audit_results", "_resurrect_sample.json")))
    assert doc["selected"] == ["CAND-001", "CAND-002"]
    assert doc["rule"].startswith("声称类")

# ---- SWR-V3.4-040/041: 覆盖账本聚合与缺口 ----
def test_coverage_ledger_write_and_idempotent():
    import tempfile, subprocess, sys, os, json as _json, shutil
    sys.path.insert(0, WORK)
    # 测试写真实账本资产 → 快照/恢复, 防污染 (账本为记录型资产)
    ledger_path = os.path.join(WORK, "resources", "issue_coverage_matrix.json")
    snapshot = open(ledger_path).read()
    try:
        _run_ledger_tests()
    finally:
        open(ledger_path, "w").write(snapshot)


def _run_ledger_tests():
    import tempfile, subprocess, sys, os, json as _json
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    # v3.6 (P1-4): 回填前置要求 r4_findings H1-H7 全 VERIFIED——fixture 补全
    _json.dump({"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
         "sink_type": "CWE-770", "status": "VERIFIED", "language": "c", "cwe": ["CWE-770"]},
        {"id": "CAND-002", "source_file": "b.py", "source_line": 1,
         "sink_type": "CWE-327", "status": "VERIFIED", "language": "python"}],
        "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED", "findings": []}
                        for i in range(1, 8)]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                        tmp, "--stage", "coverage-ledger", "--write"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = _json.loads(r.stdout)
    assert out["status"] == "LEDGER_WRITTEN"
    assert "RESOURCE-DOSxc" in out["new_counts"]
    assert "CRYPTOxpython" in out["new_counts"]
    # 幂等 (skip 分支附 would_be_new_counts, v3.6)
    r2 = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                         tmp, "--stage", "coverage-ledger", "--write"],
                        capture_output=True, text=True)
    out2 = _json.loads(r2.stdout)
    assert out2["status"] == "LEDGER_IDEMPOTENT_SKIP"
    assert "would_be_new_counts" in out2
    assert "RESOURCE-DOSxc" in out2["would_be_new_counts"]

def test_coverage_ledger_gaps_prints_crypto_gap():
    import tempfile, subprocess, sys, os, json as _json
    sys.path.insert(0, WORK)
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    _json.dump({"schema_version": "3.0", "candidates": []},
               open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                        tmp, "--stage", "coverage-ledger"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = _json.loads(r.stdout)
    assert out["status"] == "LEDGER_GAPS"
    assert any("CRYPTO" in g for g in out["gap_cells"])

# ---- v3.4.1: coverage 读 _r2_filter.json (旧 schema 兼容) ----
def test_coverage_ledger_empty_queue_lang_from_surface():
    """空队 (R3 空队, R2 keep 0 合法终态) + input_surface lang=go →
    账本写 go 格, other 零新增。quic-go 实录: 全 Go 项目 R4 findings 误记
    *xother 格, 账本失真人工修正——回退链根修。"""
    import tempfile, subprocess, sys, os, json as _json
    sys.path.insert(0, WORK)
    # 测试写真实账本资产 → 快照/恢复, 防污染 (账本为记录型资产)
    ledger_path = os.path.join(WORK, "resources", "issue_coverage_matrix.json")
    snapshot = open(ledger_path).read()
    try:
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, ".audit_results"))
        _json.dump({"schema_version": "3.0", "surfaces": [
            {"id": "SURF-DATA-001", "name": "a", "type": "data", "lang": "go"}]},
            open(os.path.join(tmp, ".audit_results", "input_surface.json"), "w"))
        _json.dump({"schema_version": "3.0", "candidates": [],
                    "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                                     "findings": []} for i in range(2, 8)] +
                    [{"hypothesis_id": "H1", "status": "VERIFIED", "findings": [
                        {"title": "x", "cwe": ["CWE-770"]}]}]},
            open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                            tmp, "--stage", "coverage-ledger", "--write"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        out = _json.loads(r.stdout)
        assert out["status"] == "LEDGER_WRITTEN"
        assert "RESOURCE-DOSxgo" in out["new_counts"], out["new_counts"]
        assert not any("xother" in k for k in out["new_counts"]), out["new_counts"]
    finally:
        open(ledger_path, "w").write(snapshot)


def test_coverage_ledger_derivation_chain():
    """候选非空 (lang=rust) + surface lang=go → 仍按候选 rust 计
    (回退链不覆盖候选级事实——回退只服务空队形态, 防破坏既有行为)。"""
    import tempfile, subprocess, sys, os, json as _json
    sys.path.insert(0, WORK)
    ledger_path = os.path.join(WORK, "resources", "issue_coverage_matrix.json")
    snapshot = open(ledger_path).read()
    try:
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, ".audit_results"))
        _json.dump({"schema_version": "3.0", "surfaces": [
            {"id": "SURF-DATA-001", "name": "a", "type": "data", "lang": "go"}]},
            open(os.path.join(tmp, ".audit_results", "input_surface.json"), "w"))
        _json.dump({"schema_version": "3.0", "candidates": [
            {"id": "CAND-001", "source_file": "a.rs", "source_line": 1,
             "sink_type": "CWE-770", "status": "VERIFIED", "language": "rust",
             "cwe": ["CWE-770"]}],
            "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                             "findings": []} for i in range(1, 8) if i != 2] +
            [{"hypothesis_id": "H2", "status": "VERIFIED", "findings": [
                {"title": "y", "cwe": ["CWE-345"]}]}]},
            open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                            tmp, "--stage", "coverage-ledger", "--write"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        out = _json.loads(r.stdout)
        assert out["status"] == "LEDGER_WRITTEN"
        # 候选级语言优先: RESOURCE-DOS 记 rust 不记 go (surface lang 被候选覆盖)
        assert "RESOURCE-DOSxrust" in out["new_counts"], out["new_counts"]
        assert "RESOURCE-DOSxgo" not in out["new_counts"], out["new_counts"]
        # R4 findings 走主导语言 (dom=rust, 与候选一致)
        assert "DATA-INTEGRITYxrust" in out["new_counts"], out["new_counts"]
    finally:
        open(ledger_path, "w").write(snapshot)


# ---------------- v3.5 (B2/B5) 防回退 ----------------

def test_step05_dispatch_family_wording():
    """v3.5 (B2): static_short 按语言家族分派——各家族措辞含本族构建/加载语义。"""
    for lang, needle in (("go", "go.mod"), ("rust", "Cargo.toml"),
                         ("kotlin", "sourceSet"), ("scala", "sourceSet"),
                         ("csharp", ".csproj"), ("swift", "Package.swift"),
                         ("php", "require/include"), ("ruby", "Gemfile"),
                         ("perl", "use/require"), ("powershell", "Import-Module"),
                         ("shell", "source/调用")):
        assert needle in bv.STATIC_SHORT_BY_FAMILY[lang], lang
    assert "CMake" in bv.STATIC_SHORT_BY_FAMILY["c"]  # C 系措辞保留


def test_step05_dispatch_script_family_no_c_words():
    """v3.5 (B2): script 族措辞不得再是 C 系构建词汇 (偏见 B2 根因)。"""
    for lang in ("php", "ruby", "perl", "powershell", "shell"):
        t = bv.STATIC_SHORT_BY_FAMILY[lang]
        for cword in ("CMake", "GOPATH", "cargo", "Makefile"):
            assert cword not in t, f"{lang} 仍含 C 系词汇 {cword}"


def test_coverage_ledger_write_blocked_r4():
    """v3.6 (P1-4): r4_findings 未全 VERIFIED 时 --write 被机械阻断且不烧 sources key
    (puma 审计实录: 先回填后补标 cwe 使 INJECTION×ruby 缺口不可回写)。"""
    import tempfile, subprocess, sys, os, json as _json
    sys.path.insert(0, WORK)
    ledger_path = os.path.join(WORK, "resources", "issue_coverage_matrix.json")
    snapshot = open(ledger_path).read()
    try:
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, ".audit_results"))
        # H-7 缺失 (只有 H1-H6 VERIFIED)
        _json.dump({"schema_version": "3.0", "candidates": [
            {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
             "sink_type": "CWE-770", "status": "VERIFIED", "language": "c",
             "cwe": ["CWE-770"]}],
            "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                             "findings": []} for i in range(1, 7)]},
            open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        before = open(ledger_path).read()
        r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                            tmp, "--stage", "coverage-ledger", "--write"],
                           capture_output=True, text=True)
        assert r.returncode == 1, r.stdout
        out = _json.loads(r.stdout)
        assert out["status"] == "LEDGER_WRITE_BLOCKED_R4"
        assert "H-7" in out["missing"]
        # 不烧 sources key: 账本字节级不变
        assert open(ledger_path).read() == before
    finally:
        open(ledger_path, "w").write(snapshot)


def test_coverage_ledger_write_blocked_feedback():
    """v3.6 (P1-4): r4_feedback 未决冲突时 --write 被阻断且不烧 key。
    冲突构造: H-7 default_value_table 承诺 true vs REACHABLE 候选 evidence
    声称默认明文 (零值 false)——同 test_v321 r4_feedback 冲突先例。"""
    import tempfile, subprocess, sys, os, json as _json
    sys.path.insert(0, WORK)
    ledger_path = os.path.join(WORK, "resources", "issue_coverage_matrix.json")
    snapshot = open(ledger_path).read()
    try:
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, ".audit_results"))
        _json.dump({"schema_version": "3.0", "candidates": [
            {"id": "CAND-001", "source_file": "a.go", "source_line": 1,
             "sink_type": "CWE-400", "status": "VERIFIED", "verdict": "REACHABLE",
             "language": "go", "cwe": ["CWE-400"],
             "evidence": "tls_enable 零值 false 默认明文可达 (配置未提交实际值)"}],
            "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                             "findings": []} for i in range(1, 7)] +
            [{"hypothesis_id": "H-7", "status": "VERIFIED", "findings": [],
              "default_value_table": [{"name": "tls_enable", "default": "true"}]}]},
            open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        before = open(ledger_path).read()
        r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                            tmp, "--stage", "coverage-ledger", "--write"],
                           capture_output=True, text=True)
        assert r.returncode == 1, r.stdout
        out = _json.loads(r.stdout)
        assert out["status"] == "LEDGER_WRITE_BLOCKED_FEEDBACK"
        assert any(c.get("key") == "tls_enable" for c in out["conflicts"])
        assert open(ledger_path).read() == before
    finally:
        open(ledger_path, "w").write(snapshot)


def test_coverage_ledger_pressure():
    """v3.5 (B5): 账本格压力统计——饱和格标记 + 族偏斜降序。"""
    ledger = {"rows": [
        {"family": "RESOURCE-DOS", "langs": {"go": 55, "python": 3}},
        {"family": "CRYPTO", "langs": {"rust": 2}},
    ]}
    p = bv._ledger_pressure(ledger)
    assert p["pressure_cells"][0] == {"cell": "RESOURCE-DOS x go",
                                      "count": 55, "saturated": True}
    assert p["pressure_cells"][1]["saturated"] is False
    # top_share 降序: CRYPTO 2/2=1.0 高于 RESOURCE-DOS 55/58≈0.948
    assert p["family_skew"][0]["family"] == "CRYPTO"
    assert p["family_skew"][1]["family"] == "RESOURCE-DOS"
    assert p["family_skew"][1]["top_share"] == round(55 / 58, 3)
