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

def test_needs_harness_rce_leak_trigger():
    """v3.6 (P1-3): EMPIRICAL_CLAIMS 8 类对称——rce/leak 声称触发 needs_harness
    (旧 6 类集: rce/leak 能绑定清单却不触发 harness——对称缺口)。"""
    assert hr.needs_harness({"claim_type": "rce", "evidence_grade": "edge_proven"}) is True
    assert hr.needs_harness({"claim_type": "leak", "evidence_grade": "static_only"}) is True
    assert hr.needs_harness({"claim_type": "rce", "evidence_grade": "empirically_confirmed"}) is False
    assert hr.needs_harness({"claim_type": "leak", "evidence_grade": "empirically_confirmed"}) is False

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


def test_env_traps_covers_16_langs():
    """v3.6 (P2-⑥): PER_LANG_ENV_TRAPS 对齐 harness_manuals/ 16 语言
    (旧 7 语言: cpp/cs/typescript/kotlin/scala/perl/php/powershell/shell 缺条目)。"""
    import os
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "harness_manuals")
    manuals = {f[:-3] for f in os.listdir(base)
               if f.endswith(".md")
               and f not in ("mixed_build.md", "ENVIRONMENT_PROBES.md")}
    assert len(manuals) == 16
    missing = manuals - set(hr.PER_LANG_ENV_TRAPS)
    assert missing == set(), f"缺 env 陷阱的语言: {missing}"
    # 反向: PER_LANG 键不得悬空 (无手册的语言条目是孤儿设计)
    orphan = set(hr.PER_LANG_ENV_TRAPS) - manuals
    assert orphan == set(), f"悬空 PER_LANG 键: {orphan}"


def test_env_traps_each_lang_has_items():
    """v3.6 (P2-⑥): 每语言条目非空且不含项目名 (去项目化义务)。"""
    for lang, items in hr.PER_LANG_ENV_TRAPS.items():
        assert items and all(isinstance(t, str) and t for t in items), lang
        blob = " ".join(items).lower()
        for tok in ("ktor", "actix", "awstats", "sinatra", "django"):
            assert tok not in blob, (lang, tok)


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
