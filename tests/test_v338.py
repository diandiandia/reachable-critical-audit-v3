"""v3.38 (SWR-V3.38-001~005): 模型能力利用五机制守卫。
- 清单挂载修复 (v3.37 两条目 binding) + CK-SIBLING-CONSISTENCY
- self_refutations schema/任务书条款/证伪注入
- SKILL.md R2 两条款 + R5 回收条款"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def _cand(**kw):
    base = {"id": "CAND-001", "source_file": "a.go", "source_line": 1,
            "sink_type": "CWE-000", "status": "VERIFIED", "verdict": "REACHABLE",
            "evidence_grade": "edge_proven", "evidence": "e", "summary": "s"}
    base.update(kw)
    return base


def test_t0_v337_entries_bind(tmp_path, monkeypatch):
    """T-0: v3.37 两条目补 binding 且 binder 实测挂载。"""
    import checklist_binder as cb
    # CK-MAGNITUDE-OWNERSHIP: R5 语义空间挂载 (claim_type=oom)
    bound = dict(cb.bind(_cand(cwe=["CWE-770"], claim_type="oom")))
    assert "CK-MAGNITUDE-OWNERSHIP" in bound, bound
    # CK-SLICE-CAPACITY: CWE-125 命中
    bound = dict(cb.bind(_cand(cwe=["CWE-125"])))
    assert "CK-SLICE-CAPACITY" in bound, bound
    # 非实证类非 memory-safety 候选不挂载这两条 (零误挂)
    bound = dict(cb.bind(_cand(cwe=["CWE-697"], claim_type=None)))
    assert "CK-MAGNITUDE-OWNERSHIP" not in bound
    assert "CK-SLICE-CAPACITY" not in bound


def test_t1_sibling_consistency_entry():
    """T-1: CK-SIBLING-CONSISTENCY 条目 + binding + 去项目化 + 挂载。"""
    import checklist_binder as cb
    d = json.load(open(os.path.join(ROOT, "assets", "resources",
                                    "checklist_library.json")))
    e = next(c for c in d["checklists"] if c["id"] == "CK-SIBLING-CONSISTENCY")
    assert e["family"] == "sibling-consistency"
    assert len(e["steps"]) == 4
    assert e.get("binding"), "缺 binding 永不挂载 (v3.37 欠账同形)"
    body = json.dumps({k: v for k, v in e.items() if k != "source_lessons"},
                      ensure_ascii=False).lower()
    for tok in ("caddy", "cand-001", "load.go"):
        assert tok not in body, tok
    # 端点形态候选 (summary 含 端点/admin——关键词吃 summary/snippet/title
    # 字段集, 不含 evidence) 挂载; 非端点形态不挂载 (且不短路 resource 兜底,
    # SWR-087 CK-GENERIC-RESOURCE 机制)
    ep = _cand(cwe=["CWE-770"], summary="admin /load 与 /adapt 端点的请求体无界整读")
    assert "CK-SIBLING-CONSISTENCY" in dict(cb.bind(ep))
    tok = _cand(cwe=["CWE-400"], summary="token.indexOf(delimiter) 线性扫描")
    assert "CK-SIBLING-CONSISTENCY" not in dict(cb.bind(tok))
    assert "CK-GENERIC-RESOURCE" in dict(cb.bind(tok))


def test_t2_self_refutations_wired():
    """T-2: schema 可选字段 + verify prompt 条款 + refute 注入。"""
    import workflow_export as we
    assert "self_refutations" in we.VERDICT_SCHEMA["properties"]
    assert "self_refutations" not in we.VERDICT_SCHEMA["required"]
    # verify prompt 条款 (经 export_script 落盘任务书)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        proj = os.path.join(tmp, "proj")
        os.makedirs(os.path.join(proj, ".audit_results"))
        json.dump({"candidates": [
            _cand(status="PENDING", verdict="PENDING", claim_type="unbounded",
                  cwe=["CWE-770"])], "r4_findings": [], "target_kind": "application"},
            open(os.path.join(proj, ".audit_results", "verify_queue.json"), "w"))
        we.export_script(proj, mode="verify", batch_size=1)
        tf = json.load(open(os.path.join(proj, ".audit_results",
                                         "verify_payload_slim.json")))[0]["taskFile"]
        text = open(tf).read()
        assert "自证伪轮" in text and "self_refutations" in text
        assert "实证机会条款" in text
    # refute_prompt 注入
    c = _cand(claim_type="unbounded", cwe=["CWE-770"],
              self_refutations=["若 body 大小由部署方配置决定则翻转",
                                "若 admin 不可达于异主体则翻转"])
    pr = we.refute_prompt(c, 0)
    assert "证伪攻击面" in pr and "若 body 大小" in pr


def test_t3_skillmd_clauses():
    """T-3: SKILL.md R2 两条款 + R5 回收条款在位。"""
    text = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "同族不一致防御枚举" in text
    assert "公开面关联检索" in text
    assert "harness 回收条款" in text
    assert "upstream_recon.json" in text


def test_t4_counts_and_regression():
    """T-4: 清单 48 + 既有 47 条 id 稳定。"""
    d = json.load(open(os.path.join(ROOT, "assets", "resources",
                                    "checklist_library.json")))
    assert len(d["checklists"]) == 50  # v3.40 +1 (SWR-V3.40-003)
    ids = [c["id"] for c in d["checklists"]]
    assert len(ids) == len(set(ids))
    for cid in ("CK-UNBOUNDED-HOPS", "CK-SLICE-CAPACITY", "CK-MAGNITUDE-OWNERSHIP"):
        assert cid in ids
