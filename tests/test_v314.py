#!/usr/bin/env python3
"""SWR-V3.14: protobuf 复审计复盘缺陷修复测试 (8 用例)。

覆盖: journal anomaly 按 mode 阈值/账本幂等分支 manual_merge_guidance/
复活抽样 sample 文件权威三分支/unknown_surface_ids 建议映射/r3_link 值域
warn/R4-候选终态一致性 warn/SKILL.md 指引文案/TOOLING 3.14。"""
import contextlib
import io
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import workflow_export as we


def _mk_repo(tmp_path, files=None, queue=None, surfaces=None):
    repo = str(tmp_path)
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for f, body in (files or {}).items():
        p = os.path.join(repo, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(body)
    if surfaces is not None:
        json.dump(surfaces, open(os.path.join(ar, "input_surface.json"), "w"))
    if queue is not None:
        json.dump(queue, open(os.path.join(ar, "verify_queue.json"), "w"))
    return repo


def _mk_journal(td, results):
    """journal.jsonl 构造: results = [(id, payload_dict), ...]"""
    os.makedirs(td, exist_ok=True)
    with open(os.path.join(td, "journal.jsonl"), "w") as f:
        for cid, payload in results:
            rec = {"type": "result", "key": "k", "agentId": "a",
                   "result": {"id": cid, **payload}}
            f.write(json.dumps(rec) + "\n")
    return td


# ---- SWR-V3.14-001: anomaly 阈值按 mode ----

def test_anomaly_mode_aware_threshold(tmp_path):
    td = str(tmp_path)
    # 默认 1: 同 id 2 个不同 result → anomaly
    _mk_journal(td, [("A", {"verdict": "REACHABLE", "evidence": "e1"}),
                     ("A", {"verdict": "UNREACHABLE", "evidence": "e2"})])
    assert bv._detect_journal_anomaly(td) == ["A"]
    # r35 设计形态: max_distinct_per_id=2 → 2 个不判, 3 个判
    assert bv._detect_journal_anomaly(td, max_distinct_per_id=2) == []
    _mk_journal(td, [("A", {"verdict": "REACHABLE", "evidence": "e1"}),
                     ("A", {"verdict": "UNREACHABLE", "evidence": "e2"}),
                     ("A", {"verdict": "NEEDS_REVIEW", "evidence": "e3"})])
    assert bv._detect_journal_anomaly(td, max_distinct_per_id=2) == ["A"]


# ---- SWR-V3.14-005: 账本幂等分支增量指引 ----

def test_ledger_idempotent_merge_guidance(tmp_path, capsys):
    # 先首写烧 sources key (r4 前置需 H1-H7 全 VERIFIED), 再复跑验证幂等分支
    # manual_merge_guidance (delta=队列聚合非零)
    r4 = [{"hypothesis_id": h, "verdict": "reviewed_clean", "findings": [],
           "tracked_surfaces": [], "status": "VERIFIED"}
          for h in ["H-1", "H-2", "H-3", "H-4", "H-5", "H-6", "H-7"]]
    queue = {"candidates": [{"id": "C", "source_file": "a.go", "source_line": 1,
                             "sink_type": "CWE-770", "language": "go",
                             "cwe": ["CWE-770"], "status": "VERIFIED",
                             "verdict": "UNREACHABLE"}],
             "r4_findings": r4, "target_kind": "library"}
    repo = _mk_repo(tmp_path, queue=queue)
    bv.stage_coverage_ledger(repo, write=True)
    out1 = capsys.readouterr().out
    assert "LEDGER_WRITTEN" in out1
    bv.stage_coverage_ledger(repo, write=True)
    out2 = capsys.readouterr().out
    d = json.loads(out2)
    assert d["status"] == "LEDGER_IDEMPOTENT_SKIP"
    assert "manual_merge_guidance" in d
    mg = d["manual_merge_guidance"]
    assert mg["delta_cells"] and "RESOURCE-DOSxgo" in mg["delta_cells"]
    assert "rows" in mg["protocol"] and "manual_merge_note" in mg["protocol"]


# ---- SWR-V3.14-006: 复活抽样 sample 文件权威 ----

def _unreachable(cid):
    return {"id": cid, "status": "VERIFIED", "verdict": "UNREACHABLE",
            "source_file": "a.go", "source_line": 1, "sink_type": "CWE-000"}


def test_resurrect_sample_file_authority(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": [_unreachable("A"), _unreachable("B"),
                                                    _unreachable("C")]})
    ar = os.path.join(repo, ".audit_results")
    # 分支1: 文件存在且与候选集合一致 → 文件池为准 (selected=[C] 仅 1 条)
    json.dump({"selected": ["C"], "unselected": ["A", "B"], "rule": "r"},
              open(os.path.join(ar, "_resurrect_sample.json"), "w"))
    d = we.export_script_resurrect(repo)
    assert [x["id"] for x in d.get("payload", [])] == ["C"]
    # 文件 rule 注记标注权威来源
    saved = json.load(open(os.path.join(ar, "_resurrect_sample.json")))
    assert "v3.14" in saved["rule"]
    # 分支2: 文件漂移 (含已终态候选) → 内部抽样重写
    json.dump({"selected": ["A"], "unselected": ["B", "C", "D"], "rule": "r"},
              open(os.path.join(ar, "_resurrect_sample.json"), "w"))
    d2 = we.export_script_resurrect(repo)
    pool2 = [x["id"] for x in d2.get("payload", [])]
    assert pool2 and set(pool2) <= {"A", "B", "C"}
    saved2 = json.load(open(os.path.join(ar, "_resurrect_sample.json")))
    assert set(saved2["selected"]) | set(saved2["unselected"]) == {"A", "B", "C"}
    # 分支3: 文件缺失 → 内部抽样并写文件 (现状)
    os.remove(os.path.join(ar, "_resurrect_sample.json"))
    d3 = we.export_script_resurrect(repo)
    assert [x["id"] for x in d3.get("payload", [])]
    assert os.path.exists(os.path.join(ar, "_resurrect_sample.json"))


