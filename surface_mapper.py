#!/usr/bin/env python3
"""M1 surface_mapper — R1 输入面测绘编排。

满足: SWR-V3-001 (architecture_context), SWR-V3-002 (4 域任务书),
      SWR-V3-003/004 (surface 校验: entry_points 证据强制 + 枚举校验),
      SWR-V3-005 (多产出合并去重/冲突标注).
用法:
    python3 surface_mapper.py context <project_root>          # 产出 architecture_context.json
    python3 surface_mapper.py tasks   <project_root>          # 产出 4 域测绘任务书
    python3 surface_mapper.py validate <input_surface.json>   # 校验测绘产出
    python3 surface_mapper.py merge <f1.json> <f2.json> ...   # 合并测绘产出
"""
import html
import json
import os
import re
import sys

DOMAINS = ["network", "data", "process", "storage"]
# v3.2 (SWR-V3.2-011): 第五域 boundary——跨语言 FFI 边界是第一等攻击面 (P-B)
BOUNDARY_DOMAIN = "boundary"
BOUNDARY_KINDS = ("extern", "ctypes", "cffi", "n-api", "jni", "embed", "ffi-other",
               "proto", "http-service", "subprocess", "grpc", "cli")

VALID_TRUST = {"unauthenticated_remote", "authenticated_remote", "gated",
               "trusted_channel", "local", "environment", "unknown"}
VALID_CONFIDENCE = {"high", "medium", "low"}

BUILD_FILES = ["Package.swift", "Cargo.toml", "pom.xml", "build.gradle",
               "CMakeLists.txt", "package.json", "go.mod", "pyproject.toml",
               "requirements.txt", "Gemfile", "composer.json", "Makefile"]


def build_architecture_context(project_root):
    """SWR-V3-001: 从 README/依赖清单/构建文件提取项目背景。"""
    ctx = {
        "project_root": project_root,
        "lang": _detect_lang(project_root),
        "deps": [],
        "entry_hints": [],
        "maturity": "unknown",
        "build_files": [],
        "readme_summary": "",
    }
    for bf in BUILD_FILES:
        p = os.path.join(project_root, bf)
        if os.path.exists(p):
            ctx["build_files"].append(bf)
            ctx["deps"].extend(_extract_deps(bf, open(p, errors="ignore").read()))
    readme = _find_readme(project_root)
    if readme:
        text = open(readme, errors="ignore").read()
        ctx["readme_summary"] = text[:500].replace("\n", " ")[:200]
        low = text.lower()
        for kw, tag in [("vulnerability", "security-process"), ("security policy", "security-process"),
                        ("oss-fuzz", "fuzzed"), ("cve", "cve-history")]:
            if kw in low:
                ctx["maturity"] = "mature" if ctx["maturity"] != "mature" else ctx["maturity"]
                ctx["entry_hints"].append(tag)
    # v3.1 (W6 §23.6/§24.6): 项目形态判定——mature framework 的 R4 与 R3 并行
    # 且 H1/H7 深度上调 (R4 产率三连超 R3: actix 6:1 / sinatra 9:2)
    ctx["project_kind"] = _classify_project_kind(project_root, ctx)
    # v3.2 (SWR-V3.2-010): 语言清单——混合项目审计的基础 (候选级 lang 的来源)
    ctx["language_inventory"] = language_inventory(project_root)
    return ctx


def _classify_project_kind(root, ctx):
    """SWR-V3.1-020: 项目形态判定 framework/library/infra/app。
    依据: 构建文件类型 + 源码规模 + 是否存在框架标志文件。"""
    bfs = set(ctx.get("build_files", []))
    kind_hints = []
    for marker, kind in [
        ("Gemfile", "framework"), ("Cargo.toml", "framework"),
        ("Package.swift", "framework"), ("composer.json", "framework"),
        ("pom.xml", "framework"), ("build.gradle", "framework"),
        ("go.mod", "framework"), ("package.json", "framework"),
        ("Makefile", "infra"), ("CMakeLists.txt", "infra"),
    ]:
        if marker in bfs:
            kind_hints.append(kind)
    if "setup.py" in bfs or "pyproject.toml" in bfs:
        kind_hints.append("framework")
    if kind_hints and "framework" in kind_hints:
        return "framework"
    if kind_hints and "infra" in kind_hints and "framework" not in kind_hints:
        return "infra"
    return "app"


