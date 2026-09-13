"""test_v341 — hibernate-orm 验收复盘七缺陷测试守卫 (SWR-V3.41-001..007)。

案例支撑: /root/hibernate-orm/.audit_results/lessons.md「对 skill 的教训」
2026-09-12——复活 gap 渲染 bool 拼接 TypeError / 报告 B.5+B.2 降级文案 /
H-4 非法 claim_type 静默流入 / H2 单方言实测外推致复活翻转 /
comment-hint-format 三通道转义不对称 / CAND-005 逃生舱等价性 / java 矩阵 5/10。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv


def _load_we():
    spec = importlib.util.spec_from_file_location(
        "workflow_export", os.path.join(ROOT, "src", "workflow_export.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


we = _load_we()


# ---------- SWR-V3.41-001: 复活 gap 字段契约分离 ----------

def test_gap_render_uses_resurrect_gap_text():
    """re_verify_gap(True) + resurrect_gap(文本) → prompt 含 gap 文本, 不抛 TypeError。"""
    payload = we.export_script.__globals__
    # 直接构造 export 入参形态: 借 resurrect 导出同款 gap 渲染路径 (verify 分支)
    # 通过模块级函数间接验证: 用临时队列导出 verify 波 (带 re_verify_gap 的 PENDING 候选)
    import tempfile
    tmp = tempfile.mkdtemp()
    ar = os.path.join(tmp, ".audit_results")
    os.makedirs(ar)
    q = {"candidates": [{
        "id": "CAND-999", "status": "PENDING", "source_file": "a.java",
        "source_line": 1, "sink_type": "CWE-89", "attempt": 0,
        "re_verify_gap": True,
        "resurrect_gap": "复活者缺口: 非复合路径绕过 appendLiteral (file:line 证据)",
    }]}
    with open(os.path.join(ar, "verify_queue.json"), "w") as f:
        json.dump(q, f)
    r = we.export_script(tmp, mode="verify", batch_size=1)
    assert r.get("payload"), f"export 失败: {r}"
    prompt = r["payload"][0]["prompt"]
    assert "复活复核 gap" in prompt
    assert "非复合路径绕过 appendLiteral" in prompt, "gap 文本未渲染进 prompt"


def test_gap_render_bool_without_text_no_typeerror():
    """re_verify_gap(True) 且无 resurrect_gap → 不抛 TypeError, 不渲染 gap 文本段。"""
    import tempfile
    tmp = tempfile.mkdtemp()
    ar = os.path.join(tmp, ".audit_results")
    os.makedirs(ar)
    q = {"candidates": [{
        "id": "CAND-998", "status": "PENDING", "source_file": "a.java",
        "source_line": 1, "sink_type": "CWE-89", "attempt": 0,
        "re_verify_gap": True,
    }]}
    with open(os.path.join(ar, "verify_queue.json"), "w") as f:
        json.dump(q, f)
    r = we.export_script(tmp, mode="verify", batch_size=1)
    assert r.get("payload"), f"export 失败 (TypeError 回归?): {r}"
    prompt = r["payload"][0]["prompt"]
    # 段落标题仍渲染 (标志在), 但无 gap 正文拼接 (TypeError 形态的根因)
    assert "复活复核 gap" in prompt


# ---------- SWR-V3.41-002: 报告段 import 路径对齐 ----------

def test_report_import_sites_include_src():
    """两处报告段 sys.path.insert 与其余导入点同形 (根 + src 双插)。"""
    text = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    lines = [l for l in text.splitlines()
             if "sys.path.insert" in l and "os.path.join" in l and "_parent" in l]
    # 其余 5 处 (根+src 双插) + 本修复 2 处 (根+src 双插) 应全为双插形态
    assert len(lines) >= 7, f"双插导入点不足: {len(lines)}"
    src_inserts = [l for l in text.splitlines()
                   if 'os.path.join(_parent, "src")' in l
                   or 'os.path.join(_rep_parent, "src")' in l]
    assert len(src_inserts) >= 7, f"src 插入点不足: {len(src_inserts)}"


# ---------- SWR-V3.41-003: claim_type 枚举告警 ----------

def test_illegal_claim_type_warned(capsys):
    items = [{"hypothesis_id": "H-4", "verdict": "confirmed",
              "findings": [{"title": "t", "severity": "Medium",
                            "claim_type": "source_fact"}]}]
    bv._warn_r4_enums(items)
    err = capsys.readouterr().err
    warnings = [json.loads(l)["warning"] for l in err.splitlines() if l.strip()]
    kinds = {w["kind"] for w in warnings}
    assert "illegal_claim_type" in kinds, f"非法 claim_type 未告警: {err}"
    w = [x for x in warnings if x["kind"] == "illegal_claim_type"][0]
    assert w["suggestion"]["suggested"] == "other"


def test_empty_claim_type_warned(capsys):
    items = [{"hypothesis_id": "H-6", "verdict": "confirmed",
              "findings": [{"title": "t", "severity": "High", "claim_type": ""}]}]
    bv._warn_r4_enums(items)
    err = capsys.readouterr().err
    warnings = [json.loads(l)["warning"] for l in err.splitlines() if l.strip()]
    kinds = {w["kind"] for w in warnings}
    assert "empty_claim_type" in kinds, f"空串 claim_type 未告警: {err}"


def test_legal_claim_types_no_new_warning(capsys):
    """反面分支: 合法枚举零新增告警 (crash/oom/leak/other/null)。"""
    items = [{"hypothesis_id": "H-2", "verdict": "confirmed",
              "findings": [
                  {"title": "a", "severity": "High", "claim_type": "crash"},
                  {"title": "b", "severity": "Medium", "claim_type": "oom"},
                  {"title": "c", "severity": "Low", "claim_type": "leak"},
                  {"title": "d", "severity": "Low", "claim_type": "other"},
                  {"title": "e", "severity": "Low", "claim_type": None},
              ]}]
    bv._warn_r4_enums(items)
    err = capsys.readouterr().err
    warnings = [json.loads(l)["warning"] for l in err.splitlines() if l.strip()]
    kinds = {w["kind"] for w in warnings}
    assert "illegal_claim_type" not in kinds
    assert "empty_claim_type" not in kinds
    assert not warnings, f"合法枚举产生告警: {err}"


# ---------- SWR-V3.41-004: 方言/平台语义矩阵条款 ----------

def test_verify_prompt_contains_dialect_matrix_clause():
    text = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    assert "方言/平台语义矩阵" in text, "任务书步骤 4 缺方言/平台语义矩阵条款"
    assert "单格实测不得外推到语义相异方言族" in text


# ---------- SWR-V3.41-005: checklist +1 ----------

def test_checklist_50_channel_escape_ledger():
    d = json.load(open(os.path.join(
        ROOT, "assets", "resources", "checklist_library.json")))
    items = d["checklists"]
    assert len(items) == 50, f"计数守卫: 期望 50, got {len(items)}"
    c = [x for x in items if x["id"] == "CK-CHANNEL-ESCAPE-LEDGER"]
    assert c, "CK-CHANNEL-ESCAPE-LEDGER 不存在"
    assert c[0]["family"] == "injection"
    assert "source_lessons" in c[0] and c[0]["source_lessons"]


# ---------- SWR-V3.41-006: precedent +1 ----------

def test_precedent_19_escape_hatch_equiv():
    d = json.load(open(os.path.join(
        ROOT, "assets", "resources", "precedent_library.json")))
    items = d["precedents"]
    assert len(items) == 19, f"计数守卫: 期望 19, got {len(items)}"
    c = [x for x in items if x["id"] == "PREC-ESCAPE-HATCH-EQUIV"]
    assert c, "PREC-ESCAPE-HATCH-EQUIV 不存在"
    assert "source_lessons" in c[0] and c[0]["source_lessons"]


# ---------- SWR-V3.41-007: java 矩阵两格 ----------

def test_java_matrix_two_new_cells():
    d = json.load(open(os.path.join(
        ROOT, "assets", "resources", "language_issue_inventory.json")))
    by_id = {e.get("id"): e for e in d["entries"]}
    m = by_id.get("INV-java-013")
    assert m and m["family"] == "MEMORY-SAFETY" and m["lang"] == "java"
    a = by_id.get("INV-java-014")
    assert a and a["family"] == "AUTHN" and a["lang"] == "java"
    for e in (m, a):
        assert e["source"]["tier"] == "source_seeded"
        assert e["source"]["date"] == "2026-09-12"
