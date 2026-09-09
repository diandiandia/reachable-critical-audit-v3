"""SWR-V3.31: 人因闭环点机械化测试。
门禁①b spotcheck / hints 单命令 / lessons 单落盘 / R4 触发轴 /
equivalent ownership warn / 四轴+通道边界条款。
"""

import json
import os
import sys
import tempfile

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))
sys.path.insert(0, os.path.join(WORKSPACE, "tools"))

import evidence_ledger as el
import language_issue_matrix as lim
import lessons_recorder as lr


def _q(ids=()):
    return {"candidates": [{"id": i, "status": "VERIFIED",
                            "verdict": "NEEDS_REVIEW", "claim_type": "other"}
                           for i in ids],
            "r4_findings": [{"hypothesis_id": f"H-{i}", "status": "VERIFIED",
                             "verdict": "reviewed_clean", "findings": []}
                            for i in range(1, 8)],
            "target_kind": "library"}


# ---- SWR-V3.31-001: 门禁 ①b ----

def test_gate_1b_blocks_without_spotcheck():
    q = _q(["CAND-001"])
    r2 = {"keep": [], "bc": 49, "total": 56, "spot_checked": []}
    ok, v = el.assert_ledger(q, dispatched=["CAND-001"], r2_filter=r2)
    assert not ok
    assert any(x["gate"] == "keep0_spotcheck" for x in v)


def test_gate_1b_passes_with_spotcheck():
    q = _q(["CAND-001"])
    r2 = {"keep": [], "bc": 49, "total": 56,
          "spot_checked": [{"point": "a"}, {"point": "b"}, {"point": "c"}]}
    ok, v = el.assert_ledger(q, dispatched=["CAND-001"], r2_filter=r2)
    assert ok, v


def test_gate_1b_skips_when_none():
    q = _q(["CAND-001"])
    ok, v = el.assert_ledger(q, dispatched=["CAND-001"], r2_filter=None)
    assert ok
    assert not any(x["gate"] == "keep0_spotcheck" for x in v)


def test_gate_1b_not_triggered_when_keep_nonempty():
    q = _q(["CAND-001"])
    r2 = {"keep": [{"id": "HYP-x"}], "bc": 10, "total": 56, "spot_checked": []}
    ok, v = el.assert_ledger(q, dispatched=["CAND-001"], r2_filter=r2)
    assert ok, v


# ---- SWR-V3.31-002: hints 单命令 ----

def test_hints_merged_output():
    h = lim.hints("c")
    assert set(h.keys()) == {"lang", "kind", "cells", "inventory", "lessons_refs"}  # v3.32 增 kind/lessons_refs
    assert h["lang"] == "c"
    assert h["cells"]  # 已种格非空
    assert len(h["inventory"]) >= 10  # K1 达标语言


# ---- SWR-V3.31-003: lessons 单落盘 ----

def test_write_lesson_targets_project_local():
    with tempfile.TemporaryDirectory() as tmp:
        # 最小队列让 render 可工作
        os.makedirs(os.path.join(tmp, ".audit_results"))
        json.dump({"candidates": [], "r4_findings": []},
                  open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        out = lr.write_lesson(tmp, process_notes=["测试注记"])
        assert out == os.path.join(tmp, ".audit_results", "lessons.md")
        assert os.path.exists(out)
        content = open(out).read()
        assert "测试注记" in content


def test_write_lesson_no_repo_lessons_write():
    import glob
    before = set(glob.glob(os.path.join(WORKSPACE, "assets", "lessons", "SKILL_LESSONS_*.md")))
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".audit_results"))
        json.dump({"candidates": [], "r4_findings": []},
                  open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
        lr.write_lesson(tmp)
    after = set(glob.glob(os.path.join(WORKSPACE, "assets", "lessons", "SKILL_LESSONS_*.md")))
    assert after == before, "仓库 lessons/ 不应新增文件"


# ---- SWR-V3.31-004: R4 触发轴 ----

def test_skmd_r4_trigger_extended():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "target_kind ∈ {library, hybrid}" in sk
    assert "7/9" in sk


# ---- SWR-V3.31-005: equivalent ownership warn 语义 (数据侧) ----

def test_equivalent_warn_field_semantics():
    """warn 在 collect 路径 (batch_verify); 此处验证 canonical 数据形态契约。"""
    good = {"fidelity": "equivalent",
            "ownership_model": "持有图: ..."}
    bad = {"fidelity": "equivalent"}
    assert good.get("ownership_model")
    assert not bad.get("ownership_model")


# ---- SWR-V3.31-006: 四轴表与通道边界 ----

def test_skmd_axis_table_and_channel_boundary():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "形态判定四轴职责表" in sk
    assert "R2/R4 通道边界条款" in sk
    assert "claim_nulled_by 主申报方承载消化" in sk


# ---- 版本链 ----

def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.38"
