#!/usr/bin/env python3
"""D-COMP-10 checklist_binder — 假设/候选 → 家族检查清单自动绑定 (v3.1 新增)。

满足: REQ-V3.1-050 (家族清单绑定), REQ-V3.1-051 (绑定规则: cwe/语义家族/关键词),
      REQ-V3.1-052 (任务书清单注入).

用法:
    python3 checklist_binder.py bind <candidate.json>   # 输出绑定的清单 id 列表
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


def _kw_match(kw, text):
    """SWR-V3.4.4-001: 关键词匹配——ASCII 关键词按词边界 (防 "ws" 误配
    "jws", jsrsasign CAND-001 实测); CJK 关键词保持子串语义 (无词边界概念)。"""
    kw = str(kw).lower()
    if kw.isascii():
        return re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text) is not None
    return kw in text


def _signals_ok(sig, candidate, text):
    """SWR-V3.4.3-040: 清单适用性门控——applicability_signals 存在时必须命中
    才绑定 (CK-WS-MATERIALIZE 经 cwe CWE-400 误绑纯 JWT 库的 P1/P2 教训)。
    形态: {text:[关键词], requires_lang:[lang], requires_claim:[claim 子串]}。"""
    if not sig:
        return True
    tl = text.lower()
    if sig.get("text"):
        if not any(_kw_match(k, tl) for k in sig["text"]):
            return False
    if sig.get("requires_lang"):
        langs = sig["requires_lang"]
        if not isinstance(langs, list):
            langs = [langs]
        clang = str(candidate.get("lang") or candidate.get("language") or "").lower()
        if not any(_kw_match(l, clang) for l in langs):
            return False
    if sig.get("requires_claim"):
        claims = sig["requires_claim"]
        if not isinstance(claims, list):
            claims = [claims]
        cclaim = str(candidate.get("claim_type") or "").lower()
        if not any(str(k).lower() in cclaim for k in claims):
            return False
    return True


# SWR-V3.4.3-040: 资源族 cwe 命中专属清单但信号不匹配时的通用兜底
_RESOURCE_CWES = {"CWE-400", "CWE-789", "CWE-770", "CWE-401", "CWE-833"}

# v3.5.2 (B9): R5 实证类清单的真实绑定触发集——与 SKILL R5 强制声称集一致
# (crash/panic/oom/unbounded/xss/protocol_dos/rce/leak)。
# 旧实现: applies_to_phase=="R5" → 无条件 matched=[] → CK-EMPIRICAL-SCOPE 永不可达。
R5_CLAIM_TYPES = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos",
                  "rce", "leak")


def _in_r5_semantic_space(candidate):
    """v3.5.2 (B9): 候选是否已进入实证语义空间——empirical dict 已存在
    (R5 回填/写回), 或 claim_type ∈ R5 强制声称集 (将触发实证义务)。"""
    if isinstance(candidate.get("empirical"), dict):
        return True
    claim = str(candidate.get("claim_type") or "").lower()
    return any(c in claim for c in R5_CLAIM_TYPES)


def bind(candidate, lib=None):
    """SWR-V3.1-050/051: 按 binding 规则匹配清单。返回 [(checklist_id, matched_rule)]。
    binding 支持两种形态：结构化 dict {cwe:[], keywords:[], verdict_context?}
    （v3.1 标准）或字符串（兼容旧格式，按引号/括号提取关键词）。
    v3.4.3 (SWR-V3.4.3-040): applicability_signals 门控 + 资源族信号不匹配时
    绑 CK-GENERIC-RESOURCE 兜底 (不再把 WS 专属清单绑给非 WS 候选)。"""
    lib = lib or load_library()
    cwe = _cwe_set(candidate)
    text = _candidate_text(candidate)
    verdict = candidate.get("verdict")
    bound = []
    resource_mismatch = False
    for ck in lib.get("checklists", []):
        rule = ck.get("binding", "")
        matched = []
        want = set()
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
                # v3.5.2 (B9, 过设计裁决): 实证类清单真实绑定——候选进入实证
                # 语义空间 (empirical dict / claim_type ∈ R5 强制声称集) 时绑定,
                # 不依赖 keywords 碰巧命中; 否则维持不绑定 (非实证候选不注入)。
                if _in_r5_semantic_space(candidate):
                    if not matched:
                        matched.append("r5-semantic")
                else:
                    matched = []
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
            # SWR-V3.4.3-040: 信号门控——cwe 命中但问题域不匹配 → 不绑定
            if ck.get("applicability_signals") and \
                    not _signals_ok(ck["applicability_signals"], candidate, text):
                if want & _RESOURCE_CWES:
                    resource_mismatch = True
                continue
            bound.append((ck.get("id"), matched))
    if resource_mismatch and not bound:
        bound.append(("CK-GENERIC-RESOURCE", ["signal-mismatch-fallback"]))
    return bound


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "bind":
        cand = json.load(open(argv[2]))
        for cid, why in bind(cand):
            print(f"{cid}: {why}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