def _component_role(hint):
    """SWR-V3.2.1-060: component_hint → component_role。
    frontend→client-only (浏览器客户端, 无服务端可达面); scripts/headers→build-config;
    其余 (core/bindings)→server-side (绑定层通常运行在服务端进程内)。"""
    if hint == "frontend":
        return "client-only"
    if hint in ("scripts", "headers"):
        return "build-config"
    return "server-side"


def language_inventory(root):
    """SWR-V3.2-010: 全语言清单。{lang: {file_count, dirs, component_hint}}。
    component_hint 启发式: 绑定层目录名 (bindings/ffi/ctypes/csrc/native/ext)/
    头文件目录 (include)/脚本目录 (scripts)/前端目录 (www/web/ui/frontend)。
    component_role (v3.2.1): server-side/client-only/build-config。
    单语言项目清单长度 1 (向后兼容)。"""
    from signature_matcher import CODE_EXTENSIONS
    inv = {}
    BIND_DIRS = {"bindings", "ffi", "ctypes", "csrc", "native", "ext", "napi"}
    for dirpath, _dirs, files in os.walk(root):
        if any(part in dirpath for part in (".git", "node_modules", ".venv", "target", "build")):
            continue
        parts = set(p.lower() for p in dirpath.split(os.sep))
        hint = "core"
        if parts & BIND_DIRS:
            hint = "bindings"
        elif "include" in parts or "include" in {p.lower() for p in dirpath.split(os.sep)}:
            hint = "headers"
        elif "scripts" in parts:
            hint = "scripts"
        elif parts & {"www", "web", "ui", "frontend"}:
            hint = "frontend"
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue
            lang = ext
            # v3.2: 头文件归并到 C 语言组 (h/hpp/cc 是 C 组件的组成部分而非独立语言)
            if lang in (".h", ".hpp"):
                lang = ".c"
            rec = inv.setdefault(lang, {"file_count": 0, "dirs": set(), "component_hint": hint})
            rec["file_count"] += 1
            rec["dirs"].add(dirpath)
    out = [{"lang": k, "file_count": v["file_count"],
            "component_hint": v["component_hint"],
            "component_role": _component_role(v["component_hint"]),
            "sample_dirs": sorted(v["dirs"])[:3]} for k, v in sorted(inv.items(), key=lambda x: -x[1]["file_count"])]
    return out


def _detect_lang(root):
    # W5 回归发现: 纯扩展名计数把 .po/.md 翻译/文档文件误判为主语言 (lighttpd→.po);
    # 仅统计源码扩展名 (与 signature_matcher.CODE_EXTENSIONS 同源)
    from signature_matcher import CODE_EXTENSIONS
    counts = {}
    for dirpath, _dirs, files in os.walk(root):
        if any(part in dirpath for part in (".git", "node_modules", ".venv", "target", "build")):
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue
            counts[ext] = counts.get(ext, 0) + 1
    if not counts:
        return "unknown"
    return max(counts, key=counts.get)


def _extract_deps(build_file, content):
    deps = []
    if build_file == "Package.swift":
        for line in content.splitlines():
            if "package(url:" in line:
                deps.append(line.split("url:")[1].strip().split(",")[0].strip('"'))
    elif build_file == "Cargo.toml":
        in_deps = False
        for line in content.splitlines():
            if line.startswith("[dependencies"):
                in_deps = True
                continue
            if line.startswith("[") and not line.startswith("[dependencies"):
                in_deps = False
            if in_deps and "=" in line:
                deps.append(line.split("=")[0].strip())
    elif build_file == "pom.xml":
        import re
        deps = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
    elif build_file == "package.json":
        try:
            d = json.loads(content)
            deps = list(d.get("dependencies", {}).keys()) + list(d.get("devDependencies", {}).keys())
        except Exception:
            pass
    return deps[:30]


