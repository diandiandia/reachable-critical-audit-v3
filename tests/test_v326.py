"""SWR-V3.26: P0 交付链与防漂移修复测试。
SWR-V3.26-001: install.sh git 前置守卫三用例（脏树拒绝 / --allow-dirty
放行 / 干净树放行）——warn 级防线 v3.16→v3.22 复发史后的拒绝级修法。
"""

import os
import shutil
import subprocess
import sys
import tempfile

import pytest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# install.sh 为 workspace-only 资产 (install.sh 不安装自身, 同 test_v33
# docs/design 惯例)——安装副本上下文中守卫测试跳过 (守卫本身即 dev 侧交付链)
_INSTALL_SH = os.path.join(WORKSPACE, "install.sh")
SKIP_NO_INSTALL = pytest.mark.skipif(not os.path.exists(_INSTALL_SH),
                                     reason="install.sh 仅存在于开发仓库")

# install.sh 复制清单所需的最小 skill 布局（模块占位即可, 冒烟段
# pytest 无测试收集 → 尾部 || 分支 → exit 0, 既有行为）
_MODULES = [
    "surface_mapper", "signature_lib", "signature_matcher",
    "generation_registry", "language_issue_matrix", "evidence_ledger",
    "harness_runner", "workflow_export", "checklist_binder",
    "precedent_library", "r2_guard", "lessons_recorder",
]
_DIRS = ["tools", "resources", "task_templates", "templates", "tests",
         "lessons", "harness_manuals", "docs/legacy"]


def _make_fixture_repo():
    tmp = tempfile.mkdtemp(prefix="v326_fixture_")
    for d in _DIRS:
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
    open(os.path.join(tmp, "SKILL.md"), "w").write("# fixture\n")
    open(os.path.join(tmp, "README.md"), "w").write("# fixture\n")
    open(os.path.join(tmp, "docs/legacy/SKILL_V2.1.md"), "w").write("# v2.1\n")
    for m in _MODULES:
        open(os.path.join(tmp, m + ".py"), "w").write("# fixture\n")
    shutil.copy(os.path.join(WORKSPACE, "install.sh"), tmp)
    subprocess.run(["git", "-C", tmp, "init", "-q"], check=True)
    subprocess.run(["git", "-C", tmp, "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", tmp, "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
    subprocess.run(["git", "-C", tmp, "commit", "-qm", "init"], check=True)
    return tmp


def _run_install(tmp, dst, allow_dirty=False):
    cmd = [os.path.join(tmp, "install.sh")]
    if allow_dirty:
        cmd.append("--allow-dirty")
    cmd.append(dst)
    return subprocess.run(cmd, capture_output=True, text=True)


@SKIP_NO_INSTALL
def test_install_refuses_dirty_tree():
    """脏树拒绝: 未提交改动存在时 install.sh exit≠0 且 stderr 含脏清单。"""
    tmp = _make_fixture_repo()
    try:
        open(os.path.join(tmp, "uncommitted.py"), "w").write("# dirty\n")
        dst = os.path.join(tmp, "dst")
        r = _run_install(tmp, dst)
        assert r.returncode != 0, "脏树安装应被拒"
        assert "未提交改动" in r.stderr, f"缺拒绝指引: {r.stderr}"
        assert "uncommitted.py" in r.stderr, f"缺脏文件清单: {r.stderr}"
        assert not os.path.exists(os.path.join(dst, "SKILL.md")), \
            "拒绝后不应落盘"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@SKIP_NO_INSTALL
def test_install_allow_dirty_flag_bypasses():
    """--allow-dirty 显式豁免: 同脏树下放行且文件落盘 (反面分支)。"""
    tmp = _make_fixture_repo()
    try:
        open(os.path.join(tmp, "uncommitted.py"), "w").write("# dirty\n")
        dst = os.path.join(tmp, "dst")
        r = _run_install(tmp, dst, allow_dirty=True)
        assert r.returncode == 0, f"--allow-dirty 应放行: {r.stdout}\n{r.stderr}"
        assert os.path.exists(os.path.join(dst, "SKILL.md")), "豁免后应落盘"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@SKIP_NO_INSTALL
def test_install_clean_tree_passes():
    """干净树放行: 无未提交改动时 install.sh 正常完成 (零误伤基线)。"""
    tmp = _make_fixture_repo()
    try:
        dst = os.path.join(tmp, "dst")
        r = _run_install(tmp, dst)
        assert r.returncode == 0, f"干净树应放行: {r.stdout}\n{r.stderr}"
        assert os.path.exists(os.path.join(dst, "SKILL.md"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- 版本链登记 ----

def test_tooling_version_guard():
    sys.path.insert(0, WORKSPACE)
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.28"
