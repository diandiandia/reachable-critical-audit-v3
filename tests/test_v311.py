#!/usr/bin/env python3
"""SWR-V3.11: Android 系审计设计缺陷修复测试。

覆盖: attacker_tier 枚举与推导/报告标注、契约库 source 必填与去项目化与三层
注入、模板产物面指引、运行时版本检查项、H4 时序子项、镜像提示（语义域约束）、
构建差异声明、旧队列兼容。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import surface_mapper as sm
import workflow_export as we


def _mk_ar(tmp_path, files):
    repo = str(tmp_path)
    ar = os.path.join(repo, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for f, body in files.items():
        p = os.path.join(ar, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(body, str):
            with open(p, "w") as fh:
                fh.write(body)
        else:
            with open(p, "w") as fh:
                json.dump(body, fh)
    return repo


# ---- SWR-V3.11-001/002: attacker_tier 枚举与推导 ----

def test_attacker_tier_enum_and_derive():
    # 显式合法值
    assert bv._derive_attacker_tier(
        {"attacker_tier": "remote", "reachability_type": "DIRECT"},
        {"id": "x"}) == "remote"
    # 非法值回退推导
    assert bv._derive_attacker_tier(
        {"attacker_tier": "bogus", "reachability_type": "DIRECT"},
        {"id": "x"}) == "same_process"
    # DIRECT → same_process
    assert bv._derive_attacker_tier(
        {"reachability_type": "DIRECT", "evidence": "任意"}, {"id": "x"}) == "same_process"
    # ACROSS_BOUNDARY + 平台组件注入信号 → same_device_cross_app
    assert bv._derive_attacker_tier(
        {"reachability_type": "ACROSS_BOUNDARY",
         "evidence": "经导出组件与 intent 参数注入"}, {"id": "x"}) == "same_device_cross_app"
    # ACROSS_BOUNDARY + 网络内容信号 → remote
    assert bv._derive_attacker_tier(
        {"reachability_type": "ACROSS_BOUNDARY",
         "evidence": "远程 HTTP 响应字节"}, {"id": "x"}) == "remote"
    # 无法判定 → None (主代理裁决, 不机械兜底)
    assert bv._derive_attacker_tier(
        {"reachability_type": "ACROSS_BOUNDARY", "evidence": "不明"},
        {"id": "x"}) is None


def test_attacker_tier_render_suffix():
    c = {"id": "CAND-001", "verdict": "REACHABLE", "attacker_tier": "remote"}
    assert bv._tier_suffix(c) == " [tier: remote]"
    c2 = {"id": "CAND-002", "verdict": "REACHABLE", "attacker_tier": "same_process"}
    assert bv._tier_suffix(c2) == ""
    c3 = {"id": "CAND-003", "verdict": "NEEDS_REVIEW", "attacker_tier": "remote"}
    assert bv._tier_suffix(c3) == ""


# ---- SWR-V3.11-004/005: 契约库 schema 与去项目化 ----

def test_contracts_source_required():
    import checklist_binder as cb
    lib = cb.load_library()
    contracts = lib.get("platform_api_contracts", [])
    assert len(contracts) >= 4
    for c in contracts:
        assert (c.get("source") or "").strip(), f"{c.get('id')} 缺 source"


def test_contracts_deproject():
    import checklist_binder as cb
    lib = cb.load_library()
    blob = json.dumps(lib.get("platform_api_contracts", []), ensure_ascii=False).lower()
    for banned in ("flutter", "androidx", "media3", "aomenc", "vpxenc", "gson"):
        assert banned not in blob


def test_contracts_zero_injection_on_no_platform():
    import checklist_binder as cb
    assert cb.platform_api_contracts([]) == []
    assert cb.platform_api_contracts(["web"]) == []  # 首版条目仅 mobile


# ---- SWR-V3.11-006: 三层注入 ----

def test_contracts_injection_three_layers():
    # verify/resurrect 脚本模板引用契约注入的代码路径 (prompt 注入在 export 时执行)
    src = open(os.path.join(ROOT, "workflow_export.py")).read()
    assert "platform_api_contracts" in src
    # refuter 视角 1 含契约对照条款
    assert "平台 API 行为契约" in src


# ---- SWR-V3.11-007/008: 模板产物面 ----

def test_template_artifact_clause():
    tpl = open(os.path.join(ROOT, "task_templates",
                            "surface_map_domain.md")).read()
    assert "生成器/模板产物面指引" in tpl and "instantiated_artifact" in tpl
    # verifier 步骤 0.5 条款
    src = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    assert "模板产物存在性" in src and "SWR-V3.11-008" in src


# ---- SWR-V3.11-011: 运行时版本条件项 ----

def test_runtime_version_clause():
    src = open(os.path.join(ROOT, "tools", "batch_verify.py")).read()
    assert "运行时版本条件" in src and "受影响" in src


# ---- SWR-V3.11-012: H4 时序子项 ----

def test_h4_timing_subitem():
    tpl = open(os.path.join(ROOT, "task_templates", "biz_hypothesis.md")).read()
    assert "初始化时序注入面" in tpl
    skill = open(os.path.join(ROOT, "SKILL.md")).read()
    assert "初始化时序注入面 v3.11" in skill


# ---- SWR-V3.11-013: 镜像提示 (语义域约束) ----

def _surf(sid, lang, name, taints):
    return {"id": sid, "type": "data", "name": name, "lang": lang,
            "entry_points": [{"file": f"{sid}.c", "line": 1}],
            "taint_channels": taints,
            "trust_boundary": {"type": "host_api"}, "confidence": "high"}


def test_mirror_candidates_same_domain_only(tmp_path):
    repo = _mk_ar(tmp_path, {})
    f = os.path.join(repo, "_r1_a.json")
    # message 域 codec 族 (跨语言) + image 域 (不同语义, 不得与 message 族配对)
    surfaces = [
        _surf("S-1", "dart", "StandardMessageCodec decode", ["插件消息字节"]),
        _surf("S-2", "java", "StandardMessageCodec readBytes", ["插件消息通道"]),
        _surf("S-3", "cpp", "Image codec decode frame", ["图像帧字节"]),
    ]
    json.dump({"surfaces": surfaces}, open(f, "w"))
    merged = sm.merge_surfaces([f], repo)
    mc = merged.get("mirror_candidates", [])
    assert ["S-1", "S-2"] in mc, "同域跨语言镜像族应命中"
    assert ["S-1", "S-3"] not in mc, "跨语义域不得配对"
    assert ["S-2", "S-3"] not in mc


def test_mirror_candidates_single_lang_none(tmp_path):
    repo = _mk_ar(tmp_path, {})
    f = os.path.join(repo, "_r1_a.json")
    surfaces = [
        _surf("S-1", "cpp", "Codec decode", ["消息"]),
        _surf("S-2", "cpp", "Codec encode", ["消息"]),
    ]
    json.dump({"surfaces": surfaces}, open(f, "w"))
    merged = sm.merge_surfaces([f], repo)
    assert not merged.get("mirror_candidates"), "单语言仓库不得输出镜像提示"


# ---- SWR-V3.11-009: 构建差异声明 ----

def test_scope_build_divergence(tmp_path):
    repo = _mk_ar(tmp_path, {})
    # 构建清单在项目根 (非 .audit_results 下)
    with open(os.path.join(repo, "DEPS"), "w") as fh:
        fh.write("deps = {\n  'src/third_party/missing_dep': 'https://x',\n}\n")
    snap = sm.scope_snapshot(repo)
    div = snap.get("build_divergence")
    assert div and div[0]["manifest"] == "DEPS"
    assert "src" in div[0].get("missing_or_empty", [])


# ---- SWR-V3.11-016: 旧队列兼容 ----

def test_old_queue_no_attacker_tier(tmp_path):
    repo = _mk_ar(tmp_path, {})
    # v3.10.2 形态: 无 attacker_tier 字段 → 推导不得抛异常
    v = {"reachability_type": "DIRECT", "evidence": "x", "verdict": "REACHABLE"}
    tier = bv._derive_attacker_tier(v, {"id": "CAND-001"})
    assert tier == "same_process"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
