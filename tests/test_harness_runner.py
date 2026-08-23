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

def test_templates_registered_no_dangling():
    # v3.5: multipart_align 悬空注册已删除 (注册名 = 磁盘文件一一对应)
    assert "multipart_align" not in hr.TEMPLATES
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, spec in hr.TEMPLATES.items():
        assert os.path.exists(os.path.join(base, spec["script"])), name

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


def test_cli_manual_traps_require_lang():
    """v3.5.2 (P3): manual/traps 缺 lang 参数报 usage exit=2 (旧: 静默默认 rust)。"""
    import subprocess
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("manual", "traps"):
        p = subprocess.run(
            [sys.executable, os.path.join(here, "harness_runner.py"), sub],
            capture_output=True, text=True)
        assert p.returncode == 2, (sub, p.returncode)
        assert "usage" in p.stderr, (sub, p.stderr)
