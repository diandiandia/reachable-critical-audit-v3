#!/usr/bin/env python3
"""target_kind 判定器 (v3.2.1, SWR-V3.2.1-001~003)。

R0 阶段判定审计目标类型 {application, library, hybrid}:
- 信号源: 包清单/监听器/服务启动链/Dockerfile/README/发布物
- 输出: 推荐值 + 逐信号证据 + 置信度; --write 落盘 .audit_results/target_kind.json

设计动机 (SYSTEM_DESIGN_V3_2_1 §2.1): fixture 同批库型裁决矛盾 + Lersosa 三处
部署前提错误均源于 verifier 未按目标类型装载存在性规则——库型"公共 API 即信任边界",
应用型"默认部署即攻击面", 混用必然系统性误判 (W6 §25.1)。

用法:
    python3 target_kind.py <project_root> [--write]
"""
import json
import os
import re
import sys

LIB_KEYWORDS = ("library", "sdk", "framework", "toolkit", "包", "库", "组件库")
APP_KEYWORDS = ("server", "service", "deploy", "docker", "k8s", "kubernetes",
                "服务", "部署", "网关", "监听")

LISTEN_PATTERN = re.compile(
    r"0\.0\.0\.0|Listen\(|Server::builder|uvicorn\.run|app\.listen|net\.Listen|"
    r"http\.ListenAndServe|grpc\.NewServer|axum::serve|hyper::Server",
    re.IGNORECASE)

SCAN_SWALLOW_PATTERN = re.compile(
    r"except\s+(Exception|BaseException|\w+Error).{0,80}(log|warn|pass|continue)",
    re.DOTALL)


def _scan_files(root, exts, max_files=400):
    hits = []
    for dirpath, _dirs, files in os.walk(root):
        if any(part in dirpath for part in (".git", "node_modules", ".venv",
                                            "target", "build", "__pycache__")):
            continue
        for f in files:
            if os.path.splitext(f)[1].lower() in exts:
                hits.append(os.path.join(dirpath, f))
                if len(hits) >= max_files:
                    return hits
    return hits


def _grep(root, pattern, exts, max_hits=12):
    """返回 (命中文件, 行号, 行内容) 列表。"""
    out = []
    for path in _scan_files(root, exts):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if pattern.search(line):
                        out.append((path, i, line.strip()[:120]))
                        if len(out) >= max_hits:
                            return out
        except OSError:
            continue
    return out


