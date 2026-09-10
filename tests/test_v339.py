"""v3.39 (SWR-V3.39-001~004): haproxy 验收复盘四修复守卫。
- normalize ASCII 关键词词边界 (cli 不误配 client)
- seed 双写覆盖 battle 条目 + 缺格自动建
- asset_guards 计数常量集中 (动态一致性)
- severity_override dict 形态归一化"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_guards


def test_t1_normalize_ascii_word_boundary():
    """T-1: wire-client 自由文本不再被 cli 子串误映射; CJK/词内命中照常。"""
    from surface_mapper import normalize_surfaces

    def _tb(text):
        out = normalize_surfaces({"surfaces": [{"id": "S", "type": "network",
            "lang": "c", "entry_points": [], "taint_channels": [],
            "trust_boundary": text, "confidence": "high"}]})
        return out["surfaces"][0]["trust_boundary"]["type"]

    # "cli" 不得子串命中 "client" (haproxy 实录形态) — else 兜底 environment
    assert _tb("wire-client-bytes->parser") == "environment"
    # 词边界内命中照常: 独立 "cli" 词
    assert _tb("cli 参数入口") == "local"
    # 规范枚举 canonical 短路不变
    assert _tb("local") == "local"
    assert _tb("unauthenticated_remote") == "unauthenticated_remote"
    # CJK 子串语义不变
    assert _tb("未认证的外部请求者") == "unauthenticated_remote"
    assert _tb("本地部署者配置") == "local"


def test_t2_seed_battle_doublewrite(tmp_path):
    """T-2: seed battle_verified 条目 → 矩阵格自动双写 + 缺格自动创建。"""
    import language_issue_matrix as lim
    inv_p = os.path.join(ROOT, "assets", "resources", "language_issue_inventory.json")
    mat_p = os.path.join(ROOT, "assets", "resources", "language_issue_matrix.json")
    inv = json.load(open(inv_p))
    mat = json.load(open(mat_p))
    # 临时测试条目 (fake id 不影响现有数据)
    probe = {"lang": "c", "family": "STATE", "title": "v3.39 双写探针条目",
             "cwe": ["CWE-841"], "pattern": "v3.39 双写探针 pattern",
             "sink_hint": "probe sink", "pitfall": "probe pitfall",
             "source": {"tier": "battle_verified", "origin": "v3.39 test", "date": "2026-09-10"}}
    try:
        payload = {"entries": [probe]}
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            fpath = f.name
        r = lim.seed_entries(fpath)
        assert r["added"] == ["INV-c-019"], r
        # 双写核验
        inv2 = json.load(open(inv_p))
        e = next(x for x in inv2["entries"] if x["id"] == "INV-c-019")
        mat2 = json.load(open(mat_p))
        cell = next(c for c in mat2["cells"] if c["lang"] == "c" and c["family"] == "STATE")
        assert probe["pattern"] in cell["patterns"]
        assert "CWE-841" in cell["cwes"]
        assert "probe sink" in cell["sinks"]
    finally:
        # 回滚探针条目与格内容
        inv3 = json.load(open(inv_p))
        inv3["entries"] = [x for x in inv3["entries"] if x["id"] != "INV-c-019"]
        json.dump(inv3, open(inv_p, "w"), ensure_ascii=False, indent=1)
        mat3 = json.load(open(mat_p))
        cell = next(c for c in mat3["cells"] if c["lang"] == "c" and c["family"] == "STATE")
        cell["patterns"] = [p for p in cell["patterns"] if "探针" not in p]
        cell["cwes"] = [c for c in cell["cwes"] if c != "CWE-841"]
        cell["sinks"] = [x for x in cell["sinks"] if x != "probe sink"]
        cell["pitfalls"] = [x for x in cell["pitfalls"] if x != "probe pitfall"]
        cell["source_lessons"] = [x for x in cell["source_lessons"] if "v3.39 test" not in x]
        json.dump(mat3, open(mat_p, "w"), ensure_ascii=False, indent=1)


def test_t3_asset_guards_consistent():
    """T-3: asset_guards 常量 = 资产实况 (动态一致性, 单点更新义务)。"""
    inv = json.load(open(os.path.join(ROOT, "assets", "resources",
                                      "language_issue_inventory.json")))
    assert len(inv["entries"]) == asset_guards.INVENTORY_ENTRIES
    bc = sum(1 for e in inv["entries"]
             if e.get("verify", {}).get("status") == "battle_confirmed")
    assert bc == asset_guards.BATTLE_CONFIRMED
    ck = json.load(open(os.path.join(ROOT, "assets", "resources",
                                     "checklist_library.json")))
    assert len(ck["checklists"]) == asset_guards.CHECKLISTS


def test_t4_severity_override_dict_normalized(tmp_path, capsys):
    """T-4: stage_collect 对 dict 形态 severity_override 归一化 + warn (实路径)。"""
    import batch_verify as bv
    proj = tmp_path / "proj"
    (proj / ".audit_results").mkdir(parents=True)
    verdicts = [{"id": "CAND-001", "verdict": "REACHABLE",
                 "reachability_type": "DIRECT", "call_chain": ["a.c:1"],
                 "call_chain_depth": 1, "evidence": "e",
                 "evidence_grade": "edge_proven", "blocking_point": None,
                 "severity_override": {"value": "medium", "reason": "r1"},
                 "claim_type": None}]
    q = {"candidates": [{"id": "CAND-001", "source_file": "a.c",
                         "source_line": 1, "sink_type": "CWE-770",
                         "status": "PENDING", "priority": 0}],
         "target_kind": "application"}
    json.dump(q, open(proj / ".audit_results" / "verify_queue.json", "w"))
    bv.stage_collect(str(proj), 0, {"CAND-001": verdicts[0]})
    q2 = json.load(open(proj / ".audit_results" / "verify_queue.json"))
    c = q2["candidates"][0]
    assert c["severity_override"] == "medium"
    assert c["severity_override_reason"] == "r1"
    err = capsys.readouterr().err
    assert "severity_override_dict_normalized" in err
    # 字符串形态零变化 (无 warn)
    verdicts[0]["severity_override"] = "high"
    verdicts[0]["severity_override_reason"] = "r2"
    bv.stage_collect(str(proj), 1, {"CAND-001": verdicts[0]})
    q3 = json.load(open(proj / ".audit_results" / "verify_queue.json"))
    assert q3["candidates"][0]["severity_override"] == "high"
