#!/usr/bin/env python3
"""SWR-V3.17: 运行时/引擎形态能力补全测试 (约 21 用例)。

覆盖: 生成层注册表 (默认视图零行为变化/DSL 族/去项目化) /
scaled_caps 三档 / 清单族 5 条 / target_profile 签收契约 /
super-large 两阶段档 / containment 严重度管线 / 语义轴 tracked 并入 /
差分实证模板 / 模板与手册章节 / 版本链。"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import generation_registry as gr
import signature_matcher as sm
import surface_mapper as smap

# ---- SWR-V3.17-001: 生成层注册表 ----


def test_registry_default_view_equals_legacy():
    """默认视图与现 CODE_EXTENSIONS 逐位一致 (零行为变化)。"""
    assert gr.default_extensions() == sm.CODE_EXTENSIONS


def test_registry_merged_view_contains_dsl_and_generated():
    v = gr.merged_view()
    assert ".proto" in v and ".pb.cc" in v and ".pb.h" in v
    assert ".tq" not in v  # 项目专属 DSL 不入默认注册表 (三禁止①)


def test_registry_lang_family_and_provenance():
    assert gr.lang_family_for(".h") == ".c"
    assert gr.lang_family_for(".pb.cc") == ".c"
    assert gr.provenance_for(".pb.cc") == (".proto", "generated")
    assert gr.provenance_for(".proto") == (".proto", "dsl")
    assert gr.provenance_for(".tq") is None


def test_registry_profile_local_layer_signed_only(tmp_path):
    """generation_layers 仅签收后生效; 未签收 = 空 (零强制义务)。"""
    ar = tmp_path / ".audit_results"
    ar.mkdir()
    (ar / "target_profile.json").write_text(json.dumps({
        "recommended": {"generation_layers": [
            {"ext": ".tq", "lang_family": ".cpp", "generates": [".inc"]}]},
        "signed_by": None}))
    assert ".tq" not in gr.merged_view(str(tmp_path))
    (ar / "target_profile.json").write_text(json.dumps({
        "recommended": {"generation_layers": [
            {"ext": ".tq", "lang_family": ".cpp", "generates": [".inc"]}]},
        "signed_by": "main-agent"}))
    v = gr.merged_view(str(tmp_path))
    assert ".tq" in v and ".inc" in v
    assert gr.lang_family_for(".inc", str(tmp_path)) == ".cpp"


# ---- SWR-V3.17-007: scaled_caps ----


def test_scaled_caps_three_bands():
    assert sm.scaled_caps(100) == (60, 40, 300)     # 现状常量
    assert sm.scaled_caps(2000) == (60, 40, 300)
    assert sm.scaled_caps(2001) == (120, 60, 600)
    assert sm.scaled_caps(8000) == (120, 60, 600)
    assert sm.scaled_caps(8001) == (180, 80, 900)


def test_expand_window_default_caps_unchanged(tmp_path):
    """caps 缺省 = 现状常量路径 (旧调用方零变化)。"""
    f = tmp_path / "a.c"
    f.write_text("int foo(int x) { return x; }\n" * 5)
    entry = {"file": str(f), "line": 1}
    idx = {"foo": [{"file": str(f), "line": 1, "callee": "foo"}]}
    w = sm.expand_window(entry, idx)
    assert isinstance(w, list)


# ---- SWR-V3.17-006: 清单族 ----


def test_checklist_family_added():
    lib = json.load(open(os.path.join(ROOT, "resources",
                                      "checklist_library.json")))
    ids = [c["id"] for c in lib["checklists"]]
    assert len(ids) == 44
    for cid in ("CK-GC-WRITE-BARRIER", "CK-GC-ROOT-SCAN", "CK-TIER-TRANSITION",
                "CK-ALLOC-ESCAPE", "CK-GENERATED-CODE"):
        item = [c for c in lib["checklists"] if c["id"] == cid][0]
        assert item["family"] in ("runtime-memory-model", "generated-code")
        assert "verifier" in item["applies_to"] and "refuter" in item["applies_to"]


def test_checklist_family_no_bare_signal_words():
    """applicability_signals.text 禁裸词 (词边界纪律: 裸 gc/barrier 子串误配)。"""
    lib = json.load(open(os.path.join(ROOT, "resources",
                                      "checklist_library.json")))
    for c in lib["checklists"]:
        if c.get("family") not in ("runtime-memory-model", "generated-code"):
            continue
        sigs = (c.get("applicability_signals") or {}).get("text", [])
        for s in sigs:
            assert s.strip().lower() not in ("gc", "barrier", "collector",
                                             "root", "tier"), \
                f"{c['id']} 含裸信号词 {s!r}"


def test_checklist_family_deprojected():
    from signature_lib import DEPROJECT_BLACKLIST
    lib = json.load(open(os.path.join(ROOT, "resources",
                                      "checklist_library.json")))
    for c in lib["checklists"]:
        if c.get("family") not in ("runtime-memory-model", "generated-code"):
            continue
        blob = json.dumps(c, ensure_ascii=False)
        for tok in DEPROJECT_BLACKLIST:
            assert tok not in blob, f"{c['id']} 含项目 token: {tok}"


# ---- SWR-V3.17-008: target_profile 签收契约 ----


def test_target_profile_recommend_and_write(tmp_path):
    (tmp_path / "engine.c").write_text("int main(){return 0;}\n")
    (tmp_path / "README.md").write_text(
        "an interpreter and a virtual machine with bytecode compiler and sandbox\n")
    out = subprocess.run([sys.executable,
                          os.path.join(ROOT, "tools", "target_profile.py"),
                          str(tmp_path), "--write"],
                         capture_output=True, text=True)
    assert out.returncode == 0
    r = json.loads(out.stdout)
    assert r["recommended"]["surface_model"] == "semantic"
    assert r["recommended"]["containment_default"] == "process_sandbox"
    prof = json.load(open(tmp_path / ".audit_results" / "target_profile.json"))
    assert prof["signed_by"] is None  # 未签收占位


def test_load_target_profile_signed_vs_unsigned(tmp_path):
    ar = tmp_path / ".audit_results"
    ar.mkdir()
    assert gr.load_target_profile(str(tmp_path))["surface_model"] == "entry"
    (ar / "target_profile.json").write_text(json.dumps({
        "recommended": {"surface_model": "semantic",
                        "containment_default": "process_sandbox"},
        "signed_by": None}))
    assert gr.load_target_profile(str(tmp_path))["surface_model"] == "entry"
    (ar / "target_profile.json").write_text(json.dumps({
        "recommended": {"surface_model": "semantic"},
        "overrides": {"containment_default": "language"},
        "signed_by": "main-agent"}))
    prof = gr.load_target_profile(str(tmp_path))
    assert prof["surface_model"] == "semantic"
    assert prof["containment_default"] == "language"


# ---- SWR-V3.17-002: super-large 两阶段档 ----


def _mk_files(root, n):
    root.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        d = root / f"comp{i % 3}"
        d.mkdir(exist_ok=True)
        (d / f"f{i}.c").write_text("int x;\n")


def test_size_tier_super_large(tmp_path):
    _mk_files(tmp_path / "repo", 2100)
    t = smap.size_tier(str(tmp_path / "repo"))
    assert t["tier"] == "super-large"
    assert t["two_phase"] is True
    assert t["components"] and all("file_count" in c for c in t["components"])


def test_size_tier_large_unchanged(tmp_path):
    _mk_files(tmp_path / "repo", 600)
    t = smap.size_tier(str(tmp_path / "repo"))
    assert t["tier"] == "large"
    assert t["two_phase"] is False and t["components"] == []


# ---- SWR-V3.17-003: containment 严重度管线 ----


def _cand(cwe=None, claim_type=None, containment=None, override=None):
    c = {"source_file": "x.cc", "source_line": 1}
    if cwe:
        c["cwe"] = cwe
    if claim_type:
        c["claim_type"] = claim_type
    if containment:
        c["containment"] = containment
    if override:
        c["severity_override"] = override
        c["severity_override_reason"] = "test"
    return c


def test_severity_containment_adjustment():
    assert bv.severity_for(_cand(cwe=["CWE-787"]))[0] == "critical"  # 零变化
    assert bv.severity_for(_cand(cwe=["CWE-787"], containment="process_sandbox"))[0] == "high"
    assert bv.severity_for(_cand(cwe=["CWE-787"], containment="language"))[0] == "high"
    # language 只降 critical: high 不动
    assert bv.severity_for(_cand(cwe=["CWE-89"], containment="language"))[0] == "high"
    assert bv.severity_for(_cand(cwe=["CWE-787"], containment="hardware_isolated"))[0] == "medium"
    # medium 封底不降
    assert bv.severity_for(_cand(cwe=["CWE-79"], containment="process_sandbox"))[0] == "medium"
    # override 绝对优先
    assert bv.severity_for(_cand(cwe=["CWE-787"], containment="process_sandbox",
                                 override="critical"))[0] == "critical"
    # 来源串携带 containment
    sev, src = bv.severity_for(_cand(cwe=["CWE-787"], containment="process_sandbox"))
    assert "containment:process_sandbox" in src


def test_derive_containment(tmp_path):
    v_explicit = {"containment": "process_sandbox"}
    assert bv._derive_containment(v_explicit, {"id": "C1"}, str(tmp_path)) == "process_sandbox"
    # 非法值 → 无 profile 时 none (warn 到 stderr)
    assert bv._derive_containment({"containment": "bogus"}, {"id": "C2"},
                                  str(tmp_path)) == "none"
    # 签收 profile → 缺省推导
    ar = tmp_path / ".audit_results"
    ar.mkdir()
    (ar / "target_profile.json").write_text(json.dumps({
        "recommended": {"containment_default": "process_sandbox"},
        "signed_by": "main-agent"}))
    assert bv._derive_containment({}, {"id": "C3"}, str(tmp_path)) == "process_sandbox"


def test_collect_lands_containment(tmp_path):
    ar = tmp_path / ".audit_results"
    ar.mkdir()
    queue = {"candidates": [{"id": "CAND-001", "source_file": "a.c",
                             "source_line": 1, "sink_type": "CWE-787",
                             "status": "PENDING", "priority": 0}]}
    (ar / "verify_queue.json").write_text(json.dumps(queue))
    v = {"verdict": "REACHABLE", "reachability_type": "DIRECT",
         "call_chain": ["a", "b", "c"], "call_chain_depth": 3,
         "evidence": "x", "evidence_grade": "edge_proven", "blocking_point": None,
         "claim_type": "crash", "containment": "process_sandbox"}
    bv.stage_collect(str(tmp_path), "b1", {"CAND-001": v})  # print 契约, 无返回值
    q = json.load(open(ar / "verify_queue.json"))
    assert q["candidates"][0]["containment"] == "process_sandbox"


def test_containment_suffix():
    assert bv._containment_suffix(_cand(containment="process_sandbox")) == " [沙箱收敛]"
    assert bv._containment_suffix(_cand(containment="none")) == ""
    assert bv._containment_suffix(_cand()) == ""


# ---- SWR-V3.17-005: 语义轴 tracked 并入 ----


def test_tracked_ids_semantic_axis_merged(tmp_path):
    ar = tmp_path / ".audit_results"
    ar.mkdir()
    (ar / "verify_queue.json").write_text(json.dumps({"candidates": []}))
    surfaces = {"surfaces": [
        {"id": "SURF-DATA-001", "name": "普通面"},
        {"id": "SURF-DATA-002", "name": "语义轴",
         "semantic_axis": {"namespace": "builtins",
                           "anchor_files": ["a.cc:1"], "cardinality": "10s"}},
    ]}
    tracked = bv._tracked_ids(str(tmp_path),
                              {"candidates": [], "r4_findings": []}, surfaces)
    assert "SURF-DATA-002" in tracked
    assert "SURF-DATA-001" not in tracked  # 非语义面零影响
    # 裸数组形态容忍
    tracked2 = bv._tracked_ids(str(tmp_path), {"candidates": []},
                               surfaces["surfaces"])
    assert "SURF-DATA-002" in tracked2


# ---- SWR-V3.17-004: 差分实证模板 ----


PROBE = os.path.join(ROOT, "templates", "harness", "differential_probe.py")


def test_differential_probe_usage():
    r = subprocess.run([sys.executable, PROBE], capture_output=True, text=True)
    assert r.returncode == 2


def test_differential_probe_divergent_and_consistent(tmp_path):
    c = tmp_path / "corpus"
    c.mkdir()
    (c / "in1").write_text("hello")
    base = [sys.executable, PROBE, "--configs", "2",
            "--cmd-0", "cat", "--cmd-1", "wc -c",
            "--corpus", str(c), "--compare", "output_hash"]
    r = subprocess.run(base, capture_output=True, text=True)
    assert r.returncode == 4
    out = json.loads(r.stdout)
    assert out["status"] == "DIVERGENT" and out["divergent"]
    base2 = [sys.executable, PROBE, "--configs", "2",
             "--cmd-0", "cat", "--cmd-1", "cat",
             "--corpus", str(c), "--compare", "output_hash"]
    r2 = subprocess.run(base2, capture_output=True, text=True)
    out2 = json.loads(r2.stdout)
    assert out2["status"] == "CONSISTENT"


def test_differential_template_registered():
    import harness_runner as hr
    assert "differential" in hr.TEMPLATES
    spec = hr.TEMPLATES["differential"]
    assert "any" in spec["langs"]
    assert os.path.exists(os.path.join(ROOT, spec["script"]))


# ---- P3 内容章节存在性 ----


def test_semantic_axis_template_section():
    t = open(os.path.join(ROOT, "task_templates",
                          "surface_map_domain.md")).read()
    assert "语义轴测绘段" in t and "semantic_axis" in t
    assert "组件约束段" in t and "{component_scope}" in t


def test_mixed_build_chapter():
    t = open(os.path.join(ROOT, "harness_manuals", "mixed_build.md")).read()
    assert "生成物重超大型构建" in t and "differential_probe.py" in t


# ---- 版本链 ----


def test_tooling_version_and_skillmd():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "workflow_export", os.path.join(ROOT, "workflow_export.py"))
    we = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(we)
    assert we.TOOLING_VERSION == "3.19"
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "v3.17 增量" in skill and "44 条检查清单" in skill
