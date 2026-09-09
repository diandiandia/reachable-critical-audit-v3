"""SWR-V3.33: Servo 验收复盘十一缺陷修复测试。
merge 同 id 碰撞/域覆盖 warn / fidelity 路径+一致性 / r4 归位 warn /
去重承载终态 / hints 种格通道 / fixminer 路径信号 / SKILL.md 三条款 / 版本链。
"""

import json
import os
import subprocess
import sys
import tempfile

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))
sys.path.insert(0, os.path.join(WORKSPACE, "tools"))

import surface_mapper as sm
import r2_guard as rg
import language_issue_matrix as lim
import batch_verify as bv


def _surface(sid, typ, file_):
    return {"id": sid, "name": f"t {sid}", "type": typ, "lang": "rust",
            "entry_points": [{"file": file_, "line": 1,
                              "evidence": {"snippet": "x"}}],
            "taint_channels": ["t"], "trust_boundary": "unknown",
            "confidence": "high", "downstream_hints": []}


def _write(fn, data):
    p = os.path.join(fn)
    json.dump(data, open(p, "w"))
    return p


# ---- SWR-V3.33-001: merge 同 id 碰撞标注 ----

def test_merge_same_id_collision_conflict():
    with tempfile.TemporaryDirectory() as tmp:
        a = _write(os.path.join(tmp, "_r1_a.json"),
                   {"surfaces": [_surface("SURF-DATA-001", "data", "a.rs")]})
        b = _write(os.path.join(tmp, "_r1_b.json"),
                   {"surfaces": [_surface("SURF-DATA-001", "data", "b.rs")]})
        m = sm.merge_surfaces([a, b], tmp)
        ids = [c["surfaces"] for c in m["conflicts"]
               if c.get("resolution") == "kept-first-same-id"]
        assert ["SURF-DATA-001", "SURF-DATA-001"] in ids, m["conflicts"]
        # 去重行为不变: 面仅保留一条
        assert len(m["surfaces"]) == 1
        # 标注含来源与对账提示
        c = next(x for x in m["conflicts"]
                 if x.get("resolution") == "kept-first-same-id")
        assert len(c["sources"]) == 2 and "对账" in c.get("note", "")


def test_merge_no_same_id_collision_no_conflict():
    with tempfile.TemporaryDirectory() as tmp:
        a = _write(os.path.join(tmp, "_r1_a.json"),
                   {"surfaces": [_surface("SURF-DATA-001", "data", "a.rs")]})
        b = _write(os.path.join(tmp, "_r1_b.json"),
                   {"surfaces": [_surface("SURF-DATA-002", "data", "b.rs")]})
        m = sm.merge_surfaces([a, b], tmp)
        assert not any(c.get("resolution") == "kept-first-same-id"
                       for c in m["conflicts"])


# ---- SWR-V3.33-002: 域覆盖收口 warn ----

def test_merge_domain_unmapped_warn():
    with tempfile.TemporaryDirectory() as tmp:
        a = _write(os.path.join(tmp, "_r1_net.json"),
                   {"surfaces": [_surface("SURF-NET-001", "network", "n.rs")]})
        b = _write(os.path.join(tmp, "_r1_data.json"),
                   {"surfaces": [_surface("SURF-DATA-001", "data", "d.rs")]})
        m = sm.merge_surfaces([a, b], tmp)
        assert "process" in m.get("domain_unmapped", [])
        assert "storage" in m.get("domain_unmapped", [])


def test_merge_signed_empty_domain_exempt():
    with tempfile.TemporaryDirectory() as tmp:
        a = _write(os.path.join(tmp, "_r1_data.json"),
                   {"surfaces": [_surface("SURF-DATA-001", "data", "d.rs")]})
        b = _write(os.path.join(tmp, "_r1_storage.json"),
                   {"reviewed_by": "main-agent",
                    "empty_domain_reason": "目标无持久层文件读写面"})
        m = sm.merge_surfaces([a, b], tmp)
        assert "storage" not in m.get("domain_unmapped", [])
        assert "process" in m.get("domain_unmapped", [])


def test_merge_all_domains_no_warn():
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, dom in enumerate(("network", "data", "process", "storage")):
            files.append(_write(os.path.join(tmp, f"_r1_{dom}.json"),
                                {"surfaces": [_surface(f"SURF-{dom.upper()}-001",
                                                       dom, f"{dom}.rs")]}))
        m = sm.merge_surfaces(files, tmp)
        assert not m.get("domain_unmapped")


# ---- SWR-V3.33-003/004: fidelity 路径存在性 + surface_ids 一致性 ----

