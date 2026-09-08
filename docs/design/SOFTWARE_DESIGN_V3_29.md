# SOFTWARE_DESIGN_V3.29 — 闭环接线

## P 分层序列

```
P1 加载器: goal priority 段 + hitrate 命令 + seed 双写 + _CWE_FAMILY
P2 数据: 2025 CWE Top 25 试点种格 (156 条目, 经自家 seed 命令入库)
P3 条款: SKILL.md 增量段 (R2 接通 + R6 命中率)
P4 版本链: TOOLING 3.29 + 守卫 ×19 + tracking + gen_tracking
```

## P1-1:goal priority 段(SWR-V3.29-001)

goal_progress() 输出增:
```json
"priority": {
  "per_lang_sorted_by_gap": [{"lang", "gap_to_target", "entries"}...按 gap 降序],
  "top_gap_languages": ["..."前 3],
  "note": "控制器输出: 种格与选题优先补 gap 最大语言 (提示级)"
}
```

## P1-2:hitrate 命令(SWR-V3.29-002)

```
python3 language_issue_matrix.py hitrate <lang> <cwe,...>
→ {"lang": "c", "queried": 5, "hits": [{"id", "title", "cwe"}...], "hit_rate": "2/5"}
```
只读;cwe 归一(CWE-770/770 双形态);命中=条目 cwe 与查询集相交。

## P1-3:seed 双写(SWR-V3.29-003)

seed_entries 通过校验后:
1. inventory 追加(既有逻辑)
2. 矩阵同步:family = _CWE_FAMILY[cwe 首位]或 OTHER;cells 中 (lang,family)
   存在 → patterns 去重追加、cwes 并集、source_lessons 追加 origin;
   不存在 → 建格 {lang, family, status:"seeded", cwes:[...], patterns:[...],
   sinks:[sink_hint], pitfalls:[pitfall], source_lessons:[origin]}
3. 两文件原子写(inventory 后矩阵;失败时两文件均在,一致性靠测试断言)

_CWE_FAMILY 映射(与账本 fam_map 同口径,按严重度表族归):
787/125/416/415/476/190/129/843/120/121/122→MEMORY-SAFETY;
78/94/77/89/502/22/918→INJECTION;862/863/639/306/352/284→AUTHN;
79/434→WEB;770→RESOURCE-DOS;20/200→DATA-INTEGRITY;其余→OTHER。

## P2:试点种格数据(映射表,设计件留档)

2025 CWE Top 25(WebFetch 取证)。每语言映射(保守适用性):
- c/cpp:787,416,125,120,476,121,122,770
- rust/swift:787,416,125,770,20,22,284,863,639,918(rust pitfall 注 unsafe 域)
- go:22,78,79,352,862,918,770,20,639,94
- java/kotlin/scala:89,502,22,79,352,862,918,770,434,639
- csharp:89,502,79,22,352,862,770,639,78,434
- python:79,89,352,862,22,78,94,502,918,770
- javascript:79,352,862,22,78,94,918,770,639,434
- php:79,89,22,78,94,352,862,502,434,770
- ruby:79,89,22,78,94,352,862,502,770,639
- perl:78,94,79,22,20,770,284,863,200,639
- powershell:78,77,94,22,284,863,862,20,770,200
- shell:78,77,94,22,20,770,200,284,863,639

条目形态:title=CWE 官方名;pattern=通用机制一句话;pitfall=通用注意点;
source={tier:"external_seeded", origin:"CWE Top 25 2025 rank N
(https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html)",
date:"2026-09-08"};verify=unverified 全量。
预期:156 条目,36→192;K1 16/16;K2 0/16 不变。

## P3:SKILL.md 增量段条款(SWR-V3.29-005)

1. R2 假设生成装载扩展(SWR-V3.18-002 语义扩展,提示级):
   "生成假设前执行 `cells <lang>` 与 `inventory <lang>`——cells 为该语言
   已种格提示,inventory 为该语言排序问题条目(含 external_seeded 档);
   external_seeded 条目只作假设空间提示,裁决必须以源码证据为准。"
2. R6 收官命中率条款(提示级):
   "收官时执行 `hitrate <lang> <本次确认问题 cwe 列表>` 并把命中率记入
   lessons 过程观察段——资产→发现能力的传导度量。"

## P4:版本链

TOOLING 3.29;守卫 ×19 同步(test_v329 登记后 20);SKILL.md 增量段;
tracking 手工段;gen_tracking 登记。

## 测试设计:test_v329.py

- test_goal_priority_order:gap 降序 + top_gap_languages 长度 3
- test_hitrate_math:c 语言查 770,787,999 → 命中 2/3 形态断言
- test_hitrate_unknown_lang:空输出
- test_seed_doublewrite_consistency:inventory 条目 (lang,family,pattern) ⊆ 矩阵格
- test_inventory_count_192_and_k1:192 条目 + goal K1 16/16
- test_seed_entries_origin_and_tier:全部 external 条目 origin 含 cwe.mitre.org
- test_seed_entries_deproject:正文键零项目名
- test_skmd_clauses:R2 接通条款 + R6 命中率条款文本在 SKILL.md
- test_tooling_version_guard:3.29
