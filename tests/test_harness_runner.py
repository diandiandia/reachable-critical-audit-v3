import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness_runner as hr

def test_needs_harness_oom_trigger():
    c = {"claim_type": "oom", "evidence_grade": "edge_proven"}
    assert hr.needs_harness(c) is True

def test_needs_harness_empirically_confirmed_skips():
    c = {"claim_type": "oom", "evidence_grade": "empirically_confirmed"}
    assert hr.needs_harness(c) is False

def test_needs_harness_non_empirical_claim():
    c = {"claim_type": "authz-bypass", "evidence_grade": "edge_proven"}
    assert hr.needs_harness(c) is False

def test_3_templates_registered():
    # v3.1 清理: multipart_align 死 stub 已删除 (仅 3 个真实模板)
    for name in ("ws_frame_alloc", "ws_frame_accum", "xss_path_sim"):
        assert name in hr.TEMPLATES
        assert os.path.exists(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            hr.TEMPLATES[name]["script"]))

def test_apply_result_confirmed():
    c = {"id": "C-1", "verdict": "REACHABLE", "evidence_grade": "edge_proven"}
    hr.apply_result(c, {"status": "confirmed", "rss_growth_kb": 1000000})
    assert c["evidence_grade"] == "empirically_confirmed"

def test_apply_result_refuted_demotes():
    c = {"id": "C-1", "verdict": "REACHABLE", "evidence_grade": "edge_proven"}
    hr.apply_result(c, {"status": "refuted", "reason": "对齐必然恢复"})
    assert c["verdict"] == "UNREACHABLE"
    assert c["correction_record"] and c["evidence_grade"] == "static_only"

def test_parse_empirical_result():
    r = hr.parse_empirical_result('log... {"status": "confirmed", "x": 1} tail')
    assert r["status"] == "confirmed"
    r2 = hr.parse_empirical_result("no json here")
    assert r2["status"] == "parse_error"

def test_sampling_protocol_contains_rate_check():
    assert "投递速率确认" in hr.SAMPLING_PROTOCOL
    assert "/proc/" in hr.SAMPLING_PROTOCOL
