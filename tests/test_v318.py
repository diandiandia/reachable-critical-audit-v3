#!/usr/bin/env python3
"""SWR-V3.18: 语言问题矩阵 per-language 知识基座测试 (8 用例)。

覆盖: schema 合法 / langs、families 与账本逐位一致 / 种格全字段 +
pending 零注入 / cells_for 别名归一与未知语言 / stats 形态 / CLI 两命令 /
种格正文去项目化 / SKILL.md 条款存在 / TOOLING 3.18。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import language_issue_matrix as lim


def _ledger():
    return json.load(open(os.path.join(ROOT, "resources",
                                       "issue_coverage_matrix.json")))


def _matrix():
    return json.load(open(os.path.join(ROOT, "resources",
                                       "language_issue_matrix.json")))


# ---- SWR-V3.18-001: 矩阵数据 ----


def test_matrix_schema_valid():
    m = _matrix()
    assert set(m["langs"]) == set(_ledger()["langs"]), "langs 与账本不一致"
    assert set(m["families"]) == set(_ledger()["families"]), "families 与账本不一致"
    assert len(m["langs"]) == 16 and len(m["families"]) == 12
    for c in m["cells"]:
        assert c.get("status") == "seeded"
        assert c["lang"] in m["langs"] and c["family"] in m["families"]
        for k in ("cwes", "patterns", "sinks", "pitfalls", "source_lessons"):
            assert c.get(k), f"{c['lang']}x{c['family']} 缺字段 {k}"
        # 种格 CWE 必须属于其族 (账本 fam_map 校验——种格诚实纪律的机械面)
        fam_cwes = set(_ledger()["families"][c["family"]]["cwe"])
        for cw in c["cwes"]:
            n = int(cw.split("-")[1])
            assert n in fam_cwes, f"{c['lang']}x{c['family']} 的 {cw} 不在族 cwe 清单"


def test_matrix_no_duplicate_cells():
    m = _matrix()
    keys = [(c["lang"], c["family"]) for c in m["cells"]]
    assert len(keys) == len(set(keys)), "重复种格"


def test_matrix_seeded_deprojected():
    """种格正文 (patterns/sinks/pitfalls) DEPROJECT_BLACKLIST 零命中——
    项目归属只允许在 source_lessons (追溯字段)。"""
    from signature_lib import DEPROJECT_BLACKLIST
    for c in _matrix()["cells"]:
        blob = json.dumps({"patterns": c["patterns"], "sinks": c["sinks"],
                           "pitfalls": c["pitfalls"]}, ensure_ascii=False)
        for tok in DEPROJECT_BLACKLIST:
            assert tok not in blob, \
                f"{c['lang']}x{c['family']} 正文含项目 token: {tok}"


# ---- SWR-V3.18-002: 加载器与消费契约 ----


def test_cells_for_seeded_only_and_alias():
    # 种格返回; pending 格 (如 csharp x RACE) 零注入
    assert lim.cells_for("csharp", "INJECTION")
    assert lim.cells_for("csharp", "RACE") == []
    # 别名归一: cs→csharp, ts→javascript (与 _LANG_ALIAS 同规则)
    assert [c["lang"] for c in lim.cells_for("cs", "AUTHN")] == ["csharp"]
    assert lim.cells_for("ts", "RESOURCE-DOS")
    # 未知语言零注入
    assert lim.cells_for("lua") == []
    assert lim.cells_for("") == []


def test_stats_shape():
    s = lim.stats()
    assert s["total_cells"] == 192
    assert s["seeded"] >= 32 and s["seeded"] + s["pending"] == 192
    assert set(s["per_lang"]) == set(_ledger()["langs"])
    assert set(s["per_family"]) == set(_ledger()["families"])
    # 每语言至少 1 种格 (首版种格判据)
    assert all(n >= 1 for n in s["per_lang"].values())


def test_cli_cells_and_stats():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "language_issue_matrix.py"),
                        "stats"], capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)["total_cells"] == 192
    r2 = subprocess.run([sys.executable, os.path.join(ROOT, "language_issue_matrix.py"),
                         "cells", "go", "RESOURCE-DOS"], capture_output=True, text=True)
    assert r2.returncode == 0
    cells = json.loads(r2.stdout)
    assert cells and all(c["family"] == "RESOURCE-DOS" for c in cells)
    r3 = subprocess.run([sys.executable, os.path.join(ROOT, "language_issue_matrix.py"),
                         "cells"], capture_output=True, text=True)
    assert r3.returncode == 2  # 缺 lang usage


# ---- SWR-V3.18-003: SKILL.md 条款 ----


def test_skillmd_clauses():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "language_issue_matrix.py cells" in skill  # R2 提示条款
    assert "语言问题矩阵" in skill and "回填" in skill  # 增量段/回填纪律
    assert "v3.18 增量" in skill


# ---- 版本链 ----


def test_tooling_version_318():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "workflow_export", os.path.join(ROOT, "workflow_export.py"))
    we = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(we)
    assert we.TOOLING_VERSION == "3.18"
