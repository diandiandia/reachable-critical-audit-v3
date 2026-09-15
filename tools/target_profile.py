#!/usr/bin/env python3
"""target_profile 判定器 (v3.17, SWR-V3.17-008)。

R0 阶段判定审计目标的"形态画像"——运行时/引擎形态与超大型目标的五根
硬编码轴的数据化载体:
- surface_model: entry | semantic | hybrid   (输入面形态, 默认 entry)
- generation_layers: 项目局部 DSL 扩展名     (默认空, 两段式局部署名)
- scale_class: small/medium/large/super-large(默认按文件数机械推导)
- containment_default: 防护边界缺省值        (默认 none)
- empirical_modes: 实证模式建议              (默认空)

信号全部机制形态 (零项目名零框架名)。输出推荐值 + 逐信号证据;
--write 落盘 .audit_results/target_profile.json (signed_by 留 null,
主代理复核签收后写入——未签收时各消费者按全默认装载 = 现状行为)。

用法:
    python3 tools/target_profile.py <project_root> [--write]
"""
import glob
import json
import os
import re
import shutil
import sys

SKIP_DIRS = {".git", "node_modules", ".venv", "target", "build",
             "__pycache__", "dist", "vendor", ".audit_results"}

BUILD_MANIFESTS = ("BUILD.gn", "BUILD.bazel", "MODULE.bazel", "CMakeLists.txt",
                   "meson.build")

# 语义面信号词 (机制形态, 词边界匹配; 引擎/运行时类 README 高频词)
SEMANTIC_KEYWORDS = ("interpreter", "virtual machine", "runtime", "bytecode",
                     "compiler", "jit", "language", "engine", "解释器",
                     "虚拟机", "字节码", "运行时", "编译器")

SANDBOX_KEYWORDS = ("sandbox", "沙箱", "沙盒")

MANAGED_DIR_SIGNALS = ("gc", "gc-common", "memory")  # 目录名机制形态


def _scan_files(root):
    """文件普查 (生成层合并视图 + profile 局部层), 返回 {ext: count}。"""
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent not in sys.path:
        sys.path.insert(0, parent)
        sys.path.insert(0, os.path.join(parent, "src"))
    import generation_registry as gr
    exts = gr.merged_view(root)
    counts = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in exts:
                counts[ext] = counts.get(ext, 0) + 1
    return counts


def _find_files(root, pat):
    """按路径片段匹配文件/目录 (JIT 信号等目录结构探测)。"""
    hits = []
    for dirpath, dirs, files in os.walk(root):
        if pat in dirpath:
            hits.append(dirpath)
        for f in files:
            if pat in f:
                hits.append(os.path.join(dirpath, f))
    return hits


def _scan_build_manifests(root):
    """构建清单 hits (通用构建工具, 只查顶层两级)。"""
    hits = []
    for dirpath, dirs, files in os.walk(root):
        depth = dirpath[len(root.rstrip(os.sep)):].count(os.sep)
        if depth > 2:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in BUILD_MANIFESTS:
                hits.append(os.path.relpath(os.path.join(dirpath, f), root))
    return hits


