import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import surface_mapper as sm

def _mk_surface(repo, snippet="if (! empty($_REQUEST['target']))"):
    f = os.path.join(repo, "app.pl")
    open(f, "w").write("\n".join(["#!/usr/bin/perl"] * 9 + [snippet]))
    return {
        "id": "S-001", "type": "network_endpoint", "name": "CGI query",
        "entry_points": [{"file": f, "line": 10, "function": "main",
                          "evidence": {"snippet": snippet}}],
        "taint_channels": ["query_string"],
        "downstream_hints": ["config load"],
        "trust_boundary": {"type": "unauthenticated_remote", "gate": "none"},
        "confidence": "high",
    }

def test_validate_ok():
    with tempfile.TemporaryDirectory() as tmp:
        d = {"surfaces": [_mk_surface(tmp)]}
        ok, errors = sm.validate_surfaces(d)
        assert ok, errors

def test_validate_rejects_missing_evidence():
    d = {"surfaces": [{"id": "S-1", "type": "network_endpoint", "name": "x",
        "entry_points": [{"file": "f", "line": 1, "evidence": {"snippet": ""}}],
        "taint_channels": [], "trust_boundary": {"type": "unauthenticated_remote"},
        "confidence": "high"}]}
    ok, errors = sm.validate_surfaces(d)
    assert not ok and any("snippet" in e for e in errors)

def test_validate_maps_free_text_trust():
    # v3.2: 自由文本 trust_boundary 映射到枚举 + original 留档 (Lersosa 实测形态)
    with tempfile.TemporaryDirectory() as tmp:
        s = _mk_surface(tmp)
        s["trust_boundary"] = {"type": "外部请求者 → 服务层"}
        ok, errors = sm.validate_surfaces({"surfaces": [s]})
        assert ok, errors
        norm = sm.normalize_surfaces({"surfaces": [s]})
        assert norm["surfaces"][0]["trust_boundary"]["type"] == "unauthenticated_remote"
        assert norm["surfaces"][0]["trust_boundary"]["original"] == "外部请求者 → 服务层"

def test_validate_rejects_mismatched_line():
    with tempfile.TemporaryDirectory() as tmp:
        s = _mk_surface(tmp)
        s["entry_points"][0]["line"] = 3   # 第 3 行是 shebang 行, 与 snippet 不匹配
        ok, errors = sm.validate_surfaces({"surfaces": [s]})
        assert not ok and any("不匹配" in e for e in errors)

def test_merge_multi_domain():
    with tempfile.TemporaryDirectory() as tmp:
        s1 = _mk_surface(tmp)
        s2 = json.loads(json.dumps(s1))
        s2["id"] = "S-002"; s2["type"] = "data_input"
        f1 = os.path.join(tmp, "a.json"); f2 = os.path.join(tmp, "b.json")
        json.dump({"surfaces": [s1]}, open(f1, "w"))
        json.dump({"surfaces": [s2]}, open(f2, "w"))
        merged = sm.merge_surfaces([f1, f2])
        assert len(merged["surfaces"]) == 2
        assert any(c["resolution"] == "kept-first-multi-domain" for c in merged["conflicts"])

def test_architecture_context():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "Cargo.toml"), "w").write(
            "[dependencies]\nactix-web = \"4\"\ntokio = \"1\"\n")
        open(os.path.join(tmp, "README.md"), "w").write("Security policy: see SECURITY.md")
        open(os.path.join(tmp, "main.rs"), "w").write("fn main() {}")
        open(os.path.join(tmp, "lib.rs"), "w").write("pub fn f() {}")
        ctx = sm.build_architecture_context(tmp)
        assert "Cargo.toml" in ctx["build_files"]
        assert "actix-web" in ctx["deps"]
        # v3.3 (REQ-V3.3-006): maturity 独立信号——无 git 标签时 README 安全流程
        # 关键词降为 developing (旧版 README 关键词直接判 mature 的启发式已退役)
        assert ctx["maturity"] == "developing"
        assert ctx["maturity_info"]["signals"] == ["readme:security-process"]
        assert ctx["lang"] == ".rs"

