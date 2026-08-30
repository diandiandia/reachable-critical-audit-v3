# REQ V3.16 — v3.15 验收审计复盘缺陷修复（2026-08-30）

## 上下文

v3.15 验收审计（frameworks/av，零 clone 约束）暴露 5 项缺陷，全部经代码
取证核实（编辑点行号为 dev 树实测），案例支撑全部为 av 批次会话内实录
（lessons.md/队列/反驳波输出）。按惯例不改阶段骨架、六门禁判据语义、队列
数据模型主体。原拟第 6 项（collect 边缺口）取证后确认 SWR-V3.10-006 已
覆盖——裁除（过设计防线）。

## 修复清单（5 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | 零实证环境批量裁决无机械辅助——av 批 11 条同构理由（~200 字骨架）手工逐条写（gate ③ 只给 violations 裸清单） | 队列/门禁支持 `audit_constraint`（如 no-build）→ gate ③ 对约束下未实证的实证类 REACHABLE 输出结构化批量 demote 建议（统一理由模板 + 建议清单），主代理逐条确认落盘；建议级非自动改写 | evidence_ledger.py:250-258（gate ③） |
| D-2 | R4 verdict 枚举逃逸四连（H2 REACHABLE/H4 CONFIRMED/H5 REACHABLE/H6 UNREACHABLE）——任务书「三选一」提示无约束力；D-3 建议映射接住但根因未除 | biz_hypothesis 模板输出契约段枚举加粗 + 附反面示例（"REACHABLE/UNREACHABLE 不是 R4 verdict 值"）+ r4-collect 告警文案引用模板行 | task_templates/biz_hypothesis.md:55/112 |
| D-3 | 首判量级归因系统性低估 1-3 数量级（CAND-004 SSRC 源对象 ~10MB vs 真实 192KB/Stream 急切缓冲 36,000x；CAND-009 Program 对象同构）——verifier 只算顶层对象尺寸 | CK-CHECKPOINT-AFTER-ACCUM steps 增「构造器链急切分配」条目：无界计数类候选的量级必须以对象图内部急切分配为准（成员缓冲/嵌套对象），不得只算顶层对象尺寸 | resources/checklist_library.json（CK-CHECKPOINT-AFTER-ACCUM） |
| D-4 | 树外平台门禁是反驳第一来源（CAND-013 Java fd 重定向→scheme 大小写变体契约；MediaHTTPService 调用方提供；SELinux 域）——多树/框架树审计任务书未列树外层清单 | verifier 任务书（PTM 注入块后）加树外层清单条款：多树目标必须显式列「树外层清单」（绑定库/框架语言层/系统策略层），阻断论证引用树外门禁须写层名与契约（提示级） | workflow_export.py:710-716（注入块） |
| D-5 | dev/installed 双副本账本漂移——coverage-ledger 写往被调用副本（sources 分歧 4 键实录，主代理机械并集修复） | coverage-ledger --write 落盘后检查另一副本存在且 sources 一致，不一致输出 LEDGER_COPY_DRIFT warn（附并集修复指引）；不自动改写 | tools/batch_verify.py:1516（写入后） |

## 版本链 v3.16

- workflow_export.py:22 TOOLING_VERSION → "3.16"
- SKILL.md v3.16 增量段
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、test_v39.py:266、test_v314.py:219 → "3.16"
- gen_tracking VERSIONS 登记 + REQUIREMENTS_TRACKING 手工段（禁再生成）

## 开发序列

- **C0**（本文档集）：REQ + SWR + SYSTEM_DESIGN + SOFTWARE_DESIGN + BIAS_EVAL
- **P1 机械**：D-1（audit_constraint 建议）+ D-2（模板枚举强化）+ D-5（账本漂移 warn）
- **P2 内容**：D-3（清单条目）+ D-4（树外层条款）
- **P3 版本链+测试**：TOOLING 3.16 + SKILL.md 增量段 + 守卫 5 处 + tracking + test_v316.py + 全量回归 + 旧队列复跑零新增告警（gpac/freetype/av）+ install 同步

## 测试守卫约束

- 必须保持绿：tests/test_v315.py 19 用例全量、test_v314.py、test_evidence_ledger.py（门禁名不增）、test_doc_lint.py（资产计数不漂移）、test_v39.py:253（清单 39 条）
- 新增 tests/test_v316.py（约 7 用例）：D-1 建议输出（约束命中/未命中/自动不改写三分支）/D-2 模板反面示例文案存在/D-3 清单条目文本存在/D-4 注入条款文本存在/D-5 漂移 warn 与一致零 warn/TOOLING 3.16

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck <非 fixture 项目>
# 旧队列复跑: /root/gpac /root/freetype /root/av 六门禁零新增告警
# 禁止: python3 tools/gen_tracking.py
```
