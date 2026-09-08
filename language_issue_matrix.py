#!/usr/bin/env python3
"""语言问题矩阵加载器 (v3.18, SWR-V3.18-002)。

per-language 知识基座的唯一读入口——R2 假设生成前的提示级消费
(SKILL.md R2 条款)。只返回已种格 (status=seeded); 未种格 (pending)
零注入零提示 (v3.6 confirmed:false 诚实占位先例)。

v3.28 (SWR-V3.28-001~004): Top15×Top10 目标物化——inventory 问题粒度层
(每语言排序问题条目, rank 机械计算不落盘)、goal 目标达成度视图、
seed 外部种格第二通道 (强制出处/去项目化/幂等)。

用法:
    python3 language_issue_matrix.py cells <lang> [family]
    python3 language_issue_matrix.py stats
    python3 language_issue_matrix.py inventory <lang>
    python3 language_issue_matrix.py goal
    python3 language_issue_matrix.py seed <json-file>
"""
import json
import os
import re
import sys

_DATA = None
_INV = None

# 语言别名归一 (与 tools/batch_verify._LANG_ALIAS 同规则): 签名侧标签 ↔ 账本规范名
_LANG_ALIAS = {"cs": "csharp", "ts": "javascript", "typescript": "javascript",
               "js": "javascript", "py": "python", "rb": "ruby",
               "ps1": "powershell", "kt": "kotlin", "sh": "shell"}

# v3.28 (SWR-V3.28-002): 族严重度档 (机械排序依据, 与报告严重度表同族)
_SEV_TIER = {"MEMORY-SAFETY": 1, "INJECTION": 1, "RESOURCE-DOS": 2, "RACE": 2,
             "STATE": 2, "AUTHN": 2, "ERROR-HANDLING": 2, "NUMERIC": 2,
             "DATA-INTEGRITY": 3, "CRYPTO": 3, "WEB": 3, "OTHER": 4}
# cwe 严重档 (严重表子集): 787/125/416/415/476/190/129/843/78/94/77/502/191
_SEV_CWE = {"787", "125", "416", "415", "476", "190", "129", "843",
            "78", "94", "77", "502", "191"}
# v3.28 (SWR-V3.28-004): 去项目化黑名单 (与 tests/test_deproject_assets 同口径)
_DEPROJECT_TOKENS = ("quickjs", "qjs", "bjson", "sinatra", "lighttpd", "mbedtls",
                     "django", "grpc", "jsrsasign", "awstats", "ktor", "actix")


def load():
    global _DATA
    if _DATA is not None:
        return _DATA
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "resources", "language_issue_matrix.json")
    try:
        with open(path, encoding="utf-8") as f:
            _DATA = json.load(f)
    except OSError:
        _DATA = {"langs": [], "families": [], "cells": []}
    return _DATA


def load_inventory():
    """v3.28 (SWR-V3.28-001): Top15×Top10 问题清单资产。缺失时返回空骨架。"""
    global _INV
    if _INV is not None:
        return _INV
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "resources", "language_issue_inventory.json")
    try:
        with open(path, encoding="utf-8") as f:
            _INV = json.load(f)
    except OSError:
        _INV = {"langs": [], "goal": {}, "entries": []}
    return _INV


def _cwe_max_sev(cwes):
    """cwe 列表的最大严重档: 命中严重表 → 1, 其余 → 2, 空 → 3。"""
    sev = 3
    for c in cwes or []:
        digits = re.sub(r"[^\d]", "", str(c))
        if digits in _SEV_CWE:
            sev = 1
        elif sev == 3:
            sev = 2
    return sev


def inventory_for(lang):
    """v3.28 (SWR-V3.28-002): 该语言问题条目, 按 (族严重档, cwe 最大严重度, id)
    机械排序。未知语言 → []。rank 不落盘 (排序是视图)。"""
    d = load_inventory()
    lg = _norm_lang(lang)
    out = [e for e in d.get("entries", []) if _norm_lang(e.get("lang", "")) == lg]
    out.sort(key=lambda e: (_SEV_TIER.get(e.get("family", "OTHER"), 4),
                            _cwe_max_sev(e.get("cwe")), e.get("id", "")))
    return out


def goal_progress():
    """v3.28 (SWR-V3.28-003): 目标达成度视图——每语言距 Top10 缺口 + K1/K2 进度。"""
    d = load_inventory()
    inv = d.get("entries", [])
    goal = d.get("goal", {})
    target = goal.get("per_lang_target", 10)
    k1 = goal.get("milestones", {}).get("K1", {}).get("criterion", "")
    k2 = goal.get("milestones", {}).get("K2", {}).get("criterion", "")
    per_lang = []
    k1_ok = k2_ok = 0
    for lg in d.get("langs", []):
        es = [e for e in inv if e.get("lang") == lg]
        bc = sum(1 for e in es if e.get("verify", {}).get("status") == "battle_confirmed")
        ext = sum(1 for e in es if e.get("source", {}).get("tier") == "external_seeded")
        if len(es) >= target:
            k1_ok += 1
        if bc >= target:
            k2_ok += 1
        per_lang.append({"lang": lg, "entries": len(es),
                         "gap_to_target": max(0, target - len(es)),
                         "battle_confirmed": bc,
                         "external_seeded": ext})
    return {
        "goal": {"per_lang_target": target},
        "milestones": {
            "K1": {"criterion": k1, "progress": f"{k1_ok}/{len(d.get('langs', []))}"},
            "K2": {"criterion": k2, "progress": f"{k2_ok}/{len(d.get('langs', []))}"},
        },
        "per_lang": per_lang,
        "totals": {"entries": len(inv),
                   "battle_confirmed": sum(1 for e in inv
                                           if e.get("verify", {}).get("status")
                                           == "battle_confirmed")},
    }


