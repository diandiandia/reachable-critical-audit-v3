#!/usr/bin/env python3
"""M12 r2_guard — R2 假设 schema 守卫 (v3.1 新增)。

满足: SWR-V3.1-070 (validate_hypothesis: surface_ids 强制数组 + 存在性),
      SWR-V3.1-071 (anchor_check: 锚点行 doc block/注释拦截),
      SWR-V3.1-072 (audit_filter_drops: keep/drop 全量落盘).

用法:
    python3 r2_guard.py validate <hypotheses.json> <input_surface.json>
    python3 r2_guard.py anchor <hypothesis.json> <project_root>
    python3 r2_guard.py drops <r2_filter_output.json>
    python3 r2_guard.py fidelity <r2_filter_result.json> [hypotheses.json]
        # SWR-V3.4.6-002: 落盘保真——bc/drop 缺 surface_ids 时从 hypotheses.json
        # 反查补齐 (restored_from_hypotheses 标记), 缺 hypotheses 参数自动探测同目录
"""
import glob
import json
import os
import re
import sys

# doc block / 纯注释行前缀（跨语言）
COMMENT_PREFIXES = ("//!", "//", "/*", "*", "#", "--", "'''", '"""', "//#")
DOC_BLOCK_RE = re.compile(
    r'^\s*(//!|/\*|\*|#|--|\'\'|"""|//\s*!|//\s*@|#\s*!)', re.IGNORECASE)


def validate_hypotheses(hypotheses, input_surface, strict=True, project_root=None):
    """SWR-V3.1-070: 假设 schema 校验。
    - surface_ids 必须为数组（单值字符串/缺失 → 违规, W6 §9.6/§12.6/§16.7 三次重现的根修）
    - 每个 surface_id 必须存在于 input_surface.json（孤儿假设拦截）
    返回 (ok, issues)。"""
    hyps = hypotheses.get("hypotheses", []) if isinstance(hypotheses, dict) else hypotheses
    known = {s.get("id") for s in
             (input_surface.get("surfaces", []) if isinstance(input_surface, dict) else input_surface)}
    issues = []
    for h in hyps:
        hid = h.get("hypothesis_id") or h.get("id", "<no-id>")
        sids = h.get("surface_ids") or h.get("surface_id") or []
        if isinstance(sids, str):
            issues.append({"severity": "blocking",
                           "msg": f"{hid}: surface_ids 为单值字符串, 必须为数组 (W6 §9.6)"})
            sids = [sids]
        if not sids:
            issues.append({"severity": "blocking",
                           "msg": f"{hid}: surface_ids 缺失 (门禁⑦簿记依赖, W6 §16.7)"})
        for sid in sids:
            if sid not in known:
                issues.append({"severity": "blocking",
                               "msg": f"{hid}: surface_id {sid} 不存在于 input_surface.json"})
    for h in hyps:
        hid = h.get("hypothesis_id") or h.get("id", "<no-id>")
        if h.get("lang_pair") and not h.get("lang"):
            issues.append({"severity": "warn",
                           "msg": f"{hid}: lang_pair 存在但缺 lang (v3.2 boundary 假设)"})
    # v3.2.1 (SWR-V3.2.1-050): gate 语义含"默认可达/默认开启"且 shipped_config.json
    # 存在 → 强制追加第三层检查引用条款 (W6 §25.4: 代码零值≠shipped 实际值)
    sc = os.path.join(project_root or "", ".audit_results", "shipped_config.json")
    if os.path.exists(sc):
        for h in hyps:
            hid = h.get("hypothesis_id") or h.get("id", "<no-id>")
            gate = str(h.get("gate") or "")
            if any(k in gate for k in ("默认", "默认可达", "默认开启", "默认明文")):
                issues.append({
                    "severity": "warn",
                    "msg": (f"{hid}: gate 声称默认可达——必须引用 "
                            f".audit_results/shipped_config.json 第三层检查"
                            f"(shipped 配置实际值, 而非代码零值, W6 §25.4)")})
    blocking = [i for i in issues if i["severity"] == "blocking"]
    return (len(blocking) == 0), issues


