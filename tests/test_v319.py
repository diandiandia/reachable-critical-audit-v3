#!/usr/bin/env python3
"""SWR-V3.19: V8 审计复盘缺陷修复测试 (8 用例)。

覆盖: correction_record 双形态 lenient (str 跳过零崩溃零改写 / dict 检查保留) /
verifier 步骤 0 缺陷可达性措辞 / ENVIRONMENT_PROBES sanitizer-dcheck 条目 /
复活第 9 维构建配置矩阵 / SKILL.md 条款 (D-3/D-4) / TOOLING 3.19。"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import evidence_ledger as el
import workflow_export as we


def _mk_queue(records):
    """records: per-candidate correction_record 形态列表。"""
    cands = []
    for i, cr in enumerate(records):
        cands.append({"id": f"CAND-{i:03d}", "source_file": "a.c",
                      "source_line": 1, "sink_type": "CWE-125",
                      "status": "VERIFIED", "verdict": "NEEDS_REVIEW",
                      "correction_record": cr})
    return {"candidates": cands, "target_kind": "library",
            "r4_findings": [], "escalated_signed_off": False}


def _assert(queue):
    return el.assert_ledger(
        queue,
        dispatched=[c["id"] for c in queue["candidates"]],
        surface_data={"total": 0, "tracked_ids": [], "mirror_pairs": []})


# ---- SWR-V3.19-001: 双形态 lenient ----


def test_correction_record_str_entries_no_crash():
    """纯 str 条目队列: 零崩溃, 零 adjudication warn (str 为注记形态)。"""
    q = _mk_queue([["主代理裁决注记 (str 形态)"],
                   ["另一条注记", "再一条"]])
    q2 = copy.deepcopy(q)
    ok, violations = _assert(q)
    assert q == q2, "lenient 检查不得改写队列任何字段"
    assert not any(v.get("gate") == "adjudication_unverified" for v in violations)


def test_correction_record_dict_check_preserved():
    """dict 条目检查保留: demote_to 无核验记录 → warn 照常触发。"""
    q = _mk_queue([[{"demote_to": "NEEDS_REVIEW", "reason": "x"}]])
    ok, violations = _assert(q)
    assert any(v.get("gate") == "adjudication_unverified" for v in violations)


def test_correction_record_mixed_lenient():
    """混形态队列 (V8 实录形态): 零崩溃, dict 检查与 str 跳过并存。"""
    q = _mk_queue([["注记 str", {"demote_to": "UNREACHABLE",
                                "reason": "实证证伪",
                                "adjudication_verification": "已核实"}],
                   [{"demote_to": "NEEDS_REVIEW", "reason": "缺核验"}]])
    q2 = copy.deepcopy(q)
    ok, violations = _assert(q)
    assert q == q2
    # 只有缺核验的 dict 条目触发 warn (CAND-002)
    warns = [v for v in violations if v.get("gate") == "adjudication_unverified"]
    assert len(warns) == 1 and warns[0]["ids"] == ["CAND-001"]


# ---- SWR-V3.19-002: 步骤 0 缺陷可达性措辞 ----


def test_verifier_prompt_defect_reachability_clause():
    ctx = {"file": "src/x.cc", "line": 1, "cwe": "CWE-125",
           "category": "?", "lang": "cpp", "language": "cpp",
           "sink": "arr[i] = payload[i];",
           "sources_regex": "recv|read|payload"}
    cand = {"id": "CAND-001", "source_file": "src/x.cc", "source_line": 1,
            "sink_type": "CWE-125", "attempt": 0}
    prompt = bv._build_prompt(cand, ctx, ROOT)
    assert "sink 可达 ≠ 缺陷可达" in prompt
    assert "结构性可达,\n缺陷未确证" in prompt


# ---- SWR-V3.19-005: ENVIRONMENT_PROBES 条目 ----


def test_environment_probes_sanitizer_dcheck():
    txt = open(os.path.join(ROOT, "harness_manuals",
                            "ENVIRONMENT_PROBES.md")).read()
    assert "sanitizer 构建变体与 dcheck 交互" in txt
    assert "dcheck_always_on=false" in txt
    from signature_lib import DEPROJECT_BLACKLIST
    for tok in DEPROJECT_BLACKLIST:
        assert tok not in txt, f"ENVIRONMENT_PROBES 含项目 token: {tok}"


# ---- SWR-V3.19-006: 复活第 9 维 ----


def test_resurrect_prompt_dimension_9():
    p = we.resurrect_prompt({"id": "CAND-001",
                             "evidence": "test evidence",
                             "call_chain": ["a", "b"]})
    assert "构建配置前提是否已枚举" in p
    assert "指针压缩/sandbox/特性开关/GC 模式" in p
    # 既有 8 维零变化抽查
    assert "承重前提是否真伪" in p and "死代码豁免是否误用" in p


# ---- SWR-V3.19-003/004: SKILL.md 条款 ----


def test_skillmd_v319_clauses():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "实质机制优先实证提示" in skill  # D-3
    assert "实证降级簿记" in skill          # D-4
    assert "correction_record[] 双形态" in skill or "双形态注记" in skill
    assert "v3.19 增量" in skill


# ---- 版本链 ----


def test_tooling_version_319():
    assert we.TOOLING_VERSION == "3.20"
