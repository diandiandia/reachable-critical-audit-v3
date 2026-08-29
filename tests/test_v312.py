#!/usr/bin/env python3
"""SWR-V3.12: 状态机分析能力补强测试 (14 用例)。

覆盖: STATE 账本族归属与缺口扫描、严重度映射 841/696/670、4 条 CK-STATE-*
绑定契约 (cwe 锚定/关键词绑定/词边界信号门控/裸词零误绑)、
PREC-STATE-GATE-REENTRY 双路径触达与去项目化、TOOLING_VERSION 3.12 与
SKILL.md 增量段、verify 导出清单注入。"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import checklist_binder as cb
import precedent_library as pl
import signature_lib
import workflow_export as we

_STATE_CKS = {"CK-STATE-TRANSITION", "CK-STATE-CONFUSION",
              "CK-MULTISTEP-INVARIANT", "CK-FRAME-GATE-REENTRY"}


def _ids(res):
    return [r[0] for r in res]


def _state_cks(bound):
    return [i for i in _ids(bound) if i in _STATE_CKS]


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


# ---- SWR-V3.12-001: STATE 账本族 ----

def test_ledger_state_family_and_rows(tmp_path):
    ledger = json.load(open(os.path.join(ROOT, "resources",
                                         "issue_coverage_matrix.json")))
    assert ledger["families"]["STATE"]["cwe"] == [841, 696, 670]
    state_rows = [r for r in ledger["rows"] if r["family"] == "STATE"]
    assert state_rows and state_rows[0]["langs"] == {}
    # 数据驱动归属: 841 聚合进 STATE 而非 OTHER
    counts = bv._aggregate_counts(
        {"candidates": [_cand("C-1", cwe=["CWE-841"])], "r4_findings": []},
        str(tmp_path))
    assert ("STATE", "go") in counts and counts[("STATE", "go")] == 1
    assert ("OTHER", "go") not in counts


def test_ledger_gap_scan_shows_state(tmp_path, capsys):
    rc = bv.stage_coverage_ledger(str(tmp_path), write=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert '"status": "LEDGER_GAPS"' in out
    assert "STATE x " in out  # STATE 空行 → 全 16 语言缺口格可见


# ---- SWR-V3.12-002: 严重度映射 ----

def test_severity_state_cwes():
    assert bv.severity_for({"cwe": ["CWE-841"]}) == ("high", "cwe:CWE-841")
    assert bv.severity_for({"cwe": ["CWE-696"]}) == ("high", "cwe:CWE-696")
    assert bv.severity_for({"cwe": ["CWE-670"]}) == ("medium", "cwe:CWE-670")
    # override 优先级与 claim_type 回退不变
    assert bv.severity_for({"cwe": ["CWE-841"], "severity_override": "critical",
                            "severity_override_reason": "r"})[0] == "critical"
    assert bv.severity_for({"cwe": [], "claim_type": "protocol_dos"}) == \
        ("high", "claim_type(protocol_dos)")


# ---- SWR-V3.12-003: 清单绑定契约 ----

def test_ck_state_bind_via_cwe():
    bound = _state_cks(cb.bind({"summary": "协议处理", "cwe": ["CWE-841"],
                                "lang": "go"}))
    assert bound == ["CK-STATE-TRANSITION"]  # 唯一 841 锚定条目, 不与 CONFUSION 共绑


def test_ck_state_co_binding_bizlogic():
    bound = _ids(cb.bind({"summary": "状态机非法状态转移静默通过", "cwe": [],
                          "lang": "go"}))
    assert "CK-STATE-TRANSITION" in bound and "CK-BIZ-LOGIC" in bound  # 共绑合法


def test_ck_multistep_binds_cwe_and_keyword():
    assert _state_cks(cb.bind({"summary": "解析", "cwe": ["CWE-696"],
                               "lang": "go"})) == ["CK-MULTISTEP-INVARIANT"]
    assert "CK-MULTISTEP-INVARIANT" in _ids(cb.bind(
        {"summary": "多步流程跳步重放乱序", "cwe": [], "lang": "go"}))


def test_ck_confusion_binds_keyword_only():
    assert "CK-STATE-CONFUSION" in _ids(cb.bind(
        {"summary": "对象重入双解释", "cwe": [], "lang": "go"}))
    # CWE-841 无关键词不绑 CONFUSION (无 CWE 锚定——跨族语义)
    assert "CK-STATE-CONFUSION" not in _ids(cb.bind(
        {"summary": "协议处理", "cwe": ["CWE-841"], "lang": "go"}))


def test_ck_frame_gate_signal_gating_positive():
    assert "CK-FRAME-GATE-REENTRY" in _ids(cb.bind(
        {"summary": "状态机逐帧处理 帧门禁 一次性检查", "cwe": [], "lang": "go"}))


def test_ck_frame_gate_signal_gating_negative():
    # 关键词命中 (状态机/重入) 但无 frame/chunk/逐帧类信号 → 信号门控拦截
    assert "CK-FRAME-GATE-REENTRY" not in _ids(cb.bind(
        {"summary": "状态机重入 模块化实现", "cwe": [], "lang": "go"}))


def test_no_bare_word_false_positive():
    # keywords 无裸 ASCII 单词 (state/frame 会子串误配 statement/framework)
    assert _state_cks(cb.bind({"summary": "statement 里 framework 初始化",
                               "cwe": [], "lang": "go"})) == []
    assert _state_cks(cb.bind({"summary": "state 变量重置", "cwe": [],
                               "lang": "go"})) == []


def test_state_checklists_deproject():
    d = json.load(open(os.path.join(ROOT, "resources", "checklist_library.json")))
    items = [c for c in d["checklists"] if c["id"] in _STATE_CKS]
    assert len(items) == 4
    for it in items:
        blob = json.dumps(it, ensure_ascii=False)
        for tok in signature_lib.DEPROJECT_BLACKLIST:
            assert tok not in blob, f"清单含项目 token: {tok}"
        assert "/root/" not in blob
        assert "applications" not in it  # v3.4 遗留死字段不复刻 (BIAS_EVAL O-2)


# ---- SWR-V3.12-004: 先例触达 ----

def test_precedent_state_reachable():
    # CWE 元组路径
    assert any(p["id"] == "PREC-STATE-GATE-REENTRY"
               for p in pl.match({"summary": "解析", "cwe": ["CWE-841"],
                                  "lang": "go"}))
    # 关键词路径 (ASCII 小写形态)
    assert any(p["id"] == "PREC-STATE-GATE-REENTRY"
               for p in pl.match({"summary": "state machine 重入",
                                  "cwe": ["CWE-000"], "lang": "go"}))
    # 自证伪提示可达
    hints = pl.self_refutation_hints({"summary": "状态机门禁", "cwe": ["CWE-841"],
                                      "lang": "go"})
    assert any("PREC-STATE-GATE-REENTRY" in h for h in hints)
    # 5 字段去项目化 (机制形态)
    prec = [p for p in pl.match({"summary": "解析", "cwe": ["CWE-841"],
                                 "lang": "go"})
            if p["id"] == "PREC-STATE-GATE-REENTRY"][0]
    for field in ("name", "criterion", "counterexample",
                  "applicability_scope", "applications"):
        blob = json.dumps(prec.get(field, []), ensure_ascii=False)
        for tok in signature_lib.DEPROJECT_BLACKLIST:
            assert tok not in blob, f"先例 {field} 含项目 token: {tok}"
        assert "/root/" not in blob


# ---- SWR-V3.12-006: 版本链 ----

def test_tooling_version_and_skillmd_counts():
    assert we.TOOLING_VERSION == "3.13"  # v3.13 版本链前进 (SWR-V3.13-006)
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "## 🆕 v3.12 增量" in skill
    assert "38 条检查清单" in skill and "17 条裁决先例" in skill
    # 严重度表含 STATE 行
    assert "STATE 状态机序对/协议类（841/696）" in skill
    assert "STATE 状态机控制流（670）" in skill


def test_verify_prompt_injects_state_checklist():
    tmp = _mk_project([_cand("S-1", summary="状态机非法状态转移",
                             cwe=["CWE-841"])])
    r = we.export_script(tmp, mode="verify", batch_size=4)
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    assert "CK-STATE-TRANSITION" in r["payload"][0]["prompt"]
    assert "家族检查清单" in r["payload"][0]["prompt"]
