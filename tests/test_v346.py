"""test_v3_46 — K6-K9 (linux kernel 批次 6-9) 复盘修复测试 (SWR-V3.46-001..007).

D-1 attacker_tier 句级否定清洗 / D-2 r4 schema 键名归一三形态 / D-3 workflow
taskFile 存在性预检 + r4-collect 重复 --file 报错 / D-4 surface_map config
门核条款 / D-5 零硬件实证通道手册 / D-6 版本滞后告警文案 / D-7 复活抽样规则
注释 (零行为变更)。
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import batch_verify as bv
import workflow_export as we

SKILL = open(os.path.join(ROOT, "SKILL.md")).read()
SURFACE_MAP = open(os.path.join(ROOT, "assets", "task_templates",
                               "surface_map_domain.md")).read()
BIZ = open(os.path.join(ROOT, "assets", "task_templates",
                        "biz_hypothesis.md")).read()
MANUAL = open(os.path.join(ROOT, "assets", "harness_manuals",
                           "kernel_zero_hardware_channels.md")).read()


def _mk_project(files=None, queue=None):
    tmp = tempfile.mkdtemp()
    ar = os.path.join(tmp, ".audit_results")
    os.makedirs(ar, exist_ok=True)
    for rel, content in (files or {}).items():
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content)
    json.dump(queue if queue is not None else {"candidates": []},
              open(os.path.join(ar, "verify_queue.json"), "w"))
    return tmp


# ---- SWR-V3.46-001 (D-1): attacker_tier 句级否定清洗 ----

def test_scan_disclaimer_sentence_not_remote():
    hits, disc = bv._remote_keyword_scan("该通道不是 remote".lower())
    assert hits == 0 and disc is True


def test_scan_disclaimer_variants():
    # K6/K7 实录形态: 非 remote / 不经网络 / 没有网络权限 / not remote
    for ev in ("非 remote 入口", "该面不经网络", "该面没有网络权限",
               "is not remote but local"):
        hits, disc = bv._remote_keyword_scan(ev.lower())
        assert hits == 0 and disc is True, ev


def test_scan_positive_sentence_counts():
    hits, _ = bv._remote_keyword_scan("远程服务器返回数据".lower())
    assert hits > 0


def test_scan_mixed_positive_wins():
    # 免责句 + 正向句并存 → 正向命中仍计 remote (保守方向)
    hits, disc = bv._remote_keyword_scan(
        "该面不经网络，但服务器可访问".lower())
    assert hits > 0 and disc is True


def test_scan_negation_after_keyword_not_exempt():
    # 否定在关键词之后不豁免 (远程服务器没有校验 仍是远程面)
    hits, _ = bv._remote_keyword_scan("远程服务器没有校验长度".lower())
    assert hits > 0


def test_scan_attributive_not_exempt():
    # 属性短语不构成免责 (未经授权的远程访问 是远程面)
    hits, _ = bv._remote_keyword_scan("未经授权的远程访问".lower())
    assert hits > 0


def test_derive_full_disclaimer_none_and_warns(capsys):
    v = {"attacker_tier": "", "reachability_type": "ACROSS_BOUNDARY",
         "evidence": "该通道不是 remote, 经内核共享内存"}
    assert bv._derive_attacker_tier(v, {"id": "CAND-001"}) is None
    err = capsys.readouterr().err
    assert "SWR-V3.46-001" in err and "交主代理裁决" in err


def test_derive_positive_remote():
    v = {"attacker_tier": "", "reachability_type": "ACROSS_BOUNDARY",
         "evidence": "远程数据经服务器解析"}
    assert bv._derive_attacker_tier(v, {"id": "CAND-002"}) == "remote"


def test_derive_direct_unchanged():
    v = {"attacker_tier": "", "reachability_type": "DIRECT",
         "evidence": "不是 remote"}
    assert bv._derive_attacker_tier(v, {"id": "CAND-003"}) == "same_process"


# ---- SWR-V3.46-002 (D-2): r4 schema 键名归一三形态 ----

def test_norm_id_alias():
    raw = {"hypotheses": [{"id": "H1", "verdict": "reviewed_clean",
                           "findings": [], "tracked_surfaces": ["S-1"]}]}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["hypothesis_id"] == "H1" and "id" not in items[0]
    assert "id->hypothesis_id" in flags


def test_norm_hypothesis_desc_interference():
    # K9 (b): 顶层 hypothesis 描述键干扰 → 提取 id + 描述转 note
    raw = {"hypothesis": "H4: 跨进程信任边界破坏",
           "findings": [{"title": "t", "tracked_surfaces": ["S-1"]}]}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["hypothesis_id"] == "H4"
    assert items[0]["hypothesis_note"] == "H4: 跨进程信任边界破坏"
    assert "hypothesis" not in items[0]
    assert "hypothesis-desc->hypothesis_id+note" in flags


def test_norm_tracked_prefix_alias():
    # K9 (c): hypothesis_tracked_surfaces 前缀键不被识别
    raw = {"hypotheses": [{"hypothesis_id": "H6", "verdict": "reviewed_clean",
                           "findings": [],
                           "hypothesis_tracked_surfaces": ["S-2"]}]}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["tracked_surfaces"] == ["S-2"]
    assert "hypothesis_tracked_surfaces->tracked_surfaces" in flags


def test_norm_bare_id_hypothesis_key_untouched():
    # 裸 id 形态 (hypothesis: "H1") 不归一——v3.42 近似键诊断契约拥有该形态
    # (不自动改写), v3.46 只处理描述文本干扰
    raw = {"hypothesis": "H1", "verdict": "confirmed", "findings": []}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0].get("hypothesis") == "H1"
    assert "hypothesis_id" not in items[0]
    assert flags == []


def test_norm_hypothesis_desc_no_id():
    # 描述文本无内嵌 H-N → 转 hypothesis_note (无 id 提取)
    raw = {"hypothesis": "跨进程信任边界描述", "findings": []}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["hypothesis_note"] == "跨进程信任边界描述"
    assert "hypothesis_id" not in items[0]
    assert "hypothesis" not in items[0]
    assert "hypothesis-desc->hypothesis_note" in flags


def test_norm_hypothesis_mismatch_kept():
    # hypothesis_id 已存在且 hypothesis 值不同 → 保守保留 + flag (不猜不删)
    raw = {"hypotheses": {"H2": {"hypothesis": "H3", "verdict": "confirmed",
                                 "findings": [], "tracked_surfaces": ["S-3"]}}}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["hypothesis_id"] == "H2"
    assert items[0]["hypothesis"] == "H3"
    assert "hypothesis-mismatch-kept" in flags


def test_norm_dict_form_dup_dropped():
    raw = {"hypotheses": {"H2": {"hypothesis": "H2", "verdict": "confirmed",
                                 "findings": [], "tracked_surfaces": ["S-3"]}}}
    items, flags = bv._normalize_r4_payload(raw)
    assert items[0]["hypothesis_id"] == "H2" and "hypothesis" not in items[0]
    assert "hypothesis-dup-dropped" in flags


def test_norm_canonical_zero_flags():
    raw = {"hypotheses": [{"hypothesis_id": "H1", "verdict": "confirmed",
                           "findings": [], "tracked_surfaces": ["S-1"]}]}
    items, flags = bv._normalize_r4_payload(raw)
    assert flags == []


def test_norm_flags_warn_printed(capsys):
    # 归一命中在 r4-collect 输出 warn (计数不阻断; R4_TRACKED_MISSING 先拦下
    # 也可以——warn 已打印)
    tmp = _mk_project(files={
        ".audit_results/input_surface.json": json.dumps({"surfaces": []})})
    f = os.path.join(tmp, ".audit_results", "findings.json")
    json.dump({"hypotheses": [{"id": "H1", "verdict": "confirmed",
                               "findings": []}]}, open(f, "w"))
    r = bv.stage_r4_collect(tmp, f)
    assert r == 1  # tracked 缺失原子性阻断
    err = capsys.readouterr().err
    assert "SWR-V3.46-002" in err and "id->hypothesis_id" in err


def test_template_key_contract():
    assert "键名契约（v3.46, SWR-V3.46-002）" in BIZ
    assert "`id` 替代" in BIZ and "`hypothesis_tracked_surfaces` 前缀拼写" in BIZ


# ---- SWR-V3.46-003 (D-3): taskFile 预检 + 重复 --file ----

def test_export_scripts_have_existsync_precheck():
    for name in ("VERIFY_SCRIPT", "REFUTATION_SCRIPT", "RESURRECT_SCRIPT"):
        js = getattr(we, name)
        assert "existsSync" in js, name
        assert "taskFile 不存在" in js, name
        assert "SWR-V3.46-003" in js, name


def test_dup_file_arg_explicit_error(capsys):
    tmp = _mk_project()
    argv = sys.argv
    try:
        sys.argv = ["batch_verify.py", tmp, "--stage", "r4-collect",
                    "--file", "a.json", "--file", "b.json"]
        try:
            bv.main()
            assert False, "重复 --file 应退出"
        except SystemExit as e:
            assert e.code == 1
    finally:
        sys.argv = argv
    err = capsys.readouterr().err
    assert "--file 重复指定" in err and "a.json" in err and "b.json" in err


# ---- SWR-V3.46-004 (D-4): config 门核条款 ----

def test_surface_map_config_gate_clause():
    assert "config 门核条款（v3.46, SWR-V3.46-004）" in SURFACE_MAP
    assert "写 `local` 前必须核对编译面" in SURFACE_MAP


# ---- SWR-V3.46-005 (D-5): 零硬件实证通道手册 ----

def test_zero_hardware_manual_exists_and_complete():
    for h in ("## 1. 纯软件 USB 控制器通道", "## 2. 虚拟 USB 存储控制器通道",
              "## 3. 远程协议模拟控制器通道", "## 4. 用户态 RPC responder 通道"):
        assert h in MANUAL, h
    assert "单变量纪律" in MANUAL and "equivalent" in MANUAL


def test_zero_hardware_manual_deprojected():
    from test_deproject_assets import PROJECT_TOKENS  # 同行守卫黑名单
    low = MANUAL.lower()
    hits = [t for t in PROJECT_TOKENS if t in low]
    assert not hits, f"手册含项目 token: {hits}"


def test_skill_md_points_to_manual():
    assert "kernel_zero_hardware_channels" in SKILL
    assert "SWR-V3.46-005" in SKILL


# ---- SWR-V3.46-006 (D-6): 版本滞后告警文案 ----

def test_version_lag_warning_text():
    tmp = _mk_project(files={
        ".audit_results/workflow_verify.js":
        'tooling_version: "3.45",\n'})
    w = bv._tooling_version_warning(tmp)
    assert w and "仅提示不阻断" in w and "重新导出后可安全运行" in w


def test_version_lag_no_warning_when_matching():
    tmp = _mk_project(files={
        ".audit_results/workflow_verify.js":
        f'tooling_version: "{we.TOOLING_VERSION}",\n'})
    assert bv._tooling_version_warning(tmp) is None


# ---- SWR-V3.46-007 (D-7): 复活抽样规则注释 (零行为变更) ----

def test_resurrect_eligible_unreachable_only():
    tmp = _mk_project(queue={"candidates": [
        {"id": "CAND-1", "status": "VERIFIED", "verdict": "REACHABLE"},
        {"id": "CAND-2", "status": "VERIFIED", "verdict": "UNREACHABLE"},
        {"id": "CAND-3", "status": "VERIFIED", "verdict": "NEEDS_REVIEW"},
        {"id": "CAND-4", "status": "VERIFIED", "verdict": "UNREACHABLE",
         "resurrection_review": {"revived": False}},
    ]})
    we.export_script_resurrect(tmp)
    slim = json.load(open(os.path.join(
        tmp, ".audit_results", "resurrect_payload_slim.json")))
    ids = [c["id"] for c in slim]
    assert ids == ["CAND-2"], ids
    assert "SWR-V3.46-007" in open(os.path.join(
        ROOT, "src", "workflow_export.py")).read()


# ---- 版本链 ----

def test_tooling_version_bumped():
    assert we.TOOLING_VERSION == "3.46"
    assert "TOOLING 3.46。" in SKILL
    assert "| v3.46 | 2026-09-24" in SKILL
