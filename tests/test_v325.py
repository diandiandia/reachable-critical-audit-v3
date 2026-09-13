#!/usr/bin/env python3
"""SWR-V3.25: MaintainWise 验收审计复盘缺陷修复测试 (8 用例)。

覆盖: verify 导出 taskFile 化 (D-1) / r35-collect A' 文件目录输入 (D-2) /
verifier 编码矩阵条款 (D-3) / r4-collect severity 传递 warn (D-4) /
storage 预置数据文件面指引 (D-5) / R5 核取提示句 (D-6) /
去项目化 + 版本链。"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import workflow_export as we

SKILL = open(os.path.join(ROOT, "SKILL.md")).read()
SURFACE_TMPL = open(os.path.join(ROOT, "assets", "task_templates", "surface_map_domain.md")).read()

PROJECT_TOKENS = ("v8", "WebKit", "firefox", "Chrome", "MaintainWise", "CAND-")


# ---- SWR-V3.25-001: verify 导出 taskFile 化 ----

def _mk_queue(d):
    p = tempfile.mkdtemp()
    os.makedirs(os.path.join(p, ".audit_results"))
    q = {"candidates": d, "r4_findings": [], "target_kind": "application"}
    json.dump(q, open(os.path.join(p, ".audit_results", "verify_queue.json"), "w"))
    return p


def test_verify_export_taskfile():
    p = _mk_queue([{"id": "CAND-001", "status": "PENDING", "source_file": "x.py",
                    "source_line": 1, "sink_type": "CWE-20", "attempt": 0}])
    r = we.export_script(p, mode="verify", batch_size=4)
    pl = r["payload"]
    assert len(pl) == 1
    assert pl[0].get("taskFile"), "verify 导出缺 taskFile"
    assert os.path.exists(os.path.join(p, pl[0]["taskFile"])), "taskFile 未落盘"
    assert "verify_payload_slim.json" in os.listdir(os.path.join(p, ".audit_results"))
    # 反面分支: payload 条目保留 prompt 仅作回退, slim 文件不含 prompt 全文
    slim = json.load(open(os.path.join(p, ".audit_results", "verify_payload_slim.json")))
    assert "prompt" not in slim[0] and "taskFile" in slim[0]


# ---- SWR-V3.25-002: r35-collect A' 文件目录输入 ----

def test_r35_collect_refute_files_dir(capsys):
    p = _mk_queue([{"id": "CAND-001", "status": "VERIFIED", "verdict": "REACHABLE",
                    "evidence_grade": "edge_proven", "claim_type": None,
                    "source_file": "x.py", "source_line": 1}])
    d = os.path.join(p, ".audit_results")
    # 双杀 -> demote
    json.dump({"id": "CAND-001", "refuted": True, "reason": "kill a", "agent": "r0"},
              open(os.path.join(d, "_refute_CAND-001_0.json"), "w"))
    json.dump({"id": "CAND-001", "refuted": True, "reason": "kill b", "agent": "r1"},
              open(os.path.join(d, "_refute_CAND-001_1.json"), "w"))
    assert bv.stage_r35_collect(p, d) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["status"] == "R35_COLLECTED"
    c = bv.load_queue(p)["candidates"][0]
    assert c["refutation"]["refute_count"] == 2 and c["refutation"]["survived"] is False
    assert c["verdict"] == "NEEDS_REVIEW"
    # 1 kill 1 不杀 -> survived 保留分歧理由
    p2 = _mk_queue([{"id": "CAND-001", "status": "VERIFIED", "verdict": "REACHABLE",
                     "evidence_grade": "edge_proven", "claim_type": None,
                     "source_file": "x.py", "source_line": 1}])
    d2 = os.path.join(p2, ".audit_results")
    json.dump({"id": "CAND-001", "refuted": True, "reason": "kill", "agent": "r0"},
              open(os.path.join(d2, "_refute_CAND-001_0.json"), "w"))
    json.dump({"id": "CAND-001", "refuted": False, "reason": "confirm", "agent": "r1"},
              open(os.path.join(d2, "_refute_CAND-001_1.json"), "w"))
    assert bv.stage_r35_collect(p2, d2) == 0
    q2 = bv.load_queue(p2)
    assert q2["candidates"][0]["verdict"] == "REACHABLE"
    assert q2["candidates"][0]["refutation"]["survived"] is True


# ---- SWR-V3.25-003: verifier 编码矩阵条款 ----

def test_verifier_prompt_encoding_matrix():
    cand = {"id": "CAND-001", "source_file": "x.py", "source_line": 1,
            "sink_type": "CWE-22", "type": "TAINT_ANALYSIS", "cwe": ["CWE-22"]}
    ctx = bv._build_context(cand, ROOT)
    p = bv._build_prompt(cand, ctx, ROOT)
    assert "路径穿越编码矩阵" in p and "%252e" in p and "SWR-V3.25-003" in p
    # 反面分支: 非路径族不注入
    cand2 = {"id": "CAND-002", "source_file": "x.py", "source_line": 1,
             "sink_type": "CWE-20", "type": "TAINT_ANALYSIS", "cwe": ["CWE-20"]}
    p2 = bv._build_prompt(cand2, bv._build_context(cand2, ROOT), ROOT)
    assert "路径穿越编码矩阵" not in p2
    # 去项目化
    for tok in PROJECT_TOKENS:
        assert tok not in p[p.index("路径穿越编码矩阵"):p.index("路径穿越编码矩阵") + 200]


# ---- SWR-V3.25-004: severity 传递 warn ----

def test_r4_collect_severity_advisory(capsys):
    p = _mk_queue([{"id": "CAND-001", "status": "VERIFIED", "verdict": "REACHABLE",
                    "evidence_grade": "empirically_confirmed", "claim_type": "leak",
                    "source_file": "x.py", "source_line": 1,
                    "cwe": ["CWE-287"]}])
    inp = os.path.join(p, ".audit_results", "_r4_merged.json")
    json.dump({"hypotheses": [{"hypothesis_id": "H-5",
                "verdict": "confirmed",
                "findings": [{"title": "T 任意文件读",
                              "cwe": ["CWE-22"], "severity": "Critical",
                              "call_chain": ["x.py:1"], "evidence": "e",
                              "fix": "f", "tracked_surfaces": ["SURF-x-001"],
                              "r3_link": "CAND-001", "claim_type": "leak",
                              "empirical_result": "CONFIRMED: 实测"}]}]},
             open(inp, "w"))
    json.dump({"surfaces": [{"id": "SURF-x-001", "name": "x", "type": "network",
                             "entry_points": [{"file": "x.py", "line": 1,
                                               "evidence": {"snippet": "x"}}],
                             "trust_boundary": {"type": "unauthenticated_remote"}}]},
              open(os.path.join(p, ".audit_results", "input_surface.json"), "w"))
    bv.stage_r4_collect(p, inp)
    r = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert r["status"] == "R4_COLLECTED"
    advs = r.get("severity_advisories", [])
    assert any(a["kind"] == "severity_transfer_advisory"
               and a["candidate_mechanical"] != "Critical" for a in advs), advs


# ---- SWR-V3.25-005: storage 预置数据文件面指引 ----

def test_surface_template_preseeded_files():
    seg = SURFACE_TMPL[SURFACE_TMPL.index("预置数据文件面指引"):]
    assert "预置数据库" in seg and "默认口令" in seg
    assert "SWR-V3.25-005" in seg and "storage 域注入" in seg
    for tok in PROJECT_TOKENS:
        assert tok not in seg.split("非网络/离线项目映射指引")[0], f"新段含项目 token: {tok}"


# ---- SWR-V3.25-006: R5 核取提示句 ----

def test_r5_harvest_hint():
    line = [l for l in SKILL.splitlines() if "先核取" in l]
    assert line and "已有实测数字" in line[0]
    assert "提示级" in line[0]
    for w in ("强制", "必须"):
        assert w not in line[0]


# ---- 版本链 ----

def test_tooling_version_325():
    assert we.TOOLING_VERSION == "3.41"
