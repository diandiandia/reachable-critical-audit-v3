#!/usr/bin/env python3
"""SWR-V3.7: 报告分级 + 机械渲染 md 测试。

覆盖: severity 映射优先级/override 透传与非法回退/报告六段结构/按严重程度
排序且 NEEDS_REVIEW 不进清单/最小队列降级不抛异常/六门禁表/PENDING→FAIL/
去项目化/语言覆盖表角色/coverage_bridge tracked 合并。
既有锁 (test_report_outputs/test_end_to_end) 不动。"""
import io, json, os, sys, contextlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import signature_lib
import batch_verify as bv

# 报告模板/渲染内容不得携带的历史项目 token (第一原则: 项目名只在追溯字段)
REPORT_BLACKLIST = (signature_lib.DEPROJECT_BLACKLIST +
                    ["sinatra", "lighttpd", "actix", "mbedtls", "awstats",
                     "puma", "fastjson", "django", "ktor", "nestjs",
                     "java-jwt", "akka"])

SECTION_HEADS = ["## 一、问题清单（按严重程度排序）", "## 二、问题详情",
                 "## 三、修复建议与结论（主代理补充）",
                 "## 附录 A：NEEDS_REVIEW 清单与同事实映射",
                 "## 附录 B：审计过程信息"]