def _find_readme(root):
    for name in ("README.md", "README.rst", "README", "Readme.md"):
        p = os.path.join(root, name)
        if os.path.exists(p):
            return p
    return None


def gen_surface_tasks(project_root, ctx=None):
    """SWR-V3-002: 按 4 域生成测绘任务书（含架构背景字段）。"""
    ctx = ctx or build_architecture_context(project_root)
    tasks = []
    domain_guides = {
        "network": "HTTP/WS/RPC 端点、协议解码器、管理端口、套接字监听",
        "data": "文件上传/下载、配置加载、日志文件解析、模板加载、序列化入口",
        "process": "IPC、环境变量注入、命令行参数、信号处理、子进程",
        "storage": "数据库查询入口、缓存键来源、LDAP/外部存储",
        # v3.2: 语言间边界——混合项目最高危面 (所有权/ABI/释放责任)
        BOUNDARY_DOMAIN: ("跨语言 FFI 边界: extern \"C\"/ctypes/cffi/N-API/JNI/CPython 嵌入/JS addon——"
                          "枚举每个边界调用点 {调用方向, 语言对, 桥接文件:行, 边界类型, 数据流方向}"),
    }
    domains = DOMAINS + [BOUNDARY_DOMAIN]
    # v3.2 (SWR-V3.2-012): 架构背景按语言分片 (每语言组件摘要段)
    lang_ctx = ctx.get("language_inventory") or []
    lang_sections = "\n".join(
        f"- {li['lang']}: {li['file_count']} 文件, 组件角色={li['component_hint']}"
        for li in lang_ctx) or "- (单语言)"
    for domain in domains:
        tasks.append({
            "domain": domain,
            "guide": domain_guides[domain],
            "architecture_context": {
                "lang": ctx["lang"],
                "deps": ctx["deps"],
                "entry_hints": ctx["entry_hints"],
                "maturity": ctx["maturity"],
                "readme_summary": ctx["readme_summary"],
                "build_files": ctx["build_files"],
                "language_inventory": ctx.get("language_inventory", []),
                "lang_sections": lang_sections,
            },
            "output_schema": {
                "surface": ["id", "type", "name", "entry_points", "taint_channels",
                            "downstream_hints", "trust_boundary", "confidence",
                            "lang", "boundary_kind", "call_direction", "lang_pair"],
                "entry_point": ["file", "line", "function", "evidence"],
                "evidence": {"snippet": "该行代码片段(必须非空)"},
            },
            "evidence_requirement": (
                "每个 surface 的 entry_points 必须附 file:line + 代码片段证据;"
                "缺证据的 surface 将被校验拒收(REQ-V3-022)。"
            ),
        })
    return tasks


