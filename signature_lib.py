#!/usr/bin/env python3
"""M2 signature_library — 语义签名库：schema 校验、known_instances 强制、冒烟测试。

满足: SWR-V3-010 (schema+校验器), SWR-V3-011 (known_instances 强制),
      SWR-V3-013 (冒烟测试: 每签名取 1 个 known_instance 验证 hints 可命中).
用法:
    python3 signature_lib.py validate                       # 校验 resources/signature_library.json
    python3 signature_lib.py smoke --repo /path/to/repo     # 对源码副本做冒烟测试
"""
import json
import re
import sys
import os

VALID_PROFILES = {"server-framework", "parser-library", "cgi-tool", "web-app",
                  "security-boundary", "cli-tool", "desktop", "embedded", "any"}

# v3.2.2 (P-A, REQ-V3.2.2-001/002): 通用型第一原则——资产去项目化。
# L2 词族签名必须声明 lang; L3 语义族 lang 缺省为 "any"。
VALID_LANGS = {"any", "c", "cpp", "python", "java", "go", "rust", "kotlin", "scala",
               "cs", "js", "ts", "typescript", "php", "perl", "ruby", "shell",
               "powershell", "ps", "swift", "lua"}

# 项目专属 API 名黑名单（mbedtls 审计复盘取证, 2026-08-17）。
# 命中任一 token 的 grep 模式或 semantic 文本 = 资产携带项目残留, validate 拒绝。
# token 匹配: 大小写不敏感子串。
DEPROJECT_BLACKLIST = [
    "multer", "replyto",                 # NestJS
    "maxdecodedcontentlength", "maxframesize",  # Ktor
    "good_origin", "request_origin",     # lighttpd mod
    "cleanxss",                          # WordPress/AWStats
    "safe_join", "validate_host", "get_host", "read_body",  # Django
    "required_args_constructor", "lersosa",  # Lersosa
    "wp-admin", "wwwroot", "xpc 鉴权",   # 历史项目目录名
    "checkautotype",                     # fastjson
    "configdir", "serve_from",           # AWStats 时代
]

FIXTURE_INSTANCES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "tests", "fixtures", "known_instances.json")

REQUIRED_FIELDS = ["sig_id", "semantic", "cwe", "platform_profiles",
                   "detection_hints", "known_instances", "empirical_harness"]

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resources", "signature_library.json")


def load(path=DEFAULT_PATH):
    return json.load(open(path))


def _deproject_scan(sig):
    """v3.2.2: 扫描 semantic + grep 模式, 命中项目专属名黑名单返回违规列表。"""
    hits = []
    haystack = (str(sig.get("semantic", "")) + " " +
                " ".join(sig.get("detection_hints", {}).get("grep", []))).lower()
    for tok in DEPROJECT_BLACKLIST:
        if tok in haystack:
            hits.append(tok)
    return hits


