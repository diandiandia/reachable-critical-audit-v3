# SWR_V3_36: trust_boundary 规范枚举透传

## SWR-V3.36-001: 规范枚举短路透传 (str 分支)

- **裁决**: `normalize_surfaces` str 分支在关键词映射**之前**检查小写化值 `in VALID_TRUST`;命中则 `mapped = t` 透传, 原文入 `original` 留档。自由文本仍走关键词映射, 语义零变化。
- **义务三问**: ①触发条件——任何 trust_boundary 为规范枚举串的 surface 归一化 (无条件, 因为它是数据正确性而非新检查步骤); ②消费者——validate/merge 全链 + evidence_ledger/batch_verify/workflow_export 三处下游; ③裁掉丢什么——Caddy 实录 35/70 面边界语义改写, 直接污染 R2 假设空间。
- **测试守卫**: test_v336.py T-1/T-3。

## SWR-V3.36-002: dict 遗留分支对称短路

- **裁决**: dict 遗留分支 (`type not in VALID_TRUST` 触发) 内对小写化后 `in VALID_TRUST` 的值同样短路透传 (大小写变体规范值不落入关键词映射)。
- **义务三问**: ①触发条件——dict 形态且 type 为规范值大小写变体; ②消费者——同上; ③裁掉丢什么——`{"type":"Environment"}` 现状会走 "env" 关键词改写为 local, 同 D-1 病根的另一入口。
- **测试守卫**: test_v336.py T-4。

## 兼容性不变式

- 自由文本关键词映射分支零改动 (T-2 回归锚定);
- 旧审计产物 (servo/firefox input_surface.json 的 `{type,original:null}` 规范 dict) 不触发两分支 (type ∈ VALID_TRUST), 零行为变化;
- merge/validate/门禁/报告零改动。
