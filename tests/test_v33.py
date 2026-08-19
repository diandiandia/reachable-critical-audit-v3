"""v3.3 需求测试 (REQ-V3.3-013 追踪泛化 + 分类器联动)。"""
import json, os, sys, tempfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "tools"))


def _require_design_docs():
    """docs/design 为 workspace-only 资产 (install.sh 不安装)——
    安装目录冒烟测试跳过依赖它的用例。"""
    import gen_tracking as gt
    if not os.path.exists(os.path.join(gt.ROOT, gt.DOCS["REQ-V3.3"])):
        pytest.skip("docs/design 仅存在于开发仓库")


def test_gen_tracking_generalized_ids():
    _require_design_docs()
    """v3.3 (REQ-V3.3-013): 泛化正则同时提取 REQ-V3-001 / REQ-V3.2.2-001 /
    REQ-V3.3-001 形态; 重建后 tracking 含 v3.2.2 与 v3.3 段。"""
    import gen_tracking as gt
    ids = [rid for rid, _ in gt.extract(gt.DOCS["REQ-V3.3"])]
    assert ids and all(rid.startswith("REQ-V3.3-") for rid in ids)
    assert len(ids) == 14
    ids22 = [rid for rid, _ in gt.extract(gt.DOCS["REQ-V3.2.2"])]
    assert ids22 and all(rid.startswith("REQ-V3.2.2-") for rid in ids22)
    # 旧形态仍被识别
    ids3 = [rid for rid, _ in gt.extract(gt.DOCS["REQ-V3"])]
    assert ids3 and all(rid.startswith("REQ-V3-") for rid in ids3)
    tracking = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "docs/design/REQUIREMENTS_TRACKING.md"),
        encoding="utf-8").read()
    assert "REQ-V3.2.2-001" in tracking and "REQ-V3.3-001" in tracking


def test_gen_tracking_extract_text_not_prefix():
    _require_design_docs()
    """v3.3 回归: 泛化正则的捕获组错位曾把需求文本提取成 "REQ"
    (内层交替组截断 ID) — 文本列必须是完整需求描述。"""
    import gen_tracking as gt
    for rid, text in gt.extract(gt.DOCS["REQ-V3.3"])[:3]:
        assert len(text) > 10, (rid, text)
        assert text != "REQ" and text != "SWR"
