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

def test_cluster_collect_broadcast():
    tmp = _mk_project()
    task = {"cluster_key": ["a.rs", "CWE-918"], "members": [
        {"id": "CAND-001", "source_file": "a.rs", "source_line": 1}]}
    tf = os.path.join(tmp, ".audit_results", "_cluster_xxx.json")
    json.dump(task, open(tf, "w"))
    verdict = {"verdict": "UNREACHABLE", "verdict_map": "all",
               "call_chain": ["a:1:f", "b:2:g", "c:3:h"], "call_chain_depth": 3,
               "blocking_point": "N/A", "evidence": "噪声簇",
               "exceptions": []}
    bv.stage_cluster_collect(tmp, tf, verdict)
    q = bv.load_queue(tmp)
    c = q["candidates"][0]
    assert c["verdict"] == "UNREACHABLE" and c["clustered_verified"]

def test_cluster_collect_exception_overrides():
    tmp = _mk_project()
    task = {"cluster_key": ["a.rs", "CWE-918"], "members": [
        {"id": "CAND-001", "source_file": "a.rs", "source_line": 1}]}
    tf = os.path.join(tmp, ".audit_results", "_cluster_xxx.json")
    json.dump(task, open(tf, "w"))
    ex = {"id": "CAND-001", "verdict": "REACHABLE", "reachability_type": "DIRECT",
          "call_chain": ["a:1", "b:2", "c:3"], "call_chain_depth": 3, "evidence": "e",
          "blocking_point": None}
    bv.stage_cluster_collect(tmp, tf, {"verdict": "UNREACHABLE", "exceptions": [ex]})
    q = bv.load_queue(tmp)
    assert q["candidates"][0]["verdict"] == "REACHABLE"

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
def test_coverage_normalizes_surf_prefix():
    import tempfile, subprocess, sys, os
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "surfaces": [
        {"id": "S-001", "name": "x", "type": "network_endpoint"}]},
        open(os.path.join(tmp, ".audit_results", "input_surface.json"), "w"))
    json.dump({"schema_version": "3.0", "candidates": [],
               "r4_findings": [{"hypothesis_id": "H-1", "status": "VERIFIED",
                 "findings": [{"title": "t", "tracked_surfaces": ["SURF-S-001"]}]}]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                        tmp, "--stage", "coverage"],
                       capture_output=True, text=True)
    out = json.loads(r.stdout)
    assert out["status"] == "COVERAGE_OK", out
    assert out["missing"] == []
    assert r.returncode == 0

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
    _json.dump({"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
         "sink_type": "CWE-770", "status": "VERIFIED", "language": "c", "cwe": ["CWE-770"]},
        {"id": "CAND-002", "source_file": "b.py", "source_line": 1,
         "sink_type": "CWE-327", "status": "VERIFIED", "language": "python"}]},
        open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    r = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                        tmp, "--stage", "coverage-ledger", "--write"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = _json.loads(r.stdout)
    assert out["status"] == "LEDGER_WRITTEN"
    assert "RESOURCE-DOSxc" in out["new_counts"]
    assert "CRYPTOxpython" in out["new_counts"]
    # 幂等
    r2 = subprocess.run([sys.executable, os.path.join(WORK, "tools", "batch_verify.py"),
                         tmp, "--stage", "coverage-ledger", "--write"],
                        capture_output=True, text=True)
    assert _json.loads(r2.stdout)["status"] == "LEDGER_IDEMPOTENT_SKIP"

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
