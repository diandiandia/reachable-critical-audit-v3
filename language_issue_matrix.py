#!/usr/bin/env python3
"""语言问题矩阵加载器 (v3.18, SWR-V3.18-002)。

per-language 知识基座的唯一读入口——R2 假设生成前的提示级消费
(SKILL.md R2 条款)。只返回已种格 (status=seeded); 未种格 (pending)
零注入零提示 (v3.6 confirmed:false 诚实占位先例)。

用法:
    python3 language_issue_matrix.py cells <lang> [family]
    python3 language_issue_matrix.py stats
"""
import json
import os
import sys

_DATA = None

# 语言别名归一 (与 tools/batch_verify._LANG_ALIAS 同规则): 签名侧标签 ↔ 账本规范名
_LANG_ALIAS = {"cs": "csharp", "ts": "javascript", "typescript": "javascript",
               "js": "javascript", "py": "python", "rb": "ruby",
               "ps1": "powershell", "kt": "kotlin", "sh": "shell"}


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
    if len(argv) < 2 or argv[1] not in ("cells", "stats"):
        print("usage: python3 language_issue_matrix.py cells <lang> [family] | "
              "stats", file=sys.stderr)
        return 2
    if argv[1] == "stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=1))
        return 0
    if len(argv) < 3:
        print("usage: python3 language_issue_matrix.py cells <lang> [family]",
              file=sys.stderr)
        return 2
    out = cells_for(argv[2], argv[3] if len(argv) > 3 else None)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
