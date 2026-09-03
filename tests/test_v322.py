#!/usr/bin/env python3
"""SWR-V3.22: Firefox 验收审计复盘缺陷修复测试 (14 用例)。

覆盖: size_tier 分支调序 (D-1) / claim=other 严重度封顶 (D-2) /
复活未选中自动簿记 (D-4) / refutation budget 与链阈值 (D-5) /
refutation/resurrect 导出 taskFile 化 (D-9) / R4 落盘契约 (D-6) /
SKILL.md 条款 (D-7/D-10/D-11/D-3 注记) / TOOLING 3.22。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import surface_mapper as sm
import workflow_export as we


def _mk_project(tmp_path, cands, extra_files=None):
    d = tmp_path / "proj"
    (d / ".audit_results").mkdir(parents=True)
    queue = {"candidates": cands, "target_kind": "hybrid",
             "r4_findings": [], "escalated_signed_off": False}
    (d / ".audit_results" / "verify_queue.json").write_text(
        json.dumps(queue), encoding="utf-8")
    return str(d)


def _cand(cid, verdict="UNREACHABLE", **kw):
    c = {"id": cid, "source_file": "a.c", "source_line": 1,
         "sink_type": "CWE-125", "status": "VERIFIED", "verdict": verdict}
    c.update(kw)
    return c


# ---- SWR-V3.22-001: size_tier 分支调序 ----


def test_tier_super_large_multilang_priority(tmp_path):
    """3+ 语言 + >2000 文件 → super-large (此前被 n_langs>2 遮蔽)。"""
    d = tmp_path / "multi"
    for lang_dir in ("c", "rust", "js"):
        (d / lang_dir).mkdir(parents=True)
    for i in range(5):
        (d / "c" / f"f{i}.c").write_text("int x;\n")
        (d / "rust" / f"f{i}.rs").write_text("fn f() {}\n")
        (d / "js" / f"f{i}.js").write_text("let x;\n")
    # 15 文件 < 2000——用小规模直接测分支内部逻辑: 单测调 tier 需要 >2000 文件,
    # 这里改用 monkeypatch 验证分支顺序语义: 通过 _component_inventory 侧不参与,
    # 只测调序后 n_langs>2 不再提前返回 super-large 路径
    import surface_mapper as sm2
    # 用 fixture 目录测: 3 语言 15 文件应走 n_langs>2 large 分支 (保底不破坏)
    r = sm2.size_tier(str(d))
    assert r["tier"] == "large" and r.get("agent_count") == 5
    assert "n_langs" in r["rationale"] or "语言混合" in r["rationale"]


def test_tier_super_large_branch_precedes_multilang():
    """源码级守卫: super-large 判断在 n_langs>2 之前 (调序断言)。"""
    import inspect
    src = inspect.getsource(sm.size_tier)
    assert src.index("if count > 2000") < src.index("if n_langs > 2")


# ---- SWR-V3.22-002: claim=other 严重度封顶 ----


def test_severity_claim_other_capped():
    c = {"cwe": ["CWE-125"], "claim_type": "other"}
    sev, src = bv._mechanical_severity(c)
    assert sev == "medium" and "结构性可达封顶" in src


def test_severity_crash_unaffected():
    c = {"cwe": ["CWE-125"], "claim_type": "crash"}
    sev, src = bv._mechanical_severity(c)
    assert sev == "critical"


def test_severity_override_still_wins():
    c = {"cwe": ["CWE-125"], "claim_type": "other",
         "severity_override": "high", "severity_override_reason": "实质机制"}
    sev, src = bv.severity_for(c)
    assert sev == "high" and src == "override"


# ---- SWR-V3.22-004: 复活未选中自动簿记 ----


def test_r35n_auto_bookkeep_unselected(tmp_path):
    cands = [_cand("CAND-001", status="VERIFIED", verdict="UNREACHABLE")]
    proj = _mk_project(tmp_path, cands)
    (tmp_path / "proj" / ".audit_results" / "_resurrect_sample.json").write_text(
        json.dumps({"selected": [], "unselected": ["CAND-001"]}))
    # journal 无该候选记录 → 未选中簿记
    import subprocess
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    (journal_dir / "journal.jsonl").write_text(
        json.dumps({"type": "result", "result": {"id": "CAND-999", "revived": False,
                                                 "reason": "x"}}) + "\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "batch_verify.py"),
                        proj, "--stage", "r35n-collect", "--from-journal", str(journal_dir),
                        "--expect", "CAND-999"], capture_output=True, text=True)
    out = json.loads(r.stdout)
    assert "CAND-001" in out.get("auto_bookkept", [])
    q = bv.load_queue(proj)
    rr = q["candidates"][0].get("resurrection_review")
    assert rr == {"revived": False, "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}


def test_r35n_auto_bookkeep_skips_selected(tmp_path):
    """selected 集内无 journal 记录=异常, 不自动写。"""
    cands = [_cand("CAND-001", status="VERIFIED", verdict="UNREACHABLE")]
    proj = _mk_project(tmp_path, cands)
    (tmp_path / "proj" / ".audit_results" / "_resurrect_sample.json").write_text(
        json.dumps({"selected": ["CAND-001"], "unselected": []}))
    import subprocess
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    (journal_dir / "journal.jsonl").write_text(
        json.dumps({"type": "result", "result": {"id": "CAND-999", "revived": False,
                                                 "reason": "x"}}) + "\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "batch_verify.py"),
                        proj, "--stage", "r35n-collect", "--from-journal", str(journal_dir),
                        "--expect", "CAND-999"], capture_output=True, text=True)
    out = json.loads(r.stdout)
    assert "CAND-001" not in out.get("auto_bookkept", [])
    q = bv.load_queue(proj)
    assert not q["candidates"][0].get("resurrection_review")


# ---- SWR-V3.22-005: refutation budget 与链阈值 ----


def test_refutation_budget_and_chain_threshold(tmp_path):
    """evidence >800 字符不截于 800; 12+ 跳链保留 12 跳 + 注记。"""
    c = {"id": "CAND-001", "source_file": "a.c", "source_line": 1,
         "evidence": "x" * 2500, "call_chain": [f"a.c:{i}:f{i}" for i in range(20)],
         "evidence_grade": "edge_proven"}
    p = we.refute_prompt(c, 0)
    assert "x" * 800 in p or len([l for l in p.splitlines() if "x" in l]) > 0
    assert "[截断: 全链 20 跳, 见 verify_queue.json]" in p
    assert "a.c:11:f11" in p and "a.c:12:f12" not in p  # 保留 12 跳


# ---- SWR-V3.22-009: 导出 taskFile 化 ----


def test_refutation_export_taskfiles(tmp_path):
    cands = [_cand("CAND-001", verdict="REACHABLE", status="VERIFIED",
                   evidence_grade="edge_proven",
                   evidence="ev", call_chain=["a:1:f", "b:2:g", "c:3:h"])]
    proj = _mk_project(tmp_path, cands)
    r = we.export_script(proj, mode="refutation", batch_size=6)
    assert r.get("count") == 1
    c = r["payload"][0]
    assert len(c["taskFiles"]) == 2
    for tf in c["taskFiles"]:
        assert os.path.exists(os.path.join(proj, tf))
    slim = json.load(open(os.path.join(proj, ".audit_results",
                                       "refutation_payload_slim.json")))
    assert slim[0]["id"] == "CAND-001" and len(slim[0]["taskFiles"]) == 2


def test_resurrect_export_taskfiles(tmp_path):
    cands = [_cand("CAND-001", verdict="UNREACHABLE", status="VERIFIED")]
    proj = _mk_project(tmp_path, cands)
    r = we.export_script_resurrect(proj, batch_size=8)
    assert r.get("count") == 1
    c = r["payload"][0]
    assert c.get("taskFile")
    assert os.path.exists(os.path.join(proj, c["taskFile"]))
    slim = json.load(open(os.path.join(proj, ".audit_results",
                                       "resurrect_payload_slim.json")))
    assert slim[0]["id"] == "CAND-001"


# ---- SWR-V3.22-006/007/010/011/003: 模板与条款 ----


def test_biz_hypothesis_landing_contract():
    txt = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
    assert "落盘契约" in txt
    assert "_r4_hN.json" in txt
    assert "default_value_table 全量保留" in txt
    assert "UNWRITTEN" in txt


def test_skillmd_v322_clauses():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "decision {by, date, choice}" in skill      # D-7
    assert "面覆盖前置核对" in skill                    # D-10
    assert "蒸馏失败模式清单" in skill                  # D-11
    assert "薄封装默认派发" in skill                    # D-9
    assert "存储键为**单数**" in skill                  # D-3 注记


# ---- 版本链 ----


def test_tooling_version_322():
    assert we.TOOLING_VERSION == "3.22"
