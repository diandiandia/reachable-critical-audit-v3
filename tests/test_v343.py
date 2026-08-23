"""v3.4.3 缺陷闭环回归 (SWR-V3.4.3-080..089)。"""
import json, os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import batch_verify as bv
import evidence_ledger as el
import workflow_export as we
import surface_mapper as sm
import checklist_binder as cb
import precedent_library as pl

WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mk_proj():
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": [], "target_kind": "library"},
              open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    return tmp


def test_r4_collect_adaptive_drift_forms():
    """SWR-080: 四类漂移形态自适应 + canonical 零变化。"""
    proj = _mk_proj()
    raw = {
        "hypotheses": {
            "H1": {"verdict": "confirmed",
                   "tracked_surfaces": ["SURF-DATA-001"]},
        },
        "findings": [
            {"id": "F1", "hypothesis": "H1",
             "title": "payload 上限失效",
             "cwe": "CWE-789", "severity": "low", "claim_type": "unbounded",
             "evidence": ["a:1", "b:2"],
             "r3_link": {"candidate": "CAND-004", "note": "共享根因"},
             "recommendation": "拒绝 0 值"}
        ],
    }
    json.dump(raw, open(os.path.join(proj, ".audit_results", "_r4.json"), "w"),
              ensure_ascii=False)
    bv.stage_r4_collect(proj, os.path.join(proj, ".audit_results", "_r4.json"))
    f = bv.load_queue(proj)["r4_findings"][0]
    fi = f["findings"][0]
    assert f["hypothesis_id"] == "H-1"
    assert fi["severity"] == "Low"
    assert "a:1" in fi["evidence"] and "b:2" in fi["evidence"]
    assert fi["r3_link"].startswith("CAND-004")
    assert fi["fix"] == "拒绝 0 值"
    assert fi["tracked_surfaces"] == ["SURF-DATA-001"]  # hypothesis 级下放
    assert "schema_normalized_by" not in f  # v3.5: 归一化标记字段已删
    # canonical 输入零变化
    proj2 = _mk_proj()
    canon = {"hypotheses": [{"hypothesis_id": "H2", "verdict": "reviewed_clean",
                             "findings": []}]}
    json.dump(canon, open(os.path.join(proj2, ".audit_results", "_r4c.json"), "w"),
              ensure_ascii=False)
    bv.stage_r4_collect(proj2, os.path.join(proj2, ".audit_results", "_r4c.json"))
    f2 = bv.load_queue(proj2)["r4_findings"][0]
    assert f2["hypothesis_id"] == "H-2"
    assert "schema_normalized_by" not in f2


def test_surface_prefix_map():
    """SWR-081: SURF-DATA-* → SURF-DAT-* 前缀映射; 真未知保留告警。"""
    proj = _mk_proj()
    json.dump({"schema_version": "3.0", "surfaces": [
        {"id": "SURF-DAT-003", "name": "x", "type": "data", "entry_points": []}]},
        open(os.path.join(proj, ".audit_results", "input_surface.json"), "w"),
        ensure_ascii=False)
    raw = {"hypotheses": [{"hypothesis_id": "H2", "verdict": "reviewed_clean",
                           "findings": [{"title": "t", "severity": "Low",
                                         "tracked_surfaces": ["SURF-DATA-003"]}]}]}
    json.dump(raw, open(os.path.join(proj, ".audit_results", "_r4m.json"), "w"),
              ensure_ascii=False)
    bv.stage_r4_collect(proj, os.path.join(proj, ".audit_results", "_r4m.json"))
    fi = bv.load_queue(proj)["r4_findings"][0]["findings"][0]
    assert fi["tracked_surfaces"] == ["SURF-DAT-003"]
    assert fi["mapped_surface_ids"] == {"SURF-DATA-003": "SURF-DAT-003"}


def test_resurrect_cli_and_r35n_collect():
    """SWR-082: --mode resurrect 导出 + r35n-collect 落盘候选级 dict + 幂等。"""
    proj = _mk_proj()
    q = bv.load_queue(proj)
    q["candidates"] = [{"id": "CAND-001", "status": "VERIFIED",
                        "verdict": "UNREACHABLE", "source_file": "f.c",
                        "source_line": 1, "sink_type": "CWE-400"}]
    bv.save_queue(proj, q)
    assert bv.stage_workflow_script(proj, mode="resurrect") == 0
    payload = json.load(open(os.path.join(
        proj, ".audit_results", "workflow_resurrect.js"), "w")) if False else None
    # r35n-collect 幂等落盘
    jd = tempfile.mkdtemp()
    with open(os.path.join(jd, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result", "result": {
            "id": "CAND-001", "revived": False, "reason": "维持 UNREACHABLE"}}) + "\n")
    assert bv.stage_r35n_collect(proj, jd, expect_ids=["CAND-001"]) == 0
    c = bv.load_queue(proj)["candidates"][0]
    assert c["resurrection_review"] == {"revived": False, "outcome": "维持 UNREACHABLE"}
    assert bv.stage_r35n_collect(proj, jd, expect_ids=["CAND-001"]) == 0  # 幂等


