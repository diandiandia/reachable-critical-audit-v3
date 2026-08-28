"""v3.4.4 验收暴露缺陷修复批次测试 (SWR-V3.4.4-001..010)。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))

import tempfile

import checklist_binder
import precedent_library
import batch_verify as bv
import workflow_export as we
import lessons_recorder as lr


def _mk_project(cands):
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    json.dump({"schema_version": "3.0", "candidates": cands},
              open(os.path.join(tmp, ".audit_results", "verify_queue.json"), "w"))
    return tmp


def _cand(cid, status="PENDING", verdict=None, grade="static_only"):
    return {"id": cid, "status": status, "verdict": verdict,
            "evidence_grade": grade, "claim_type": None,
            "source_file": "x.js", "source_line": 1}


# ---- SWR-V3.4.4-001: 词边界匹配 ----
def test_signal_word_boundary():
    sig = {"text": ["ws"]}
    cand = {"lang": "javascript"}
    # "jws" 子串不得命中 (jsrsasign CAND-001 实测误配)
    assert checklist_binder._signals_ok(sig, cand,
                                        "KJUR.jws.JWS.verify token") is False
    # 独立 "ws" 词命中
    assert checklist_binder._signals_ok(sig, cand,
                                        "ws server frame handling") is True
    # "websocket" 内嵌 "ws" 不命中 (有独立 websocket 关键词兜底)
    assert checklist_binder._signals_ok(sig, cand, "websocket codec") is False
    # CJK 关键词保持子串语义
    assert checklist_binder._signals_ok({"text": ["无上限"]}, cand,
                                        "该路径无上限") is True
    # requires_lang 同样词边界: "c" 不得误配 "scala"
    assert checklist_binder._signals_ok({"requires_lang": ["c"]},
                                        {"lang": "scala"}, "") is False
    assert checklist_binder._signals_ok({"requires_lang": ["c"]},
                                        {"lang": "c"}, "") is True


def test_precedent_signal_word_boundary():
    p = {"applicability_signals": {"text": ["ws"]}}
    cand = {"lang": "javascript"}
    assert precedent_library._signals_ok(p, cand,
                                         "jws verify flow") is False
    assert precedent_library._signals_ok(p, cand, "ws frame") is True


# ---- SWR-V3.4.4-002: r4-collect 保留主代理裁决字段 ----
def test_r4_collect_preserves_adjudication():
    tmp = _mk_project([])
    f1 = {"hypothesis_id": "H7", "verdict": "confirmed",
          "findings": [{"title": "F5 pkey typo", "claim_type": None,
                        "claim_nulled_by": "main-agent-deployment-layout-correction",
                        "empirical_result": "CONFIRMED(src 笔误真实)",
                        "evidence": "原始证据 [主代理裁决 2026-08-21: 部署布局纠正]"}]}
    bv.stage_r4_collect(tmp, _wfile(tmp, f1))
    q = bv.load_queue(tmp)
    got = q["r4_findings"][0]["findings"][0]
    assert got["claim_type"] is None
    assert got["claim_nulled_by"] == "main-agent-deployment-layout-correction"

    # 重新 collect (agent 新产出带 claim_type=crash 与无标记 empirical)
    f2 = {"hypothesis_id": "H7", "verdict": "confirmed",
          "findings": [{"title": "F5 pkey typo", "claim_type": "crash",
                        "empirical_result": "plain text no marker",
                        "evidence": "新证据 (无裁决段)"}]}
    bv.stage_r4_collect(tmp, _wfile(tmp, f2))
    q = bv.load_queue(tmp)
    got = q["r4_findings"][0]["findings"][0]
    # 旧裁决 (claim 置空) 保留, agent 显式 crash 不覆盖
    assert got["claim_type"] is None
    assert got["claim_nulled_by"] == "main-agent-deployment-layout-correction"
    # CONFIRMED 前缀的旧 empirical 保留 (新值无标记)
    assert got["empirical_result"].startswith("CONFIRMED")
    # 主代理裁决段追加进 evidence (agent 新证据与裁决尾拼接)
    assert got["evidence"].startswith("新证据 (无裁决段)")
    assert "主代理裁决" in got["evidence"]
    assert "adjudication_preserved_from" in got


def _wfile(tmp, findings):
    p = os.path.join(tmp, ".audit_results", "_f.json")
    json.dump(findings, open(p, "w"), ensure_ascii=False)
    return p


# ---- SWR-V3.4.4-003: refutation 截断告警 qualified_total ----
def test_refutation_qualified_total():
    cands = [_cand(f"R-{i}", status="VERIFIED", verdict="REACHABLE",
                   grade="edge_proven") for i in range(1, 7)]
    tmp = _mk_project(cands)
    r = we.export_script(tmp, mode="refutation", batch_size=4)
    assert r["qualified_total"] == 6
    assert r["count"] == 4
    assert r["truncated"] is True
    assert r["exported"] == 4
    assert "batch-size 6" in r["advice"]
    # 全量导出时无截断标记
    r2 = we.export_script(tmp, mode="refutation", batch_size=6)
    assert r2["qualified_total"] == 6
    assert "truncated" not in r2


# ---- SWR-V3.4.4-004: collect 报错指引 r35-collect ----
def test_collect_error_hints_r35():
    tmp = _mk_project([])
    td = os.path.join(tmp, "_wf")
    os.makedirs(td)
    with open(os.path.join(td, "journal.jsonl"), "w") as f:
        f.write(json.dumps({"type": "result",
                            "result": {"id": "CAND-1", "refuted": False,
                                       "reason": "x"}}) + "\n")
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        try:
            bv.stage_collect(tmp, 0, {})
        except SystemExit:
            pass
        # stage_collect 是 CLI 分支的底层函数; 直接测 helper
        hint = bv._refutation_journal_hint(td)
    assert "r35-collect" in hint


# ---- SWR-V3.4.4-005/006: R4 任务书部署布局 + 前缀契约 ----
def test_r4_template_deployment_and_prefix():
    tpl = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "task_templates", "biz_hypothesis.md")).read()
    assert "部署布局" in tpl and "SWR-V3.4.4-005" in tpl
    # v3.10 (SWR-V3.10-008): 措辞生态中立化——npm 系短语 (vm 全量加载 src)
    # 替换为发布面三查 + 编译开关面通用形态
    assert "发布面三查" in tpl and "编译开关面" in tpl
    assert "CONFIRMED:" in tpl and "REFUTED:" in tpl and "SOURCE_FACT:" in tpl
    assert "SWR-V3.4.4-006" in tpl


# ---- SWR-V3.4.4-007: verifier 任务书计数类规范 ----
def test_verifier_prompt_counting_clause():
    cand = _cand("X-1")
    cand["source_file"] = "a.js"
    cand["sink_type"] = "CWE-338"
    cand["lang"] = "javascript"
    ctx = bv._build_context(cand, "/tmp")
    p = bv._build_prompt(cand, ctx, "/tmp")
    assert "SWR-V3.4.4-007" in p
    assert "几何随机变量" in p


# ---- SWR-V3.4.4-008: tooling 版本守卫 ----
def test_tooling_version_guard():
    tmp = _mk_project([])
    # 构造版本不符的导出脚本
    with open(os.path.join(tmp, ".audit_results", "workflow_verify.js"), "w") as f:
        f.write('const x = 1\nreturn { mode: "verify", tooling_version: "9.9.9" }\n')
    w = bv._tooling_version_warning(tmp)
    assert w is not None and "9.9.9" in w and we.TOOLING_VERSION in w
    # 无脚本/无版本字段 → 无告警
    tmp2 = _mk_project([])
    assert bv._tooling_version_warning(tmp2) is None
    # 导出端注入版本号
    tmp3 = _mk_project([_cand("A-1")])
    we.export_script(tmp3, mode="verify", batch_size=1)
    js = open(os.path.join(tmp3, ".audit_results", "workflow_verify.js")).read()
    assert f'tooling_version: "{we.TOOLING_VERSION}"' in js
    assert bv._tooling_version_warning(tmp3) is None


# ---- SWR-V3.4.4-009: lessons 项目名绝对化 ----
def test_lessons_project_name_absolutized():
    data = lr.collect(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "..", "jsrsasign_tmp_dummy"))
    # 即使目录不存在, collect 也应产出绝对化后的 basename (非空/非 "..")
    assert data["project"] and data["project"] not in (".", "..", "")


# ---- SWR-V3.4.4-010: workflow_export CLI resurrect ----
def test_cli_resurrect_empty_pool():
    tmp = _mk_project([])
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = we.main([__file__, tmp, "--mode", "resurrect"])
    out = json.loads(buf.getvalue())
    assert rc == 0
    assert out["status"] == "WORKFLOW_NOTHING_TO_DO"
    assert out["mode"] == "resurrect"