def normalize_surfaces(data, project_root=None):
    """W5 回归发现: 子智能体产出形态多样（裸数组 / {"surfaces":[]} 包裹;
    trust_boundary 为字符串或 {"type":...}; snippet 含 HTML 实体转义;
    entry_points.file 为项目相对路径）。
    归一化到 validate/merge 的统一契约, 不拒收可修复形态。"""
    surfaces = data.get("surfaces", []) if isinstance(data, dict) else data
    if not isinstance(surfaces, list):
        return None
    # v3.2 (SWR-V3.2-013): surface lang 透传; 缺省时由调用方在 merge 阶段按
    # 主语言继承 (normalize 不臆造——继承责任在 merge/main-agent)
    out = []
    for s in surfaces:
        if not isinstance(s, dict):
            continue
        s = dict(s)
        tb = s.get("trust_boundary")
        if isinstance(tb, str):
            # v3.2: agent 常写描述性自由文本——按关键词映射到枚举, 原文留档
            s["trust_boundary_raw"] = tb
            t = tb.lower()
            if any(k in t for k in ("未认证", "unauthenticated", "任意", "外部请求者")):
                mapped = "unauthenticated_remote"
            elif any(k in t for k in ("部署者", "cli", "配置", "env", "本地", "localhost", "127.0.0.1")):
                mapped = "local"
            elif any(k in t for k in ("tls", "会话", "令牌", "token", "认证")):
                mapped = "authenticated_remote"
            elif any(k in t for k in ("gated", "gate", "门控")):
                mapped = "gated"
            else:
                mapped = "environment"
            s["trust_boundary"] = {"type": mapped, "original": tb}
        elif isinstance(tb, dict) and tb.get("type") not in VALID_TRUST:
            # v3.2: 上一轮 normalize 已把自由文本包进 dict 的产物 (遗留形态)
            s.setdefault("trust_boundary_raw", tb.get("type"))
            t = str(tb.get("type", "")).lower()
            if any(k in t for k in ("未认证", "unauthenticated", "任意", "外部请求者")):
                mapped = "unauthenticated_remote"
            elif any(k in t for k in ("部署者", "cli", "配置", "env", "本地", "localhost", "127.0.0.1")):
                mapped = "local"
            elif any(k in t for k in ("tls", "会话", "令牌", "token", "认证")):
                mapped = "authenticated_remote"
            elif any(k in t for k in ("gated", "gate", "门控")):
                mapped = "gated"
            else:
                mapped = "environment"
            s["trust_boundary"] = {"type": mapped, "original": tb.get("type")}
        for ep in s.get("entry_points", []) or []:
            ev = ep.get("evidence")
            if isinstance(ev, dict) and ev.get("snippet"):
                raw = str(ev["snippet"])
                # W6 回归发现: 无条件 html.unescape 会把源码中的字面实体
                # (Perl 的 s/&/&amp;/g 这类转义代码) 误解码。保留原始文本,
                # 匹配时双态尝试 (原始 + unescape 变体)。
                ev["snippet"] = raw
                if html.unescape(raw) != raw:
                    ev["snippet_unescaped"] = html.unescape(raw)
            f = ep.get("file", "")
            if f and project_root and not os.path.isabs(f):
                ep["file"] = os.path.join(project_root, f)
        out.append(s)
    result = {"surfaces": out}
    # W6/Pester 发现: 透传非 surfaces 字段 (reviewed_by/empty_domain_reason 等
    # 空域签收信息), 否则 validate 空域签收检查永远失败。
    if isinstance(data, dict):
        for k, v in data.items():
            if k != "surfaces":
                result[k] = v
    return result


