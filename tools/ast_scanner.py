import os
import re
import json
import sys
import warnings

NON_SOURCE_EXTS = {
    "", ".md", ".txt", ".json", ".lock", ".yaml", ".yml", ".toml", ".xml",
    ".html", ".css", ".csv", ".tsv", ".svg", ".png", ".jpg", ".jpeg", ".gif",
    ".pdf", ".zip", ".gz", ".tar", ".ico", ".map",
}

# Tree-sitter 兼容层: 同时支持旧版 tree_sitter_languages 和新版独立语言包 (v0.26+)
HAS_TREE_SITTER = False
TS_QUERY_OLD_API = False  # True=tree_sitter_languages, False=独立包 v0.26+
TS_GET_LANG = None
TS_GET_PARSER = None
TS_QUERY_CLS = None
TS_CURSOR_CLS = None

# 语言 → tree-sitter 独立包名称映射
_TS_PACKAGES = {
    "java": "tree_sitter_java",
    "cpp": "tree_sitter_cpp",
    "python": "tree_sitter_python",
    "javascript": "tree_sitter_javascript",
    "go": "tree_sitter_go",
    "rust": "tree_sitter_rust",
    "csharp": "tree_sitter_c_sharp",
    "php": "tree_sitter_php",
    "ruby": "tree_sitter_ruby",
    "swift": "tree_sitter_swift",
    "kotlin": "tree_sitter_kotlin",
    "scala": "tree_sitter_scala",
    "shell": "tree_sitter_bash",
    "perl": "tree_sitter_perl",
    "powershell": None,
}

try:
    import tree_sitter_languages
    HAS_TREE_SITTER = True
    TS_QUERY_OLD_API = True
    TS_GET_LANG = tree_sitter_languages.get_language
    TS_GET_PARSER = tree_sitter_languages.get_parser
except ImportError:
    try:
        import tree_sitter
        HAS_TREE_SITTER = True
        TS_QUERY_OLD_API = False
        from tree_sitter import Language, Parser, Query, QueryCursor as QC
        # tree-sitter 0.26 的 Language(PyCapsule) 会触发 DeprecationWarning，无害，抑制之
        warnings.filterwarnings("ignore", message="int argument support is deprecated", category=DeprecationWarning)
        TS_QUERY_CLS = Query
        TS_CURSOR_CLS = QC

        _TS_LANG_CACHE = {}
        for _ts_lang, _ts_mod_name in _TS_PACKAGES.items():
            if _ts_mod_name is None:
                continue
            try:
                _ts_mod = __import__(_ts_mod_name, fromlist=["language"])
                _ts_lang_func = None
                for _attr in ("language", f"language_{_ts_lang}", "lang"):
                    if hasattr(_ts_mod, _attr):
                        _ts_lang_func = getattr(_ts_mod, _attr)
                        break
                if _ts_lang_func is None:
                    continue
                _TS_LANG_CACHE[_ts_lang] = Language(_ts_lang_func())
            except ImportError:
                pass

        def TS_GET_LANG(lang):
            lang_obj = _TS_LANG_CACHE.get(lang)
            if lang_obj is None:
                raise ImportError(f"No tree-sitter grammar for '{lang}'")
            return lang_obj

        def TS_GET_PARSER(lang):
            p = Parser()
            p.language = TS_GET_LANG(lang)
            return p
    except ImportError:
        pass

# 统一执行 tree-sitter 查询: 返回 [(node, tag_name), ...]
def _ts_run_query(lang_obj, query_str, root_node):
    if TS_QUERY_OLD_API:
        query = lang_obj.query(query_str)
        return list(query.captures(root_node))
    # New API (v0.26+)
    query = TS_QUERY_CLS(lang_obj, query_str)
    cursor = TS_CURSOR_CLS(query)
    results = []
    for pattern_idx, capture_dict in cursor.matches(root_node):
        for tag, nodes in capture_dict.items():
            for node in nodes:
                results.append((node, tag))
    return results


# 每语言冒烟测试代码片段: 必须真实触发该语言最常见的高危 sink 调用,
# 用于验证规则库的 AST pattern / 结构化模型是否真的能命中语法树。
# 规则库中与这些片段无关的规则 (如 Java 规则命中 Python 片段) 不算失效。
SMOKE_SAMPLES = {
    "java": "void f() { Runtime.getRuntime().exec(userInput); String q = \"SELECT * FROM t WHERE id=\" + id; Class.forName(userInput); }",
    "cpp": 'void f() { memcpy(dst, src, userLen); char *p = (char*)malloc(userSize); system(userCmd); strcpy(dst, src); }',
    "python": "import os, subprocess, pickle\ndef f(): os.system(user_cmd); subprocess.call(user_args, shell=True); eval(user_code); pickle.loads(user_data)",
    "javascript": "function f() { eval(userCode); require(userMod); child_process.exec(userCmd); }",
    "go": 'func f() { cmd := exec.Command("sh", "-c", userInput); err := os.Chdir(userPath); result := xpath.Compile(userExpr) }',
    "rust": "fn f() { let out = Command::new(\"sh\").arg(\"-c\").arg(userInput); let p = File::open(userPath).unwrap(); let v = Vec::with_capacity(userSize); std::process::exit(0); }",
    "csharp": "void f() { var p = System.Diagnostics.Process.Start(\"/bin/sh\", userInput); var q = \"SELECT * FROM t WHERE id=\" + id; }",
    "php": "<?php system($userCmd); eval($userCode); $stmt = mysqli_query($conn, \"SELECT * FROM t WHERE id=$id\"); ?>",
    "ruby": "def f; system(user_cmd); eval(user_code); conn.execute(\"SELECT * FROM t WHERE id=\" + id); end",
    "swift": 'import Foundation\nfunc f() { let d = try Data(contentsOf: userURL); let p = Process(); p.executableURL = URL(fileURLWithPath: "/bin/sh"); p.arguments = ["-c", userCmd]; }',
    "kotlin": "fun f() { Runtime.getRuntime().exec(userInput); val q = \"SELECT * FROM t WHERE id=\" + id; Class.forName(userInput) }",
    "scala": "object A { def f() { import sys.process._; userInput.!; java.lang.Runtime.getRuntime().exec(userInput) } }",
    "shell": "#!/bin/bash\ncat /etc/shadow\neval \"$USER_INPUT\"\nexec \"$USER_CMD\"",
    "perl": 'sub f { system($userCmd); eval($userCode); open(my $fh, "<", $userPath); }',
    "powershell": "Invoke-Expression $userCode; Start-Process $userCmd; Get-Content $userPath",
}


