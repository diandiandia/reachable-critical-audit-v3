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
