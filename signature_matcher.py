#!/usr/bin/env python3
"""M3 signature_matcher — R2 面内签名匹配与假设生成。

满足: SWR-V3-020 (ProjectIndex), SWR-V3-021 (窗口展开 depth=3),
      SWR-V3-022 (窗口内 hints 匹配), SWR-V3-023 (假设生成去重),
      SWR-V3-024 (筛选任务书), SWR-V3-025 (LOGIC_PATTERN 独立队列).
用法:
    python3 signature_matcher.py index <project_root>          # 建 ProjectIndex
    python3 signature_matcher.py match <input_surface.json> <project_index.json>
    python3 signature_matcher.py gen <hits.json>               # 生成 hypotheses
"""
import json
import os
import re
import sys
import signature_lib

# v3.3.1: 扩展名/别名 → 签名 lang 词表 (对齐 signature_lib.VALID_LANGS 词汇)
# v3.5.2 (P3): 归一词汇与 batch_verify._LANG_ALIAS 一致——cs→csharp、
# ts/typescript/js→javascript (账本 16 名规范集); L2 过滤双侧归一化见
# _sig_applicable (签名标签 cs/typescript 属签名侧内部名, 归一后等值匹配)
EXT_LANG_ALIAS = {
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "hpp": "cpp",
    "rs": "rust", "go": "go", "java": "java", "py": "python", "rb": "ruby",
    "cs": "csharp", "ts": "javascript", "typescript": "javascript", "kt": "kotlin",
    "kts": "kotlin", "scala": "scala", "swift": "swift", "php": "php",
    "pl": "perl", "pm": "perl", "sh": "shell", "ps1": "powershell",
    "js": "javascript", "m": "objc", "mm": "objc", "lua": "lua",
}


def norm_lang(lang):
    """v3.3.1: surface lang 归一化——剥点/小写/别名映射; None 原样返回。"""
    if not lang:
        return None
    l = str(lang).strip().lstrip(".").lower()
    return EXT_LANG_ALIAS.get(l, l)

DEFAULT_DEPTH = 3
LOGIC_PATTERN_PREFIX = "SIG-LOGIC-"
# 窗口有界化 (W5 回归发现: god-file 全文件窗口 + 无 cap BFS 导致窗口爆炸)
ENTRY_LINE_CONTEXT = 60   # 第 0 层: entry 行 ±N 行邻域
LAYER_CAP = 40            # 每层 BFS 新增节点上限
WINDOW_CAP = 300          # 总窗口节点上限

SKIP_DIRS = {".git", "node_modules", ".venv", "target", "build", "dist",
             ".build", "vendor", "third_party", ".audit_results", "spec"}

# 仅索引源码文件 (W5 回归发现: README/文档/JSON 产物中的示例代码
# 会被窗口展开当真实调用点, 造成自我引用污染)
CODE_EXTENSIONS = {".c", ".h", ".cc", ".cpp", ".hpp", ".rs", ".rb", ".py",
                   ".js", ".ts", ".java", ".go", ".php", ".swift", ".kt",
                   ".scala", ".cs", ".pl", ".pm", ".sh", ".ps1", ".m", ".mm"}