def anchor_check(hypothesis, project_root):
    """SWR-V3.1-071: 锚点行验证。sink 行必须是可执行代码而非文档注释/纯注释行。
    v3.2.2 (REQ-V3.2.2-013): 兼容 hit_sites 数组形态 (R2 假设数据模型)。
    返回 {ok, reason, line_text}。"""
    f = hypothesis.get("source_file") or hypothesis.get("file")
    line = hypothesis.get("source_line") or hypothesis.get("line")
    if (not f or not line) and hypothesis.get("hit_sites"):
        hs = hypothesis["hit_sites"][0]
        f, line = hs.get("file"), hs.get("line")
    if not f or not line:
        return {"ok": False, "reason": "锚点缺 file/line (候选需 source_file/source_line 或 hit_sites[0])"}
    path = f if os.path.isabs(f) else os.path.join(project_root, f)
    if not os.path.exists(path):
        return {"ok": False, "reason": f"锚点文件不存在: {path}"}
    try:
        with open(path, errors="ignore") as fh:
            lines = fh.read().splitlines()
        ln = int(line)
        text = lines[ln - 1] if 0 < ln <= len(lines) else ""
    except (OSError, ValueError):
        return {"ok": False, "reason": f"锚点行读取失败: {path}:{line}"}
    stripped = text.strip()
    if not stripped or DOC_BLOCK_RE.match(text) or stripped.startswith(COMMENT_PREFIXES):
        return {"ok": False, "reason": "锚点行是文档注释/纯注释/空行 (退化候选, W6 §23.7)",
                "line_text": text[:60]}
    return {"ok": True, "line_text": text[:60]}


def anchor_check_all(hypotheses, project_root):
    """v3.2.2 (REQ-V3.2.2-013): 批量锚点检查 (hit_sites 全量)。
    CLI 用; 返回 (ok, results)。"""
    hyps = hypotheses.get("hypotheses", []) if isinstance(hypotheses, dict) else hypotheses
    results = []
    for h in hyps:
        hid = h.get("hypothesis_id") or h.get("id", "<no-id>")
        for hs in h.get("hit_sites", []):
            r = anchor_check(hs, project_root)
            results.append({"hypothesis": hid, "file": hs.get("file"),
                            "line": hs.get("line"), **r})
    bad = [r for r in results if not r["ok"]]
    return (len(bad) == 0), results


def audit_filter_drops(kept, dropped, path=None):
    """SWR-V3.1-072: keep/drop 全量落盘（dropped_by + reason 必填, W6 §16.7）。
    返回 (data, missing_reasons) — drop 条目缺 reason 时强制补 "unrecorded"。"""
    data = {"kept": kept, "dropped": dropped,
            "audited_at": "2026-08-17", "schema_version": "3.1"}
    missing = []
    for d in dropped:
        if not d.get("reason"):
            d["reason"] = "unrecorded"
            missing.append(d.get("id") or d.get("hypothesis_id"))
        d.setdefault("dropped_by", "unrecorded")
    if path:
        json.dump(data, open(path, "w"), ensure_ascii=False, indent=1)
    return data, missing


# v3.4.6 filter 产出三组键名 (模板 canonical) 与 v3.1 落盘键名 (kept/dropped) 双形态
_FILTER_GROUPS = ("keep", "drop", "boundary_confirmations", "kept", "dropped")


