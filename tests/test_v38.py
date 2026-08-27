"""v3.8 批次硬化回归 (SWR-V3.8-001~010, docs/design/REQ_SWR_V3_8_BATCH_HARDENING.md)。

五项目 JVM 批次 (zookeeper/kafka/tomcat/nacos/shardingsphere) 暴露的机械层缺陷:
形态判定盲区 / R4 枚举完整性 / edge 契约 / 任务书契约 / 锚点退化。
"""
import io
import json
import os
import sys
import tempfile
import contextlib

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "tools"))

import batch_verify as bv
import surface_mapper as sm
import target_kind


# ---- SWR-V3.8-001: LISTEN_PATTERN NIO/channel 与裸 socket 服务器形态 ----

def test_listen_pattern_nio_tokens():
    assert target_kind.LISTEN_PATTERN.search("ServerSocketChannel.open()")
    assert target_kind.LISTEN_PATTERN.search("new ServerSocket(port)")


def test_nio_server_gets_app_listener_signal():
    """tomcat 形态: NioEndpoint 用 channel+bind, 旧模式 app 0/lib 1.0 误判。"""
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "NioEndpoint.java"), "w").write(
        "public class NioEndpoint {\n"
        "  public void bind() {\n"
        "    ServerSocketChannel ssc = ServerSocketChannel.open();\n"
        "    ssc.bind(new InetSocketAddress(8080));\n"
        "  }\n"
        "}\n")
    r = target_kind.determine_target_kind(tmp)
    listener = [s for s in r["signals"] if s["signal"] == "listener"]
    assert listener, r["signals"]
    assert any(s["direction"] == "app" for s in listener), listener


# ---- SWR-V3.8-002: maturity release-X.Y.Z 标签形态 ----

def test_maturity_release_prefix_tag():
    """zookeeper 形态: release-3.9.5 无 v 前缀, 旧正则判 unknown。"""
    import subprocess as sp
    with tempfile.TemporaryDirectory() as tmp:
        sp.run(["git", "init", "-q"], cwd=tmp, check=True)
        sp.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                "commit", "-q", "--allow-empty", "-m", "i"], cwd=tmp, check=True)
        sp.run(["git", "tag", "release-3.9.5"], cwd=tmp, check=True)
        ctx = sm.build_architecture_context(tmp)
        assert ctx["maturity"] == "mature", ctx["maturity_info"]
        assert "git_tag:release-3.9.5" in ctx["maturity_info"]["signals"]


def test_maturity_release_prefix_developing():
    import subprocess as sp
    with tempfile.TemporaryDirectory() as tmp:
        sp.run(["git", "init", "-q"], cwd=tmp, check=True)
        sp.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                "commit", "-q", "--allow-empty", "-m", "i"], cwd=tmp, check=True)
        sp.run(["git", "tag", "release-0.2.0"], cwd=tmp, check=True)
        ctx = sm.build_architecture_context(tmp)
        assert ctx["maturity"] == "developing", ctx["maturity_info"]


# ---- SWR-V3.8-003/004/005: R4 collect 枚举完整性告警 ----

def _mk_r4_project():
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, ".audit_results"))
    q = {"schema_version": "2.0", "candidates": []}
    bv.save_queue(tmp, q)
    return tmp


def _collect(tmp, findings):
    f = os.path.join(tmp, "_r4.json")
    json.dump(findings, open(f, "w"))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        bv.stage_r4_collect(tmp, f)
    return err.getvalue()


def test_r4_collect_illegal_verdict_warns_but_lands():
    tmp = _mk_r4_project()
    out = _collect(tmp, [{"hypothesis_id": "H-1", "verdict": "PARTIAL",
                          "findings": []}])
    assert "illegal_hypothesis_verdict" in out and "PARTIAL" in out
    q = bv.load_queue(tmp)
    assert len(q["r4_findings"]) == 1  # warn 不阻断


def test_r4_collect_illegal_severity_warns():
    tmp = _mk_r4_project()
    out = _collect(tmp, [{"hypothesis_id": "H-1", "verdict": "confirmed",
                          "findings": [{"title": "x", "severity": "informational",
                                        "evidence": "e"}]}])
    assert "illegal_finding_severity" in out and "informational" in out


def test_r4_collect_refuted_title_warns():
    tmp = _mk_r4_project()
    out = _collect(tmp, [{"hypothesis_id": "H-1", "verdict": "confirmed",
                          "findings": [{"title": "[refuted] foo", "severity": "Medium",
                                        "evidence": "e"}]}])
    assert "refuted_finding_in_list" in out


def test_r4_collect_legal_enums_silent():
    tmp = _mk_r4_project()
    out = _collect(tmp, [{"hypothesis_id": "H-1", "verdict": "reviewed_clean",
                          "findings": []},
                         {"hypothesis_id": "H-2", "verdict": "confirmed",
                          "findings": [{"title": "ok", "severity": "High",
                                        "evidence": "e"}]}])
    assert out == ""


# ---- SWR-V3.8-006: verifier 任务书 edge 契约 + 跨语言调用点 ----

def test_verify_prompt_edge_contract_and_cross_lang():
    cand = {"id": "CAND-1", "source_file": "a.java", "source_line": 3,
            "sink_type": "CWE-94", "lang": "java"}
    ctx = bv._build_context(cand, "/tmp")
    p = bv._build_prompt(cand, ctx, "/tmp")
    assert "edge_evidence 契约" in p
    assert "禁止合并多跳为一条" in p
    assert "混合语言项目" in p
    assert "跨语言调用形态" in p


