#!/usr/bin/env python3
"""SWR-V3.23: real-target 验证轮 + CVE-2026-85046 召回复盘缺陷修复测试 (8 用例)。

覆盖: fidelity 所有权模型核实条款 (D-1) / 发现包络边界声明 (D-2) /
JIT 假设族 + CWE-843 入表 + profile jit 信号 (D-3) / differential 发现通道 (D-4) /
召回率回归集 fixture (D-5) / R4 注入 R2 进行中结论 (D-6) /
修法形态纪律反面分支 / 去项目化守卫。"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import target_profile as tp
import workflow_export as we

SKILL = open(os.path.join(ROOT, "SKILL.md")).read()
SURFACE_TMPL = open(os.path.join(ROOT, "task_templates", "surface_map_domain.md")).read()
BIZ_TMPL = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
DIFF_PY = open(os.path.join(ROOT, "templates", "harness", "differential_probe.py")).read()


# ---- SWR-V3.23-001: fidelity 所有权模型核实 ----

def test_skillmd_fidelity_ownership_check():
    assert "所有权模型核实" in SKILL
    assert "引用持有图" in SKILL
    assert "无法映射" in SKILL and "不得作为缺陷前提" in SKILL
    # 修法形态纪律: 无新门禁名、无自动改写
    assert "自动改写" not in SKILL[SKILL.index("所有权模型核实") - 200:
                                   SKILL.index("所有权模型核实") + 600]


# ---- SWR-V3.23-002: 发现包络边界声明 ----

def test_skillmd_boundary_declaration():
    assert "发现包络边界声明" in SKILL
    assert "JIT/编译器优化正确性层" in SKILL
    assert "闭源依赖内部" in SKILL
    assert "非目标平台变体" in SKILL
    # 提示级: warn 注记不阻断
    assert "warn 注记不阻断" in SKILL


# ---- SWR-V3.23-003: JIT 假设族 + CWE-843 + profile jit 信号 ----

def test_severity_table_has_843():
    assert "787/125/416/415/476/190/129/843" in SKILL


def test_surface_template_jit_axis():
    assert "JIT 优化正确性层轴测绘段" in SURFACE_TMPL
    assert "generation_layers 含 jit 时注入" in SURFACE_TMPL
    assert "CWE-843" in SURFACE_TMPL
    # 零项目名 (maglev/turbofan 为通用技术名, 允许)
    seg = SURFACE_TMPL[SURFACE_TMPL.index("JIT 优化正确性层轴测绘段"):]
    for tok in ("v8", "CAND-", "firefox", "WebKit"):
        assert tok not in seg.split("组件约束段")[0], f"JIT 轴段含项目 token: {tok}"


def test_target_profile_jit_signal():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "src", "compiler", "maglev"))
    open(os.path.join(d, "x.cc"), "w").write("int x;")
    r = tp.recommend(d)
    recs = " ".join(str(s.get("recommends", "")) for s in r.get("signals", []))
    assert "generation_layers+jit" in recs
    # 无反例: 无 jit 目录时不建议 jit
    d2 = tempfile.mkdtemp()
    open(os.path.join(d2, "y.py"), "w").write("x = 1")
    r2 = tp.recommend(d2)
    recs2 = " ".join(str(s.get("recommends", "")) for s in r2.get("signals", []))
    assert "generation_layers+jit" not in recs2


# ---- SWR-V3.23-004: differential 发现通道 ----

def test_differential_discovery_channel():
    assert "differential 发现通道" in SKILL or "differential 发现" in SKILL
    assert "generation_layers 含 jit" in SKILL
    assert "提示级" in SKILL
    assert "SWR-V3.23-004" in DIFF_PY
    assert "R2 发现通道" in DIFF_PY


# ---- SWR-V3.23-005: 召回率回归集 fixture ----

def test_recall_regression_fixture():
    p = os.path.join(ROOT, "tests", "fixtures", "recall_regression_set.json")
    d = json.load(open(p))
    e = d["entries"][0]
    assert e["id"] == "RECALL-001"
    for k in ("defect_class", "family", "cwe", "profile_signals",
              "expected_hypothesis", "case_source"):
        assert k in e
    assert "CWE-843" in e["cwe"]
    # 第一原则守卫: 运行时路径不得引用该 fixture
    for fname in ("workflow_export.py", "tools/batch_verify.py",
                  "tools/target_profile.py", "surface_mapper.py"):
        fp = os.path.join(ROOT, fname)
        if os.path.exists(fp):
            assert "recall_regression_set" not in open(fp).read(), fname


# ---- SWR-V3.23-006: R4 注入 R2 进行中结论 ----

def test_r4_taskbook_r2_injection():
    assert "R2 进行中结论注入" in BIZ_TMPL
    assert "keep/drop 条目" in BIZ_TMPL
    assert "R2 未出结论" in BIZ_TMPL
    # 零项目名
    for tok in ("WebKit", "v8", "CAND-"):
        assert tok not in BIZ_TMPL[BIZ_TMPL.index("R2 进行中结论注入"):]


# ---- 版本链 ----

def test_tooling_version_323():
    assert we.TOOLING_VERSION == "3.31"
