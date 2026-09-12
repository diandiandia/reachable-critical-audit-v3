# SWR_V3_40 — 每条修复一条 SWR（含裁决理由 + 测试守卫）

## SWR-V3.40-001 (D-1, P1): grade_verdict 增加 fidelity 分支

裁决理由: 判级唯一权威函数 (SWR-V3.4.3-011) 不读 fidelity, 而 SKILL.md 范围纪律
「mechanism 档不得升 empirically_confirmed」只存在于文档——文档纪律无机械承载,
Hadoop 审计主代理两例越级 (CAND-019/024), 由证伪者 harness_runner.check_scope
复现纠正。修法为判定函数一致化 (机制已有, 判定不消费), 不触及六门禁语义。
测试守卫: test_v340.py::test_grade_verdict_mechanism_fidelity——
mechanism+status=confirmed → edge_proven + errors 注记; real_target 缺省 → empirically_confirmed 回归。

## SWR-V3.40-002 (D-2, P3): verifier 任务书「步骤 3.5 攻击者字节承载判定」

裁决理由: CAND-024 证伪票原文「该链是触发器链而非数据流链」——调用链逐跳真实
但任一跳都不承载攻击者字节, REACHABLE+rce 不成立。义务形态: 提示级任务书条款,
无新门禁 (verifier 输出 schema 不变, evidence 文本承载标注)。
测试守卫: test_v340.py::test_verifier_prompt_datacarry——任务书构建输出含
「攻击者字节承载」义务段。

## SWR-V3.40-003 (D-3, P3): checklist +1 CK-SIBLING-FIX-AUDIT（修复触发型）

裁决理由: 与 CK-SIBLING-CONSISTENCY (v3.38, 端点关键词触发) 非重造——后者绑定
端点/监听/路由词汇, 反序列化 store 类不命中; 本条目触发 = fixminer 命中/公开补丁
(修复触发), 枚举同族实例加固状态差分。Hadoop 两例 (ZK vs LevelDB, 内层 vs 外层)
均为修复触发型。applies_to: verifier/main-agent。
测试守卫: test_v340.py::test_checklist_49——计数 49 + id 存在 + family 字段。

## SWR-V3.40-004 (D-4, P3): hypothesis_filter 位域证据义务

裁决理由: B5 筛选器笔记「TYPE 3bit 索引 4 值枚举」与 AclEntryStatusFormat.java
声明行 TYPE(PERMISSION.BITS, 2) 不符——判据缺少「Read 声明行」义务, 锚点错误
传导至 real_target 阶段才纠正 (真实溢出在 XAttrFormat.getNamespace)。
测试守卫: test_v340.py::test_filter_template_bitfield——模板含位域证据条款。

## SWR-V3.40-005 (D-5, P3): ENVIRONMENT_PROBES 增 setuid 辅助二进制部署拓扑段

裁决理由: CAND-001 real_target 实证的 12 轮失败日志收敛实录 (cfg 祖先 root-owned
/二进制 6750/nm_uid=真实调用者 uid/tmp 族目录属主/容器用户 work_dir) 是可复用
手册知识; 形态为内容资产增补, 无机制变更。
测试守卫: test_v340.py::test_env_probes_setuid——手册含五要素段。

## SWR-V3.40-006 (D-6, P3): hypothesis_filter 默认关方向判定

裁决理由: B2 批次 13 keep/0 drop 的根因是「防御已到位」核查不区分两种默认关方向
——feature 默认关 (RegistryDNS/ATS v2) 降可达性, 鉴权 gate 默认关
(authorization=false 使 ACL 恒真) 升可达性, 两方向裁决不可互套。
测试守卫: test_v340.py::test_filter_template_defaultoff——模板含方向判定句。

## SWR-V3.40-007 (D-7, P2): r35-collect 实证回填候选扫描

裁决理由: r35-collect 已采集 refutation 文本但只从 note 字段摘 poc_evidence,
证伪者实测数字实际落在 strengthened/reason (Hadoop CAND-010/029 实录: AXFR 4
rrsets/fd-hold 3/3 使 2 候选恢复 empirically_confirmed, 全靠主代理手工)。
形态: warn 级提示清单 (empirical_backfill_candidates), 主代理按回填规范裁决,
**不自动改写** (纪律 #4)。消费端=主代理。
测试守卫: test_v340.py::test_r35_collect_backfill_candidates——含实测数字的
refutation 输入 → 输出含提示; 无实测数字 → 空 (反面分支)。

## 义务入库三问（逐条过）

| SWR | 触发条件 | 消费者 | 裁掉丢什么 |
|---|---|---|---|
| -001 | 判级重算时 | collect/门禁③ | 范围纪律零机械承载 (本周期实犯两例) |
| -002 | verifier 派发时 | verifier | 触发器链误判 rce (CAND-024 2/2 证伪实录) |
| -003 | checklist binder 绑定 | verifier | 修复变体假设漏 2 严重候选 |
| -004 | filter 排除判据 4 | filter | 锚点错误传导至 real_target |
| -005 | harness 实证时 | 主代理 | 12 轮收敛成本每审计重付 |
| -006 | filter 排除判据 5 | filter | B2 形态 13 条方向误判 |
| -007 | r35-collect 执行 | 主代理 | 证伪者实测白丢 (2 恢复实录) |
