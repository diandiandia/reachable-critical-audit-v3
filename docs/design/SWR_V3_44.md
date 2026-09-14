# SWR_V3_44 — K1 复盘修复裁决记录

每缺陷一条 SWR。source 引用 = linux lessons.md 条目 (案例支撑义务)。

## SWR-V3.44-001 (D-1a): r35n-collect 自动簿记跳过声称类

**缺陷 (代码核实)**: tools/batch_verify.py `stage_r35n_collect` 尾部 auto-bookkeep
循环对全部「UNREACHABLE 且无 resurrection_review 且不在 selected」的候选写
`{"revived": False, "outcome": "复活抽样未选中"}`——不区分声称类。gate ③c
(evidence_ledger.py:343-353) 的判据是 `is_claim_like(c) and not c.get("resurrection_review")`
(presence 检查) → 声称类候选被簿记后 gate 即放行, 而**无任何真实复活复核发生**。
K1 实录: 初版样本漏声称类全量 7 条, 靠主代理在 collect 前跑 gate 前置自检才暴露;
若先 collect 再 gate, 簿记掩蔽使违规不可见 (linux lessons.md 过程观察2)。

**修复**: auto-bookkeep 循环对 `is_claim_like(c)` 的候选跳过 (不写簿记), 收集进
`claim_like_unreviewed` 名单, 输出附 warn: 「声称类候选无真实复活复核, gate ③c
将持续违规——须经复活波复核或主代理裁决签收」。非声称类簿记行为不变。

**裁决理由**: 修的是掩蔽洞而非抽样规则 (规则在 resurrect_pool SWR-V3.2-040 已
正确)。跳过而非自动复活 (禁止自动改写纪律——复活复核是 agent 级动作, 不能
机械代做)。warn 级不新增门禁 (过设计防线)。

**测试守卫**:
- 声称类候选 (claim_type=crash) 未选中 → collect 后无 resurrection_review + 输出含 warn 名单;
- 非声称类未选中 → 簿记照常写入;
- selected 内有 journal 记录 → 正常落盘不受影响。

## SWR-V3.44-002 (D-1b): 复活波导出纪律条款

**缺陷**: K1 主代理手写 resurrect_payload (第一波/第二波) 绕过
export_script_resurrect, 抽样决策偏离 is_claim_like 单真相 (初版漏声称类全量)。
(linux lessons.md 第 1 条)。

**修复**: SKILL.md R3.5-N 节追加一句: 复活波优先经
`export_script_resurrect` 导出 (内置声称类全量规则, 与 gate ③c 同源);
主代理手工构造 payload 时, 派发前机械对照 `is_claim_like` 清单核验
selected ⊇ 声称类集。提示级。

