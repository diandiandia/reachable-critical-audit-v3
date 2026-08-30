# SWR V3.16 — 设计规则（2026-08-30）

## SWR-V3.16-001（D-1 audit_constraint 结构化建议）

候选携带 `audit_constraint`（枚举如 no-build/no-device/tree-incomplete）时，
gate ③ 对「约束下未实证的实证类 REACHABLE」除 violations 外输出
`suggestion: batch_demote`——含统一理由模板（引用约束语义）+ 受影响 id 清单。
主代理逐条确认落盘（evidence_ledger.commit 现状路径），**不自动改写**。
理由：av 批 11 条同构手工降级实录。测试：约束命中输出建议/无约束零输出/
门禁判据不变（violations 仍阻断）。

## SWR-V3.16-002（D-2 R4 verdict 枚举强化）

biz_hypothesis 模板输出契约段：三值枚举**加粗** + 反面示例行
（"REACHABLE/UNREACHABLE/NEEDS_REVIEW 是 R3 候选 verdict，不是本假说
verdict；本假说仅 confirmed/reviewed_clean/not_applicable"）。
r4-collect 的 R4_ENUM_WARNING 文案附模板行指引。理由：av 四文件全逃逸
实录——提示无约束力的根因是位置/醒目度。测试：反面示例文案存在断言。

## SWR-V3.16-003（D-3 构造器链急切分配条目）

CK-CHECKPOINT-AFTER-ACCUM steps 增条目：「无界计数类候选的量级必须以对象图
内部急切分配为准——枚举构造器链的成员缓冲/嵌套对象（每 Stream 192KB 急切
缓冲实录, 顶层对象尺寸低估 3-4 个数量级），量级声明写最大成员分配」。
理由：CAND-004/009 反驳轮量级修正实录。测试：条目文本存在断言。

## SWR-V3.16-004（D-4 树外层清单条款）

verifier 任务书 PTM 注入块后追加：多树/框架树目标必须显式列「树外层清单」
（绑定依赖库/框架语言层如 Java 门禁/系统策略层如 SELinux 域），阻断论证
引用树外门禁时须写层名与契约（提示级；树外层不可枚举时如实注明）。
理由：CAND-013 Java fd 重定向→scheme 大小写变体是反驳最高价值修正实录。
测试：注入文本存在断言。

## SWR-V3.16-005（D-5 账本双副本漂移 warn）

coverage-ledger --write 落盘后：若检测到另一 skill 副本（dev/installed 双活
形态）的 issue_coverage_matrix.json 存在且 sources 不一致 → 输出
LEDGER_COPY_DRIFT warn（附并集修复指引），不自动改写。
理由：4 键漂移实录。测试：漂移 warn 与一致零 warn 两用例。

## 版本链

TOOLING_VERSION → "3.16"；SKILL.md v3.16 增量段；守卫 5 处（test_v310:276/
test_v312:180/test_v313:191/test_v39:266/test_v314:219）；gen_tracking
VERSIONS 登记 + REQUIREMENTS_TRACKING 手工段；tests/test_v316.py 约 7 用例。
