#!/usr/bin/env python3
"""SWR-V3-090: 端到端数据流集成测试（surface→hypothesis→queue→grade→assert→report）
用临时仓库模拟: 入口文件 + 含累积 sink 的被调文件 + 签名库命中。"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import surface_mapper, signature_matcher, signature_lib, evidence_ledger, harness_runner
import batch_verify as bv


def _mk_repo():
    tmp = tempfile.mkdtemp()
    # 入口: 请求处理 (含查询参数 → 文件打开, 触发 SIG-PATH-WHITELIST 的 open 形态)
    open(os.path.join(tmp, "entry.pl"), "w").write(
        "#!/usr/bin/perl\nsub main {\n  my $cfg = param('configdir');\n"
        "  my $path = '/etc/awstats/' . $cfg;\n"
        "  if ($path !~ /etc\\/awstats/) { die; }\n"
        "  open(F, \"<$path\") or die;\n}\n")
    open(os.path.join(tmp, "README.md"), "w").write("AWStats-like CGI tool\n")
    return tmp


def test_end_to_end(tmp_path=None):
    repo = _mk_repo()
    # 1) R1: 架构上下文 + 测绘任务书
    ctx = surface_mapper.build_architecture_context(repo)
    tasks = surface_mapper.gen_surface_tasks(repo, ctx)
    assert len(tasks) == 5  # v3.2: 4 域 + boundary 第五域
    # 2) 手写 1 个 surface (模拟测绘 agent 产出), 经校验器
    entry = os.path.join(repo, "entry.pl")
    surfaces = {"surfaces": [{
        "id": "S-001", "type": "network_endpoint", "name": "CGI query",
        "entry_points": [{"file": entry, "line": 3, "function": "main",
                          "evidence": {"snippet": "my $cfg = param('configdir');"}}],
        "taint_channels": ["query_string"],
        "downstream_hints": ["config load"],
        "trust_boundary": {"type": "unauthenticated_remote", "gate": "none"},
        "confidence": "high",
    }]}
    ok, errs = surface_mapper.validate_surfaces(surfaces)
    assert ok, errs
    # 3) R2: 索引 + 窗口 + 签名匹配 + 假设
    idx = signature_matcher.build_project_index(repo)
    sigs = signature_lib.load()["signatures"]
    hits = signature_matcher.match_signatures(surfaces["surfaces"], sigs, idx, depth=2)
    # entry.pl 含 "open(F, \"<$path\")" 与 "!~" 等 — 至少命中 PATH-WHITELIST
    sig_hits = {h["sig_id"] for h in hits}
    assert "SIG-PATH-WHITELIST-002" in sig_hits, f"hits={sig_hits}"
    hyps = signature_matcher.gen_hypotheses(hits, sigs)
    assert hyps["hypotheses"] or hyps["logic_hypotheses"]
    # 4) R3: 模拟 verifier 产出 (带边证据) → 分级 → 入队 → 断言
    hyp = (hyps["hypotheses"] or hyps["logic_hypotheses"])[0]
    verdict = {
        "id": "CAND-001",
        "hypothesis_id": hyp["id"],
        "verdict": "REACHABLE",
        "reachability_type": "DIRECT",
        "call_chain": ["entry.pl:3:main", "entry.pl:6:main", "entry.pl:6:main"],
        "call_chain_depth": 3,
        "edge_evidence": [
            {"edge": "entry.pl:3->entry.pl:6", "proof": "grep -n 'open(' entry.pl → line 6"},
            {"edge": "entry.pl:6->entry.pl:6", "proof": "同函数直通"}],
        "platform_precondition": None, "platform_evidence": None,
        "trust_boundary": {"channels": {"query_string": "逐通道验证: param() 直取未过滤"}},
        "gate": "AWSTATS_ENABLE_CONFIG_DIR", "gate_note": "未锚定子串校验",
        "claim_type": "xss", "evidence": "configdir 门禁未锚定", "cwe": ["CWE-22"],
    }
    grade, gerrs = evidence_ledger.grade_verdict(verdict)
    assert grade == "edge_proven", gerrs
    issues = evidence_ledger.check_preconditions(verdict)
    assert not [i for i in issues if i["severity"] == "blocking"], issues
    # 5) 入队 (merge) + 断言门禁 (xss 声称需实证 → 应报 empirical_required)
    queue = {"schema_version": "3.0", "candidates": []}
    evidence_ledger.commit(queue, {**verdict, "status": "VERIFIED", "evidence_grade": grade})
    ok_assert, violations = evidence_ledger.assert_ledger(queue)
    assert not ok_assert  # xss 声称未实证 → empirical_required
    gates = {v["gate"] for v in violations}
    assert "empirical_required" in gates
    # 6) R5: 触发判定 + 模拟实证确认 → 再断言
    cand = queue["candidates"][0]
    assert harness_runner.needs_harness(cand) is True
    harness_runner.apply_result(cand, {"status": "confirmed", "harness": "xss_path_sim"})
    ok2, v2 = evidence_ledger.assert_ledger(queue)
    # 7) 报告 (batch_verify report 需 .audit_results 队列; 用其函数)
    os.makedirs(os.path.join(repo, ".audit_results"), exist_ok=True)
    bv.save_queue(repo, queue)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_report(repo)
    rep = json.loads(buf.getvalue())
    assert rep["reachable"] == 1
    assert rep["evidence_grade_distribution"].get("empirically_confirmed") == 1
