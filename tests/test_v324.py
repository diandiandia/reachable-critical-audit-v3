#!/usr/bin/env python3
"""SWR-V3.24: 三引擎全景召回评估驱动缺陷修复测试 (8 用例)。

覆盖: H4 site-isolation/资源归因检查点 (D-1) / JIT 根因归属条款 (D-2) /
边界声明补 UI+移动两族 (D-3) / 召回率回归集扩 L0b/L0d/L0c (D-4) /
equivalent 档 real-target 抽验提示 (D-5) / 提示级形态反面分支 /
去项目化扫描 / 版本链。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import workflow_export as we

SKILL = open(os.path.join(ROOT, "SKILL.md")).read()
SURFACE_TMPL = open(os.path.join(ROOT, "task_templates", "surface_map_domain.md")).read()
BIZ_TMPL = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "recall_regression_set.json")

PROJECT_TOKENS = ("v8", "WebKit", "firefox", "Chrome", "CAND-")


def _line_with(text, needle):
    return [l for l in text.splitlines() if needle in l]


# ---- SWR-V3.24-001: H4 site-isolation/资源归因检查点 ----

def test_h4_site_isolation_checkpoint():
    line = _line_with(BIZ_TMPL, "site-isolation/资源归因")
    assert line, "H4 缺 site-isolation 子条"
    line = line[0]
    assert "资源归因" in line and "origin" in line
    assert "SWR-V3.24-001" in line
    for tok in PROJECT_TOKENS:
        assert tok not in line, f"site-isolation 子条含项目 token: {tok}"
    # 提示级: 无义务词
    for w in ("强制", "必须"):
        assert w not in line


# ---- SWR-V3.24-002: JIT 根因归属条款 ----

def test_jit_attribution_clause():
    line = _line_with(SURFACE_TMPL, "根因归属条款")
    assert line, "JIT 轴段缺归属条款"
    line = line[0]
    assert "归属未知" in line and "[ambig]" in line
    assert "CWE-843 映射仅适用于归属成立的候选" in line
    assert "SWR-V3.24-002" in line
    for tok in PROJECT_TOKENS:
        assert tok not in line, f"归属条款含项目 token: {tok}"
    for w in ("强制", "必须"):
        assert w not in line


# ---- SWR-V3.24-003: 边界声明补两族 ----

def test_boundary_declaration_extended():
    assert "（d）UI 信任指示层" in SKILL
    assert "（e）移动端平台集成层" in SKILL
    assert "UI 信任逻辑非代码缺陷" in SKILL
    # 提示级形态保留
    assert "缺失 = warn 注记不阻断" in SKILL


# ---- SWR-V3.24-004: 召回率回归集扩三类 ----

def test_recall_fixture_extended():
    d = json.load(open(FIXTURE))
    entries = d["entries"]
    assert len(entries) >= 4, f"fixture 应含 4+ 条目, 实为 {len(entries)}"
    by_id = {e["id"]: e for e in entries}
    assert "RECALL-001" in by_id  # 既有样本未动
    for eid, cwe_need, fam in (("RECALL-002", "CWE-416", "MEMORY-SAFETY"),
                               ("RECALL-003", "CWE-863", "TRUST-BOUNDARY"),
                               ("RECALL-004", "CWE-787", "MEMORY-SAFETY")):
        e = by_id[eid]
        assert cwe_need in e["cwe"], eid
        assert e["family"] == fam, eid
        for k in ("defect_class", "profile_signals",
                  "expected_hypothesis", "case_source"):
            assert k in e and e[k], f"{eid} 缺字段 {k}"
        # 去项目化: 除 case_source 外零项目 token
        for k, v in e.items():
            if k == "case_source":
                continue
            s = json.dumps(v, ensure_ascii=False)
            for tok in PROJECT_TOKENS:
                assert tok.lower() not in s.lower(), f"{eid}.{k} 含项目 token: {tok}"


def test_recall_fixture_not_referenced_by_task_templates():
    for fname in ("task_templates/biz_hypothesis.md",
                  "task_templates/surface_map_domain.md"):
        fp = os.path.join(ROOT, fname)
        assert "recall_regression_set" not in open(fp).read(), fname


# ---- SWR-V3.24-005: equivalent 档 real-target 抽验提示 ----

def test_equivalent_spotcheck_hint():
    line = _line_with(SKILL, "equivalent 档结论强度低于 real_target")
    assert line, "R5 保真段缺抽验提示句"
    line = line[0]
    assert "抽验" in line and "提示级" in line
    assert "不强制不阻断" in line  # 提示级语义
    assert "必须" not in line
    for tok in PROJECT_TOKENS:
        assert tok not in line, f"抽验提示句含项目 token: {tok}"


# ---- 版本链 ----

def test_tooling_version_324():
    assert we.TOOLING_VERSION == "3.26"
