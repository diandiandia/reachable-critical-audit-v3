"""v3.5 (P5): 去项目化防回退——第一原则三禁止的机器守卫。

根因 (v3.5 三项体检): DEPROJECT_BLACKLIST 只扫签名资产, 模板/手册/先例库是
覆盖盲区——templates/harness 曾硬编码 ktor/actix 端口 18083/18084 与 AWStats
专属逻辑 (xss_path_sim.pl 全文复刻), harness_manuals 曾含 6 处 /root/ 绝对路径,
precedent_library 五字段曾携带 ~60 处项目 CAND-id。

本文件断言: 运行时资产 (templates/harness + harness_manuals) 与先例库五字段
零项目 token 零 /root/; fixture 豁免区 (tests/fixtures) 锚点合规在位。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import signature_lib

WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRECEDENT_FIELDS = ("name", "criterion", "counterexample",
                    "applicability_scope", "applications")


def test_runtime_assets_zero_project_tokens():
    """templates/harness + harness_manuals 零黑名单 token 零 /root/。
    注册名 ↔ 磁盘文件一一对应由 test_harness_runner 守; 本测试守内容。"""
    hits = signature_lib._scan_runtime_assets()
    assert hits == [], f"运行时资产残留: {hits}"


def test_precedent_library_fields_generic():
    """先例库五字段零项目 token 零 /root/ (A1 形状抽象防回退)。"""
    data = json.load(open(os.path.join(WORK, "resources", "precedent_library.json")))
    bad = []
    for p in data["precedents"]:
        for f in PRECEDENT_FIELDS:
            t = str(p.get(f, "")).lower()
            for tok in signature_lib.DEPROJECT_BLACKLIST:
                if tok in t:
                    bad.append((p.get("id"), f, tok))
            if "/root/" in str(p.get(f, "")):
                bad.append((p.get("id"), f, "/root/"))
    assert bad == [], f"先例库残留: {bad}"


def test_fixture_anchor_compliant():
    """AWStats 专属逻辑只允许存于 tests/fixtures 豁免区 (A2 迁移防回退)。"""
    anchor = os.path.join(WORK, "tests", "fixtures", "xss_path_sim_awstats_anchor.pl")
    assert os.path.exists(anchor), "fixture 锚点缺失"
    assert "CleanXSS" in open(anchor).read()  # fixture 豁免区可保留溯源内容
    live = open(os.path.join(WORK, "templates", "harness", "xss_path_sim.pl")).read()
    assert "CleanXSS" not in live
    assert "awstats" not in live.lower()
    assert "AWStats" not in live


def test_known_instances_only_in_fixtures():
    """回归锚点库只允许在 tests/fixtures (三禁止③ 防回退)。"""
    assert os.path.exists(os.path.join(WORK, "tests", "fixtures", "known_instances.json"))
    assert not os.path.exists(os.path.join(WORK, "resources", "known_instances.json"))


def test_harness_templates_no_hardcoded_ports():
    """B1 端口参数化防回退: 模板零历史战役专属端口字面量。"""
    for fn in ("ws_frame_alloc.py", "ws_frame_accum.py"):
        t = open(os.path.join(WORK, "templates", "harness", fn)).read()
        assert "18083" not in t and "18084" not in t, fn
        assert "<host> <port>" in t or "host, port" in t, fn  # argv 必传形态
