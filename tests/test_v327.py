"""SWR-V3.27: QuickJS 验收审计复盘知识基座补种测试。
矩阵 C 种格三条目 (未计数裸分配/子上下文继承/反序列化计数回绕) +
清单 CK-LIMIT-BYPASS-ENUM + R4 任务书正向确认惯例 + 版本链登记。
"""

import json
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "src"))


def _matrix_c_cells():
    import language_issue_matrix
    d = language_issue_matrix.load()
    return {c['family']: c for c in d['cells'] if c['lang'] == 'c'}


def test_matrix_seeded_limit_bypass_pattern():
    """SWR-V3.27-001: C×RESOURCE-DOS patterns 含资源门禁旁路条目 (QuickJS 三站点族)。"""
    c = _matrix_c_cells()['RESOURCE-DOS']
    assert any("计数分配器包装层" in p for p in c['patterns']), \
        "RESOURCE-DOS patterns 缺资源门禁旁路条目"
    assert any("裸 malloc" in p for p in c['patterns'])


def test_matrix_seeded_subcontext_pitfall():
    """SWR-V3.27-002: C×RESOURCE-DOS pitfalls 含子上下文继承条目 (worker rt 不继承实录)。"""
    c = _matrix_c_cells()['RESOURCE-DOS']
    assert any("继承矩阵" in p for p in c['pitfalls']), \
        "RESOURCE-DOS pitfalls 缺子上下文继承条目"
    assert any("fail-open" in p for p in c['pitfalls'])


def test_matrix_seeded_reader_overflow_pitfall():
    """SWR-V3.27-003: C×MEMORY-SAFETY pitfalls 含反序列化计数回绕条目 (H2-F1 实录)。"""
    c = _matrix_c_cells()['MEMORY-SAFETY']
    assert any("size_t" in p and "逐项溢出检查" in p for p in c['pitfalls']), \
        "MEMORY-SAFETY pitfalls 缺反序列化计数回绕条目"


def test_ck_limit_bypass_enum_structure():
    """SWR-V3.27-004: CK-LIMIT-BYPASS-ENUM 结构完整 + id 唯一 + 绑定规则合规。"""
    d = json.load(open(os.path.join(WORKSPACE, "assets", "resources", "checklist_library.json")))
    cks = d['checklists']
    ids = [c['id'] for c in cks]
    assert len(ids) == len(set(ids)), "清单 id 重复"
    entry = next(c for c in cks if c['id'] == 'CK-LIMIT-BYPASS-ENUM')
    assert entry['family'] == 'resource-dos'
    assert set(entry['binding']['cwe']) == {"CWE-770", "CWE-789"}
    assert entry['applies_to'] == ['verifier', 'refuter']
    assert len(entry['steps']) >= 4
    # 去项目化: 正文零项目名 (source_lessons 追溯字段允许)
    blob = json.dumps({k: v for k, v in entry.items() if k != 'source_lessons'},
                      ensure_ascii=False).lower()
    for tok in ('quickjs', 'qjs', 'bjson', 'sab'):
        assert tok not in blob, f"CK-LIMIT-BYPASS-ENUM 正文含项目名 {tok}"


def test_asset_count_45_synced():
    """SWR-V3.27-004 计数联动: 清单库 45 + SKILL.md 正文节计数同步。"""
    d = json.load(open(os.path.join(WORKSPACE, "assets", "resources", "checklist_library.json")))
    assert len(d['checklists']) == 49  # v3.37 +2; v3.40 +1 (SWR-V3.40-003)
    sk = open(os.path.join(WORKSPACE, "SKILL.md")).read()
    assert "49 条检查清单" in sk, "SKILL.md 清单计数未同步 48"


def test_biz_template_convention():
    """SWR-V3.27-005: R4 任务书含正向确认条目惯例段 (severity=low + 枚举提醒)。"""
    t = open(os.path.join(WORKSPACE, "assets", "task_templates", "biz_hypothesis.md")).read()
    assert "正向确认条目惯例" in t
    assert "severity 一律 low" in t
    assert "禁止自造" in t and "default_reachability" in t
    assert "claim_type 仅枚举值" in t


def test_tooling_version_guard():
    import workflow_export as we
    assert we.TOOLING_VERSION == "3.40"
