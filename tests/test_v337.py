"""v3.37 (SWR-V3.37-001/002/003): Caddy 验收复盘三修复守卫。
- taskFile/taskFiles 落盘引用绝对化 (Workflow agent cwd 不可假定项目根)
- CK-SLICE-CAPACITY (切片越界声称容量语义) / CK-MAGNITUDE-OWNERSHIP (量级驱动权)"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_guards
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def _mk_proj(tmp_path, mode):
    import workflow_export as we
    proj = tmp_path / "proj"
    (proj / ".audit_results").mkdir(parents=True, exist_ok=True)
    status = "PENDING" if mode == "verify" else "VERIFIED"
    verdict = "PENDING" if mode == "verify" else "REACHABLE"
    q = {"candidates": [{"id": "CAND-001", "source_file": "a.go", "source_line": 1,
                         "sink_type": "CWE-770", "status": status,
                         "verdict": verdict, "evidence_grade": "edge_proven",
                         "claim_type": "unbounded", "evidence": "e",
                         "call_chain": ["a.go:1"], "cwe": ["CWE-770"]}],
         "r4_findings": [], "target_kind": "application"}
    json.dump(q, open(proj / ".audit_results" / "verify_queue.json", "w"))
    return proj, we.export_script


def _export_and_read(tmp_path, mode):
    """直调 export_script (verify/refutation 分支), 返回落盘 payload。"""
    proj, export_script = _mk_proj(tmp_path, mode)
    result = export_script(str(proj), mode=mode, batch_size=1)
    assert result.get("count", 0) == 1, result
    payload = json.load(open(proj / ".audit_results" / (
        "refutation_payload_slim.json" if mode == "refutation"
        else "verify_payload_slim.json")))
    return proj, payload


def test_t1_taskfiles_absolute(tmp_path):
    """T-1: verify/refutation payload 的 taskFile/taskFiles 为绝对路径。"""
    for mode in ("verify", "refutation"):
        proj, payload = _export_and_read(tmp_path, mode)
        assert payload, mode
        for c in payload:
            if mode == "verify":
                tf = c["taskFile"]
                assert os.path.isabs(tf), (mode, tf)
                assert tf.startswith(str(proj)), (mode, tf)
                assert os.path.exists(tf), (mode, tf)
            else:
                assert len(c["taskFiles"]) == 2, mode
                for tf in c["taskFiles"]:
                    assert os.path.isabs(tf), (mode, tf)
                    assert tf.startswith(str(proj)), (mode, tf)
                    assert os.path.exists(tf), (mode, tf)


def test_t1b_resurrect_taskfile_absolute(tmp_path):
    """T-1b: resurrect 形态 taskFile 绝对路径 (第三处)。"""
    import workflow_export as we
    proj = tmp_path / "proj2"
    (proj / ".audit_results").mkdir(parents=True, exist_ok=True)
    q = {"candidates": [{"id": "CAND-001", "source_file": "a.go", "source_line": 1,
                         "sink_type": "CWE-248", "status": "VERIFIED",
                         "verdict": "UNREACHABLE", "evidence_grade": "static_only",
                         "claim_type": "panic", "evidence": "e"}],
         "r4_findings": [], "target_kind": "application"}
    json.dump(q, open(proj / ".audit_results" / "verify_queue.json", "w"))
    result = we.export_script_resurrect(str(proj), batch_size=8)
    assert result.get("count", 0) == 1, result
    payload = json.load(open(proj / ".audit_results" / "resurrect_payload_slim.json"))
    for c in payload:
        assert os.path.isabs(c["taskFile"]), c["taskFile"]
        assert os.path.exists(c["taskFile"]), c["taskFile"]


def test_t2_slice_capacity_checklist():
    """T-2: CK-SLICE-CAPACITY 条目存在 + family=memory-safety + 去项目化。"""
    d = json.load(open(os.path.join(ROOT, "assets", "resources",
                                    "checklist_library.json")))
    e = next(c for c in d["checklists"] if c["id"] == "CK-SLICE-CAPACITY")
    assert e["family"] == "memory-safety"
    assert e["applies_to"] == ["verifier", "refuter"]
    assert len(e["steps"]) == 4
    blob = json.dumps(e, ensure_ascii=False)
    assert "cap" in blob and "len" in blob  # 容量语义判据在位
    for tok in ("caddy", "CAND-011", "fileloader"):
        assert tok not in json.dumps({k: v for k, v in e.items()
                                      if k != "source_lessons"}).lower(), tok


def test_t3_magnitude_ownership_checklist():
    """T-3: CK-MAGNITUDE-OWNERSHIP 条目存在 + family=empirical + 去项目化。"""
    d = json.load(open(os.path.join(ROOT, "assets", "resources",
                                    "checklist_library.json")))
    e = next(c for c in d["checklists"] if c["id"] == "CK-MAGNITUDE-OWNERSHIP")
    assert e["family"] == "empirical"
    assert e["applies_to"] == ["verifier", "refuter"]
    assert len(e["steps"]) == 4
    body = json.dumps({k: v for k, v in e.items() if k != "source_lessons"},
                      ensure_ascii=False).lower()
    for tok in ("caddy", "cand-002", "templates"):
        assert tok not in body, tok
    assert "加固缺口" in body or "NEEDS_REVIEW" in body


def test_t4_checklist_count_and_legacy_regression():
    """T-4: 清单总数 47 + 既有条目零改动 (抽样 45 条 id 稳定)。"""
    d = json.load(open(os.path.join(ROOT, "assets", "resources",
                                    "checklist_library.json")))
    assert len(d["checklists"]) == asset_guards.CHECKLISTS
    ids = [c["id"] for c in d["checklists"]]
    assert len(ids) == len(set(ids)), "清单 id 重复"
    assert "CK-UNBOUNDED-HOPS" in ids and "CK-DYNAMIC-DEFENSE" in ids
