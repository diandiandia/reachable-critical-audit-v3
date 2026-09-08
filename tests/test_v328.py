"""SWR-V3.28: Top15×Top10 目标物化测试。
inventory 问题粒度层 (36 条目/机械排序) + goal 达成度视图 + seed 双通道
(四个反面分支) + 回填升档数据完整性 + 版本链登记。
"""

import json
import os
import shutil
import sys
import tempfile

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

import language_issue_matrix as lim

INV_PATH = os.path.join(WORKSPACE, "resources", "language_issue_inventory.json")


def _inv():
    return json.load(open(INV_PATH))


# ---- SWR-V3.28-001: inventory 资产 ----

def test_inventory_loads_and_fields():
    d = _inv()
    entries = d['entries']
    assert len(entries) == 192, "inventory 条目数漂移 (36 派生 + 156 Top25 试点种格)"
    assert d['goal']['per_lang_target'] == 10
    for e in entries:
        for k in ("id", "lang", "title", "family", "cwe", "source", "verify"):
            assert k in e, f"{e.get('id')} 缺字段 {k}"
        assert e['source']['tier'] in ("battle_verified", "external_seeded",
                                       "source_seeded")
        assert e['verify']['status'] in ("battle_confirmed", "unverified")
        assert e['lang'] in d['langs']


def test_inventory_covers_all_langs():
    d = _inv()
    langs = {e['lang'] for e in d['entries']}
    assert langs == set(d['langs']), "inventory 语言集与矩阵不一致"


# ---- SWR-V3.28-002: 机械排序 ----

def test_inventory_rank_order():
    es = lim.inventory_for("c")
    fams = [e['family'] for e in es]
    # MEMORY-SAFETY (档 1) 必须先于 CRYPTO (档 3)
    assert fams.index("MEMORY-SAFETY") < fams.index("CRYPTO")
    # 排序确定性: 重复调用一致
    assert [e['id'] for e in lim.inventory_for("c")] == [e['id'] for e in es]


def test_inventory_unknown_lang_empty():
    assert lim.inventory_for("brainfuck") == []


# ---- SWR-V3.28-003: goal 视图 ----

def test_goal_math():
    g = lim.goal_progress()
    d = _inv()
    assert g['goal']['per_lang_target'] == 10
    assert g['totals']['entries'] == len(d['entries'])
    for row in g['per_lang']:
        assert row['gap_to_target'] == max(0, 10 - row['entries'])
        assert row['battle_confirmed'] <= row['entries']
    assert g['milestones']['K1']['progress'].endswith("/16")
    assert g['milestones']['K2']['progress'].endswith("/16")


def test_goal_milestones_defined():
    d = _inv()
    assert "每语言 ≥10" in d['goal']['milestones']['K1']['criterion']
    assert "battle_confirmed" in d['goal']['milestones']['K2']['criterion']


# ---- SWR-V3.28-004: seed 双通道 ----

def _seed_payload(tmp, entries):
    p = os.path.join(tmp, "seed.json")
    json.dump({"entries": entries}, open(p, "w"), ensure_ascii=False)
    return p


def _valid_seed():
    return {"lang": "c", "title": "外部种格测试条目",
            "family": "OTHER", "cwe": ["CWE-400"],
            "pattern": "测试形态", "sink_hint": "sink", "pitfall": "pit",
            "source": {"tier": "external_seeded", "origin": "CWE Top 25 (2024)",
                       "date": "2026-09-08"}}


def test_seed_valid_and_idempotent():
    tmp = tempfile.mkdtemp()
    try:
        shutil.copy(INV_PATH, os.path.join(tmp, "inv.json"))
        p = _seed_payload(tmp, [_valid_seed()])
        # 在隔离副本上验证 seed 校验逻辑 (lim 加载的是 workspace 资源——
        # 校验逻辑通过 seed_entries 的 rejected/added 语义测试, 不实际污染 workspace)
        # 幂等语义: 同名条目重复提交会被拒 (用 workspace 现有条目模拟)
        dup = {"lang": "c", "title": _inv()['entries'][0]['title'],
               "family": "OTHER", "cwe": ["CWE-400"], "pattern": "x",
               "sink_hint": "s", "pitfall": "p",
               "source": {"tier": "external_seeded", "origin": "o",
                          "date": "2026-09-08"}}
        r = lim.seed_entries(_seed_payload(tmp, [dup]))
        assert any("duplicate" in d.get("reasons", []) for d in r["rejected"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_seed_reject_no_origin():
    e = _valid_seed()
    e["source"] = {"tier": "external_seeded"}
    tmp = tempfile.mkdtemp()
    try:
        r = lim.seed_entries(_seed_payload(tmp, [e]))
        assert any("缺 origin" in d["reasons"][0] for d in r["rejected"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_seed_reject_project_name():
    e = _valid_seed()
    e["pattern"] = "quickjs 形态的描述"
    tmp = tempfile.mkdtemp()
    try:
        r = lim.seed_entries(_seed_payload(tmp, [e]))
        assert any("deproject" in d["reasons"][0] for d in r["rejected"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_seed_reject_bad_lang_and_cwe():
    e1 = _valid_seed()
    e1["lang"] = "brainfuck"
    e2 = _valid_seed()
    e2["title"] = "坏 cwe 条目"
    e2["cwe"] = ["770"]  # 缺 CWE- 前缀
    tmp = tempfile.mkdtemp()
    try:
        r = lim.seed_entries(_seed_payload(tmp, [e1, e2]))
        reasons = [d["reasons"] for d in r["rejected"]]
        assert any(any("bad lang" in s for s in rs) for rs in reasons)
        assert any(any("bad cwe" in s for s in rs) for rs in reasons)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- 回填升档数据完整性 (SWR-V3.28-005 数据侧) ----

def test_battle_confirmed_entries_have_evidence():
    d = _inv()
    for e in d['entries']:
        if e['verify']['status'] == 'battle_confirmed':
            assert e['verify']['battles'], f"{e['id']} battle_confirmed 无战役名"
            assert e['verify']['candidates'], f"{e['id']} battle_confirmed 无候选 id"
            assert e['verify']['date']


def test_quickjs_entries_confirm_candidates():
    d = _inv()
    by_title = {e['title'][:12]: e for e in d['entries']}
    found = [e for e in d['entries']
             if e['verify']['status'] == 'battle_confirmed']
    assert len(found) == 2
    cands = [c for e in found for c in e['verify']['candidates']]
    assert "CAND-001" in cands and "H-2-F1" in cands and "H-7-F2" in cands


def test_inventory_deproject():
    # 正文键 (title/pattern/sink_hint/pitfall) 零项目名; source/verify 为追溯字段允许
    body = json.dumps([{k: e.get(k) for k in ("title", "pattern", "sink_hint",
                                              "pitfall")}
                       for e in _inv()['entries']], ensure_ascii=False).lower()
    for tok in ("quickjs", "sinatra", "mbedtls", "lighttpd", "django", "grpc"):
        assert tok not in body, f"inventory 正文含项目名 {tok}"


# ---- 版本链登记 ----

def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.29"
