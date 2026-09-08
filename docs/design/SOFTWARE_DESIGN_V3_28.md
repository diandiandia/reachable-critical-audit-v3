# SOFTWARE_DESIGN_V3.28 — Top15×Top10 目标物化

## P 分层序列

```
P1 加载器+资产: inventory JSON(派生) + inventory/goal/seed 命令 + test_v328
P4 版本链: TOOLING 3.28 + 守卫 ×18 + SKILL.md 增量段(含回填升档条款) + tracking + gen_tracking
```

## P1-1:inventory JSON(一次性派生,派生脚本不落仓库)

派生规则(34 矩阵格 × pattern 粒度 → 36 条目;问题粒度=pattern 而非格——多 pattern
格各成条目,QuickJS 限额旁路族独立承载):
- id = `INV-<lang>-<NNN>`(按 lang 序编号)
- title = pattern(每条 pattern 一条目=一个问题;pitfall 全量 join 保留格的完整指引)
- family/cwe/sink_hint 取自 cell(sink_hint=cell.sinks[0])
- source.tier:cell.source_lessons 含战役证据(具体战役名/W6 实录)→
  battle_verified;仅清单/签名引用 → source_seeded
- verify:仅 QuickJS 实证条目升 battle_confirmed——
  C×RESOURCE-DOS → battles=["quickjs"] candidates=["CAND-001","CAND-003","H-1-F1","H-7-F2"]
  C×MEMORY-SAFETY → battles=["quickjs"] candidates=["H-2-F1","H-2-F2"]
  其余 → status=unverified,battles=[],candidates=[](旧战役候选 id 不可溯,诚实)
- goal 元数据:{"per_lang_target": 10, "milestones": K1/K2 定义}

## P1-2:加载器三命令

```python
_SEV_TIER = {"MEMORY-SAFETY": 1, "INJECTION": 1, "RESOURCE-DOS": 2, "RACE": 2,
             "STATE": 2, "AUTHN": 2, "ERROR-HANDLING": 2, "NUMERIC": 2,
             "DATA-INTEGRITY": 3, "CRYPTO": 3, "WEB": 3, "OTHER": 4}
# cwe 严重度: 787/125/416/415/476/190/129/843/78/94/77/502/191→1; 其余→2

def load_inventory():  # resources/language_issue_inventory.json
def inventory_for(lang):  # 按 (tier, cwe_max_sev, id) 排序; 未知语言 []
def goal_progress():
    # per_lang: entries/gap_to_10/battle_confirmed/tier 分布
    # milestones: K1 (entries>=10 语言数)/K2 (battle_confirmed>=10 语言数) → x/16
def seed_entries(path):
    # 校验: 每条目 source.tier ∈ 枚举 且 external_seeded 必须 origin+date;
    # lang 在 langs; cwe 格式 CWE-\d+; 去项目化扫描 (黑名单 token);
    # 幂等: (lang,title) 重复 → 拒绝该条目
    # 通过校验者追加写回 inventory JSON
```

main 增 `inventory <lang>` / `goal` / `seed <file>` 三分支。

## P4:版本链

1. TOOLING_VERSION "3.27"→"3.28"
2. 守卫 ×18 同步(test_v328 登记后 19)
3. SKILL.md 增量段——含 **回填升档条款(P3 提示级)**:
   验收收官时,确认问题的 cwe 命中 inventory 条目 → 该条目 verify.status=
   battle_confirmed,battles 追加战役名,candidates 追加候选 id,date 落盘
4. REQUIREMENTS_TRACKING.md 手工段 + gen_tracking VERSIONS 登记

## 测试设计:test_v328.py

- test_inventory_loads:34 条目 + 字段完备 + lang 枚举校验
- test_inventory_rank_order:MEMORY-SAFETY 条目前于 CRYPTO 条目(c 语言)
- test_goal_math:gap = 10 - entries;K1/K2 分母 16;总数 34
- test_goal_milestone_fields:K1/K2 定义存在
- test_seed_valid:合法 external 种子入库(临时副本)
- test_seed_reject_no_origin / _project_name / _bad_lang / _duplicate(四个反面分支)
- test_verify_battle_confirmed:QuickJS 条目 candidates 含 CAND-001/H-2-F1
- test_tooling_version_guard:"3.28"
