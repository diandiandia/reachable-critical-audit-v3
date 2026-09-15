"""test_v3_45 — K2-K5 (linux kernel 批次 2-5) 复盘修复测试 (SWR-V3.45-001..016).

D-1 域计数前缀匹配+type 枚举 warn / D-2 r4-collect 键漂移 / D-3 auto_bookkept
覆写 / D-4 hypotheses 双形态渲染 / D-5 refuted 合规不告警 / D-6 引导面探针 /
D-7 claim_self_reported / D-8 containment 一致性 warn / D-9..D-16 文本条款。
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import surface_mapper as sm
import target_profile as tp
import workflow_export as we

SKILL = open(os.path.join(ROOT, "SKILL.md")).read()
BIZ = open(os.path.join(ROOT, "assets", "task_templates",
                        "biz_hypothesis.md")).read()
FILTER = open(os.path.join(ROOT, "assets", "task_templates",
                           "hypothesis_filter.md")).read()


def _mk_project(files=None):
    tmp = tempfile.mkdtemp()
    ar = os.path.join(tmp, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for rel, content in (files or {}).items():
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content)
    return tmp


# ---- SWR-V3.45-001 (D-1): 域计数前缀匹配 + type 枚举 warn ----

def test_merge_prefix_type_counting():
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    base = {"id": "S-1", "name": "x", "entry_points": [],
            "taint_channels": [], "trust_boundary": "local", "confidence": "high"}
    s = dict(base); s["type"] = "network_endpoint"
    f = os.path.join(ar, "_r1_a.json")
    json.dump([s], open(f, "w"))
    merged = sm.merge_surfaces([f], project_root=tmp)
    assert "network" not in merged.get("domain_unmapped", []), \
        "全名 type 应按前缀计入 network 域"


def test_validate_type_enum_warn():
    # 域前缀形态 (network_endpoint) 为历史兼容值不告警; 真非法值才告警
    s = {"id": "S-1", "name": "x", "type": "foo_bar",
         "entry_points": [], "taint_channels": [],
         "trust_boundary": "local", "confidence": "high"}
    ok, errs = sm.validate_surfaces([s], project_root=None)
    assert any("非枚举值" in e for e in errs)


# ---- SWR-V3.45-002 (D-2): r4-collect 键漂移 ----

def test_r4_hypothesis_key_diagnosis(capsys):
    # 整组缺失 (hypothesis 键) → 既有 v3.42 近似键诊断 (不自动改写)
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    json.dump({"candidates": []}, open(os.path.join(ar, "verify_queue.json"), "w"))
    merged = os.path.join(ar, "_r4_m.json")
    json.dump({"hypotheses": [{"hypothesis": "H3", "verdict": "reviewed_clean",
                               "findings": []}]}, open(merged, "w"))
    bv.stage_r4_collect(tmp, merged)
    err = capsys.readouterr().err
    assert "R4_COLLECT_WARNING" in err
    assert "字段名提示" in err


def test_r4_missing_hypothesis_id_warns(capsys):
    # 混合形态 (部分缺 id) → v3.45 新增告警 (K3-7 静默丢条目形态)
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    json.dump({"candidates": []}, open(os.path.join(ar, "verify_queue.json"), "w"))
    merged = os.path.join(ar, "_r4_m.json")
    json.dump({"hypotheses": [{"hypothesis_id": "H1", "verdict": "reviewed_clean",
                               "findings": []},
                              {"verdict": "reviewed_clean", "findings": []}]},
              open(merged, "w"))
    bv.stage_r4_collect(tmp, merged)
    err = capsys.readouterr().err
    assert "missing_hypothesis_id" in err


# ---- SWR-V3.45-003 (D-3): auto_bookkept 覆写 ----

def _r35n_project():
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    q = {"candidates": [{"id": "C-1", "status": "VERIFIED",
                         "verdict": "UNREACHABLE",
                         "claim_type": "other",
                         "evidence": "结构性可达",
                         "resurrection_review": {
                             "revived": False, "auto_bookkept": True,
                             "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}}]}
    json.dump(q, open(os.path.join(ar, "verify_queue.json"), "w"))
    journal = os.path.join(tmp, "journal")
    os.makedirs(journal)
    with open(os.path.join(journal, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result", "result":
                            {"id": "C-1", "revived": True,
                             "reason": "verifier 阻断论证两假前提"}}) + "\n")
    return tmp, journal


def test_r35n_real_decision_overwrites_bookkeep():
    tmp, journal = _r35n_project()
    rc = bv.stage_r35n_collect(tmp, journal, expect_ids=["C-1"])
    assert rc == 0
    q = json.load(open(os.path.join(tmp, ".audit_results", "verify_queue.json")))
    rr = q["candidates"][0]["resurrection_review"]
    assert rr["revived"] is True
    assert "auto_bookkept" not in rr


def test_r35n_real_decision_idempotent_skip():
    tmp, journal = _r35n_project()
    bv.stage_r35n_collect(tmp, journal, expect_ids=["C-1"])
    rc = bv.stage_r35n_collect(tmp, journal, expect_ids=["C-1"])
    assert rc == 0
    q = json.load(open(os.path.join(tmp, ".audit_results", "verify_queue.json")))
    rr = q["candidates"][0]["resurrection_review"]
    assert rr["revived"] is True
    assert "auto_bookkept" not in rr


# ---- SWR-V3.45-004 (D-4): hypotheses 双形态渲染 ----

def test_render_bare_list_hypotheses():
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    json.dump({"candidates": []}, open(os.path.join(ar, "verify_queue.json"), "w"))
    json.dump([{"id": "H-1"}, {"id": "H-2"}],
              open(os.path.join(ar, "hypotheses.json"), "w"))
    q = bv.load_queue(tmp)
    rep_path = bv.render_report_md(tmp, {"total_candidates": 0, "verified": 0,
                                    "pending": 0, "evidence_grade_distribution": {},
                                    "reachable": 0, "reachable_static_only_violations": [],
                                    "correction_records": 0})  # 不抛异常即通过
    out = open(rep_path).read()
    assert "假设: 2" in out


# ---- SWR-V3.45-005 (D-5): refuted 合规不告警 ----

def _warn_items(items):
    import io
    from contextlib import redirect_stderr
    buf = io.StringIO()
    with redirect_stderr(buf):
        bv._warn_r4_enums(items)
    return buf.getvalue()


def test_refuted_compliant_no_warn():
    items = [{"hypothesis_id": "H1", "verdict": "reviewed_clean",
              "findings": [{"title": "[refuted] xxx", "severity": "Low"}]}]
    assert "refuted_finding_in_list" not in _warn_items(items)


def test_refuted_noncompliant_warns():
    items = [{"hypothesis_id": "H1", "verdict": "reviewed_clean",
              "findings": [{"title": "[refuted] xxx", "severity": "Medium"}]}]
    assert "refuted_finding_in_list" in _warn_items(items)


# ---- SWR-V3.45-006 (D-6): 引导面探针 ----

def test_boot_probe_recommends_real_target():
    tmp = _mk_project()
    img = os.path.join(tmp, "arch", "arm64", "boot", "Image")
    os.makedirs(os.path.dirname(img), exist_ok=True)
    open(img, "w").write("")
    old_which = shutil.which
    shutil.which = lambda n: "/usr/bin/" + n
    try:
        r = tp.recommend(tmp)
    finally:
        shutil.which = old_which
    assert r["recommended"]["empirical_modes"] == ["real-target"]
    assert any(s["id"] == "S7" for s in r["signals"])


def test_boot_probe_empty_tree():
    tmp = _mk_project()
    r = tp.recommend(tmp)
    assert r["recommended"]["empirical_modes"] == []


# ---- SWR-V3.45-007 (D-7): claim_self_reported 归档 ----

def test_claim_self_reported_archived():
    entry = {}
    v = {"verdict": "UNREACHABLE", "claim_type": "crash"}
    # 直接调用 collect 内的落盘逻辑不可行 (需完整环境), 改为验证 grade/claim
    # 归档语义经 collect 全链: 用最小 journal 形态走 stage_collect
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    q = {"candidates": [{"id": "C-1", "status": "PENDING"}]}
    json.dump(q, open(os.path.join(ar, "verify_queue.json"), "w"))
    journal = os.path.join(tmp, "journal")
    os.makedirs(journal)
    with open(os.path.join(journal, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result", "result": {
            "id": "C-1", "verdict": "UNREACHABLE", "reachability_type": "DIRECT",
            "call_chain": ["a:1 f", "b:2 g"], "call_chain_depth": 2,
            "evidence": "x", "evidence_grade": "edge_proven",
            "blocking_point": None, "claim_type": "crash"}}) + "\n")
    verdicts = bv._extract_journal_verdicts(journal)
    assert "C-1" in verdicts
    bv.stage_collect(tmp, 0, verdicts)
    q2 = json.load(open(os.path.join(ar, "verify_queue.json")))
    c = q2["candidates"][0]
    assert c.get("claim_type") is None
    assert c.get("claim_self_reported") == "crash"


# ---- SWR-V3.45-008 (D-8): containment 一致性 warn ----

def test_containment_kernel_ctx_warns(capsys):
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    prof = {"recommended": {"containment_default": "process_sandbox"},
            "signed_by": "main-agent"}
    json.dump(prof, open(os.path.join(ar, "target_profile.json"), "w"))
    v = {"containment": None, "evidence": "写发生在 softirq 上下文"}
    c = {"id": "C-1"}
    got = bv._derive_containment(v, c, tmp)
    err = capsys.readouterr().err
    assert got == "process_sandbox"
    assert "SWR-V3.45-008" in err


def test_containment_clean_no_warn(capsys):
    tmp = _mk_project()
    ar = os.path.join(tmp, ".audit_results")
    prof = {"recommended": {"containment_default": "process_sandbox"},
            "signed_by": "main-agent"}
    json.dump(prof, open(os.path.join(ar, "target_profile.json"), "w"))
    v = {"containment": None, "evidence": "用户态进程"}
    c = {"id": "C-1"}
    bv._derive_containment(v, c, tmp)
    err = capsys.readouterr().err
    assert "SWR-V3.45-008" not in err


# ---- SWR-V3.45-009/010/011/012/013/014/015/016: 文本条款 ----

def test_d9_template_clauses():
    assert "非法值反例" in BIZ and "static_verified" in BIZ
    assert "散文意图映射" in BIZ and "reviewed_clean" in BIZ
    assert "面桥接" in BIZ and "coverage_note 声明新面" in BIZ


def test_d10_verifier_dimensions():
    assert "快照读/活体读" in open(os.path.join(ROOT, "tools",
        "batch_verify.py")).read()
    assert "生命周期/提交期 GC" in open(os.path.join(ROOT, "tools",
        "batch_verify.py")).read()
    assert "交付二进制核查" in open(os.path.join(ROOT, "tools",
        "batch_verify.py")).read()


def test_d11_resurrect_prompt():
    p = we.resurrect_prompt({"id": "C-1", "evidence": "x", "call_chain": []})
    assert "实证通道已开时" in p
    assert "行号 ±5 容差" in p


def test_d12_filter_progress():
    assert "进度摘要" in FILTER and "严禁长时间静默" in FILTER


def test_d13_dispatch_clause():
    assert "分片落盘条款" in SKILL and "严禁粘贴完整 JSON" in SKILL


def test_d14_hygiene():
    assert "工作区卫生检查" in SKILL and "git status --short" in SKILL


def test_d15_combo_window():
    assert "新机制×旧机制组合窗口" in SKILL


def test_d16_override_hint():
    assert "severity_override + severity_override_reason 落盘" in SKILL


# ---- 版本链 ----

def test_tooling_version():
    assert we.TOOLING_VERSION == "3.45"
