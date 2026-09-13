"""test_v342 — Keycloak 复盘六缺陷测试守卫 (SWR-V3.42-001..006)。

D-1 refutation 资格判定健壮化 / D-2 r4-collect 近似键诊断 /
D-3 verifier 分支级声称提示 / D-4 upstream 树内核实提示 /
D-5 filter drop 维度提示 / D-6 前缀级联提示。
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import workflow_export as we


# ---------- SWR-V3.42-001: refutation 资格判定 ----------

def test_refutation_empty_dict_eligible():
    """空 refutation dict 视为未复核 → 进 qualified。"""
    c = {"id": "X1", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven", "refutation": {}}
    assert not we._has_refutation_result(c)


def test_refutation_sigonly_eligible():
    """仅签收字段 (strengthened_verified_by) 视为未复核 → 进 qualified。"""
    c = {"id": "X2", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven",
         "refutation": {"strengthened_verified_by": "main-agent"}}
    assert not we._has_refutation_result(c)


def test_refutation_with_votes_excluded():
    """含 votes 视为已复核 → 排除。"""
    c = {"id": "X3", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven",
         "refutation": {"votes": 2, "refute_count": 0}}
    assert we._has_refutation_result(c)


def test_refutation_with_summary_excluded():
    """含 summary 视为已复核 → 排除 (r35-collect 双形态)。"""
    c = {"id": "X4", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven",
         "refutation": {"summary": "survived"}}
    assert we._has_refutation_result(c)


def test_refutation_missing_key_not_refuted():
    """无 refutation 键 = 未复核。"""
    c = {"id": "X5", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven"}
    assert not we._has_refutation_result(c)


def test_refutation_advisory_lists_empty_keys(tmp_path):
    """全排除空转时 advisory 含 empty_refutation_keys——
    空 refutation 键候选因其他条件 (status) 不 eligible 时的诊断。"""
    project = tmp_path / "proj"
    project.mkdir()
    q = {"candidates": [
        {"id": "A1", "status": "PENDING", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven", "refutation": {}},
        {"id": "A2", "status": "PENDING", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven",
         "refutation": {"strengthened_verified_by": "x"}},
    ], "target_kind": "application"}
    (project / ".audit_results").mkdir()
    json.dump(q, open(project / ".audit_results" / "verify_queue.json", "w"))
    r = we.export_script(str(project), mode="refutation")
    assert r["status"] == "WORKFLOW_NOTHING_TO_DO"
    assert r["qualified_total"] == 0
    assert sorted(r["empty_refutation_keys"]) == ["A1", "A2"]


def test_refutation_mixed_pool_skips_empty(tmp_path):
    """混合队列: 空 refutation 候选进池 (重新复核), 已复核候选不进。"""
    project = tmp_path / "proj"
    project.mkdir()
    q = {"candidates": [
        {"id": "B1", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven", "refutation": {}},
        {"id": "B2", "status": "VERIFIED", "verdict": "REACHABLE",
         "evidence_grade": "edge_proven",
         "refutation": {"votes": 2, "refute_count": 0}},
    ], "target_kind": "application"}
    (project / ".audit_results").mkdir()
    json.dump(q, open(project / ".audit_results" / "verify_queue.json", "w"))
    r = we.export_script(str(project), mode="refutation")
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    ids = [c["id"] for c in r["payload"]]
    assert "B1" in ids and "B2" not in ids


# ---------- SWR-V3.42-002: r4-collect 近似键诊断 ----------

def test_r4_collect_fieldname_hint(tmp_path, capsys):
    """裸对象用 hypothesis 而非 hypothesis_id → diagnosis 含映射提示。"""
    import batch_verify as bv
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".audit_results").mkdir()
    json.dump({"candidates": [], "target_kind": "application"},
              open(project / ".audit_results" / "verify_queue.json", "w"))
    bad = {"hypothesis": "H1", "verdict": "confirmed", "findings": []}
    json.dump(bad, open(project / ".audit_results" / "_r4_h1.json", "w"))
    old_argv = sys.argv[:]
    sys.argv = ["batch_verify.py", str(project), "--stage", "r4-collect",
                "--file", str(project / ".audit_results" / "_r4_h1.json")]
    try:
        bv.main()
    except SystemExit:
        pass  # pytest 环境下 cwd/argv 差异导致的退出容忍
    finally:
        sys.argv = old_argv
    err = capsys.readouterr().err
    assert "R4_COLLECT_WARNING" in err
    assert "字段名提示" in err and "hypothesis_id" in err


# ---------- SWR-V3.42-003: verifier 分支级声称提示 ----------

def test_verifier_prompt_branch_claim_hint(tmp_path):
    """verifier 任务书含分支级声称提示句。"""
    import batch_verify as bv
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".audit_results").mkdir()
    src = project / "srv"
    src.mkdir()
    (src / "T.java").write_text("public class T { void x() {} }")
    q = {"candidates": [
        {"id": "CAND-001", "source_file": "srv/T.java", "source_line": 1,
         "sink_type": "CWE-79", "status": "PENDING", "priority": 0}],
        "target_kind": "application"}
    json.dump(q, open(project / ".audit_results" / "verify_queue.json", "w"))
    c = q["candidates"][0]
    ctx = bv._build_context(c, str(project))
    prompt = bv._build_prompt(c, ctx, str(project))
    assert "分支级声称" in prompt
    assert "待实证子断言" in prompt


# ---------- SWR-V3.42-004/006: SKILL.md 提示句 ----------

def test_skillmd_upstream_verify_hint():
    """SKILL.md 公开面关联检索段含树内 commit 佐证提示。"""
    skill = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
    content = open(skill).read()
    assert "已修复/已包含" in content and "merge-base --is-ancestor" in content


def test_skillmd_prefix_cascade_hint():
    """SKILL.md 实证回填规范段含前缀级联提示。"""
    skill = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
    content = open(skill).read()
    assert "回填前缀语义" in content and "预判 gate 链级联" in content


# ---------- SWR-V3.42-005: filter 模板 drop 维度提示 ----------

def test_filter_template_drop_dimension_hint():
    """hypothesis_filter.md 排除判据段含信息暴露/跨信任域维度核对。"""
    tpl = os.path.join(os.path.dirname(__file__), "..", "assets",
                       "task_templates", "hypothesis_filter.md")
    content = open(tpl).read()
    assert "信息暴露/跨信任域维度核对" in content
    assert "R2 filter 与 R4 假说的判据差集" in content


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-x", "-q"])
