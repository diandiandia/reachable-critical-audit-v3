"""v3.40 (SWR-V3.40-001~007): Hadoop 验收复盘七修复守卫。

案例支撑: /root/hadoop/.audit_results/lessons.md「对 skill 的教训」1-7 条
(2026-09-10)。每条 SWR 至少一用例含反面分支。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import evidence_ledger as el

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _v(**kw):
    base = {"verdict": "REACHABLE", "call_chain": ["a:1", "b:2"],
            "edge_evidence": [{"edge": "a:1->b:2", "proof": "p"}],
            "evidence_grade": None}
    base.update(kw)
    return base


# ---------- SWR-V3.40-001: grade_verdict fidelity 分支 ----------

def test_grade_verdict_mechanism_not_confirmed():
    v = _v(empirical={"status": "confirmed", "fidelity": "mechanism"})
    g, errs = el.grade_verdict(v)
    assert g == "edge_proven", f"mechanism 档不得升 empirically_confirmed, got {g}"
    assert any("fidelity=mechanism" in e for e in errs), "须附机制档注记"


def test_grade_verdict_mechanism_no_edges_static():
    v = _v(empirical={"status": "confirmed", "fidelity": "mechanism"},
           edge_evidence=[])
    g, errs = el.grade_verdict(v)
    assert g == "static_only", "无边证据时按边证据逻辑复算 (不得滞留 edge_proven)"


def test_grade_verdict_mechanism_status_mechanism_only():
    # 反面分支: status 非 confirmed 集的 mechanism 档已由既有逻辑处理
    v = _v(empirical={"status": "mechanism_only", "fidelity": "mechanism"})
    g, _ = el.grade_verdict(v)
    assert g == "edge_proven"


def test_grade_verdict_real_target_and_default_regression():
    v1 = _v(empirical={"status": "confirmed", "fidelity": "real_target"})
    g1, _ = el.grade_verdict(v1)
    assert g1 == "empirically_confirmed"
    v2 = _v(empirical={"status": "confirmed"})  # fidelity 缺省 real_target
    g2, _ = el.grade_verdict(v2)
    assert g2 == "empirically_confirmed"
    v3 = _v(empirical={"status": "confirmed", "fidelity": "equivalent"})
    g3, _ = el.grade_verdict(v3)
    assert g3 == "empirically_confirmed"


# ---------- SWR-V3.40-002: verifier 任务书攻击者字节承载 ----------

def test_verifier_prompt_datacarry():
    src = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    assert "攻击者字节承载判定" in src
    assert "触发器链而非数据流链" in src
    assert "步骤 3.5" in src


# ---------- SWR-V3.40-003: checklist 49 + CK-SIBLING-FIX-AUDIT ----------

def test_checklist_49_sibling_fix_audit():
    d = json.load(open(os.path.join(
        ROOT, "assets", "resources", "checklist_library.json")))
    items = d["checklists"] if isinstance(d, dict) and "checklists" in d else d
    assert len(items) == 49, f"计数守卫: 期望 49, got {len(items)}"
    c = items[-1]
    assert c["id"] == "CK-SIBLING-FIX-AUDIT"
    assert c["family"] == "sibling-fix-audit"
    assert "source_lessons" in c and c["source_lessons"]


# ---------- SWR-V3.40-004: hypothesis_filter 位域证据义务 ----------

def test_filter_template_bitfield():
    txt = open(os.path.join(
        ROOT, "assets", "task_templates", "hypothesis_filter.md")).read()
    assert "位域/ordinal 越界判据的证据义务" in txt
    assert "枚举常量声明行" in txt
    assert "bit 范围" in txt


# ---------- SWR-V3.40-005: ENVIRONMENT_PROBES setuid 段 ----------

def test_env_probes_setuid():
    txt = open(os.path.join(
        ROOT, "assets", "harness_manuals", "ENVIRONMENT_PROBES.md")).read()
    assert "setuid 辅助二进制部署拓扑" in txt
    for kw in ("配置链", "二进制权限", "调用者身份", "数据目录族", "工作目录"):
        assert kw in txt, f"五要素缺 {kw}"
    # 去项目化: 手册段零项目名 (PROJECT_TOKENS 抽查形态)
    for bad in ("hadoop", "container-executor"):
        assert bad not in txt.split("setuid 辅助二进制部署拓扑")[1], \
            f"运行时手册携带项目名: {bad}"


# ---------- SWR-V3.40-006: hypothesis_filter 默认关方向 ----------

def test_filter_template_defaultoff():
    txt = open(os.path.join(
        ROOT, "assets", "task_templates", "hypothesis_filter.md")).read()
    assert "开关方向" in txt
    assert "feature 默认关" in txt
    assert "鉴权/校验 gate 默认关" in txt


# ---------- SWR-V3.40-007: r35-collect 实证回填候选扫描 ----------

def test_r35_collect_backfill_candidates():
    src = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    assert "empirical_backfill_candidates" in src
    assert "EMP_BACKFILL_MARKERS" in src
    assert "不自动改写" in src
