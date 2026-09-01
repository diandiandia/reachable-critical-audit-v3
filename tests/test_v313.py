#!/usr/bin/env python3
"""SWR-V3.13: 错误路径处理族 + 数值语义族 + 账本锚点一致性修复测试 (14 用例)。

覆盖: NUMERIC/ERROR-HANDLING 账本族与锚定修正 (436/444/1333 归族)、严重度
映射 9 码、4 条 CK 绑定契约 (cwe/关键词双路径 + 限定形态负例)、去项目化、
TOOLING_VERSION 3.13 与 SKILL.md 增量段、verify 导出清单注入。"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import checklist_binder as cb
import signature_lib
import workflow_export as we

_V313_CKS = {"CK-NUMERIC-TRUNCATION", "CK-NUMERIC-SEMANTICS",
             "CK-ERROR-BRANCH", "CK-ERROR-CLEANUP"}


def _ids(res):
    return [r[0] for r in res]


def _v313(res):
    return [i for i in _ids(res) if i in _V313_CKS]


def _mk_project(cands):
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    bv.save_queue(tmp, {"schema_version": "2.0", "candidates": cands})
    return tmp


def _cand(cid, summary="", cwe=None, claim="other"):
    c = {"id": cid, "source_file": f"src/{cid}.go", "source_line": 7,
         "language": "go", "sink_type": (cwe[0] if cwe else "CWE-000"),
         "summary": summary, "claim_type": claim, "status": "PENDING"}
    if cwe:
        c["cwe"] = cwe
    return c


# ---- SWR-V3.13-001: 账本族与锚定修正 ----

def test_ledger_new_families_and_rows():
    ledger = json.load(open(os.path.join(ROOT, "resources",
                                         "issue_coverage_matrix.json")))
    assert ledger["families"]["NUMERIC"]["cwe"] == [191, 369, 681, 697]
    assert ledger["families"]["ERROR-HANDLING"]["cwe"] == [457, 665]
    assert 436 in ledger["families"]["WEB"]["cwe"]
    assert 444 in ledger["families"]["WEB"]["cwe"]
    assert 1333 in ledger["families"]["RESOURCE-DOS"]["cwe"]
    assert 190 in ledger["families"]["MEMORY-SAFETY"]["cwe"]  # 不重归
    for fam in ("NUMERIC", "ERROR-HANDLING"):
        rows = [r for r in ledger["rows"] if r["family"] == fam]
        assert rows and rows[0]["langs"] == {}


def test_ledger_reanchor_aggregation(tmp_path):
    counts = bv._aggregate_counts(
        {"candidates": [
            _cand("A", cwe=["CWE-436"]), _cand("B", cwe=["CWE-444"]),
            _cand("C", cwe=["CWE-1333"]), _cand("D", cwe=["CWE-191"]),
            _cand("E", cwe=["CWE-457"])],
         "r4_findings": []}, str(tmp_path))
    assert ("WEB", "go") in counts and counts[("WEB", "go")] == 2
    assert ("RESOURCE-DOS", "go") in counts and counts[("RESOURCE-DOS", "go")] == 1
    assert ("NUMERIC", "go") in counts and counts[("NUMERIC", "go")] == 1
    assert ("ERROR-HANDLING", "go") in counts
    assert ("OTHER", "go") not in counts


def test_ledger_gap_scan_shows_new_families(tmp_path, capsys):
    rc = bv.stage_coverage_ledger(str(tmp_path), write=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "NUMERIC x " in out and "ERROR-HANDLING x " in out


# ---- SWR-V3.13-002: 严重度映射 9 码 ----

def test_severity_numeric_cwes():
    assert bv.severity_for({"cwe": ["CWE-191"]}) == ("critical", "cwe:CWE-191")
    assert bv.severity_for({"cwe": ["CWE-369"]}) == ("high", "cwe:CWE-369")
    assert bv.severity_for({"cwe": ["CWE-681"]}) == ("medium", "cwe:CWE-681")
    assert bv.severity_for({"cwe": ["CWE-697"]}) == ("medium", "cwe:CWE-697")


def test_severity_error_handling_cwes():
    assert bv.severity_for({"cwe": ["CWE-457"]}) == ("high", "cwe:CWE-457")
    assert bv.severity_for({"cwe": ["CWE-665"]}) == ("medium", "cwe:CWE-665")


def test_severity_reanchor_cwes():
    assert bv.severity_for({"cwe": ["CWE-436"]}) == ("medium", "cwe:CWE-436")
    assert bv.severity_for({"cwe": ["CWE-444"]}) == ("high", "cwe:CWE-444")
    assert bv.severity_for({"cwe": ["CWE-1333"]}) == ("high", "cwe:CWE-1333")
    # 既有锁回归 + override/回退不变
    assert bv.severity_for({"cwe": ["CWE-841"]}) == ("high", "cwe:CWE-841")
    assert bv.severity_for({"cwe": ["CWE-670"]}) == ("medium", "cwe:CWE-670")
    assert bv.severity_for({"cwe": ["CWE-1333"], "severity_override": "critical",
                            "severity_override_reason": "r"})[0] == "critical"
    assert bv.severity_for({"cwe": [], "claim_type": "protocol_dos"}) == \
        ("high", "claim_type(protocol_dos)")


# ---- SWR-V3.13-003/004: 清单绑定契约 ----

def test_ck_numeric_bind_via_cwe():
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-191"],
                          "lang": "go"})) == ["CK-NUMERIC-TRUNCATION"]
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-681"],
                          "lang": "go"})) == ["CK-NUMERIC-TRUNCATION"]
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-369"],
                          "lang": "go"})) == ["CK-NUMERIC-SEMANTICS"]
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-697"],
                          "lang": "go"})) == ["CK-NUMERIC-SEMANTICS"]


def test_ck_numeric_bind_via_keyword():
    assert "CK-NUMERIC-TRUNCATION" in _ids(cb.bind(
        {"summary": "长度截断 回绕", "cwe": [], "lang": "go"}))
    assert "CK-NUMERIC-TRUNCATION" in _ids(cb.bind(
        {"summary": "integer overflow wraparound", "cwe": [], "lang": "go"}))
    assert "CK-NUMERIC-SEMANTICS" in _ids(cb.bind(
        {"summary": "除零 不一致比较", "cwe": [], "lang": "go"}))
    assert "CK-NUMERIC-SEMANTICS" in _ids(cb.bind(
        {"summary": "divide by zero 风险", "cwe": [], "lang": "go"}))


def test_ck_error_branch_keyword_binding():
    for kw in ("错误分支", "失败分支", "条件反转", "异常路径",
               "error path", "failure path"):
        assert "CK-ERROR-BRANCH" in _ids(cb.bind(
            {"summary": f"处理 {kw} 逻辑", "cwe": [], "lang": "go"})), kw
    # 负例: 异常处理 形态 (无新裸 异常 关键词) 不绑新条目
    assert _v313(cb.bind({"summary": "异常处理 catch 分支", "cwe": [],
                          "lang": "go"})) == []
    # CK-SIBLING-LISTENERS 自身经 verdict_context=UNREACHABLE 门控正常绑定
    bound = _ids(cb.bind({"summary": "异常处理 catch 分支", "cwe": [],
                          "lang": "go", "verdict": "UNREACHABLE"}))
    assert "CK-SIBLING-LISTENERS" in bound and not set(bound) & _V313_CKS


def test_ck_error_cleanup_bind():
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-457"],
                          "lang": "go"})) == ["CK-ERROR-CLEANUP"]
    assert _v313(cb.bind({"summary": "解析", "cwe": ["CWE-665"],
                          "lang": "go"})) == ["CK-ERROR-CLEANUP"]
    assert "CK-ERROR-CLEANUP" in _ids(cb.bind(
        {"summary": "未初始化 缓冲释放", "cwe": [], "lang": "go"}))
    assert "CK-ERROR-CLEANUP" in _ids(cb.bind(
        {"summary": "uninitialized 结构体", "cwe": [], "lang": "go"}))


def test_no_bare_word_false_binds():
    # 限定形态负例 (宽词「算术」等共绑合法, 不声称全量零误绑)
    assert _v313(cb.bind({"summary": "error_handler 注册", "cwe": [],
                          "lang": "go"})) == []
    assert _v313(cb.bind({"summary": "cleanup() 调用", "cwe": [],
                          "lang": "go"})) == []
    assert _v313(cb.bind({"summary": "error 处理", "cwe": [],
                          "lang": "go"})) == []
    assert _v313(cb.bind({"summary": "异常 处理逻辑", "cwe": [],
                          "lang": "go"})) == []


# ---- SWR-V3.13-005: 去项目化 ----

def test_new_checklists_deproject():
    d = json.load(open(os.path.join(ROOT, "resources", "checklist_library.json")))
    items = [c for c in d["checklists"] if c["id"] in _V313_CKS]
    assert len(items) == 4
    for it in items:
        blob = json.dumps(it, ensure_ascii=False)
        for tok in signature_lib.DEPROJECT_BLACKLIST:
            assert tok not in blob, f"清单含项目 token: {tok}"
        assert "/root/" not in blob
        assert "applications" not in it  # v3.4 遗留死字段不复刻


# ---- SWR-V3.13-006: 版本链 ----

def test_tooling_version_and_skillmd_counts():
    assert we.TOOLING_VERSION == "3.16"
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "## 🆕 v3.13 增量" in skill
    assert "44 条检查清单" in skill and "18 条裁决先例" in skill
    for token in ("NUMERIC 整数下溢（191", "NUMERIC 除零（369）",
                  "ERROR-HANDLING 未初始化（457）", "WEB 请求走私（444）",
                  "RESOURCE-DOS ReDoS（1333）", "NUMERIC 截断/不一致比较（681/697）",
                  "ERROR-HANDLING 初始化不完整（665）", "WEB 双解析器前提（436）"):
        assert token in skill, token


def test_verify_prompt_injects_new_checklists():
    tmp = _mk_project([_cand("N-1", summary="长度截断回绕",
                             cwe=["CWE-681"]),
                       _cand("E-1", summary="错误分支条件反转",
                             cwe=["CWE-457"])])
    r = we.export_script(tmp, mode="verify", batch_size=4)
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    prompts = [p["prompt"] for p in r["payload"]]
    assert "CK-NUMERIC-TRUNCATION" in prompts[0]
    assert "CK-ERROR-CLEANUP" in prompts[1]
    assert all("家族检查清单" in p for p in prompts)
