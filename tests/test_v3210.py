#!/usr/bin/env python3
"""SWR-V3.21: WebKit 审计复盘第二批次缺陷修复测试 (7 用例)。

覆盖: recorder 渲染无悬空"待回填"/无 W6 指向 + 审计轨迹语义保留 (D-3a) /
SKILL.md 探针→可行性路由条款 (D-1) / R1 谓词矛盾扫描条款 (D-2) /
lessons 蒸馏同周期绑定 (D-3b) / skill-optimizer DDL 条款 (D-3c) /
新条款段零项目名 / TOOLING 3.21。

文件名 v3210: 规避与 v3.2.1 套件 tests/test_v321.py 的命名冲突（该文件自
v3.5.2 起承载 SWR-V3.2.1-080/081 测试，2026-09-03 v3.21 开发期曾误覆盖，
已从 HEAD 恢复）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import lessons_recorder as lr
import workflow_export as we


def _render(tmp_path):
    """最小项目渲染 recorder 文档。"""
    d = tmp_path / "proj"
    (d / ".audit_results").mkdir(parents=True)
    import json
    (d / ".audit_results" / "verify_queue.json").write_text(
        json.dumps({"candidates": []}), encoding="utf-8")
    body, data = lr.render(str(d))
    return body


# ---- SWR-V3.21-003①: recorder 渲染 ----


def test_recorder_no_dangling_backfill(tmp_path):
    body = _render(tmp_path)
    assert "待回填" not in body
    assert "W6_MORE_LANGS_FINDINGS" not in body
    assert "唯一读入口" in body
    assert "审计轨迹" in body  # 低价值条目保留路径语义不消失
    assert "不承载待办" in body
    assert "<project>/.audit_results/lessons.md" in body


# ---- SWR-V3.21-001: 探针→可行性路由 ----


def test_skillmd_feasibility_routing():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "探针→可行性路由前移" in skill
    assert "empirical_feasibility" in skill
    assert "real-target /" in skill and "equivalent-harness" in skill
    assert "决策权在用户，主代理不得代选" in skill
    assert "static-only 轨候选的证伪票价值" in skill
    assert "笔记级产物" in skill


# ---- SWR-V3.21-002: R1 谓词矛盾扫描 ----


def test_skillmd_contradiction_scan():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "R1 谓词矛盾扫描" in skill
    assert "contradiction record" in skill
    assert "拒绝|拦截|白名单|过滤|仅允许|不允许|禁止" in skill
    assert "语义判定由主代理裁决，不做自动改写" in skill
    assert "反向测绘" in skill  # 换行处断词容忍


# ---- SWR-V3.21-003②: 蒸馏同周期绑定 ----


def test_skillmd_lessons_binding():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "蒸馏与收官同周期绑定" in skill
    assert "禁止留下悬空" in skill
    assert "只作机械证据、不承载待办" in skill


# ---- SWR-V3.21-003③: skill-optimizer DDL ----


def test_skill_optimizer_ddl_clause():
    # $HOME 探测（禁硬编码绝对路径——纪律 #8 对本 skill 自身同样适用）
    so_path = os.path.join(os.path.expanduser("~"), ".claude", "skills",
                           "skill-optimizer", "SKILL.md")
    assert os.path.exists(so_path), f"skill-optimizer SKILL.md 不存在: {so_path}"
    so = open(so_path).read()
    assert "DDL 消化条款" in so
    assert "本次启动" in so
    assert "显式裁除" in so
    assert "不得静默跳过" in so


# ---- 反面分支: 新条款段零项目名 ----


def test_new_clauses_deprojected():
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    # 只取两个新条款段落本体（不含版本历史段——历史段有项目名是追溯惯例）
    seg1 = skill[skill.index("探针→可行性路由前移"):skill.index("不进队列") + 4]
    seg2 = skill[skill.index("R1 谓词矛盾扫描"):skill.index("不做自动改写") + 6]
    seg3 = skill[skill.index("蒸馏与收官同周期绑定"):skill.index("待回填\"") + 4]
    for tok in ("WebKit", "CAND-019", "CAND-0"):
        for seg in (seg1, seg2, seg3):
            assert tok not in seg, f"新条款段含项目 token: {tok}"


# ---- 版本链 ----


def test_tooling_version_321():
    assert we.TOOLING_VERSION == "3.21"