def _read_readme(root):
    for name in ("README.md", "README", "README.rst", "README.txt"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            try:
                return open(p, errors="ignore").read()
            except OSError:
                return ""
    return ""


def recommend(root):
    """机械推荐: {recommended, signals, confidence}。"""
    signals = []
    counts = _scan_files(root)
    total = sum(counts.values())

    # S1 规模档位 (与 surface_mapper.size_tier 阈值一致)
    if total > 2000:
        scale_class = "super-large"
    elif total > 500:
        scale_class = "large"
    elif total > 100:
        scale_class = "medium"
    else:
        scale_class = "small"
    signals.append({"id": "S1", "signal": "file_count",
                    "evidence": f"源码文件 {total} (生成层合并视图)",
                    "recommends": f"scale_class={scale_class}"})

    # S2 DSL 扩展名普查 → generation_layers 建议 (只从通用 dsl_entries 拷贝命中项;
    # 未入注册表的项目专属 DSL 主代理手工补录)
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent not in sys.path:
        sys.path.insert(0, parent)
        sys.path.insert(0, os.path.join(parent, "src"))
    import generation_registry as gr
    reg = gr.load()
    known = {e["ext"]: e for e in reg.get("dsl_entries", [])}
    layers = []
    for ext, n in sorted(counts.items()):
        if ext in known:
            e = known[ext]
            layers.append({"ext": ext, "role": e.get("role", "dsl"),
                           "lang_family": e.get("lang_family", ".c"),
                           "generates": e.get("generates", []),
                           "provenance": "dsl_entries"})
            signals.append({"id": "S2", "signal": "dsl_ext",
                            "evidence": f"{ext} 命中 {n} 文件 (通用 DSL 族)",
                            "recommends": f"generation_layers+{ext}"})
    # 提示级: 高占比非默认扩展名 (可能为项目专属 DSL, 主代理裁决是否补录)
    default = gr.default_extensions()
    unlisted = sorted(((e, n) for e, n in counts.items()
                       if e not in default and e not in known),
                      key=lambda x: -x[1])[:5]
    for ext, n in unlisted:
        signals.append({"id": "S2u", "signal": "unlisted_ext",
                        "evidence": f"{ext} 命中 {n} 文件 (非默认扩展名)",
                        "recommends": "主代理裁决: 项目专属 DSL 补录 generation_layers"})

    # S2j JIT 编译器目录信号 → generation_layers+jit 建议 (v3.23, SWR-V3.23-003;
    # 仅建议, 主代理签收; JIT 优化正确性层轴测绘的门控信号)
    for pat in ("src/compiler/maglev", "src/compiler/turbofan", "src/jit",
                "jit_compiler", "src/backend"):
        hits = _find_files(root, pat)
        if hits:
            layers.append({"ext": "jit", "role": "runtime_layer",
                           "lang_family": "runtime",
                           "generates": ["machine_code"],
                           "provenance": "jit_dir_signal"})
            signals.append({"id": "S2j", "signal": "jit_dir",
                            "evidence": f"JIT 编译器目录信号: {pat} ({len(hits)} 命中)",
                            "recommends": "generation_layers+jit"})
            break

    # S3 构建清单 hits → 两阶段测绘信号 (super-large 载体)
    manifests = _scan_build_manifests(root)
    if manifests:
        signals.append({"id": "S3", "signal": "build_manifest",
                        "evidence": f"构建清单 {manifests[:3]} 等 {len(manifests)} 处",
                        "recommends": "组件清单按构建目标分组"})

    # S4 README 语义面关键词 → surface_model 推荐
    readme = _read_readme(root)
    sem_hits = sorted({kw for kw in SEMANTIC_KEYWORDS
                       if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])",
                                    readme, re.IGNORECASE)})
    surface_model = "entry"
    if len(sem_hits) >= 2:
        surface_model = "semantic"
        signals.append({"id": "S4", "signal": "semantic_keywords",
                        "evidence": f"README 命中 {sem_hits}",
                        "recommends": "surface_model=semantic"})

    # S5 目录信号 → managed-runtime 提示 (纯提示, 不直接推荐字段)
    dirs1 = set()
    for d in os.listdir(root):
        p = os.path.join(root, d)
        if os.path.isdir(p) and d not in SKIP_DIRS:
            dirs1.add(d.lower())
    if dirs1 & set(MANAGED_DIR_SIGNALS):
        signals.append({"id": "S5", "signal": "managed_dir",
                        "evidence": f"顶层目录含 {sorted(dirs1 & set(MANAGED_DIR_SIGNALS))}",
                        "recommends": "managed-runtime 清单族适用 (提示级)"})

    # S6 沙箱关键词 → containment_default 推荐
    blob = readme + " " + " ".join(manifests)
    containment = "none"
    if re.search(r"(?<![a-z0-9])sandbox(?![a-z0-9])", blob, re.IGNORECASE) \
            or any(k in blob for k in ("沙箱", "沙盒")):
        containment = "process_sandbox"
        signals.append({"id": "S6", "signal": "sandbox_keyword",
                        "evidence": "README/构建清单命中沙箱关键词",
                        "recommends": "containment_default=process_sandbox"})

    # SWR-V3.45-006: 交付物引导面探针——static-only 判定前核对树内是否自带
    # 可引导产物与宿主仿真/交叉编译工具 (K2-7 实录: 三候选+复活者各自独立证伪
    # 同一 static-only 前提; 判定依据从未核对交付树内已构建镜像)。提示级建议,
    # 主代理签收后消费者装载, 零信号零行为变化。
    boot_hits = []
    for _g in ("arch/*/boot/Image", "arch/*/boot/bzImage", "arch/*/boot/zImage",
               "arch/x86/boot/vmlinux.bin"):
        boot_hits.extend(glob.glob(os.path.join(root, _g)))
    for _f in ("vmlinux", "vmlinuz", "bzImage"):
        if os.path.isfile(os.path.join(root, _f)):
            boot_hits.append(os.path.join(root, _f))
    qemu = shutil.which("qemu-system-aarch64") or shutil.which("qemu-system-x86_64") \
        or shutil.which("qemu-system-riscv64") or shutil.which("qemu-system-arm")
    xgcc = shutil.which("aarch64-linux-gnu-gcc") or shutil.which("x86_64-linux-gnu-gcc") \
        or shutil.which("riscv64-linux-gnu-gcc") or shutil.which("arm-linux-gnueabihf-gcc")
    empirical_modes = []
    if boot_hits and (qemu or xgcc):
        empirical_modes = ["real-target"]
        signals.append({"id": "S7", "signal": "bootable_artifact",
                        "evidence": f"树内可引导产物 {len(boot_hits)} 处 + 宿主 "
                                    f"qemu/交叉编译器信号 (qemu={bool(qemu)}, xgcc={bool(xgcc)})",
                        "recommends": "empirical_modes=[real-target] (提示级, "
                                      "主代理签收后生效, SWR-V3.45-006)"})
    recommended = {
        "surface_model": surface_model,
        "generation_layers": layers,
        "scale_class": scale_class,
        "containment_default": containment,
        "empirical_modes": empirical_modes,
    }
    conf = "high" if signals else "low"
    return {"recommended": recommended, "signals": signals, "confidence": conf}


def main(argv):
    if len(argv) < 2:
        print("usage: python3 tools/target_profile.py <project_root> [--write]",
              file=sys.stderr)
        return 2
    root = argv[1]
    out = recommend(root)
    if "--write" in argv[2:]:
        ar = os.path.join(root, ".audit_results")
        os.makedirs(ar, exist_ok=True)
        prof = {"recommended": out["recommended"], "signals": out["signals"],
                "confidence": out["confidence"], "signed_by": None,
                "overrides": {}}
        with open(os.path.join(ar, "target_profile.json"), "w") as f:
            json.dump(prof, f, ensure_ascii=False, indent=1)
        out["written"] = os.path.join(ar, "target_profile.json")
        out["note"] = ("signed_by 为空 = 未签收, 各消费者按全默认装载; "
                       "主代理复核后写入 signed_by/overrides")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
