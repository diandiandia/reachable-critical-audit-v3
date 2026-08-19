#!/usr/bin/env python3
"""M11 precedent_library — 先例检索 + 自证伪提示生成 + 应用回填 (v3.1 新增)。

满足: SWR-V3.1-030 (match 检索), SWR-V3.1-031 (self_refutation_hints),
      SWR-V3.1-032 (record_application 幂等回填), SWR-V3.1-033 (add_precedent).

用法:
    python3 precedent_library.py match <candidate.json>
    python3 precedent_library.py hints <candidate.json>
    python3 precedent_library.py record <precedent_id> <application.json>
"""
import json
import os
import sys

DEFAULT_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "resources", "precedent_library.json")

# cwe 家族 → 先例 id 硬映射（Host 采信族/absolute-form 族等跨语言家族）
CWE_FAMILY_MAP = {
    ("CWE-436", "CWE-444", "CWE-601"): ["PREC-HOST-FAMILY-001",
                                          "PREC-VICTIM-TRIGGER-001",
                                          "PREC-DOC-DESIGN-001"],
    ("CWE-400",): ["PREC-STREAM-MATERIALIZE-001", "PREC-ENGINE-MATRIX-001",
                   "PREC-GATE-RATING-001"],
    ("CWE-770", "CWE-789"): ["PREC-GATE-RATING-001", "PREC-STREAM-MATERIALIZE-001"],
    ("CWE-1333",): ["PREC-RUNTIME-VERSION-001"],
}

# summary 关键词 → 先例 id（默认/gate/引擎/能力/文档等前提形态）
KEYWORD_MAP = {
    "默认": ["PREC-DEFAULT-3LAYER-001"],
    "gate": ["PREC-DEFAULT-3LAYER-001", "PREC-CONFIG-FLIP-001", "PREC-GATE-RATING-001"],
    "引擎": ["PREC-ENGINE-MATRIX-001"],
    "能力": ["PREC-CAPABILITY-001"],
    "前提": ["PREC-CONDITIONAL-REACHABLE-001"],
    "文档": ["PREC-DOC-DESIGN-001"],
    "开发": ["PREC-DEV-FACE-001"],
    "矩阵": ["PREC-MATRIX-001"],
    "类型": ["PREC-TYPE-SYSTEM-001"],
    "流式": ["PREC-STREAM-MATERIALIZE-001"],
    "needs_review": ["PREC-DUAL-LENS-001"],
    "host": ["PREC-HOST-FAMILY-001"],
    "referer": ["PREC-VICTIM-TRIGGER-001"],
}

_CACHE = {}


def load(path=None):
    path = path or DEFAULT_LIB
    if path not in _CACHE:
        with open(path, encoding="utf-8") as f:
            _CACHE[path] = json.load(f)
    return _CACHE[path]


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
    return {str(cw).upper()} if cw else set()


def _candidate_text(candidate):
    """SWR-V3.1-030: 候选检索文本（match 与精度门共用）。"""
    return " ".join(str(candidate.get(k) or "")
                    for k in ("summary", "sink_type", "claim_type", "verdict",
                              "blocking_point", "r35_note", "lang", "lang_pair")).lower()


def _signals_ok(p, candidate, text):
    """SWR-V3.3.2-023: 先例精度门——applicability_signals 存在时必须命中才注入；
    无 signals 的先例不拦截（向后兼容，增量填充）。"""
    sig = p.get("applicability_signals")
    if not sig:
        return True
    if sig.get("text"):
        if not any(k.lower() in text for k in sig["text"]):
            return False
    if sig.get("requires_lang_pair") and not candidate.get("lang_pair"):
        return False
    return True


def match(candidate, lib=None):
    """SWR-V3.1-030: 按 cwe 家族/summary 关键词/claim_type 检索先例。
    返回命中先例全文（criterion 与 counterexample 都返回——counterexample 是
    适用性反查, W6 §11: 论据适用前提范围先于论据本身判定）。"""
    lib = lib or load()
    by_id = {p["id"]: p for p in lib.get("precedents", [])}
    hits = []
    seen = set()
    cwe = _cwe_set(candidate)
    text = _candidate_text(candidate)
    for fam, ids in CWE_FAMILY_MAP.items():
        if cwe & set(fam):
            for pid in ids:
                if by_id.get(pid) and pid not in seen:
                    seen.add(pid)
                    hits.append(by_id[pid])
    for kw, ids in KEYWORD_MAP.items():
        if kw in text:
            for pid in ids:
                if by_id.get(pid) and pid not in seen:
                    seen.add(pid)
                    hits.append(by_id[pid])
    # v3.2 (SWR-V3.2-030): lang_pair/lang 字段存在 → 多语言裁决分组先例
    if candidate.get("lang_pair") or candidate.get("lang"):
        pid = "PREC-MULTI-LANG-001"
        if by_id.get(pid) and pid not in seen:
            seen.add(pid)
            hits.append(by_id[pid])
    return hits


def self_refutation_hints(candidate, lib=None, max_hints=2):
    """SWR-V3.1-031: 匹配先例 → 证伪论据模板化（每候选 ≤2 条），
    注入 verifier 任务书作自证伪提示（W6 §17.10/§19.5 攻击面前置）。
    SWR-V3.3.2-023: 精度门——applicability_signals 不命中的先例不注入
    （Host 族先例误注入 Java 配置候选的七项目批次教训）。"""
    hits = match(candidate, lib)
    text = _candidate_text(candidate)
    hits = [p for p in hits if _signals_ok(p, candidate, text)]
    hints = []
    for p in hits[:max_hints]:
        hints.append(
            f"[{p['id']}] {p['name']}: {p['criterion']} "
            f"(注意适用前提: {p.get('applicability_scope', '')})")
    return hints


def record_application(precedent_id, application, path=None):
    """SWR-V3.1-032: 审计后回填 applications[]（幂等: 按 application.id 去重）。"""
    path = path or DEFAULT_LIB
    lib = load(path)
    found = None
    for p in lib.get("precedents", []):
        if p["id"] == precedent_id:
            found = p
            break
    if found is None:
        raise KeyError(f"precedent {precedent_id} 不存在")
    found.setdefault("applications", [])
    key = application.get("id") or application.get("candidate")
    if key and any(a.get("id") == key or a.get("candidate") == key
                   for a in found["applications"]):
        return lib
    found["applications"].append(application)
    _write(path, lib)
    return lib


def add_precedent(precedent, path=None):
    """SWR-V3.1-033: schema 校验后追加新先例（主代理自由裁量回填）。"""
    path = path or DEFAULT_LIB
    lib = load(path)
    required = ("id", "name", "criterion", "counterexample",
                "applicability_scope", "applications", "source_lessons")
    missing = [k for k in required if k not in precedent]
    if missing:
        raise ValueError(f"先例缺字段: {missing}")
    ids = {p["id"] for p in lib.get("precedents", [])}
    if precedent["id"] in ids:
        raise ValueError(f"先例 {precedent['id']} 已存在")
    lib.setdefault("precedents", []).append(precedent)
    _write(path, lib)
    return lib


def _write(path, lib):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=1)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "match":
        cand = json.load(open(argv[2]))
        for p in match(cand):
            print(f"- {p['id']} {p['name']}: {p['criterion'][:80]}")
        return 0
    if cmd == "hints":
        cand = json.load(open(argv[2]))
        for h in self_refutation_hints(cand):
            print("-", h)
        return 0
    if cmd == "record":
        app = json.load(open(argv[3]))
        record_application(argv[2], app)
        print(f"recorded into {argv[2]}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