def _fidelity_setup(tmp, keep_entries, hyp_sids):
    fr = {"keep": keep_entries, "drop": [], "boundary_confirmations": []}
    frp = os.path.join(tmp, "r2_filter_result.json")
    json.dump(fr, open(frp, "w"))
    hp = os.path.join(tmp, "hypotheses.json")
    json.dump({"hypotheses": [
        {"id": e["id"], "surface_ids": hyp_sids[e["id"]],
         "sources": ["LLM"]} for e in keep_entries]}, open(hp, "w"))
    return frp, hp


def test_fidelity_focus_sink_missing_path_error():
    with tempfile.TemporaryDirectory() as tmp:
        frp, hp = _fidelity_setup(
            tmp, [{"id": "HYP-1", "surface_ids": ["S-1"],
                   "sources": ["LLM"], "focus_sink": "no/such/file.rs:10"}],
            {"HYP-1": ["S-1"]})
        errs = rg.check_focus_sinks(json.load(open(frp)), tmp)
        assert any("focus_sink 路径不存在" in e for e in errs)


def test_fidelity_focus_sink_valid_path_ok():
    with tempfile.TemporaryDirectory() as tmp:
        real = os.path.join(tmp, "real.rs")
        open(real, "w").write("fn main() {}\n")
        frp, hp = _fidelity_setup(
            tmp, [{"id": "HYP-1", "surface_ids": ["S-1"],
                   "sources": ["LLM"], "focus_sink": "real.rs:1"}],
            {"HYP-1": ["S-1"]})
        errs = rg.check_focus_sinks(json.load(open(frp)), tmp)
        assert errs == []


def test_fidelity_surface_ids_rewrite_error():
    with tempfile.TemporaryDirectory() as tmp:
        frp, hp = _fidelity_setup(
            tmp, [{"id": "HYP-1", "surface_ids": ["S-999"],
                   "sources": ["LLM"], "focus_sink": "real.rs:1"}],
            {"HYP-1": ["S-1"]})
        errs, mismatches = rg.check_surface_ids_consistency(
            json.load(open(frp)), json.load(open(hp)))
        assert mismatches == ["HYP-1"]
        assert any("原样继承" in e for e in errs)


def test_fidelity_surface_ids_verbatim_ok():
    with tempfile.TemporaryDirectory() as tmp:
        frp, hp = _fidelity_setup(
            tmp, [{"id": "HYP-1", "surface_ids": ["S-1"],
                   "sources": ["LLM"], "focus_sink": "real.rs:1"}],
            {"HYP-1": ["S-1"]})
        errs, mismatches = rg.check_surface_ids_consistency(
            json.load(open(frp)), json.load(open(hp)))
        assert errs == [] and mismatches == []


# ---- SWR-V3.33-005: r4-collect reviewed_clean Medium+ 归位 warn ----

def _r4_collect_setup(tmp, verdict, sev):
    os.makedirs(os.path.join(tmp, ".audit_results"), exist_ok=True)
    qp = os.path.join(tmp, ".audit_results", "verify_queue.json")
    json.dump({"candidates": [], "target_kind": "library"}, open(qp, "w"))
    fp = os.path.join(tmp, "_r4_in.json")
    json.dump({"hypotheses": [
        {"hypothesis_id": "H-1", "verdict": verdict,
         "findings": [{"title": "t", "severity": sev, "claim_type": None,
                       "tracked_surfaces": []}]}]}, open(fp, "w"))
    return qp, fp


def _r4_collect_run(tmp, fp):
    """stage_r4_collect 以 stdout 打印结果 JSON (CLI 形态), 捕获解析。"""
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_r4_collect(tmp, fp)
    raw = buf.getvalue()
    i = raw.find("{")
    return json.loads(raw[i:raw.rfind("}") + 1])


def test_r4_collect_reviewed_clean_medium_plus_warn():
    with tempfile.TemporaryDirectory() as tmp:
        qp, fp = _r4_collect_setup(tmp, "reviewed_clean", "Medium")
        r = _r4_collect_run(tmp, fp)
        assert r.get("reviewed_clean_medium_plus"), r
        assert r["reviewed_clean_medium_plus"][0]["hypothesis"] == "H-1"


def test_r4_collect_reviewed_clean_low_no_warn():
    with tempfile.TemporaryDirectory() as tmp:
        qp, fp = _r4_collect_setup(tmp, "reviewed_clean", "Low")
        r = _r4_collect_run(tmp, fp)
        assert not r.get("reviewed_clean_medium_plus")


def test_r4_collect_confirmed_no_warn():
    with tempfile.TemporaryDirectory() as tmp:
        qp, fp = _r4_collect_setup(tmp, "confirmed", "Medium")
        r = _r4_collect_run(tmp, fp)
        assert not r.get("reviewed_clean_medium_plus")


# ---- SWR-V3.33-006: 报告去重承载终态 ----

