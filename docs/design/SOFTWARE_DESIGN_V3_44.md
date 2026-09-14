# SOFTWARE_DESIGN_V3_44 — 函数级设计 + P 分层序列

## P1 机械: D-1a (tools/batch_verify.py stage_r35n_collect)

当前形态 (行号实测 2026-09-14):
```python
    for c in queue["candidates"]:
        if c.get("verdict") == "UNREACHABLE" and not c.get("resurrection_review"):
            if c["id"] in selected:
                continue
            c["resurrection_review"] = {"revived": False,
                                        "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}
            auto_bookkept.append(c["id"])
```
目标形态:
```python
    # SWR-V3.44-001: 声称类跳过自动簿记——簿记「未选中」会使 gate ③c 的
    # presence 检查被满足而无一真实复核 (掩蔽洞, K1 初版样本漏声称类全量实录);
    # 声称类无真实复核 = 持续违规, 不得机械掩蔽
    import evidence_ledger as _el44
    claim_like_unreviewed = []
    for c in queue["candidates"]:
        if c.get("verdict") == "UNREACHABLE" and not c.get("resurrection_review"):
            if c["id"] in selected:
                continue
            if _el44.is_claim_like(c):
                claim_like_unreviewed.append(c["id"])
                continue
            c["resurrection_review"] = {"revived": False,
                                        "outcome": "复活抽样未选中 (规则见 _resurrect_sample.json)"}
            auto_bookkept.append(c["id"])
```
- import 放循环前 (函数级局部 import, 与 stage_r35_collect 的 `import
  evidence_ledger as el` 形态一致; 用别名避免与既有局部名冲突)。
- 输出 JSON 增 `"claim_like_unreviewed": claim_like_unreviewed` 字段; 非空时
  附 stderr warn 一行: 「声称类候选 {ids} 无真实复活复核且未簿记——gate ③c
  将持续违规, 须经复活波复核或主代理裁决」。
- is_claim_like 与 gate ③c 同源 (evidence_ledger.is_claim_like, SWR-V3.15-002
  单真相)——不复制判定。

## P3 内容: D-2 + D-6 (tools/batch_verify.py _build_prompt)

- step 1.5 尾部追加 (SWR-V3.44-003):
```
- **未合并补丁检索（v3.44, SWR-V3.44-003, 提示级）**：写「无首发归属/无公开
  修复」类断言前，必须执行未合并补丁检索（lore.kernel.org / openwall 关键词:
  sink 关键标识 + 子系统名）——公开但未合并的补丁同样是「非首发发现」的
  判定输入（git log 只能命中已合并历史, 未合并补丁不在其中, 曾致 verifier
  断言无归属而证伪者检索到 4 天前的未合并补丁）。网络不可用或检索范围受限
  时如实注明「检索受限」，不得写「无公开修复」。
```
- step 4 追加两句 (SWR-V3.44-006):
```
- 声明「全覆盖/无未枚举子集」前必须列出子集清单——自身 residual note 承认
  「其余实现未逐一核查」与「全覆盖」声明自相矛盾是复活波命中形态（v3.44,
  SWR-V3.44-006）
- 配置/构建前提分支的语义核查（v3.44, SWR-V3.44-006）: 标注「该分支不可达」
  前，先核查该分支下防御前提是否成立（CONFIG_*=n/flag=0 分支的守护性质——
  「默认构建不会走到」≠「该分支下前提成立」）；分支语义未核查的「不可达」
  标注不构成阻断论证
```

## P3 内容: SKILL.md 四处条款 (D-1b/D-3/D-4/D-7)

1. R3.5-N 复活抽样段 (SWR-V3.44-002): 追加「复活波优先经
   export_script_resurrect 导出（内置声称类全量规则, 与 gate ③c 同源）;
   主代理手工构造 payload 时, 派发前机械对照 is_claim_like 清单核验
   selected ⊇ 声称类集」。
2. R3.5 补强签收段 (SWR-V3.44-004): 追加「签收 strengthened/
   attribution_correction 前两级预推演: ① claim 重评级联——新 claim ∈
   EMPIRICAL_CLAIMS → gate ③/R5 触发 → 终态预判 (NEEDS_REVIEW 或实证计划);
   ② 口径一致性——containment/attacker_tier/severity 结构化值与证据文本
   对照 (内核/软中断上下文等 profile 派生缺省不适用场景)」。
3. R2 fixminer 段 (SWR-V3.44-005): 追加「修复族密集目标 (快照已含全部近期
   修复) 的批次预期——低 REACHABLE 率是预期而非审计失败, 价值 = 修复变体
   残留 + 未覆盖兄弟路径; 批次开题时按 fixminer 信号预设预期」。
4. R0 目录守卫段 (SWR-V3.44-007): 追加「同项目多批次续审时, 批前把上层产物
   归档 .audit_results/batch_<N>/ (报告/教训/队列/波次注册表), 新批从干净
   顶层重跑 R0-R6; 归档是执行约定, 不改机制」。

## P4 版本链 (SWR-V3.44-008)

1. src/workflow_export.py TOOLING_VERSION "3.43"→"3.44"
2. 版本守卫测试行同步 (grep -rn '"3.43"' tests/ 逐处核对——test_v313/
   test_v329/test_v342/test_v343 等)
3. SKILL.md v3.44 增量段 (列 SWR 号 + 验收判据)
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking VERSIONS 登记
5. 资产计数守卫核对 (零资产增删 → 212/157/208 不变)
6. 冻结守卫演进 (test_v343.py test_mechanism_freeze_scope): 锚点改
   dd967a1 (v3.43 末提交), 判据收窄为「diff hunk 头不得命中受保护判定函数名
   (assert_ledger/severity_for/grade_verdict/VERDICT_SCHEMA/REFUTATION_SCHEMA/
   RESURRECT_SCHEMA/_aggregate_counts/is_claim_like)」, docstring 注明 v3.43
   冻结实验已闭环 (K1 验收判据达成), v3.44 起守卫收窄为判定逻辑。

## 开发序列

P1 → P3(batch_verify) → P3(SKILL.md) → P4 → 测试 (tests/test_v344.py 新增)
→ 全量回归 → 旧队列复跑 → selfcheck → install.sh → installed 验证 → commits。
