import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import signature_lib

def test_validate_ok():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    ok, errors = signature_lib.validate(d)
    assert ok, errors

def test_validate_rejects_empty_known_instances():
    # v3.2.2: 锚点移入 tests/fixtures, known_instances 非空强制退役——
    # 空 known_instances 不再报错; 但 lang/cwe/deproject 检查生效
    d = json.load(open(signature_lib.DEFAULT_PATH))
    d["signatures"][0]["known_instances"] = []
    ok, errors = signature_lib.validate(d)
    assert ok, errors

def test_validate_rejects_l2_without_lang():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    l2 = next(s for s in d["signatures"] if s.get("tier") == "L2")
    l2["lang"] = None
    ok, errors = signature_lib.validate(d)
    assert not ok and any("lang 必填" in e for e in errors)

def test_validate_rejects_project_specific_token():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    d["signatures"][0]["detection_hints"]["grep"] = ["multer"]
    ok, errors = signature_lib.validate(d)
    assert not ok and any("项目专属名" in e for e in errors)

def test_all_signatures_have_lang_and_cwe():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    for s in d["signatures"]:
        assert s.get("cwe"), s["sig_id"]
        assert s.get("lang") in signature_lib.VALID_LANGS, s["sig_id"]
        if s.get("tier") == "L2":
            assert s["lang"] != "any", s["sig_id"]

def test_integrity_selfcheck_passes_on_library():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    ok, lines = signature_lib.integrity_selfcheck(d)
    assert ok, lines

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
    fixture = signature_lib.load_fixture_instances()
    sig0 = d["signatures"][0]["sig_id"]
    inst = next((i for i in fixture.get(sig0, []) if i.get("confirmed")), None)
    assert inst is not None, "fixture 缺 confirmed 实例"
    with tempfile.TemporaryDirectory() as tmp:
        # 造一个仓库: 实例文件含匹配模式
        f = os.path.join(tmp, inst["file"])
        os.makedirs(os.path.dirname(f), exist_ok=True)
        lines = ["x"] * inst["line"]
        lines[inst["line"] - 1] = "this.buf.extend_from_slice(&chunk[..]);"
        open(f, "w").write("\n".join(lines))
        results, rate, testable = signature_lib.smoke_test(d, [tmp])
        assert results[sig0]["hit"] is True

def test_smoke_skip_when_repo_missing():
    d = json.load(open(signature_lib.DEFAULT_PATH))
    results, rate, testable = signature_lib.smoke_test(d, ["/nonexistent-repo-xyz"])
    assert all(r.get("skipped") for k, r in results.items() if k != "__integrity__")
    assert rate == 0.0
    # v3.2.2: 非 fixture 仓库 → 完整性自检结果存在且通过
    integ = results.get("__integrity__")
    assert integ is not None and integ["hit"] is True
