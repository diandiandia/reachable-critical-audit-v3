"""SWR-V3.29: 闭环接线测试。
控制器 goal priority (K2 误差信号) / 反馈 hitrate / seed 双写一致性 /
Top25 试点种格数据完整性 (K1 16/16) / R2+R6 条款 / 版本链登记。
"""

import json
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))

import language_issue_matrix as lim

INV = json.load(open(os.path.join(WORKSPACE, "assets", "resources",
                                  "language_issue_inventory.json")))
MATRIX = json.load(open(os.path.join(WORKSPACE, "assets", "resources",
                                    "language_issue_matrix.json")))


# ---- SWR-V3.29-001: 控制器 priority ----

def test_goal_priority_sorted_and_k2_first():
    g = lim.goal_progress()
    p = g["priority"]
    rows = p["per_lang_sorted_by_gap"]
    assert rows[0]["battle_gap"] >= rows[-1]["battle_gap"], "K2 gap 未降序"
    assert len(p["top_gap_languages"]) == 3
    # K1 已达标 → gap_to_target 全 0, 误差信号由 battle_gap 承载
    assert all(r["gap_to_target"] == 0 for r in rows)


def test_goal_k1_reached_k2_honest():
    g = lim.goal_progress()
    assert g["milestones"]["K1"]["progress"] == "16/16"
    assert g["milestones"]["K2"]["progress"] == "0/16"
    assert g["totals"]["entries"] == 199
    assert g["totals"]["battle_confirmed"] == 9


# ---- SWR-V3.29-002: hitrate ----

def test_hitrate_math():
    h = lim.hitrate("c", ["CWE-770", "CWE-787", "CWE-999"])
    assert h["queried"] == 3
    assert h["hit_entries"] >= 3
    assert "770" in h["hits"][0]["cwe"][0] or "787" in h["hits"][0]["cwe"][0]
    ids = [x["id"] for x in h["hits"]]
    assert "INV-c-005" in ids or "INV-c-003" in ids


def test_hitrate_unknown_lang():
    h = lim.hitrate("brainfuck", ["CWE-770"])
    assert h["queried"] == 1 and h["hit_entries"] == 0 and h["hits"] == []


# ---- SWR-V3.29-003: seed 双写一致性 ----

def test_seed_doublewrite_consistency():
    """inventory 每条目 (lang,family,pattern) 必须在矩阵对应格 patterns 中。"""
    cells = {}
    for c in MATRIX["cells"]:
        cells.setdefault((c["lang"], c["family"]), set()).update(c.get("patterns", []))
    for e in INV["entries"]:
        key = (e["lang"], e["family"])
        assert key in cells, f"{e['id']} 的 (lang,family) 无矩阵格"
        assert e["pattern"] in cells[key], f"{e['id']} pattern 未双写进矩阵"


def test_matrix_cells_grew_by_seed():
    seeded = [c for c in MATRIX["cells"] if c.get("status") == "seeded"]
    assert len(seeded) >= 34, "双写后矩阵格不应少于派生基线"


# ---- SWR-V3.29-004: Top25 试点种格数据 ----

def test_top25_entries_origin_and_tier():
    ext = [e for e in INV["entries"]
           if e["source"]["tier"] == "external_seeded"]
    assert len(ext) == 156
    for e in ext:
        assert "cwe.mitre.org/top25" in e["source"]["origin"], e["id"]
        assert e["source"]["date"] == "2026-09-08"
        assert e["verify"]["status"] == "unverified", \
            f"{e['id']} 外部条目不得伪造 battle_confirmed"
        assert e["title"].startswith("CWE-"), e["id"]


def test_top25_entries_deproject():
    body = json.dumps([{k: e.get(k) for k in ("title", "pattern", "pitfall")}
                       for e in INV["entries"]
                       if e["source"]["tier"] == "external_seeded"],
                      ensure_ascii=False).lower()
    for tok in ("quickjs", "sinatra", "mbedtls", "lighttpd", "django"):
        assert tok not in body, f"Top25 条目正文含项目名 {tok}"


# ---- SWR-V3.29-005: SKILL.md 条款 ----

def test_skmd_r2_and_r6_clauses():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    flat = sk.replace("\n", " ")
    assert "inventory <lang>" in flat
    assert "external_seeded" in flat and "只作假设空间提示" in flat
    assert "hitrate <lang>" in flat and "传导度量" in flat


# ---- 版本链登记 ----

def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.38"
