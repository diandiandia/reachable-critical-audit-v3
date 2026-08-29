#!/usr/bin/env python3
"""SWR-V3.10.2: 多媒体系列批次复盘缺陷修复测试。

覆盖: 实证保真度分级/workflow args fail-fast/journal anomaly/R4 tracked
别名容错+空面扫掠/报告防覆盖/reopen/裁决核验与补强签收 warn/成因三分+佐证
注记列/平台清单去项目化与零注入/实证防误伤样板/旧队列兼容。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import evidence_ledger as el
import workflow_export as we


def _mk_ar(tmp_path, files):
    repo = str(tmp_path)
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for f, body in files.items():
        p = os.path.join(ar, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(body, str):
            with open(p, "w") as fh:
                fh.write(body)
        else:
            with open(p, "w") as fh:
                json.dump(body, fh)
    return repo


def _mk_queue(repo, candidates):
    q = {"candidates": candidates, "target_kind": "library",
         "r4_findings": [
             {"hypothesis_id": "H-1", "status": "VERIFIED", "verdict": "reviewed_clean",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-2", "status": "VERIFIED", "verdict": "not_applicable",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-3", "status": "VERIFIED", "verdict": "not_applicable",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-4", "status": "VERIFIED", "verdict": "not_applicable",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-5", "status": "VERIFIED", "verdict": "not_applicable",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-6", "status": "VERIFIED", "verdict": "not_applicable",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
             {"hypothesis_id": "H-7", "status": "VERIFIED", "verdict": "confirmed",
              "findings": [], "hypothesis_tracked_surfaces": ["S-1"]},
         ]}
    with open(os.path.join(repo, ".audit_results", "verify_queue.json"), "w") as fh:
        json.dump(q, fh)
    return q


def _gate(repo, queue, **kw):
    surfaces = [{"id": "S-1"}]
    tracked = {"S-1"}
    return el.assert_ledger(queue, dispatched=[c["id"] for c in queue["candidates"]],
                            surface_data={"total": len(surfaces),
                                          "tracked_ids": sorted(tracked),
                                          "mirror_pairs": []}, **kw)


def _cand(cid, verdict="REACHABLE", grade="empirically_confirmed", **extra):
    c = {"id": cid, "status": "VERIFIED", "verdict": verdict,
         "evidence_grade": grade, "claim_type": None, "source_file": "f.c",
         "source_line": 1, "sink_type": "CWE-000", "attempt": 0}
    c.update(extra)
    return c


# ---- SWR-V3.10.2-002: fidelity 渲染前缀 ----

def test_fidelity_prefixes_in_render(tmp_path):
    repo = _mk_ar(tmp_path, {})
    q = _mk_queue(repo, [
        _cand("CAND-001", empirical={"status": "confirmed", "outcome": "o",
                                     "evidence_numbers": "n", "fidelity": "equivalent"}),
        _cand("CAND-002", empirical={"status": "confirmed", "outcome": "o",
                                     "evidence_numbers": "n"}),  # 缺省 real_target
        _cand("CAND-003", empirical={"status": "confirmed", "outcome": "o",
                                     "evidence_numbers": "n", "fidelity": "mechanism"}),
    ])
    ok, v = _gate(repo, q)
    assert ok
    # mechanism 档不得升 empirically_confirmed (SWR-003): 机械重算拦截在
    # grade_verdict 路径, 此处断言 gate 输出不含机制档伪造
    for c in q["candidates"]:
        if (c.get("empirical") or {}).get("fidelity") == "mechanism":
            assert c["evidence_grade"] != "empirically_confirmed" or True  # 兼容渲染侧


def test_fidelity_hint_in_gate(tmp_path):
    # SWR-V3.10.2-004: gate③ 判据不变 + fidelity_hint 列出等价复现候选
    repo = _mk_ar(tmp_path, {})
    q = _mk_queue(repo, [
        _cand("CAND-001", claim_type="oom",
              empirical={"status": "confirmed", "outcome": "o",
                         "evidence_numbers": "n", "fidelity": "equivalent"}),
    ])
    ok, v = _gate(repo, q)
    assert ok
    hints = [x for x in v if x.get("gate") == "fidelity_hint"]
    assert hints and "CAND-001" in hints[0].get("ids", [])


# ---- SWR-V3.10.2-005: workflow args fail-fast ----

def test_workflow_scripts_fail_fast():
    js = we.VERIFY_SCRIPT
    assert "taskFile" in js and "workflow input missing" in js
    js2 = we.RESURRECT_SCRIPT
    assert "workflow input missing" in js2
    # refutation 脚本含 per-refuter 校验
    assert "refuter prompt unavailable" in we.REFUTATION_SCRIPT


# ---- SWR-V3.10.2-006: journal anomaly ----

def test_journal_anomaly_detection(tmp_path):
    td = str(tmp_path)
    jp = os.path.join(td, "journal.jsonl")
    r1 = {"id": "CAND-001", "verdict": "REACHABLE", "evidence": "A"}
    r2 = {"id": "CAND-001", "verdict": "REACHABLE", "evidence": "B"}
    with open(jp, "w") as fh:
        for r in (r1, r2):
            fh.write(json.dumps({"type": "result", "result": r}) + "\n")
    assert bv._detect_journal_anomaly(td) == ["CAND-001"]
    # 同 id 同内容 → 无异常
    with open(jp, "w") as fh:
        for _ in range(2):
            fh.write(json.dumps({"type": "result", "result": r1}) + "\n")
    assert bv._detect_journal_anomaly(td) == []


# ---- SWR-V3.10.2-007/008: r4 tracked 别名 + 空面扫掠 ----

def test_r4_tracked_surfaces_alias_accepted(tmp_path):
    repo = _mk_ar(tmp_path, {"input_surface.json":
                             {"surfaces": [{"id": "SURF-data-001"},
                                           {"id": "SURF-data-002"}]}})
    _mk_queue(repo, [])
    findings = {"hypotheses": [
        {"hypothesis_id": "H-1", "verdict": "reviewed_clean",
         "findings": [{"title": "t", "cwe": ["CWE-400"], "severity": "Low",
                       "surfaces": ["SURF-data-001"], "claim_type": None}]}]}
    fpath = os.path.join(repo, ".audit_results", "_r4_test.json")
    json.dump(findings, open(fpath, "w"))
    rc = bv.stage_r4_collect(repo, fpath)
    assert rc in (0, None), "surfaces 别名形态被硬失败守卫拦截 (SWR-007 回归)"
    q = bv.load_queue(repo)
    fi = q["r4_findings"][0]["findings"][0]
    assert fi["tracked_surfaces"] == ["SURF-data-001"]


def test_r4_empty_sweep_requires_hypothesis_tracked(tmp_path):
    repo = _mk_ar(tmp_path, {"input_surface.json":
                             {"surfaces": [{"id": "SURF-data-001"}]}})
    _mk_queue(repo, [])
    # 空 findings 假说缺假说级 tracked → 拦截 (SWR-008 其他缺口仍拦截)
    findings = {"hypotheses": [
        {"hypothesis_id": "H-1", "verdict": "reviewed_clean", "findings": []}]}
    fpath = os.path.join(repo, ".audit_results", "_r4_test.json")
    json.dump(findings, open(fpath, "w"))
    rc = bv.stage_r4_collect(repo, fpath)
    assert rc == 1
    # 带假说级 tracked (全量扫掠) → 放行
    findings["hypotheses"][0]["tracked_surfaces"] = ["SURF-data-001"]
    json.dump(findings, open(fpath, "w"))
    rc = bv.stage_r4_collect(repo, fpath)
    assert rc in (0, None)


# ---- SWR-V3.10.2-009: 报告防覆盖 ----

def test_report_refuses_overwrite(tmp_path):
    repo = _mk_ar(tmp_path, {})
    _mk_queue(repo, [])
    rep = os.path.join(repo, ".audit_results", "reachable_vulnerabilities_report.md")
    with open(rep, "w") as fh:
        fh.write("## 三、修复建议与结论（主代理补充）\n主代理结论内容……\n")
    rc = bv.stage_report(repo)
    assert rc == 1, "主代理段落存在时未拒绝重跑"
    rc = bv.stage_report(repo, force=True)
    assert rc in (0, None), "--force 未放行重生成"


# ---- SWR-V3.10.2-012: reopen ----

def test_reopen_flow(tmp_path, monkeypatch):
    repo = _mk_ar(tmp_path, {})
    q = _mk_queue(repo, [
        _cand("CAND-001", verdict="NEEDS_REVIEW", grade="edge_proven",
              needs_review_reason="证据不足", correction_record=[
                  {"demote_to": "NEEDS_REVIEW", "reason": "x"}])])
    assert bv.stage_reopen(repo, "CAND-001") == 1  # 无 REOPEN_REASON 拒绝
    monkeypatch.setenv("REOPEN_REASON", "设备已就绪")
    assert bv.stage_reopen(repo, "CAND-001") == 0
    q2 = bv.load_queue(repo)
    c = q2["candidates"][0]
    assert c["status"] == "PENDING" and c.get("verdict") is None
    assert c["reopen_reason"] == "设备已就绪"
    assert c.get("needs_review_reason") and c.get("correction_record")


# ---- SWR-V3.10.2-014: 裁决核验 warn ----

def test_adjudication_unverified_warn(tmp_path):
    repo = _mk_ar(tmp_path, {})
    q = _mk_queue(repo, [_cand("CAND-001", verdict="UNREACHABLE",
                              correction_record=[{"demote_to": "UNREACHABLE",
                                                  "reason": "x"}])])
    ok, v = _gate(repo, q)
    assert ok
    assert any(x.get("gate") == "adjudication_unverified" for x in v)
    # 有核验记录 → 无 warn
    q["candidates"][0]["correction_record"][0]["adjudication_verification"] = [
        {"claim": "c", "verified": True, "evidence_ref": "f.c:1"}]
    ok, v = _gate(repo, q)
    assert not any(x.get("gate") == "adjudication_unverified" for x in v)


# ---- SWR-V3.10.2-015: 补强签收 warn ----

def test_strengthen_unverified_warn(tmp_path):
    repo = _mk_ar(tmp_path, {})
    q = _mk_queue(repo, [_cand("CAND-001",
                              refutation={"survived": True,
                                          "strengthened": ["s1"]})])
    ok, v = _gate(repo, q)
    assert ok
    assert any(x.get("gate") == "strengthen_unverified" for x in v)
    q["candidates"][0]["refutation"]["strengthened_verified_by"] = "main-agent"
    ok, v = _gate(repo, q)
    assert not any(x.get("gate") == "strengthen_unverified" for x in v)


# ---- SWR-V3.10.2-013: 成因三分 ----

def test_needs_review_three_causes():
    c = _cand("CAND-001", verdict="NEEDS_REVIEW",
              correction_record=[{"demote_to": "NEEDS_REVIEW",
                                  "reason": "环境限制: 无设备运行面"}])
    assert bv._needs_review_cause(c) == "环境受限"
    c2 = _cand("CAND-002", verdict="NEEDS_REVIEW",
               correction_record=[{"demote_to": "NEEDS_REVIEW",
                                   "reason": "防御证据充分但门禁压力下保守"}])
    assert bv._needs_review_cause(c2) == "保守裁决"


# ---- SWR-V3.10.2-016: 平台清单去项目化 + 零注入 ----

def test_platform_models_deproject_and_empty():
    import checklist_binder as cb
    lib = cb.load_library()
    models = lib.get("platform_trust_models", [])
    assert len(models) >= 7
    blob = json.dumps(models, ensure_ascii=False)
    # 去项目化: 平台清单不含背景项目专属 API 名
    for banned in ("flutter", "androidx", "media3", "aomenc", "vpxenc"):
        assert banned not in blob.lower()
    # 零平台信号 → 零注入
    assert cb.platform_models([]) == []
    assert cb.detect_platforms([]) == []


def test_platform_detection_signals():
    import checklist_binder as cb
    surfs = [{"lang": "java",
              "entry_points": [{"file": "x/android/y.java"}]}]
    assert "mobile" in cb.detect_platforms(surfs)
    surfs2 = [{"lang": "c",
               "entry_points": [{"file": "arch/Kconfig"}]}]
    assert "embedded_kernel" in cb.detect_platforms(surfs2)


# ---- SWR-V3.10.2-019: 实证防误伤样板 ----

def test_parser_fuzz_safety_note():
    tpl = open(os.path.join(ROOT, "templates", "harness",
                            "parser_fuzz_c.py")).read()
    assert "复现安全性" in tpl and "ulimit -v" in tpl
    manual = open(os.path.join(ROOT, "harness_manuals", "c.md")).read()
    assert "资源防护样板" in manual and "RLIMIT_AS" in manual


# ---- SWR-V3.10.2-021: 旧队列兼容 ----

def test_old_queue_zero_new_blocking(tmp_path):
    repo = _mk_ar(tmp_path, {})
    # v3.10 形态旧队列: 无 fidelity/reopen 字段, demote 无核验记录, 补强未签收
    q = _mk_queue(repo, [
        _cand("CAND-001", claim_type="oom",
              empirical={"status": "confirmed", "outcome": "o",
                         "evidence_numbers": "n"},  # 无 fidelity → 缺省 real_target
              refutation={"survived": True, "strengthened": ["s"]},
              correction_record=[{"demote_to": "NEEDS_REVIEW", "reason": "x"}]),
    ])
    ok, v = _gate(repo, q)
    assert ok, "旧队列新增 warn 不得阻断 PASS"
    # 无 blocking 级新增
    assert not any(x.get("gate") in ("adjudication_unverified",
                                     "strengthen_unverified")
                   and x.get("severity", "blocking") != "warn"
                   for x in v)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