def _smoke_check_language(lang, lang_rules):
    """冒烟测试: 用该语言典型 sink 片段解析语法树, 运行每条规则,
    返回 {rule_cwe: True(命中)/False(未命中)} 与片段解析是否成功。

    为避免把"片段未覆盖的 API"误判为 pattern 错配, 每条规则只在
    冒烟片段中确实出现其 sink 关键字/方法名时才计入测试 (否则标记
    为 skipped, 不计入命中率分母)。完全无法验证的规则由调用方告警。"""
    if lang not in SMOKE_SAMPLES:
        return {}, False
    sample = SMOKE_SAMPLES[lang]
    try:
        lang_obj = TS_GET_LANG(lang)
        parser = TS_GET_PARSER(lang)
        tree = parser.parse(bytes(sample, "utf8"))
        root_node = tree.root_node
        sample_text = sample.encode("utf-8")
        parse_ok = (root_node.has_error is False) or (root_node.child_count > 0)
    except Exception:
        return {}, False

    per_rule = {}
    for r in lang_rules:
        cwe = r.get("cwe_id", "?")
        sinks = r.get("sinks", {})
        # 收集该规则的 sink 关键字 (ast_patterns 里的标识符 + 结构化模型 method/signature)
        keys = []
        for qs in sinks.get("ast_patterns", []):
            for tok in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", qs):
                keys.append(tok)
        for key in ("go_models", "swift_models"):
            for m in sinks.get(key, []):
                meth = m.get("method") or ""
                sig = m.get("signature") or ""
                if meth:
                    keys.append(meth)
                if sig:
                    keys.append(sig.split("(")[0].strip())
        # 片段中出现任意 sink 关键字 → 该规则可测试; 否则跳过 (不误判)
        present = [k for k in keys if k and k in sample_text.decode("utf-8", errors="ignore")]
        if not present:
            per_rule[cwe] = None  # skipped: 片段未覆盖, 不计入命中率
            continue

        hits = False
        # 1) AST S-expression pattern 真实执行
        for qs in sinks.get("ast_patterns", []):
            try:
                if _ts_run_query(lang_obj, qs, root_node):
                    hits = True
                    break
            except Exception:
                pass
        # 2) 结构化模型 method/signature 名出现即视为可命中 (方法名级可解析性)
        if not hits:
            for key in ("go_models", "swift_models"):
                for m in sinks.get(key, []):
                    meth = m.get("method") or ""
                    sig = m.get("signature") or ""
                    base = sig.split("(")[0].strip() if sig else ""
                    if (meth and f".{meth}" in sample) or (base and base in sample):
                        hits = True
                        break
                if hits:
                    break
        per_rule[cwe] = hits
    return per_rule, parse_ok

def _anchor_check_language(lang, lang_rules, anchors):
    """锚点召回测试 (REQ-24): 对每个 ground-truth CVE 锚点, 运行该语言全部
    规则的 sink (regex + ast_patterns) 判断是否命中。返回 {anchor_index: bool}。

    锚点必须被该语言任意一条规则捕获, 否则该语言规则库存在攻击面盲区,
    --self-check 判 FAIL (阻止审计启动)。"""
    if not anchors or lang not in SMOKE_SAMPLES:
        # 无锚点或该语言无冒烟片段 (grammar 未装) 时跳过, 由调用方处理
        return None
    try:
        lang_obj = TS_GET_LANG(lang)
        parser = TS_GET_PARSER(lang)
    except Exception:
        return None
    results = {}
    for idx, anchor in enumerate(anchors):
        sample = anchor.get("sample_code", "")
        if not sample:
            results[idx] = None
            continue
        try:
            tree = parser.parse(bytes(sample, "utf8"))
            root_node = tree.root_node
            sample_text = sample.encode("utf-8")
        except Exception:
            results[idx] = False
            continue
        hit = False
        for r in lang_rules:
            sinks = r.get("sinks", {})
            # 1) AST pattern 真实执行
            for qs in sinks.get("ast_patterns", []):
                try:
                    if _ts_run_query(lang_obj, qs, root_node):
                        hit = True
                        break
                except Exception:
                    pass
            if hit:
                break
            # 2) regex sink 命中
            for rx in sinks.get("regex", []):
                try:
                    if re.search(rx, sample_text.decode("utf-8", errors="ignore")):
                        hit = True
                        break
                except Exception:
                    pass
            if hit:
                break
        results[idx] = hit
    return results

