#!/usr/bin/env python3
"""SWR-V3.15: 五项目批次收官缺陷修复测试 (约 15 用例)。

覆盖: 报告守卫双形态 / is_claim_like 两处等值 (含 sink_type 差与否定语境词) /
R4 枚举建议映射 / post-resurrect advisory / 截断 key 集扩展矩阵 / tracked_surfaces
双形态 / scope_diff 消费优先 affected_dirs / 清单与先例新条目 / 模板文案 /
复活维度清单 / TOOLING 3.15。"""
import contextlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import workflow_export as we
import evidence_ledger as el


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


def _mk_cand(**kw):
    c = {"id": "CAND-001", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "claim_type": None, "evidence": "", "summary": ""}
    c.update(kw)
    return c


# ---------------- D-2: is_claim_like 统一判定 ----------------

def test_is_claim_like_claim_type_priority():
    assert el.is_claim_like({"claim_type": "oom"}) is True
    assert el.is_claim_like({"claim_type": "other", "evidence": "unbounded 放大"}) is True  # fallback
    assert el.is_claim_like({"claim_type": "other", "evidence": "路径解析"}) is False


def test_is_claim_like_rce_leak_included():
    # 旧本地副本缺 rce/leak 两声称类 (漂移源之一) —— 统一函数必须含
    assert el.is_claim_like({"claim_type": "rce"}) is True
    assert el.is_claim_like({"claim_type": "leak"}) is True


def test_is_claim_like_pool_gate_equivalence():
    # 门禁③c 与复活池同函数同字段——构造 sink_type 差用例 (旧池多扫 sink_type)
    c = _mk_cand(evidence="", summary="", sink_type="CWE-400")
    assert el.is_claim_like(c) is False
    # 否定语境词行为两处一致即可 (统一优先于否定语义精化)
    neg = _mk_cand(evidence="无 RCE/leak 风险")
    assert el.is_claim_like(neg) is True  # 文本命中; 门禁与池同此行为


def test_resurrect_pool_uses_unified_function(tmp_path):
    # 声称类 (unified is_claim_like) 全量 + 其他类 20% (min 2) 抽样
    repo = _mk_repo(tmp_path, queue={"candidates": [
        _mk_cand(id="CAND-001", evidence="unbounded 累积"),
        _mk_cand(id="CAND-002", evidence="普通路径解析"),
        _mk_cand(id="CAND-003", evidence="普通表解析"),
        _mk_cand(id="CAND-004", evidence="普通编码解析"),
    ]})
    pool = we.resurrect_pool(bv.load_queue(repo)["candidates"], batch_size=8)
    ids = [c["id"] for c in pool]
    assert "CAND-001" in ids                      # 声称类全量
    assert len([i for i in ids if i != "CAND-001"]) == 2   # 其他 20% min 2


# ---------------- D-1: 报告守卫双形态 ----------------

def test_report_guard_accepts_mechanical_template(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": []})
    rep = os.path.join(repo, ".audit_results", "reachable_vulnerabilities_report.md")
    # 机械模板形态: 标题 + 无全角括号占位 (四次 REFUSED 的实录形态)
    open(rep, "w").write(
        "## 三、修复建议与结论（主代理补充）\n"
        "> 本段由主代理补充；补充后**不得重跑 `--stage report`**。\n")
    import io as _io
    buf = _io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = bv.stage_report(repo)
    assert rc is None  # 守卫放行 (双形态识别), 不 REFUSED


def test_report_guard_refuses_edited_section(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": []})
    rep = os.path.join(repo, ".audit_results", "reachable_vulnerabilities_report.md")
    open(rep, "w").write(
        "## 三、修复建议与结论（主代理补充）\n"
        "### 修复建议\n1. 修复 A: 具体修复内容\n2. 修复 B\n")
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = bv.stage_report(repo)
    assert rc == 1  # 已编辑段落 → REFUSED
    assert "REPORT_REFUSED_OVERWRITE" in buf.getvalue()


# ---------------- D-3: R4 枚举建议映射 ----------------

def test_r4_enum_warning_has_suggestion(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": []})
    src = os.path.join(repo, ".audit_results", "r4_merged.json")
    json.dump({"hypotheses": [
        {"hypothesis_id": "H-1", "verdict": "NO_REACHABLE_CONFIRMED", "findings": [
            {"title": "x", "severity": "informational", "cwe": [], "evidence": "",
             "fix": "", "tracked_surfaces": [], "r3_link": None}]}]}, open(src, "w"))
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        n = bv.stage_r4_collect(repo, src)
    out = buf.getvalue()
    assert '"suggestion"' in out
    assert '"suggested": "reviewed_clean"' in out
    assert '"suggested": "low"' in out


# ---------------- D-4: post-resurrect advisory ----------------

def test_refutation_export_advisory(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": [
        _mk_cand(id="CAND-001", status="VERIFIED", verdict="REACHABLE",
                 evidence_grade="edge_proven", re_verify_gap="gap...",
                 refutation={"votes": 2, "refute_count": 0, "survived": True})]})
    r = we.export_script(repo, mode="refutation")
    assert "post_resurrect_advisory" in r
    assert r["post_resurrect_advisory"]["ids"] == ["CAND-001"]
    # 无陈旧 refutation 时无 advisory
    q = bv.load_queue(repo)
    q["candidates"][0].pop("refutation", None)
    bv.save_queue(repo, q)
    r2 = we.export_script(repo, mode="refutation")
    assert "post_resurrect_advisory" not in r2


# ---------------- D-5: 截断 key 集扩展 ----------------

def test_truncate_bracket_heads_kept():
    ev = "[G1 累积循环无预算] in_rtp_sdp.c:77-104 核实\n[G2 dedup 绕过] 实证\n次要描述文本"
    out = we._truncate_evidence(ev, budget=800)
    assert "G1 累积循环无预算" in out and "G2 dedup 绕过" in out


def test_truncate_verdict_head_kept():
    ev = "VERDICT: REACHABLE (CWE-190)...\n细节段落"
    out = we._truncate_evidence(ev, budget=800)
    assert "VERDICT: REACHABLE" in out


def test_truncate_all_minor_head_tail_splice():
    # 全 minor 多段 (方括号头不匹配 key 集) → 首尾拼接兜底, 永不切净
    # (gpac CAND-001/freetype CAND-002 双实录)
    ev = ("平文证据无任何段头\n[任意段一] 内容甲\n[任意段二] 内容乙\n"
          + "x" * 1200 + "结尾句")
    out = we._truncate_evidence(ev, budget=800)
    assert "平文证据无任何段头" in out and "结尾句" in out
    assert "无关键段头" in out


def test_truncate_single_segment_no_crash():
    ev = "单段无换行键头证据"
    out = we._truncate_evidence(ev, budget=800)
    assert "单段无换行键头证据" in out


# ---------------- D-6: tracked_surfaces 双形态 ----------------

def test_tracked_ids_dict_entries(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": [], "r4_findings": [
        {"hypothesis_id": "H-2", "tracked_surfaces": ["SURF-NET-001"],
         "hypothesis_tracked_surfaces": [
             {"surface_id": "SURF-DATA-010", "verdict": "clean", "evidence": "x"}]}]},
        surfaces={"surfaces": []})
    ids = bv._tracked_ids(repo, bv.load_queue(repo), [])
    assert "SURF-NET-001" in ids and "SURF-DATA-010" in ids


