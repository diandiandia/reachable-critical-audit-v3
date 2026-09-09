"""SWR-V3.32: 发现力四杠杆测试。
对抗枚举/修复驱动条款文本 / fixminer 输出形态 / r35 回显字段 /
hints --kind 加权 + lessons_refs / 向后兼容 / 版本链。
"""

import json
import os
import subprocess
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))

import language_issue_matrix as lim


# ---- SWR-V3.32-001/002: SKILL.md 条款 ----

def test_skmd_adversarial_and_fixminer_clauses():
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "对抗枚举条款" in sk and "缺陷形态展开" in sk
    assert "修复驱动假设条款" in sk and "fixminer" in sk
    assert "只挖不判" in sk


# ---- SWR-V3.32-002: fixminer ----

def test_fixminer_output_shape():
    r = subprocess.run([sys.executable,
                        os.path.join(WORKSPACE, "tools", "fixminer.py"),
                        "/root/quickjs", "--since", "60"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0
    d = json.loads(r.stdout)
    assert d["status"] == "OK"
    for c in d.get("fix_commits", []):
        # v3.33 (SWR-V3.33-008) 增 path_signal 键
        assert set(c.keys()) == {"hash", "subject", "files", "family",
                                 "path_signal"}
        assert c["family"] in ("MEMORY-SAFETY", "INJECTION", "RESOURCE-DOS",
                               "AUTHN", "RACE", "DATA-INTEGRITY", "OTHER")


def test_fixminer_no_git():
    r = subprocess.run([sys.executable,
                        os.path.join(WORKSPACE, "tools", "fixminer.py"),
                        "/tmp/nonexistent_dir_xyz"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert json.loads(r.stdout)["status"] == "NO_GIT"


def test_fixminer_usage_without_args():
    r = subprocess.run([sys.executable,
                        os.path.join(WORKSPACE, "tools", "fixminer.py")],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "usage" in r.stderr


# ---- SWR-V3.32-004: hints 加权与检索 ----

def test_hints_kind_reorder_library():
    h_default = lim.hints("c")
    h_lib = lim.hints("c", "library")
    top_default = h_default["inventory"][0]["family"]
    top_lib = h_lib["inventory"][0]["family"]
    assert top_lib in ("MEMORY-SAFETY", "RESOURCE-DOS", "STATE", "RACE",
                       "NUMERIC")
    assert h_lib["kind"] == "library"
    # 数据不因视图改变
    assert len(h_lib["inventory"]) == len(h_default["inventory"])


def test_hints_lessons_refs_nonempty_for_c():
    h = lim.hints("c")
    assert h["lessons_refs"], "c 语言应检索到历史教训引用"
    # v3.33 (SWR-V3.33-007) 增 matrix/ 种格通道; 两前缀均合法
    assert all(r.startswith(("lessons/", "matrix/")) for r in h["lessons_refs"])


def test_hints_no_kind_backward_compat():
    h = lim.hints("go")
    assert h["kind"] is None
    assert h["cells"] or h["inventory"]


# ---- 版本链 ----

def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.38"