def seed_entries(path):
    """v3.28 (SWR-V3.28-004): 外部种格第二通道。
    逐条校验: tier 枚举 + external_seeded 强制 origin/date + lang 枚举 +
    cwe 格式 + 去项目化扫描 + (lang,title) 幂等。返回 {added, rejected}。"""
    d = load()
    inv = load_inventory()
    langset = {_norm_lang(l) for l in d.get("langs", [])}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"added": 0, "rejected": [f"file: {e}"]}
    candidates = payload.get("entries", payload if isinstance(payload, list) else [])
    existing = {(e.get("lang"), e.get("title")) for e in inv.get("entries", [])}
    added, rejected = [], []
    for e in candidates:
        problems = []
        src = e.get("source") or {}
        if src.get("tier") not in ("battle_verified", "external_seeded", "source_seeded"):
            problems.append("bad tier")
        if src.get("tier") == "external_seeded" and not (src.get("origin") and src.get("date")):
            problems.append("external_seeded 缺 origin/date")
        if _norm_lang(e.get("lang", "")) not in langset:
            problems.append("bad lang")
        for c in e.get("cwe", []):
            if not re.fullmatch(r"CWE-\d+", str(c)):
                problems.append(f"bad cwe {c}")
                break
        blob = json.dumps({k: v for k, v in e.items()
                           if k not in ("source",)}, ensure_ascii=False).lower()
        if any(tok in blob for tok in _DEPROJECT_TOKENS):
            problems.append("deproject token")
        if (e.get("lang"), e.get("title")) in existing:
            problems.append("duplicate")
        if problems:
            rejected.append({**( {k: e.get(k) for k in ("lang", "title")} ),
                             "reasons": problems})
            continue
        n = sum(1 for x in inv["entries"] if x.get("lang") == e.get("lang")) + 1
        e.setdefault("id", f"INV-{e['lang']}-{n:03d}")
        e.setdefault("verify", {"status": "unverified", "battles": [],
                                "candidates": [], "date": None})
        inv["entries"].append(e)
        existing.add((e.get("lang"), e.get("title")))
        added.append(e.get("id"))
    if added:
        here = os.path.dirname(os.path.abspath(__file__))
        out = os.path.join(here, "resources", "language_issue_inventory.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(inv, f, ensure_ascii=False, indent=1)
    return {"added": added, "rejected": rejected}


def _norm_lang(lang):
    """账本规范名归一 (别名 → 规范名; 未知保留原值)。"""
    lg = (lang or "").strip().lower()
    return _LANG_ALIAS.get(lg, lg)


def cells_for(lang, family=None):
    """该语言已种格条目列表 (family 给定时过滤)。未知语言/pending 格 → []。
    只返回 status=seeded——pending 零注入是消费者契约。"""
    d = load()
    lg = _norm_lang(lang)
    fam = (family or "").strip().upper()
    out = []
    for c in d.get("cells", []):
        if _norm_lang(c.get("lang", "")) != lg:
            continue
        if c.get("status") != "seeded":
            continue
        if fam and (c.get("family") or "").upper() != fam:
            continue
        out.append(c)
    return out


def stats():
    """{seeded, per_lang, per_family, total}——验收盘点与缺口可见性。"""
    d = load()
    langs = d.get("langs", [])
    fams = d.get("families", [])
    seeded = [c for c in d.get("cells", []) if c.get("status") == "seeded"]
    per_lang = {lg: sum(1 for c in seeded if c["lang"] == lg) for lg in langs}
    per_family = {f: sum(1 for c in seeded if c["family"] == f) for f in fams}
    return {"total_cells": len(langs) * len(fams),
            "seeded": len(seeded),
            "pending": len(langs) * len(fams) - len(seeded),
            "per_lang": per_lang,
            "per_family": per_family}


def main(argv):
    if len(argv) < 2 or argv[1] not in ("cells", "stats", "inventory", "goal",
                                        "seed"):
        print("usage: python3 language_issue_matrix.py "
              "cells <lang> [family] | stats | inventory <lang> | goal | "
              "seed <json-file>", file=sys.stderr)
        return 2
    if argv[1] == "stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=1))
        return 0
    if argv[1] == "goal":
        print(json.dumps(goal_progress(), ensure_ascii=False, indent=1))
        return 0
    if len(argv) < 3:
        print(f"usage: python3 language_issue_matrix.py {argv[1]} <arg>",
              file=sys.stderr)
        return 2
    if argv[1] == "cells":
        out = cells_for(argv[2], argv[3] if len(argv) > 3 else None)
    elif argv[1] == "inventory":
        out = inventory_for(argv[2])
    else:  # seed
        out = seed_entries(argv[2])
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