def validate_surfaces(data, project_root=None):
    """SWR-V3-003/004: schema 校验 + entry_points 证据强制 + 枚举校验。
    证据校验含源码行模糊匹配（行内容须含 snippet 前 40 字符）。
    输入先经 normalize_surfaces 归一化（裸数组/字符串 trust_boundary/HTML 实体/
    相对路径均可）。project_root 用于解析相对路径证据。"""
    errors = []
    data = normalize_surfaces(data, project_root)
    surfaces = data.get("surfaces", []) if data else []
    if not surfaces:
        # W6/Pester 发现: 空域是合法测绘结论 (本地测试工具无网络端点)。
        # 空数组必须带主代理签收 (reviewed_by + empty_domain_reason) 才放行,
        # 防止 agent 静默空产出。
        if isinstance(data, dict) and data.get("reviewed_by") and data.get("empty_domain_reason"):
            return True, []
        return False, ["'surfaces' 缺失或为空 (空域需主代理签收: reviewed_by + empty_domain_reason)"]
    seen = set()
    for s in surfaces:
        tag = s.get("id", "<no-id>")
        if tag in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(tag)
        for f in ("type", "name", "entry_points", "taint_channels",
                  "trust_boundary", "confidence"):
            if f not in s:
                errors.append(f"{tag}: missing '{f}'")
        if s.get("type") == "boundary":
            bk = s.get("boundary_kind")
            if bk not in BOUNDARY_KINDS:
                errors.append(f"{tag}: boundary surface 缺 boundary_kind (需 {BOUNDARY_KINDS})")
            if not s.get("lang_pair"):
                errors.append(f"{tag}: boundary surface 缺 lang_pair (语言对)")
        tb = s.get("trust_boundary", {})
        if not isinstance(tb, dict) or tb.get("type") not in VALID_TRUST:
            errors.append(f"{tag}: trust_boundary.type 非法 (需 {sorted(VALID_TRUST)})")
        if s.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"{tag}: confidence 非法")
        eps = s.get("entry_points", [])
        if not eps:
            errors.append(f"{tag}: entry_points 为空 (REQ-V3-022)")
        for ep in eps:
            if not all(k in ep for k in ("file", "line", "evidence")):
                errors.append(f"{tag}: entry_point 缺 file/line/evidence")
                continue
            ev = ep.get("evidence", {})
            if not isinstance(ev, dict) or not ev.get("snippet", "").strip():
                errors.append(f"{tag}: entry_point {ep.get('file')}:{ep.get('line')} 缺 snippet 证据")
                continue
            # 源码行模糊匹配: 折叠空白后, 源行必须是 snippet 的子串 (snippet 常混入
            # agent 注释, 故反向包含), 且行号在 ±2 窗口内。agent 行号 ±1~2 漂移常见
            # (grep 输出/代码块对齐); 源码对齐空白 (captures           =) 折叠后消除。
            # 窗口外命中不自动放行 (防幻觉), 但错误附 suggested_line 供主代理修正。
            snip_folded = re.sub(r"\s+", " ", ev["snippet"].strip())
            # v3.1 (W6 §18.7/§22.1): 多行 snippet 取首行作匹配键——agent 常把函数
            # 体整段当 snippet, 首行才是真实锚点; ±2 主窗口外命中全文件搜索 (±80
            # 语义: 全文件命中即候选), 修复器逐 entry 应用 suggested_line 并标记
            # paraphrased (首行全文件无命中 = 可能臆造, 主代理必须人工复核)
            first_line_key = snip_folded.split("|||")[0] if "|||" in snip_folded \
                else snip_folded.splitlines()[0].strip()[:50] if snip_folded else ""
            ev["_first_line_key"] = first_line_key
            # W6: 源码字面实体 (Perl s/&/&amp;/g) vs agent HTML 实体化 (&& → &amp;&amp;)
            # 无法可靠区分 → 双态变体, 任一命中即可
            snip_variants = {snip_folded}
            if ev.get("snippet_unescaped"):
                snip_variants.add(re.sub(r"\s+", " ", ev["snippet_unescaped"].strip()))
            ok_line = False
            suggested = None
            if os.path.exists(ep["file"]):
                try:
                    lines = open(ep["file"], errors="ignore").read().splitlines()
                    folded_lines = [re.sub(r"\s+", " ", ln).strip() for ln in lines]
                    lo = max(1, ep["line"] - 2)
                    hi = min(len(lines), ep["line"] + 2)
                    ok_line = any(folded_lines[i - 1] and any(
                                  folded_lines[i - 1] in sv or sv in folded_lines[i - 1]
                                  for sv in snip_variants)
                                  for i in range(lo, hi + 1))
                    if not ok_line:
                        # W6 回归发现: 超短行 ("(", "#", ")") 几乎总是任何 snippet 的
                        # 子串, 反向包含匹配产生假命中污染 suggested_lines
                        hits = [i for i, fl in enumerate(folded_lines, 1)
                                if fl and len(fl) >= 10 and any(
                                    fl in sv or sv in fl for sv in snip_variants)]
                        if not hits and first_line_key:
                            # v3.1 (W6 §18.7): 首行键全文件匹配 (±80 语义)
                            hits = [i for i, fl in enumerate(folded_lines, 1)
                                    if fl and len(fl) >= 10 and
                                    (first_line_key in fl or fl in first_line_key)]
                        if not hits:
                            # 第三层启发式: snippet 与源行部分重叠 (agent 混拼上下文) 时,
                            # 提取 snippet 中最长的 name(...) callee 名做唯一调用行匹配
                            callees = re.findall(r"\b([A-Za-z_][\w]*)\s*\(", snip_folded)
                            if callees:
                                callee = max(callees, key=len)
                                hits = [i for i, fl in enumerate(folded_lines, 1)
                                        if re.search(r"\b" + re.escape(callee) + r"\s*\(", fl)]
                        suggested = hits[0] if len(hits) == 1 else None
                        suggested_all = hits[:4] if len(hits) > 1 else []
                        if not hits:
                            # v3.1 (W6 §22.1): 无命中 = 可能 paraphrased/臆造,
                            # 标记而非静默 (主代理必须人工复核)
                            ep["paraphrased"] = True
                except OSError:
                    pass
            if not ok_line:
                msg = f"{tag}: {ep['file']}:{ep['line']} 证据与源码行不匹配"
                if suggested:
                    msg += f" [suggested_line={suggested}]"
                elif suggested_all:
                    msg += f" [suggested_lines={','.join(map(str, suggested_all))}]"
                errors.append(msg)
    return (len(errors) == 0), errors


