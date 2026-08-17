import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import signature_lib

def test_validate_ok():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    ok, errors = signature_lib.validate(d)
    assert ok, errors

def test_validate_rejects_empty_known_instances():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    d["signatures"][0]["known_instances"] = []
    ok, errors = signature_lib.validate(d)
    assert not ok and any("known_instances 为空" in e for e in errors)

def test_validate_rejects_bad_grep():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    d["signatures"][0]["detection_hints"]["grep"] = ["append("]
    ok, errors = signature_lib.validate(d)
    assert not ok and any("bad grep pattern" in e for e in errors)

def test_validate_rejects_bad_profile():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    d["signatures"][0]["platform_profiles"] = ["bogus-profile"]
    ok, errors = signature_lib.validate(d)
    assert not ok and any("invalid platform_profiles" in e for e in errors)

def test_smoke_hit():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    with tempfile.TemporaryDirectory() as tmp:
        # 造一个仓库: 实例文件含匹配模式
        inst = d["signatures"][0]["known_instances"][0]
        f = os.path.join(tmp, inst["file"])
        os.makedirs(os.path.dirname(f), exist_ok=True)
        lines = ["x"] * inst["line"]
        lines[inst["line"] - 1] = "this.buf.extend_from_slice(&chunk[..]);"
        open(f, "w").write("\n".join(lines))
        results, rate, testable = signature_lib.smoke_test(d, [tmp])
        assert results[d["signatures"][0]["sig_id"]]["hit"] is True

def test_smoke_skip_when_repo_missing():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    results, rate, testable = signature_lib.smoke_test(d, ["/nonexistent-repo-xyz"])
    assert all(r.get("skipped") for r in results.values())
    assert rate == 0.0
