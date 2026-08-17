import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import evidence_ledger as el

def test_grade_reachable_no_edges_downgrades():
    v = {"verdict": "REACHABLE", "call_chain": ["a", "b", "c"], "edge_evidence": []}
    grade, errors = el.grade_verdict(v)
    assert grade == "static_only"
    assert any("static_only" in e for e in errors)

def test_grade_edge_proven():
    v = {"verdict": "REACHABLE", "call_chain": ["a", "b"],
         "edge_evidence": [{"edge": "a->b", "proof": "grep hit"}]}
    grade, errors = el.grade_verdict(v)
    assert grade == "edge_proven"

def test_grade_empirical():
    v = {"verdict": "REACHABLE", "empirical": {"status": "confirmed"}}
    grade, _ = el.grade_verdict(v)
    assert grade == "empirically_confirmed"

def test_edge_without_proof_errors():
    v = {"verdict": "REACHABLE", "call_chain": ["a", "b"],
         "edge_evidence": [{"edge": "a->b", "proof": ""}]}
    _, errors = el.grade_verdict(v)
    assert any("proof" in e for e in errors)

def test_preconditions_platform_evidence():
    v = {"platform_precondition": "linux_only"}
    issues = el.check_preconditions(v)
    assert any(i["severity"] == "blocking" and "platform_evidence" in i["msg"] for i in issues)

def test_commit_merge_semantics():
    q = {"candidates": [{"id": "CAND-1", "status": "PENDING"}]}
    el.commit(q, {"id": "CAND-1", "verdict": "UNREACHABLE", "status": "VERIFIED"})
    assert len(q["candidates"]) == 1 and q["candidates"][0]["verdict"] == "UNREACHABLE"
    el.commit(q, {"id": "CAND-2", "verdict": "REACHABLE"})
    assert len(q["candidates"]) == 2   # 新增不覆写

def test_commit_correction_record():
    q = {"candidates": [{"id": "CAND-1", "verdict": "REACHABLE", "evidence_grade": "edge_proven"}]}
    el.commit(q, {"id": "CAND-9", "correction": {"target": "CAND-1",
                 "reason": "R5 实证证伪", "demote_to": "UNREACHABLE"}})
    c = q["candidates"][0]
    assert c["verdict"] == "UNREACHABLE" and c["correction_record"]

def test_assert_gates():
    q = {"candidates": [
        {"id": "C-1", "status": "PENDING"},
        {"id": "C-2", "status": "VERIFIED", "verdict": "REACHABLE", "evidence_grade": "static_only"},
        {"id": "C-3", "status": "VERIFIED", "verdict": "REACHABLE", "claim_type": "oom",
         "evidence_grade": "edge_proven"},
    ], "r4_findings": []}
    ok, violations = el.assert_ledger(q)
    assert not ok
    gates = {v["gate"] for v in violations}
    assert {"no_pending", "no_static_only_reachable", "empirical_required", "r4_all_verified"} <= gates

def test_assert_clean_passes():
    q = {"candidates": [
        {"id": "C-1", "status": "VERIFIED", "verdict": "UNREACHABLE", "evidence_grade": "edge_proven"},
        {"id": "C-2", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "empirically_confirmed", "claim_type": "oom"},
    ], "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert ok, violations

# ---- W3: 六门禁扩展 (REQ-V3-093/095/096) ----

def _clean_queue():
    return {"candidates": [
        {"id": "C-1", "status": "VERIFIED", "verdict": "UNREACHABLE", "evidence_grade": "edge_proven"},
        {"id": "C-2", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "empirically_confirmed", "claim_type": "oom"},
    ], "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}

def test_reconciliation_gate():
    q = _clean_queue()
    ok, _ = el.assert_ledger(q, dispatched=["C-1", "C-2"])
    assert ok
    ok2, v2 = el.assert_ledger(q, dispatched=["C-1", "C-2", "C-3"])
    assert not ok2
    g = [v for v in v2 if v["gate"] == "reconciliation"][0]
    assert g["unresolved_ids"] == ["C-3"]

def test_escalated_gate():
    q = _clean_queue()
    q["candidates"][0]["status"] = "ESCALATED"
    ok, v = el.assert_ledger(q)
    assert not ok
    assert "escalated_unsigned" in {x["gate"] for x in v}
    q["escalated_signed_off"] = True
    ok2, _ = el.assert_ledger(q)
    assert ok2

def test_surface_coverage_gate():
    q = _clean_queue()
    ok, _ = el.assert_ledger(q, surface_data={"total": 12, "tracked": 12})
    assert ok
    ok2, v2 = el.assert_ledger(q, surface_data={"total": 12, "tracked": 9})
    assert not ok2
    g = [x for x in v2 if x["gate"] == "surface_coverage"][0]
    assert (g["tracked"], g["total"]) == (9, 12)
    # total=0 (无 input_surface.json) 同样不放行
    ok3, v3 = el.assert_ledger(q, surface_data={"total": 0, "tracked": 0})
    assert not ok3

def test_skipped_gates_warn_not_fail():
    q = _clean_queue()
    ok, v = el.assert_ledger(q)  # dispatched/surface_data 均未提供
    assert ok  # warn 级, 不阻断
    assert any(x["gate"] == "skipped_gates" for x in v)

def test_escalated_is_terminal_for_reconciliation():
    q = _clean_queue()
    q["candidates"][0]["status"] = "ESCALATED"
    q["escalated_signed_off"] = True
    ok, _ = el.assert_ledger(q, dispatched=["C-1", "C-2"])
    assert ok  # ESCALATED 是合法终态, 不触发对账差异