class ASTCoarseScanner:
    EXTENSION_MAP = {
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "cpp",
        ".h": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
        ".c++": "cpp",
        ".h++": "cpp",
        ".py": "python",
        ".pyw": "python",
        ".go": "go",
        ".rs": "rust",
        ".js": "javascript",
        ".ts": "javascript",
        ".jsx": "javascript",
        ".tsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".cs": "csharp",
        ".csx": "csharp",
        ".php": "php",
        ".phtml": "php",
        ".php3": "php",
        ".php4": "php",
        ".php5": "php",
        ".phps": "php",
        ".rb": "ruby",
        ".rbw": "ruby",
        ".rake": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".scala": "scala",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".pl": "perl",
        ".pm": "perl",
        ".t": "perl",
        ".ps1": "powershell"
    }

    def __init__(self, profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)

    def scan(self, workspace_path):
        candidates = []
        rules = self.profile.get("rules", {})
        lang_hits = {}
        total_source_files = 0
        unknown_extensions = {}

        # PROPERTY_CHECK 模式 (REQ-05) — 独立于语言识别, 对所有文件运行
        # (exported_no_permission 的锚点是 AndroidManifest.xml, 不在 EXTENSION_MAP 内)
        prop_patterns_raw = self.profile.get("property_check_patterns", [])
        prop_patterns = prop_patterns_raw.get("patterns", []) if isinstance(prop_patterns_raw, dict) else prop_patterns_raw

        for root, dirs, files in os.walk(workspace_path):
            rel_root = os.path.relpath(root, workspace_path)
            if rel_root != "." and self._is_ignored_path(rel_root):
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not self._is_ignored_path(
                d if rel_root == "." else os.path.join(rel_root, d)
            )]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                lang = self.EXTENSION_MAP.get(ext)
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, workspace_path)

                # R1.5 强制触发条件: 统计源文件数（所有非 .min. 文件）
                if ".min." not in file:
                    total_source_files += 1

                # L2 fallback 检测: 记录未能映射到预设语言的扩展名
                if not lang and ext not in NON_SOURCE_EXTS:
                    unknown_extensions[ext] = unknown_extensions.get(ext, 0) + 1

                # 读取文件内容 (源码规则 + property-check 共用)
                content = None
                if (lang and lang in rules) or prop_patterns:
                    try:
                        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f_code:
                            content = f_code.read()
                    except Exception:
                        content = None

                # ---- 源码语言规则扫描 (仅预设语言) ----
                if content is not None and lang and lang in rules:
                    if lang not in lang_hits:
                        lang_hits[lang] = 0
                    lang_rules = rules[lang]

                    # 收集 sinks 下的规则
                    ast_queries = []
                    regex_patterns = []
                    for item in lang_rules:
                        sinks = item.get("sinks", {})
                        if "ast_patterns" in sinks:
                            ast_queries.extend(sinks["ast_patterns"])
                        if "regex" in sinks:
                            # Go/Swift CodeQL rules now carry structured model
                            # context.  Do not run broad bare-name regex for
                            # these rules (`Exec(`, `Query(`, `init(`), because
                            # it creates high-noise candidates unrelated to the
                            # modeled package/type.
                            if lang == "go" and sinks.get("go_models"):
                                continue
                            if lang == "swift" and sinks.get("swift_models"):
                                continue
                            regex_patterns.extend(sinks["regex"])

                    ast_success = False
                    # 1. 尝试使用 Tree-Sitter 语法解析
                    if HAS_TREE_SITTER and ast_queries:
                        try:
                            ast_candidates = self._scan_via_tree_sitter(content, lang, ast_queries, rel_path, rules[lang])
                            candidates.extend(ast_candidates)
                            ast_success = True
                        except Exception as e:
                            # 语法解析报错，打印日志并降级到正则
                            sys.stderr.write(f"[Warning] AST scan failed for {rel_path}: {str(e)}. Falling back to regex...\n")

                    structured_candidates = self._scan_structured_models(content, lang, rel_path, lang_rules)
                    candidates.extend(structured_candidates)

                    # 2. 正则粗筛始终执行，AST 命中用于提升置信度；缺少 AST 支撑的
                    #    正则候选会在 _scan_via_regex 中降级为 NEEDS_REVIEW。
                    if regex_patterns:
                        line_candidates = self._scan_via_regex(content, regex_patterns, rel_path, lang, rules[lang])
                        candidates.extend(line_candidates)

                # ---- PROPERTY_CHECK 扫描 (所有文件, 语言无关) ----
                if content is not None and prop_patterns:
                    prop_candidates = self._scan_property_checks(content, prop_patterns, rel_path, lang)
                    candidates.extend(prop_candidates)

        # 编号并规范化 Schema 输出 (REQ-02, REQ-09)
        candidates = self._dedupe_candidates(candidates)
        for idx, cand in enumerate(candidates, 1):
            cand["id"] = f"CAND-{idx:03d}"
            cand["origin"] = cand.get("origin", "L0")
            cand["source_file"] = cand.get("file_path", "")
            cand["source_line"] = cand.get("line_number", 0)
            cand["sink_type"] = cand.get("cwe_id", "Unknown")
            status = cand.get("status")
            verdict = cand.get("verdict")
            if status in ("REACHABLE", "UNREACHABLE", "NEEDS_REVIEW"):
                cand["status"] = "VERIFIED"
                cand["verdict"] = verdict if verdict in ("REACHABLE", "UNREACHABLE", "NEEDS_REVIEW") else status
            else:
                cand["status"] = status if status in ("PENDING", "VERIFIED") else "PENDING"
                cand["verdict"] = verdict if verdict in ("REACHABLE", "UNREACHABLE", "NEEDS_REVIEW") else None
            cand["reachability_type"] = None
            cand["blocking_point"] = None
            # 统计语言命中数
            lang = cand.get("language", "")
            if lang:
                lang_hits[lang] = lang_hits.get(lang, 0) + 1

        # 过滤 test/build/third-party 候选 + 按 CWE 标记优先级 (语言无关)
        filtered, discarded = self._filter_and_prioritize(candidates)

        # 按优先级统计
        priority_dist = {}
        for c in filtered:
            p = c.get("priority", 2)
            priority_dist[p] = priority_dist.get(p, 0) + 1

        # L2 fallback: 非预设语言扩展
        l2_exts = [
            {"ext": ext, "count": cnt}
            for ext, cnt in sorted(unknown_extensions.items(), key=lambda x: -x[1])
        ]
        l2_required = (
            len(filtered) == 0 and len(l2_exts) > 0 and total_source_files > 0
        )

        # 主体语言统计
        lang_file_counts = {}
        for root, dirs, files in os.walk(workspace_path):
            rel_root = os.path.relpath(root, workspace_path)
            if rel_root != "." and self._is_ignored_path(rel_root):
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not self._is_ignored_path(
                d if rel_root == "." else os.path.join(rel_root, d)
            )]
            for file in files:
                if ".min." in file:
                    continue
                ext = os.path.splitext(file)[1].lower()
                lang = self.EXTENSION_MAP.get(ext)
                if lang:
                    lang_file_counts[lang] = lang_file_counts.get(lang, 0) + 1

        scan_meta = {
            "total_source_files": total_source_files,
            "raw_candidates": len(candidates),
            "discarded_test_build": discarded,
            "candidates_after_filter": len(filtered),
            "priority_distribution": priority_dist,
            "r1_5_required": True,  # R1.5 始终执行
            "l2_required": l2_required,
            "l2_exts": l2_exts,
            "l2_note": (
                f"项目含 {len(l2_exts)} 种非预设语言扩展名 "
                f"({', '.join(e['ext'] for e in l2_exts[:5])})"
                if l2_required else None
            )
        }
        return filtered, scan_meta

    def _scan_property_checks(self, content, prop_patterns, file_path, lang):
        """PROPERTY_CHECK 锚点扫描 (REQ-05)。

        property_check_patterns 的 `detect` 字段是**自然语言语义描述**(如
        "方法体内未出现 owner 比对")，无法作为逐行正则匹配——缺失型判定必须
        交给 R3 子智能体研判。scanner 在此只负责用各 pattern 的**可机器匹配
        字段**定位可疑锚点行，并把语义描述带入 `verification_logic`：
          - anchor_regex: 直接作为正则匹配 (如 exported=true)
          - anchor_hints.<lang>: 语言相关关键字, 转义后子串匹配
          - sinks: 函数/前缀名列表, 转义后作为调用点匹配 (如 setuid()
                   privilege_boundary_skip); 以 `_` 结尾视为前缀 (capng_*)
          - files: 仅当当前文件名匹配时才生效 (如 AndroidManifest.xml)
        """
        candidates = []
        lines = content.splitlines()
        base_name = os.path.basename(file_path)

        for prop in prop_patterns:
            pid = prop.get("id", "PROPERTY_CHECK")
            cwe_id = prop.get("cwe_id", "CWE-862")

            # files 约束: pattern 限定文件名时, 不匹配则整体跳过
            file_globs = prop.get("files", [])
            if file_globs:
                import fnmatch
                if not any(fnmatch.fnmatch(base_name, g) for g in file_globs):
                    continue

            # 组装该 pattern 在当前语言下的匹配器: (compiled_regex, raw)
            matchers = []
            for rx_pat in prop.get("anchor_regex", []):
                try:
                    matchers.append((re.compile(rx_pat), rx_pat))
                except re.error:
                    pass
            hints = prop.get("anchor_hints", {}).get(lang, [])
            for h in hints:
                matchers.append((re.compile(re.escape(h)), h))
            for s in prop.get("sinks", []):
                # `capng_` 这类前缀 → 匹配 前缀+标识符+( ; 普通名 → 名+(
                if s.endswith("_"):
                    matchers.append((re.compile(re.escape(s) + r"\w*\s*\("), s))
                else:
                    matchers.append((re.compile(r"\b" + re.escape(s) + r"\s*\("), s))

            if not matchers:
                continue

            verification_logic = prop.get("verification_logic", prop.get("detect", ""))

            for idx, line in enumerate(lines):
                for rx, raw in matchers:
                    try:
                        if rx.search(line):
                            sink_content = line.strip()
                            if len(sink_content) > 1000:
                                sink_content = sink_content[:1000] + "... [TRUNCATED]"
                            candidates.append({
                                "language": lang,
                                "cwe_id": cwe_id,
                                "category": pid,
                                "type": "PROPERTY_CHECK",
                                "file_path": file_path,
                                "line_number": idx + 1,
                                "sink_content": sink_content,
                                "matched_hint": raw,
                                "origin": "L0",
                                "status": "PENDING",
                                "sources_regex": [],
                                "reachability_constraints": prop.get("detect", ""),
                                "verification_logic": verification_logic
                            })
                            break
                    except Exception:
                        pass
        return candidates

    def _scan_via_tree_sitter(self, content, lang, ast_queries, file_path, lang_rules):
        lang_obj = TS_GET_LANG(lang)
        parser = TS_GET_PARSER(lang)
        
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        candidates = []
        lines = content.splitlines()

        for query_str in ast_queries:
            captures = _ts_run_query(lang_obj, query_str, root_node)
            for node, tag in captures:
                line_no = node.start_point[0] + 1
                line_content = lines[line_no - 1] if line_no <= len(lines) else ""
                
                # 匹配该 S-expression 属于哪一个 CWE
                matched_rule = self._find_rule_by_ast(lang_rules, query_str)
                cwe_id = matched_rule.get("cwe_id")

                # Rust unsafe 安全注释豁免 (REQ-22)
                is_rust_unsafe = (lang == "rust" and cwe_id in ("CWE-119", "CWE-416", "CWE-787"))
                if is_rust_unsafe:
                    start = max(0, line_no - 9)
                    end = min(len(lines), line_no + 2)
                    rust_exempted = False
                    for ctx_line in lines[start:end]:
                        stripped = ctx_line.strip()
                        if stripped.startswith("// Safety:") or stripped.startswith("# Safety:") or \
                           stripped.startswith("// SAFETY:") or stripped.startswith("// safety:") or \
                           stripped.startswith("/* Safety:") or stripped.startswith("/* SAFETY:"):
                            rust_exempted = True
                            break
                    if rust_exempted:
                        continue

                # Optimization 1: 初筛漏斗过滤优化
                if cwe_id == "CWE-476" and lang == "cpp":
                    try:
                        ptr_name = node.text.decode('utf-8', errors='ignore').lstrip('*').strip()
                        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_\->\.]*$', ptr_name):
                            checked = False
                            for pre_line in lines[max(0, line_no - 6):line_no - 1]:
                                if re.search(r'\b' + re.escape(ptr_name) + r'\b', pre_line):
                                    if 'NULL' in pre_line or '== 0' in pre_line or '!= 0' in pre_line or '!' in pre_line or 'if' in pre_line:
                                        checked = True
                                        break
                            if checked:
                                continue
                    except Exception:
                        pass
                
                sink_content = line_content.strip()
                if len(sink_content) > 1000:
                    sink_content = sink_content[:1000] + "... [TRUNCATED]"

                candidates.append({
                    "language": lang,
                    "cwe_id": matched_rule["cwe_id"],
                    "category": matched_rule["category"],
                    "type": matched_rule.get("type", "TAINT_ANALYSIS"),
                    "file_path": file_path,
                    "line_number": line_no,
                    "sink_content": sink_content,
                    "origin": "L0",
                    "status": "PENDING",
                    "sources_regex": matched_rule.get("sources", {}).get("regex", []),
                    "reachability_constraints": matched_rule.get("reachability_constraints", ""),
                    "verification_logic": matched_rule.get("verification_logic", "")
                })
        return candidates

    def _scan_structured_models(self, content, lang, file_path, lang_rules):
        if lang not in ("go", "swift"):
            return []
        candidates = []
        lines = content.splitlines()
        go_imports = self._go_import_aliases(content) if lang == "go" else {}

        for rule in lang_rules:
            sinks = rule.get("sinks", {})
            model_key = "go_models" if lang == "go" else "swift_models"
            models = sinks.get(model_key, [])
            if not isinstance(models, list) or not models:
                continue
            for line_idx, line in enumerate(lines):
                for model in models:
                    if not isinstance(model, dict):
                        continue
                    if lang == "go":
                        matched = self._line_matches_go_model(line, model, go_imports, content)
                    else:
                        matched = self._line_matches_swift_model(line, model, content)
                    if not matched:
                        continue
                    sink_content = line.strip()
                    if len(sink_content) > 1000:
                        sink_content = sink_content[:1000] + "... [TRUNCATED]"
                    candidates.append({
                        "language": lang,
                        "cwe_id": rule["cwe_id"],
                        "category": rule["category"],
                        "type": rule.get("type", "TAINT_ANALYSIS"),
                        "file_path": file_path,
                        "line_number": line_idx + 1,
                        "sink_content": sink_content,
                        "origin": "L0",
                        "status": "PENDING",
                        "sources_regex": rule.get("sources", {}).get("regex", []),
                        "reachability_constraints": rule.get("reachability_constraints", ""),
                        "verification_logic": rule.get("verification_logic", ""),
                        "matched_model": {
                            "package": model.get("package", model.get("module", "")),
                            "type": model.get("type", ""),
                            "method": model.get("method", ""),
                            "signature": model.get("signature", ""),
                            "access_path": model.get("access_path", ""),
                            "sink_kind": model.get("sink_kind", ""),
                        },
                    })
                    break
        return candidates

    @staticmethod
    def _go_import_aliases(content):
        aliases = {}
        # Accept both single import lines and entries inside import (...).
        for m in re.finditer(
            r'(?m)^\s*(?:import\s+)?(?:(?P<alias>[A-Za-z_][A-Za-z0-9_]*|\.)\s+)?["`](?P<pkg>[^"`]+)["`]',
            content,
        ):
            pkg = m.group("pkg")
            alias = m.group("alias")
            if alias == ".":
                alias = ""
            if not alias:
                parts = [p for p in pkg.split("/") if p and not re.fullmatch(r"v\d+", p)]
                alias = parts[-1].replace("-", "_") if parts else ""
            aliases.setdefault(pkg, set()).add(alias)
        return aliases

    @staticmethod
    def _line_matches_go_model(line, model, imports, content):
        method = model.get("method", "")
        if not method:
            return False
        package = model.get("package", "")
        typ = model.get("type", "")

        aliases = imports.get(package, set()) if package else set()
        if package and not aliases and f'"{package}"' not in content and f"`{package}`" not in content:
            return False

        method_call = re.compile(r'(?:\.|\b)' + re.escape(method) + r'\s*\(')
        if typ:
            # Receiver type cannot be reliably known without type solving; require
            # package import plus selector-style method call as the conservative
            # local evidence.
            return bool(method_call.search(line))

        if aliases:
            for alias in aliases:
                if alias and re.search(r'\b' + re.escape(alias) + r'\s*\.\s*' + re.escape(method) + r'\s*\(', line):
                    return True
            return False

        # Empty package model: only accept direct calls, not arbitrary selectors.
        return bool(re.search(r'\b' + re.escape(method) + r'\s*\(', line))

    @staticmethod
    def _swift_first_label(signature):
        m = re.search(r'\(([^:),]+):', signature or "")
        return m.group(1) if m else ""

    @classmethod
    def _line_matches_swift_model(cls, line, model, content):
        method = model.get("method", "")
        signature = model.get("signature", "")
        typ = model.get("type", "")
        if not method:
            return False

        if method.startswith("sqlite3_"):
            return bool(re.search(r'\b' + re.escape(method) + r'\s*\(', line))

        first_label = cls._swift_first_label(signature)
        type_seen = bool(typ and re.search(r'\b' + re.escape(typ) + r'\b', line))

        if signature.startswith("init("):
            # Swift initializer syntax: Data(contentsOf: ...), Bundle(path: ...)
            if not typ or not first_label:
                return False
            return bool(re.search(
                r'\b' + re.escape(typ) + r'\s*\([^)]*\b' + re.escape(first_label) + r'\s*:',
                line,
            ))

        method_seen = bool(re.search(r'(?:\.|\b)' + re.escape(method) + r'\s*\(', line))
        label_seen = bool(first_label and re.search(r'\b' + re.escape(first_label) + r'\s*:', line))

        # For noisy names such as run/write/open, require the modeled type on the
        # same line.  For labeled Swift APIs, method+label is sufficiently
        # specific even if the receiver variable type is not locally visible.
        noisy = {"run", "write", "open", "set", "get", "load", "init"}
        if method in noisy:
            return type_seen and (method_seen or label_seen)
        if label_seen:
            return method_seen or type_seen
        return method_seen and (type_seen or not typ)

    def _scan_via_regex(self, content, regex_patterns, file_path, lang, lang_rules):
        candidates = []
        lines = content.splitlines()
        compiled = [(re.compile(pat), pat) for pat in regex_patterns]

        for line_idx, line in enumerate(lines):
            for rx, raw_pat in compiled:
                if rx.search(line):
                    matched_rule = self._find_rule_by_regex(lang_rules, raw_pat)
                    cwe_id = matched_rule.get("cwe_id")

                    # Optimization 1: Rust unsafe 安全注释豁免
                    # 如果 unsafe 调用行附近有 Safety 注释，标记为 NEEDS_REVIEW 而非 PENDING
                    is_rust_unsafe = (lang == "rust" and cwe_id in ("CWE-119", "CWE-416", "CWE-787"))
                    rust_exempted = False
                    if is_rust_unsafe:
                        start = max(0, line_idx - 8)
                        end = min(len(lines), line_idx + 3)
                        for ctx_line in lines[start:end]:
                            stripped = ctx_line.strip()
                            if stripped.startswith("// Safety:") or stripped.startswith("# Safety:") or \
                               stripped.startswith("// SAFETY:") or stripped.startswith("// safety:") or \
                               stripped.startswith("/* Safety:") or stripped.startswith("/* SAFETY:"):
                                rust_exempted = True
                                break
                    
                    # Optimization 2: 初筛漏斗过滤优化
                    if cwe_id == "CWE-476" and lang == "cpp":
                        try:
                            match_ptr = re.search(r'\*([a-zA-Z_][a-zA-Z0-9_\->\.]*)', line)
                            if match_ptr:
                                ptr_name = match_ptr.group(1).strip()
                                checked = False
                                for pre_line in lines[max(0, line_idx - 5):line_idx]:
                                    if re.search(r'\b' + re.escape(ptr_name) + r'\b', pre_line):
                                        if 'NULL' in pre_line or '== 0' in pre_line or '!= 0' in pre_line or '!' in pre_line or 'if' in pre_line:
                                            checked = True
                                            break
                                if checked:
                                    continue
                        except Exception:
                            pass

                    sink_content = line.strip()
                    if len(sink_content) > 1000:
                        sink_content = sink_content[:1000] + "... [TRUNCATED]"

                    # REQ-03: 正则降级扫描产生的候选点标记 ast_verified=False，若无 AST 精确校验支撑则降级为 NEEDS_REVIEW 初始候选
                    needs_review = HAS_TREE_SITTER and matched_rule.get("sinks", {}).get("ast_patterns")
                    # Rust unsafe 调用有 safety 注释时降级为 NEEDS_REVIEW（需人工复核）
                    if rust_exempted:
                        needs_review = True

                    candidates.append({
                        "language": lang,
                        "cwe_id": matched_rule["cwe_id"],
                        "category": matched_rule["category"],
                        "type": matched_rule.get("type", "TAINT_ANALYSIS"),
                        "file_path": file_path,
                        "line_number": line_idx + 1,
                        "sink_content": sink_content,
                        "origin": "L0",
                        "status": "VERIFIED" if needs_review else "PENDING",
                        "verdict": "NEEDS_REVIEW" if needs_review else None,
                        "sources_regex": matched_rule.get("sources", {}).get("regex", []),
                        "reachability_constraints": matched_rule.get("reachability_constraints", ""),
                        "verification_logic": matched_rule.get("verification_logic", "")
                    })
                    break
        return candidates

    # ---- 语言无关优先级与过滤 ----

    _CWE_PRIORITY = {
        "CWE-78": 0, "CWE-89": 0, "CWE-94": 0, "CWE-119": 0, "CWE-416": 0,
        "CWE-502": 0, "CWE-787": 0, "CWE-918": 0, "CWE-789": 0,
        "CWE-20": 1, "CWE-22": 1, "CWE-125": 1, "CWE-190": 1, "CWE-269": 1,
        "CWE-285": 1, "CWE-287": 1, "CWE-611": 1, "CWE-862": 1,
        "CWE-79": 2, "CWE-134": 2, "CWE-200": 2, "CWE-250": 2, "CWE-352": 2,
        "CWE-362": 2, "CWE-400": 2, "CWE-434": 2, "CWE-476": 2, "CWE-601": 2, "CWE-908": 2,
    }
    _IGNORE_PATH_PARTS = {
        "test", "tests", "mock", "mocks", "unittest", "mockcify",
        "tools", "tool", "build", "scripts", "scratch", "target", "dist",
        "node_modules", "vendor", "third_party", "libs", ".git", ".audit_results",
        ".agents", ".codex", ".venv", "__pycache__", "reachable-critical-audit",
    }
    # SWR-V3-070: 语言→测试路径形态映射 (5 种漏网形态, lessons A7)
    LANG_TEST_PATH_MAP = {
        "ruby": ["/spec/"],
        "powershell": ["tst/", "*.Tests.*"],
        "rust": ["*_tests.rs", "/benches/"],
        "javascript": ["*.spec.*", "*.test.*"],
        "csharp": [".Tests/"],
    }

    @classmethod
    def _is_ignored_path(cls, rel_path):
        import fnmatch
        norm = rel_path.replace("\\", "/")
        parts = norm.split("/")
        for part in parts:
            if part in cls._IGNORE_PATH_PARTS:
                return True
            if part.endswith("Test") or part.startswith("Test"):
                return True
        for patterns in cls.LANG_TEST_PATH_MAP.values():
            for pat in patterns:
                if any(ch in pat for ch in "*?["):
                    if fnmatch.fnmatch(norm, pat):
                        return True
                    if fnmatch.fnmatch(norm.split("/")[-1], pat):
                        return True
                else:
                    # 无通配符: 路径子串语义 (如 "/spec/" / "tst/")
                    if pat in norm:
                        return True
        return False

    @classmethod
    def _priority_for_cwe(cls, cwe_id):
        return cls._CWE_PRIORITY.get(cwe_id, 2)

    def _filter_and_prioritize(self, candidates):
        filtered = []
        discarded = 0
        for cand in candidates:
            fp = cand.get("file_path", "")
            if self._is_ignored_path(fp):
                discarded += 1
                continue
            cand["priority"] = self._priority_for_cwe(cand.get("cwe_id", ""))
            filtered.append(cand)
        return filtered, discarded

    def _dedupe_candidates(self, candidates):
        deduped = {}
        status_rank = {"PENDING": 0, "VERIFIED": 1}
        verdict_rank = {None: 0, "NEEDS_REVIEW": 1, "UNREACHABLE": 2, "REACHABLE": 3}
        for cand in candidates:
            key = (
                cand.get("file_path"),
                cand.get("line_number"),
                cand.get("cwe_id"),
                cand.get("category"),
                cand.get("type"),
            )
            existing = deduped.get(key)
            if not existing:
                deduped[key] = cand
                continue
            existing_score = (
                status_rank.get(existing.get("status"), 0),
                verdict_rank.get(existing.get("verdict"), 0),
            )
            new_score = (
                status_rank.get(cand.get("status"), 0),
                verdict_rank.get(cand.get("verdict"), 0),
            )
            if new_score < existing_score:
                deduped[key] = cand
        return list(deduped.values())

    def _find_rule_by_ast(self, lang_rules, ast_pattern):
        for rule in lang_rules:
            if ast_pattern in rule.get("sinks", {}).get("ast_patterns", []):
                return rule
        return {"cwe_id": "Unknown", "category": "General Sink"}

    def _find_rule_by_regex(self, lang_rules, regex_pattern):
        for rule in lang_rules:
            if regex_pattern in rule.get("sinks", {}).get("regex", []):
                return rule
        return {"cwe_id": "Unknown", "category": "General Sink"}

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(script_dir, "../resources/security_profiles.json")

    # REQ-03: R0 AST 物理工具强制 self-check 支持
    if len(sys.argv) > 1 and sys.argv[1] == "--self-check":
        profile_ok = os.path.exists(profile_path)
        profile_langs = []
        wrapper_langs = []
        rules_by_lang = {}
        total_rules_count = 0
        coverage_rule_count = 0
        manual_review_rule_count = 0
        empty_ast_count = 0
        langs_with_gaps = {}
        if profile_ok:
            try:
                with open(profile_path, 'r', encoding='utf-8') as pf:
                    pdata = json.load(pf)
                rules_by_lang = pdata.get("rules", {})
                profile_langs = list(rules_by_lang.keys())
                wrapper_langs = list(pdata.get("wrapper_detection", {}).keys())
                for lang_name, r_list in rules_by_lang.items():
                    total_rules_count += len(r_list)
                    for r in r_list:
                        is_manual_review_rule = bool(r.get("source_reason")) and not r.get("codeql_model")
                        if is_manual_review_rule:
                            manual_review_rule_count += 1
                            continue
                        coverage_rule_count += 1
                        sinks = r.get("sinks", {})
                        has_machine_check = (
                            bool(sinks.get("ast_patterns")) or
                            bool(sinks.get("go_models")) or
                            bool(sinks.get("swift_models"))
                        )
                        if not has_machine_check:
                            empty_ast_count += 1
                            langs_with_gaps[lang_name] = langs_with_gaps.get(lang_name, 0) + 1
            except Exception:
                profile_ok = False

        grammars_available = []
        if HAS_TREE_SITTER:
            if TS_QUERY_OLD_API:
                for lang in profile_langs:
                    try:
                        TS_GET_LANG(lang)
                        grammars_available.append(lang)
                    except Exception:
                        pass
            else:
                grammars_available = list(_TS_LANG_CACHE.keys())

        # REQ-03: AST 覆盖率门槛 (真实值; 覆盖率不足不阻断启动, 但如实告警)
        AST_COVERAGE_THRESHOLD = 95.0
        coverage_pct = round((1 - empty_ast_count / coverage_rule_count) * 100, 1) if coverage_rule_count else 0
        required_grammar_langs = sorted([
            lang for lang, rules in rules_by_lang.items()
            if rules and lang != "powershell"
        ])
        grammar_missing = [
            lang for lang in required_grammar_langs
            if lang not in grammars_available
        ]

        # REQ-03+: 冒烟匹配测试 — 用各语言典型 sink 片段实测 AST pattern / 结构化
        # 模型是否真实命中语法树, 替代"字符串存在性"的虚假覆盖率。语言级判定:
        # 该语言规则中至少 1 条真实命中 → 规则库可解析性成立; 0 命中 → 该语言
        # 规则库失效 (AST pattern 与真实语法树错配, 如 pre-v2 Swift simple_identifier)。
        smoke_summary = {}
        smoke_total_tested = 0
        smoke_total_hit = 0
        smoke_total_skipped = 0
        smoke_failed_langs = []
        if HAS_TREE_SITTER:
            for lang, lang_rules in rules_by_lang.items():
                if not lang_rules or lang == "powershell":
                    continue
                per_rule, parse_ok = _smoke_check_language(lang, lang_rules)
                if not per_rule and not parse_ok and lang not in SMOKE_SAMPLES:
                    continue
                n_skipped = sum(1 for v in per_rule.values() if v is None)
                n_rules = sum(1 for v in per_rule.values() if v is not None)
                n_hit = sum(1 for v in per_rule.values() if v is True)
                smoke_total_tested += n_rules
                smoke_total_hit += n_hit
                smoke_total_skipped += n_skipped
                smoke_summary[lang] = {
                    "rules_tested": n_rules,
                    "rules_hit": n_hit,
                    "rules_skipped_no_sink_in_sample": n_skipped,
                    "sample_parsed": parse_ok,
                    "ok": n_rules == 0 or n_hit > 0,
                    "failed_cwes": sorted({c for c, h in per_rule.items() if h is False}),
                }
                if n_rules and n_hit == 0:
                    smoke_failed_langs.append(lang)

        smoke_real_hit_rate = (
            round(smoke_total_hit / smoke_total_tested * 100, 1)
            if smoke_total_tested else None
        )
        # 可解析性判定: 每个有冒烟片段的语言, 其可测试规则中至少 1 条真实命中
        # (片段未覆盖的规则不计入, 由 failed_cwes 报告供人工核查)
        smoke_ok = all(s["ok"] for s in smoke_summary.values()) if smoke_summary else True

        ast_coverage_ok = coverage_pct >= AST_COVERAGE_THRESHOLD
        grammar_coverage_ok = HAS_TREE_SITTER and not grammar_missing
        # smoke_coverage_ok 反映"冒烟片段可解析且有规则命中", 作为**报告指标 + 告警**,
        # 不阻断 R0 启动: 规则库 pattern 缺陷由 smoke_warning 如实暴露, 供规则库维护。
        status_ok = profile_ok and HAS_TREE_SITTER and ast_coverage_ok and grammar_coverage_ok
        res = {
            "status": "ok" if status_ok else "FAIL: AST self-check failed",
            "has_tree_sitter": HAS_TREE_SITTER,
            "tree_sitter_api": "tree_sitter_languages" if TS_QUERY_OLD_API else "individual_packages_v0.26",
            "grammars_available": grammars_available,
            "required_grammar_languages": required_grammar_langs,
            "grammar_missing": grammar_missing,
            "grammar_coverage_ok": grammar_coverage_ok,
            "profile_loaded": profile_ok,
            "configured_languages": profile_langs,
            "wrapper_detection_languages": [l for l in wrapper_langs if not l.startswith("_")],
            "total_rules": total_rules_count,
            "coverage_rule_count": coverage_rule_count,
            "manual_review_regex_rules": manual_review_rule_count,
            "ast_patterns_coverage_pct": coverage_pct,
            "smoke_real_hit_rate_pct": smoke_real_hit_rate,
            "smoke_tested_rules": smoke_total_tested,
            "smoke_hit_rules": smoke_total_hit,
            "smoke_skipped_rules": smoke_total_skipped,
            "smoke_failed_languages": smoke_failed_langs,
            "smoke_by_language": smoke_summary,
            "ast_coverage_threshold_pct": AST_COVERAGE_THRESHOLD,
            "ast_coverage_ok": ast_coverage_ok,
            "smoke_coverage_ok": smoke_ok,
            "rules_missing_ast_patterns": empty_ast_count,
            "ast_gap_by_language": langs_with_gaps,
            "coverage_note": (
                "Coverage denominator excludes manual_additions-style rules with source_reason "
                "and no codeql_model; those are counted in manual_review_regex_rules. "
                "For CodeQL-sourced rules, coverage counts either tree-sitter ast_patterns "
                "or structured CodeQL models (go_models/swift_models) as machine-checkable support. "
                "smoke_real_hit_rate_pct 由各语言典型 sink 片段实测 AST pattern/结构化模型命中 "
                "计算(替代字符串存在性), smoke_coverage_ok 要求每个有冒烟片段语言至少 1 条规则真实命中。"
            )
        }
        if not res["ast_coverage_ok"]:
            res["warning"] = (
                f"AST S-expression 覆盖率 {coverage_pct}% 低于阈值 {AST_COVERAGE_THRESHOLD}%; "
                f"{empty_ast_count} 条规则仅有正则 (命中将降级为 NEEDS_REVIEW): {langs_with_gaps}"
            )
        if not smoke_ok and smoke_failed_langs:
            res["smoke_warning"] = (
                "冒烟匹配测试失败: 以下语言的规则库 AST pattern/结构化模型在典型 sink 片段上"
                f" 0 命中 (语法树错配, 需修 pattern): {smoke_failed_langs}. "
                "这些语言的规则在实际扫描中会退化为纯 regex / 无法命中。"
            )
        if grammar_missing:
            res["grammar_warning"] = (
                "缺少以下有规则语言的 tree-sitter grammar: "
                + ", ".join(grammar_missing)
            )
        # REQ-24: 锚点召回自检 — 对 anchor_registry.json 中每语言 CVE 锚点做命中测试
        anchor_results = {}
        anchor_recall_by_lang = {}
        anchor_failed_langs = []
        try:
            with open(os.path.join(script_dir, "../resources/anchor_registry.json"), encoding="utf-8") as af:
                anchor_data = json.load(af)
        except Exception:
            anchor_data = {}
        anchors_by_lang = anchor_data.get("anchors", {}) if isinstance(anchor_data, dict) else {}
        if HAS_TREE_SITTER:
            for lang, lang_rules in rules_by_lang.items():
                anchors = anchors_by_lang.get(lang, [])
                if not anchors:
                    continue
                per = _anchor_check_language(lang, lang_rules, anchors)
                if per is None:
                    # grammar 不可用 → 该语言锚点无法验证; 缺 grammar 已由 REQ-03
                    # grammar_missing 判定 fail-fast, 此处仅告警不重复计数
                    anchor_results[lang] = {"checked": 0, "hit": 0, "total": len(anchors), "skipped": True}
                    continue
                hit_n = sum(1 for v in per.values() if v is True)
                anchor_results[lang] = {
                    "checked": len(per), "hit": hit_n, "total": len(anchors),
                    "skipped": False,
                    "missed_cves": [anchors[i].get("cve") for i, v in per.items() if v is not True],
                }
                recall = (hit_n / len(anchors) * 100.0) if anchors else 100.0
                anchor_recall_by_lang[lang] = round(recall, 1)
                if recall < 100.0:
                    anchor_failed_langs.append(lang)
        anchor_global_total = sum(a.get("total", 0) for a in anchor_results.values() if not a.get("skipped"))
        anchor_global_hit = sum(a.get("hit", 0) for a in anchor_results.values() if not a.get("skipped"))
        anchor_recall_pct = round(anchor_global_hit / anchor_global_total * 100.0, 1) if anchor_global_total else None
        res["anchor_recall_pct"] = anchor_recall_pct
        res["anchor_recall_by_lang"] = anchor_recall_by_lang
        res["anchor_results"] = anchor_results
        if anchor_failed_langs:
            res["anchor_warning"] = (
                "锚点召回未达 100% (REQ-24): " + ", ".join(anchor_failed_langs)
                + " — 该语言规则库存在真实 CVE 攻击面盲区, 审计启动被阻止。"
            )
            status_ok = False
        print(json.dumps(res, indent=2, ensure_ascii=False))
        sys.exit(0 if status_ok else 1)

