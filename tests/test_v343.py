"""test_v343 — 机制冻结实验 + 知识补种 + 架构体检 (SWR-V3.43-001..008)。

K-1 c 矩阵 PAGE-CACHE-OWNERSHIP / K-2 java 十格归并种格 /
K-3 H7 谓词逻辑错误 / K-4 fixminer 窗口 / K-5 H3 kernel 锚点 /
S-1 第四问 / S-2 重设计触发判据 / S-3 条款消费度量。
机制冻结守卫: 本周期无判定逻辑改动 (版本链机械步除外)。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SKILL = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
ROOT = os.path.join(os.path.dirname(__file__), "..")


def _skill():
    return open(SKILL).read()


# ---------- SWR-V3.43-001: K-1 页缓存所有权族 ----------

def test_matrix_pagecache_seeded():
    """c 矩阵含 TRUST-BOUNDARY 页缓存所有权条目。"""
    import language_issue_matrix as lim
    inv = lim.load_inventory()
    entry = [e for e in inv.get("entries", [])
             if e.get("lang") == "c" and "零拷贝/in-place 优化所有权" in e.get("title", "")]
    assert entry, "c 矩阵缺 PAGE-CACHE-OWNERSHIP 条目"
    e = entry[0]
    assert "CWE-787" in e.get("cwe", []) and "CWE-290" in e.get("cwe", [])
    src = e.get("source", {})
    assert src.get("tier") == "external_seeded"
    assert src.get("origin") and src.get("date")


def test_hitrate_pagecache_query():
    """hitrate 查询 CWE-787 应命中新条目 (发现力对照判据)。"""
    import language_issue_matrix as lim
    r = lim.hitrate("c", ["CWE-787"])
    titles = " ".join(h["title"] for h in r.get("hits", []))
    assert "零拷贝" in titles, f"页缓存族未命中: {r}"


# ---------- SWR-V3.43-002: K-2 java 十格归并种格 ----------

def test_matrix_java_seeded_10():
    """java 矩阵含 Keycloak hitrate 十格归并条目 (7 族归并)。"""
    import language_issue_matrix as lim
    inv = lim.load_inventory()
    java = [e for e in inv.get("entries", []) if e.get("lang") == "java"]
    titles = " ".join(e.get("title", "") for e in java)
    for frag in ("日志注入", "信任代理判定 fail-open", "时序窗口",
                 "空引用/越界解引用", "类型混淆", "无界集合累积",
                 "撤销策略未生效"):
        assert frag in titles, f"java 矩阵缺 {frag}"


def test_hitrate_keycloak_10_queries():
    """Keycloak hitrate 10 个未种 CWE 查询应全部被覆盖 (7/18 → 覆盖率 100%)。"""
    import re
    import language_issue_matrix as lim
    queried = {"117", "290", "367", "362", "613", "294", "476", "704",
               "789", "303"}
    r = lim.hitrate("java", ["CWE-117", "CWE-290", "CWE-367", "CWE-362",
                             "CWE-613", "CWE-294", "CWE-476", "CWE-704",
                             "CWE-789", "CWE-303"])
    covered = set()
    for h in r.get("hits", []):
        covered |= {re.sub(r"[^\d]", "", str(c)) for c in h.get("cwe", [])}
    missing = queried - covered
    assert not missing, f"hitrate 缺口未闭合: {missing}"


# ---------- SWR-V3.43-003: K-3 H7 谓词逻辑错误 ----------

def test_skillmd_h7_logic_error_hint():
    c = _skill()
    assert "鉴权谓词弱化或逻辑错误" in c
    assert "谓词本身错误而非被弱化" in c


# ---------- SWR-V3.43-004: K-4 fixminer 窗口 ----------

def test_skillmd_fixminer_window_hint():
    c = _skill()
    assert "同形态修复族间隔 >1 年时" in c
    assert "SWR-V3.43-004" in c


# ---------- SWR-V3.43-005: K-5 H3 kernel 锚点 ----------

def test_h3_kernel_anchor_hint():
    tpl = os.path.join(ROOT, "assets", "task_templates", "biz_hypothesis.md")
    c = open(tpl).read()
    assert "任务退出竞态" in c and "RBTree 双插入" in c
    assert "io_uring 形态" in c


# ---------- SWR-V3.43-006/007: S-1/S-2 skill-optimizer ----------

def test_optimizer_fourth_question():
    so = os.path.join(ROOT, "..", "skill-optimizer", "SKILL.md")
    if not os.path.exists(so):
        so = os.path.expanduser("~/.claude/skills/skill-optimizer/SKILL.md")
    c = open(so).read()
    assert "义务入库四问" in c
    assert "可推导知识默认不入库" in c


def test_optimizer_redesign_triggers():
    so = os.path.join(ROOT, "..", "skill-optimizer", "SKILL.md")
    if not os.path.exists(so):
        so = os.path.expanduser("~/.claude/skills/skill-optimizer/SKILL.md")
    c = open(so).read()
    assert "架构重设计触发判据" in c
    assert "修复互相冲突" in c and "特例化累积" in c
    assert "门禁形同虚设" in c and "知识复用率趋零" in c
    assert "兼容性债务累积" in c


# ---------- SWR-V3.43-008: S-3 条款消费度量 ----------

def test_skillmd_consumption_metric_hint():
    c = _skill()
    assert "条款消费度量" in c
    assert "无消费即裁除" in c


# ---------- 机制冻结守卫 ----------

# v3.44 (SWR-V3.44-008): v3.43 周期文件级冻结已随 K1 验收闭合 (判据达成)。
# 守卫从「本周期判定逻辑零改动 (文件级)」收窄为「判定逻辑守卫」——
# 允许域 = P3 提示级 prompt 文本 / P1 簿记守卫; 禁止域 = 判定函数与 schema
# (diff hunk 头命中受保护函数名即违规, 用 hunk 的 @@ 函数锚定判定)。

PROTECTED = ("def assert_ledger", "def severity_for", "def grade_verdict",
             "VERDICT_SCHEMA", "REFUTATION_SCHEMA", "RESURRECT_SCHEMA",
             "def _aggregate_counts", "def is_claim_like", "def resurrect_pool")

def test_mechanism_freeze_scope():
    """判定逻辑守卫: 受保护判定函数/schema 的 diff hunk 零命中。

    锚点 = v3.43 末提交 (dd967a1); 允许改动 src/tools 文件中的提示级
    prompt 文本与簿记守卫, 禁止触碰判定函数本体。
    """
    import subprocess
    r = subprocess.run(
        ["git", "-C", ROOT, "diff", "dd967a1", "--", "src/workflow_export.py",
         "tools/batch_verify.py", "src/evidence_ledger.py",
         "src/surface_mapper.py", "src/signature_lib.py",
         "src/language_issue_matrix.py", "src/harness_runner.py",
         "src/r2_guard.py", "src/precedent_library.py",
         "src/checklist_binder.py"],
        capture_output=True, text=True)
    diff = r.stdout
    if not diff:
        return  # 无改动
    hits = []
    for line in diff.split("\n"):
        if line.startswith("@@"):
            for p in PROTECTED:
                if p in line:
                    hits.append((line.strip(), p))
    assert not hits, f"判定逻辑守卫违规 (受保护函数被改动): {hits}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-x", "-q"])