def build_project_index(project_root):
    """SWR-V3-020: {callee_name: [(file, line, caller_func)]} 轻量调用索引。
    函数定义与调用点均由正则粗粒度识别（服务于窗口展开，不需完整调用图精度）。"""
    index = {}
    # Ruby 方法名带 ! ? = 后缀 (dispatch!/call!/merge!/attr=); 对 C 系语言 `foo!(x)` 的
    # 副作用仅为多一个 foo! 索引条目 (窗口展开提示用, 无害)
    # \b 前缀必须: 否则 "#ifdef _WIN32" 的 "def" 会把 _WIN32 当函数定义 (lighttpd 实测)
    def_re = re.compile(r"\b(?:fn|def|func|function|sub)\s+([A-Za-z_][\w]*[!?=]?)|"
                        r"public\s+(?:static\s+)?[\w<>\[\],? ]+\s+([A-Za-z_][\w]*[!?=]?)\s*\(")
    # C 系函数定义: 行首缩进后 类型词序列 + 名字 + '(' (排除关键字/预处理)
    c_def_re = re.compile(r"^\s*(?:[A-Za-z_][\w]*[\s*]+)+([A-Za-z_][\w]*)\s*\([^;]*$")
    c_keywords = {"if", "for", "while", "switch", "return", "else", "case", "sizeof"}
    call_re = re.compile(r"\b([A-Za-z_][\w]*[!?]?)\s*\(")
    # Ruby 无括号裸调用 (invoke { dispatch! }): 仅 !/? 后缀裸词, 惯例上必是方法调用
    bare_call_re = re.compile(r"\b([A-Za-z_][\w]*[!?])(?![\w(])")
    for dirpath, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if os.path.splitext(fname)[1].lower() not in CODE_EXTENSIONS:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                lines = open(fpath, errors="ignore").read().splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, 1):
                for m in call_re.finditer(line):
                    name = m.group(1)
                    if name in ("if", "for", "while", "switch", "catch", "return"):
                        continue
                    index.setdefault(name, []).append(
                        {"file": fpath, "line": lineno,
                         "caller": _current_func(lines, lineno)})
                for m in bare_call_re.finditer(line):
                    name = m.group(1)
                    index.setdefault(name, []).append(
                        {"file": fpath, "line": lineno,
                         "caller": _current_func(lines, lineno)})
    return index


def _current_func(lines, lineno):
    """向上找最近的函数定义行作为调用者函数名（粗粒度）。
    C 系: 行首类型序列+名字+( 且名字非关键字; 脚本系: fn/def/func/function/sub。"""
    re_def = re.compile(r"\b(?:fn|def|func|function|sub)\s+([A-Za-z_][\w]*[!?=]?)")
    c_def_re = re.compile(r"^\s*(?:[A-Za-z_][\w]*[\s*]+)+([A-Za-z_][\w]*)\s*\(")
    c_keywords = {"if", "for", "while", "switch", "return", "else", "case", "sizeof"}
    for i in range(lineno - 1, max(lineno - 200, -1), -1):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re_def.search(line)
        if m:
            return m.group(1)
        m2 = c_def_re.match(line)
        if m2 and m2.group(1) not in c_keywords:
            return m2.group(1)
    return "<toplevel>"


def expand_window(entry, project_index, depth=DEFAULT_DEPTH):
    """SWR-V3-021: 从 entry 沿调用图展开 depth 层，返回窗口内调用点集合。
    第 0 层 = entry 行 ±ENTRY_LINE_CONTEXT 行邻域内的调用点（近似 entry 所在函数;
    W5 回归发现: "整个文件全部调用点"在 god-file 上爆炸——base.rb 2000 行
    直接窗口覆盖全库）。每层 BFS 带 cap, 总窗口带 cap。"""
    window = []
    seen = set()
    if os.path.exists(entry["file"]):
        lines = open(entry["file"], errors="ignore").read().splitlines()
        call_re = re.compile(r"\b([A-Za-z_][\w]*)\s*\(")
        lo = max(1, entry["line"] - ENTRY_LINE_CONTEXT)
        hi = min(len(lines), entry["line"] + ENTRY_LINE_CONTEXT)
        for lineno in range(lo, hi + 1):
            for m in call_re.finditer(lines[lineno - 1]):
                site = {"file": entry["file"], "line": lineno, "callee": m.group(1)}
                k = (site["file"], site["line"])
                if k not in seen:
                    seen.add(k)
                    window.append(site)
    # 第 1..depth 层: 被调用函数的所有调用点（反向: 找到调用它的位置）;
    # 下层 frontier = 新增调用点所在行的全部被调名 (逐层向调用方展开)
    frontier = [s["callee"] for s in list(window)]
    file_line_cache = {}
    for _ in range(depth):
        next_frontier = set()
        for callee in frontier:
            for call_site in project_index.get(callee, []):
                k = (call_site["file"], call_site["line"])
                if k not in seen:
                    seen.add(k)
                    window.append({"file": call_site["file"], "line": call_site["line"],
                                   "callee": callee})
                    if call_site["file"] not in file_line_cache:
                        try:
                            file_line_cache[call_site["file"]] = open(
                                call_site["file"], errors="ignore").read().splitlines()
                        except OSError:
                            file_line_cache[call_site["file"]] = []
                    if 1 <= call_site["line"] <= len(file_line_cache[call_site["file"]]):
                        line = file_line_cache[call_site["file"]][call_site["line"] - 1]
                        next_frontier.update(m.group(1) for m in
                                             call_re.finditer(line))
                    if len(window) >= WINDOW_CAP:
                        break
            if len(window) >= WINDOW_CAP:
                break
        frontier = list(next_frontier)[:LAYER_CAP]  # 每层 cap; 空则终止
        if len(window) >= WINDOW_CAP:
            break
    return window


