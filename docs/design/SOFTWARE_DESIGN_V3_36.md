# SOFTWARE_DESIGN_V3_36: 函数级设计

## normalize_surfaces (src/surface_mapper.py:516)

### str 分支 (编辑点 :536-552)

```
tb = s.get("trust_boundary")
if isinstance(tb, str):
    s["trust_boundary_raw"] = tb
    t = tb.lower()
    if t in VALID_TRUST:                 # v3.36 (SWR-V3.36-001) canonical 短路
        mapped = t
    elif <既有关键词链, 逐项不变>:
        ...
    s["trust_boundary"] = {"type": mapped, "original": tb}
```

### dict 遗留分支 (编辑点 :553-570)

```
elif isinstance(tb, dict) and tb.get("type") not in VALID_TRUST:
    s.setdefault("trust_boundary_raw", tb.get("type"))
    t = str(tb.get("type", "")).lower()
    if t in VALID_TRUST:                 # v3.36 (SWR-V3.36-002) 大小写变体对称短路
        mapped = t
    elif <既有关键词链, 逐项不变>:
        ...
    s["trust_boundary"] = {"type": mapped, "original": tb.get("type")}
```

### 语义要点

- 短路条件用**小写化值**判定, `mapped = t`(即规范小写形态)——大小写变体
  (如 "Unauthenticated_Remote") 归一为规范值, 仍留 original 原文;
- 关键词链整体不动 (自由文本映射零回退);
- dict 分支触发条件不变 (`type not in VALID_TRUST`), 规范 dict 仍直接透传,
  本分支内短路只服务"非规范值字符串恰好等于规范值大小写变体"的边角形态。

## P 分层序列

P1: surface_mapper.py 两分支短路 → P2: tests/test_v336.py 守卫 →
P4: 版本链五件。