def test_tasks_5_domains():
    # v3.2: 4 域 + boundary 第五域 (FFI 边界专项)
    with tempfile.TemporaryDirectory() as tmp:
        tasks = sm.gen_surface_tasks(tmp)
        assert [t["domain"] for t in tasks] == ["network", "data", "process", "storage", "boundary"]
        b = tasks[-1]
        assert "boundary_kind" in b["output_schema"]["surface"]
        assert all(t["architecture_context"] and t["evidence_requirement"] for t in tasks)


# ---- W5 回归发现固化: 契约归一化 + 证据模糊匹配 ----

def test_normalize_bare_array_and_string_trust():
    data = [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [], "taint_channels": [],
             "trust_boundary": "gated", "confidence": "high"}]
    norm = sm.normalize_surfaces(data)
    assert norm["surfaces"][0]["trust_boundary"]["type"] == "gated"  # v3.2: +original 留档

def test_normalize_html_entities_and_relative_paths():
    data = [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": "lib/a.rb", "line": 1,
                               "evidence": {"snippet": "a &amp;&amp; b"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]
    norm = sm.normalize_surfaces(data, "/repo")
    ep = norm["surfaces"][0]["entry_points"][0]
    assert ep["file"] == "/repo/lib/a.rb"
    # W6 契约: 保留原始 snippet (源码字面实体不可误解码), 另存 unescape 变体
    assert ep["evidence"]["snippet"] == "a &amp;&amp; b"
    assert ep["evidence"]["snippet_unescaped"] == "a && b"


def test_source_literal_entities_match_dual_variant():
    """W6/AWStats 回归: 源码字面实体 (Perl s/&/&amp;/g;) 不得被 unescape 破坏匹配;
    agent HTML 实体化 (&& → &amp;&amp;) 亦能经变体命中。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.pl")
        open(f, "w").write('$QueryString =~ s/&/&amp;/g;\n')
        d = {"surfaces": [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": f, "line": 1,
                               "evidence": {"snippet": "$QueryString =~ s/&/&amp;/g;"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d)
        assert ok, errors

def test_gated_is_valid_trust():
    with tempfile.TemporaryDirectory() as tmp:
        s = _mk_surface(tmp)
        s["trust_boundary"] = {"type": "gated"}
        ok, errors = sm.validate_surfaces({"surfaces": [s]})
        assert ok, errors

def test_whitespace_alignment_and_comment_suffix_match():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.rb")
        open(f, "w").write("captures           = pattern.match(route)\n")
        d = {"surfaces": [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": f, "line": 1,
                               "evidence": {"snippet":
                                   "captures = pattern.match(route) # 注释混入"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d)
        assert ok, errors

def test_line_drift_suggests_correction():
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.rb")
        open(f, "w").write("\n" * 9 + "def real_sink\n")
        d = {"surfaces": [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": f, "line": 1,
                               "evidence": {"snippet": "def real_sink"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d)
        assert not ok
        assert any("suggested_line=10" in str(e) for e in errors)


def test_merge_keeps_all_surfaces_multi_per_file():
    """W5 回归发现: append 缩进错误曾导致每文件只保留最后一个 surface。"""
    with tempfile.TemporaryDirectory() as tmp:
        f1 = os.path.join(tmp, "a.json")
        f2 = os.path.join(tmp, "b.json")
        json.dump([{"id": "S-1", "type": "data", "name": "x",
                    "entry_points": [{"file": "x.rb", "line": 1,
                                      "evidence": {"snippet": "a"}}],
                    "taint_channels": [], "trust_boundary": "unauthenticated_remote",
                    "confidence": "high"},
                   {"id": "S-2", "type": "data", "name": "y",
                    "entry_points": [{"file": "y.rb", "line": 1,
                                      "evidence": {"snippet": "b"}}],
                    "taint_channels": [], "trust_boundary": "unauthenticated_remote",
                    "confidence": "high"}], open(f1, "w"))
        json.dump([{"id": "S-3", "type": "network", "name": "z",
                    "entry_points": [{"file": "z.rb", "line": 1,
                                      "evidence": {"snippet": "c"}}],
                    "taint_channels": [], "trust_boundary": "unauthenticated_remote",
                    "confidence": "high"}], open(f2, "w"))
        merged = sm.merge_surfaces([f1, f2])
        assert sorted(s["id"] for s in merged["surfaces"]) == ["S-1", "S-2", "S-3"]


def test_snippet_prefix_of_source_line_matches():
    """W5/lighttpd 回归: snippet 为源行前缀 (缺行尾 '{') 时窗口匹配须通过。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.c")
        open(f, "w").write("static void magnet_set_request(lua_State *L, request_st * const r) {\n")
        d = {"surfaces": [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": f, "line": 1,
                               "evidence": {"snippet":
                                   "static void magnet_set_request(lua_State *L, request_st * const r)"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d)
        assert ok, errors


def test_callee_name_fallback_for_mixed_snippet():
    """W5/lighttpd 回归: snippet 混拼上下文 (ds = ...array_match_key_prefix_klen(...);)
    时, 提取 callee 名做唯一调用行建议。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "a.c")
        open(f, "w").write("static handler_t\nmod_alias_remap (void)\n{\n"
                           "    ds = array_match_key_prefix_klen(aliases, uri_ptr, uri_len);\n}\n")
        d = {"surfaces": [{"id": "S-1", "type": "data", "name": "x",
             "entry_points": [{"file": f, "line": 1,
                               "evidence": {"snippet":
                                   "ds = (data_string *)array_match_key_prefix_klen(aliases, uri_ptr, uri_len);"}}],
             "taint_channels": [], "trust_boundary": "unauthenticated_remote",
             "confidence": "high"}]}
        ok, errors = sm.validate_surfaces(d)
        assert not ok
        assert any("suggested_line=4" in str(e) for e in errors)


def test_classify_four_values():
    """v3.3 (REQ-V3.3-005): 四值分类——纯库 Cargo.toml 判 library 而非 framework
    (偏见审查 §3 裁决: 构建文件硬映射已退役)。"""
    with tempfile.TemporaryDirectory() as tmp:
        # 纯库: Cargo.toml + 大量 pub API + 无 main
        open(os.path.join(tmp, "Cargo.toml"), "w").write("[package]\n")
        for i in range(6):
            open(os.path.join(tmp, f"lib{i}.rs"), "w").write("pub fn f() {}\n")
        ctx = sm.build_architecture_context(tmp)
        assert ctx["project_kind"] == "library", ctx["kind_signals"]
    with tempfile.TemporaryDirectory() as tmp:
        # app: main + 监听
        open(os.path.join(tmp, "main.rs"), "w").write(
            "fn main() {}\nfn srv() { let _l = std::net::TcpListener::bind(\"0.0.0.0:80\"); }\n")
        ctx = sm.build_architecture_context(tmp)
        assert ctx["project_kind"] == "app", ctx["kind_signals"]
    with tempfile.TemporaryDirectory() as tmp:
        # infra: 仅 CMakeLists, 无源码
        open(os.path.join(tmp, "CMakeLists.txt"), "w").write("cmake_minimum_required\n")
        ctx = sm.build_architecture_context(tmp)
        assert ctx["project_kind"] == "infra", ctx["kind_signals"]
    with tempfile.TemporaryDirectory() as tmp:
        # 无任何信号 → app (保守)
        open(os.path.join(tmp, "x.txt"), "w").write("hi\n")
        ctx = sm.build_architecture_context(tmp)
        assert ctx["project_kind"] == "app", ctx["kind_signals"]


def test_build_files_lowercase_variant():
    """v3.3 (REQ-V3.3-005): 小写构建文件变体检出 (Lua 仓库 makefile 实测根因)。"""
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "makefile"), "w").write("all:\n")
        ctx = sm.build_architecture_context(tmp)
        assert "Makefile" in ctx["build_files"]


def test_maturity_git_tag():
    """v3.3 (REQ-V3.3-006): git 版本标签 → mature/developing 语义。"""
    import subprocess as sp
    with tempfile.TemporaryDirectory() as tmp:
        sp.run(["git", "init", "-q"], cwd=tmp, check=True)
        sp.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                "commit", "-q", "--allow-empty", "-m", "i"], cwd=tmp, check=True)
        sp.run(["git", "tag", "v2.1.0"], cwd=tmp, check=True)
        ctx = sm.build_architecture_context(tmp)
        assert ctx["maturity"] == "mature"
        assert "git_tag:v2.1.0" in ctx["maturity_info"]["signals"]


def test_trust_boundary_host_api():
    """v3.3 (REQ-V3.3-008): host_api 枚举 + 关键词映射。"""
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.c")
        open(f, "w").write("void f() {}\n")
        d = {"surfaces": [{"id": "S-1", "type": "data_input", "name": "x",
                           "entry_points": [{"file": f, "line": 1,
                                             "function": "f",
                                             "evidence": {"snippet": "void f() {}"}}],
                           "taint_channels": [], "downstream_hints": [],
                           "trust_boundary": "宿主公共 API 调用方传入",
                           "confidence": "high"}]}
        ok, errs = sm.validate_surfaces(d)
        assert ok, errs
        norm = sm.normalize_surfaces(d)
        assert norm["surfaces"][0]["trust_boundary"]["type"] == "host_api"


def test_v331_normalize_surface_lang():
    """v3.3.1: normalize 归一化 surface lang 形态 ('.c'→c, ts→typescript)。"""
    d = {"surfaces": [{"id": "S-1", "type": "data_input", "name": "x",
                       "lang": ".c",
                       "entry_points": [{"file": "a.c", "line": 1,
                                         "function": "f",
                                         "evidence": {"snippet": "f();"}}],
                       "taint_channels": [], "downstream_hints": [],
                       "trust_boundary": "host_api",
                       "confidence": "high"}]}
    norm = sm.normalize_surfaces(d)
    assert norm["surfaces"][0]["lang"] == "c"
    d2 = {"surfaces": [dict(d["surfaces"][0], lang="ts")]}
    norm2 = sm.normalize_surfaces(d2)
    # v3.5.2 (P3): ts 归一化到账本规范名 javascript (旧值 typescript)
    assert norm2["surfaces"][0]["lang"] == "javascript"


def test_merge_warns_id_gap():
    """v3.4.5 (SWR-V3.4.5-003): 域内 id 序列空洞告警 (非阻断)——缺号可能是
    agent 整段漏报的信号 (gRPC 审计: boundary 域缺 003)。"""
    import io, contextlib
    with tempfile.TemporaryDirectory() as tmp:
        f1 = os.path.join(tmp, "_r1_boundary.json")
        json.dump({"surfaces": [
            {"id": "SURF-BOUNDARY-001", "type": "boundary",
             "entry_points": [{"file": "a.c", "line": 1}]},
            {"id": "SURF-BOUNDARY-002", "type": "boundary",
             "entry_points": [{"file": "b.c", "line": 2}]},
            {"id": "SURF-BOUNDARY-004", "type": "boundary",
             "entry_points": [{"file": "c.c", "line": 3}]},
        ]}, open(f1, "w"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            merged = sm.merge_surfaces([f1])
        assert len(merged["surfaces"]) == 3, "空洞不阻断合并"
        assert "SURF-BOUNDARY-003" in err.getvalue(), err.getvalue()
        assert "missing" in err.getvalue()


def test_merge_same_file_cross_domain_hint():
    """v3.4.6 (SWR-V3.4.6-003): 同文件双面但 entry_points 不重叠 →
    merge 输出 same_file_cross_domain_pairs 提示 (不自动成对, 主代理裁决)。
    quic-go 实录: token_store.go 被 data/storage 两域测绘不同函数,
    conflict 启发式不触发 → mirror 漏对且无人工核对提示。"""
    import io, contextlib
    with tempfile.TemporaryDirectory() as tmp:
        f1 = os.path.join(tmp, "_r1_data.json")
        json.dump({"surfaces": [
            {"id": "SURF-DATA-010", "type": "data",
             "entry_points": [{"file": "token_store.go", "line": 10}]},
            {"id": "SURF-DATA-011", "type": "data",
             "entry_points": [{"file": "other.go", "line": 3}]},
        ]}, open(f1, "w"))
        f2 = os.path.join(tmp, "_r1_storage.json")
        json.dump({"surfaces": [
            {"id": "SURF-STORAGE-008", "type": "storage",
             "entry_points": [{"file": "token_store.go", "line": 40}]},
        ]}, open(f2, "w"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            merged = sm.merge_surfaces([f1, f2])
        pairs = merged["same_file_cross_domain_pairs"]
        assert any(set(p["pair"]) == {"SURF-DATA-010", "SURF-STORAGE-008"}
                   for p in pairs), pairs
        assert "hint" in err.getvalue() and "SURF-DATA-010" in err.getvalue()
        # 同文件同域 (DATA-011/other.go 无同文件跨域面) → 不成对
        assert not any(set(p["pair"]) == {"SURF-DATA-010", "SURF-DATA-011"}
                       for p in pairs)
    # 不同文件 / 同域 → 空清单
    with tempfile.TemporaryDirectory() as tmp:
        f1 = os.path.join(tmp, "_r1_a.json")
        json.dump({"surfaces": [
            {"id": "SURF-DATA-001", "type": "data",
             "entry_points": [{"file": "a.go", "line": 1}]},
            {"id": "SURF-DATA-002", "type": "data",
             "entry_points": [{"file": "b.go", "line": 1}]},
        ]}, open(f1, "w"))
        merged = sm.merge_surfaces([f1])
        assert merged["same_file_cross_domain_pairs"] == []


# ---------------- v3.5 (B3) 语言门补全防回退 ----------------

def test_exec_entry_kotlin_csharp_swift():
    """v3.5 (B3): main 模式补 Kotlin fun main/C# static void Main/Swift @main。"""
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "Main.kt")
        open(p, "w").write("package app\n\nfun main() {\n}\n")
        assert sm._detect_exec_entry([p])[0]
        p = os.path.join(tmp, "Program.cs")
        open(p, "w").write("public static void Main(string[] args) {\n}\n")
        assert sm._detect_exec_entry([p])[0]
        p = os.path.join(tmp, "App.swift")
        open(p, "w").write("@main\nstruct App {\n}\n")
        assert sm._detect_exec_entry([p])[0]


def test_listen_new_vocab():
    """v3.5 (B3): listen 模式补 C# HttpListener/Ruby TCPServer/PHP
    stream_socket_server/Perl IO::Socket::INET。"""
    cases = ("HttpListener l = new();", "server = TCPServer.new",
             "stream_socket_server('tcp://0.0.0.0:80')",
             "IO::Socket::INET->new(LocalAddr => '0.0.0.0')")
    with tempfile.TemporaryDirectory() as tmp:
        for i, snippet in enumerate(cases):
            p = os.path.join(tmp, f"f{i}.txt")
            open(p, "w").write(snippet + "\n")
            assert sm._detect_exec_entry([p])[1], snippet


def test_src_exts_covers_16_langs():
    """v3.5 (B3): _SRC_EXTS 覆盖全部 16 预设语言扩展名。"""
    for ext in (".scala", ".php", ".pl", ".pm", ".ps1", ".sh",
                ".kt", ".cs", ".swift", ".ts", ".rb"):
        assert ext in sm._SRC_EXTS, ext


def test_no_main_generalized():
    """v3.5 (B3): 无 main → library 泛化到脚本/JVM/.NET 系; shell 排除保持保守。"""
    ctx = {"build_files": []}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(6):
            open(os.path.join(tmp, f"m{i}.php"), "w").write("<?php function f() {}\n")
        kind, signals = sm._classify_project_kind(tmp, ctx)
        assert "php_no_main" in signals
        assert kind == "library"
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(6):
            open(os.path.join(tmp, f"m{i}.sh"), "w").write("#!/bin/sh\necho hi\n")
        kind, signals = sm._classify_project_kind(tmp, ctx)
        assert "shell_no_main" not in signals  # shell 保守排除
        assert kind in ("app", "framework", "infra", "library")