def match_signatures(surfaces, signatures, project_index, depth=DEFAULT_DEPTH):
    """SWR-V3-022: 对窗口内调用点源码行跑签名 grep hints。
    产出 Hit = {surface_id, sig_id, site(file,line), matched_pattern, line_text}"""
    hits = []
    compiled = {}
    for sig in signatures:
        try:
            compiled[sig["sig_id"]] = [re.compile(p) for p in sig["detection_hints"]["grep"]]
        except re.error as e:
            raise ValueError(f"{sig['sig_id']}: {e}")
    file_cache = {}
    # v3.2 (SWR-V3.2-020): L2 词族按 surface.lang 过滤——C 词族不打 Rust surface
    # v3.3.1: surface lang 归一化——R1 测绘产出常见带点扩展名形态 ('.c') 或
    # 别名 (ts/sh/kt/ps1), 与签名 lang 词表 (c/typescript/shell/kotlin/powershell)
    # 不一致时 L2 过滤静默全不命中 (Lua 审计 0 hits 的另一半根因)
    def _sig_applicable(sig, surface):
        if sig.get("tier") == "L2" and sig.get("lang"):
            # v3.5.2 (P3): 双侧归一化——签名标签允许内部名 (cs/typescript),
            # 归一后与 surface 规范名等值比较 (cs↔csharp, ts/typescript↔javascript)
            return norm_lang(surface.get("lang")) == norm_lang(sig["lang"])
        return True
    for surface in surfaces:
        for entry in surface.get("entry_points", []):
            window = expand_window(entry, project_index, depth)
            for site in window:
                # v3.2.2 (REQ-V3.2.2-003): tests/ 路径排除——
                # 测试辅助代码的匹配是噪声 (mbedtls tests/src/test_helpers 实证)
                parts = site["file"].replace(os.sep, "/").split("/")
                if any(p in ("tests", "test") for p in parts):
                    continue
                if site["file"] not in file_cache:
                    try:
                        file_cache[site["file"]] = open(site["file"], errors="ignore").read().splitlines()
                    except OSError:
                        file_cache[site["file"]] = []
                lines = file_cache[site["file"]]
                if not (1 <= site["line"] <= len(lines)):
                    continue
                for sig in signatures:
                    if not _sig_applicable(sig, surface):
                        continue
                    for pat in compiled[sig["sig_id"]]:
                        m = pat.search(lines[site["line"] - 1])
                        if m:
                            hits.append({
                                "surface_id": surface["id"],
                                "sig_id": sig["sig_id"],
                                "site": {"file": site["file"], "line": site["line"]},
                                "matched_pattern": pat.pattern,
                                "line_text": lines[site["line"] - 1].strip()[:200],
                                "lang": surface.get("lang"),  # v3.2 SWR-V3.2-021
                            })
                            break  # 同一签名同一行只记 1 条
    return hits


