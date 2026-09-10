# SOFTWARE_DESIGN_V3_39: 编辑点级设计

## D-1: normalize 词边界 (src/surface_mapper.py)

新增辅助函数 (与 checklist_binder._kw_match 同语义, normalize 侧本地实现防
跨模块耦合):

```python
_ASCII_KW = re.compile(r"\b([A-Za-z0-9_-]+)\b")
def _kw_hit(kw, text):
    """ASCII 关键词按词边界 (防 cli 误配 client, SWR-V3.4.4-001 同源);
    CJK 关键词保持子串语义。"""
    if kw.isascii():
        return bool(_ASCII_KW.search(text) and kw in _ASCII_KW.findall(text))
    return kw in text
```

两分支关键词链的 `any(k in t for k in (...))` 全部替换为
`any(_kw_hit(k, t) for k in (...))` (4 处)。

## D-2: seed 双写扩展 (src/language_issue_matrix.py seed_entries)

双写循环 `for e in [...external_seeded...]` → `for e in inv["entries"] if
e 的 id 在本次 added 列表` (或按 source.tier 全量, 幂等); 格缺失时创建
seeded 五字段格; origin 串按 tier: `(external_seeded date)` /
`(battle_verified date)` / `(source_seeded date)`。

## D-3: tests/asset_guards.py

集中常量 (与资产实况同步维护, 单点):
CHECKLISTS=48, INVENTORY_ENTRIES=202, BATTLE_CONFIRMED=12,
QUICKJS_BATTLE=2, CADDY_BATTLE=7, HAPROXY_BATTLE=3, MATRIX_CELLS 按需。
test_v328/v329/v337 引用之。

## D-4: severity_override 形态 (tools/batch_verify.py + SKILL.md)

消费点 (r4-collect ~:521 与 grade 路径) 读字段前:
```python
ov = v.get("severity_override")
if isinstance(ov, dict):   # 形态容忍归一化 (SWR-V3.39-004)
    v["severity_override"] = ov.get("value")
    v["severity_override_reason"] = ov.get("reason", v.get("severity_override_reason", ""))
    <warn: dict 形态已归一化>
```
SKILL.md 严重程度段补: "severity_override 为字符串合法值 {critical,high,
medium}, 理由写独立字段 severity_override_reason"。

## P 分层序列

P1 D-1/D-2 → P2 D-3 → P3 D-4 → P4 版本链五件。
