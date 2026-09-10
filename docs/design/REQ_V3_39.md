# REQ_V3_39: haproxy 验收复盘四修复

## 缺陷清单 (代码核实)

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | normalize_surfaces 的 ASCII 关键词用子串匹配——"cli" 命中 "client", wire 字节自由文本误映射为 local; "env" 同理命中 "environment" (v3.36 canonical 短路掩盖了后者) | haproxy 验收实录: 40/82 面 trust_boundary 自由文本被低质量映射, 主代理逐类裁决归位 (22 类); binder 已有词边界修复 SWR-V3.4.4-001 (ws/jws) 而 normalize 未跟进 | 两分支关键词匹配改词边界语义 (ASCII \b 词边界, CJK 子串) | src/surface_mapper.py 两分支 |
| D-2 | seed 双写仅覆盖 external_seeded——battle_verified 条目需手动双写矩阵格 + 手动建格 (c×AUTHN 缺格实录) | haproxy R6 回填实录: 手动补双写 + 建 c×AUTHN 格; 同轮计数守卫失同步 | seed_entries 双写循环覆盖全部成功种格条目, 格缺失自动创建 (tier 区分 origin 格式) | src/language_issue_matrix.py seed_entries |
| D-3 | 资产计数守卫散落 test_v328/v329/quickjs 多个断言点——合法回填需多点编辑, R6 守卫失同步两次复发 (caddy/haproxy) | 两轮 R6 回填同形态复发实录 | 集中常量 tests/asset_guards.py, 各守卫 import | tests/test_v328/v329/v337 + 新 asset_guards.py |
| D-4 | severity_override 字段形态未文档化——主代理按 dict {value,reason} 写, 消费者要字符串+reason 字段 → r4-collect AttributeError | haproxy r4-collect 实录 | SKILL.md 契约一句 + batch_verify 形态容忍归一化 (dict→string+reason, warn) | SKILL.md + tools/batch_verify.py |

## 测试守卫 (tests/test_v339.py)

- T-1: "wire-client-bytes->parser" 不映射 local; CJK 关键词 ("cli 参数"/"本地配置") 照常映射 (回归);
- T-2: seed battle_verified 条目 → 矩阵格自动双写 + 缺格自动创建;
- T-3: asset_guards 常量 = 资产实况 (动态一致性);
- T-4: dict 形态 severity_override → 归一化 + warn;
- T-5: 全量回归 + servo/haproxy 旧队列复跑零新增告警。

## 开发序列

P1 (D-1/D-2) → P2 (D-3) → P3 (D-4) → P4 版本链五件 → 安装。
阶段 6 验收: haproxy 已闭环 (本轮); 下个新项目验证 v3.39 修复。
