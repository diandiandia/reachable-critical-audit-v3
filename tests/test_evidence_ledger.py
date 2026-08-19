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
    q = {"target_kind": "application", "candidates": [
        {"id": "C-1", "status": "VERIFIED", "verdict": "UNREACHABLE", "evidence_grade": "edge_proven"},
        {"id": "C-2", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "empirically_confirmed", "claim_type": "oom"},
    ], "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert ok, violations

# ---- W3: 六门禁扩展 (REQ-V3-093/095/096) ----

def _clean_queue():
    # v3.2.1: target_kind 为门禁⑧ 必填字段 (旧队列复跑以 require_target_kind=False 豁免)
    return {"target_kind": "application", "candidates": [
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

# ---- SWR-V3.3.2-001: gate ③ verdict 条件 ----
def test_gate3_verdict_condition_needs_review_claim_not_triggered():
    q = {"target_kind": "application", "candidates": [
        {"id": "CAND-1", "status": "NEEDS_REVIEW", "verdict": "NEEDS_REVIEW",
         "claim_type": "crash", "evidence_grade": "edge_proven"},
    ], "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert ok, violations
    assert not any(v.get("gate") == "empirical_required" for v in violations)

def test_gate3_reachable_claim_still_enforced():
    q = {"target_kind": "application", "candidates": [
        {"id": "CAND-1", "status": "VERIFIED", "verdict": "REACHABLE",
         "claim_type": "crash", "evidence_grade": "edge_proven"},
    ], "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert not ok
    assert any(v.get("gate") == "empirical_required" for v in violations)

# ---- SWR-V3.3.2-002: demote 清 claim ----
def test_commit_demote_clears_claim():
    q = {"target_kind": "application",
         "candidates": [{"id": "CAND-1", "status": "VERIFIED", "verdict": "REACHABLE",
                         "claim_type": "crash", "evidence_grade": "empirically_confirmed"}],
         "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"} for i in range(1, 8)]}
    el.commit(q, {"id": "CAND-1",
                  "correction": {"target": "CAND-1", "demote_to": "NEEDS_REVIEW",
                                 "reason": "R5 可选路径裁决", "by": "main-agent"}})
    c = q["candidates"][0]
    assert c["verdict"] == "NEEDS_REVIEW"
    assert c.get("claim_type") is None
    assert c.get("claim_nulled_by") == "commit-demote-v3.3.2"
    # demote 后 gate ③ 不再误触发
    c["status"] = "NEEDS_REVIEW"
    ok, violations = el.assert_ledger(q)
    assert ok, violations

# ---- SWR-V3.3.2-003: status 大小写归一化 ----
def test_empirical_status_case_normalized():
    v = {"verdict": "REACHABLE", "empirical": {"status": "CONFIRMED"}}
    grade, errors = el.grade_verdict(v)
    assert grade == "empirically_confirmed", errors

def test_grade_mismatch_warns():
    v = {"verdict": "REACHABLE", "call_chain": ["a", "b"],
         "edge_evidence": [{"edge": "a->b", "proof": "hit"}],
         "evidence_grade": "empirically_confirmed"}  # 无 empirical 字段 → 机械=edge_proven
    grade, errors = el.grade_verdict(v)
    assert grade == "edge_proven"
    assert any("不一致" in e for e in errors)

# ---- SWR-V3.3.2-004: ③b 结构化 + 收窄 ----
def _r4q(findings):
    return {"target_kind": "application",
            "candidates": [{"id": "C-1", "status": "VERIFIED", "verdict": "UNREACHABLE",
                            "evidence_grade": "edge_proven"}],
            "r4_findings": [
                {"hypothesis_id": f"H-{i}", "status": "VERIFIED"}
                for i in range(1, 8)] + [
                {"hypothesis_id": "H-1", "status": "VERIFIED", "verdict": "confirmed",
                 "findings": findings}]}

def test_gate3b_structured_medium_without_empirical_blocks():
    q = _r4q([{"title": "x", "severity": "Medium", "claim_type": "oom",
               "empirical_result": None}])
    ok, violations = el.assert_ledger(q)
    assert not ok
    assert any(v.get("gate") == "empirical_required_r4" for v in violations)

def test_gate3b_structured_medium_confirmed_passes():
    q = _r4q([{"title": "x", "severity": "Medium", "claim_type": "oom",
               "empirical_result": "CONFIRMED — 实测 RSS +500MB"}])
    ok, violations = el.assert_ledger(q)
    assert ok, [v for v in violations if v.get("gate") == "empirical_required_r4"]

def test_gate3b_low_no_claim_not_blocked():
    # Low 且无 claim_type → 收窄后不强制 (旧关键词匹配曾误伤)
    q = _r4q([{"title": "crash 倾向但宿主驱动", "severity": "Low",
               "claim_type": None, "empirical_result": None,
               "evidence": "unbounded growth 由宿主配置决定"}])
    ok, violations = el.assert_ledger(q)
    assert ok, [v for v in violations if v.get("gate") == "empirical_required_r4"]

def test_gate3b_low_forced_claim_mechanism_accepted():
    # Low + forced claim + 机制级证据 → 收窄条款接受
    q = _r4q([{"title": "x", "severity": "Low", "claim_type": "oom",
               "empirical_result": "机制级确证（静态链路）"}])
    ok, violations = el.assert_ledger(q)
    assert ok, [v for v in violations if v.get("gate") == "empirical_required_r4"]

# ---- SWR-V3.3.2-005: 复活改判防漏放 ----
def test_post_resurrect_refutation_required():
    q = {"target_kind": "application",
         "candidates": [{"id": "C-1", "status": "VERIFIED", "verdict": "REACHABLE",
                         "evidence_grade": "edge_proven", "claim_type": "other",
                         "re_verify_gap": "复活者 gap"}],
         "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"}
                         for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert not ok
    assert any(v.get("gate") == "post_resurrect_refutation" for v in violations)

def test_post_resurrect_refutation_satisfied():
    q = {"target_kind": "application",
         "candidates": [{"id": "C-1", "status": "VERIFIED", "verdict": "REACHABLE",
                         "evidence_grade": "empirically_confirmed", "claim_type": "other",
                         "re_verify_gap": "gap", "refutation": {"by": "refuter-1"}}],
         "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED"}
                         for i in range(1, 8)]}
    ok, violations = el.assert_ledger(q)
    assert ok, [v for v in violations if v.get("gate") == "post_resurrect_refutation"]

# ---- SWR-V3.3.2-006: r4_feedback 结构化输入 ----
def test_r4_feedback_structured_table_conflict():
    # H7 结构化表 committed=true vs 候选 code-lens 声称默认 false → 冲突 warn
    q = {"target_kind": "application",
         "candidates": [
            {"id": "C-1", "status": "VERIFIED", "verdict": "REACHABLE",
             "evidence_grade": "empirically_confirmed", "claim_type": "other",
             "evidence": "tls_enable 默认 false（明文）, 检查点缺失"}],
         "r4_findings": [
            {"hypothesis_id": f"H-{i}", "status": "VERIFIED"}
            for i in range(1, 8)] + [
            {"hypothesis_id": "H-7", "status": "VERIFIED", "verdict": "confirmed",
             "default_value_table": [
                 {"name": "tls_enable", "default": "true",
                  "code_point": "config.yaml", "disposition": "保留"}]}]}
    ok, violations = el.assert_ledger(q)
    # warn 级不阻断 PASS, 但冲突必须产出
    assert ok
    assert any(v.get("gate") == "r4_feedback" for v in violations)

# ---- v3.4.1: 旧 empirical schema (无 status, 有 scope) 兼容 ----
def test_grade_old_empirical_scope_inference():
    v = {"verdict": "REACHABLE",
         "empirical": {"scope": "e2e", "harness": "h/", "result": "RSS +8GB"}}
    grade, errors = el.grade_verdict(v)
    assert grade == "empirically_confirmed", errors
    assert any("旧 empirical schema" in e for e in errors)

def test_grade_mechanism_scope_not_inferred():
    # 机制级 scope 不推断 (REQ-V3.1-045 范围纪律)
    v = {"verdict": "REACHABLE",
         "empirical": {"scope": "mechanism", "result": "静态核实"},
         "call_chain": ["a", "b"],
         "edge_evidence": [{"edge": "a->b", "proof": "hit"}]}
    grade, errors = el.grade_verdict(v)
    assert grade == "edge_proven", (grade, errors)

def test_r4_feedback_single_char_key_filtered():
    q = {"target_kind": "application",
         "candidates": [
            {"id": "C-1", "status": "VERIFIED", "verdict": "REACHABLE",
             "evidence_grade": "empirically_confirmed", "claim_type": "other",
             "evidence": "c=744 配置行"}],
         "r4_findings": [
            {"hypothesis_id": f"H-{i}", "status": "VERIFIED"}
            for i in range(1, 8)] + [
            {"hypothesis_id": "H-7", "status": "VERIFIED", "verdict": "confirmed",
             "default_value_table": [
                 {"name": "c", "default": "574", "code_point": "x",
                  "disposition": "保留"}]}]}
    ok, violations = el.assert_ledger(q)
    assert ok
    assert not any(v.get("gate") == "r4_feedback" for v in violations)
