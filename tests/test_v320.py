#!/usr/bin/env python3
"""SWR-V3.20: WebKit 审计复盘缺陷修复测试 (15 用例)。

覆盖: 自报分级三值枚举+机械口径注记 (D-1) / collect drift_summary 方向对
计数 (D-2) / lessons_recorder 方向对 detail (D-3) / 守卫通过子集枚举义务 +
guard_pass_subsets 条件校验 warn 正反分支 (D-4) / premises_verified 同形态
(D-5) / schema optional 不进 required / 白名单落盘 / 零改写反面分支 /
TOOLING 3.20。"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import lessons_recorder as lr
import workflow_export as we


def _prompt_ctx():
    return {"file": "src/x.cc", "line": 1, "cwe": "CWE-125",
            "category": "?", "lang": "cpp", "language": "cpp",
            "sink": "arr[i] = payload[i];",
            "sources_regex": "recv|read|payload"}


def _mk_project(tmp_path, cand):
    """最小项目: .audit_results/verify_queue.json + 单候选 PENDING。"""
    d = tmp_path / "proj"
    (d / ".audit_results").mkdir(parents=True)
    queue = {"candidates": [cand], "target_kind": "library",
             "r4_findings": [], "escalated_signed_off": False}
    (d / ".audit_results" / "verify_queue.json").write_text(
        json.dumps(queue), encoding="utf-8")
    return str(d)


def _base_cand(cid="CAND-001"):
    return {"id": cid, "source_file": "src/x.cc", "source_line": 1,
            "sink_type": "CWE-125", "status": "PENDING", "attempt": 0}


def _verdict(**kw):
    v = {"id": "CAND-001", "verdict": "UNREACHABLE",
         "reachability_type": "DIRECT",
         "call_chain": ["src/a.cc:1:f", "src/b.cc:2:g", "src/x.cc:1:h"],
         "call_chain_depth": 3, "evidence": "阻断论证", "blocking_point": "src/x.cc:5",
         "evidence_grade": "static_only", "cwe": ["CWE-125"]}
    v.update(kw)
    return v


# ---- SWR-V3.20-001: 三值枚举 + 机械口径注记 ----


def test_prompt_grade_enum_three_values():
    cand = _base_cand()
    prompt = bv._build_prompt(cand, _prompt_ctx(), ROOT)
    assert '"evidence_grade": "static_only | edge_proven | empirically_confirmed"' in prompt
    assert "仅追溯" in prompt
    assert "机械重算为唯一权威" in prompt
    assert "结构化进 edge_evidence 数组" in prompt


def test_prompt_guard_and_premise_obligations():
    cand = _base_cand()
    prompt = bv._build_prompt(cand, _prompt_ctx(), ROOT)
    assert "守卫通过子集" in prompt
    assert "guard_pass_subsets" in prompt
    assert "premises_verified" in prompt
    assert "逐条" in prompt


# ---- SWR-V3.20-002: drift_summary ----


def test_collect_drift_summary_promote_by_edges(tmp_path, capsys):
    """自报 static_only + 满边证据 → 机械 edge_proven, drift_summary 计数。"""
    proj = _mk_project(tmp_path, _base_cand())
    v = _verdict(evidence_grade="static_only",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    ds = out["drift_summary"]
    assert ds["recomputed"] == 1 and ds["promoted"] == 1 and ds["demoted"] == 0
    assert ds["pairs"] == {"static_only->edge_proven": 1}


def test_collect_drift_summary_promote_by_empirical(tmp_path, capsys):
    """R5 回填实证后重 collect 实录形态: 队列已有 empirical + 自报 edge_proven,
    机械重算 → empirically_confirmed, 漂移对计数。"""
    cand = _base_cand()
    cand["grade_self_reported"] = "edge_proven"
    cand["evidence_grade"] = "edge_proven"
    cand["empirical"] = {"status": "confirmed", "outcome": "crash"}
    proj = _mk_project(tmp_path, cand)
    v = _verdict(evidence_grade="edge_proven",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    ds = out["drift_summary"]
    assert ds["pairs"] == {"edge_proven->empirically_confirmed": 1}
    assert ds["promoted"] == 1


def test_collect_no_drift_zero_summary(tmp_path, capsys):
    """自报=机械 (满边 edge_proven) → drift_summary 零计数。"""
    proj = _mk_project(tmp_path, _base_cand())
    v = _verdict(verdict="REACHABLE", evidence_grade="edge_proven",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    assert out["drift_summary"]["recomputed"] == 0


# ---- SWR-V3.20-003: lessons_recorder 方向对 ----


def test_recorder_drift_detail_pair(tmp_path):
    proj = _mk_project(tmp_path, _base_cand())
    v = _verdict(evidence_grade="static_only",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    r = lr.collect(str(tmp_path / "proj"))
    hits = [i for i in r["issues"] if i["kind"] == "grade_recomputed"]
    assert len(hits) == 1
    assert "static_only->edge_proven" in hits[0]["detail"]


def test_recorder_stale_flag_no_fake_pair(tmp_path):
    """陈旧标记 (重 collect 无新漂移, 当前值一致) → 不产出伪方向对。"""
    cand = _base_cand()
    cand["grade_self_reported"] = "edge_proven"
    cand["evidence_grade"] = "edge_proven"
    cand["grade_recomputed_by"] = "collect-mechanical-recompute"
    proj = _mk_project(tmp_path, cand)
    v = _verdict(evidence_grade="edge_proven",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    r = lr.collect(str(tmp_path / "proj"))
    hits = [i for i in r["issues"] if i["kind"] == "grade_recomputed"]
    assert len(hits) == 1
    assert "edge_proven->edge_proven" not in hits[0]["detail"]
    assert "历史标记" in hits[0]["detail"]


# ---- SWR-V3.20-006: canonical 保留键推断 ----


def test_grade_verdict_canonical_keys_fallback():
    """SKILL.md canonical 回填形态 (outcome/evidence_numbers/report 无 status)
    机械判 empirically_confirmed + 附回填提示——WebKit 6 例实证候选形态。"""
    import evidence_ledger as el
    v = {"verdict": "REACHABLE", "call_chain": ["a:1:f", "b:2:g"],
         "edge_evidence": [{"edge": "f->g", "proof": "b:2"}],
         "empirical": {"outcome": "SIGBUS", "evidence_numbers": "1/1",
                       "report": "empirical/REPORT.md"}}
    grade, errors = el.grade_verdict(v)
    assert grade == "empirically_confirmed"
    assert any("status" in e for e in errors)


def test_grade_verdict_partial_canonical_no_promote():
    """三保留键不全且无 status/scope → 不判 empirically_confirmed。"""
    import evidence_ledger as el
    v = {"verdict": "REACHABLE", "call_chain": ["a:1:f", "b:2:g"],
         "edge_evidence": [{"edge": "f->g", "proof": "b:2"}],
         "empirical": {"outcome": "SIGBUS"}}
    grade, errors = el.grade_verdict(v)
    assert grade == "edge_proven"


# ---- SWR-V3.20-004/005: 条件校验 warn 与白名单落盘 ----


def test_unreachable_without_fields_warns(tmp_path, capsys):
    proj = _mk_project(tmp_path, _base_cand())
    bv.stage_collect(proj, "b1", {"CAND-001": _verdict()})
    out = json.loads(capsys.readouterr().out)
    assert any("guard_pass_subsets" in w for w in out["warnings"])
    assert any("premises_verified" in w for w in out["warnings"])


def test_dead_code_exempt_no_warn(tmp_path, capsys):
    proj = _mk_project(tmp_path, _base_cand())
    v = _verdict(blocking_point="no production callers")
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    assert out["warnings"] == []


def test_reachable_no_warn(tmp_path, capsys):
    proj = _mk_project(tmp_path, _base_cand())
    v = _verdict(verdict="REACHABLE", evidence_grade="edge_proven",
                 edge_evidence=[{"edge": "f->g", "proof": "src/b.cc:2"},
                                {"edge": "g->h", "proof": "src/x.cc:1"}])
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    assert out["warnings"] == []


def test_fields_whitelist_landing_and_zero_rewrite(tmp_path, capsys):
    """两字段非空落盘; warn 不改写 verdict/grade; 自报值保留原值。"""
    proj = _mk_project(tmp_path, _base_cand())
    gps = [{"guard_location": "src/x.cc:5", "enumerated_subsets": "size 声明",
            "coverage": "全覆盖"}]
    pv = [{"premise": "capacity 非零", "file": "src/x.cc:5", "status": "broken"}]
    v = _verdict(guard_pass_subsets=gps, premises_verified=pv)
    bv.stage_collect(proj, "b1", {"CAND-001": v})
    out = json.loads(capsys.readouterr().out)
    assert out["warnings"] == []
    q = bv.load_queue(proj)
    e = q["candidates"][0]
    assert e["guard_pass_subsets"] == gps and e["premises_verified"] == pv
    assert e["verdict"] == "UNREACHABLE"
    assert e["grade_self_reported"] == "static_only"
    assert e["evidence_grade"] == "static_only"


# ---- P2: schema optional 不进 required ----


def test_verdict_schema_optional_fields():
    s = we.VERDICT_SCHEMA
    assert "guard_pass_subsets" in s["properties"]
    assert "premises_verified" in s["properties"]
    assert "guard_pass_subsets" not in s["required"]
    assert "premises_verified" not in s["required"]


# ---- 版本链 ----


def test_tooling_version_320():
    assert we.TOOLING_VERSION == "3.20"