def _mk_full_repo(tmp_path):
    """全量 fixture: 3 REACHABLE (严重/高/中) + 1 NEEDS_REVIEW + R4 + bridge。"""
    repo = str(tmp_path)
    os.makedirs(os.path.join(repo, "src"), exist_ok=True)
    os.makedirs(os.path.join(repo, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(repo, "scripts"), exist_ok=True)
    open(os.path.join(repo, "src", "main.go"), "w").write("package main\n")
    open(os.path.join(repo, "src", "auth.py"), "w").write("# auth\n")
    open(os.path.join(repo, "src", "view.py"), "w").write("# view\n")
    open(os.path.join(repo, "src", "buf.c"), "w").write("#include <stdio.h>\n")
    open(os.path.join(repo, "frontend", "app.js"), "w").write("// app\n")
    open(os.path.join(repo, "scripts", "build.sh"), "w").write("#!/bin/sh\n")
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    queue = {"schema_version": "3.0",
             "coverage_bridge": [{"surface": "S-BRIDGE-1", "basis": "relay"}],
             "candidates": [
        {"id": "CAND-001", "source_file": "src/main.go", "source_line": 42,
         "sink_type": "CWE-78", "members": [{"id": "HYP-001"}],
         "status": "VERIFIED", "verdict": "REACHABLE",
         "reachability_type": "full_chain",
         "call_chain": ["reqHandler", "buildCmd", "exec"], "call_chain_depth": 3,
         "claim_type": "rce", "cwe": ["CWE-78"],
         "evidence": "input flows into command execution without escaping",
         "evidence_grade": "edge_proven", "language": "go",
         "refutation": {"votes": 2, "refute_count": 0, "survived": True}},
        {"id": "CAND-002", "source_file": "src/auth.py", "source_line": 77,
         "sink_type": "CWE-862", "members": [{"id": "HYP-002"}],
         "status": "VERIFIED", "verdict": "REACHABLE",
         "reachability_type": "full_chain",
         "call_chain": ["api", "_admin", "delete"], "call_chain_depth": 3,
         "claim_type": "other", "cwe": ["CWE-862"],
         "evidence": "admin endpoint lacks authentication",
         "evidence_grade": "static_only", "language": "python"},
        {"id": "CAND-003", "source_file": "src/view.py", "source_line": 9,
         "sink_type": "CWE-79", "members": [{"id": "HYP-003"}],
         "status": "VERIFIED", "verdict": "REACHABLE",
         "reachability_type": "edge_proven",
         "call_chain": ["index", "render"], "call_chain_depth": 2,
         "claim_type": "xss", "cwe": ["CWE-79"],
         "evidence": "unescaped reflection into output",
         "evidence_grade": "edge_proven", "language": "python"},
        {"id": "CAND-004", "source_file": "src/buf.c", "source_line": 101,
         "sink_type": "CWE-125", "members": [{"id": "HYP-004"}],
         "status": "NEEDS_REVIEW", "verdict": "NEEDS_REVIEW",
         "evidence": "证据不足 无法取证",
         "correction_record": ["证据不足 无法取证"]},
    ], "r4_findings": [{
        "hypothesis_id": "HYP-001", "verdict": "confirmed",
        "findings": [
            {"title": "t", "cwe": ["CWE-78"], "severity": "critical",
             "claim_type": "rce", "evidence": "e",
             "fix": "validate command args, avoid shell",
             "tracked_surfaces": ["S-001"]},
            # R4 独立 High (无 r3_link): 应入清单「高」节
            {"title": "control endpoint lacks any auth", "cwe": ["CWE-862"],
             "severity": "High", "claim_type": "other",
             "evidence": "stop command reachable without token",
             "fix": "require token by default",
             "empirical_result": {"outcome": "CONFIRMED"}},
            # R4 Medium: 应入清单「中」节
            {"title": "weak header trust", "cwe": ["CWE-20"],
             "severity": "Medium", "claim_type": "other",
             "evidence": "forwarded headers trusted",
             "fix": "validate trusted proxies"},
            # R4 Low: 不进清单, 留 B.4 表
            {"title": "minor info leak", "cwe": ["CWE-200"],
             "severity": "Low", "claim_type": "other",
             "evidence": "version banner disclosed"},
            # R4 同事实 = R3 候选: 不重复列, 记去重说明
            {"title": "same fact as CAND-001", "cwe": ["CWE-789"],
             "severity": "High", "claim_type": "unbounded",
             "evidence": "duplicate of candidate", "r3_link": "CAND-001"},
        ]}]}
    bv.save_queue(repo, queue)
    with open(os.path.join(ar, "hypotheses.json"), "w") as f:
        json.dump({"hypotheses": [
            {"id": "HYP-001", "surface_ids": ["S-001"], "semantic_family": "INJECTION"},
            {"id": "HYP-002", "surface_ids": ["S-002"]}]}, f)
    surfaces = {"surfaces": [
        {"id": "S-001", "name": "http in", "lang": "go",
         "entry_points": [{"file": "src/main.go", "line": 10, "function": "h"}],
         "trust_boundary": {"type": "unauthenticated_remote"}},
        {"id": "S-002", "name": "admin api", "lang": "python",
         "entry_points": [{"file": "src/auth.py", "line": 5, "function": "a"}],
         "trust_boundary": {"type": "unauthenticated_remote"}},
        {"id": "S-FFI-1", "name": "cgo edge", "lang": "go",
         "boundary_kind": "cgo", "lang_pair": "go->c",
         "entry_points": [{"file": "src/main.go", "line": 20, "function": "f"}],
         "trust_boundary": {"type": "gated"}}],
        "mirror_pairs": [["S-001", "S-002"]]}
    with open(os.path.join(ar, "input_surface.json"), "w") as f:
        json.dump(surfaces, f)
    return repo


def _render(repo):
    """render_report_md 返回写入路径; 测试断言内容, 读回。"""
    path = bv.render_report_md(repo)
    return open(path).read()


# ── 1. 严重程度机械映射优先级 ──────────────────────────────────────────
def test_severity_mapping_precedence():
    assert bv.severity_for({"cwe": ["CWE-78"], "claim_type": "rce"}) == ("critical", "cwe:CWE-78")
    assert bv.severity_for({"cwe": ["CWE-79"], "claim_type": "xss"}) == ("medium", "cwe:CWE-79")
    # override > cwe max
    assert bv.severity_for({"cwe": ["CWE-78"], "claim_type": "rce",
                            "severity_override": "high",
                            "severity_override_reason": "library-internal"}) == ("high", "override")
    # cwe max: 多 cwe 取最高
    sev, src = bv.severity_for({"cwe": ["CWE-79", "CWE-78"]})
    assert sev == "critical" and "CWE-78" in src
    # claim_type 回退 (无 cwe 命中)
    assert bv.severity_for({"cwe": [], "claim_type": "protocol_dos"}) == ("high", "claim_type(protocol_dos)")
    # default
    assert bv.severity_for({"cwe": [], "claim_type": "other"}) == ("medium", "default")


# ── 2. 非法 override 回退机械值 + 告警行 ───────────────────────────────
def test_severity_override_invalid_ignored(tmp_path):
    repo = str(tmp_path)
    os.makedirs(os.path.join(repo, ".audit_results"), exist_ok=True)
    bv.save_queue(repo, {"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.go", "source_line": 1,
         "sink_type": "CWE-78", "members": [{"id": "H-1"}],
         "status": "VERIFIED", "verdict": "REACHABLE",
         "claim_type": "rce", "cwe": ["CWE-78"],
         "evidence": "e", "evidence_grade": "edge_proven",
         "severity_override": "severe", "severity_override_reason": "typo"}]})
    sev, src = bv.severity_for({"cwe": ["CWE-78"], "severity_override": "severe"})
    assert sev == "critical" and src == "invalid_override"
    md = _render(repo)
    assert "⚠override非法" in md          # 告警行
    assert "来源: override" not in md      # 未当合法 override 渲染


