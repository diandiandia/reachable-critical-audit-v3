#!/usr/bin/env python3
"""SWR-V3.10: kernel 级项目首例审计复盘缺陷修复测试。

覆盖: tracked 三源(波次 glob/logic 组/假说级)/向后兼容/edge_gap 信号/
empirical 键名容错/r2_guard 波次回退/任务书文本断言(假说级 tracked/
empirical 指引/部署布局中立化/focus_sink 纯格式/upstream 搜索)/
parser_fuzz stub 指引/TOOLING_VERSION。"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "..", "tools"))

import batch_verify as bv
import r2_guard


def _mk_ar(tmp_path, files):
    """在临时项目下建 .audit_results 并写入 files。"""
    repo = str(tmp_path)
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for f, body in files.items():
        p = os.path.join(ar, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(body, str):
            with open(p, "w") as fh:
                fh.write(body)
        else:
            with open(p, "w") as fh:
                json.dump(body, fh)
    return repo


def _mk_surfaces(n):
    return [{"id": f"SURF-T-{i:03d}"} for i in range(n)]


# ---------------------------------------------------------------- SWR-001/003

def test_tracked_ids_multi_wave_and_logic(tmp_path):
    """多波批次: 主 + 分波 filter 文件 + logic 组三源并集。"""
    main = {"keep": [{"id": "H1", "surface_ids": ["SURF-T-000"]}],
            "drop": [{"id": "H2", "surface_ids": ["SURF-T-001"],
                      "reason": "x", "dropped_by": "filter", "scope_dependent": False}],
            "boundary_confirmations": [{"id": "H3", "surface_ids": ["SURF-T-002"],
                                        "confirmed_defense": "x"}]}
    wave2 = {"keep": [{"id": "H4", "surface_ids": ["SURF-T-003"]}],
             "drop": [], "boundary_confirmations": []}
    hyps = {"hypotheses": [{"id": "H5", "surface_ids": ["SURF-T-004"]}],
            "logic_hypotheses": [{"note": "n", "surface_ids": ["SURF-T-005", "SURF-T-006"]}]}
    repo = _mk_ar(tmp_path, {
        "r2_filter_result.json": main,
        "r2_filter_result_k2.json": wave2,
        "hypotheses.json": hyps})
    queue = {"candidates": [], "r4_findings": []}
    ids = bv._tracked_ids(repo, queue, _mk_surfaces(7))
    # filter 存在时 hypotheses 组不并入 (v3.9 优先语义保留), logic 组恒并入
    assert ids == ["SURF-T-000", "SURF-T-001", "SURF-T-002", "SURF-T-003",
                   "SURF-T-005", "SURF-T-006"], ids


def test_tracked_ids_hypothesis_tracked_surfaces(tmp_path):
    """假说级 tracked (reviewed_clean 审查触及面) 并入。"""
    repo = _mk_ar(tmp_path, {"r2_filter_result.json": {"keep": [], "drop": [],
                                                        "boundary_confirmations": []}})
    queue = {"candidates": [],
             "r4_findings": [{"hypothesis_id": "H1", "verdict": "reviewed_clean",
                              "findings": [],
                              "hypothesis_tracked_surfaces": ["SURF-T-000", "SURF-T-001"]}]}
    ids = bv._tracked_ids(repo, queue, _mk_surfaces(3))
    assert ids == ["SURF-T-000", "SURF-T-001"], ids


def test_tracked_ids_legacy_unchanged(tmp_path):
    """无分波/无 logic 的旧队列与 v3.9 行为一致 (三组并集)。"""
    fr = {"keep": [{"id": "H1", "surface_ids": ["SURF-T-000"]}],
          "drop": [{"id": "H2", "surface_ids": ["SURF-T-001"], "reason": "x",
                    "dropped_by": "filter", "scope_dependent": False}],
          "boundary_confirmations": []}
    repo = _mk_ar(tmp_path, {"r2_filter_result.json": fr})
    ids = bv._tracked_ids(repo, {"candidates": [], "r4_findings": []}, _mk_surfaces(2))
    assert ids == ["SURF-T-000", "SURF-T-001"], ids


def test_r4_collect_hypothesis_tracked_merge(tmp_path):
    """canonical R4 文件含假说级 tracked → collect 后落
    hypothesis_tracked_surfaces; 幂等; 有 finding 载体时不重复。"""
    payload = {"hypotheses": [
        {"hypothesis_id": "H1", "verdict": "reviewed_clean", "findings": [],
         "tracked_surfaces": ["SURF-T-000", "SURF-T-001"],
         "verdict_evidence": ["x"]},
        {"hypothesis_id": "H2", "verdict": "confirmed",
         "findings": [{"title": "f", "cwe": ["CWE-400"], "severity": "Low",
                       "call_chain": [], "evidence": "e", "fix": "f",
                       "tracked_surfaces": ["SURF-T-002"], "r3_link": None,
                       "claim_type": None, "empirical_result": None}],
         "tracked_surfaces": ["SURF-T-003"]}]}
    repo = _mk_ar(tmp_path, {"verify_queue.json": {"candidates": []}})
    # input_surface 存在时 R4_TRACKED_MISSING 守卫会校验 finding 的 tracked——
    # H2 finding 有 tracked, H1 无 finding, 不触发硬失败
    _mk_ar(tmp_path, {"input_surface.json": {"surfaces": _mk_surfaces(4)}})
    src = os.path.join(str(tmp_path), ".audit_results", "_r4.json")
    with open(src, "w") as fh:
        json.dump(payload, fh)
    bv.stage_r4_collect(repo, src)
    q = json.load(open(os.path.join(repo, ".audit_results", "verify_queue.json")))
    by_h = {f["hypothesis_id"]: f for f in q["r4_findings"]}
    assert sorted(by_h["H-1"]["hypothesis_tracked_surfaces"]) == ["SURF-T-000", "SURF-T-001"]
    # H2 有 finding 载体 → 假说级不重复收集
    assert "hypothesis_tracked_surfaces" not in by_h["H-2"]
    # 幂等: 重复 collect 不重复追加
    bv.stage_r4_collect(repo, src)
    q2 = json.load(open(os.path.join(repo, ".audit_results", "verify_queue.json")))
    by_h2 = {f["hypothesis_id"]: f for f in q2["r4_findings"]}
    assert len(by_h2["H-1"]["hypothesis_tracked_surfaces"]) == 2


# ---------------------------------------------------------------- SWR-004

def test_r2_guard_fidelity_wave_fallback(tmp_path, capsys):
    """主 hypotheses.json 缺失 → glob 波次文件合并反查, 无 WARN。"""
    fr = {"keep": [], "drop": [
        {"id": "H1", "reason": "x", "dropped_by": "filter",
         "scope_dependent": False}], "boundary_confirmations": []}
    wave = {"hypotheses": [{"id": "H1", "surface_ids": ["SURF-T-000"],
                            "sources": ["LLM"], "semantic_family": "x",
                            "cwe": ["CWE-400"], "hit_sites": [],
                            "hypothesis": "x", "checklist": []}]}
    ar = os.path.join(str(tmp_path), ".audit_results")
    os.makedirs(ar, exist_ok=True)
    fp = os.path.join(ar, "r2_filter_result.json")
    with open(fp, "w") as fh:
        json.dump(fr, fh)
    with open(os.path.join(ar, "_r2_hypotheses_k1.json"), "w") as fh:
        json.dump(wave, fh)
    old = sys.argv
    sys.argv = ["r2_guard.py", "fidelity", fp]
    try:
        rc = r2_guard.main(sys.argv)
    finally:
        sys.argv = old
    out = capsys.readouterr()
    assert rc == 0
    assert "WARN" not in out.err
    assert "WARN" not in out.out
    fixed = json.load(open(fp))
    assert fixed["drop"][0]["surface_ids"] == ["SURF-T-000"]


# ---------------------------------------------------------------- SWR-005

def test_render_empirical_standard_keys(tmp_path):
    """empirical 仅标准键 → 渲染回退出实测文本; 空 dict → 占位不抛异常。"""
    q = {"candidates": [{
        "id": "CAND-1", "status": "VERIFIED", "verdict": "REACHABLE",
        "evidence_grade": "empirically_confirmed", "claim_type": "crash",
        "cwe": ["CWE-125"], "sink_type": "CWE-125",
        "source_file": "a.c", "source_line": 1,
        "call_chain": ["a.c:1"], "call_chain_depth": 1,
        "evidence": "e",
        "empirical": {"verdict": "CONFIRMED_OOB",
                      "result": "ASAN heap-buffer-overflow READ 255",
                      "input": "slot 213 + len 255",
                      "harness": ".audit_results/empirical/x/",
                      "backfilled_by": "main-agent"}}],
        "r4_findings": []}
    repo = _mk_ar(tmp_path, {"verify_queue.json": q,
                             "input_surface.json": {"surfaces": _mk_surfaces(1)}})
    path = bv.render_report_md(repo)
    text = open(path).read()
    assert "outcome=CONFIRMED_OOB" in text
    assert "ASAN heap-buffer-overflow READ 255" in text
    assert "slot 213 + len 255" in text
    assert "harness=.audit_results/empirical/x/" in text


def test_render_empirical_empty_no_raise(tmp_path):
    q = {"candidates": [{
        "id": "CAND-1", "status": "VERIFIED", "verdict": "REACHABLE",
        "evidence_grade": "empirically_confirmed", "claim_type": "crash",
        "cwe": ["CWE-125"], "sink_type": "CWE-125",
        "source_file": "a.c", "source_line": 1,
        "call_chain": ["a.c:1"], "call_chain_depth": 1,
        "evidence": "e", "empirical": {}}],
        "r4_findings": []}
    repo = _mk_ar(tmp_path, {"verify_queue.json": q,
                             "input_surface.json": {"surfaces": _mk_surfaces(1)}})
    path = bv.render_report_md(repo)  # 空 dict 跳过渲染段且不抛异常即通过
    assert os.path.exists(path)


# ---------------------------------------------------------------- SWR-006

def test_collect_edge_gap_signal(tmp_path):
    """自报 edge_proven + 边数不足 → collect 后候选带 edge_gap 信号。"""
    repo = _mk_ar(tmp_path, {"verify_queue.json": {"candidates": [{
        "id": "CAND-1", "source_file": "a.c", "source_line": 1,
        "sink_type": "CWE-125", "status": "PENDING", "priority": 0}]}})
    ver = {"id": "CAND-1", "verdict": "REACHABLE",
           "reachability_type": "DIRECT",
           "call_chain": ["a.c:1", "a.c:2", "a.c:3", "a.c:4"],
           "call_chain_depth": 4,
           "evidence": "e", "evidence_grade": "edge_proven",
           "blocking_point": None,
           "edge_evidence": [{"edge": "a<-b", "proof": "p"}],
           "cwe": ["CWE-125"], "claim_type": "crash"}
    bv.stage_collect(repo, 0, {"CAND-1": ver})
    q = json.load(open(os.path.join(repo, ".audit_results", "verify_queue.json")))
    c = q["candidates"][0]
    assert c["evidence_grade"] == "static_only"
    assert c.get("edge_gap") and "疑似合并边" in c["edge_gap"]


# ---------------------------------------------------------------- SWR-007/008/010

def test_biz_hypothesis_v310_texts():
    p = os.path.join(ROOT, "task_templates", "biz_hypothesis.md")
    t = open(p).read()
    assert "tracked_surfaces" in t and "SWR-V3.10-002" in t
    assert "verdict 非 confirmed 或 findings 为空" in t
    assert "编译开关面" in t and "SWR-V3.10-008" in t
    assert "Low + 声称类" in t and "SWR-V3.10-007" in t


def test_hypothesis_filter_focus_sink_contract():
    p = os.path.join(ROOT, "task_templates", "hypothesis_filter.md")
    t = open(p).read()
    assert "纯 `path:line`" in t and "SWR-V3.10-010" in t


# ---------------------------------------------------------------- SWR-011

def test_verify_prompt_v310_steps(tmp_path):
    """verifier prompt 含 upstream 搜索步骤与路径格式条款。"""
    cand = {"id": "CAND-1", "source_file": "a.c", "source_line": 1,
            "sink_type": "CWE-125"}
    repo = _mk_ar(tmp_path, {"verify_queue.json": {"candidates": []}})
    ctx = bv._build_context(cand, project_root=repo)
    prompt = bv._build_prompt(cand, ctx, repo)
    assert "upstream 修复搜索" in prompt
    assert "快照落于修复" in prompt
    assert "相对项目根" in prompt
    assert "首发归属" in prompt and "非首发发现" in prompt


# ---------------------------------------------------------------- SWR-009/012/013

def test_shipped_config_prompt_build_switch():
    import workflow_export as we
    p = we.shipped_config_prompt({"name": "c1", "lang": "config",
                                  "project_root": "/x",
                                  "dirs": ["configs"]})
    assert "编译开关/特性键" in p
    assert "显式关闭" in p


def test_parser_fuzz_stub_doc():
    p = os.path.join(ROOT, "templates", "harness", "parser_fuzz_c.py")
    t = open(p).read()
    assert "有状态 sink 的最小 stub 复刻法" in t
    assert "无符号下溢语义保留" in t
    p2 = os.path.join(ROOT, "harness_manuals", "c.md")
    t2 = open(p2).read()
    assert "有状态 sink 的最小 stub 复刻法" in t2


def test_tooling_version_v310():
    # v3.13: TOOLING_VERSION 版本链前进 (SWR-V3.13-006)
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.18"
    sk = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "## 🆕 v3.10 增量" in sk


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# ---------------------------------------------------------------- SWR-V3.10.1-001

def test_confirmed_issues_verdict_filter(tmp_path):
    """非 confirmed 假说的复核记录不得进确认问题清单 (spec 口径:
    "R4 confirmed findings"; libjpeg-turbo 9 条复核 clean 记录渲染为
    "中"级问题的实录修复)。"""
    q = {"candidates": [],
         "r4_findings": [
             {"hypothesis_id": "H-1", "verdict": "reviewed_clean",
              "findings": [{"title": "复核 clean 记录", "severity": None,
                            "tracked_surfaces": ["SURF-T-000"]}]},
             {"hypothesis_id": "H-2", "verdict": "not_applicable",
              "findings": [{"title": "目标无认证机制", "severity": None,
                            "tracked_surfaces": ["SURF-T-000"]}]},
             {"hypothesis_id": "H-3", "verdict": "confirmed",
              "findings": [{"title": "真实 Medium 问题", "severity": "Medium",
                            "claim_type": "oom", "empirical_result": "CONFIRMED: x",
                            "tracked_surfaces": ["SURF-T-000"]}]},
         ]}
    repo = _mk_ar(tmp_path, {"verify_queue.json": q,
                             "input_surface.json": {"surfaces": _mk_surfaces(1)}})
    issues, dupes = bv._confirmed_issues(q, [])
    assert [i["key"] for i in issues] == ["H-3-F1"], issues
    assert dupes == []


def test_preserve_adjudication_titleless_keying(tmp_path):
    """SWR-V3.10.1-002: title 缺失形态按 finding_id 匹配——各 finding 保留
    各自字段, 不得被末条覆盖; 新值带 CONFIRMED 前缀时不回退旧值。"""
    old = {"findings": [
        {"finding_id": "f-1", "empirical_result": "CONFIRMED: A 测量",
         "claim_type": "unbounded"},
        {"finding_id": "f-2", "empirical_result": "CONFIRMED: B 测量",
         "claim_type": "oom"},
    ]}
    new = {"findings": [
        {"finding_id": "f-1", "empirical_result": "CONFIRMED: A 测量 v2",
         "claim_type": "unbounded"},
        {"finding_id": "f-2", "empirical_result": "CONFIRMED: B 测量 v2",
         "claim_type": "oom"},
    ]}
    bv._preserve_adjudication(old, new)
    # 各自保留各自的 empirical (v3.10.1-002 修复前: 全部被末条 f-2 覆盖)
    assert new["findings"][0]["empirical_result"] == "CONFIRMED: A 测量 v2"
    assert new["findings"][1]["empirical_result"] == "CONFIRMED: B 测量 v2"
    # 真实保留语义: 旧值带 CONFIRMED (主代理复验) + 新值裸文本 → 保留旧值
    old2 = {"findings": [{"finding_id": "f-3",
                          "empirical_result": "CONFIRMED: 主代理复验",
                          "empirical_verified_by": "main-agent"}]}
    new2 = {"findings": [{"finding_id": "f-3",
                          "empirical_result": "机制级静态核对"}]}
    bv._preserve_adjudication(old2, new2)
    assert new2["findings"][0]["empirical_result"] == "CONFIRMED: 主代理复验"
    assert new2["findings"][0]["empirical_verified_by"] == "main-agent"
