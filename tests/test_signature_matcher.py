import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import signature_matcher as sm
import signature_lib

def _mk_repo():
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "server.c"), "w").write(
        "void handler(void) {\n  buf_extend(remote_data());\n}\n"
        "void buf_extend(char *d) { buffer_append(d); }\n"
        "void caller_top(void) { handler(); }\n")
    open(os.path.join(tmp, "entry.pl"), "w").write(
        "sub main {\n  my $x = get_query();\n  open(F, \"<$x\");\n}\n")
    return tmp

def test_index_and_window():
    repo = _mk_repo()
    idx = sm.build_project_index(repo)
    assert "buf_extend" in idx          # 调用点被索引
    entry = {"file": os.path.join(repo, "server.c"), "line": 1}
    window = sm.expand_window(entry, idx, depth=2)
    files = {w["file"] for w in window}
    assert len(window) >= 3
    # 第 1 层应含调用 buf_extend 的调用点 (server.c 内), 第 2 层含 caller_top 调用 handler 的点
    assert any(w["callee"] == "buf_extend" for w in window)

def test_match_hits_window_only():
    repo = _mk_repo()
    idx = sm.build_project_index(repo)
    sigs = signature_lib.load()["signatures"]
    surfaces = {"surfaces": [{
        "id": "S-001", "type": "network_endpoint", "name": "x",
        "entry_points": [{"file": os.path.join(repo, "entry.pl"), "line": 1,
                          "evidence": {"snippet": "sub main"}}],
        "taint_channels": [], "trust_boundary": {"type": "unauthenticated_remote"},
        "confidence": "high"}]}
    hits = sm.match_signatures(surfaces["surfaces"], sigs, idx, depth=2)
    # entry.pl 含 open(F, "<$x") 但 SIG-PATH-WHITELIST hints 需 contains(/!~ 等
    # 窗口命中取决于 hints; 至少应产出 (surface, sig) 结构的 hits 或空, 且全部命中在窗口文件内
    assert all("surface_id" in h and "sig_id" in h and "site" in h for h in hits)
    assert all(h["site"]["file"] == os.path.join(repo, "entry.pl") for h in hits)

def test_gen_hypotheses_dedup_and_logic():
    hits = [
        {"surface_id": "S-1", "sig_id": "SIG-LOGIC-WEAKEN-005",
         "site": {"file": "f", "line": 1}, "matched_pattern": "x", "line_text": "y"},
        {"surface_id": "S-1", "sig_id": "SIG-LOGIC-WEAKEN-005",
         "site": {"file": "f", "line": 2}, "matched_pattern": "x", "line_text": "y"},
        {"surface_id": "S-2", "sig_id": "SIG-TRUNC-CAST-004",
         "site": {"file": "g", "line": 3}, "matched_pattern": "z", "line_text": "w"},
    ]
    sigs = signature_lib.load()["signatures"]
    hyps = sm.gen_hypotheses(hits, sigs)
    # S-1×LOGIC 合并为 1 条且进 logic 队列
    assert len(hyps["logic_hypotheses"]) == 1
    assert len(hyps["logic_hypotheses"][0]["hit_sites"]) == 2
    assert len(hyps["hypotheses"]) == 1
    assert hyps["hypotheses"][0]["checklist"]  # checklist 随假设携带

def test_filter_tasks():
    hyps = {"hypotheses": [{"id": "HYP-001", "surface_id": "S", "semantic_family": "x",
                             "hit_sites": [], "checklist": []}],
            "logic_hypotheses": []}
    tasks = sm.emit_filter_tasks(hyps)
    assert tasks and tasks[0]["template"] == "hypothesis_filter"
    assert "exclude_criteria" in tasks[0]


