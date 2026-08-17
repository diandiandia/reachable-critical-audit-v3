#!/usr/bin/env python3
"""D-COMP-10 checklist_binder — 假设/候选 → 家族检查清单自动绑定 (v3.1 新增)。

满足: REQ-V3.1-050 (家族清单绑定), REQ-V3.1-051 (绑定规则: cwe/语义家族/关键词),
      REQ-V3.1-052 (任务书清单注入), REQ-V3.1-053 (H7 默认值模板绑定).

用法:
    python3 checklist_binder.py bind <candidate.json>   # 输出绑定的清单 id 列表
    python3 checklist_binder.py bind-all <verify_queue.json>  # 全队列绑定并写回
"""
import json
import os
import re
import sys

DEFAULT_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "resources", "checklist_library.json")


def load_library(path=None):
    with open(path or DEFAULT_LIB, encoding="utf-8") as f:
        return json.load(f)


def _cwe_set(candidate):
    cw = candidate.get("cwe")
    if cw is None:
        cw = candidate.get("sink_type")
    if isinstance(cw, str):
        try:
            parsed = json.loads(cw.replace("'", '"'))
            if isinstance(parsed, list):
                cw = parsed
        except Exception:
            pass
    if isinstance(cw, list):
        return {str(c).upper() for c in cw}
    if cw:
        return {str(cw).upper()}
    return set()


def _candidate_text(candidate):
    return " ".join(str(candidate.get(k) or "")
                    for k in ("sink_type", "summary", "snippet", "title", "claim"))


def bind(candidate, lib=None):
    """SWR-V3.1-050/051: 按 binding 规则匹配清单。返回 [(checklist_id, matched_rule)]。
    binding 支持两种形态：结构化 dict {cwe:[], keywords:[], verdict_context?}
    （v3.1 标准）或字符串（兼容旧格式，按引号/括号提取关键词）。"""
    lib = lib or load_library()
    cwe = _cwe_set(candidate)
    text = _candidate_text(candidate)
    verdict = candidate.get("verdict")
    bound = []
    for ck in lib.get("checklists", []):
        rule = ck.get("binding", "")
        matched = []
        if isinstance(rule, dict):
            want = {str(w).upper() for w in (rule.get("cwe") or [])}
            if want & cwe:
                matched.append(f"cwe-match:{sorted(want & cwe)}")
            for kw in (rule.get("keywords") or []):
                alts = [a for a in re.split(r"[/、]", str(kw)) if len(a) >= 2]
                if any(a.lower() in text.lower() for a in alts):
                    matched.append(f"kw:{kw}")
                    break  # keywords 任一命中即匹配
            vc = rule.get("verdict_context")
            if vc and vc != verdict:
                matched = []
            if rule.get("applies_to_phase") == "R5":
                matched = []  # 实证类清单由 R5 流程显式绑定
        else:
            for m in re.findall(r"cwe\s*[∈=]\s*\{([^}]*)\}", rule):
                want = {w.strip().upper() for w in m.split(",") if w.strip()}
                if want & cwe:
                    matched.append(f"cwe-match:{sorted(want & cwe)}")
            kw_sources = re.findall(
                r"[\"“]([^\"”]{2,40})[\"”]|『([^』]{2,40})』|[（(]([^（）()]{2,60})[）)]",
                rule)
            for grp in kw_sources:
                kw = next((g for g in grp if g), "")
                alts = [a for a in re.split(r"[/、]", kw) if len(a) >= 2]
                if any(a.lower() in text.lower() for a in alts):
                    matched.append(f"kw:{kw}")
        if matched:
            bound.append((ck.get("id"), matched))
    return bound


def bind_all(queue, lib=None):
    """SWR-V3.1-052: 全队列绑定，checklist_ids 写回候选（不覆盖已有）。"""
    lib = lib or load_library()
    for c in queue.get("candidates", []):
        bound = bind(c, lib)
        if bound:
            c.setdefault("checklist_ids", [])
            for cid, why in bound:
                if cid not in c["checklist_ids"]:
                    c["checklist_ids"].append(cid)
            c.setdefault("checklist_bindings", []).append(
                {cid: why for cid, why in bound})
    return queue


def h7_template_bind():
    """SWR-V3.1-053: H7 默认值全表模板绑定（固定集合）。"""
    return ["CK-DEFAULT-VALUE-TABLE", "CK-DEFAULT-3LAYER", "CK-SENTINEL-SEMANTICS"]


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "bind":
        cand = json.load(open(argv[2]))
        for cid, why in bind(cand):
            print(f"{cid}: {why}")
        return 0
    if cmd == "bind-all":
        path = argv[2]
        queue = json.load(open(path))
        bind_all(queue)
        json.dump(queue, open(path, "w"), ensure_ascii=False, indent=1)
        n = sum(1 for c in queue.get("candidates", []) if c.get("checklist_ids"))
        print(f"bound {n} candidates")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
