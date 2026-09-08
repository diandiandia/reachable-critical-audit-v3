"""v3.36 (SWR-V3.36-001/002): trust_boundary 规范枚举透传守卫。
根因: Caddy 阶段 6 验收 R1 合并 35/70 面 tb 被关键词映射器静默改写
(local/trusted_channel→environment 兜底, environment→local 命中 "env" 子串)。
规范输入是精确值, 自由文本映射器不得改写规范枚举。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))
from surface_mapper import normalize_surfaces, VALID_TRUST


def _norm(tb):
    out = normalize_surfaces({"surfaces": [{
        "id": "SURF-X-001", "type": "network", "lang": "go",
        "entry_points": [], "taint_channels": [],
        "trust_boundary": tb, "confidence": "high"}]})
    return out["surfaces"][0]["trust_boundary"]


def test_t1_canonical_strings_pass_through_verbatim():
    """T-1: 8 个 VALID_TRUST 规范串逐个过 normalize → type == 输入值。"""
    for v in sorted(VALID_TRUST):
        got = _norm(v)
        assert got["type"] == v, f"{v!r} 被改写为 {got['type']!r}"
        assert got["original"] == v


def test_t2_free_text_keyword_mapping_unchanged():
    """T-2: 自由文本关键词映射零回退 (既有语义回归锚)。"""
    cases = {
        "外部请求者 → 服务层": "unauthenticated_remote",
        "本地部署者配置": "local",
        "TLS 会话": "authenticated_remote",
        "gated 门控入口": "gated",
        "宿主库调用方传入": "host_api",
        "无明显关键词的文本": "environment",
    }
    for text, want in cases.items():
        got = _norm(text)
        assert got["type"] == want, f"{text!r} → {got['type']!r} ≠ {want}"


def test_t3_mixed_batch_canonical_untouched():
    """T-3: Caddy 批形态混合输入同批 → 规范串零改写, 自由文本照常映射。"""
    out = normalize_surfaces({"surfaces": [
        {"id": "S1", "type": "network", "lang": "go", "entry_points": [],
         "taint_channels": [], "trust_boundary": "local", "confidence": "high"},
        {"id": "S2", "type": "network", "lang": "go", "entry_points": [],
         "taint_channels": [], "trust_boundary": "trusted_channel",
         "confidence": "high"},
        {"id": "S3", "type": "network", "lang": "go", "entry_points": [],
         "taint_channels": [], "trust_boundary": "environment",
         "confidence": "high"},
        {"id": "S4", "type": "network", "lang": "go", "entry_points": [],
         "taint_channels": [], "trust_boundary": "unknown",
         "confidence": "high"},
        {"id": "S5", "type": "network", "lang": "go", "entry_points": [],
         "taint_channels": [], "trust_boundary": "本地部署者配置",
         "confidence": "high"},
    ]})
    by_id = {s["id"]: s["trust_boundary"]["type"] for s in out["surfaces"]}
    assert by_id == {"S1": "local", "S2": "trusted_channel", "S3": "environment",
                     "S4": "unknown", "S5": "local"}


def test_t4_dict_legacy_case_variant_short_circuit():
    """T-4: dict 遗留分支大小写变体规范值透传 (SWR-V3.36-002)。"""
    got = _norm({"type": "Environment"})
    assert got["type"] == "environment", got
    got = _norm({"type": "Trusted_Channel"})
    assert got["type"] == "trusted_channel", got
    # 规范 dict 原有透传行为不变 (type ∈ VALID_TRUST 时不进分支)
    got = _norm({"type": "gated", "gate": "none"})
    assert got["type"] == "gated" and got.get("gate") == "none"


def test_t5_legacy_free_text_dict_still_maps():
    """T-5: dict 遗留分支非规范自由文本仍走关键词映射 (回归)。"""
    got = _norm({"type": "未认证的外部请求者"})
    assert got["type"] == "unauthenticated_remote"
    assert got["original"] == "未认证的外部请求者"