**裁决理由**: 导出器规则已在位; 约束的是主代理偏离形态。提示级 (执行纪律), 不
强制 (手工构造在 Mode A' 与特殊波次仍合法)。

**测试守卫**: SKILL.md 含该句 (文本断言)。

## SWR-V3.44-003 (D-2): verifier 未合并补丁检索义务

**缺陷**: step 1.5 (SWR-V3.10-011) 的佐证检索只覆盖 git log 与公开 CVE 列表;
CAND-016 verifier 据此断言「无未合并公开修复」, 而证伪者检索到 4 天前的
openwall 未合并补丁 (Zihan Xi 2026-09-09)。首发口径声明没有检索动作支撑。
(linux lessons.md 第 2 条)。

**修复**: step 1.5 尾部追加: 「无首发归属/无公开修复」类断言前, 必须执行未合并
补丁检索 (lore.kernel.org / openwall 关键词: sink 标识+子系统名)——命中则按
『非首发发现』标注; 网络不可用或检索范围受限时如实注明「检索受限」, 不得
写「无公开修复」。提示级。

**裁决理由**: 已有条款的检索范围缺口, 补一句义务不新增机制。

**测试守卫**: _build_prompt 产物含 lore.kernel.org/openwall 与「检索受限」文本。

## SWR-V3.44-004 (D-3): 签收级联预推演 + 口径一致性清单

**缺陷**: 两形态——(a) strengthened 的 claim 重评 (other→oom/unbounded) 触发
gate ③ 强制实证与 NEEDS_REVIEW 级联, K1 两次签收后才走级联 (过程观察5);
(b) containment/attacker_tier/severity 的结构化值与证据文本矛盾三例
(profile 派生 process_sandbox vs 内核上下文 none), 均靠证伪者抓出, 主代理
签收时才发现 (过程观察6)。(linux lessons.md 第 3/4 条)。

**修复**: SKILL.md R3.5 补强签收段增清单句: 签收 strengthened/
attribution_correction 前执行两级预推演——① claim 重评级联: 新 claim 是否
∈ EMPIRICAL_CLAIMS → gate ③/R5 触发 → 终态预判 (NEEDS_REVIEW 或实证计划);
② 口径一致性: containment/attacker_tier/severity 结构化值与证据文本对照
(内核/软中断上下文等 profile 派生缺省不适用场景)。提示级清单。

**裁决理由**: 签收动作已有 (回源码核实); 补的是清单化的级联/口径预检, 防
「签收后返工」。不自动改写 (仅清单)。

**测试守卫**: SKILL.md 含「级联预推演」与「口径一致性」文本。

## SWR-V3.44-005 (D-4): fixminer 密集目标预期管理

**缺陷**: K1 六子系统快照含全部 2026 修复族 → 14/16 UNREACHABLE 是预期形态;
若无预期管理, 收官时低 REACHABLE 率会被误判为发现力问题。(linux lessons.md
第 5 条)。

**修复**: SKILL.md fixminer 条款 (SWR-V3.32-002) 增一句: 修复族密集目标
(快照已含全部近期修复) 的批次预期——低 REACHABLE 率是预期而非审计失败,
价值 = 修复变体残留 + 未覆盖兄弟路径; 批次开题时按 fixminer 信号预设预期。

**裁决理由**: 预期管理是批次开题上下文, 一句成本最低。

**测试守卫**: SKILL.md fixminer 段含「变体残留」文本。

## SWR-V3.44-006 (D-6): 全覆盖声明子集清单 + 配置分支语义核查

**缺陷**: K1 四次复活 (CAND-002/005/006/007) 三形态——「全覆盖」声明建立在
未枚举子集上 (CAND-005 residual note 与声明自相矛盾)、配置分支 (CONFIG_*=n/
flag=0) 被预设不可达而未核查分支下前提、守卫窗口与写点解耦。step 4 已有
guard_pass_subsets 枚举义务 (SWR-V3.20-004), 缺声明自洽与配置分支语义两项。
(linux lessons.md 第 7 条)。

**修复**: step 4 追加两句 (提示级):
(a) 声明「全覆盖/无未枚举子集」前必须列出子集清单——自身 residual note
承认未核查与「全覆盖」声明自相矛盾是复活波命中形态;
(b) 配置/构建前提分支的语义核查: 标注「该分支不可达」前, 先核查该分支下
防御前提是否成立 (CONFIG_*=n/flag=0 分支的守护性质), 分支语义未核查的
「不可达」标注不构成阻断论证。

**裁决理由**: 复活波三形态是 K1 实测最高频翻转维度, 前置为 verifier 自检
义务比事后复活更便宜。提示级不强制 (verifier 裁决自由)。

**测试守卫**: _build_prompt 产物含「子集清单」与「配置/构建前提分支的语义核查」文本。

## SWR-V3.44-007 (D-7): 同项目多批次归档约定

**缺陷**: skill 的「批次选题规则」是多项目选题, 无同项目多批续审约定; K1
顶层 40+ 产物 (报告/教训/队列/波次注册表) 与 K2 重写碰撞 (本会话 Q2 分析)。

**修复**: SKILL.md R0 目录守卫步骤后追加提示级一行: 同项目多批次续审时, 批
前把上层产物归档 `.audit_results/batch_<N>/` (报告/教训/队列/波次注册表),
新批从干净顶层重跑 R0-R6; 归档是执行约定, 不改任何机制。

**裁决理由**: 归档布局是决策不是可推导知识; 一行提示级成本最低; 不改机制
(工具只读写顶层, 归档子目录天然隔离)。

**测试守卫**: SKILL.md R0 节含「batch_<N>」文本。

## SWR-V3.44-008 (P4): 版本链 + 冻结守卫基线推进

TOOLING_VERSION 3.43→3.44; 版本守卫测试行同步 (test_v313/test_v329/
test_v342/test_v343 等含版本断言处); SKILL.md v3.44 增量段 (列 SWR-V3.44-001..007
+ 验收判据); REQUIREMENTS_TRACKING 手工追加段 + gen_tracking VERSIONS 登记;
资产计数守卫核对 (本周期零资产条目增删, 计数不变)。

冻结守卫演进: test_v343.py `test_mechanism_freeze_scope` 的 v3.43 周期判据
(「本周期判定逻辑零改动」) 已随 v3.43 提交闭合 (K1 验收判据达成)。v3.44 起
守卫收窄为**判定逻辑守卫**: 改动的 src/tools 文件 diff hunk 头不得命中受保护
判定函数名 (assert_ledger / severity_for / grade_verdict / VERDICT_SCHEMA /
REFUTATION_SCHEMA / RESURRECT_SCHEMA / _aggregate_counts / is_claim_like)——
提示级 prompt 文本 (P3) 与簿记守卫 (D-1a) 属允许域。锚点 = v3.43 末提交
(dd967a1)。

## 裁除记录 (DDL 消化)

- D-5 (双栏呈现, linux lessons.md 第 6 条): 裁除。已存在机制 (NEEDS_REVIEW
  correction_record 佐证注记列渲染) + 义务四问④ (主代理可推导的写作形态,
  入库成本=条款密度)。
- 历史 11 份项目 lessons.md: 各周期已消化 (tracking source 追溯), 无新条目。

## SWR-V3.44-009 (P4): 同项目多批次开题四步条款

**来源**: 用户裁定（2026-09-14, 本会话 Q1 两次追问显式化需求）——同一大目标
分批次审计时每批开题按四步走：五年窗口 recon → R1 面测绘 → 批次计划文档 →
R2-R6。案例支撑: 五年窗口修复族是变体残留假设的主要来源（老修复族同款缺口
在多年后快照仍存在的批次实录）。

**修复**: SKILL.md 批次选题规则段后追加提示级条款（fixminer --since 1825 +
逐子系统五年 CVE 检索并入 upstream_recon + 计划文档三要素 + 执行）。

**义务四问**: ① 触发 = 同项目多批开题; ② 消费者 = 主代理批次开题; ③ 裁掉丢
= 开题纪律无显式载体（用户两次追问 = 需求裁定）; ④ 可推导但用户明确要求入库
——用户裁定优先于第四问默认倾向（权衡而非默认, SWR-V3.43-006）。

**测试守卫**: test_v3_44.py test_skillmd_batch_opening_four_steps。
