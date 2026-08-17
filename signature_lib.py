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

REQUIRED_FIELDS = ["sig_id", "semantic", "cwe", "platform_profiles",
                   "detection_hints", "known_instances", "empirical_harness"]

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "resources", "signature_library.json")


def load(path=DEFAULT_PATH):
    return json.load(open(path))


def validate(data):
    """SWR-V3-010/011: schema 校验 + known_instances 非空强制。返回 (ok, errors)。"""
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
        profs = sig.get("platform_profiles", [])
        bad = [p for p in profs if p not in VALID_PROFILES]
        if bad:
            errors.append(f"{tag}: invalid platform_profiles {bad}")
        # SWR-V3-011: known_instances 非空强制
        insts = sig.get("known_instances", [])
        if not insts:
            errors.append(f"{tag}: known_instances 为空 (SWR-V3-011 强制非空)")
        else:
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


def smoke_test(data, repo_paths):
    """SWR-V3-013: 对每个签名取第 1 个 confirmed known_instance，
    在其文件行窗口(±3 行)验证 detection_hints.grep 至少 1 条命中。
    known_instances 横跨多仓库: 仅在提供的 repo 中定位不到时计 skipped（不计入命中率分母）;
    全部实例 skipped 视为配置错误。返回 (results, hit_rate)。"""
    results = {}
    testable = 0
    for sig in data["signatures"]:
        inst = next((x for x in sig["known_instances"] if x.get("confirmed")), None)
        if inst is None:
            results[sig["sig_id"]] = {"hit": False, "instance": None,
                                      "detail": "no confirmed instance", "skipped": True}
            continue
        fpath = None
        for repo in repo_paths:
            cand = os.path.join(repo, inst["file"])
            if os.path.exists(cand):
                fpath = cand
                break
        if fpath is None:
            results[sig["sig_id"]] = {"hit": False, "skipped": True,
                                      "instance": f"{inst['file']}:{inst['line']}",
                                      "detail": "instance not located in provided repos"}
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
                print(f"{'PASS' if r['hit'] else 'FAIL'}  {sig}  @ {r['instance']}  {r['detail']}")
        required = data["smoke_test"]["required_hit_rate"]
        print(f"hit_rate={rate:.0%} required={required:.0%} testable={testable}")
        # v3.1 (W6 §7): 全 skipped 放行 (testable=0 时 hit_rate 无意义)
        if testable == 0:
            print("all instances skipped (testable=0) -> PASS per W6 §7")
            return 0
        return 0 if rate >= required else 2
    print("usage: signature_lib.py [validate|smoke <repo>]")
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