def validate(data):
    """SWR-V3-010/011 + v3.2.2: schema 校验 + lang 必填(L2) + 去项目化扫描。
    known_instances 非空强制退役 (v3.2.2): 回归锚点移入 tests/fixtures,
    validate 不再要求签名内嵌实例。返回 (ok, errors)。"""
    errors = []
    if not isinstance(data, dict) or "signatures" not in data:
        return False, ["missing 'signatures'"]
    seen_ids = set()
    for i, sig in enumerate(data["signatures"]):
        tag = sig.get("sig_id", f"<index {i}>")
        for f in REQUIRED_FIELDS:
            if f not in sig:
                errors.append(f"{tag}: missing field '{f}'")
        if sig.get("sig_id") in seen_ids:
            errors.append(f"{tag}: duplicate sig_id")
        seen_ids.add(sig.get("sig_id"))
        # v3.2.2: cwe 非空 + semantic 非空
        if not sig.get("cwe"):
            errors.append(f"{tag}: cwe 为空 (语义族必须 CWE 锚定)")
        if not str(sig.get("semantic", "")).strip():
            errors.append(f"{tag}: semantic 为空 (需抽象形态描述)")
        # v3.2.2: lang 必填 (L2 词族必须具体语言; L3 语义族缺省 any)
        tier = sig.get("tier") or sig.get("level")
        lang = sig.get("lang")
        if tier == "L2":
            if not lang or lang not in VALID_LANGS or lang == "any":
                errors.append(f"{tag}: L2 词族 lang 必填 (got {lang!r})")
        elif lang is not None and lang not in VALID_LANGS:
            errors.append(f"{tag}: invalid lang {lang!r}")
        # v3.2.2 (REQ-V3.2.2-001): 去项目化扫描
        for tok in _deproject_scan(sig):
            errors.append(f"{tag}: 项目专属名 '{tok}' 出现在 semantic/grep (第一原则三禁止①)")
        profs = sig.get("platform_profiles", [])
        bad = [p for p in profs if p not in VALID_PROFILES]
        if bad:
            errors.append(f"{tag}: invalid platform_profiles {bad}")
        insts = sig.get("known_instances", [])
        for inst in insts:
            if not all(k in inst for k in ("project", "file", "line", "confirmed")):
                errors.append(f"{tag}: instance 缺字段 {inst}")
        hints = sig.get("detection_hints", {})
        if "grep" not in hints or "checklist" not in hints:
            errors.append(f"{tag}: detection_hints 需含 grep 与 checklist")
        else:
            for pat in hints.get("grep", []):
                try:
                    re.compile(pat)
                except re.error as e:
                    errors.append(f"{tag}: bad grep pattern {pat!r}: {e}")
    smoke_cfg = data.get("smoke_test", {})
    if smoke_cfg.get("mode") != "anchor_recall" or "required_hit_rate" not in smoke_cfg:
        errors.append("smoke_test 配置缺失或非法")
    return (len(errors) == 0), errors


def _compile_grep(patterns):
    out = []
    for p in patterns:
        try:
            out.append(re.compile(p))
        except re.error as e:
            raise ValueError(f"bad grep pattern {p!r}: {e}")
    return out


def load_fixture_instances(path=FIXTURE_INSTANCES_PATH):
    """v3.2.2: 回归锚点从 resources 移入 tests/fixtures (第一原则三禁止③)。
    返回 {sig_id: [instances]}；fixture 文件缺失时返回空表（完整性自检会报缺）。"""
    if not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path))
    except (OSError, ValueError):
        return {}
    if isinstance(data, dict) and isinstance(data.get("instances"), list):
        out = {}
        for inst in data["instances"]:
            out.setdefault(inst.get("sig_id"), []).append(inst)
        return out
    return {}


def _scan_runtime_assets(base=None):
    """v3.5 (P5): 去项目化扫描扩展至运行时资产目录 (templates/harness + harness_manuals)。
    R0 selfcheck 完整性分支必须拦截模板/手册的项目残留回退——v3.5 体检实测模板曾
    硬编码 ktor/actix 端口与 AWStats 专属逻辑 (黑名单只扫签名资产是覆盖盲区)。
    返回 [(相对路径, 命中项)]。base 参数仅供测试注入临时目录。"""
    here = base or os.path.dirname(os.path.abspath(__file__))
    hits = []
    for rel in ("templates", "harness_manuals"):
        base_dir = os.path.join(here, rel)
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                p = os.path.join(root, fn)
                try:
                    text = open(p, errors="ignore").read()
                except OSError:
                    continue
                low = text.lower()
                for tok in DEPROJECT_BLACKLIST:
                    if tok in low:
                        hits.append((os.path.relpath(p, here), tok))
                if "/root/" in text:
                    hits.append((os.path.relpath(p, here), "绝对路径 /root/"))
    return hits


def integrity_selfcheck(data):
    """v3.2.2 (REQ-V3.2.2-005): 非 fixture 仓库的 R0 自检语义——
    签名库完整性: validate + lang 完备 + 去项目化 0 命中 + 全部 grep 可编译。
    v3.3 (REQ-V3.3-004): 追加 L2 词族 ↔ harness_manuals 覆盖对齐检查。
    v3.5 (P5): 去项目化扫描扩展至 templates/harness + harness_manuals。
    返回 (ok, detail_lines)。"""
    lines = []
    ok, errors = validate(data)
    if not ok:
        return False, errors
    for sig in data["signatures"]:
        tier = sig.get("tier") or sig.get("level")
        lang = sig.get("lang")
        if tier == "L2" and (not lang or lang == "any"):
            lines.append(f"{sig['sig_id']}: L2 词族缺具体 lang")
        tok = _deproject_scan(sig)
        if tok:
            lines.append(f"{sig['sig_id']}: 项目专属名 {tok}")
        try:
            _compile_grep(sig["detection_hints"]["grep"])
        except ValueError as e:
            lines.append(f"{sig['sig_id']}: {e}")
    for missed in l2_manual_alignment(data):
        lines.append(missed)
    for f, tok in _scan_runtime_assets():
        lines.append(f"{f}: 运行时资产残留 {tok}")
    if lines:
        return False, lines
    return True, [f"integrity OK: {len(data['signatures'])} signatures (lang/cwe/deproject/runtime-assets/manual 对齐完备)"]


