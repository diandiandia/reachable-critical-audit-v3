#!/usr/bin/env python3
"""M4 evidence_ledger — 证据账本：分级校验、前提维度、merge 写回、断言门禁。

满足: SWR-V3-030 (grade_verdict 三级分级), SWR-V3-031 (边证据 proof 强制),
      SWR-V3-032 (check_preconditions: platform/trust/gate),
      SWR-V3-033 (commit merge 语义 + correction_record),
      SWR-V3-034 (assert_ledger 四门禁).
用法:
    python3 evidence_ledger.py grade <verdict.json>      # 分级校验
    python3 evidence_ledger.py check <verdict.json>      # 前提维度检查
    python3 evidence_ledger.py assert <verify_queue.json>  # 账本断言
"""
import json
import os
import re
import sys

GRADES = ("static_only", "edge_proven", "empirically_confirmed")
VERDICTS = ("REACHABLE", "UNREACHABLE", "NEEDS_REVIEW")
EMPIRICAL_CLAIMS = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos")
HYPOTHESES_IDS = [f"H-{i}" for i in range(1, 8)]
EMPIRICAL_MARKERS = ("实测", "实证", "empirically", "harness", "rack-test",
                     "cargo test", "curl", "e2e", "端到端", "probe", "pytest")
CONFIRMED_EMPIRICAL_STATUSES = ("confirmed", "empirically_confirmed", "passed")
DEFAULT_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "resources", "precedent_library.json")


def load_lenient(path):
    """SWR-V3.1-040: lenient JSON load + 单遍转义修复 (W6 §3.1-3.3)。
    字符串内 `\\` 后接合法转义（含 `\\u`+4hex）原样保留；否则双写该 `\\` 并
    跳过下一字符（单遍扫描不重审，杜绝修复振荡 §3.2）。"""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_fix_escapes_single_pass(text))