# ---- SWR-V3.14-002: unknown_surface_ids 建议映射 ----

def test_unknown_surface_suggestions(tmp_path):
    queue = {"candidates": [], "target_kind": "library",
             "r4_findings": [{"hypothesis_id": "H-1", "verdict": "confirmed",
                              "findings": [{"title": "t", "cwe": ["CWE-400"],
                                            "severity": "Low", "claim_type": None,
                                            "empirical_result": None,
                                            "tracked_surfaces": ["SURF-DATA-001"],
                                            "r3_link": None}]}]}
    repo = _mk_repo(tmp_path, queue=queue,
                    surfaces={"surfaces": [{"id": "S-DATA-001", "lang": "c"}]})
    src = os.path.join(repo, "r4.json")
    json.dump({"hypotheses": [{"hypothesis_id": "H-1", "verdict": "confirmed",
                               "findings": [{"title": "t", "cwe": ["CWE-400"],
                                             "severity": "Low",
                                             "tracked_surfaces": ["SURF-DATA-001"],
                                             "r3_link": None, "claim_type": None,
                                             "empirical_result": None}]}]},
              open(src, "w"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_r4_collect(repo, src)
    d = json.loads(buf.getvalue())
    assert d.get("unknown_surface_ids"), d
    sug = d.get("suggested_corrections") or {}
    assert "SURF-DATA-001" in sug and "S-DATA-001" in sug["SURF-DATA-001"]
    # tracked_surfaces 不被自动改写 (仍为原值)
    q = bv.load_queue(repo)
    assert q["r4_findings"][0]["findings"][0]["tracked_surfaces"] == ["SURF-DATA-001"]


# ---- SWR-V3.14-003: r3_link 值域 ----

def test_r3_link_domain_warn():
    out, flags = bv._adapt_r4_finding({"title": "t", "r3_link": "HYP-001"})
    assert out.get("r3_link_invalid") is True
    assert "r3-link-invalid" in flags
    out2, flags2 = bv._adapt_r4_finding({"title": "t", "r3_link": "CAND-002"})
    assert not out2.get("r3_link_invalid") and "r3-link-invalid" not in flags2
    out3, flags3 = bv._adapt_r4_finding({"title": "t", "r3_link": None})
    assert not out3.get("r3_link_invalid") and "r3-link-invalid" not in flags3


# ---- SWR-V3.14-004: R4-候选终态一致性 warn ----

def test_r4_verdict_link_conflict(tmp_path):
    def run(findings):
        queue = {"candidates": [{"id": "CAND-009", "status": "VERIFIED",
                                 "verdict": "NEEDS_REVIEW",
                                 "source_file": "a.c", "source_line": 1,
                                 "sink_type": "CWE-78"}],
                 "target_kind": "library", "r4_findings": []}
        repo = _mk_repo(tmp_path, queue=queue,
                        surfaces={"surfaces": [{"id": "S-A-001", "lang": "c"}]})
        src = os.path.join(repo, "r4.json")
        json.dump({"hypotheses": [{"hypothesis_id": "H-4", "verdict": "confirmed",
                                   "findings": findings}]}, open(src, "w"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bv.stage_r4_collect(repo, src)
        return json.loads(buf.getvalue())
    base = {"title": "f 维持 R3 UNREACHABLE", "cwe": ["CWE-78"],
            "severity": "Low", "tracked_surfaces": ["S-A-001"],
            "r3_link": "CAND-009", "claim_type": None, "empirical_result": None,
            "evidence": "维持 R3 UNREACHABLE"}
    d1 = run([base])
    conflicts = d1.get("r4_verdict_link_conflict") or []
    assert conflicts and conflicts[0]["candidate_verdict"] == "NEEDS_REVIEW"
    assert conflicts[0]["claimed_verdict"] == "UNREACHABLE"
    # 一致形态零告警
    ok = dict(base)
    ok["title"] = "f 终态 NEEDS_REVIEW 参照"
    ok["evidence"] = "复活重验后终态 NEEDS_REVIEW"
    d2 = run([ok])
    assert not d2.get("r4_verdict_link_conflict")
    # 无 r3_link 零告警
    nolink = dict(base); nolink["r3_link"] = None
    d3 = run([nolink])
    assert not d3.get("r4_verdict_link_conflict")


# ---- SWR-V3.14-007/008: 文案存在 ----

def test_skillmd_guidance_texts():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "优先派发具备写盘能力的子智能体" in skill
    assert "strengthened_verified_by" in skill
    assert "与 `strengthened[]` 平级" in skill  # 层级指引 (行内换行不参与断言)


# ---- SWR-V3.14-009: 版本链 ----

def test_tooling_version_v314():
    assert we.TOOLING_VERSION == "3.17"  # v3.15 版本链前进
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "## 🆕 v3.14 增量" in skill
