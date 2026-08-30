# SWR V3.15 — 设计规则（2026-08-30）

每条对应 REQ_V3_15 修复项，标注裁决理由与测试守卫。

## SWR-V3.15-001（D-1 报告守卫双形态）

stage_report 防覆盖判定同时识别「（主代理补充）」与「本段由主代理补充」双形态；
机械模板第三节占位文案补「（主代理补充）」标记。理由：模板占位与守卫判定
语法不一致是四次 REFUSED 的根因（batch_verify.py:1704 实测）。测试：未编辑
模板重跑不 REFUSED。

## SWR-V3.15-002（D-2 统一 claim 判定函数）

新增 `is_claim_like(cand, fields=("claim_type","evidence","summary"))`（落
evidence_ledger.py，workflow_export 导入）：① claim_type 非空且命中
EMPIRICAL_CLAIMS → True；② 否则字段集文本扫描命中 → True（降级 fallback）。
resurrect_pool 与门禁③c 同调此函数、同字段集（pool 不再额外带 sink_type——
字段差是三次漏选的机械根因）。理由：两处义务（复活义务、池选样）必须同判定。
否定语境词（"无 RCE"）行为两处一致即可——统一优先于否定语义精化。测试：
两处等值（含 sink_type 差与否定语境词用例）。

## SWR-V3.15-003（D-3 R4 枚举建议映射）

r4-collect 的 R4_ENUM_WARNING 附结构化建议映射：verdict 非法（NO_REACHABLE_CONFIRMED/
NOT_CONFIRMED/未确认类）→ 建议 reviewed_clean；severity informational → 建议 low。
只建议不自动改写（D-4 先例：误猜风险>收益，且 v3.14 计划已裁自动改写）。
测试：告警输出含建议映射字段。

## SWR-V3.15-004（D-4 post-resurrect advisory）

export_script refutation 结果附 `post_resurrect_advisory`：带 re_verify_gap 且
verdict=REACHABLE 且带 refutation 字段的候选清单（陈旧字段致资格排除）+ 归档
refutation_history 指引。理由：libarchive 静默空转实录；提示级非强制。

## SWR-V3.15-005（D-5 截断 key 集扩展）

_TRUNC_KEY_HEAD 扩展三形态：① 方括号段头 `^\[(?:G\d+|PREC-[\w-]+|CK-[\w-]+)\]`
② 平文 `^VERDICT` ③ `^复活 gap 逐条核实`。全 minor 首尾拼接兜底保留（热修）。
理由：verifier 证据的段落形态本批已出现三类未被识别形态。测试矩阵：方括号
段头保留/全 minor 首尾拼接/单段无 key 头/既有【】头不回退。

## SWR-V3.15-006（D-6 tracked_surfaces 契约）

hypothesis_tracked_surfaces canonical=字符串 id 列表；富形态（{surface_id,
verdict, evidence}）改 sweep_records 承载；_tracked_ids 容忍 dict 条目提取
surface_id（热修保留）。理由：渲染器与门禁⑦ 消费字符串；富形态有证据价值
但不污染 canonical。测试：双形态 _tracked_ids 输出一致。

## SWR-V3.15-007（D-7 scope_diff 消费契约）

scope_reopen_advice 优先消费 diff["affected_dirs"]（机器通道）；changes 字符串
解析降级 fallback（_chg_dir 保留）。surface_mapper.py docstring 补契约注：
changes 为人读描述（字符串），机器消费走 affected_dirs。理由：生产者设计形态
不变，消费者契约化。测试：affected_dirs 优先路径 + 字符串 fallback 路径。

## SWR-V3.15-008（D-8/D-14 模板条款）

biz_hypothesis 模板加 canonical 字段名条款（一行）；surface_map_domain 模板加
空域签收条款（域空输出 {"surfaces":[]} + 空域理由，主代理签收
empty_domain_reason）。理由：agent 漂移的两个高频缺口（gpac H2 自报失真、
freetype 网络空域自发行为）。测试：模板文案存在断言。

## SWR-V3.15-009（D-9 CK-EMPIRICAL-SCOPE 基线对照条目）

checklist_library CK-EMPIRICAL-SCOPE steps 增一条：资源类（oom/unbounded/
protocol_dos）实证必须双测——对照组（无攻击输入/基线运行）+ 攻击组，报告
基线值与增量；单次读数不可作证据。理由：gpac CAND-001「27,000x 放大」为
~105MB 基线伪影实录。绑定不扩（该 CK 已绑定 R5/verifier）。测试：清单条目
文本存在断言。

## SWR-V3.15-010（D-10 PREC-GUARD-SUBSET-001）

precedent_library 新增 PREC-GUARD-SUBSET-001：阻断主张「守卫封顶/上限已封」
必须枚举守卫通过子集（文件真实包含声明尺寸/自动切换 tier/重试路径/配置档位），
不得只实证拒绝路径。绑定词：守卫/封顶/上限/有界/拒绝。理由：gpac CAND-007
（短读守卫被真实内容绕过）+ CAND-001（1MB 档 AUTO→TCP_ONLY 自动切换）双实录。
形态=自证伪提示（提示级，非强制字段）。测试：匹配词命中注入断言。

## SWR-V3.15-011（D-11 CK-VENDORED-CONTRACT）

checklist_library 新增 CK-VENDORED-CONTRACT：绑定依赖库/第三方 vendored 解析器
的契约检查列为阻断维度（库侧缺校验 ≠ 缺陷成立——先查绑定层契约：llhttp 状态机
转移/openssl 低阶点拒绝/对等端校验等）。绑定词：vendored/llhttp/绑定/libcrypto/
第三方。注入 verifier/证伪者（checklist 绑定机制）+ 复活者维度清单追加一行。
理由：nghttp2 llhttp 死代码误判 + s2n-tls 绑定层两次生效实录。测试：清单条目
存在 + 复活维度清单文本断言。

## SWR-V3.15-012（D-12 未测平台清单一行）

verifier 任务书 PTM 注入块追加一行：平台条件性前提（32 位回绕/LLP64/平台 API）
必须显式列「未实测平台/构建清单」，供复活波定向补测。理由：freetype CAND-002
复活者自发补测实录（强制 32 位类型重建+ASAN）。提示级。测试：注入文本存在断言。

## 版本链与守卫

TOOLING_VERSION → "3.15"（workflow_export.py:22）；SKILL.md v3.15 增量段 +
D-13/D-14 文案；test_v310.py:276 / test_v312.py:180 / test_v313.py:191 /
test_v39.py:266 → "3.15"；gen_tracking VERSIONS 登记 + REQUIREMENTS_TRACKING
手工段。新增 tests/test_v315.py（约 15 用例，见 REQ_V3_15 测试守卫约束节）。