def restore_surface_ids(data, hypotheses):
    """SWR-V3.4.6-002: filter 产出 surface_ids 保真。
    keep/drop/boundary_confirmations 三组条目缺 surface_ids 时, 从 hypotheses.json
    按 id 反查补齐 (对旧产出兼容, 缺字段不拒收只修复), 补后写
    restored_from_hypotheses 标记。返回 (data, restored_ids)。
    门禁⑦ tracked 覆盖簿记只认 surface_ids; bc/drop 丢字段 → 覆盖虚低 →
    假缺口阻断收尾 (quic-go 41→31 实录)。"""
    hyps = {}
    if isinstance(hypotheses, dict):
        for h in hypotheses.get("hypotheses", []):
            hid = h.get("id") or h.get("hypothesis_id")
            if hid:
                hyps[hid] = h
    restored = []
    for group in _FILTER_GROUPS:
        for item in data.get(group, []):
            if not isinstance(item, dict):
                continue
            sids = item.get("surface_ids") or item.get("surface_id") or []
            if isinstance(sids, str):
                sids = [sids]
            if sids:
                continue
            src = hyps.get(item.get("id"))
            if not src:
                continue
            sids = src.get("surface_ids") or src.get("surface_id") or []
            if isinstance(sids, str):
                sids = [sids]
            if sids:
                item["surface_ids"] = sids
                item["restored_from_hypotheses"] = True
                restored.append(item.get("id"))
    return data, restored


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "validate":
        hyps = json.load(open(argv[2]))
        surf = json.load(open(argv[3]))
        ok, issues = validate_hypotheses(hyps, surf)
        print("OK" if ok else "FAIL")
        for i in issues:
            print(f"  [{i['severity']}] {i['msg']}")
        return 0 if ok else 1
    if cmd == "anchor":
        hyp = json.load(open(argv[2]))
        root = argv[3] if len(argv) > 3 else "."
        # v3.2.2: 假设文件 (hit_sites 数组) → 批量检查; 单候选 → 单点检查
        if isinstance(hyp, dict) and "hypotheses" in hyp:
            ok, results = anchor_check_all(hyp, root)
            for r in results:
                print(f"{'OK ' if r['ok'] else 'BAD'} {r['hypothesis']} "
                      f"{r.get('file')}:{r.get('line')} {r.get('reason')}")
            return 0 if ok else 1
        r = anchor_check(hyp, root)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["ok"] else 1
    if cmd == "drops":
        data = json.load(open(argv[2]))
        kept = data.get("kept", [])
        # v3.2.2 (REQ-V3.2.2-012): 键名归一——filter 任务书模板产出 "drop" (单数),
        # 守卫读 "dropped" (复数) 曾静默报 0 (mbedtls 审计实测)
        dropped = data.get("dropped") or data.get("drop") or []
        out, missing = audit_filter_drops(kept, dropped)
        print(f"kept={len(kept)} dropped={len(dropped)} missing_reason={missing}")
        return 0
    if cmd == "fidelity":
        # SWR-V3.4.6-002: surface_ids 保真校验/修复 (r2_filter_result.json)
        data = json.load(open(argv[2]))
        hyps = None
        if len(argv) > 3:
            hyps = json.load(open(argv[3]))
        else:
            cand = os.path.join(os.path.dirname(os.path.abspath(argv[2])), "hypotheses.json")
            if os.path.exists(cand):
                hyps = json.load(open(cand))
            else:
                # SWR-V3.10-004: 波次回退——多波批次的主文件可能尚未合并,
                # glob _r2_hypotheses_*.json 合并反查 (kernel 审计 K1/K2 分波
                # 文件形态下主文件缺失 WARN 实录); 全部缺失才跳过
                wdir = os.path.dirname(os.path.abspath(argv[2]))
                merged = {"hypotheses": [], "logic_hypotheses": []}
                for wp in sorted(glob.glob(
                        os.path.join(wdir, "_r2_hypotheses_*.json"))):
                    try:
                        wd = json.load(open(wp))
                        merged["hypotheses"].extend(wd.get("hypotheses", []) or [])
                        merged["logic_hypotheses"].extend(
                            wd.get("logic_hypotheses", []) or [])
                    except (OSError, ValueError):
                        pass
                if merged["hypotheses"] or merged["logic_hypotheses"]:
                    hyps = merged
                else:
                    print("WARN: hypotheses.json 缺失, 跳过反查修复", file=sys.stderr)
        data, restored = restore_surface_ids(data, hyps or {})
        json.dump(data, open(argv[2], "w"), ensure_ascii=False, indent=2)
        print(f"surface_ids_fidelity: restored={restored}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