def size_tier(project_root):
    """SWR-V3.1-010 (W6 §17.1/§18.6/§20.5/§24.7): 规模自适应档位。
    <100 文件 → small: 2 agents 无限时; 100-500 → medium: 4 agents 无限时;
    >500 → large: 4 agents + 45min 硬时限 + 每 10 分钟中间产物落盘。"""
    count = 0
    for dirpath, _dirs, files in os.walk(project_root):
        if any(part in dirpath for part in (".git", "node_modules", ".venv", "target", "build")):
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in {".c", ".h", ".py", ".rb", ".rs", ".go", ".java", ".kt",
                       ".scala", ".swift", ".php", ".js", ".ts", ".cs", ".ps1",
                       ".sh", ".pl", ".pm"}:
                count += 1
    inv = language_inventory(project_root)
    n_langs = len(inv)
    mixed_domains = DOMAINS + [BOUNDARY_DOMAIN]
    if n_langs > 2:
        # v3.2 (SWR-V3.2-014): 3+ 语言混合项目保底 large 档 (多组件审计成本)
        return {"tier": "large", "agent_count": 5, "time_limit_min": 45,
                "checkpoint_every_min": 10, "domains_split": mixed_domains,
                "rationale": f"v3.2: {n_langs} 语言混合项目 → 4+1 域保底 large 档"}
    if count < 100:
        # v3.2: 2 语言混合项目 domains 也含 boundary 域
        ds = mixed_domains if n_langs >= 2 else ["network+data", "process+storage"]
        return {"tier": "small", "agent_count": 2 if n_langs < 2 else 3,
                "time_limit_min": None, "checkpoint_every_min": None, "domains_split": ds,
                "rationale": "W6 §24.7 (sinatra 20 surfaces 2 agents)" + (f"; v3.2 {n_langs} 语言 → 含 boundary 域" if n_langs >= 2 else "")}
    if count <= 500:
        ds = mixed_domains if n_langs >= 2 else DOMAINS
        return {"tier": "medium", "agent_count": 4, "time_limit_min": None,
                "checkpoint_every_min": None, "domains_split": ds,
                "rationale": "W6 §20.5 (495 文件是 R1 agent 舒适区)"}
    ds = mixed_domains if n_langs >= 2 else DOMAINS
    return {"tier": "large", "agent_count": 4, "time_limit_min": 45,
            "checkpoint_every_min": 10, "domains_split": ds,
            "rationale": "W6 §17.1/§18.6 (WP 2.5h 失控 / Dubbo 2h+; 失控判据=超时+无落盘)"}