# ---- SWR-V3.8-008: surface_mapper 注释行锚点退化拦截 ----

def test_validate_rejects_comment_line_anchor():
    """zookeeper 形态: 声称行是注释而窗口邻行命中代码 → 拒收 + suggested_line。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.c")
        open(f, "w").write(
            "int a;\n"
            "void f() {}\n"
            "// set the buffer to null\n")
        d = {"surfaces": [{"id": "S-1", "type": "data_input", "name": "x",
                           "entry_points": [{"file": f, "line": 3,
                                             "function": "f",
                                             "evidence": {"snippet": "void f() {}"}}],
                           "taint_channels": [], "downstream_hints": [],
                           "trust_boundary": "unauthenticated_remote",
                           "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d, tmp)
        assert not ok, "注释行锚点必须被拒收"
        assert any("suggested_line=2" in e for e in errors), errors


def test_validate_code_line_anchor_off_by_one_still_ok():
    """±2 窗口对代码行漂移的容忍是设计行为, 不得因硬化被收紧。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.c")
        open(f, "w").write("int a;\nvoid f() {}\n")
        d = {"surfaces": [{"id": "S-1", "type": "data_input", "name": "x",
                           "entry_points": [{"file": f, "line": 1,
                                             "function": "f",
                                             "evidence": {"snippet": "void f() {}"}}],
                           "taint_channels": [], "downstream_hints": [],
                           "trust_boundary": "unauthenticated_remote",
                           "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d, tmp)
        assert ok, errors


# ---- SWR-V3.8-009/010: 任务书契约固化 ----

def test_surface_map_domain_template_contracts():
    tpl = open(os.path.join(WORKSPACE, "task_templates",
                            "surface_map_domain.md")).read()
    assert "五域一律输出下方 canonical 包裹形态" in tpl
    assert '"type":"boundary"' in tpl
    assert "boundary_kind" in tpl and "lang_pair" in tpl
    assert "逐字符核实字符集的实际内容" in tpl
    assert "白名单含 '.' 即 '..' 序列合法" in tpl


def test_biz_hypothesis_template_contracts():
    tpl = open(os.path.join(WORKSPACE, "task_templates",
                            "biz_hypothesis.md")).read()
    assert "禁止自创" in tpl and "PARTIAL" in tpl
    assert "[refuted]" in tpl
    assert "informational 不是合法值" in tpl
    assert "每 2-3 条 finding 就覆盖写盘一次" in tpl


# ---- SWR-V3.8-014: SKILL.md 版本基线佐证 ----

def test_skill_md_version_corroboration():
    text = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "版本基线佐证" in text
    assert "git describe --tags` 只作参考" in text
    assert "构建清单佐证" in text


# ---- SWR-V3.8-020: size_tier 与 CODE_EXTENSIONS 单事实源 (BIAS_EVAL F1) ----

def test_size_tier_counts_cpp_files():
    """修复前 size_tier 内联集合缺 .cpp → C++ 仓库 0 文件计入 → small。"""
    import signature_matcher
    tmp = tempfile.mkdtemp()
    for i in range(150):
        open(os.path.join(tmp, f"f{i}.cpp"), "w").write("int x;\n")
    assert ".cpp" in signature_matcher.CODE_EXTENSIONS
    tier = sm.size_tier(tmp)
    assert tier["tier"] == "medium", tier["tier"]


# ---- SWR-V3.8-021: .sql 进入识别层 (BIAS_EVAL F2) ----

def test_sql_in_code_extensions_and_inventory():
    import signature_matcher
    assert ".sql" in signature_matcher.CODE_EXTENSIONS
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "schema.sql"), "w").write("SELECT 1;\n")
    inv = sm.language_inventory(tmp)
    # inventory 为 per-language dict 列表, lang 字段点号形态 (下游 lang_of 归一化)
    assert any(x["lang"] == ".sql" for x in inv), inv


# ---- SWR-V3.8-022: _EXT_LANG 与 alias 表对齐 (BIAS_EVAL F3) ----

def test_ext_lang_sql_and_objc():
    assert bv._EXT_LANG[".sql"] == "sql"
    assert bv._EXT_LANG[".m"] == "objc"
    assert bv._EXT_LANG[".mm"] == "objc"


# ---- SWR-V3.8-023: 构建清单 5 缺口 (BIAS_EVAL F4) ----

def test_build_files_top15_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        for name in (".csproj", ".sln", "build.sbt", "build.gradle.kts",
                     "tsconfig.json"):
            open(os.path.join(tmp, name), "w").write("")
        ctx = sm.build_architecture_context(tmp)
        for name in (".csproj", ".sln", "build.sbt", "build.gradle.kts",
                     "tsconfig.json"):
            assert name in ctx["build_files"], f"{name} 未检出: {ctx['build_files']}"


# ---- SWR-V3.8-024: LISTEN_PATTERN Top15 token 缺口 (BIAS_EVAL F5) ----

def test_listen_pattern_swift_ktor_akka_tokens():
    assert target_kind.LISTEN_PATTERN.search("ServerBootstrap.bind(host, port)")
    assert target_kind.LISTEN_PATTERN.search("embeddedServer(Netty, 8080)")
    assert target_kind.LISTEN_PATTERN.search("Http().newServerAt(...).bindAndHandle(route)")