def _merge_queue(queue_path, new_candidates):
    """SWR-V3-073: merge 语义——既有队列候选保留 (origin 非 L0 的优先保留)，
    新扫描候选追加；同 key 去重时保留已 VERIFIED 者。"""
    if os.path.exists(queue_path):
        try:
            existing = json.load(open(queue_path, encoding="utf-8"))
            old = existing.get("candidates", []) if isinstance(existing, dict) else existing
        except Exception:
            old = []
    else:
        old = []
    old_keys = {(c.get("file_path"), c.get("line_number"), c.get("cwe_id"),
                 c.get("category")) for c in old}
    keep = list(old)
    for cand in new_candidates:
        key = (cand.get("file_path"), cand.get("line_number"), cand.get("cwe_id"),
               cand.get("category"))
        if key not in old_keys:
            keep.append(cand)
            old_keys.add(key)
    return keep, len(old)



    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    mode = "coarse"
    noise_check = False
    if "--mode" in sys.argv:
        i = sys.argv.index("--mode")
        mode = sys.argv[i + 1] if i + 1 < len(sys.argv) else "coarse"
        sys.argv = sys.argv[:i] + sys.argv[i + 2:]
    if "--noise-check" in sys.argv:
        noise_check = True
        sys.argv.remove("--noise-check")
    if mode == "deep":
        print(json.dumps({"status": "DEEP_MODE_NOT_IMPLEMENTED",
                          "note": "SWR-V3-071: tree-sitter 深度佐证模式占位; v3 默认路径为"
                                  "输入面测绘 (surface_mapper), 全库扫描仅作辅助"},
                         ensure_ascii=False))
        sys.exit(0)

    # REQ-12 目录守卫: 缺省输出到 <workspace>/.audit_results/ (batch_verify.py 硬编码
    # 从该路径读取)。绝不落盘到项目源码根目录。允许 argv[2] 覆盖, 但会规范到
    # .audit_results/ 子目录以保持契约一致。
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
        if os.path.basename(os.path.normpath(output_dir)) != ".audit_results":
            output_dir = os.path.join(output_dir, ".audit_results")
    else:
        output_dir = os.path.join(workspace, ".audit_results")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profile = os.path.join(script_dir, "../resources/security_profiles.json")
    
    scanner = ASTCoarseScanner(profile)
    results, scan_meta = scanner.scan(workspace)
    
    # SWR-V3-073: 入队 merge 语义——保留既有候选 (如 R0.5 入队的 R05-*)，只增改不覆写
    os.makedirs(output_dir, exist_ok=True)
    queue_path = os.path.join(output_dir, "verify_queue.json")
    merged_candidates, preserved = _merge_queue(queue_path, results)
    with open(queue_path, 'w', encoding='utf-8') as f:
        json.dump({"schema_version": "2.0", "candidates": merged_candidates}, f,
                  indent=2, ensure_ascii=False)
    
    print(f"SUCCESS: AST/Regex Scan complete. Found {len(results)} new Candidates, "
          f"preserved {preserved} existing. Written to {queue_path}")
    if noise_check:
        # SWR-V3-072: 按 sink_type 抽样误报率 (>80% 提示降权)
        from collections import Counter
        by_sink = Counter(c.get("cwe_id", "?") for c in results)
        noise = {"SCAN_META": scan_meta, "NOISE_CHECK": {
            "note": "抽样误报率需主 Agent 对每 sink_type 人工抽 10 条判定; "
                    ">80% 的规则应降权/禁用 (lessons 1.1)",
            "candidate_distribution": dict(by_sink.most_common(15)),
        }}
        print(json.dumps(noise, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"SCAN_META": scan_meta}, indent=2, ensure_ascii=False))
