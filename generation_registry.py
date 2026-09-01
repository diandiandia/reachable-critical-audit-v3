#!/usr/bin/env python3
"""生成层注册表 (v3.17, SWR-V3.17-001)。

源码扩展名默认视图 + 通用 DSL 族映射。运行时/引擎形态目标的生成物
(.pb.cc / DSL→生成代码 类) 在默认视图内可见并带 provenance; 项目专属
DSL 经 target_profile.generation_layers 审计期局部署名 (两段式:
机制入库, 项目专属扩展名不入运行时资产)。

消费者:
- surface_mapper._sample_source_files / language_inventory / size_tier
- signature_matcher.build_project_index
- tools/batch_verify.stage_collect (candidate language 推断)

用法:
    from generation_registry import merged_view, lang_family_for, provenance_for
"""
import json
import os

_DEFAULT = None


def load():
    """读 resources/generation_registry.json (进程内缓存, 读失败回退空注册表)。"""
    global _DEFAULT
    if _DEFAULT is not None:
        return _DEFAULT
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "resources", "generation_registry.json")
    try:
        with open(path, encoding="utf-8") as f:
            _DEFAULT = json.load(f)
    except OSError:
        _DEFAULT = {"default_extensions": [], "dsl_entries": []}
    return _DEFAULT


def default_extensions():
    """默认扩展名视图 (与 signature_matcher.CODE_EXTENSIONS 逐位一致)。"""
    return set(load().get("default_extensions", []))


def _dsl_entries():
    return load().get("dsl_entries", [])


def _dsl_lookup():
    """ext → entry 映射 (dsl ext 与生成物 ext 双向可达同一 entry)。"""
    out = {}
    for e in _dsl_entries():
        out[e["ext"]] = e
        for g in e.get("generates", []):
            out[g] = e
    return out


def profile_generation_exts(project_root):
    """target_profile.generation_layers 的项目局部扩展名 (未签收 = 空集)。

    返回 (exts, ext→lang_family)。profile 缺失/未签收/形态非法一律空集——
    零强制义务, 未签收 = 现状行为。
    """
    if not project_root:
        return set(), {}
    try:
        with open(os.path.join(project_root, ".audit_results",
                               "target_profile.json"), encoding="utf-8") as f:
            prof = json.load(f)
    except OSError:
        return set(), {}
    if not prof.get("signed_by"):
        return set(), {}
    layers = prof.get("generation_layers") or []
    exts, fam = set(), {}
    for layer in layers:
        if not isinstance(layer, dict) or not layer.get("ext"):
            continue
        exts.add(layer["ext"])
        fam[layer["ext"]] = layer.get("lang_family", layer["ext"])
        for g in layer.get("generates", []):
            exts.add(g)
            fam[g] = layer.get("lang_family", layer["ext"])
    return exts, fam


def merged_view(project_root=None):
    """源码普查扩展名全集 = 默认 ∪ DSL ∪ 生成物 ∪ profile 局部
    (无 profile 时 = 默认 ∪ 通用 DSL 族, 纯增量)。"""
    exts = set(default_extensions())
    for e in _dsl_entries():
        exts.add(e["ext"])
        exts.update(e.get("generates", []))
    extra, _ = profile_generation_exts(project_root)
    exts.update(extra)
    return exts


def lang_family_for(ext, project_root=None):
    """ext → 语言组键。'.h'/'.hpp' → '.c' (language_inventory 既有惯例);
    DSL/生成物 → lang_family; 未知 → 原 ext (调用方自行兜底)。"""
    ext = (ext or "").lower()
    if ext in (".h", ".hpp"):
        return ".c"
    lookup = _dsl_lookup()
    if ext in lookup:
        return lookup[ext].get("lang_family", ext)
    _, fam = profile_generation_exts(project_root)
    if ext in fam:
        return fam[ext]
    return ext


def provenance_for(ext):
    """ext 的生成物溯源: 生成物 → (dsl_ext, 'generated');
    DSL 源 → (ext, 'dsl'); 其他 → None。"""
    ext = (ext or "").lower()
    e = _dsl_lookup().get(ext)
    if e is None:
        return None
    if ext in e.get("generates", []):
        return e["ext"], "generated"
    return ext, "dsl"


# ---- v3.17 (SWR-V3.17-008): target_profile 消费者装载契约 ----

_PROFILE_DEFAULTS = {
    "surface_model": "entry",
    "generation_layers": [],
    "scale_class": None,
    "containment_default": "none",
    "empirical_modes": [],
}


def load_target_profile(project_root):
    """读 .audit_results/target_profile.json (签收后生效)。

    消费者统一契约: 文件缺失/形态非法/未签收 (signed_by 空) → 全默认 dict
    = 现状行为 (零强制义务)。签收后返回 recommended ∪ overrides。
    """
    prof = dict(_PROFILE_DEFAULTS)
    if not project_root:
        return prof
    try:
        with open(os.path.join(project_root, ".audit_results",
                               "target_profile.json"), encoding="utf-8") as f:
            raw = json.load(f)
    except OSError:
        return prof
    if not raw.get("signed_by"):
        return prof
    rec = raw.get("recommended") or {}
    ovr = raw.get("overrides") or {}
    for k in _PROFILE_DEFAULTS:
        if k in ovr:
            prof[k] = ovr[k]
        elif k in rec:
            prof[k] = rec[k]
    return prof
