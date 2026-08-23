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


def test_v33_new_l2_families_valid():
    """v3.3 (REQ-V3.3-001): 新 4 族 L2 签名 lang 必填 + 去项目化。"""
    sl = signature_lib.load()
    sigs = {s["sig_id"]: s for s in sl["signatures"]}
    for sid in ("SIG-C-ALLOC-001", "SIG-GO-ACCUM-001",
                "SIG-RS-UNSAFE-001", "SIG-JAVA-DESER-001"):
        assert sid in sigs, f"missing {sid}"
        assert sigs[sid]["lang"] in ("c", "go", "rust", "java")
        assert sigs[sid]["tier"] == "L2"
        for w in sigs[sid]["detection_hints"]["grep"]:
            assert "multer" not in w and "lua" not in w.lower()


def test_v33_new_l3_families():
    """v3.3 (REQ-V3.3-002): SIG-STATE-RACE / SIG-CRYPTO-WEAK cwe 完备。"""
    sl = signature_lib.load()
    sigs = {s["sig_id"]: s for s in sl["signatures"]}
    assert set(sigs["SIG-STATE-RACE-001"]["cwe"]) >= {"CWE-362", "CWE-367"}
    assert set(sigs["SIG-CRYPTO-WEAK-001"]["cwe"]) >= {"CWE-327", "CWE-330"}
    assert sigs["SIG-STATE-RACE-001"]["lang"] == "any"


def test_v33_l2_manual_alignment():
    """v3.3 (REQ-V3.3-004): L2 词族语言全部有 harness_manuals/<lang>.md。"""
    missed = signature_lib.l2_manual_alignment(signature_lib.load())
    assert missed == [], missed

# ---- SWR-V3.3.2-023: 先例精度门 ----
def test_prec_precision_gate_host_family_not_injected_for_java_config():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import precedent_library as pl
    # 模拟 hikaricp CAND-001 形态: Java 配置反射候选, 无 Host 头信号, 无 lang_pair
    cand = {"id": "CAND-001", "sink_type": "CWE-470",
            "summary": "PropertyElf Class.forName 任意类实例化", "lang": "java"}
    hints = pl.self_refutation_hints(cand)
    ids = [h.split("]")[0].lstrip("[") for h in hints]
    assert "PREC-HOST-FAMILY-001" not in ids
    assert "PREC-MULTI-LANG-001" not in ids

def test_prec_precision_gate_host_family_injected_for_host_candidate():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import precedent_library as pl
    cand = {"id": "CAND-002", "sink_type": "CWE-601",
            "summary": "请求 Host 头采信拼接密码重置链接", "lang": "python"}
    hints = pl.self_refutation_hints(cand)
    ids = [h.split("]")[0].lstrip("[") for h in hints]
    assert "PREC-HOST-FAMILY-001" in ids

# ---- SWR-V3.4-042: 问题类清单绑定 ----
def test_checklist_crypto_bind():
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import checklist_binder as cb
    r = cb.bind({"id": "C-1", "sink_type": "CWE-327", "summary": "对称加密",
                 "language": "c"})
    ids = [i for i, _ in r]
    assert "CK-CRYPTO-MISUSE" in ids
    # 回归: CWE-770 绑定不含新清单
    r2 = cb.bind({"id": "C-2", "sink_type": "CWE-770", "summary": "累积", "language": "c"})
    ids2 = [i for i, _ in r2]
    assert "CK-CRYPTO-MISUSE" not in ids2
    assert "CK-CHECKPOINT-AFTER-ACCUM" in ids2


# ---------------- v3.5 (B4/P5) 防回退 ----------------

def test_all_signatures_have_confirmed_fixture():
    """v3.5 (B4): 7 新增 fixture 后每签名 ≥1 confirmed 实例——R0 冒烟零 skipped
    兜底 (c/cpp/go 三种账本最重语言曾在 fixtures 零代表)。"""
    import signature_lib
    d = signature_lib.load()
    fixture = signature_lib.load_fixture_instances()
    missing = [s["sig_id"] for s in d["signatures"]
               if not any(x.get("confirmed") for x in fixture.get(s["sig_id"], []))]
    assert missing == [], f"零 confirmed fixture 的签名: {missing}"


def test_selfcheck_flags_template_residue(tmp_path):
    """v3.5 (P5): _scan_runtime_assets 注入违规内容 → 命中——模板/手册项目残留
    回退会被 R0 selfcheck 完整性分支拦截。"""
    import signature_lib
    d = tmp_path / "templates" / "harness"
    d.mkdir(parents=True)
    (d / "ok.py").write_text("import socket\nsock.sendall(b'x')\n")
    assert signature_lib._scan_runtime_assets(base=str(tmp_path)) == []
    (d / "bad_tok.py").write_text("cleanxss = 1  # 项目专属 API\n")
    hits = signature_lib._scan_runtime_assets(base=str(tmp_path))
    assert any(f.endswith("bad_tok.py") and tok == "cleanxss" for f, tok in hits)
    (d / "bad_root.py").write_text("root = '/root/secret'\n")
    hits = signature_lib._scan_runtime_assets(base=str(tmp_path))
    assert any(f.endswith("bad_root.py") and "绝对路径" in tok for f, tok in hits)


def test_selfcheck_flags_resources_root_residue(tmp_path):
    """v3.5.1: _scan_runtime_assets 扩展扫 resources/——数据资产拦 /root/ 绝对路径
    (资源目录的 source_lessons/cve 描述等合法字段含项目名, 黑名单 token 不扫);
    resources 内 /root/ 回退 (如账本 sources 曾存 36 条项目路径) 被 R0 拦截。"""
    import signature_lib
    d = tmp_path / "resources"
    d.mkdir(parents=True)
    (d / "matrix.json").write_text('{"sources": ["/root/actix-web", "/root/Lersosa"]}\n')
    hits = signature_lib._scan_runtime_assets(base=str(tmp_path))
    assert any(f.endswith("matrix.json") and "绝对路径" in tok for f, tok in hits)
    # 同目录合法追溯字段 (项目名无 /root/ 路径) 不触发
    (d / "matrix.json").write_text('{"sources": ["a1b2c3d4e5f6a1b2"]}\n')
    assert signature_lib._scan_runtime_assets(base=str(tmp_path)) == []
