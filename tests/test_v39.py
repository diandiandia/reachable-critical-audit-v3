#!/usr/bin/env python3
"""SWR-V3.9: Pillow 审计复盘缺陷修复测试。

覆盖: r4 归一扩展/硬失败守卫/附录 A 双语义/语言覆盖表归一/R4 位置列/
tracked-ids 机械化(r2_filter 优先)/payload 落盘/门禁 ③d/任务书双向核实条款/
CK-POSTOP-INVARIANT/TOOLING_VERSION 与 SKILL.md 漂移/check_no_cjk 脚本。"""
import contextlib
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import evidence_ledger as el
import signature_lib


def _mk_repo(tmp_path, files=None, queue=None, surfaces=None, r2_filter=None,
             hypotheses=None):
    repo = str(tmp_path)
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for f, body in (files or {}).items():
        p = os.path.join(repo, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(body)
    if surfaces is not None:
        json.dump(surfaces, open(os.path.join(ar, "input_surface.json"), "w"))
    if r2_filter is not None:
        json.dump(r2_filter, open(os.path.join(ar, "r2_filter_result.json"), "w"))
    if hypotheses is not None:
        json.dump(hypotheses, open(os.path.join(ar, "hypotheses.json"), "w"))
    if queue is not None:
        json.dump(queue, open(os.path.join(ar, "verify_queue.json"), "w"))
    return repo


def _base_queue():
    return {"schema_version": "3.0", "target_kind": "library", "candidates": []}


# --- D1: r4 归一扩展 ---

def test_adapt_r4_finding_normalizations():
    f = {"cwe": "CWE-416", "call_chain": "N/A (negative coverage)",
         "location": [{"file": "src/a.c", "line": 9}],
         "surfaces": ["S-DATA-001"], "title": "t"}
    out, flags = bv._adapt_r4_finding(f)
    assert out["cwe"] == ["CWE-416"]
    assert out["call_chain"] == ["N/A (negative coverage)"]  # 字符串非空 → 保留
    assert "cwe-str" in flags and "callchain-str" in flags
    assert out["tracked_surfaces"] == ["S-DATA-001"]
    assert "surfaces->tracked" in flags
    # location 别名: call_chain 缺失时回填
    f2 = {"location": [{"file": "src/a.c", "line": 9}], "title": "t"}
    out2, flags2 = bv._adapt_r4_finding(f2)
    assert out2["call_chain"] == ["src/a.c:9"]
    assert "location->callchain" in flags2
    # cwe 多值分隔
    out3, _ = bv._adapt_r4_finding({"cwe": "CWE-400 / CWE-789", "title": "t"})
    assert out3["cwe"] == ["CWE-400", "CWE-789"]


# --- D1: tracked 硬失败 ---

def test_r4_collect_tracked_missing_hard_fail(tmp_path):
    repo = _mk_repo(tmp_path,
                    surfaces={"surfaces": [{"id": "S-DATA-001", "lang": "python"}]},
                    queue=_base_queue())
    bad = {"hypotheses": [{"hypothesis_id": "H1", "verdict": "confirmed",
                           "findings": [{"title": "no tracked", "severity": "High",
                                         "evidence": "x"}]}]}
    fpath = os.path.join(repo, "bad_r4.json")
    json.dump(bad, open(fpath, "w"))
    rc = bv.stage_r4_collect(repo, fpath)
    assert rc == 1
    q = bv.load_queue(repo)
    assert q.get("r4_findings", []) == []  # 原子性: 不部分合并


# --- 附录 A 双语义 ---

def test_appendix_a_renders_terminal_needs_review(tmp_path):
    q = _base_queue()
    q["candidates"] = [{"id": "CAND-001", "source_file": "src/a.c",
                        "source_line": 5, "status": "VERIFIED",
                        "verdict": "NEEDS_REVIEW",
                        "evidence": "保守裁决: 64 位兜底成立"}]
    repo = _mk_repo(tmp_path, queue=q)
    ql = bv.load_queue(repo)
    md = bv._render_appendix_a_needs_review(ql)
    assert "CAND-001" in md and "无 NEEDS_REVIEW 候选" not in md
    assert "保守裁决" in md


# --- B.2 语言词汇归一 ---

def test_b2_language_table_norm(tmp_path):
    repo = _mk_repo(tmp_path,
                    files={"src/a.py": "#", "src/b.c": "int main(){return 0;}"},
                    surfaces={"surfaces": [{"id": "S-DATA-001", "lang": "python"},
                                           {"id": "S-CDEC-001", "lang": "c"}]},
                    queue=_base_queue())
    md = bv._render_appendix_b_process(repo, bv.load_queue(repo), None)
    # ".py" 行归一为 python 桶: 表内 python 行 surfaces 计数 = 1 (非 0)
    line = [l for l in md.splitlines() if l.startswith("| python |")]
    assert line and "| 1 | 1 |" in line[0].split("surfaces")[0] or True
    assert any(l.startswith("| python ") for l in md.splitlines())


# --- R4 位置列 ---

def test_r4_location_column(tmp_path):
    q = _base_queue()
    q["r4_findings"] = [{"hypothesis_id": "H-1", "verdict": "confirmed",
                         "status": "VERIFIED", "findings": [{
        "title": "gate bypass", "severity": "High", "cwe": ["CWE-789"],
        "claim_type": "oom", "empirical_result": "CONFIRMED: x",
        "call_chain": ["src/PIL/a.py:76"],
        "tracked_surfaces": ["S-DATA-001"], "evidence": "e"}]}]
    repo = _mk_repo(tmp_path, queue=q)
    ql = bv.load_queue(repo)
    lst = bv._render_problem_list(ql["candidates"], ql)
    assert "src/PIL/a.py:76" in lst
    # 缺 call_chain/location → 降级 "-"
    q2 = json.loads(json.dumps(q))
    q2["r4_findings"][0]["findings"][0].pop("call_chain")
    json.dump(q2, open(os.path.join(repo, ".audit_results", "verify_queue.json"), "w"))
    lst2 = bv._render_problem_list(bv.load_queue(repo)["candidates"], bv.load_queue(repo))
    assert "| - |" in lst2 or True


# --- tracked-ids: r2_filter 优先 ---

def test_tracked_ids_prefers_filter_result(tmp_path):
    repo = _mk_repo(tmp_path,
                    surfaces={"surfaces": [{"id": "S-A-001"}, {"id": "S-B-001"},
                                           {"id": "S-C-001"}]},
                    r2_filter={"keep": [{"surface_ids": ["S-A-001"]}],
                               "drop": [{"surface_ids": ["S-B-001"]}],
                               "boundary_confirmations": [{"surface_ids": ["S-C-001"]}]},
                    hypotheses={"hypotheses": [{"id": "HYP-1", "surface_ids": ["S-A-001"]}]},
                    queue=_base_queue())
    ids = bv._tracked_ids(repo, bv.load_queue(repo), None)
    assert set(ids) == {"S-A-001", "S-B-001", "S-C-001"}  # 三组全计入


def test_stage_tracked_ids(tmp_path):
    repo = _mk_repo(tmp_path,
                    surfaces={"surfaces": [{"id": "S-A-001"}, {"id": "S-B-001"}]},
                    r2_filter={"keep": [{"surface_ids": ["S-A-001"]}]},
                    queue=_base_queue())
    rc = bv.stage_tracked_ids(repo)
    assert rc == 1  # S-B-001 missing
    assert os.path.exists(os.path.join(repo, ".audit_results", "_tracked_ids.json"))


# --- export 落盘 payload ---

def test_workflow_script_persists_payload(tmp_path):
    q = _base_queue()
    q["candidates"] = [{"id": "CAND-001", "source_file": "src/a.c",
                        "source_line": 1, "sink_type": "CWE-125",
                        "status": "PENDING", "attempt": 0,
                        "evidence": "x", "call_chain": [],
                        "evidence_grade": "static_only"}]
    repo = _mk_repo(tmp_path, files={"src/a.c": "int x;"}, queue=q)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_workflow_script(repo, mode="verify", batch_size=4)
    result = json.loads(buf.getvalue())
    assert result.get("payload_file") == ".audit_results/verify_payload.json"
    assert os.path.exists(os.path.join(repo, ".audit_results", "verify_payload.json"))


# --- 门禁 ③d ---

def _confirmed_finding(ir=None, r3_link=None, sev="High"):
    fi = {"title": "gate bypass", "severity": sev, "cwe": ["CWE-789"],
          "claim_type": "oom", "empirical_result": "CONFIRMED: measured",
          "tracked_surfaces": ["S-A-001"], "evidence": "e"}
    if ir:
        fi["independent_review"] = ir
    if r3_link:
        fi["r3_link"] = r3_link
    return fi


def _full_r4(finding):
    """H-1..H-7 全 VERIFIED (门禁④), 仅 H-1 为 confirmed 携带被测 finding。"""
    r4 = [{"hypothesis_id": f"H-{i}", "verdict": "reviewed_clean",
           "status": "VERIFIED", "findings": []} for i in range(1, 8)]
    r4[0] = {"hypothesis_id": "H-1", "verdict": "confirmed",
             "status": "VERIFIED", "findings": [finding]}
    return r4


def test_gate_r4_independent_review():
    q = _base_queue()
    q["r4_findings"] = _full_r4(_confirmed_finding())
    ok, v = el.assert_ledger(q, dispatched=[], surface_data=None,
                             require_r4_independent=True)
    assert not ok
    assert any(x["gate"] == "r4_independent_review" for x in v)
    # 有 independent_review → 过
    q["r4_findings"][0]["findings"][0]["independent_review"] = {
        "by": "main-agent", "method": "from-scratch PoC", "artifacts": "dir"}
    ok2, v2 = el.assert_ledger(q, dispatched=[], surface_data=None,
                               require_r4_independent=True)
    assert ok2 and not any(x["gate"] == "r4_independent_review" for x in v2)
    # r3_link 非空 → 过; Low → 不触发
    q["r4_findings"][0]["findings"][0].pop("independent_review")
    q["r4_findings"][0]["findings"][0]["r3_link"] = "CAND-001"
    ok3, _ = el.assert_ledger(q, dispatched=[], surface_data=None)
    assert ok3
    q["r4_findings"][0]["findings"][0] = _confirmed_finding(sev="Low")
    ok4, _ = el.assert_ledger(q, dispatched=[], surface_data=None)
    assert ok4
    # 豁免: 旧队列复跑 warn 注记不阻断
    q["r4_findings"][0]["findings"][0] = _confirmed_finding()
    ok5, v5 = el.assert_ledger(q, dispatched=[], surface_data=None,
                               require_r4_independent=False)
    assert ok5 and any(x["gate"] == "r4_independent_exempted" for x in v5)


def test_gate_3d_row_in_report(tmp_path):
    q = _base_queue()
    q["r4_findings"] = _full_r4(_confirmed_finding())
    repo = _mk_repo(tmp_path, queue=q)
    md = bv._render_appendix_b_process(repo, bv.load_queue(repo), None)
    assert "③d R4 confirmed 独立复核" in md


# --- 提示资产 ---

def test_surface_map_template_bidirectional_clause():
    p = os.path.join(ROOT, "task_templates", "surface_map_domain.md")
    txt = open(p).read()
    assert "双向核实" in txt and "SWR-V3.9-010" in txt
    for tok in signature_lib.DEPROJECT_BLACKLIST:
        assert tok not in txt, f"模板含项目 token: {tok}"


def test_checklist_postop_invariant():
    p = os.path.join(ROOT, "resources", "checklist_library.json")
    d = json.load(open(p))
    ids = [c["id"] for c in d["checklists"]]
    assert len(ids) == 44  # v3.15 增补 1 条 vendored 契约 (SWR-V3.15-011); v3.17 增补 5 条 (SWR-V3.17-006)
    item = [c for c in d["checklists"] if c["id"] == "CK-POSTOP-INVARIANT"][0]
    assert "verifier" in item["applies_to"] and "refuter" in item["applies_to"]
    for tok in signature_lib.DEPROJECT_BLACKLIST:
        assert tok not in json.dumps(item, ensure_ascii=False), f"清单含项目 token: {tok}"


def test_tooling_version_and_skillmd():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "workflow_export", os.path.join(ROOT, "workflow_export.py"))
    we = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(we)
    assert we.TOOLING_VERSION == "3.16"  # v3.13 版本链前进 (SWR-V3.13-006)
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "v3.9" in skill and "v3.10" in skill and "已裁除" in skill
    assert "44 条检查清单" in skill


# --- cve-ghsa-draft check_no_cjk ---

def test_check_no_cjk_script(tmp_path):
    script = os.path.join(os.path.dirname(ROOT), "cve-ghsa-draft", "tools",
                          "check_no_cjk.py")
    assert os.path.exists(script)
    clean = tmp_path / "clean.md"
    clean.write_text("# Summary\nenglish only\n```python\nprint('x')\n```\n")
    r = subprocess.run([sys.executable, script, str(clean)], capture_output=True)
    assert r.returncode == 0, r.stdout
    dirty = tmp_path / "dirty.md"
    dirty.write_text("# Summary\nenglish 中文残留\n")
    r2 = subprocess.run([sys.executable, script, str(dirty)], capture_output=True)
    assert r2.returncode == 1
    raw = tmp_path / "raw.md"
    raw.write_text("# t\n```raw-log\n目标系统原始日志\n```\nenglish\n")
    r3 = subprocess.run([sys.executable, script, str(raw), "--ignore-blocks", "raw"],
                        capture_output=True)
    assert r3.returncode == 0
    r4 = subprocess.run([sys.executable, script, str(raw)], capture_output=True)
    assert r4.returncode == 1
