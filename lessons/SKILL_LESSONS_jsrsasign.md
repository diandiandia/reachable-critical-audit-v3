# SKILL Lessons — jsrsasign（2026-08-21）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

### R3
- [grade_recomputed] CAND-004: 机械分级重算 (main-agent-call-chain-restructure)
- [grade_recomputed] CAND-007: 机械分级重算 (main-agent-r5-empirical-upgrade)

### R3.5
- [verdict_correction] CAND-004: {'target': 'CAND-004', 'by': 'main-agent', 'reason': 'verifier 将 3 条独立路径压平成 10 跳 call_chain, 违反单线性链数据模型; 8 条边证据实际覆盖三路全部相邻对(路径 B/C 已列于 paths_analyzed)。机械重算 len(edges)=8 < len(chain)-1=9 故误判 static_only。主代理重构为路径 A 单链 4 跳, 边证据 8 条不变, 机械重算 = edge_proven。', 'demote_to': None}

## 主代理过程观察（人工补充）

- 【版本来源一致性】compact 后主代理误用 installed v3.4.2 路径跑 r4-collect/r35-collect/门禁，而 R2/R3 payload 由 workspace v3.4.3 导出——验收项目必须全程显式使用 workspace 代码路径，或先 install 再审计（高价值, W6 候选）。
- 【R4 部署布局义务】H7 agent 对 pkcs5pkey 的实证为 vm 全量加载 src（"浏览器等价全库加载"），非部署布局；主代理 grep 证实该模块不在任何发布产物（npm lib/all-min/Makefile 均零命中）→ claim 置空。R4 任务书应把步骤 0.5 部署布局义务显式扩展到 H1-H7 假说验证（高价值, W6 候选）。
- 【版本引用规范】npm bundle 自报 VERSION 11.1.4 vs package.json 11.1.5（ChangeLog 仅 README 改动）——报告引用版本时应同时注明两者（低价值保留）。
- 【refutation batch_size 静默截断】9 个资格候选默认 batch_size=4 只导出 4 个，主代理需显式 --batch-size；建议导出时输出资格全集计数（v3.4.3 候选）。
- 【kw:ws 子串误配】CK-WS-MATERIALIZE 的 applicability_signals 关键词 "ws" 子串命中 "jws"（CAND-001）——信号关键词需要词边界匹配（W6 候选）。
- 【计数类证据不可复现】CAND-010 的 MR 调用计数 79/48 被证伪者实测 55/69 且方向翻转（几何随机变量）——verifier 任务书应提示计数类观测不做可复现证据引用（W6 候选）。
- 【R3.5 产粮新模式】证伪者自行实证将 CAND-007 从 edge_proven 升级 empirically_confirmed（满足 R5 强制实证）——反证波次首次出现"升级而非降级"的产出形态。
- 【R3.5 拦截率 0/20】自证伪提示+步骤0 承重前提机制持续有效（同 P2 批次观察）；证伪者产出大量 strengthened/attribution_corrections（asn1cms:986 归因错误等被纠正）证明差异化视角复核的独立价值。
- 【库型发布布局核对】pkcs5pkey-1.0.js 为 src 存在但零发布模块——步骤 0.5 的"模块存在≠被导入/构建"是密码库审计的关键防线：npm files 字段 + Makefile + bundle grep 三查（高价值, W6 候选）。
- 【弱随机家族分布】CWE-338 四连（SecureRandom fallback 种子/CryptoJS IV+盐/TSA nonce/MR 基）——11.1.2 只修 rng.js 主路径（#655 HIGH）未同步其余三处："修一处未修全"是密码库弱随机缺陷的典型分布（高价值, W6 候选）。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