def gen_hypotheses(hits, signatures):
    """SWR-V3-023: 去重(同 surface×sig 合并)、附 checklist/semantic_family、生成 HYP-xxx。
    SWR-V3-025: LOGIC_PATTERN 签名独立队列 logic_hypotheses。
    SWR-V3.1-051: L1 签名命中不生成假设（仅作阅读提示, 返回 reading_hints）。"""
    by_sig = {s["sig_id"]: s for s in signatures}
    groups = {}
    for h in hits:
        key = (h["surface_id"], h["sig_id"])
        groups.setdefault(key, []).append(h)
    hypotheses, logic_hypotheses, reading_hints, n = [], [], [], 0
    for (surf, sig_id), hs in sorted(groups.items()):
        sig = by_sig.get(sig_id, {})
        if sig.get("tier") != "L3":
            # v3.1 (W6 §14.1/§19.1) + v3.2.2 (REQ-V3.2.2-004):
            # L1/L2 词族命中零假设, 仅作阅读提示——假设生成主路径是 LLM 基于 surface 图,
            # 词族命中是佐证器 (mbedtls 审计: L2 pickle/get_host 词族产出跨项目假族)
            reading_hints.append({
                "signature_id": sig_id,
                "surface_id": surf,
                "tier": sig.get("tier", "L2"),
                "sites": [{"file": h["site"]["file"], "line": h["site"]["line"],
                           "matched": h["matched_pattern"]} for h in hs],
                "note": f"{sig.get('tier', 'L1/L2')} 词族命中: 仅作佐证/阅读提示, 不生成假设"})
            continue
        n += 1
        hyp = {
            "id": f"HYP-{n:03d}",
            "surface_id": surf,
            "signature_id": sig_id,
            "semantic_family": sig.get("semantic", ""),
            "cwe": sig.get("cwe", []),
            "checklist": sig.get("detection_hints", {}).get("checklist", []),
            "hit_sites": [{"file": h["site"]["file"], "line": h["site"]["line"],
                           "matched": h["matched_pattern"],
                           "line_text": h["line_text"]} for h in hs],
            "status": "PENDING",
            "sources": [sig_id],  # v3.1 贡献度度量 (W6 设计 P-A)
        }
        if sig_id.startswith(LOGIC_PATTERN_PREFIX):
            logic_hypotheses.append(hyp)
        else:
            hypotheses.append(hyp)
    return {"hypotheses": hypotheses, "logic_hypotheses": logic_hypotheses,
            "reading_hints": reading_hints}


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "index":
        root = argv[2]
        idx = build_project_index(root)
        out = argv[3] if len(argv) > 3 else os.path.join(
            root, ".audit_results", "project_index.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(idx, open(out, "w"))
        print(f"index: {len(idx)} callees -> {out}")
        return 0
    if cmd == "match":
        surfaces = json.load(open(argv[2]))
        index = json.load(open(argv[3]))
        sigs = signature_lib.load()["signatures"]
        hits = match_signatures(surfaces["surfaces"], sigs, index)
        # R0 铁律: 产物必须以 .audit_results/ 为前缀——默认落盘到
        # surfaces 文件同目录 (即 <project>/.audit_results/)
        out = argv[4] if len(argv) > 4 else os.path.join(
            os.path.dirname(os.path.abspath(argv[2])), "hits.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump({"hits": hits}, open(out, "w"), ensure_ascii=False, indent=2)
        print(f"{len(hits)} hits -> {out}")
        return 0
    if cmd == "gen":
        hits = json.load(open(argv[2]))["hits"]
        sigs = signature_lib.load()["signatures"]
        hyps = gen_hypotheses(hits, sigs)
        # SWR-V3.4.5-001: 文件所有权分离——佐证器输出独立文件
        # hypotheses_gen.json, 禁止与 LLM 主路径共享 hypotheses.json
        # (gRPC 审计: gen 曾覆盖主代理先写的 LLM 假设清单)
        out = argv[3] if len(argv) > 3 else os.path.join(
            os.path.dirname(os.path.abspath(argv[2])), "hypotheses_gen.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        main_hyp = os.path.join(os.path.dirname(out), "hypotheses.json")
        if os.path.exists(main_hyp):
            print(f"warn: {main_hyp} 已存在 (属 LLM 主路径产物), "
                  f"佐证器输出至 {os.path.basename(out)}, 主代理需合并而非覆盖")
        json.dump(hyps, open(out, "w"), ensure_ascii=False, indent=2)
        print(f"{len(hyps['hypotheses'])} hypotheses + {len(hyps['logic_hypotheses'])} logic -> {out}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