def test_confirmed_issues_carrier_need_review_self_list():
    queue = {"candidates": [{"id": "CAND-001", "verdict": "NEEDS_REVIEW"}],
             "r4_findings": [{"hypothesis_id": "H-1", "verdict": "confirmed",
                              "findings": [{"title": "t", "severity": "High",
                                            "claim_type": "oom",
                                            "empirical_result": "SOURCE_FACT: x",
                                            "tracked_surfaces": [],
                                            "r3_link": "CAND-001"}]}]}
    issues, dupes = bv._confirmed_issues(queue, queue["candidates"])
    assert dupes == []
    assert any(it.get("fid") == "H-1-F1" for it in issues)


def test_confirmed_issues_carrier_reachable_dedup():
    queue = {"candidates": [{"id": "CAND-001", "verdict": "REACHABLE"}],
             "r4_findings": [{"hypothesis_id": "H-1", "verdict": "confirmed",
                              "findings": [{"title": "t", "severity": "High",
                                            "claim_type": "oom",
                                            "empirical_result": "SOURCE_FACT: x",
                                            "tracked_surfaces": [],
                                            "r3_link": "CAND-001"}]}]}
    issues, dupes = bv._confirmed_issues(queue, queue["candidates"])
    assert dupes == [("H-1-F1", "CAND-001", "high")]
    assert not any(it.get("fid") == "H-1-F1" for it in issues)


# ---- SWR-V3.33-007: hints 种格通道 ----

def test_hints_matrix_channel_rust():
    h = lim.hints("rust")
    assert any(r.startswith("matrix/") for r in h["lessons_refs"]), \
        "rust 应检索到种格 source_lessons 条目 (D-4 证伪修复)"


def test_hints_unknown_lang_no_matrix_channel():
    h = lim.hints("lua")
    assert not h["cells"]
    # 种格通道零注入: 未种格语言不得出现 matrix/ 条目
    # (文件名通道命中历史 lessons 文件属既有行为, 不在本断言范围)
    assert not any(r.startswith("matrix/") for r in h["lessons_refs"])


# ---- SWR-V3.33-008: fixminer 路径信号 ----

def test_fixminer_path_signal_inclusion():
    import fixminer
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "config", "user.email", "t@t"],
                       check=True)
        subprocess.run(["git", "-C", tmp, "config", "user.name", "t"], check=True)
        open(os.path.join(tmp, "x.rs"), "w").write("fn main() {}\n")
        subprocess.run(["git", "-C", tmp, "add", "x.rs"], check=True)
        subprocess.run(["git", "-C", tmp, "commit", "-q", "-m", "tidy up"], check=True)
        # 路径信号: 安全敏感目录
        os.makedirs(os.path.join(tmp, "crypto"), exist_ok=True)
        open(os.path.join(tmp, "crypto", "key.rs"), "w").write("fn k() {}\n")
        subprocess.run(["git", "-C", tmp, "add", "crypto/key.rs"], check=True)
        subprocess.run(["git", "-C", tmp, "commit", "-q", "-m", "tidy up"], check=True)
        r = fixminer.run(tmp, since_days=1)
        assert r["status"] == "OK"
        assert any(c.get("path_signal") for c in r["fix_commits"]), \
            "路径信号 commit 应入选 (subject 净分为零)"
        # 精度护栏: 纯通用 fix 词 + 非敏感路径 不入选
        os.makedirs(os.path.join(tmp, "docs"), exist_ok=True)
        open(os.path.join(tmp, "docs", "readme.txt"), "w").write("x")
        subprocess.run(["git", "-C", tmp, "add", "docs/readme.txt"], check=True)
        subprocess.run(["git", "-C", tmp, "commit", "-q", "-m",
                        "refactor docs tests"], check=True)
        r = fixminer.run(tmp, since_days=1)
        assert all("readme" not in " ".join(c.get("files", []))
                   for c in r["fix_commits"])
        assert r.get("path_signal_count", 0) >= 1


def test_fixminer_no_git_backward_compat():
    r = subprocess.run([sys.executable,
                        os.path.join(WORKSPACE, "tools", "fixminer.py"),
                        "/tmp/nonexistent_dir_xyz_33"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert json.loads(r.stdout)["status"] == "NO_GIT"


# ---- SWR-V3.33-009/010/011: SKILL.md 三条款 ----

def test_skmd_v333_clauses():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "构建期生成代码" in sk and "SWR-V3.33-009" in sk
    assert "snippet 首行实际锚点" in sk and "SWR-V3.33-010" in sk
    assert "harness 依赖条款" in sk and "SWR-V3.33-011" in sk
    assert "SWR-V3.33-001" in sk and "SWR-V3.33-005" in sk and "SWR-V3.33-006" in sk


# ---- 版本链 ----

def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.38"
