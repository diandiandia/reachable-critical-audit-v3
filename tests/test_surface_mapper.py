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
    assert norm2["surfaces"][0]["lang"] == "typescript"
