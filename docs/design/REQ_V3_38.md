# REQ_V3_38: 模型能力利用五机制 + v3.37 挂载欠账修复

> 依据: docs/design/MODEL_LEVERAGE_EVAL_V3_37.md (评估件, 用户裁定执行 A-E)。

## 缺陷清单 (代码核实)

| # | 缺陷/机制 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-0 | v3.37 两条目 (CK-SLICE-CAPACITY/CK-MAGNITUDE-OWNERSHIP) **缺 binding 字段** → binder bind() 的 matched 恒空, 条目永不挂载 (隐性欠账, 本批取证发现) | checklist_binder.py:120-130 取证实录: 无 binding 条目 matched=[] → 不注入 | 补 binding: SLICE={cwe:[125,787]+keywords}; MAGNITUDE={applies_to_phase:"R5" 语义空间} | assets/resources/checklist_library.json |
| D-1 (A) | 同族不一致防御形态未机制化——本批最高价值发现 (/config 封顶 /load 无) 的通用形态无清单条目、无 R2 假设条款 | CAND-001 差分定级实录 | 新条目 CK-SIBLING-CONSISTENCY (binding: RESOURCE-DOS∪AUTHN∪WEB cwe + "端点" keywords) + SKILL.md R2 条款 | checklist_library.json + SKILL.md |
| D-2 (B) | 自证伪仅先例提示 (v3.1 非结构化), 证伪者拿不到 verifier 自认的翻转点 | CAND-002 前提幻觉 1/2 才拦截实录 | VERDICT_SCHEMA 增 self_refutations 可选数组 + verify prompt 自证伪轮条款 + refute_prompt 注入 | src/workflow_export.py ×3 处 |
| D-3 (C) | 公开面检索 (CVE/上游 master 对账) 后置 R3, 时间差假设通道未开 | CAND-005 commit 祖先对账实录 (反向使用); CAND-001 master 核对佐证 | SKILL.md R2 公开面关联检索条款 (提示级, 网络不可用零阻塞) | SKILL.md |
| D-4 (D) | 模型自主实证能力 (H1/H4 实录) 未义务化, 静态声称到 R5 才拦截 | CAND-011 晚拦截实录 (轮次浪费) | verify prompt 实证机会条款 (提示级, 无环境记录 blocker) | src/workflow_export.py |
| D-5 (E) | 现场构造 harness 回收义务未显式化 (paired_control_probe 入库先例隐含) | R5 现状条款只写"现场构造" | SKILL.md R5 回收条款一行 | SKILL.md |

## 测试守卫 (tests/test_v338.py)

- T-0: v3.37 两条目 binding 在位 + binder 实测挂载 (REACHABLE unbounded 候选 → CK-MAGNITUDE-OWNERSHIP 绑定; CWE-125 候选 → CK-SLICE-CAPACITY 绑定);
- T-1: CK-SIBLING-CONSISTENCY 条目 + binding + 去项目化; CWE-770 候选 → 挂载;
- T-2: VERDICT_SCHEMA 含 self_refutations (可选); verify prompt 含自证伪轮条款; refute_prompt 注入 self_refutations 文本;
- T-3: SKILL.md 含 R2 公开面关联条款 + 同族不一致条款 + R5 回收条款 + verifier 实证机会条款 (doc-lint 同形态);
- T-4: 计数 47→48 + 全量回归 + 旧队列复跑零新增告警。

## 开发序列

P1 (D-0 挂载修复 + D-2 schema) → P2 (D-2 prompt 条款) → P3 (D-1 条目 + D-3/D-4/D-5 条款) → P4 版本链五件 → 安装。
阶段 6 验收: 用户提供新项目 (验收判据见评估件第四节)。
