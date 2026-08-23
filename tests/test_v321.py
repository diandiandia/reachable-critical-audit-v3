# -*- coding: utf-8 -*-
"""v3.2.1 测试 (SWR-V3.2.1-080/081): target_kind / verifier 三段 / 门禁⑧ /
r4_feedback / component_role / shipped-config / 新清单新先例绑定。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import evidence_ledger as el
import r2_guard
import surface_mapper
import workflow_export
from target_kind import determine_target_kind
import checklist_binder
import precedent_library

FIXTURE = "/root/mixed-fixture"
LERSOSA = "/root/Lersosa"


def _make_go_library(tmp_path):
    """构造 Go 库形态项目 (go.mod module 声明 + 无 main 的 .go 文件)。

    mixed-fixture 曾作为库型 fixture (v3.2 验收), 但其目录依赖外部环境;
    tmp_path 构造等价的"库形态"信号组合: 有源码 + go.mod module + 无监听。
    """
    (tmp_path / "go.mod").write_text("module example.com/fixlib\n\ngo 1.21\n")
    (tmp_path / "fixlib.go").write_text("package fixlib\n\nfunc Do() {}\n")
    return str(tmp_path)


# ---------- M1: target_kind ----------

def test_target_kind_fixture_library(tmp_path):
    r = determine_target_kind(_make_go_library(tmp_path))
    assert r["recommendation"] in ("library", "hybrid")
    assert r["signals"]


def test_target_kind_lersosa_application():
    r = determine_target_kind(LERSOSA)
    assert r["recommendation"] == "application"


def test_target_kind_unknown_defaults_application():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = determine_target_kind(d)
        assert r["recommendation"] == "application"
        assert r["confidence"] == "low"


# ---------- M2: verifier 三段 ----------

def test_build_prompt_has_import_precheck(tmp_path):
    import batch_verify
    cand = {"id": "CAND-X", "type": None}
    ctx = {"file": "f.py", "line": 1, "language": "python", "cwe": "CWE-918",
           "category": "x", "sink": "requests.get(url)", "sources_regex": ""}
    out = tmp_path / ".audit_results"
    out.mkdir()
    (out / "verify_queue.json").write_text(
        json.dumps({"schema_version": "3.0", "target_kind": "application",
                    "candidates": []}))
    # prompt 读取 verify_queue.target_kind (原测试借用 Lersosa 目录, 环境依赖)
    p = batch_verify._build_prompt(cand, ctx, str(tmp_path))
    assert "步骤 0.5" in p and "模块可导入性预检" in p
    assert "broken_edge" in p
    assert "目标类型存在性规则" in p and "shipped 配置" in p


def test_build_prompt_write_read_family_enumeration(tmp_path):
    import batch_verify
    cand = {"id": "CAND-X", "type": None, "summary": "写入配置 → 出站重定向",
            "claim_type": "write-outbound"}
    ctx = {"file": "f.go", "line": 1, "language": "go", "cwe": "CWE-918",
           "category": "x", "sink": "minio.New(...)", "sources_regex": ""}
    assert batch_verify._is_write_read_family(cand)
    out = tmp_path / ".audit_results"
    out.mkdir()
    (out / "verify_queue.json").write_text(
        json.dumps({"schema_version": "3.0", "target_kind": "application",
                    "candidates": []}))
    p = batch_verify._build_prompt(cand, ctx, str(tmp_path))
    assert "步骤 5.5" in p and "缓存层三查" in p


def test_load_target_kind_fallback(tmp_path):
    import batch_verify
    out = tmp_path / ".audit_results"
    out.mkdir()
    (out / "target_kind.json").write_text(
        json.dumps({"recommendation": "library"}))
    assert batch_verify._load_target_kind(str(tmp_path)) == "library"
    # 队列优先
    (out / "verify_queue.json").write_text(json.dumps({"target_kind": "application"}))
    assert batch_verify._load_target_kind(str(tmp_path)) == "application"


# ---------- M5: 门禁⑧ + r4_feedback ----------

def _base_r4():
    """H1-H7 全 VERIFIED 的基础 r4_findings (门禁④依赖)。"""
    out = []
    for i in range(1, 8):
        out.append({"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                    "verdict": "reviewed_clean", "findings": []})
    return out


def test_gate8_missing_target_kind():
    q = {"candidates": [], "r4_findings": _base_r4()}
    ok, v = el.assert_ledger(q)
    assert not ok
    assert any(x["gate"] == "target_kind_required" for x in v)


def test_gate8_legacy_exemption():
    q = {"candidates": [], "r4_findings": _base_r4()}
    ok, v = el.assert_ledger(q, require_target_kind=False)
    assert ok, v


def test_gate8_present_passes():
    q = {"candidates": [], "r4_findings": _base_r4(),
         "target_kind": "application"}
    ok, v = el.assert_ledger(q)
    assert ok, v


def test_r4_feedback_conflict():
    r4 = _base_r4()
    r4[6] = {"hypothesis_id": "H-7", "status": "VERIFIED", "verdict": "confirmed",
             "findings": [{"title": "默认值盘点",
                           "evidence": "tls_enable=true (shipped config)"}]}
    q = {
        "target_kind": "application",
        "candidates": [{
            "id": "CAND-X", "verdict": "REACHABLE", "status": "VERIFIED",
            "evidence_grade": "edge_proven",
            "evidence": "tls_enable 零值 false 默认明文可达",
            "gate_note": "", "trust_boundary": "gated", "summary": "",
            "call_chain": []}],
        "r4_findings": r4,
    }
    conflicts = el.r4_feedback(q)
    assert conflicts and conflicts[0]["candidate"] == "CAND-X"
    assert conflicts[0]["key"] == "tls_enable"


def test_r4_feedback_no_conflict_on_match():
    r4 = _base_r4()
    r4[6] = {"hypothesis_id": "H-7", "status": "VERIFIED", "verdict": "confirmed",
             "findings": [{"title": "默认值盘点",
                           "evidence": "tls_enable=false (shipped config)"}]}
    q = {
        "target_kind": "application",
        "candidates": [{
            "id": "CAND-Y", "verdict": "REACHABLE", "status": "VERIFIED",
            "evidence_grade": "edge_proven",
            "evidence": "tls_enable 零值 false 默认明文可达",
            "gate_note": "", "trust_boundary": "gated", "summary": "",
            "call_chain": []}],
        "r4_findings": r4,
    }
    assert el.r4_feedback(q) == []


# ---------- M4: 新清单/新先例绑定 ----------

def test_new_checklists_bind():
    lib = checklist_binder.load_library()
    ids = {c["id"] for c in lib["checklists"]}
    assert {"CK-IMPORT-REGISTRATION", "CK-CACHE-GATE-LAYER"} <= ids
    import_cand = {"summary": "import 导入 component_scan 路由注册",
                   "cwe": "CWE-306", "lang": ".py"}
    bound = [cid for cid, _ in checklist_binder.bind(import_cand, lib)]
    assert "CK-IMPORT-REGISTRATION" in bound
    cache_cand = {"summary": "redis 缓存 default_config 写入",
                  "cwe": "CWE-918", "lang": ".go"}
    bound2 = [cid for cid, _ in checklist_binder.bind(cache_cand, lib)]
    assert "CK-CACHE-GATE-LAYER" in bound2


def test_new_precedents_exist():
    lib = precedent_library.load()
    ids = {p["id"] for p in lib["precedents"]}
    assert {"PREC-TARGET-KIND-001", "PREC-IMPORT-BREAK-001"} <= ids


# ---------- M7: component_role ----------

def test_component_role_derivation():
    assert surface_mapper._component_role("frontend") == "client-only"
    assert surface_mapper._component_role("scripts") == "build-config"
    assert surface_mapper._component_role("headers") == "build-config"
    assert surface_mapper._component_role("core") == "server-side"
    assert surface_mapper._component_role("bindings") == "server-side"


def test_lersosa_inventory_has_role(tmp_path):
    # 原测试依赖 /root/Lersosa 目录 (外部项目), 改为 tmp_path 构造:
    # frontend/ 目录 → 前端组件 client-only 判定 (与 _component_role 同启发式)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "app.ts").write_text("export const a = 1;\n")
    inv = surface_mapper.language_inventory(str(tmp_path))
    ts = [x for x in inv if x["lang"] == ".ts"]
    assert ts and ts[0]["component_role"] == "client-only"


# ---------- M6: r2_guard shipped-config 引用 ----------

def test_r2_guard_shipped_config_hint(tmp_path):
    out = tmp_path / ".audit_results"
    out.mkdir()
    (out / "shipped_config.json").write_text("{}")
    hyps = [{"hypothesis_id": "H-1", "surface_ids": ["SURF-X"],
             "gate": "默认开启可默认可达"}]
    surface = {"surfaces": [{"id": "SURF-X"}]}
    ok, issues = r2_guard.validate_hypotheses(
        {"hypotheses": hyps}, surface, project_root=str(tmp_path))
    assert ok
    assert any("shipped_config.json" in i["msg"] for i in issues)


# ---------- M3: shipped-config workflow 导出 ----------

def test_export_script_shipped_config(tmp_path):
    r = workflow_export.export_script_shipped_config(
        str(tmp_path), [{"name": "resource", "lang": "go", "dirs": "configs"}])
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    js = open(os.path.join(str(tmp_path), ".audit_results",
                           "workflow_shipped_config.js")).read()
    errs = workflow_export.lint_script(js)
    assert not errs, errs


# ---------- SWR-V3.4.6-002: R2 filter 产出 surface_ids 保真 ----------
def test_filter_result_surface_ids_fidelity():
    """v3.4.6 (SWR-V3.4.6-002): 落盘保真——bc/drop 缺 surface_ids 时从
    hypotheses.json 按 id 反查补齐 + restored_from_hypotheses 标记。
    quic-go 实录: bc/drop 只存 id → 门禁⑦ tracked 覆盖虚低 41→31 假缺口。"""
    hyps = {"hypotheses": [
        {"id": "HYP-001", "surface_ids": ["SURF-DATA-001"]},
        {"id": "HYP-002", "surface_ids": ["SURF-DATA-002", "SURF-PROC-003"]}]}
    data = {"keep": [{"id": "HYP-001", "surface_ids": ["SURF-DATA-001"]}],
            "drop": [{"id": "HYP-002", "reason": "defense"}],
            "boundary_confirmations": [{"id": "HYP-001", "confirmed_defense": "x"}]}
    out, restored = r2_guard.restore_surface_ids(data, hyps)
    assert out["drop"][0]["surface_ids"] == ["SURF-DATA-002", "SURF-PROC-003"]
    assert out["drop"][0]["restored_from_hypotheses"] is True
    assert set(restored) == {"HYP-002", "HYP-001"}
    # bc 条目同样修复 (同 id 反查)
    assert out["boundary_confirmations"][0]["surface_ids"] == ["SURF-DATA-001"]
    assert out["boundary_confirmations"][0]["restored_from_hypotheses"] is True
    # keep 已有 surface_ids → 不动, 无 restored 标记
    assert "restored_from_hypotheses" not in out["keep"][0]
    # 无反查来源 (hypotheses 缺失/未知 id) → 保持缺字段 (兼容旧产出, 不拒收)
    out2, restored2 = r2_guard.restore_surface_ids(
        {"boundary_confirmations": [{"id": "HYP-999", "confirmed_defense": "x"}]}, {})
    assert out2["boundary_confirmations"][0].get("surface_ids") is None
    assert restored2 == []
