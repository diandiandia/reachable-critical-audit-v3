import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import ast_scanner as asc

PY = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

def test_ast_path_map_5_forms():
    cases = [
        ("lib/spec/foo.rb", True),          # ruby spec/
        ("tst/Pester.Tests.ps1", True),     # powershell tst/ + *.Tests.*
        ("src/foo_tests.rs", True),         # rust *_tests.rs
        ("src/foo.spec.ts", True),          # ts *.spec.*
        ("Src/Newtonsoft.Json.Tests/x.cs", True),  # csharp .Tests/
        ("lib/sinatra/base.rb", False),     # 正常源码不拦
        ("src/main.rs", False),
    ]
    for path, expected in cases:
        got = asc.ASTCoarseScanner._is_ignored_path(path)
        assert got == expected, f"{path}: got {got}, want {expected}"

def test_ast_merge_semantics(tmp_path=None):
    if tmp_path is None:
        tmp = tempfile.mkdtemp()
    else:
        tmp = str(tmp_path)
    qp = os.path.join(tmp, "verify_queue.json")
    old = {"schema_version": "2.0", "candidates": [
        {"id": "R05-abc", "file_path": "b.c", "line_number": 2, "cwe_id": "CWE-22",
         "category": "X", "status": "PENDING"}]}
    json.dump(old, open(qp, "w"))
    new = [{"file_path": "a.c", "line_number": 1, "cwe_id": "CWE-78", "category": "Y"},
           {"file_path": "b.c", "line_number": 2, "cwe_id": "CWE-22", "category": "X"}]
    merged, preserved = asc._merge_queue(qp, new)
    assert preserved == 1                       # R05-abc 保留
    assert len(merged) == 2                     # 新 a.c 追加, b.c 同 key 去重
    ids = [c.get("id") for c in merged if c.get("id")]
    assert "R05-abc" in ids

def test_r05_cross_tags_awstats():
    # SWR-V3-060 验收: AWStats 已知结论可复现 (0d4d4c05 修复不在 7.8 tag)
    if not os.path.isdir("/root/AWStats/.git"):
        print("skip: /root/AWStats 不可用")
        return
    r = subprocess.run([PY, os.path.join(TOOLS, "r05_diff_archaeology.py"), "/root/AWStats",
                        "--grep-tier", "security", "--cross-tags", "AWSTATS_7_6,AWSTATS_7_7,AWSTATS_7_8"],
                       capture_output=True, text=True, timeout=300)
    d = json.loads(r.stdout[r.stdout.find("{"):])
    assert d["grep_tier"] == "security"
    matrix = d["cross_tags"]["matrix"]
    row = next(x for x in matrix if x["sha"].startswith("0d4d4c05"))
    assert row["in_AWSTATS_7_8"] is False     # 发行版缺口复现
    # 默认落盘 (SWR-V3-063)
    assert os.path.exists("/root/AWStats/.audit_results/r05_diff_archaeology.json")

def test_r05_no_git():
    tmp = tempfile.mkdtemp()
    r = subprocess.run([PY, os.path.join(TOOLS, "r05_diff_archaeology.py"), tmp],
                       capture_output=True, text=True)
    assert '"status": "NO_GIT"' in r.stdout