def repair_surfaces(data, project_root=None):
    """SWR-V3.1-011 (W6 §18.7/§9.4): 行号漂移自动修复器。
    逐 entry 按 ±2 主窗口 → 全文件首行键匹配 的顺序应用 suggested_line;
    无命中者标记 paraphrased。返回 (repaired_data, stats)。幂等: 已匹配
    entry 不重标 (W6 §9.5)。"""
    data = normalize_surfaces(data, project_root)
    stats = {"fixed": 0, "paraphrased": 0, "unchanged": 0}
    for s in data.get("surfaces", []):
        for ep in s.get("entry_points", []):
            ev = ep.get("evidence", {})
            snip = ev.get("snippet", "")
            if not snip or not ep.get("line"):
                continue
            # 已修复过的 entry 不再处理 (幂等契约, §9.5)
            if ep.get("suggested_line") or ep.get("paraphrased"):
                stats["unchanged"] += 1
                continue
            snip_folded = re.sub(r"\s+", " ", str(snip).strip())
            variants = {snip_folded}
            if ev.get("snippet_unescaped"):
                variants.add(re.sub(r"\s+", " ", ev["snippet_unescaped"].strip()))
            first_key = snip_folded.splitlines()[0].strip()[:50] if snip_folded else ""
            if not os.path.exists(ep["file"]):
                continue
            try:
                lines = open(ep["file"], errors="ignore").read().splitlines()
                folded = [re.sub(r"\s+", " ", ln).strip() for ln in lines]
                lo = max(1, ep["line"] - 2)
                hi = min(len(lines), ep["line"] + 2)
                ok = any(folded[i - 1] and any(folded[i - 1] in v or v in folded[i - 1]
                                               for v in variants)
                         for i in range(lo, hi + 1))
                if ok:
                    stats["unchanged"] += 1
                    continue
                hits = [i for i, fl in enumerate(folded, 1)
                        if fl and len(fl) >= 10 and
                        (first_key in fl or (first_key and fl in first_key))]
                if len(hits) == 1:
                    ep["suggested_line"] = ep["line"]
                    ep["line"] = hits[0]
                    stats["fixed"] += 1
                elif not hits:
                    ep["paraphrased"] = True
                    stats["paraphrased"] += 1
                else:
                    stats["unchanged"] += 1
            except OSError:
                pass
    return data, stats


def merge_surfaces(files, project_root=None):
    """SWR-V3-005: 多测绘产出合并。同 entry_point 多域归属合并; 其余冲突标注。
    project_root 统一解析相对路径 (否则相对/绝对混用导致多域归属检测失效)。"""
    merged = {"schema_version": "3.0", "surfaces": [], "conflicts": []}
    keymap = {}
    for f in files:
        data = normalize_surfaces(json.load(open(f)), project_root) or {"surfaces": []}
        for s in data.get("surfaces", []):
            for ep in s.get("entry_points", []):
                key = (ep["file"], ep["line"])
                if key in keymap:
                    existing = keymap[key]
                    if existing["surface"]["id"] != s["id"]:
                        # 同入口多域归属: 保留首个, 冲突标注 (不丢信息)
                        existing["multi_domain"] = True
                        merged["conflicts"].append({
                            "entry": key,
                            "surfaces": [existing["surface"]["id"], s["id"]],
                            "resolution": "kept-first-multi-domain",
                        })
                        continue
                keymap[key] = {"surface": s}
            merged["surfaces"].append(s)
    # 去重: 同 surface id 重复合并
    seen_ids = set()
    dedup = []
    for s in merged["surfaces"]:
        if s.get("id") in seen_ids:
            continue
        seen_ids.add(s.get("id"))
        dedup.append(s)
    merged["surfaces"] = dedup
    return merged


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "context":
        print(json.dumps(build_architecture_context(argv[2]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "tasks":
        tasks = gen_surface_tasks(argv[2])
        for t in tasks:
            print(json.dumps(t, ensure_ascii=False, indent=2))
        return 0
    if cmd == "validate":
        data = json.load(open(argv[2]))
        root = argv[argv.index("--root") + 1] if "--root" in argv else None
        ok, errors = validate_surfaces(data, root)
        print("OK" if ok else "FAIL")
        for e in errors:
            print("  -", e)
        return 0 if ok else 1
    if cmd == "repair":
        data = json.load(open(argv[2]))
        root = argv[argv.index("--root") + 1] if "--root" in argv else None
        repaired, stats = repair_surfaces(data, root)
        out = argv[argv.index("--out") + 1] if "--out" in argv else argv[2]
        json.dump(repaired, open(out, "w"), ensure_ascii=False, indent=1)
        print(json.dumps(stats, ensure_ascii=False))
        return 0
    if cmd == "tier":
        print(json.dumps(size_tier(argv[2]), ensure_ascii=False, indent=1))
        return 0
    if cmd == "merge":
        root = argv[argv.index("--root") + 1] if "--root" in argv else None
        files = [a for a in argv[2:] if a != "--root" and a != root]
        out = merge_surfaces(files, root)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