def l2_manual_alignment(data):
    """v3.3 (REQ-V3.3-004, SWR-V3.3-011): L2 词族语言 ↔ harness_manuals 覆盖对齐。
    返回缺失行列表（空=对齐）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    manuals = set()
    mdir = os.path.join(here, "harness_manuals")
    if os.path.isdir(mdir):
        for fn in os.listdir(mdir):
            if fn.endswith(".md"):
                manuals.add(fn[:-3])
    missed = []
    langs = {s.get("lang") for s in data.get("signatures", [])
             if (s.get("tier") or s.get("level")) == "L2"
             and s.get("lang") not in (None, "any")}
    for lang in sorted(langs):
        if lang not in manuals:
            missed.append(f"L2 词族 {lang} 无 harness_manuals/{lang}.md")
    return missed


def smoke_test(data, repo_paths):
    """SWR-V3-013 + v3.2.2: 回归锚点取自 tests/fixtures/known_instances.json。
    - 实例在 repo 中可定位 (fixture 仓库) → anchor recall, hit_rate 检查
    - 全部 skipped (非 fixture 仓库) → 完整性自检 (integrity_selfcheck),
      结果挂在 results['__integrity__'], testable=0 放行语义不变 (W6 §7)
    返回 (results, hit_rate, testable)。"""
    results = {}
    testable = 0
    fixture = load_fixture_instances()
    if not fixture:
        results["__integrity__"] = {"hit": False, "skipped": True,
                                    "instance": None,
                                    "detail": "tests/fixtures/known_instances.json 缺失或空"}
    for sig in data["signatures"]:
        # v3.5 (P5): 多实例回退——某签名的 confirmed 锚点可能有多个项目 (v3.1 三锚点
        # 回归 + B4 扩军), 第一个 confirmed 的项目不在本次传入 repos 时继续尝试其余
        # 实例 (旧逻辑: 只试第一个, ktor jvm 锚点会让 Newtonsoft.Json 锚点不可达)。
        inst = fpath = None
        for cand_inst in fixture.get(sig["sig_id"], []):
            if not cand_inst.get("confirmed"):
                continue
            for repo in repo_paths:
                cand = os.path.join(repo, cand_inst["file"])
                if os.path.exists(cand):
                    inst, fpath = cand_inst, cand
                    break
            if fpath:
                break
        if inst is None:
            results[sig["sig_id"]] = {"hit": False, "instance": None,
                                      "detail": "no confirmed fixture instance located in repos", "skipped": True}
            continue
        testable += 1
        lines = open(fpath, errors="ignore").read().splitlines()
        lo = max(0, inst["line"] - 4)          # 行号 1-based, ±3 窗口
        hi = min(len(lines), inst["line"] + 3)
        window = "\n".join(lines[lo:hi])
        try:
            compiled = _compile_grep(sig["detection_hints"]["grep"])
        except ValueError as e:
            results[sig["sig_id"]] = {"hit": False, "skipped": True,
                                      "instance": f"{inst['file']}:{inst['line']}",
                                      "detail": str(e)}
            continue
        hit = any(rx.search(window) for rx in compiled)
        results[sig["sig_id"]] = {"hit": hit, "skipped": False,
                                  "instance": f"{inst['file']}:{inst['line']}",
                                  "detail": ("hit" if hit else
                                             f"no grep pattern matched window of {inst['file']}:{inst['line']}")}
    hit_rate = (sum(1 for r in results.values() if r["hit"]) / testable) if testable else 0.0
    if testable == 0:
        # v3.2.2: 非 fixture 仓库 → 完整性自检
        iok, ilines = integrity_selfcheck(data)
        results["__integrity__"] = {"hit": iok, "skipped": False,
                                    "instance": None, "testable": testable,
                                    "detail": "; ".join(ilines)[:500]}
    # v3.1 (W6 §7): 全 skipped (testable=0) 时 hit_rate=0 是合法状态——跨仓库锚点库
    # 单仓库审计必然全 skipped, 不得按字面 hit_rate<1.0 阻止启动
    return results, hit_rate, testable


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "validate"
    data = load()
    if cmd == "validate":
        ok, errors = validate(data)
        if ok:
            print(f"OK: {len(data['signatures'])} signatures valid")
            return 0
        print("FAIL:")
        for e in errors:
            print("  -", e)
        return 1
    if cmd == "smoke":
        repos = argv[2:] if len(argv) > 2 else ["."]
        results, rate, testable = smoke_test(data, repos)
        for sig, r in results.items():
            if r.get("skipped"):
                print(f"SKIP  {sig}  @ {r.get('instance')}  {r['detail']}")
            else:
                print(f"{'PASS' if r['hit'] else 'FAIL'}  {sig}  @ {r.get('instance')}  {r['detail']}")
        required = data["smoke_test"]["required_hit_rate"]
        print(f"hit_rate={rate:.0%} required={required:.0%} testable={testable}")
        # v3.1 (W6 §7): 全 skipped 放行 (testable=0 时 hit_rate 无意义)
        if testable == 0:
            integ = results.get("__integrity__", {})
            if integ.get("hit"):
                print(f"all instances skipped (testable=0) -> integrity: {integ.get('detail')}")
                return 0
            print(f"all instances skipped (testable=0) but integrity FAIL: {integ.get('detail')}")
            return 2
        return 0 if rate >= required else 2
    if cmd == "selfcheck":
        # v3.2.2 (REQ-V3.2.2-010): R0 单一事实源——SKILL.md 只引用这一条命令。
        # 用法: python3 signature_lib.py selfcheck [<repo>]  (省略 repo = 当前目录)
        repos = argv[2:] if len(argv) > 2 else ["."]
        ok, errors = validate(data)
        if not ok:
            print("FAIL: validate")
            for e in errors:
                print("  -", e)
            return 2
        results, rate, testable = smoke_test(data, repos)
        print(f"validate OK ({len(data['signatures'])} signatures); "
              f"hit_rate={rate:.0%} testable={testable}")
        if testable > 0:
            required = data["smoke_test"]["required_hit_rate"]
            if rate < required:
                print(f"FAIL: hit_rate {rate:.0%} < required {required:.0%}")
                for sig, r in results.items():
                    if not r.get("skipped") and not r["hit"]:
                        print(f"  - {sig}: {r['detail']}")
                return 2
            return 0
        integ = results.get("__integrity__", {})
        if integ.get("hit"):
            print(f"non-fixture repo -> {integ.get('detail')}")
            return 0
        print("FAIL: integrity self-check")
        print(f"  {integ.get('detail')}")
        return 2
    print("usage: signature_lib.py [validate|smoke <repo>|selfcheck [<repo>]]")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))


# ---------------- v3.1 增量 (SWR-V3.1-052: 贡献度退役) ----------------

def retire_low_contribution(data, threshold_pct=10.0, consecutive_batches=2):
    """SWR-V3.1-052: 连续 N 批次贡献度 <threshold 的签名退役入 retired_signatures
    (W6 §14.1/§19.1 通用 regex 零区分度先例的自动化)。
    贡献度 = hypotheses_contributed / 该批次假设总数（由调用方回填 contribution 后
    传入 batch_total）。未达到连续批次数不退役。"""
    retired = []
    for sig in data.get("signatures", []):
        cont = sig.get("contribution", {})
        batches = cont.get("batches_seen", 0)
        contributed = cont.get("hypotheses_contributed", 0)
        total = cont.get("batch_total", 0)
        if batches >= consecutive_batches and total > 0 and \
           contributed / total * 100 < threshold_pct:
            entry = {"sig_id": sig["sig_id"],
                     "retired_at": "2026-08-17",
                     "reason": f"连续 {batches} 批次贡献度 {contributed}/{total} < {threshold_pct}%"}
            data.setdefault("retired_signatures", []).append(entry)
            retired.append(sig["sig_id"])
    if retired:
        keep = [s for s in data["signatures"] if s["sig_id"] not in retired]
        data["signatures"] = keep
    return retired