# ---------------- D-7: scope_diff 消费契约 ----------------

def test_scope_consumer_prefers_affected_dirs():
    import re as _re
    diff = {"changed": True,
            "affected_dirs": ["third_party/sub"],
            "changes": ["submodule third_party/sub: a -> b"]}
    # 消费逻辑内联复刻 (与 stage_workflow_script 同序): 优先 affected_dirs
    changed = list(diff.get("affected_dirs") or [])
    if not changed:
        def _chg_dir(x):
            if isinstance(x, str):
                m = _re.search(r"(?:submodule|dir) ([^:]+):", x)
                return m.group(1) if m else ""
            return str(x.get("path") or x.get("dir") or "")
        changed = [_chg_dir(x) for x in (diff.get("changes") or [])]
    assert changed == ["third_party/sub"]
    # fallback 路径: affected_dirs 空时解析字符串
    diff2 = {"changed": True, "affected_dirs": [], "changes": ["submodule third_party/sub: a -> b"]}
    changed2 = list(diff2.get("affected_dirs") or [])
    if not changed2:
        def _chg_dir2(x):
            m = _re.search(r"(?:submodule|dir) ([^:]+):", x)
            return m.group(1) if m else ""
        changed2 = [_chg_dir2(x) for x in (diff2.get("changes") or [])]
    assert changed2 == ["third_party/sub"]


# ---------------- D-9/D-10/D-11: 清单与先例新条目 ----------------

def test_checklist_new_entries_present():
    d = json.load(open(os.path.join(ROOT, "resources", "checklist_library.json")))
    by_id = {c["id"]: c for c in d["checklists"]}
    assert "CK-VENDORED-CONTRACT" in by_id
    assert any("对照组" in s for s in by_id["CK-EMPIRICAL-SCOPE"]["steps"])


def test_precedent_guard_subset_present_and_matches():
    import precedent_library as pl
    d = json.load(open(os.path.join(ROOT, "resources", "precedent_library.json")))
    assert any(p["id"] == "PREC-GUARD-SUBSET-001" for p in d["precedents"])
    hits = pl.match({"summary": "守卫封顶 上限已封 有界放大"})
    assert any(p["id"] == "PREC-GUARD-SUBSET-001" for p in hits)


# ---------------- D-8/D-12/D-14: 模板与注入文案 ----------------

def test_template_clauses_present():
    bh = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
    sm = open(os.path.join(ROOT, "task_templates", "surface_map_domain.md")).read()
    assert "canonical 字段形态" in bh and "sweep_records" in bh
    assert "域空条款" in sm and "empty_domain_reason" in sm


def test_resurrect_prompt_dimensions_present():
    p = we.resurrect_prompt({"id": "CAND-001", "evidence": "", "call_chain": []})
    assert "6. 绑定依赖库契约" in p
    assert "7. 守卫封顶类阻断" in p
    assert "8. verifier 未实测的平台维度" in p


# ---------------- 版本链 ----------------

def test_tooling_version_315():
    assert we.TOOLING_VERSION == "3.16"  # v3.16 版本链前进