def test_ruby_bang_and_parenless_calls_indexed():
    """回归发现 (W5/sinatra): Ruby !/? 后缀方法名与无括号裸调用必须被索引
    (dispatch!/call!/error_block!; invoke { dispatch! })。"""
    import tempfile
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "a.rb"), "w").write(
        "def dispatch!\n  puts :x\nend\n\ndef call!\n  invoke { dispatch! }\n  error_block!(1)\nend\n")
    idx = sm.build_project_index(tmp)
    assert any(h["caller"] == "call!" for h in idx.get("dispatch!", [])), idx.get("dispatch!")
    assert any(h["caller"] == "call!" for h in idx.get("error_block!", []))
    # def 行本身也入索引 (定义点, 供窗口展开)
    assert any("def dispatch!" in open(os.path.join(tmp, "a.rb")).read().splitlines()[h["line"] - 1]
               for h in idx.get("dispatch!", []))


def test_c_def_and_ifdef_not_misattributed():
    """W5/lighttpd 回归发现: (1) '#ifdef _WIN32' 的 'def' 曾把 _WIN32 当函数定义;
    (2) C 函数定义 (RET name() 形态) 曾不被 caller 归属识别。"""
    import tempfile
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, "a.c"), "w").write(
        "#ifdef _WIN32\n#define FOO 1\n#endif\n\n"
        "static size_t chunk_buffer_prepare_append(buffer *b, size_t sz) {\n"
        "    if (sz > buffer_string_space(b)) {\n"
        "        other_fn(b, sz);\n"
        "    }\n"
        "    return 0;\n"
        "}\n")
    idx = sm.build_project_index(tmp)
    assert "_WIN32" not in idx, "ifdef 宏名不得成为索引条目"
    hits = idx.get("other_fn", [])
    assert hits and hits[0]["caller"] == "chunk_buffer_prepare_append", hits


def test_cli_outputs_land_in_audit_results():
    """v3.2.3 (Lua 审计): match/gen 默认产物落盘 .audit_results/ (R0 铁律),
    不再写进程 CWD——此前 hits.json 落在项目根/调用者 CWD。"""
    import io, contextlib
    repo = _mk_repo()
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar)
    surf = os.path.join(ar, "input_surface.json")
    json.dump({"surfaces": [{"id": "S-1", "type": "network",
                             "entry_points": [{"file": "server.c", "line": 1}]}]},
              open(surf, "w"))
    idx = sm.build_project_index(repo)
    idxf = os.path.join(ar, "project_index.json")
    json.dump(idx, open(idxf, "w"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sm.main(["sm", "match", surf, idxf])
    assert os.path.exists(os.path.join(ar, "hits.json"))
    assert "hits.json" in buf.getvalue()
    with contextlib.redirect_stdout(buf):
        sm.main(["sm", "gen", os.path.join(ar, "hits.json")])
    assert os.path.exists(os.path.join(ar, "hypotheses.json"))
    # index 默认路径也进 .audit_results/
    with contextlib.redirect_stdout(buf):
        sm.main(["sm", "index", repo])
    assert os.path.exists(os.path.join(ar, "project_index.json"))


def test_v33_c_l2_hits_only_c_surface():
    """v3.3 (REQ-V3.3-001): C 词族只打 .c surface (lang 过滤联动)。"""
    import tempfile as _t
    repo = _t.mkdtemp()
    open(os.path.join(repo, "a.c"), "w").write(
        "void h(void) {\n  char *p = malloc(remote_len());\n}\n")
    open(os.path.join(repo, "b.rs"), "w").write(
        "fn h() { let p = unsafe { 1 }; }\n")
    idx = sm.build_project_index(repo)
    sigs = signature_lib.load()["signatures"]
    cs = {"id": "S-C", "type": "data_input", "lang": "c",
          "entry_points": [{"file": os.path.join(repo, "a.c"), "line": 2}]}
    rs = {"id": "S-R", "type": "data_input", "lang": "rust",
          "entry_points": [{"file": os.path.join(repo, "b.rs"), "line": 1}]}
    hits = sm.match_signatures([cs, rs], sigs, idx)
    c_ids = {h["sig_id"] for h in hits if h["surface_id"] == "S-C"}
    r_ids = {h["sig_id"] for h in hits if h["surface_id"] == "S-R"}
    assert "SIG-C-ALLOC-001" in c_ids
    assert "SIG-C-ALLOC-001" not in r_ids