def determine_target_kind(project_root):
    """SWR-V3.2.1-001: 六类信号 → {recommendation, signals, component_kinds, confidence}。"""
    root = project_root.rstrip("/")
    signals = []

    if not _scan_files(root, {".py", ".go", ".rs", ".c", ".js", ".ts",
                              ".java", ".rb", ".php", ".scala", ".cpp"}, 3):
        return {"recommendation": "application", "signals": signals,
                "component_kinds": {}, "confidence": "low",
                "note": "无源码文件, 默认 application (保守)"}

    def add(name, direction, evidence, weight=1.0):
        signals.append({"signal": name, "direction": direction,
                        "evidence": str(evidence)[:200], "weight": weight})

    # 1. 包清单
    for bf in ("setup.py", "pyproject.toml", "Cargo.toml", "package.json",
               "go.mod", "pom.xml", "composer.json", "Gemfile", "*.gemspec"):
        paths = _scan_files(root, {os.path.splitext(bf)[1].replace("*", "")},
                            8) if bf.startswith("*") else []
        if bf.startswith("*"):
            pass
        else:
            p = os.path.join(root, bf)
            if os.path.exists(p):
                paths = [p]
        for p in paths[:3]:
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()[:4000]
            except OSError:
                continue
            rel = os.path.relpath(p, root)
            if bf == "Cargo.toml":
                if "[[bin]]" not in txt and "[lib]" in txt:
                    add("package-manifest", "lib", f"{rel}: 无 [[bin]] 有 [lib]")
                elif "[[bin]]" in txt:
                    add("package-manifest", "app", f"{rel}: 含 [[bin]]", 0.8)
            elif bf == "package.json":
                try:
                    m = json.loads(txt)
                except Exception:
                    m = {}
                if m.get("main") and not m.get("scripts", {}).get("start"):
                    add("package-manifest", "lib", f"{rel}: main 无 start 脚本")
                elif m.get("scripts", {}).get("start"):
                    add("package-manifest", "app", f"{rel}: start 脚本", 0.8)
            elif bf == "setup.py":
                if "console_scripts" in txt or "entry_points" in txt:
                    add("package-manifest", "app", f"{rel}: entry_points", 0.6)
                elif "name=" in txt:
                    add("package-manifest", "lib", f"{rel}: 无 entry_points", 0.5)
            elif bf == "pyproject.toml":
                if "[project.scripts]" in txt or "console_scripts" in txt:
                    add("package-manifest", "app", f"{rel}: project.scripts", 0.6)
                elif "[project]" in txt:
                    add("package-manifest", "lib", f"{rel}: 无 scripts", 0.5)
            elif bf == "go.mod":
                if "package main" in txt:
                    add("package-manifest", "app", f"{rel}: package main", 0.6)
                elif txt.strip().startswith("module"):
                    add("package-manifest", "lib", f"{rel}: module 声明", 0.5)

    # 2. 监听器 (决定性强信号)
    # v3.2.2 (REQ-V3.2.2-022): 路径分域——测试/脚本/文档/库目录/示例目录命中不得计
    # app 方向 (mbedtls 实证: library/net_sockets.c 辅助函数与 programs/ 示例服务器
    # 曾致机械推荐 application; 通用规则: 仅示例目录有监听 = 示例非产品本体)
    _NON_PRODUCT_SEGS = ("tests", "test", "scripts", "script", "tools", "tool",
                         "docs", "doc")
    _LIB_SEGS = ("library", "lib")
    _EXAMPLE_SEGS = ("examples", "example", "demos", "demo", "samples",
                     "sample", "programs")

    def _classify_hit(path):
        parts = os.path.relpath(path, root).replace(os.sep, "/").split("/")
        if any(p in _NON_PRODUCT_SEGS for p in parts):
            return "nonproduct"
        if any(p in _LIB_SEGS for p in parts):
            return "libdir"
        if any(p in _EXAMPLE_SEGS for p in parts):
            return "examples"
        return "product"

    listens = _grep(root, LISTEN_PATTERN,
                    {".go", ".rs", ".py", ".js", ".ts", ".java", ".scala",
                     ".rb", ".php", ".c", ".cpp"})
    product_hits = [h for h in listens if _classify_hit(h[0]) == "product"]
    libdir_hits = [h for h in listens if _classify_hit(h[0]) == "libdir"]
    example_hits = [h for h in listens if _classify_hit(h[0]) == "examples"]
    if product_hits:
        add("listener", "app", f"{len(product_hits)} 处监听/服务构建命中(产品路径), 例: "
            f"{os.path.relpath(product_hits[0][0], root)}:{product_hits[0][1]}", 2.0)
    elif example_hits:
        add("listener", "lib", f"监听命中仅位于示例/程序目录 (示例非产品本体), 例: "
            f"{os.path.relpath(example_hits[0][0], root)}:{example_hits[0][1]}", 0.8)
    elif libdir_hits:
        add("listener", "lib", f"监听模式命中仅位于库目录 (socket 抽象辅助函数), 例: "
            f"{os.path.relpath(libdir_hits[0][0], root)}:{libdir_hits[0][1]}", 0.8)
    else:
        add("listener", "lib", "无监听器/服务构建模式命中", 1.0)

    # 3. 服务启动链 (main+wire/bootstrap/kratos)
    starters = _grep(root,
                     re.compile(r"wire\.Build|kratos\.New|BeanContainerManager|"
                                r"ActixSystem::new|#[tokio::main]|app\.run\(\)",
                                re.IGNORECASE),
                     {".go", ".rs", ".py", ".java"}, 6)
    # v3.2.2: 排除测试/脚本/文档目录的启动链 (scripts/analyze_outcomes.py 与
    # docs/conf.py 类非产品 main 曾致误判)
    starters = [s for s in starters if _classify_hit(s[0]) != "nonproduct"]
    if starters:
        add("startup-chain", "app", f"启动链命中: {starters[0][0].split(os.sep)[-1]}:{starters[0][1]}", 1.2)

    # 4. Dockerfile
    for df in ("Dockerfile", "Dockerfile.dev"):
        p = os.path.join(root, df)
        if os.path.exists(p):
            txt = open(p, encoding="utf-8", errors="ignore").read()
            if "EXPOSE" in txt or "ENTRYPOINT" in txt:
                add("dockerfile", "app", f"{df}: EXPOSE/ENTRYPOINT 服务端形态", 1.0)
            break

    # 5. README
    readme = None
    for cand in ("README.md", "README.rst", "README"):
        if os.path.exists(os.path.join(root, cand)):
            readme = cand
            break
    if readme:
        txt = open(os.path.join(root, readme), encoding="utf-8", errors="ignore").read()[:6000].lower()
        lib_hits = sum(1 for k in LIB_KEYWORDS if k.lower() in txt)
        app_hits = sum(1 for k in APP_KEYWORDS if k.lower() in txt)
        if lib_hits > app_hits:
            add("readme", "lib", f"{readme}: 库类关键词 {lib_hits} > 服务类 {app_hits}", 0.6)
        elif app_hits > lib_hits:
            add("readme", "app", f"{readme}: 服务类关键词 {app_hits} > 库类 {lib_hits}", 0.6)

    # 6. 发布物
    docs_api = docs_deploy = 0
    for dp, _d, fs in os.walk(os.path.join(root, "docs")) if os.path.isdir(os.path.join(root, "docs")) else []:
        for f in fs:
            low = f.lower()
            if "api" in low:
                docs_api += 1
            if "deploy" in low or "ops" in low:
                docs_deploy += 1
    if docs_api or docs_deploy:
        if docs_api > docs_deploy:
            add("artifacts", "lib", f"docs: api {docs_api} > deploy {docs_deploy}", 0.5)
        else:
            add("artifacts", "app", f"docs: deploy {docs_deploy} >= api {docs_api}", 0.5)

    # 汇总
    app_score = sum(s["weight"] for s in signals if s["direction"] == "app")
    lib_score = sum(s["weight"] for s in signals if s["direction"] == "lib")
    total = app_score + lib_score
    if total == 0:
        return {"recommendation": "application", "signals": signals,
                "component_kinds": {}, "confidence": "low",
                "note": "无任何信号, 默认 application (保守)"}
    ratio = app_score / total
    if ratio >= 0.6:
        kind, confidence = "application", "high" if ratio >= 0.75 else "medium"
    elif ratio <= 0.4:
        kind, confidence = "library", "high" if ratio <= 0.25 else "medium"
    else:
        kind, confidence = "hybrid", "medium"
    return {"recommendation": kind, "signals": signals,
            "component_kinds": {}, "confidence": confidence,
            "score_ratio": round(ratio, 2), "app_score": round(app_score, 1),
            "lib_score": round(lib_score, 1)}


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    result = determine_target_kind(root)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if "--write" in argv:
        outdir = os.path.join(root, ".audit_results")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "target_kind.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
