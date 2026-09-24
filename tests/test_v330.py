"""SWR-V3.30: paired_control_probe 通用双测对照探针测试。
TEMPLATES 注册/argv 契约/去项目化/真实运行判定/SKILL.md 枚举/版本链。
"""

import json
import os
import subprocess
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))

import harness_runner


def test_registered_in_templates():
    assert "paired_control_probe" in harness_runner.TEMPLATES
    spec = harness_runner.TEMPLATES["paired_control_probe"]
    assert spec["langs"] == ["any"]


def test_argv_contract_missing_commands():
    p = subprocess.run([sys.executable, os.path.join(
                        WORKSPACE, "assets/templates/harness/paired_control_probe.py")],
                       capture_output=True, text=True)
    assert p.returncode == 2 and "usage" in p.stderr


def test_deproject():
    blob = open(os.path.join(WORKSPACE, "assets/templates/harness",
                             "paired_control_probe.py")).read()
    for tok in ("quickjs", "ktor", "actix", "awstats", "sinatra", "django",
                "/root/"):
        assert tok not in blob, tok


def test_real_paired_run_confirms():
    """真实双测: 对照组 4MB 分配 vs 攻击组 32MB 分配 → PAIRED_CONFIRMED。"""
    script = os.path.join(WORKSPACE, "assets/templates/harness/paired_control_probe.py")
    ctrl = ("python3 -c 'import time; a=[bytearray(1024*1024) for _ in range(4)]; "
            "time.sleep(0.6)'")
    atk = ("python3 -c 'import time; a=[bytearray(1024*1024) for _ in range(32)]; "
           "time.sleep(0.6)'")
    p = subprocess.run([sys.executable, script, ctrl, atk,
                        "--threshold", "2.0"],
                       capture_output=True, text=True)
    assert p.returncode == 0
    d = json.loads(p.stdout)
    assert d["verdict"] == "PAIRED_CONFIRMED", d
    assert d["attack"]["peak_hwm_kb"] > 0


def test_real_paired_run_no_diff():
    """对照组与攻击组同量级 → NO_SIGNIFICANT_DIFF。"""
    script = os.path.join(WORKSPACE, "assets/templates/harness/paired_control_probe.py")
    ctrl = "python3 -c 'import time; a=bytearray(4*1024*1024); time.sleep(0.6)'"
    atk = "python3 -c 'import time; a=bytearray(5*1024*1024); time.sleep(0.6)'"
    p = subprocess.run([sys.executable, script, ctrl, atk,
                        "--threshold", "2.0"],
                       capture_output=True, text=True)
    d = json.loads(p.stdout)
    assert d["verdict"] == "NO_SIGNIFICANT_DIFF", d


def test_control_failed():
    script = os.path.join(WORKSPACE, "assets/templates/harness/paired_control_probe.py")
    p = subprocess.run([sys.executable, script, "false", "true"],
                       capture_output=True, text=True)
    d = json.loads(p.stdout)
    assert d["verdict"] == "CONTROL_FAILED"


def test_skmd_listed():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "paired_control_probe" in sk
    assert "7 个实证模板" in sk


def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.46"
