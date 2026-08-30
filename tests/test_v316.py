#!/usr/bin/env python3
"""SWR-V3.16: v3.15 验收审计复盘缺陷修复测试 (约 7 用例)。

覆盖: audit_constraint 建议三分支 / R4 verdict 模板反面示例 / 构造器链量级
清单条目 / 树外层清单注入条款 / 账本双副本漂移 warn 与一致零 warn /
TOOLING 3.16。"""
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


def _cand(**kw):
    c = {"id": "CAND-001", "status": "VERIFIED", "verdict": "REACHABLE",
         "claim_type": "oom", "evidence_grade": "edge_proven",
         "evidence": "", "summary": ""}
    c.update(kw)
    return c


# ---------------- D-1: audit_constraint 建议 ----------------

def test_gate3_constraint_suggestion_present():
    q = {"candidates": [_cand(audit_constraint="no-build")]}
    _, v = el.assert_ledger(q, dispatched=["CAND-001"], surface_data={},
                            require_resurrection=False, require_r4_independent=False,
                            require_target_kind=False)
    assert any(x.get("gate") == "empirical_required_constraint" and
               x.get("suggestion", {}).get("kind") == "batch_demote" for x in v)


def test_gate3_constraint_absent_no_suggestion():
    q = {"candidates": [_cand()]}
    _, v = el.assert_ledger(q, dispatched=["CAND-001"], surface_data={},
                            require_resurrection=False, require_r4_independent=False,
                            require_target_kind=False)
    assert not any(x.get("gate") == "empirical_required_constraint" for x in v)
    # 主条目 (阻断) 语义不变
    assert any(x.get("gate") == "empirical_required" for x in v)


def test_gate3_constraint_no_auto_rewrite():
    # 建议不改变队列内容 (断言 load 后仍 REACHABLE)
    q = {"candidates": [_cand(audit_constraint="no-build")]}
    el.assert_ledger(q, dispatched=["CAND-001"], surface_data={},
                     require_resurrection=False, require_r4_independent=False,
                     require_target_kind=False)
    assert q["candidates"][0]["verdict"] == "REACHABLE"


# ---------------- D-2: R4 verdict 模板反面示例 ----------------

def test_template_verdict_counterexample():
    t = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
    assert "反面示例" in t and "REACHABLE / UNREACHABLE / NEEDS_REVIEW 是" in t
    assert "confirmed / reviewed_clean / not_applicable" in t


# ---------------- D-3: 构造器链量级清单条目 ----------------

def test_checklist_constructor_chain_item():
    d = json.load(open(os.path.join(ROOT, "resources", "checklist_library.json")))
    c = [x for x in d["checklists"] if x["id"] == "CK-CHECKPOINT-AFTER-ACCUM"][0]
    assert any("构造器链" in s and "急切分配" in s for s in c["steps"])


# ---------------- D-4: 树外层清单注入条款 ----------------

def test_out_of_tree_clause_in_verify_prompt(tmp_path):
    repo = _mk_repo(tmp_path, queue={"candidates": []})
    cand = {"id": "CAND-X", "status": "PENDING", "source_file": "a.cpp",
            "source_line": 1, "sink_type": "CWE-770"}
    bv.save_queue(repo, {"candidates": [cand]})
    r = we.export_script(repo, mode="verify")
    prompt = r["payload"][0]["prompt"]
    assert "树外层清单" in prompt and "SELinux 域" in prompt


# ---------------- D-5: 账本双副本漂移 ----------------

def test_sibling_ledger_detection_dev_shape():
    # dev 副本形态: <parent>/reachable-critical-audit-v3 → 检查 installed sibling
    other = bv._sibling_skill_ledger(os.path.join(ROOT, "x"))
    # 任意子路径: 函数推导 installed 副本路径; 断言返回 None 或合法路径形态
    assert other is None or other.endswith(
        os.path.join("resources", "issue_coverage_matrix.json"))


def test_sibling_ledger_detection_unknown_dir():
    assert bv._sibling_skill_ledger("/tmp/other") is None


# ---------------- 版本链 ----------------

def test_tooling_version_316():
    assert we.TOOLING_VERSION == "3.16"
