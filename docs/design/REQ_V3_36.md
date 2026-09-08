# REQ_V3_36: trust_boundary 规范枚举透传修复

## 缺陷清单 (代码核实)

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | `normalize_surfaces` 对已是 `VALID_TRUST` 成员的字符串 trust_boundary 走自由文本关键词映射, 规范枚举被静默改写: `local`/`trusted_channel`/`unknown`/`authenticated_remote` 不命中任何关键词 → else 兜底改写为 `environment`; `environment` 命中 `"env"` 子串关键词 → 改写为 `local`。7 个规范值中 5 个存在改写路径 | Caddy 阶段 6 验收审计 R1 四域合并实录: 70 面中 35 面 tb 被改写 (18× trusted_channel→environment, 14× local→environment, 3× environment→local), 逐面核对 `input_surface.json` 的 `{type, original}` 差异。旧审计 (servo/firefox) 未暴露——其 agent 写自由文本, 关键词映射恰好命中; Caddy 批按任务书 canonical schema 写规范枚举, 首次触发 | `normalize_surfaces` 两分支首步加 canonical 短路: 小写化后 `in VALID_TRUST` 则透传为规范值, 不进入关键词映射 | `src/surface_mapper.py:536-552` (str 分支), `:553-570` (dict 遗留分支, 对称加固) |

## 消费者 (改写后果流向)

- `src/evidence_ledger.py:185` — 逐通道验证 warn 按 tb 判定 (边界语义失真 → 验证义务错挂)
- `tools/batch_verify.py:425` — 分级信号推导消费 tb (分级错判)
- `src/workflow_export.py:360` — verifier 任务书注入 tb (验证视角被污染)

三者之下 R2 假设空间整体建立在错误边界语义上: 本地部署面被标为 environment、可信通道面被标为 environment、environment 面被标为 local——可达性判断的信任前提失真。

## 违反纪律

skill-optimizer 纪律 #4 (不自动改写——误猜风险>收益, v3.14 D-4 裁自动 re-credit 先例): 规范输入是精确值, 无任何"猜测"成分, 映射纯属误伤。

## 修复范围 (P1 机械)

1. `normalize_surfaces` str 分支: `t = tb.lower(); if t in VALID_TRUST: mapped = t` 短路;
2. dict 遗留分支: `t = str(tb.get("type","")).lower(); if t in VALID_TRUST: mapped = t` 对称短路 (大小写变体规范值同样透传);
3. 关键词映射仅保留给非规范自由文本 (既有语义零变化)。

## 测试守卫 (tests/test_v336.py)

- T-1: 8 个 VALID_TRUST 规范串逐个过 normalize → `type == 输入值` (含原值留档 original);
- T-2: 自由文本映射回归: "外部请求者 → 服务层"→unauthenticated_remote、"本地部署者配置"→local、"TLS 会话"→authenticated_remote、无关键词文本→environment (映射语义零回退);
- T-3: Caddy 批形态混合输入 (规范串 + 自由文本同批) → 规范串零改写;
- T-4: dict 遗留分支大小写变体 ({"type":"Environment"}) → environment;
- T-5: 全量回归 (550+) 绿 + 旧队列复跑零新增告警 (servo/firefox 旧 tb 已是规范 dict, 两分支不触发——兼容性不变式)。

## 开发序列

P1 修复 → 测试守卫 → P4 版本链五件 → 安装 → Caddy 重合并复核 (R1 签收)。