def test_grade_self_reported_on_collect():
    """SWR-083: collect 机械重算 + grade_self_reported 追溯。"""
    proj = _mk_proj()
    q = bv.load_queue(proj)
    q["candidates"] = [{"id": "CAND-001", "status": "PENDING",
                        "source_file": "f.c", "source_line": 1,
                        "sink_type": "CWE-400"}]
    bv.save_queue(proj, q)
    verdicts = {"CAND-001": {
        "verdict": "REACHABLE", "reachability_type": "DIRECT",
        "call_chain": ["f.c:1:a", "f.c:2:b", "f.c:3:c"], "call_chain_depth": 2,
        "evidence": "链真实", "evidence_grade": "empirically_confirmed",
        "edge_evidence": [{"edge": "a->b", "proof": "f.c:2"},
                          {"edge": "b->c", "proof": "f.c:3"}],
        "claim_type": "unbounded", "blocking_point": "N/A"}}
    bv.stage_collect(proj, 0, verdicts)
    c = bv.load_queue(proj)["candidates"][0]
    assert c["grade_self_reported"] == "empirically_confirmed"
    assert c["evidence_grade"] == "edge_proven"  # 无 empirical dict → 机械降级
    assert c["grade_recomputed_by"] == "collect-mechanical-recompute"


def test_gate_structural_empirical():
    """SWR-084: 含「实测」+数字的 Medium finding 不再误报; 空 empirical 仍拦截。"""
    proj = _mk_proj()
    q = bv.load_queue(proj)
    fi_ok = {"title": "x", "severity": "Medium", "claim_type": "other",
             "empirical_result": "本机 g++ 实测: GET /admin/ -> 200, "
                                 "route_calls=0, 三次复跑"}
    q["r4_findings"] = [{"hypothesis_id": "H-5", "verdict": "confirmed",
                         "findings": [fi_ok]}]
    bv.save_queue(proj, q)
    ok, v = el.assert_ledger(bv.load_queue(proj), dispatched=[],
                             surface_data={"total": 0, "tracked": 0})
    assert not any("empirical" in str(x.get("gate")) for x in v
                   if isinstance(x, dict))
    # 对照: 空 empirical_result
    q = bv.load_queue(proj)
    q["r4_findings"][0]["findings"][0]["empirical_result"] = None
    bv.save_queue(proj, q)
    ok2, v2 = el.assert_ledger(bv.load_queue(proj), dispatched=[],
                               surface_data={"total": 0, "tracked": 0})
    assert any(x.get("gate") == "empirical_required_r4" for x in v2
               if isinstance(x, dict))


def test_claim_leak_schema():
    """SWR-085: leak 通过 schema 校验; 旧值集不受影响。"""
    enum = we.VERDICT_SCHEMA["properties"]["claim_type"]["enum"]
    assert "leak" in enum
    assert all(x in enum for x in ("crash", "oom", "rce", "other", "null"))


def test_boundary_capi():
    """SWR-086: capi 词族通过 validate。"""
    assert "capi" in sm.BOUNDARY_KINDS
    assert sm.canonical_surface_id("SURF-DAT-002") == ("SURF-DATA-002", True)
    assert sm.canonical_surface_id("SURF-DATA-001")[1] is False


def test_checklist_signal_gating():
    """SWR-087: CWE-400 非 WS 候选不绑 CK-WS-MATERIALIZE (兜底通用清单); WS 仍绑。"""
    jwt = {"id": "X", "sink_type": "CWE-400",
           "snippet": "token.indexOf(delimiter) 线性扫描", "lang": "java"}
    bound = cb.bind(jwt)
    assert not any(cid == "CK-WS-MATERIALIZE" for cid, _ in bound)
    assert any(cid == "CK-GENERIC-RESOURCE" for cid, _ in bound)
    ws = {"id": "Y", "sink_type": "CWE-400",
          "snippet": "websocket frame accumulation in engine", "lang": "c"}
    assert any(cid == "CK-WS-MATERIALIZE" for cid, _ in cb.bind(ws))
    # PREC 信号: 无 WS 文本的候选不再注入 PREC-STREAM-MATERIALIZE
    hints = pl.self_refutation_hints(
        {"id": "W", "sink_type": "CWE-400", "claim_type": "oom",
         "snippet": "JWT verify 物化", "lang": "java"})
    assert not any("PREC-STREAM-MATERIALIZE" in h for h in hints)


def test_truncate_protocol():
    """SWR-088: 关键段保留 + 次要段带标记; 短证据原样。"""
    minor = ("【清单执行记录】CK-WS-MATERIALIZE: N/A 非 WS 场景 " + "x" * 400)
    ev = ("【步骤0 承重前提验证】前提 A 成立。\n【调用链】三层。\n"
          "【实证】53MB token → OOM 349ms。\n" + minor + "\n") * 2
    out = we._truncate_evidence(ev, budget=800)
    assert "承重前提" in out and "实证" in out
    assert "【调用链】" not in out and "清单执行记录】" not in out
    assert "截断" in out
    assert we._truncate_evidence("【实证】abc", budget=800) == "【实证】abc"


def test_export_lang_priority():
    """SWR-089: 候选 lang 字段优先于扩展名推断。"""
    ctx = bv._build_context({"id": "X", "source_file": "httplib.h",
                             "source_line": 1, "lang": "c",
                             "sink_type": "CWE-400"}, "/tmp")
    assert ctx["language"] == "c"