# ── 3. 全流程: md 六段 + stdout 仍纯 JSON ─────────────────────────────
def test_report_md_written_with_structure(tmp_path):
    repo = _mk_full_repo(tmp_path)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_report(repo)
    r = json.loads(buf.getvalue())          # stdout 纯 JSON 契约未破
    assert r["reachable"] == 3
    md = open(os.path.join(repo, ".audit_results",
                           "reachable_vulnerabilities_report.md")).read()
    for s in SECTION_HEADS:
        assert s in md, s


# ── 4. 排序 + NEEDS_REVIEW 排除 ───────────────────────────────────────
def test_report_md_severity_sorted_and_needs_review_excluded(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    i_sev, i_high, i_med = md.index("### 严重"), md.index("### 高"), md.index("### 中")
    assert i_sev < i_high < i_med           # 严重节在最前
    # NEEDS_REVIEW 不进问题清单 (清单段只含 REACHABLE)
    listing = md.split("## 二、问题详情")[0]
    assert "CAND-004" not in listing
    # 进附录 A + 成因 + 映射表
    app_a = md.split("## 附录 A")[1].split("## 附录 B")[0]
    assert "CAND-004" in app_a and "证据不足" in app_a
    assert "同事实映射（REQ-V3.1-092）" in app_a


# ── 5. 最小队列降级不抛异常 ───────────────────────────────────────────
def test_report_md_minimal_queue_degrades(tmp_path):
    repo = str(tmp_path)
    os.makedirs(os.path.join(repo, ".audit_results"), exist_ok=True)
    bv.save_queue(repo, {"schema_version": "3.0", "candidates": []})
    md = _render(repo)                      # 全部可选输入缺失 → 不抛异常
    assert "无确认问题" in md
    assert "（主代理补充）" in md            # 占位文本
    assert "账本缺失" in md


# ── 6. 六门禁表: PENDING → FAIL 行 ────────────────────────────────────
def test_report_md_gates_table(tmp_path):
    repo = str(tmp_path)
    os.makedirs(os.path.join(repo, ".audit_results"), exist_ok=True)
    bv.save_queue(repo, {"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.go", "source_line": 1,
         "sink_type": "CWE-78", "members": [{"id": "H-1"}],
         "status": "PENDING"}]})
    md = _render(repo)
    assert "### B.5 六门禁断言" in md
    assert "① no_pending" in md and "| ① no_pending | FAIL" in md
    for gate in ("② REACHABLE 无 static_only", "③ 实证类 100% confirmed",
                 "④ H1-H7 全 VERIFIED", "⑤ 对账零差异", "⑥ escalated=0 或签收",
                 "⑦ surface 覆盖率 100%", "⑧ target_kind_required", "③c 复活攻击完成度"):
        assert gate in md, gate


