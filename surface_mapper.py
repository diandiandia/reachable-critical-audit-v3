#!/usr/bin/env python3
"""M1 surface_mapper — R1 输入面测绘编排。

满足: SWR-V3-001 (architecture_context), SWR-V3-002 (4 域任务书),
      SWR-V3-003/004 (surface 校验: entry_points 证据强制 + 枚举校验),
      SWR-V3-005 (多产出合并去重/冲突标注).

形态判定两轴 (v3.5.2, 与 SKILL.md 数据模型速查注对齐):
    project_kind ∈ {framework, library, infra, app}  = R1 测绘期上下文提示信号
        (context 产出, 仅作背景上下文, 不设门禁)
    target_kind ∈ {application, library, hybrid}     = R0 门禁签收判据
        (tools/target_kind.py, 门禁⑧ target_kind_required)
    两轴语义独立, 不得混用——测绘期上下文提示不替代验证期门禁判据。
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
import subprocess
import sys

import generation_registry as gr

DOMAINS = ["network", "data", "process", "storage"]
# v3.2 (SWR-V3.2-011): 第五域 boundary——跨语言 FFI 边界是第一等攻击面 (P-B)
BOUNDARY_DOMAIN = "boundary"
BOUNDARY_KINDS = ("extern", "ctypes", "cffi", "cgo", "n-api", "jni", "panama",
               "embed", "ffi-other", "proto", "http-service", "subprocess", "grpc", "cli",
               "capi")  # SWR-V3.4.3-031: C-API 扩展模块胶水 (Python C-API/Lua C-API/N-API);
               # v3.5.2 (P3): +cgo (Go→C 边界, 混合项目常见形态);
               # v3.8 (SWR-V3.8-032): +panama (java.lang.foreign FFM 边界——
               # elasticsearch libs/native 全为 Panama, 与 JNI 风险形态不同:
               # MemorySegment 越界/生命周期而非 JNIEnv 语义)

VALID_TRUST = {"unauthenticated_remote", "authenticated_remote", "gated",
               "trusted_channel", "local", "environment", "unknown",
               "host_api"}  # v3.3 (REQ-V3.3-008): 宿主 API 边界 (库组件默认)

# 遍历排除段 (精确分段匹配——子串匹配会把 test_xxx/target_xxx 目录整体跳过,
# v3.5 测试基线修复实证)
SKIP_DIRS = {".git", "node_modules", ".venv", "target", "build",
             "__pycache__", "dist", "vendor"}
VALID_CONFIDENCE = {"high", "medium", "low"}

BUILD_FILES = ["Package.swift", "Cargo.toml", "pom.xml", "build.gradle",
               "CMakeLists.txt", "package.json", "go.mod", "pyproject.toml",
               "requirements.txt", "Gemfile", "composer.json", "Makefile",
               # v3.8 (SWR-V3.8-023): Top15 构建清单缺口补齐 (BIAS_EVAL F4)
               # —— C# (.csproj/.sln) / Scala (build.sbt) / Kotlin (.kts 变体)
               # / TypeScript (tsconfig.json)。沿用既有根目录精确名 + 小写
               # 变体匹配语义, 无新机制。
               ".csproj", ".sln", "build.sbt", "build.gradle.kts", "tsconfig.json"]


def norm_surface_id(sid):
    """SWR-V3.3.2-040: surface id 归一化纯函数（SURF- 前缀剥离 + 去空格）。
    七项目批次实证: R4 agent 产出 SURF-S-001 而 input_surface 为 S-001——
    对账/校验统一经此函数, 不持久化 aliases（可推导数据不落盘）。
    非字符串输入原样返回。"""
    if not isinstance(sid, str):
        return sid
    s = sid.strip()
    if s.startswith("SURF-"):
        s = s[5:]
    return s


# SWR-V3.4.3-030: 域前缀缩写 → 标准前缀 (cpp-httplib 批次实证 SURF-DAT-* 与
# SURF-DATA-* 混用致下游 tracked_surfaces 对照频繁误配)
_DOMAIN_ABBREV = {"DAT": "DATA", "PRC": "PROC", "STR": "STOR", "NET": "NET",
                  "PRO": "PROC"}


def canonical_surface_id(sid):
    """SWR-V3.4.3-030: surface id 域前缀归一化。返回 (new_id, changed)。
    只归一 SURF-<域>-NNN 形态的域段 (3 字母缩写 → 全称), 其余原样返回。"""
    if not isinstance(sid, str):
        return sid, False
    m = re.match(r"^SURF-([A-Z]{3,4})-(\d+)$", sid.strip())
    if not m:
        return sid, False
    dom = _DOMAIN_ABBREV.get(m.group(1), m.group(1))
    new = f"SURF-{dom}-{m.group(2)}"
    return new, new != sid


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
        if not os.path.exists(p):
            # v3.3 (REQ-V3.3-005, SWR-V3.3-032): 小写变体 (makefile 等历史仓库常见,
            # Lua 审计实测 build_files=[] 根因)
            low = bf.lower()
            if low != bf and os.path.exists(os.path.join(project_root, low)):
                p = os.path.join(project_root, low)
            else:
                continue
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
                ctx["entry_hints"].append(tag)
    # v3.1 (W6 §23.6/§24.6): 项目形态判定——mature framework 的 R4 与 R3 并行
    # 且 H1/H7 深度上调 (R4 产率三连超 R3: actix 6:1 / sinatra 9:2)
    # v3.3 (REQ-V3.3-005/006): 四值判定 + 信号证据; maturity 独立信号
    # (git 版本标签主信号; README 安全流程关键词为辅助信号)
    ctx["project_kind"], ctx["kind_signals"] = _classify_project_kind(project_root, ctx)
    ctx["maturity_info"] = _detect_maturity(project_root)
    if ctx["maturity_info"]["level"] == "unknown" and \
            "security-process" in ctx["entry_hints"]:
        ctx["maturity_info"] = {"level": "developing",
                                "signals": ["readme:security-process"]}
    ctx["maturity"] = ctx["maturity_info"]["level"]
    # v3.2 (SWR-V3.2-010): 语言清单——混合项目审计的基础 (候选级 lang 的来源)
    ctx["language_inventory"] = language_inventory(project_root)
    return ctx


def _classify_project_kind(root, ctx):
    """v3.3 (REQ-V3.3-005): 项目形态四值判定 {framework, library, infra, app}。
    信号加权: 构建文件降为弱信号 (权重 1); 可执行入口 (main/监听器, 权重 3) 与
    公共 API 主导 (权重 2) 为强信号。返回 (kind, signals)。
    旧版 (v3.1) 仅按构建文件硬映射且无 library 返回路径——纯库项目含
    Cargo.toml 即被误判 framework (偏见审查 §3 裁决)。"""
    bfs = {b.lower() for b in ctx.get("build_files", [])}
    signals = []
    score = {"framework": 0, "library": 0, "infra": 0, "app": 0}
    # 信号 1: 构建文件 (弱信号, 不再硬映射)
    for m in ("gemfile", "cargo.toml", "package.swift", "composer.json",
              "pom.xml", "build.gradle", "go.mod", "package.json",
              "setup.py", "pyproject.toml"):
        if m in bfs:
            score["framework"] += 1
            signals.append(f"build_fw:{m}")
    for m in ("makefile", "cmakelists.txt"):
        if m in bfs:
            score["infra"] += 1
            signals.append(f"build_infra:{m}")
    # 信号 2: 可执行入口 (main/监听器, 强信号)
    # v3.3.2: listener 仅伴随 main 时满 3 分 (独立入口证据), 单独出现
    # 只计 1 分 (库实现网络能力 ≠ 独立应用, libuv/uwebsockets 实测)
    srcs = _sample_source_files(root)
    has_main, has_listener = _detect_exec_entry(srcs)
    if has_main:
        score["app"] += 3
        signals.append("exec:main")
        if has_listener:
            score["app"] += 3
            signals.append("exec:listener")
    elif has_listener:
        score["app"] += 1
        signals.append("exec:listener(hint)")
    # 信号 3: 公共 API 主导 (头文件率/include 目录/导出符号, 强信号)
    api_ratio = _public_api_ratio(srcs)
    if api_ratio is not None:
        signals.append(f"api_ratio:{api_ratio:.2f}")
        if api_ratio >= 0.35:  # v3.3.2: 0.5→0.35 (cjson 0.40 双文件库形态)
            score["library"] += 2
    if _has_include_dir(root):
        score["library"] += 2
        signals.append("include_dir")
    # v3.5 (偏见 B3): 无 main → library 泛化——Go/Java 独享特判是语言偏见
    # (库型项目普遍无 main, 不仅 Go/Java)。泛化集排除 shell/c/cpp 保持保守:
    # shell 脚本常无 main 且多为应用形态; C/C++ 无 main 时库与固件形态混杂。
    LANG_NO_MAIN_LIBRARY = {"go", "java", "kotlin", "scala", "csharp", "swift",
                            "php", "ruby", "perl", "powershell", "typescript"}
    _EXT_OF = {"go": ".go", "java": ".java", "kotlin": ".kt", "scala": ".scala",
               "csharp": ".cs", "swift": ".swift", "php": ".php", "ruby": ".rb",
               "perl": ".pl", "powershell": ".ps1", "typescript": ".ts"}
    for lang in LANG_NO_MAIN_LIBRARY:
        if _dominant_lang(srcs, _EXT_OF[lang]) and not has_main:
            score["library"] += 2
            signals.append(f"{lang}_no_main")
    # 判定 (保守倾向: 无法确定归属时按 app)
    if score["app"] >= 3:
        return "app", signals
    if score["library"] >= 2:
        return "library", signals
    if score["framework"] >= 2:
        return "framework", signals
    if score["infra"] >= 1:
        return "infra", signals
    return "app", signals


def _has_include_dir(root):
    """v3.3.2: include/ 目录含头文件 = 公共 API 约定 (libuv include/uv/*.h 实测)。"""
    inc = os.path.join(root, "include")
    if not os.path.isdir(inc):
        return False
    for dirpath, _dirs, files in os.walk(inc):
        if any(fn.endswith((".h", ".hpp")) for fn in files):
            return True
    return False


def _dominant_lang(srcs, ext):
    """v3.3.2: 该扩展名文件是否为主导 (≥60% 且 ≥5 个)。"""
    if len(srcs) < 5:
        return False
    n = sum(1 for p in srcs if p.endswith(ext))
    return n / len(srcs) >= 0.6


_SRC_EXTS = {".c", ".h", ".cpp", ".hpp", ".cc", ".rs", ".go", ".java",
             ".py", ".rb", ".js", ".ts", ".cs", ".swift", ".kt", ".scala",
             ".php", ".pl", ".pm", ".ps1", ".sh"}


def _sample_source_files(root, cap=120):
    """v3.3: 采样源码文件清单 (排除测试/构建/审计产物目录, 上限 cap)。
    misc/example/bench/fuzz/doc 类目录含开发工具与生成物, 其 main/bind 信号
    会污染分类器 (yyjson 实测: misc/make_tables.c 与 doxygen 产物 resize.js)。
    v3.3.2: 前缀族匹配覆盖进行时/复数变体 (cjson 实测: 'fuzzing' 目录不在
    精确名 'fuzz/fuzzer' 列表中致 exec:main 误报)。"""
    out = []
    # v3.17 (SWR-V3.17-001): 生成层注册表合并视图——通用 DSL 与生成物
    # (.proto/.pb.cc 类) 计入源码采样; 项目局部 DSL 经 profile 局部署名。
    exts = gr.merged_view(root)
    exact_skip = {".git", ".audit_results", "vendor", "node_modules",
                  "third_party", "build", "target"}
    prefix_skip = ("test", "fuzz", "bench", "example", "sample", "misc",
                   "doc", "doxygen", "demo")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in exact_skip
                       and not d.startswith(".")
                       and not d.lower().startswith(prefix_skip)]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in exts:
                out.append(os.path.join(dirpath, fn))
                if len(out) >= cap:
                    return out
    return out


def _detect_exec_entry(srcs):
    """v3.3: 可执行入口探测 (main 函数 / 网络监听)。采样读文件, 廉价。
    v3.3.2 精化: ①main 模式行首锚定 (排除字符串模板误报——hikaricp
    JavassistProxyFactory 的 'public static void main' 字节码模板实测)
    ②监听单独存在只计提示分 (库自身实现网络能力 ≠ 独立入口——libuv
    src/unix/tcp.c、uwebsockets src/App.h 实测)。"""
    # v3.5: re.MULTILINE 移入 compile——原 search(head, re.MULTILINE) 把
    # flags 当 pos 传入 (跳过前 8 字节), 行首锚定在短文件上失效 (fun main/@main
    # 位于文件头部时漏检, B3 扩展模式实证暴露)。
    main_pat = re.compile(
        r"^[ \t]*(?:int\s+main\s*\(|fn\s+main\s*\(|func\s+main\s*\(|"
        r"(?:public\s+)?static\s+void\s+(?:Main|main)\s*\(|def\s+main\s*\(|"
        r"fun\s+main\s*\(|@main)", re.MULTILINE)
    listen_pat = re.compile(
        r"\blisten\s*\(|\bServerSocket\s*\(|\bTcpListener\s*::|\bnet\.Listen\s*\(|"
        r"\bbind\s*\(\s*[\"']|socket\.bind\s*\(|createServer\s*\(|"
        r"http\.Server\s*\(|HttpListener|TCPServer|stream_socket_server|"
        r"IO::Socket::INET")
    has_main = has_listener = False
    for p in srcs:
        try:
            with open(p, errors="ignore") as f:
                # head+tail 采样: CLI 入口常位于文件尾部 (Lua lua.c main@777 实测)
                head = f.read(32768)
                if len(head) == 32768:
                    f.seek(0, 2)
                    size = f.tell()
                    if size > 32768:
                        f.seek(max(32768, size - 4096))
                        head += f.read(4096)
        except OSError:
            continue
        if not has_main and main_pat.search(head):
            has_main = True
        if not has_listener and listen_pat.search(head):
            has_listener = True
        if has_main and has_listener:
            return True, True
    return has_main, has_listener


def _public_api_ratio(srcs):
    """v3.3: 公共 API 主导信号——头文件率 (C/C++ 系) 或导出符号率 (Rust)。
    v3.3 精修: 单头/双文件小库形态 (1h+1c) 与 header-only 形态纳入
    (旧 >=8 阈值漏掉经典小库, yyjson 实测)。"""
    hdr = sum(1 for p in srcs if p.endswith((".h", ".hpp")))
    src = sum(1 for p in srcs if p.endswith((".c", ".cpp", ".cc")))
    if hdr > 0 and src == 0 and hdr >= 3:
        return 1.0  # header-only 库
    if hdr + src >= 2 and src > 0 and hdr >= 1:
        return hdr / (hdr + src)
    pub = 0
    rust_files = 0
    for p in srcs:
        if not p.endswith(".rs"):
            continue
        rust_files += 1
        try:
            if "pub " in open(p, errors="ignore").read(8192):
                pub += 1
        except OSError:
            pass
    if rust_files >= 5:
        return pub / rust_files
    return None


def _detect_maturity(root):
    """v3.3 (REQ-V3.3-006): maturity 独立信号 (与 project_kind 解耦)。
    稳定版本标签语义: v>=1.0 → mature; 0.x → developing; 无标签 → unknown。"""
    try:
        out = subprocess.run(
            ["git", "-C", root, "describe", "--tags", "--always"],
            capture_output=True, text=True, timeout=5)
        tag = out.stdout.strip()
        # v3.8 (SWR-V3.8-002): 兼容 release-X.Y.Z 标签形态——zookeeper 全仓
        # release-3.9.5 无 v 前缀, 旧正则判 unknown 致 maturity 覆盖下调,
        # R4 与 R3 并行不触发。仅加前缀族, 不引入新判定轴。
        m = re.match(r"(?:v|release-)?(\d+)\.(\d+)", tag)
        if m:
            level = "mature" if int(m.group(1)) >= 1 else "developing"
            return {"level": level, "signals": [f"git_tag:{tag}"]}
    except Exception:
        pass
    return {"level": "unknown", "signals": []}


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
    v3.2.2 (REQ-V3.2.2-023): 运行时占比修正——语言文件 >90% 位于
    scripts/tests/tools/docs/configs 目录时 role=build-config (mbedtls 实证:
    .sh 构建脚本曾被标 server-side 触发 "4 语言混合" 过配)。
    单语言项目清单长度 1 (向后兼容)。
    v3.17 (SWR-V3.17-001): 扩展名视图 = 生成层注册表合并视图; DSL/生成物
    经 lang_family_for 归入对应语言组 (含 provenance 语义)。"""
    exts = gr.merged_view(root)
    inv = {}
    BIND_DIRS = {"bindings", "ffi", "ctypes", "csrc", "native", "ext", "napi"}
    NON_RUNTIME_SEGS = {"scripts", "script", "tests", "test", "tools", "tool",
                        "docs", "doc", "configs", "config"}
    for dirpath, _dirs, files in os.walk(root):
        if any(p.lower() in SKIP_DIRS for p in dirpath.split(os.sep)):
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
        is_runtime_dir = not (parts & NON_RUNTIME_SEGS)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in exts:
                continue
            # v3.2: 头文件归并到 C 语言组 (h/hpp/cc 是 C 组件的组成部分而非独立语言)
            # v3.17: DSL/生成物经 lang_family_for 归入对应语言组
            lang = gr.lang_family_for(ext, root)
            rec = inv.setdefault(lang, {"file_count": 0, "runtime_files": 0,
                                        "dirs": set(), "component_hint": hint})
            rec["file_count"] += 1
            if is_runtime_dir:
                rec["runtime_files"] += 1
            rec["dirs"].add(dirpath)
    out = []
    for k, v in sorted(inv.items(), key=lambda x: -x[1]["file_count"]):
        role = _component_role(v["component_hint"])
        if v["component_hint"] in ("core", "scripts") and v["file_count"] > 0 \
                and v["runtime_files"] / v["file_count"] < 0.1:
            role = "build-config"
        out.append({"lang": k, "file_count": v["file_count"],
                    "component_hint": v["component_hint"],
                    "component_role": role,
                    "sample_dirs": sorted(v["dirs"])[:3]})
    return out


def _detect_lang(root):
    # W5 回归发现: 纯扩展名计数把 .po/.md 翻译/文档文件误判为主语言 (lighttpd→.po);
    # 仅统计源码扩展名 (与 signature_matcher.CODE_EXTENSIONS 同源)
    from signature_matcher import CODE_EXTENSIONS
    counts = {}
    for dirpath, _dirs, files in os.walk(root):
        if any(p.lower() in SKIP_DIRS for p in dirpath.split(os.sep)):
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
        BOUNDARY_DOMAIN: ("跨语言 FFI 边界: extern \"C\"/ctypes/cffi/cgo/N-API/JNI/"
                          "Panama FFM/CPython 嵌入/JS addon/C-API 胶水——"
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
    # v3.3.1: lang 形态归一化 ('.c'/'ts'/'kt' → c/typescript/kotlin),
    # 与 signature_matcher.norm_lang 同规则 (L2 过滤依赖)
    out = []
    for s in surfaces:
        if not isinstance(s, dict):
            continue
        s = dict(s)
        if s.get("lang"):
            from signature_matcher import norm_lang
            s["lang"] = norm_lang(s["lang"])
        tb = s.get("trust_boundary")
        if isinstance(tb, str):
            # v3.2: agent 常写描述性自由文本——按关键词映射到枚举, 原文留档
            s["trust_boundary_raw"] = tb
            t = tb.lower()
            if any(k in t for k in ("未认证", "unauthenticated", "任意", "外部请求者")):
                mapped = "unauthenticated_remote"
            elif any(k in t for k in ("宿主", "host api", "host_api", "公共 api", "库调用方", "调用方传入")):
                mapped = "host_api"  # v3.3 (REQ-V3.3-008)
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
            elif any(k in t for k in ("宿主", "host api", "host_api", "公共 api", "库调用方", "调用方传入")):
                mapped = "host_api"  # v3.3 (REQ-V3.3-008)
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


_COMMENT_PREFIXES = ("//", "#", "/*", "*", "<!--")
_BLANK_TOKENS = {"", "{", "}", "(", ")", ";"}


def _is_comment_or_blank(folded_line):
    """v3.8 (SWR-V3.8-008): 折叠行文本的注释/空行判定 (语言无关最小集)。
    只服务于 R1 surface 证据校验的锚点退化拦截; 与 r2_guard.anchor_check
    (R2 假设锚点) 分层, 各自管各自阶段的数据。"""
    return folded_line in _BLANK_TOKENS or folded_line.startswith(_COMMENT_PREFIXES)


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
            suggested_all = []  # v3.3: 文件不存在路径的初始化 (存量 UnboundLocalError 根修)
            if os.path.exists(ep["file"]):
                try:
                    lines = open(ep["file"], errors="ignore").read().splitlines()
                    folded_lines = [re.sub(r"\s+", " ", ln).strip() for ln in lines]
                    lo = max(1, ep["line"] - 2)
                    hi = min(len(lines), ep["line"] + 2)
                    matched_lines = [i for i in range(lo, hi + 1)
                                     if folded_lines[i - 1] and any(
                                         folded_lines[i - 1] in sv
                                         or sv in folded_lines[i - 1]
                                         for sv in snip_variants)]
                    ok_line = bool(matched_lines)
                    # v3.8 (SWR-V3.8-008): 声称行是注释/空行而命中全部来自窗口邻行
                    # → 锚点退化 (zookeeper 实录: C 文件实体转义条目锚点整体偏移 1,
                    # 指向注释行仍过 validate, 直到 r2_guard.anchor_check 才暴露)。
                    # 转 mismatch + suggested_line 修正, 复用现有修正流, 不放行。
                    ln = int(ep["line"])
                    if ok_line and 0 < ln <= len(lines) \
                            and ln not in matched_lines \
                            and _is_comment_or_blank(folded_lines[ln - 1]):
                        ok_line = False
                        ep["anchor_claimed_comment"] = True
                        # suggested/suggested_all 由下方全文件命中修正流计算
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
                        # v3.8 (SWR-V3.8-033): 多命中按 |line-claimed| 升序——
                        # 修正流建议取离声称行最近的命中 (同分取首候选曾把
                        # 修正引向文件头部无关行, quarkus 17 处裁决实录)。
                        if hits:
                            near_first = sorted(hits, key=lambda i: abs(i - int(ep["line"])))
                            suggested = near_first[0]
                            suggested_all = near_first[1:5]
                        else:
                            suggested = None
                            suggested_all = []
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
                if suggested_all:
                    msg += f" [suggested_lines={','.join(map(str, suggested_all))}]"
                errors.append(msg)
    return (len(errors) == 0), errors


def _component_inventory(project_root, exts, cap=30):
    """SWR-V3.17-002: super-large 档组件清单——深度 1 目录按文件数降序
    (排除 SKIP_DIRS), 附构建清单信号 hits。两阶段测绘的 A 阶段机械输入。"""
    depth1 = {}
    for d in os.listdir(project_root):
        p = os.path.join(project_root, d)
        if not os.path.isdir(p) or d.lower() in SKIP_DIRS:
            continue
        n = 0
        for dirpath, _dirs, files in os.walk(p):
            _dirs[:] = [x for x in _dirs if x.lower() not in SKIP_DIRS]
            for f in files:
                if os.path.splitext(f)[1].lower() in exts:
                    n += 1
        if n:
            depth1[d] = n
    return [{"dir": d, "file_count": n}
            for d, n in sorted(depth1.items(), key=lambda x: -x[1])[:cap]]


def size_tier(project_root):
    """SWR-V3.1-010 (W6 §17.1/§18.6/§20.5/§24.7): 规模自适应档位。
    <100 文件 → small: 2 agents 无限时; 100-500 → medium: 4 agents 无限时;
    >500 → large: 4 agents + 45min 硬时限 + 每 10 分钟中间产物落盘。
    v3.17 (SWR-V3.17-002): >2000 → super-large: 两阶段测绘
    (组件清单 → 组件×域派发), 45min 硬时限按组件给。"""
    # v3.8 (SWR-V3.8-020): 与 signature_matcher.CODE_EXTENSIONS 单事实源——
    # 旧内联集合缺 .cpp/.cc/.hpp/.m/.mm/.sql, C++ (top-2) 源码不计入档位
    # (BIAS_EVAL F1)。同 language_inventory 写法。
    # v3.17 (SWR-V3.17-001): 单事实源前移到生成层注册表合并视图。
    exts = gr.merged_view(project_root)
    count = 0
    for dirpath, _dirs, files in os.walk(project_root):
        if any(p.lower() in SKIP_DIRS for p in dirpath.split(os.sep)):
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in exts:
                count += 1
    inv = language_inventory(project_root)
    # v3.2.2 (REQ-V3.2.2-023): 语言混合度只计运行时语言 (server-side 组件角色)——
    # .sh/.py/.pl 构建脚本曾把 mbedtls 计为 "4 语言混合" 触发 large 档 (无害过配,
    # 但混合度语义应排除构建期语言)
    runtime_langs = [x for x in inv if x.get("component_role") == "server-side"]
    n_langs = len(runtime_langs)
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
                "rationale": "W6 §24.7 (成熟框架 20 surfaces 2 agents 档位校准)" + (f"; v3.2 {n_langs} 语言 → 含 boundary 域" if n_langs >= 2 else "")}
    if count <= 500:
        ds = mixed_domains if n_langs >= 2 else DOMAINS
        return {"tier": "medium", "agent_count": 4, "time_limit_min": None,
                "checkpoint_every_min": None, "domains_split": ds,
                "rationale": "W6 §20.5 (495 文件是 R1 agent 舒适区)"}
    ds = mixed_domains if n_langs >= 2 else DOMAINS
    if count > 2000:
        # v3.17 (SWR-V3.17-002): super-large——两阶段测绘 (A 组件清单 →
        # B 组件×域派发), 时限按组件给 (V8 评估 D-2: 3325 文件单目录实测)。
        comps = _component_inventory(project_root, exts)
        return {"tier": "super-large", "agent_count": 4,
                "time_limit_min": 45, "checkpoint_every_min": 10,
                "domains_split": ds, "two_phase": True, "components": comps,
                "rationale": (f"SWR-V3.17-002: {count} 文件 >2000 阈值——"
                              f"两阶段测绘 ({len(comps)} 组件), 45min 按组件给")}
    return {"tier": "large", "agent_count": 4, "time_limit_min": 45,
            "checkpoint_every_min": 10, "domains_split": ds,
            "two_phase": False, "components": [],
            "rationale": "W6 §17.1/§18.6 (审计失控实录 2.5h+; 失控判据=超时+无落盘)"}


def merge_surfaces(files, project_root=None):
    """SWR-V3-005: 多测绘产出合并。同 entry_point 多域归属合并; 其余冲突标注。
    project_root 统一解析相对路径 (否则相对/绝对混用导致多域归属检测失效)。
    v3.2.2 (REQ-V3.2.2-020): 产出 mirror_pairs——kept-first 冲突对,
    门禁⑦ tracked 计算自动传播镜像面覆盖 (mbedtls 审计 15 冲突对手写 bridge 制度化)。"""
    merged = {"surfaces": [], "conflicts": [],
              "mirror_pairs": []}
    # v3.11 (SWR-V3.11-013): 逻辑镜像提示——跨语言语义相似面组 (仅提示不组族,
    # 主代理裁决; 语言清单 ≥2 才检测)
    _lang_count = set()
    # SWR-V3.4.3-030: 域前缀归一化映射 (只记变更项, 供下游追溯)
    normalized_ids = {}
    keymap = {}
    for f in files:
        data = normalize_surfaces(json.load(open(f)), project_root) or {"surfaces": []}
        for s in data.get("surfaces", []):
            new_id, changed = canonical_surface_id(s.get("id", ""))
            if changed:
                normalized_ids[s["id"]] = new_id
                s["id"] = new_id
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
                        merged["mirror_pairs"].append(
                            [existing["surface"]["id"], s["id"]])
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
    # mirror_pairs 去重 (无序对)
    seen_pairs = set()
    mps = []
    for a, b in merged["mirror_pairs"]:
        k = tuple(sorted((a, b)))
        if k in seen_pairs:
            continue
        seen_pairs.add(k)
        mps.append([a, b])
    merged["mirror_pairs"] = mps
    # SWR-V3.4.5-003: 域内 id 序列空洞告警 (非阻断)——缺号可能是 agent
    # 整段漏报的信号, 主代理复核决定是否重派 (gRPC 审计: boundary 缺 003)
    _warn_id_gaps(merged["surfaces"])
    # SWR-V3.4.6-003: 同文件跨域未成对提示 (非阻断)——"同文件双面但 entry_points
    # 不重叠"形态 (quic-go: token_store.go 被 data/storage 两域测绘不同函数) 不产生
    # conflict → mirror 检测漏对 → 覆盖传播缺口且无人工核对提示。只提示不自动成对
    # (自动配对会引入误耦合——同文件不同入口可能是完全独立的两个面), 主代理裁决
    # 补 mirror_pairs 或主代理手动核对 (v3.5: coverage_bridge 字段已删)
    merged["same_file_cross_domain_pairs"] = _hint_same_file_cross_domain(
        merged["surfaces"])
    # v3.11 (SWR-V3.11-013): 逻辑镜像提示——同逻辑面 × 多语言实现的完整性信号。
    # 判定: 语义关键词重叠 (name/taint_channels) 且 lang 不同的面组。
    # 仅提示 (语义相似度判定不可靠, 不自动组族), 主代理 merge 复核时裁决。
    _langs = {str(s.get("lang") or "") for s in merged["surfaces"]}
    if len(_langs) >= 2:
        # 语义域词集 (防同名异义误配: 图像解码 codec vs 消息编解码 codec)。
        # 偏见评估注记 (P13): 首版双域从多媒体系批次提炼——对其他形态项目
        # (数据面/协议栈/存储面) 静默失效 (零输出, 无负作用)。词集为开放形态:
        # 新项目审计后按需扩展域词, 勿视为封闭全集。
        _image_domain = {"image", "图像", "帧", "frame", "instantiate", "bitmap",
                         "pixel", "像素", "图片", "动画"}
        _message_domain = {"message", "消息", "channel", "通道", "插件", "plugin",
                           "binary", "二进制", "payload", "载荷"}
        _sem = {}
        for s in merged["surfaces"]:
            blob = " ".join([str(s.get("name") or ""),
                             " ".join(str(x) for x in (s.get("taint_channels") or []))]).lower()
            kws = {w for w in ("codec", "decoder", "code", "encode", "decode",
                               "消息", "通道", "channel", "message", "协议",
                               "protocol", "parse", "解析", "编解码")
                   if w in blob}
            domains = (({"image"} if (kws & _image_domain) or any(
                        d in blob for d in _image_domain) else set())
                       | ({"message"} if (kws & _message_domain) or any(
                          d in blob for d in _message_domain) else set()))
            if len(kws) >= 2 and domains:
                _sem[s.get("id")] = (kws, domains)
        _cands = []
        _ids = list(_sem.keys())
        for i in range(len(_ids)):
            for j in range(i + 1, len(_ids)):
                a, b = _ids[i], _ids[j]
                _sa = next((s for s in merged["surfaces"] if s.get("id") == a), None)
                _sb = next((s for s in merged["surfaces"] if s.get("id") == b), None)
                if (_sa and _sb and _sa.get("lang") and _sb.get("lang")
                        and _sa["lang"] != _sb["lang"]
                        and len(_sem[a][0] & _sem[b][0]) >= 2
                        and (_sem[a][1] & _sem[b][1])):  # 同一语义域
                    _cands.append([a, b])
        if _cands:
            # 按域均衡截断 (前 10 组被单域占满会截掉其他域的镜像族——域内
            # 最多 8 组, 总上限 16)
            _dom_cands = {}
            for a, b in _cands:
                _d = sorted(_sem[a][1] & _sem[b][1])[0]
                if len(_dom_cands.get(_d, [])) < 8:
                    _dom_cands.setdefault(_d, []).append([a, b])
            _flat = [p for pairs in _dom_cands.values() for p in pairs][:16]
            merged["mirror_candidates"] = _flat
            merged["mirror_candidates_note"] = (
                "跨语言语义相似面组 (同逻辑面的多语言实现候选, 仅提示不组族; "
                "按语义域均衡截断)——主代理 merge 复核时裁决是否作为逻辑镜像族"
                "登记; R2 假设生成须覆盖族内全部语言实现 (SWR-V3.11-013/014)")
    if normalized_ids:
        merged["normalized_ids"] = normalized_ids
    return merged


def _warn_id_gaps(surfaces):
    """SWR-V3.4.5-003: 按归一化域前缀 (SURF-<DOMAIN>-NNN) 检测编号序列空洞,
    输出 warn 到 stderr (不阻断合并, 不改变返回值)。"""
    per_domain = {}
    for s in surfaces:
        # 域前缀不限长度 (NETWORK/BOUNDARY 等长域; canonical 归一化管短域错写)
        m = re.match(r"^SURF-([A-Z]+)-(\d+)$", s.get("id", ""))
        if m:
            per_domain.setdefault(m.group(1), []).append(int(m.group(2)))
    for domain, nums in sorted(per_domain.items()):
        uniq = sorted(set(nums))
        if not uniq:
            continue
        missing = sorted(set(range(uniq[0], uniq[-1] + 1)) - set(uniq))
        if missing:
            shown = ",".join(f"{n:03d}" for n in missing[:3])
            if len(missing) > 3:
                shown += f"...(+{len(missing) - 3})"
            print(f"[merge] warn: surface id 序列空洞 SURF-{domain}-{shown} "
                  f"missing ({len(uniq)} 条在册)", file=sys.stderr)


def _hint_same_file_cross_domain(surfaces):
    """SWR-V3.4.6-003: 同文件跨域未成对提示。
    同文件、不同域前缀、entry_points 无重叠 (file+line 键) 的 surface 对清单。
    返回 [{pair:[idA,idB], file, entries:{idA:[file:line,...], idB:[...]}}];
    stderr 输出提示 (非阻断)。自动成对会引入误耦合——只提示, 主代理裁决。"""
    by_file = {}
    for s in surfaces:
        for ep in s.get("entry_points", []):
            f = ep.get("file")
            if not f:
                continue
            by_file.setdefault(f, []).append(s)
    out = []
    for f, ss in by_file.items():
        uniq = {s["id"]: s for s in ss if s.get("id")}
        ids = list(uniq)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = uniq[ids[i]], uniq[ids[j]]
                ma = re.match(r"^SURF-([A-Z]+)-", a["id"])
                mb = re.match(r"^SURF-([A-Z]+)-", b["id"])
                if not ma or not mb or ma.group(1) == mb.group(1):
                    continue
                ea = {(e.get("file"), e.get("line")) for e in a.get("entry_points", [])}
                eb = {(e.get("file"), e.get("line")) for e in b.get("entry_points", [])}
                if ea & eb:
                    continue  # entry_points 重叠 → 已走 conflict/mirror 检测
                out.append({
                    "pair": [a["id"], b["id"]],
                    "file": f,
                    "entries": {
                        a["id"]: [f"{e.get('file')}:{e.get('line')}"
                                  for e in a.get("entry_points", [])],
                        b["id"]: [f"{e.get('file')}:{e.get('line')}"
                                  for e in b.get("entry_points", [])],
                    },
                })
                print(f"[merge] hint: {a['id']} <-> {b['id']} 同文件 {f} 跨域"
                      f"({ma.group(1)}/{mb.group(1)}) 且 entry_points 不重叠——"
                      f"可能是同一实现的双面, 主代理裁决补 mirror 或 bridge",
                      file=sys.stderr)
    return out


def scope_snapshot(project_root):
    """v3.2.2 (REQ-V3.2.2-018): R0 scope 快照——子模块状态 + 关键目录存在性。
    动机: mbedtls 审计中 R4 智能体自行 submodule update 物化 tf-psa-crypto,
    R1 的"子模块空目录"scope 判定与 R2 drop 理由当场作废; 快照供各阶段 diff。"""
    import subprocess
    snap = {"submodules": {}, "key_dirs": {}}
    try:
        out = subprocess.run(["git", "-C", project_root, "submodule", "status"],
                             capture_output=True, text=True, timeout=15).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                # 形态: "<sha> <path> (<describe>)" 或 "-<sha> <path>" (未物化)
                snap["submodules"][parts[1]] = parts[0]
    except (OSError, subprocess.SubprocessError) as e:
        snap["git_error"] = f"submodule status failed: {e}"
    gm = os.path.join(project_root, ".gitmodules")
    if os.path.exists(gm):
        for line in open(gm, errors="ignore"):
            line = line.strip()
            if line.startswith("path ="):
                p = line.split("=", 1)[1].strip()
                snap["key_dirs"][p] = bool(os.listdir(
                    os.path.join(project_root, p))) if os.path.isdir(
                    os.path.join(project_root, p)) else False
    # v3.11 (SWR-V3.11-009): 构建差异声明——构建清单声明的依赖/生成物 vs 树内
    # 物化状态 (审计树与部署物差异面; 空差异也落盘, 供给面完整性注记)
    snap["build_divergence"] = _build_divergence(project_root)
    return snap


_BUILD_MANIFESTS = (
    # 过设计评估裁剪 (P13): 目录提取仅对「树内目录声明」形态的清单有效
    # (DEPS/.gclient 的 'src/xxx': url 形态); 其余生态清单 (pom/gradle/cargo/
    # go.mod/npm/pyproject) 的依赖解析形态各异, 统一提取是伪能力——降为
    # 存在性注记 (仅声明「有构建清单但未做目录级提取」)
    ("DEPS", "deps", True), (".gclient", "gclient", True),
    ("build.gradle", "gradle", False), ("pom.xml", "maven", False),
    ("Cargo.toml", "cargo", False), ("go.mod", "gomod", False),
    ("package.json", "npm", False), ("pyproject.toml", "pyproject", False),
)


def _build_divergence(project_root):
    '''SWR-V3.11-009: 构建差异声明——构建清单存在但对应物化目录缺失/为空的
    差异表 (依赖未物化/生成物缺失)。提示级声明, 不改变任何裁决。'''
    div = []
    for fname, kind, extract_dirs in _BUILD_MANIFESTS:
        fp = os.path.join(project_root, fname)
        if not os.path.isfile(fp):
            continue
        if not extract_dirs:
            div.append({"manifest": fname, "kind": kind,
                        "declared_dirs_sample": [],
                        "missing_or_empty": [],
                        "note": "存在性注记: 该生态清单的依赖解析形态各异, "
                                "未做目录级提取 (过设计裁剪)——审计树差异由主代理"
                                "按生态惯例声明"})
            continue
        declared_dirs = set()
        try:
            for line in open(fp, errors="ignore"):
                line = line.strip()
                if ("src/" in line or "third_party" in line
                        or line.startswith(("'", '"'))):
                    for tok in line.replace("'", '"').split('"'):
                        if "/" in tok and not tok.startswith(("http", "file:")):
                            declared_dirs.add(tok.split("/")[0])
        except OSError:
            pass
        missing = [d for d in sorted(declared_dirs)
                   if not os.path.isdir(os.path.join(project_root, d))]
        div.append({"manifest": fname, "kind": kind,
                    "declared_dirs_sample": sorted(declared_dirs)[:8],
                    "missing_or_empty": missing[:12],
                    "note": "审计树与部署物差异声明 (SWR-V3.11-009): "
                            "未物化/空目录为树外不可验证面的依据之一"})
    return div


def scope_diff(project_root, snapshot):
    """v3.2.2 (REQ-V3.2.2-018): 现状 vs 快照差异。
    返回 {changed: bool, changes: [描述], affected_dirs: [路径]}。
    SWR-V3.15-007 契约注: changes 为人读描述字符串 (如 "submodule x: a -> b"),
    机器消费请用 affected_dirs——消费者解析人读形态是 nghttp2 AttributeError
    实录根因, 本函数保持字符串形态不变。"""
    cur = scope_snapshot(project_root)
    changes = []
    affected = []
    for name, sha in snapshot.get("submodules", {}).items():
        cur_sha = cur.get("submodules", {}).get(name)
        if cur_sha != sha:
            changes.append(f"submodule {name}: {sha} -> {cur_sha}")
            affected.append(name)
    for d, was in snapshot.get("key_dirs", {}).items():
        now = cur.get("key_dirs", {}).get(d)
        if now != was:
            changes.append(f"dir {d}: materialized={was} -> {now}")
            affected.append(d)
    return {"changed": bool(changes), "changes": changes,
            "affected_dirs": affected}


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
    if cmd == "tier":
        print(json.dumps(size_tier(argv[2]), ensure_ascii=False, indent=1))
        return 0
    if cmd == "merge":
        root = argv[argv.index("--root") + 1] if "--root" in argv else None
        files = [a for a in argv[2:] if a != "--root" and a != root]
        out = merge_surfaces(files, root)
        # v3.2.2 (REQ-V3.2.2-011): 默认落盘 input_surface.json
        # (P-E REQ-V3.2.2-020: mirror_pairs 由 merge_surfaces 产出, 一并落盘)
        out_path = (argv[argv.index("--out") + 1] if "--out" in argv
                    else os.path.join(root, ".audit_results", "input_surface.json")
                    if root else "input_surface.json")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print(f"# written: {out_path}", file=sys.stderr)
        return 0
    if cmd == "scope":
        sub = argv[2] if len(argv) > 2 else "snapshot"
        root = argv[3] if len(argv) > 3 else "."
        if sub == "snapshot":
            snap = scope_snapshot(root)
            out_path = os.path.join(root, ".audit_results", "scope_snapshot.json")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            json.dump(snap, open(out_path, "w"), ensure_ascii=False, indent=2)
            print(json.dumps(snap, ensure_ascii=False, indent=2))
            print(f"# written: {out_path}", file=sys.stderr)
            return 0
        if sub == "diff":
            sp = os.path.join(root, ".audit_results", "scope_snapshot.json")
            if not os.path.exists(sp):
                print(json.dumps({"changed": False, "changes": [],
                                  "note": "no scope_snapshot.json (R0 未快照)"},
                                 ensure_ascii=False))
                return 0
            snap = json.load(open(sp))
            print(json.dumps(scope_diff(root, snap), ensure_ascii=False, indent=2))
            return 0
        print("usage: scope <snapshot|diff> <project>", file=sys.stderr)
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
