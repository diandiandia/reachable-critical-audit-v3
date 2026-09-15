"""test_v3_44 — K1 (linux kernel) 复盘修复测试 (SWR-V3.44-001..009)。

D-1a 复活簿记掩蔽洞 / D-1b 复活波导出纪律 / D-2 未合并补丁检索 /
D-3 签收级联+口径一致性 / D-4 fixminer 预期管理 / D-6 全覆盖子集清单+
配置分支语义核查 / D-7 多批次归档 / D-8 版本链 3.44 / D-9 批次开题四步。
(命名防撞: test_v344.py 为 v3.4.4 时代旧文件, 保留不动。)
"""
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


def _mk_fixture():
    """声称类未选中 / 非声称类未选中 / selected 有 journal 记录 三形态项目。"""
    tmp = tempfile.mkdtemp()
    ar = os.path.join(tmp, ".audit_results")
    os.makedirs(ar)
    queue = {"candidates": [
        {"id": "C-1", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "claim_type": "crash", "evidence": "sink 触发 crash"},
        {"id": "C-2", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "claim_type": "other", "evidence": "结构性可达"},
        {"id": "C-3", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "claim_type": "crash", "evidence": "sink 触发 crash"},
    ]}
    json.dump(queue, open(os.path.join(ar, "verify_queue.json"), "w"))
    json.dump({"selected": ["C-3"]},
              open(os.path.join(ar, "_resurrect_sample.json"), "w"))
    journal = os.path.join(tmp, "journal")
    os.makedirs(journal)
    with open(os.path.join(journal, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result", "result":
                            {"id": "C-3", "revived": False,
                             "reason": "九维复核维持 UNREACHABLE"}}) + "\n")
    return tmp, journal


# ---- SWR-V3.44-001: 声称类跳过自动簿记 (掩蔽洞修复) ----

def test_r35n_claim_like_not_masked(capsys):
    tmp, journal = _mk_fixture()
    rc = bv.stage_r35n_collect(tmp, journal, expect_ids=["C-3"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "claim_like_unreviewed" in out
    lines = [l for l in out.split("\n") if l.strip()]
    assert json.loads(lines[-1])["claim_like_unreviewed"] == ["C-1"]
    q = json.load(open(os.path.join(tmp, ".audit_results", "verify_queue.json")))
    by_id = {c["id"]: c for c in q["candidates"]}
    # 声称类未选中: 不簿记 → gate ③c 持续违规 (掩蔽洞关闭)
    assert "resurrection_review" not in by_id["C-1"]
    # 非声称类: 簿记照常
    assert by_id["C-2"]["resurrection_review"]["revived"] is False
    assert "复活抽样未选中" in by_id["C-2"]["resurrection_review"]["outcome"]
    # selected 有 journal: 真实落盘不受影响
    assert by_id["C-3"]["resurrection_review"]["revived"] is False
    assert "九维复核" in by_id["C-3"]["resurrection_review"]["outcome"]


# ---- SWR-V3.44-002: 复活波导出纪律条款 ----

def test_skillmd_resurrect_export_discipline():
    assert "export_script_resurrect" in SKILL
    assert "selected ⊇ 声称类集" in SKILL
    assert "SWR-V3.44-002" in SKILL


def _prompt():
    cand = {"id": "X", "source_file": "net/core/skbuff.c", "source_line": 1,
            "sink_type": "CWE-787", "summary": "越界写"}
    return bv._build_prompt(cand, bv._build_context(cand), "/tmp")


# ---- SWR-V3.44-003: 未合并补丁检索义务 ----

def test_verify_prompt_unmerged_patch_search():
    p = _prompt()
    assert "lore.kernel.org / openwall" in p
    assert "检索受限" in p
    assert "SWR-V3.44-003" in p


# ---- SWR-V3.44-004: 签收级联预推演 + 口径一致性 ----

def test_skillmd_signing_cascade_and_consistency():
    assert "签收前两级预推演" in SKILL
    assert "claim 重评级联" in SKILL
    assert "口径一致性" in SKILL
    assert "profile 派生缺省不适用" in SKILL


# ---- SWR-V3.44-005: fixminer 预期管理 ----

def test_skillmd_fixminer_expectation():
    assert "修复族密集目标" in SKILL
    assert "变体残留" in SKILL
    assert "SWR-V3.44-005" in SKILL


# ---- SWR-V3.44-006: 全覆盖子集清单 + 配置分支语义核查 ----

def test_verify_prompt_subset_and_config_branch():
    p = _prompt()
    assert "子集清单" in p
    assert "配置/构建前提分支的语义核查" in p
    assert "SWR-V3.44-006" in p


# ---- SWR-V3.44-007: 多批次归档约定 ----

def test_skillmd_batch_archive_convention():
    assert "同项目多批次续审" in SKILL
    assert "batch_<N>" in SKILL
    assert "SWR-V3.44-007" in SKILL


# ---- SWR-V3.44-008: 版本链 ----

def test_tooling_version_344():
    assert we.TOOLING_VERSION == "3.45"


def test_claim_like_same_source_as_gate():
    """is_claim_like 同源 (SWR-V3.15-002 单真相) —— 簿记分流与 gate ③c 一致。"""
    import evidence_ledger as el
    # 声称类判定与 gate 同源: crash claim → True, other → False
    assert el.is_claim_like({"claim_type": "crash"}) is True
    assert el.is_claim_like({"claim_type": "other"}) is False
    assert el.is_claim_like({"claim_type": None, "evidence": "oom 风险"}) is True


# ---- SWR-V3.44-009: 同项目多批次开题四步条款 ----

def test_skillmd_batch_opening_four_steps():
    assert "同项目多批次开题四步" in SKILL
    assert "--since 1825" in SKILL
    assert "五年窗口 recon" in SKILL
    assert "批次计划文档" in SKILL
    assert "SWR-V3.44-009" in SKILL


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-x", "-q"])
