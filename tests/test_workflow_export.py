"""W1/W2/W4 测试: workflow_export 脚本导出 + bump_attempt 升级 (REQ-V3-091/092/094)."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import batch_verify as bv
import workflow_export as we


def _mk_project(cands):
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    bv.save_queue(tmp, {"schema_version": "2.0", "candidates": cands})
    return tmp


def _cand(cid, status="PENDING", verdict=None, grade=None):
    c = {"id": cid, "file_path": f"src/{cid}.rs", "source_file": f"src/{cid}.rs",
         "source_line": 7, "line_number": 7, "sink_content": "buf.push(x)",
         "language": "rust", "cwe_id": "CWE-400", "category": "memory",
         "status": status}
    if verdict:
        c["verdict"] = verdict
    if grade:
        c["evidence_grade"] = grade
    return c


def test_export_verify_script():
    tmp = _mk_project([_cand("A-1"), _cand("A-2")])
    r = we.export_script(tmp, mode="verify", batch_size=4)
    assert r["status"] == "WORKFLOW_SCRIPT_READY" and r["count"] == 2
    script = open(os.path.join(tmp, ".audit_results", "workflow_verify.js")).read()
    assert "v3-verify-wave" in script and "pipeline(" in script
    # 嵌入 schema 是合法 JSON
    marker = "const VERDICT_SCHEMA = "
    i = script.index(marker)
    j = script.index("\n", i)
    schema = json.loads(script[i + len(marker):j].rstrip())
    assert set(schema["required"]) >= {"id", "verdict", "evidence_grade", "blocking_point"}
    # payload 与候选一一对应且 prompt 含 Mode W 契约 (无文件系统, 心跳契约属于 Mode A')
    assert [p["id"] for p in r["payload"]] == ["A-1", "A-2"]
    assert "Mode W 输出契约" in r["payload"][0]["prompt"]
    assert ".pending" not in r["payload"][0]["prompt"]
    assert r["payload"][0]["prompt"].startswith("你是一个 vulnerability-verifier")


def test_export_verify_empty_pool():
    tmp = _mk_project([_cand("A-1", status="VERIFIED", verdict="UNREACHABLE")])
    r = we.export_script(tmp, mode="verify")
    # v3.4.4 (SWR-V3.4.4-003): 空池也报 qualified_total (资格全集=0)
    assert r == {"status": "WORKFLOW_NOTHING_TO_DO", "mode": "verify",
                 "qualified_total": 0}


def test_export_refutation_pool_selection():
    cands = [
        _cand("R-1", status="VERIFIED", verdict="REACHABLE", grade="edge_proven"),
        _cand("R-2", status="VERIFIED", verdict="UNREACHABLE"),
        _cand("R-3", status="VERIFIED", verdict="REACHABLE", grade="static_only"),
        _cand("R-4", status="VERIFIED", verdict="REACHABLE", grade="empirically_confirmed"),
    ]
    tmp = _mk_project(cands)
    r = we.export_script(tmp, mode="refutation", batch_size=4)
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    # 仅 REACHABLE 且 grade>=edge_proven 入选; static_only/UNREACHABLE 排除
    assert sorted(p["id"] for p in r["payload"]) == ["R-1", "R-4"]
    script = open(os.path.join(tmp, ".audit_results", "workflow_refutation.js")).read()
    assert "N_REFUTERS = 2" in script and "KILL_THRESHOLD = 2" in script
    assert "v3-refutation-wave" in script


def test_refutation_payload_shape():
    tmp = _mk_project([_cand("R-1", status="VERIFIED", verdict="REACHABLE",
                             grade="edge_proven")])
    q = bv.load_queue(tmp)
    q["candidates"][0]["evidence"] = "ev"
    q["candidates"][0]["call_chain"] = ["a:1:f", "b:2:g"]
    bv.save_queue(tmp, q)
    r = we.export_script(tmp, mode="refutation")
    p = r["payload"][0]
    assert p["evidence"] == "ev" and p["call_chain"] == ["a:1:f", "b:2:g"]
    assert p["evidence_grade"] == "edge_proven"


def test_bump_attempt_increments():
    tmp = _mk_project([_cand("A-1")])
    bv.stage_bump_attempt(tmp, "A-1")
    q = bv.load_queue(tmp)
    c = q["candidates"][0]
    assert c["attempt"] == 1 and c["status"] == "PENDING"


def test_bump_attempt_escalates_at_max():
    tmp = _mk_project([_cand("A-1")])
    q = bv.load_queue(tmp)
    q["candidates"][0]["attempt"] = 2
    bv.save_queue(tmp, q)
    bv.stage_bump_attempt(tmp, "A-1")
    c = bv.load_queue(tmp)["candidates"][0]
    assert c["status"] == "ESCALATED"
    assert c["attempt"] == 3
    assert "escalated_reason" in c
    # 已升级后再次 bump 不再累加 attempt (幂等保护)
    bv.stage_bump_attempt(tmp, "A-1")
    c = bv.load_queue(tmp)["candidates"][0]
    assert c["attempt"] == 3


def test_bump_attempt_unknown_id_noop():
    tmp = _mk_project([_cand("A-1")])
    bv.stage_bump_attempt(tmp, "NOPE")
    assert bv.load_queue(tmp)["candidates"][0].get("attempt") is None


def test_cli_stage_workflow_script_entry():
    tmp = _mk_project([_cand("A-1")])
    rc = bv.stage_workflow_script(tmp, mode="verify", batch_size=2)
    assert rc == 0
    assert os.path.exists(os.path.join(tmp, ".audit_results", "workflow_verify.js"))


def test_cli_stage_workflow_script_empty():
    tmp = _mk_project([_cand("A-1", status="VERIFIED", verdict="UNREACHABLE")])
    bv.stage_workflow_script(tmp, mode="verify")
    assert not os.path.exists(os.path.join(tmp, ".audit_results", "workflow_verify.js"))


def test_refutation_prompt_truncation_marker():
    """v3.2.3 (Lua 审计): evidence 超 800 字符截断必须带 [截断] 标记
    (旧版静默 [:800] 曾在句子中段断句误导证伪者)。"""
    c = {"id": "CAND-X", "evidence": "x" * 1500,
         "call_chain": [f"f{i}:1" for i in range(12)],
         "claim_type": "oom", "summary": "", "evidence_grade": "edge_proven"}
    p = we.refute_prompt(c, 0)
    assert "[截断" in p
    assert "1500" in p
    assert "全链 12 跳" in p


def test_claim_type_enum_has_rce_and_other():
    """v3.2.3 (Lua 审计): claim_type 枚举补 rce/other——
    此前 env→dlopen 类声称无匹配类别被迫判 null。"""
    enum = we.VERDICT_SCHEMA["properties"]["claim_type"]["enum"]
    assert "rce" in enum and "other" in enum and "null" in enum


def test_refutation_payload_includes_checklist_section():
    """v3.6 (P1-1, B9 注入时点修复): refutation 时点 claim_type 已落盘 →
    _in_r5_semantic_space 可判定 → CK-EMPIRICAL-SCOPE 以 r5-semantic 绑定,
    家族清单段注入两个证伪者 prompt。puma 审计实录: verify 导出时 PENDING
    无信号恒空, 旧 refutation 分支不注入 → 清单零到达。"""
    tmp = _mk_project([_cand("R-1", status="VERIFIED", verdict="REACHABLE",
                             grade="edge_proven")])
    q = bv.load_queue(tmp)
    q["candidates"][0]["claim_type"] = "unbounded"
    q["candidates"][0]["evidence"] = "ev"
    bv.save_queue(tmp, q)
    r = we.export_script(tmp, mode="refutation")
    p = r["payload"][0]
    assert "家族检查清单" in p["prompts"][0]
    assert "家族检查清单" in p["prompts"][1]
    assert "CK-EMPIRICAL-SCOPE" in p["prompts"][0]
    assert "CK-EMPIRICAL-SCOPE" in p["prompts"][1]


def test_resurrect_prompt_no_checklist():
    """v3.6 (P1-1 负向防回退): resurrect 分支不注入清单段
    (复活者语境是找 UNREACHABLE 缺口, 非实证范围分级消费语境)。"""
    tmp = _mk_project([_cand("U-1", status="VERIFIED", verdict="UNREACHABLE",
                             grade="edge_proven")])
    q = bv.load_queue(tmp)
    q["candidates"][0]["claim_type"] = "unbounded"
    q["candidates"][0]["evidence"] = "ev"
    bv.save_queue(tmp, q)
    r = we.export_script_resurrect(tmp)
    for p in r["payload"]:
        assert "家族检查清单" not in p["prompt"]


def test_export_scripts_args_shape_tolerance():
    """v3.4.5 (SWR-V3.4.5-002): 四处 JS 模板含裸数组形态容忍包装
    (gRPC 审计: resurrect 裸数组派发失败实录)。"""
    tmp = _mk_project([_cand("A-1")])
    # verify (PENDING 候选)
    r = we.export_script(tmp, mode="verify")
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    script = open(os.path.join(tmp, ".audit_results", "workflow_verify.js")).read()
    assert "Array.isArray(args)" in script
    # refutation (REACHABLE+edge_proven 候选)
    q = bv.load_queue(tmp)
    q["candidates"][0].update({"status": "VERIFIED", "verdict": "REACHABLE",
                               "evidence_grade": "edge_proven"})
    bv.save_queue(tmp, q)
    r = we.export_script(tmp, mode="refutation")
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    script = open(os.path.join(tmp, ".audit_results", "workflow_refutation.js")).read()
    assert "Array.isArray(args)" in script
    # resurrect (需要 UNREACHABLE 声称类候选入池)
    q["candidates"][0].update({"status": "VERIFIED", "verdict": "UNREACHABLE",
                               "claim_type": "unbounded"})
    bv.save_queue(tmp, q)
    r = we.export_script_resurrect(tmp)
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    script = open(os.path.join(tmp, ".audit_results", "workflow_resurrect.js")).read()
    assert "Array.isArray(args)" in script
    # shipped-config
    r = we.export_script_shipped_config(tmp, [{"name": "web", "prompt": "p"}])
    assert r["status"] == "WORKFLOW_SCRIPT_READY"
    script = open(os.path.join(tmp, ".audit_results", "workflow_shipped_config.js")).read()
    assert "Array.isArray(args)" in script
