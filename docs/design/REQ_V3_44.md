# REQ_V3_44 — K1 (linux kernel) 复盘缺陷修复设计

> v3.44 周期。输入: /root/linux/.audit_results/lessons.md「对 skill 的教训」7 条
> (2026-09-14 落盘) + 本会话 Q2 分析 (同项目多批次归档缺口)。
> DDL 声明: 历史 11 份项目 lessons.md 的教训条目已在各自周期消化 (tracking
> SWR source 追溯), 无新条目; 本轮唯一新输入 = linux lessons.md 7 条。

## 缺陷清单

| # | 缺陷 (案例支撑=linux lessons.md 第 N 条) | 取证 | 初判 | 修复 | 编辑点 |
|---|---|---|---|---|---|
| D-1a | 复活簿记掩蔽声称类: r35n-collect 自动簿记对声称类候选写「未选中」后, gate ③c 的 presence 检查被满足而**无任何真实复活复核** (第 1 条; 过程观察2: K1 初版样本漏声称类全量靠 gate 前置自检才抓到——若先跑 collect 再跑 gate 则掩蔽) | resurrect_pool (workflow_export.py:470) 声称类全量规则已正确在位; 掩蔽洞在 batch_verify.py stage_r35n_collect:687-699 | P1 | auto-bookkeep 跳过声称类 (is_claim_like 同源) + warn 列出 | tools/batch_verify.py stage_r35n_collect |
| D-1b | 复活波手工构造 payload 绕过导出器内置规则 (第 1 条; K1 主代理手写 resurrect_payload 绕过 export_script_resurrect) | 导出器 SWR-V3.2-040 规则在位; 主代理偏离无条款约束 | P3 | SKILL.md R3.5-N 节: 复活波优先经 export_script_resurrect 导出; 手工构造时机械对照 claim-like 集 | SKILL.md R3.5-N 段 |
| D-2 | verifier「无公开修复/可首发」断言缺未合并补丁检索义务 (第 2 条; CAND-016 verifier 断言无归属, 证伪者查到 4 天前 openwall 未合并补丁) | step 1.5 (SWR-V3.10-011) 只要求 git log + 公开 CVE 列表; lore/openwall 未合并补丁不在其中 | P3 | step 1.5 增: 未合并补丁检索 (lore.kernel.org/openwall 关键词) 后始可写「无首发归属」 | tools/batch_verify.py _build_prompt step 1.5 |
| D-3 | strengthened 签收与终态级联: claim 重评触发 gate ③/R5 需先推演 (第 3 条; 过程观察5: CAND-016/005 签收后才走级联) + containment/attacker_tier 口径与证据一致性 (第 4 条; K1 三候选 profile 派生 process_sandbox 与证据 none 矛盾, 均靠证伪者抓出) | SKILL.md R3.5 签收段无级联/口径条款 | P3 | SKILL.md R3.5 签收段: 签收清单含 claim 级联预推演 + containment/attacker_tier/severity 口径一致性核对 | SKILL.md R3.5 段 |
| D-4 | 修复族密集目标预期管理 (第 5 条; K1 14/16 UNREACHABLE = 预期形态) | fixminer 条款 (SWR-V3.32-002) 无预期管理句 | P3 | fixminer 条款增一句: 快照含全部近期修复时低 REACHABLE 率是预期, 价值=变体残留+兄弟路径 | SKILL.md R2 fixminer 段 |
| D-5 | 双栏呈现 (第 6 条) | 佐证注记机制已在位 (correction_record 渲染); 双栏是写作形态可推导 | **裁除** | 裁除理由: 义务四问④命中 (可推导知识不入库); 已存在机制 (NEEDS_REVIEW 佐证注记列) | — |
| D-6 | 「全覆盖」断言与配置前提是 UNREACHABLE 误判高频翻转维度 (第 7 条; K1 复活 4/9 三形态: 未枚举子集/配置分支/守卫窗口解耦) | step 4 guard_pass_subsets 枚举义务已在位 (SWR-V3.20-004); 缺「子集清单自洽声明」+「配置分支语义核查」 | P3 | step 4 增两句: (a) 声明「全覆盖」前必须列子集清单 (residual note 自认未核查=自相矛盾形态); (b) 配置/构建前提分支的语义核查——标注分支不可达前先核查该分支下防御前提是否成立 | tools/batch_verify.py _build_prompt step 4 |
| D-7 | 同项目多批次归档约定 (本会话 Q2; K1 顶层 40+ 产物与 K2 重写碰撞) | SKILL.md 无同项目续批条款 (「批次选题」是多项目, 非同项目续批) | P4 | SKILL.md R0 节末尾: 同项目多批续审时批前归档 .audit_results/batch_<N>/ (报告/教训/队列/波次注册表), 新批从干净顶层重跑 | SKILL.md R0 节 |

## 义务四问逐项 (v3.43 第四问)

- D-1a: ① r35n-collect 运行时; ② gate ③c (阻断掩蔽) + 主代理 (warn 名单); ③ 裁掉丢 gate ③c 实际效力 (presence 检查可被簿记满足); ④ 不可推导——掩蔽洞是机制缺陷非知识缺位。建。
- D-1b: ① 复活波导出时; ② 主代理; ③ 丢 K1 返工形态 (补派第二波); ④ 可推导但 K1 证明推导不可靠 (偏离实录)。建 (提示级一行)。
- D-2: ① verifier 写首发断言时; ② verifier/主代理申报; ③ 丢 CAND-016 类归因错误; ④ 检索义务是动作要求非知识。建 (提示级)。
- D-3: ① 签收 strengthened/attribution 时; ② 主代理; ③ 丢 K1 两次签收后返工 + 口径矛盾三例; ④ 部分可推导, 但清单化防漏。建 (提示级清单)。
- D-4: ① fixminer 密集目标批次开题; ② 主代理预期设定; ③ 丢收官时误判发现力; ④ 可推导——但一句成本极低, 防重复误判。建 (一句)。
- D-5: 裁除 (见上)。
- D-6: ① verifier 写「全覆盖」/配置前提时; ② verifier/复活波; ③ 丢 K1 三次复活形态复发; ④ 不可推导 (verifier 断言惯性恰是缺陷本体)。建 (提示级两句)。
- D-7: ① 同项目多批续审开题; ② 主代理; ③ 丢 K1/K2 产物碰撞 (40+ 文件); ④ 归档布局约定不可推导 (决策非知识)。建 (提示级一行)。

## 开发序列与验证命令

P1: D-1a (batch_verify) → P3: D-2/D-6 (batch_verify prompt) + D-1b/D-3/D-4/D-7 (SKILL.md)
→ P4: 版本链五件 (TOOLING 3.44 / 版本守卫测试 / SKILL.md 增量段 / TRACKING / 资产计数)
→ 测试: tests/test_v344.py + 全量回归 + 旧队列复跑 + selfcheck。

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/test_v344.py tests/test_v343.py -x -q   # 新用例+冻结守卫
python3 -m pytest tests/ -x -q                                  # 全量
python3 tools/batch_verify.py /root/gpac --stage coverage-ledger --write=false 2>&1 | tail -3  # 旧队列零新增
python3 src/signature_lib.py selfcheck /root/linux              # 通用性
```
