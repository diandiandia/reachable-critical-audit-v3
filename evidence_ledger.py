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
# v3.6 (P1-3): 8 类对齐 binder R5_CLAIM_TYPES 与 SKILL.md R5 触发判定
EMPIRICAL_CLAIMS = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos",
                    "rce", "leak")


def is_claim_like(cand, fields=("claim_type", "evidence", "summary")):
    """SWR-V3.15-002: 声称类判定单真相——复活池选样与门禁③c 同调此函数
    (双实现漂移三次漏选实录: s2n CAND-009/nghttp2 CAND-011/gpac CAND-011)。
    规则: claim_type 字段优先命中 EMPIRICAL_CLAIMS; 否则同字段集文本扫描降级。
    否定语境词行为两处一致即可——统一优先于否定语义精化。"""
    ct = str(cand.get("claim_type") or "").lower()
    if ct and any(k in ct for k in EMPIRICAL_CLAIMS):
        return True
    text = " ".join(str(cand.get(k) or "") for k in fields).lower()
    return any(k in text for k in EMPIRICAL_CLAIMS)


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
    边证据项缺 proof → 报错; empirical 字段非空 → empirically_confirmed。
    SWR-V3.4.3-011 (口径对齐): 本函数为 grade 唯一权威——collect 落盘时机械
    重算 (证据链/empirical 结构化字段), verifier 自报值存 grade_self_reported
    仅追溯, 不参与判定。"""
    errors = []
    if v.get("verdict") not in VERDICTS:
        errors.append("verdict 非法")
    if v.get("evidence_grade") is not None and v["evidence_grade"] not in GRADES:
        errors.append(f"evidence_grade 非法: {v['evidence_grade']}")
    empirical = v.get("empirical")
    # SWR-V3.3.2-003: status 比较前大小写归一化 (历史实证 "CONFIRMED" 大写与
    # 小写元组不匹配曾静默降级 edge_proven)
    # v3.4.1: 旧 schema 兼容——v3.3 前 empirical 字段无 status 但有 scope
    # (e2e/full_chain 级实证已记录 harness/result) → 按 scope 推断 confirmed,
    # 附告警提示回填 status (Lua 复跑实测: 2 候选被静默降级)
    status = str(empirical.get("status", "")).lower() if isinstance(empirical, dict) else ""
    scope_infer = (isinstance(empirical, dict)
                   and not status
                   and str(empirical.get("scope", "")).lower() in ("e2e", "full_chain"))
    if scope_infer:
        errors.append("旧 empirical schema 缺 status, 按 scope=e2e/full_chain 推断 "
                      "empirically_confirmed (建议回填 status:'confirmed')")
    # v3.20 (SWR-V3.20-006): canonical 保留键推断——SKILL.md R5 回填规范的
    # canonical 键集 (outcome/evidence_numbers/report) 与 status 判级互斥:
    # 按规范回填的 dict 永无法机械评到 empirically_confirmed, 存储分级不可
    # 复算 (WebKit 6 例实证候选实录)。三键齐全按已实测证据推断 confirmed,
    # 附回填提示 (同 v3.4.1 scope_infer 先例形态)
    canonical_infer = (isinstance(empirical, dict)
                       and not status and not scope_infer
                       and all(k in empirical for k in
                               ("outcome", "evidence_numbers", "report")))
    if canonical_infer:
        errors.append("empirical 缺 status, 按 canonical 保留键 (outcome/"
                      "evidence_numbers/report) 推断 empirically_confirmed "
                      "(建议回填 status:'confirmed')")
    if empirical and isinstance(empirical, dict) and \
       (status in CONFIRMED_EMPIRICAL_STATUSES or scope_infer or canonical_infer):
        grade = "empirically_confirmed"
    else:
        # v3.4.2: 旧队列显式 null (JSON null → None) 守卫——actix-web 复跑
        # CAND-010 edge_evidence=None 曾致 TypeError (None 不可迭代)
        chain = v.get("call_chain") or []
        edges = v.get("edge_evidence") or []
        for e in edges:
            if "edge" not in e or "proof" not in e or not str(e.get("proof", "")).strip():
                errors.append(f"边证据缺 proof: {e}")
        if v.get("verdict") == "REACHABLE":
            if not edges or len(edges) < max(len(chain) - 1, 0):
                grade = "static_only"
                # v3.8 (SWR-V3.8-007): 降级报错附计数——edges<chain-1 的常见根因是
                # verifier 输出合并边 (一条 proof 覆盖多跳), 计数 + 提示让主代理
                # 在收集时就定位, 不必等门禁②阻断才发现 (kafka/shardingsphere 双次实测)
                errors.append(
                    "REACHABLE 无逐跳边证据 → 自动降级 static_only (REQ-V3-042) "
                    f"[edges={len(edges)}, chain={len(chain)}, 需≥{max(len(chain) - 1, 0)}; "
                    "若 proof 文本覆盖多跳属合并边, 应从已有事实拆分为逐跳 edge_evidence]")
            else:
                grade = "edge_proven"
        else:
            grade = "edge_proven" if edges else "static_only"
    # SWR-V3.3.2-003: stored 与机械结果不一致 → 告警条目 (不再静默)
    stored = v.get("evidence_grade")
    if stored in GRADES and stored != grade:
        errors.append(f"evidence_grade 不一致: stored={stored} mechanical={grade} "
                      f"(建议写 grade_recomputed_by 标记)")
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
                    # SWR-V3.3.2-002: 声称只属 REACHABLE (REQ-V3.2.2-016)——
                    # demote 分支与 collect 的 claim-null 对称, 否则 NEEDS_REVIEW
                    # 残留 claim 误触发 gate ③
                    if c.get("claim_type"):
                        c["claim_type"] = None
                        c["claim_nulled_by"] = "commit-demote-v3.3.2"
    if found is None:
        found = {"id": cid}
        queue["candidates"].append(found)
    for k, val in verdict.items():
        if k != "correction":
            found[k] = val
    return queue


TERMINAL_STATUSES = {"VERIFIED", "ESCALATED", "NEEDS_REVIEW"}


def assert_ledger(queue, dispatched=None, surface_data=None, require_target_kind=True,
                  require_resurrection=True, require_r4_independent=True,
                  require_adjudication_verify=True, require_strengthen_verify=True):
    """SWR-V3-034 + REQ-V3-093/095/096 + SWR-V3.2.1-004/040: 门禁。
    ①no_pending ②REACHABLE 无 static_only ③实证类 100% ④H1-H7 全 VERIFIED
    ⑤对账零差异 (dispatched 提供时: 每个已派发 id 必须有终态)
    ⑥escalated=0 或主代理签收 (escalated_signed_off)
    ⑦surface 覆盖率=100% (surface_data 提供时)
    ⑧target_kind_required (v3.2.1, require_target_kind=False 仅复跑兼容)
    ③c 复活攻击完成度 (v3.2): require_resurrection=False 仅复跑 v3.2 机制发布前
    旧队列时豁免 (产出 warn 级豁免注记, 同 ⑧ 先例; v3.4.2)
    r4_feedback (v3.2.1, warn 级): H-7 默认值盘点与 R3 REACHABLE gate 证据冲突检测
    adjudication_unverified (v3.10.2, SWR-V3.10.2-014, warn 级): 主代理 demote
      裁决缺 adjudication_verification 核验记录 → 提示 (不阻断; 旧队列复跑以
      require_adjudication_verify=False 豁免, 同 ⑧/③c 先例)
    strengthen_unverified (v3.10.2, SWR-V3.10.2-015, warn 级): REACHABLE 候选
      存在未签收补强 (refutation.strengthened/attribution_correction 无
      *_verified_by) → 提示 (不阻断; 旧队列复跑以 require_strengthen_verify=False 豁免)
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
        # SWR-V3.3.2-001: gate ③ 前置 verdict==REACHABLE——声称只属 REACHABLE
        # (REQ-V3.2.2-016), NEEDS_REVIEW/UNREACHABLE 残留 claim 不触发实证门禁
        if c.get("verdict") == "REACHABLE" and \
           any(k in claim for k in EMPIRICAL_CLAIMS) and \
           c.get("evidence_grade") != "empirically_confirmed":
            violations.append({"gate": "empirical_required", "id": c.get("id"),
                               "claim": claim})
            # SWR-V3.16-001: audit_constraint 下的批量裁决建议 (warn 级附项,
            # 主条目阻断语义不变) —— av 批 11 条同构手工降级实录
            constraint = c.get("audit_constraint")
            if constraint:
                violations.append({
                    "gate": "empirical_required_constraint", "severity": "warn",
                    "id": c.get("id"), "constraint": constraint,
                    "suggestion": {
                        "kind": "batch_demote",
                        "reason_template": (
                            "audit_constraint=" + str(constraint) +
                            ": 实证类 claim 无实测支撑 → 按 v3.3 条款降 "
                            "NEEDS_REVIEW (证据不足/环境受限), 主代理逐条确认"
                            "落盘, 不自动改写")}})
    # v3.10.2 (SWR-V3.10.2-004): 实证保真度提示——等价复现候选分列 (判据不变)
    equivalent_ids = [c.get("id") for c in cands
                      if c.get("verdict") == "REACHABLE"
                      and c.get("evidence_grade") == "empirically_confirmed"
                      and (c.get("empirical") or {}).get("fidelity") == "equivalent"]
    if equivalent_ids:
        violations.append({"gate": "fidelity_hint", "severity": "warn",
                           "ids": equivalent_ids,
                           "note": "等价复现实证 (fidelity=equivalent): 申报材料须标注"
                                   " equivalence, 不得以真实目标实证口径"})
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
    # v3.4.2: 复跑 v3.2 机制发布前的旧队列 (无 resurrection_review 字段
    # 且 R3.5 波不覆盖 UNREACHABLE 方向) 时豁免——P0 三锚点复跑实测;
    # 豁免产出 warn 注记 (不阻断), 不伪造复活记录
    if require_resurrection:
        for c in cands:
            if c.get("verdict") != "UNREACHABLE":
                continue
            # SWR-V3.15-002: 统一 claim 判定函数 (与 resurrect_pool 同源)
            if is_claim_like(c) and not c.get("resurrection_review"):
                violations.append({"gate": "resurrection_required", "id": c.get("id")})
    else:
        violations.append({"gate": "resurrection_exempted", "severity": "warn",
                           "note": "③c 豁免: 旧队列复跑 (require_resurrection=False), "
                                   "队列为 v3.2 复活机制发布前产物, 不伪造复活记录 "
                                   "(同 ⑧ target_kind 豁免先例, v3.4.2)"})
    # v3.3.2 (SWR-V3.3.2-005): 复活改判防漏放——带 re_verify_gap 的候选重验改判
    # REACHABLE 后必须再经 R3.5 独立证伪 (refutation 字段), 否则违规
    # (REQ-V3.2-021 修订: 放行方向强制对抗复核)
    for c in cands:
        if c.get("re_verify_gap") and c.get("verdict") == "REACHABLE" \
           and not c.get("refutation"):
            violations.append({"gate": "post_resurrect_refutation",
                               "id": c.get("id")})

    # ③b v3.3.2 (SWR-V3.3.2-004): R4 findings 实证门禁——结构化判定 + 义务收窄
    # (W6 §18.9 修订): 强制范围 = severity≥Medium 或 claim_type∈forced-claim 类;
    # 接受证据 = confirmed/source_fact/实证; Low 额外接受机制级;
    # 旧格式 (无 claim_type 字段) 的关键词匹配降为 fallback warn
    for f in r4:
        # gate ③b 只约束 confirmed 假说的 findings——reviewed_clean 的
        # 正向确认/Info 条目 (如 "verified in-bounds") 不是漏洞声称
        if f.get("verdict") != "confirmed":
            continue
        findings = f.get("findings") or []
        for fi in findings:
            sev = (fi.get("severity") or "").strip().lower()
            ft = (fi.get("claim_type") or "").strip().lower()
            er = (fi.get("empirical_result") or "").strip()
            er_l = er.lower()
            forced = any(k in ft for k in EMPIRICAL_CLAIMS)
            # SWR-V3.4.3-010: 结构判定优先——empirical_result 含实测数字/命令
            # 输出/exit code 特征即视为有实证 (关键词表曾漏 "实测" 致 P2 误报
            # empirical_required_r4); 关键词仅作降级 fallback
            has_structural = bool(re.search(r"\d+", er)) and any(
                k in er_l for k in ("实测", "measured", "test", "复现", "repro",
                                    "exit", "秒", "ms", "mb", "gb", "kb", "ops",
                                    "rss", "pid", "vmhwm"))
            has_confirmed = has_structural or any(
                k in er_l for k in ("confirmed", "source_fact", "source fact",
                                    "实证", "已实证", "实测", "measured"))
            has_mechanism = er and any(k in er_l for k in
                                       ("mechanism", "机制级", "静态", "static"))
            if forced or sev in ("medium", "high", "critical"):
                if sev in ("low",) and has_mechanism:
                    continue  # Low 接受机制级 (义务收窄, W6 §18.9 修订)
                if has_confirmed:
                    continue
                violations.append({"gate": "empirical_required_r4",
                                   "hypothesis": f.get("hypothesis_id"),
                                   "finding": (fi.get("title") or "")[:60],
                                   "severity": sev, "claim_type": ft})
            elif not ft:
                # fallback: 无结构化 claim_type → 关键词扫描仅 warn
                # v3.4.2: evidence 可为旧 schema dict 形态 (lighttpd 复跑
                # 实测), str() 归一化防 TypeError
                text = ((fi.get("title") or "") + " " +
                        str(fi.get("evidence") or "")).lower()
                if any(k in text for k in EMPIRICAL_CLAIMS) and not has_confirmed:
                    violations.append({"gate": "empirical_required_r4_warn",
                                       "severity": "warn",
                                       "hypothesis": f.get("hypothesis_id"),
                                       "finding": (fi.get("title") or "")[:60]})
    # ③d v3.9 (REQ-V3.9-010): R4 confirmed 独立复核——放行方向对抗复核
    # (REQ-V3.2-021 精神) 在 R4 通道的补位: R3.5 证伪不覆盖 R4 confirmed finding,
    # 头部声称无对抗复核即放行 (Pillow 审计 H-1/H-4 实录, 主代理 ad-hoc 兜底
    # 才抓到 H4-1 假阴性陷阱)。判据: confirmed 假说中 High/Medium/Critical 且
    # empirical_result 前缀 CONFIRMED 的 finding 须有 independent_review
    # {by, method, artifacts} 或非空 r3_link (已过 R3.5 通道)。
    if require_r4_independent:
        for f in r4:
            if f.get("verdict") != "confirmed":
                continue
            for fi in f.get("findings") or []:
                sev = (fi.get("severity") or "").strip().lower()
                er = (fi.get("empirical_result") or "").strip()
                ir = fi.get("independent_review")
                has_ir = (isinstance(ir, dict) and any(
                    ir.get(k) for k in ("by", "method", "artifacts")))
                if (sev in ("high", "medium", "critical")
                        and er.upper().startswith("CONFIRMED")
                        and not has_ir
                        and not (isinstance(fi.get("r3_link"), str)
                                 and fi["r3_link"].strip())):
                    violations.append({
                        "gate": "r4_independent_review",
                        "hypothesis": f.get("hypothesis_id"),
                        "finding": (fi.get("title") or "")[:60],
                        "hint": ("需 independent_review {by, method, artifacts} "
                                 "(主代理从零复现/对照实验) 或非空 r3_link")})
    else:
        violations.append({"gate": "r4_independent_exempted", "severity": "warn",
                           "note": "③d 豁免: 旧队列复跑 (require_r4_independent=False), "
                                   "不伪造独立复核记录 (同 ⑧/③c 豁免先例, v3.9)"})
    # ⑦surface 覆盖 (REQ-V3-095)
    if surface_data is not None:
        total = surface_data.get("total", 0)
        tracked_ids = set(surface_data.get("tracked_ids") or [])
        if tracked_ids:
            # v3.2.2 (REQ-V3.2.2-020): mirror_pairs 镜像自动传播——
            # kept-first 多域冲突对中任一 surface 被 tracked, 对端镜像同样视为覆盖
            # (mbedtls 审计: 15 冲突对曾需主代理手写中继覆盖, mirror_pairs 机制化)
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
    # v3.10.2 (SWR-V3.10.2-014): 裁决核验记录 warn——demote 无核验记录提示
    # (放行方向已有复活波兜底, 不阻断; 旧队列复跑以豁免参数关闭)
    if require_adjudication_verify:
        unverified_demotes = []
        for c in cands:
            for cr in c.get("correction_record") or []:
                # v3.19 (SWR-V3.19-001): 双形态 lenient——str 为注记形态
                # (主代理自然写法, V8 审计实录), dict 为 demote 裁决形态
                # (v3.10.2 契约)。str 条目跳过, 不改写任何字段。
                if isinstance(cr, str):
                    continue
                if cr.get("demote_to") and not cr.get("adjudication_verification"):
                    unverified_demotes.append(c.get("id"))
                    break
        if unverified_demotes:
            violations.append({"gate": "adjudication_unverified",
                               "severity": "warn",
                               "ids": unverified_demotes,
                               "note": "主代理 demote 裁决缺 adjudication_verification "
                                       "核验记录 (回源码核实证伪者承重前提主张)"})
    # v3.10.2 (SWR-V3.10.2-015): 补强签收 warn——未签收补强进报告/申报前提示
    if require_strengthen_verify:
        unverified_strengthen = []
        for c in cands:
            if c.get("verdict") != "REACHABLE":
                continue
            ref = c.get("refutation") or {}
            has_str = bool(ref.get("strengthened") or ref.get("attribution_correction")
                           or ref.get("attribution_corrections"))
            signed = bool(ref.get("strengthened_verified_by")
                          or ref.get("attribution_correction_verified_by"))
            if has_str and not signed:
                unverified_strengthen.append(c.get("id"))
        if unverified_strengthen:
            violations.append({"gate": "strengthen_unverified",
                               "severity": "warn",
                               "ids": unverified_strengthen,
                               "note": "补强/归因修正未签收: 需在候选级 refutation dict 内"
                                       "(与 strengthened[] 平级, 非 entry 内部) 写 "
                                       "strengthened_verified_by / attribution_correction_verified_by "
                                       "=主代理签收标识; 进报告/申报材料前需主代理逐条复核"})
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
    # v3.4.2: (?<!\.) 负向断言——文件行号引用 "codec.rs:89" 曾被误当
    # key:value 赋值 (P0 actix 复跑: key="rs" 89≠53 假冲突)
    # v3.8 (SWR-V3.8-011, zookeeper 审计修正回填): 原 (?<!\.) 只挡"紧跟点号"的起点,
    # 正则会从扩展名内部再起匹配 —— "Provider.java:37" 中 java 被挡后从 "ava" 起
    # 匹配成功, 产出 key="ava" value=行号的系统性伪冲突。改用 (?<![\w.]):
    # 起点前既不能是点也不能是词字符, 扩展名内部起点一并封死。
    assign_re = re.compile(
        r"(?<![\w.])([a-z_][a-z0-9_]*)\s*[=:]\s*(true|false|\"[^\"]{1,40}\"|\d+)")
    # key + 可选镜头词 + 可选赋值符 + value ("tls_enable 零值 false" 形态)
    gap_val_re = re.compile(
        r"(?<![\w.])([a-z_][a-z0-9_]*)\s*(?:零值|默认|缺省)\s*[=:]?\s*"
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
                # v3.4.1: 单字母键 (代码片段/变量名噪音) 不计入 committed 侧
                if len(m.group(1)) < 2:
                    continue
                h7_committed.setdefault(m.group(1), []).append((m.group(2), text[:120]))
            # 形态2: key 出现后 50 字符内的 (配置|仓库|shipped|...)=value 零回指
            # ("tls_enable 代码零值=false（明文），仓库配置=true", W6 §25.4 真实形态)
            for m in re.finditer(r"(?<!\.)([a-z_][a-z0-9_]+)", text):
                tail = text[m.end(): m.end() + 50]
                cm = commit_ctx_re.search(tail)
                if cm:
                    h7_committed.setdefault(m.group(1), []).append((cm.group(1), text[:120]))
    # SWR-V3.3.2-006: 结构化输入——v3.3.2 收缩后的 H7 default_value_table
    # (list 形态, 每行 {name, default, ...}) 直接作为 committed 侧证据源,
    # 不再依赖 findings 散文正则提取
    for h in h7:
        tbl = h.get("default_value_table")
        if not isinstance(tbl, list):
            continue
        for row in tbl:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            val = row.get("default")
            if name is None or val is None:
                continue
            h7_committed.setdefault(str(name), []).append(
                (str(val), json.dumps(row, ensure_ascii=False)[:120]))
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
            if len(key) < 2 or key not in h7_committed or (key, cand_val) in seen:
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