# ── 7. 去项目化: 零黑名单 token 零 /root/ ─────────────────────────────
def test_report_md_deprojected(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    low = md.lower()
    for tok in REPORT_BLACKLIST:
        assert tok not in low, tok
    assert "/root/" not in md


# ── 8. stage_collect 透传 severity_override ───────────────────────────
def test_collect_persists_severity_override(tmp_path):
    repo = str(tmp_path)
    os.makedirs(os.path.join(repo, ".audit_results"), exist_ok=True)
    bv.save_queue(repo, {"schema_version": "3.0", "candidates": [
        {"id": "CAND-001", "source_file": "a.go", "source_line": 1,
         "sink_type": "CWE-78", "members": [{"id": "H-1"}],
         "status": "PENDING"}]})
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bv.stage_collect(repo, "b1", {"CAND-001": {
            "id": "CAND-001", "verdict": "REACHABLE", "reachability_type": "DIRECT",
            "call_chain": ["a", "b", "c"], "call_chain_depth": 3,
            "evidence": "e", "cwe": ["CWE-78"],
            "severity_override": "high", "severity_override_reason": "no direct attacker"}})
    cand = bv.load_queue(repo)["candidates"][0]
    assert cand["severity_override"] == "high"
    assert cand["severity_override_reason"] == "no direct attacker"
    assert bv.severity_for(cand) == ("high", "override")


# ── 9. 语言覆盖表角色列 ───────────────────────────────────────────────
def test_language_coverage_table_roles(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    b2 = md.split("### B.2 语言覆盖表")[1].split("### B.3")[0]
    assert "server-side" in b2 and "client-only" in b2 and "build-config" in b2
    # v3.9 (SWR-V3.9-004): 语言列经 _norm_lang 归一 (扩展名→规范名), 旧断言
    # 锁定 ".js" 原始形态与本修复冲突
    assert "| javascript | 1 | client-only |" in b2   # client-only 行 (归一后)
    assert "| shell | 1 | build-config |" in b2        # build-config 行 (归一后)


# ── 10. tracked_ids 合并 coverage_bridge ──────────────────────────────
def test_tracked_ids_includes_coverage_bridge(tmp_path):
    repo = _mk_full_repo(tmp_path)
    queue = bv.load_queue(repo)
    surfaces = json.load(open(os.path.join(repo, ".audit_results", "input_surface.json")))
    ids = bv._tracked_ids(repo, queue, surfaces)
    assert "S-001" in ids and "S-002" in ids          # hypotheses surface_ids
    assert "S-BRIDGE-1" in ids                        # coverage_bridge
    assert "S-FFI-1" not in ids                       # 未追踪面不混入


# ── 11. R4 confirmed (High/Medium) 并入问题清单 ───────────────────────
def test_report_md_includes_r4_confirmed(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    high_section = md.split("### 高（")[1].split("### 中（")[0]
    assert "HYP-001-F2" in high_section               # R4 独立 High 进「高」节
    assert "R4 确认（无 R3.5 复核）" in high_section   # 来源标注
    med_section = md.split("### 中（")[1].split("## 二、问题详情")[0]
    assert "HYP-001-F3" in med_section                # R4 Medium 进「中」节


# ── 12. r3_link 同事实 R4 条目去重 ────────────────────────────────────
def test_report_md_r4_dupe_deduped(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    listing = md.split("## 二、问题详情")[0]
    assert "HYP-001-F5" not in listing.split("\n\n**同事实去重")[0]  # 不占清单行
    assert "同事实去重（SWR-V3.4.3-060）" in listing
    assert "HYP-001-F5 ↔ CAND-001" in listing         # 去重说明行


# ── 13. R4 Low 不进清单 (留 B.4 表) ───────────────────────────────────
def test_report_md_r4_low_excluded(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    listing = md.split("## 二、问题详情")[0]
    assert "HYP-001-F4" not in listing                # Low 不在清单/详情
    b4 = md.split("### B.4 R4 假说 verdict 表")[1].split("### B.5")[0]
    assert "| HYP-001 | confirmed | 5 |" in b4        # B.4 假说行, 计数含 Low 条目


# ── 14. R4 条目详情段 (无 R3.5 复核标注 + fix) ────────────────────────
def test_report_md_r4_detail_rendered(tmp_path):
    md = _render(_mk_full_repo(tmp_path))
    details = md.split("## 二、问题详情")[1].split("## 三、修复建议与结论")[0]
    assert "HYP-001-F2" in details
    assert "R4 业务假说确认（HYP-001）" in details
    assert "无 R3.5 独立复核" in details
    assert "require token by default" in details      # R4 fix 渲染
    assert "empirical_result" in md or "CONFIRMED" in details
