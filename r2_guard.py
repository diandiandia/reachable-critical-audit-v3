#!/usr/bin/env python3
"""M12 r2_guard — R2 假设 schema 守卫 (v3.1 新增)。

满足: SWR-V3.1-070 (validate_hypothesis: surface_ids 强制数组 + 存在性),
      SWR-V3.1-071 (anchor_check: 锚点行 doc block/注释拦截),
      SWR-V3.1-072 (audit_filter_drops: keep/drop 全量落盘).

用法:
    python3 r2_guard.py validate <hypotheses.json> <input_surface.json>
    python3 r2_guard.py anchor <hypothesis.json> <project_root>
    python3 r2_guard.py drops <r2_filter_output.json>
"""
import json
import os
import re
import sys

# doc block / 纯注释行前缀（跨语言）
COMMENT_PREFIXES = ("//!", "//", "/*", "*", "#", "--", "'''", '"""', "//#")
DOC_BLOCK_RE = re.compile(
    r'^\s*(//!|/\*|\*|#|--|\'\'|"""|//\s*!|//\s*@|#\s*!)', re.IGNORECASE)


def validate_hypotheses(hypotheses, input_surface, strict=True):
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
    blocking = [i for i in issues if i["severity"] == "blocking"]
    return (len(blocking) == 0), issues


def anchor_check(hypothesis, project_root):
    """SWR-V3.1-071: 锚点行验证。sink 行必须是可执行代码而非文档注释/纯注释行。
    返回 {ok, reason, line_text}。"""
    f = hypothesis.get("source_file") or hypothesis.get("file")
    line = hypothesis.get("source_line") or hypothesis.get("line")
    if not f or not line:
        return {"ok": False, "reason": "锚点缺 file/line"}
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
        root = argv[3]
        r = anchor_check(hyp, root)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["ok"] else 1
    if cmd == "drops":
        data = json.load(open(argv[2]))
        kept = data.get("kept", [])
        dropped = data.get("dropped", [])
        out, missing = audit_filter_drops(kept, dropped)
        print(f"kept={len(kept)} dropped={len(dropped)} missing_reason={missing}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