def _fix_escapes_single_pass(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
            out.append(ch)
            i += 1
            continue
        if in_str and ch == "\\":
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt in '"\\/bfnrt':
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            if nxt == "u" and i + 5 < n and \
               all(c in "0123456789abcdefABCDEF" for c in text[i + 2:i + 6]):
                out.append(text[i:i + 6])
                i += 6
                continue
            # 非法转义: 双写该反斜杠, 跳过下一字符, 不重审 (§3.2 单遍规则)
            out.append("\\\\")
            if nxt:
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def extract_empirical_marker(v):
    """SWR-V3.1-041: 从 evidence 文本自动提取实证标记 (W6 §15.2)。
    只填 empirical 字段供门禁③可见性检查，不自动升级 grade（§17.7 范围纪律:
    升级仍需 status ∈ CONFIRMED_EMPIRICAL_STATUSES）。"""
    if v.get("empirical") and isinstance(v["empirical"], dict) and v["empirical"].get("status"):
        return v["empirical"]
    ev = (v.get("evidence") or "") + " " + (v.get("r35_note") or "")
    hits = [m for m in EMPIRICAL_MARKERS if m.lower() in ev.lower()]
    if hits:
        return {"status": "marker_found_unverified",
                "markers": hits,
                "extracted_by": "evidence_ledger v3.1",
                "note": "evidence 文本含实证标记, 等级待主代理确认 (§15.2/§17.7)"}
    return None


def grade_verdict(v):
    """SWR-V3-030/031: 分级规则 + 边证据校验。
    返回 (grade, errors)。REACHABLE 无逐跳 edge_evidence → static_only;
    边证据项缺 proof → 报错; empirical 字段非空 → empirically_confirmed。"""
    errors = []
    if v.get("verdict") not in VERDICTS:
        errors.append("verdict 非法")
    if v.get("evidence_grade") is not None and v["evidence_grade"] not in GRADES:
        errors.append(f"evidence_grade 非法: {v['evidence_grade']}")
    empirical = v.get("empirical")
    if empirical and isinstance(empirical, dict) and \
       empirical.get("status") in CONFIRMED_EMPIRICAL_STATUSES:
        grade = "empirically_confirmed"
    else:
        chain = v.get("call_chain", [])
        edges = v.get("edge_evidence", [])
        for e in edges:
            if "edge" not in e or "proof" not in e or not str(e.get("proof", "")).strip():
                errors.append(f"边证据缺 proof: {e}")
        if v.get("verdict") == "REACHABLE":
            if not edges or len(edges) < max(len(chain) - 1, 0):
                grade = "static_only"
                errors.append("REACHABLE 无逐跳边证据 → 自动降级 static_only (REQ-V3-042)")
            else:
                grade = "edge_proven"
        else:
            grade = "edge_proven" if edges else "static_only"
    return grade, errors


def check_preconditions(v):
    """SWR-V3-032: 前提维度检查。返回 Issue 列表。"""
    issues = []
    pp = v.get("platform_precondition")
    if pp and not v.get("platform_evidence"):
        issues.append({"severity": "blocking",
                       "msg": "platform_precondition 存在但无 platform_evidence (需 NEEDS_REVIEW)"})
    tb = v.get("trust_boundary")
    if tb:
        for ch, rec in (tb.get("channels") or {}).items():
            if not rec:
                issues.append({"severity": "blocking",
                               "msg": f"trust_boundary 通道 {ch} 无逐通道验证记录"})
    if v.get("gate") is not None and not v.get("gate_note"):
        issues.append({"severity": "warn", "msg": "gate 存在但无 gate_note 说明"})
    if v.get("verdict") == "REACHABLE" and v.get("evidence_grade") == "static_only":
        issues.append({"severity": "blocking",
                       "msg": "REACHABLE 且 static_only 不得申报 (REQ-V3-042)"})
    return issues


def commit(queue, verdict):
    """SWR-V3-033: merge 语义写回（只增改不覆写）。证伪/降级追加 correction_record。"""
    if "candidates" not in queue:
        queue["candidates"] = []
    cid = verdict.get("id")
    found = None
    for c in queue["candidates"]:
        if c.get("id") == cid:
            found = c
            break
    if verdict.get("correction"):
        for c in queue["candidates"]:
            if c.get("id") == verdict["correction"].get("target"):
                c.setdefault("correction_record", []).append(verdict["correction"])
                if verdict["correction"].get("demote_to"):
                    c["verdict"] = verdict["correction"]["demote_to"]
                    c["evidence_grade"] = "static_only"
    if found is None:
        found = {"id": cid}
        queue["candidates"].append(found)
    for k, val in verdict.items():
        if k != "correction":
            found[k] = val
    return queue


TERMINAL_STATUSES = {"VERIFIED", "ESCALATED", "NEEDS_REVIEW"}


def assert_ledger(queue, dispatched=None, surface_data=None, require_target_kind=True):
    """SWR-V3-034 + REQ-V3-093/095/096 + SWR-V3.2.1-004/040: 门禁。
    ①no_pending ②REACHABLE 无 static_only ③实证类 100% ④H1-H7 全 VERIFIED
    ⑤对账零差异 (dispatched 提供时: 每个已派发 id 必须有终态)
    ⑥escalated=0 或主代理签收 (escalated_signed_off)
    ⑦surface 覆盖率=100% (surface_data 提供时)
    ⑧target_kind_required (v3.2.1, require_target_kind=False 仅复跑兼容)
    r4_feedback (v3.2.1, warn 级): H-7 默认值盘点与 R3 REACHABLE gate 证据冲突检测
    返回 (ok, violations)。dispatched/surface_data 为 None 时对应门禁跳过并记 skip_note。
    ⑧/r4_feedback 之外的 warn 级违规不阻断 PASS (v3.2.1 起 ok 只计 blocking)。"""
    violations = []
    skipped = []
    cands = queue.get("candidates", [])
    pending = [c.get("id") for c in cands if c.get("status") == "PENDING"]
    if pending:
        violations.append({"gate": "no_pending", "ids": pending})
    for c in cands:
        if c.get("verdict") == "REACHABLE" and c.get("evidence_grade") == "static_only":
            violations.append({"gate": "no_static_only_reachable", "id": c.get("id")})
        claim = (c.get("claim_type") or "")
        if any(k in claim for k in EMPIRICAL_CLAIMS) and \
           c.get("evidence_grade") != "empirically_confirmed":
            violations.append({"gate": "empirical_required", "id": c.get("id"),
                               "claim": claim})
    r4 = queue.get("r4_findings", [])
    have = {h.get("hypothesis_id") for h in r4 if h.get("status") == "VERIFIED"}
    missing = [h for h in HYPOTHESES_IDS if h not in have]
    if missing:
        violations.append({"gate": "r4_all_verified", "missing": missing})
    # ⑤对账 (REQ-V3-093)
    if dispatched is not None:
        by_id = {c.get("id"): c for c in cands}
        unresolved = [d for d in dispatched
                      if by_id.get(d, {}).get("status") not in TERMINAL_STATUSES]
        if unresolved:
            violations.append({"gate": "reconciliation", "unresolved_ids": unresolved})
    else:
        skipped.append("reconciliation")
    # ⑥escalated (REQ-V3-092/096)
    escalated = [c.get("id") for c in cands if c.get("status") == "ESCALATED"]
    if escalated and not queue.get("escalated_signed_off"):
        violations.append({"gate": "escalated_unsigned", "ids": escalated})
    # ③c v3.2 (SWR-V3.2-051): R3.5-N 复活攻击完成度——声称类 UNREACHABLE
    # 必须有 resurrection_review (防漏放, 313 验收 etcd 三连救回的制度化)
    for c in cands:
        if c.get("verdict") != "UNREACHABLE":
            continue
        text = " ".join(str(c.get(k) or "")
                        for k in ("claim_type", "evidence", "summary")).lower()
        if any(k in text for k in EMPIRICAL_CLAIMS) and \
           not c.get("resurrection_review"):
            violations.append({"gate": "resurrection_required", "id": c.get("id")})
    # ③b R4 findings 同受实证类门禁 (W6 §18.9)。
    # 验收级: empirically_confirmed 或 source_fact(哨兵/算术类, 附 note/blocker,
    # §17.7/§21.4 源事实级规则)——其余均违规。
    for f in r4:
        # gate ③b 只约束 confirmed 假说的 findings——reviewed_clean 的
        # 正向确认/Info 条目 (如 "verified in-bounds") 不是漏洞声称
        if f.get("verdict") != "confirmed":
            continue
        findings = f.get("findings") or []
        for fi in findings:
            claim = (fi.get("claim_type") or
                     (fi.get("title") or "") + " " + (fi.get("evidence") or ""))
            if any(k in claim.lower() for k in EMPIRICAL_CLAIMS):
                st = fi.get("empirical_status")
                if st == "empirically_confirmed":
                    continue
                if st == "source_fact" and (fi.get("empirical_note") or fi.get("blocker")):
                    continue
                violations.append({"gate": "empirical_required_r4",
                                   "hypothesis": f.get("hypothesis_id"),
                                   "finding": fi.get("title", "")[:60],
                                   "empirical_status": st})
    # ⑦surface 覆盖 (REQ-V3-095)
    if surface_data is not None:
        total = surface_data.get("total", 0)
        tracked_ids = set(surface_data.get("tracked_ids") or [])
        if tracked_ids:
            # v3.2.2 (REQ-V3.2.2-020): mirror_pairs 镜像自动传播——
            # kept-first 多域冲突对中任一 surface 被 tracked, 对端镜像同样视为覆盖
            # (mbedtls 审计: 15 冲突对曾需主代理手写 coverage_bridge)
            mps = surface_data.get("mirror_pairs") or []
            for a, b in mps:
                if a in tracked_ids or b in tracked_ids:
                    tracked_ids.update((a, b))
            tracked = len(tracked_ids)
        else:
            # 兼容旧调用: 只给计数 (无 id 列表) → 无镜像传播能力
            tracked = surface_data.get("tracked", 0)
        if total <= 0 or tracked / total < 1.0:
            violations.append({"gate": "surface_coverage",
                               "tracked": tracked, "total": total})
    else:
        skipped.append("surface_coverage")
    # ⑧target_kind (v3.2.1, SWR-V3.2.1-004): R0 未签收 target_kind 不得启动 R3
    if require_target_kind and not queue.get("target_kind"):
        violations.append({"gate": "target_kind_required",
                           "msg": "verify_queue.target_kind 缺失 (R0 判定未签收); "
                                  "仅复跑旧队列时以 require_target_kind=False 豁免"})
    # r4_feedback (v3.2.1, SWR-V3.2.1-040, warn 级): H-7 默认值盘点 ↔ R3 gate 证据冲突
    conflicts = r4_feedback(queue)
    if conflicts:
        violations.append({"gate": "r4_feedback", "severity": "warn",
                           "conflicts": conflicts})
    if skipped:
        violations.append({"gate": "skipped_gates", "gates": skipped,
                           "severity": "warn"})
    ok = len([v for v in violations
              if v["gate"] != "skipped_gates" and v.get("severity", "blocking") != "warn"]) == 0
    return ok, violations


def r4_feedback(queue):
    """SWR-V3.2.1-040: R4 H-7 默认值盘点 ↔ R3 REACHABLE gate 证据冲突检测 (warn 级)。
    窗口双镜头匹配 (W6 §25.4 真实形态):
    - 候选侧 code-lens: key[=:]value 或 key+零值/默认/缺省+value, 且 ±40 字符窗内有
      默认主张词 (零值|默认|缺省|明文|开启) → 声称部署态 = 代码默认值 V_c
    - H-7 侧 committed-lens: key[=:]value 直接赋值; 或 key 后 40 字符窗内
      (配置|仓库|shipped|committed|实际值)=value → 提交值 V_h
    V_c ≠ V_h → 冲突 (主代理裁决)。动机: Lersosa H-7 f1 (仓库配置=true) 在
    CAND-008 原判定 (代码默认 tls_enable=false→明文) 出错处是对的。"""
    conflicts = []
    assign_re = re.compile(
        r"([a-z_][a-z0-9_]*)\s*[=:]\s*(true|false|\"[^\"]{1,40}\"|\d+)")
    # key + 可选镜头词 + 可选赋值符 + value ("tls_enable 零值 false" 形态)
    gap_val_re = re.compile(
        r"([a-z_][a-z0-9_]*)\s*(?:零值|默认|缺省)\s*[=:]?\s*"
        r"(true|false|\"[^\"]{1,40}\"|\d+)")
    commit_ctx_re = re.compile(
        r"(?:配置|仓库|shipped|committed|实际值)\s*[=:]\s*"
        r"(true|false|\"[^\"]{1,40}\"|\d+)")
    code_ctx_re = re.compile(r"零值|默认|缺省|明文|开启")
    h7 = [h for h in queue.get("r4_findings", []) if h.get("hypothesis_id") == "H-7"]
    h7_committed = {}
    for h in h7:
        for f in h.get("findings", []):
            text = " ".join(str(f.get(k) or "")
                            for k in ("title", "evidence", "correction_record"))
            # 形态1: key=value 直接赋值 ("tls_enable=true (shipped config)")
            for m in assign_re.finditer(text):
                h7_committed.setdefault(m.group(1), []).append((m.group(2), text[:120]))
            # 形态2: key 出现后 50 字符内的 (配置|仓库|shipped|...)=value 零回指
            # ("tls_enable 代码零值=false（明文），仓库配置=true", W6 §25.4 真实形态)
            for m in re.finditer(r"([a-z_][a-z0-9_]+)", text):
                tail = text[m.end(): m.end() + 50]
                cm = commit_ctx_re.search(tail)
                if cm:
                    h7_committed.setdefault(m.group(1), []).append((cm.group(1), text[:120]))
    if not h7_committed:
        return conflicts
    for c in queue.get("candidates", []):
        if c.get("verdict") != "REACHABLE":
            continue
        text = " ".join(str(c.get(k) or "")
                        for k in ("evidence", "call_chain", "gate_note",
                                  "trust_boundary", "summary"))
        seen = set()
        for m in list(assign_re.finditer(text)) + list(gap_val_re.finditer(text)):
            key, cand_val = m.group(1), m.group(2)
            if key not in h7_committed or (key, cand_val) in seen:
                continue
            seen.add((key, cand_val))
            ctx = text[max(0, m.start() - 40): m.end() + 40]
            if not code_ctx_re.search(ctx):
                continue  # 无默认主张词 → 不构成"部署态=代码默认值"声称
            for h7_val, snippet in h7_committed[key]:
                if h7_val != cand_val:
                    conflicts.append({
                        "candidate": c.get("id"), "key": key,
                        "candidate_code_lens_value": cand_val,
                        "h7_committed_value": h7_val,
                        "h7_source": snippet[:120]})
                    break
    # v3.2.2 (v3.2.2 候选遗留): resolved 标记位——主代理裁决后的冲突
    # 写 {candidate, key, resolved_by, note}, 不再重复告警 (W6 §25.6 遗留)
    resolved = {(r.get("candidate"), r.get("key")) for r in
                queue.get("r4_feedback_resolved", []) if isinstance(r, dict)}
    if resolved:
        conflicts = [c for c in conflicts
                     if (c.get("candidate"), c.get("key")) not in resolved]
    return conflicts


def consistency_check(queue):
    """SWR-V3.1-042: 同 sink 家族 verdict 可比性断言 (PREC-CONSISTENCY-001, W6 §18.3/§23.4)。
    同一 (source_file, sink_type) 家族内出现 REACHABLE 与 UNREACHABLE 并存且
    双方均无 blocking_point/correction_record 解释不对称性 → warn。"""
    groups = {}
    for c in queue.get("candidates", []):
        if c.get("status") not in TERMINAL_STATUSES or not c.get("verdict"):
            continue
        # v3.2 (SWR-V3.2-050): 分组键增加 lang——跨语言同 sink 形态不触发告警
        # (PREC-MULTI-LANG-001); 同 lang 组内保持 v3.1 一致性断言
        fam = (c.get("source_file"), (c.get("sink_type") or c.get("cwe") or ""),
               c.get("lang"))
        groups.setdefault(fam, []).append(c)
    issues = []
    for fam, cs in groups.items():
        if len(cs) < 2:
            continue
        verdicts = {c.get("verdict") for c in cs}
        if len(verdicts) > 1 and "REACHABLE" in verdicts and "UNREACHABLE" in verdicts:
            # 家族内任一路径有阻断点/裁决记录即构成可区分性解释 (§18.3:
            # 判据是"路径能否区分"——有阻断点即可区分)
            explained = any(c.get("correction_record") or c.get("blocking_point")
                            or c.get("r35_adjudication") for c in cs)
            if not explained:
                issues.append({"severity": "warn",
                               "msg": f"同 sink 家族 {fam} 裁决不可比且无解释 (PREC-CONSISTENCY-001)",
                               "ids": [c.get("id") for c in cs]})
    return issues


def check_correction_schema(queue, precedent_lib=None):
    """SWR-V3.1-043: correction_record schema 校验 (W6 §24.9/§16.12)。
    correction_record 若引用 precedent_ids 必须存在于先例库；r35_adjudication
    存在时 correction_record 必须存在（降级裁决结构化落盘义务）。"""
    issues = []
    known = set()
    if precedent_lib is not None:
        known = {p.get("id") for p in precedent_lib.get("precedents", [])}
    for c in queue.get("candidates", []):
        adj = c.get("r35_adjudication")
        if adj and adj.get("demote") and not c.get("correction_record"):
            issues.append({"severity": "warn",
                           "msg": f"{c.get('id')} 有降级裁决但无 correction_record 落盘 (SWR-V3.1-043)"})
        for rec in (c.get("correction_record") or []):
            if not isinstance(rec, dict):
                continue
            for pid in (rec.get("precedent_ids") or []):
                if pid not in known:
                    issues.append({"severity": "warn",
                                   "msg": f"{c.get('id')} correction_record 引用未知先例 {pid}"})
    return issues


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "grade":
        v = load_lenient(argv[2])
        grade, errors = grade_verdict(v)
        print(f"grade={grade}")
        for e in errors:
            print("  -", e)
        return 0
    if cmd == "check":
        v = load_lenient(argv[2])
        issues = check_preconditions(v)
        for i in issues:
            print(f"[{i['severity']}] {i['msg']}")
        blocking = [i for i in issues if i["severity"] == "blocking"]
        return 1 if blocking else 0
    if cmd == "assert":
        q = load_lenient(argv[2])
        # v3.2.1: --legacy-no-target-kind 仅复跑旧队列 (R0 未签收 target_kind) 时豁免门禁⑧
        ok, violations = assert_ledger(
            q, require_target_kind="--legacy-no-target-kind" not in argv)
        for v in violations:
            print("  -", json.dumps(v, ensure_ascii=False)[:200])
        print("ASSERT_PASSED" if ok else "ASSERT_FAILED")
        return 0 if ok else 1
    if cmd == "consistency":
        q = load_lenient(argv[2])
        lib = None
        if os.path.exists(DEFAULT_LIB):
            lib = load_lenient(DEFAULT_LIB)
        issues = consistency_check(q) + check_correction_schema(q, lib)
        for i in issues:
            print(f"[{i['severity']}] {i['msg']}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
