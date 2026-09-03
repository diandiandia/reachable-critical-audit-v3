# REQ V3.21 — WebKit 审计复盘缺陷修复·第二批次（2026-09-03）

## 上下文

v3.20 已入库 WebKit lessons.md §一补第 5/6 条；本版入库 §一补第 7/8/9 条
（S3 探针→可行性路由 / S4 R1 矛盾扫描 / S5 lessons 回填断链），完成 WebKit
批次全部报漏条目的消化。缺陷全部经代码取证核实（2026-09-03 会话）：
env_probes.json 全库零消费者（探针条款仅在 R5 实证前触发, SWR-V3.3.2-060）；
input_surface 谓词为自由文本（26/201 条目含阻断谓词, 语义判定不可机械化）；
lessons_recorder 待回填段指向 lessons/ 历史档案（v3.16.1 已冻结"不再写入"）。

修法全部为条款级（SKILL.md/文案）+ 跨 skill 入口条款（skill-optimizer 阶段 0），
零新工具、零新阶段、零新门禁、零新强制 schema。

## 修复清单（3 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | 环境探针结果未前置于实证路径决策——env_probes 在 R0 落盘但无消费者，探针条款只在 R5"实证前"触发；WebKit 7 候选走完全量 verify+双票证伪波后在 R5 才降级 NEEDS_REVIEW，10/20=50% 预期未提前呈现给用户（补装运行库 vs 接受上限决策点不存在） | SKILL.md R0/R3 派发条款：① 探针落盘后、R3 派发前主代理输出 empirical_feasibility 表（每候选三轨 real-target/equivalent-harness/static-only，笔记级产物不强制 schema），R3 任务书按轨注入实证路径预期，R5 harness 目标清单在 R3 定 ② 探针含 no-\* 运行面缺失项时，R3 派发前向用户报预期 NEEDS_REVIEW 占比 + 三选一决策点（补装/借运行面/接受上限） ③ static-only 轨证伪票价值明示=机制静态确证（非浪费） | SKILL.md R0 探针段后 + R3 派发段 |
| D-2 | 跨阶段矛盾第二实例未制度化——R1 surface 谓词（"私网 IP 拒绝"）被 CAND-019 finding 否定，靠三轮缺口闭合人工撞见纠正；lessons 只记了 R4/R2 deflate 一例 | SKILL.md 报告定稿前条款：对每个 REACHABLE finding 检查是否否定任一 R1 surface 条目阻断谓词（拒绝/拦截/白名单/过滤/仅允许类），命中即生成 contradiction record（surface id+被否定谓词+finding 证据）并反向测绘该面；附固定 grep 命令形态机械辅助清单（谓词关键词 × finding sink 文件），不建工具 | SKILL.md 报告/收尾节（六门禁前） |
| D-3 | lessons 回填断链——lessons_recorder 渲染的"待回填"段指向 lessons/W6_MORE_LANGS_FINDINGS.md（v3.16.1 已冻结的历史档案, 不可写目标）+ 价值判定与收官无时序绑定（WebKit 29 条证据悬空至本周期） | ① recorder render 待回填段改写：价值判定必须在收官落盘 lessons.md 时同步完成，高价值条目并入「对 skill 的教训」节（skill-optimizer 唯一读入口），本文件不承载待办 ② SKILL.md R6 条款：蒸馏与收官同周期绑定 ③ skill-optimizer SKILL.md 阶段 0 增 DDL 条款：每份 lessons.md「对 skill 的教训」条目必须在本次评估缺陷清单中出现或显式裁除（附理由），不得静默跳过 | lessons_recorder.py render（:118-120）+ SKILL.md R6 节 + /root/.claude/skills/skill-optimizer/SKILL.md 阶段 0 |

## 义务入库三问

| 义务 | ① 触发条件 | ② 消费者 | ③ 裁掉丢什么 |
|---|---|---|---|
| empirical_feasibility 表 | 条件触发：R0 探针落盘后（每次审计都有探针） | 主代理 R3 派发 + R5 目标清单 + 用户决策点 | 7 候选全量波次后 R5 迟到降级 + 50% NEEDS_REVIEW 无预警（WebKit 实录） |
| 用户决策点 | 条件触发：探针含 no-\* 关键运行面缺失 | 用户（决策权在用户） | 审计产量被环境砍半且用户事后才知 |
| 矛盾扫描清单 | 条件触发：存在 REACHABLE finding 且 R1 有阻断谓词面 | 主代理报告定稿 | CAND-019 类矛盾靠人工撞见（WebKit 实录） |
| lessons 蒸馏同周期绑定 | 条件触发：审计收官 | skill-optimizer 阶段 0（唯一读入口） | 29 条证据悬空 + 报漏重演（WebKit 实录） |
| skill-optimizer DDL 消化 | 无条件：每次 skill-optimizer 启动 | 缺陷清单（阶段 0 输出） | 已落盘教训被静默跳过（V8→v3.19 之外条目零消化风险） |

## 版本链 v3.21

- workflow_export.py:22 TOOLING_VERSION → "3.21"
- SKILL.md v3.21 增量段
- 版本守卫更新：test_v310/312/313/39/314/315/316/317/318/319/320 → "3.21"
  （P4 逐处实测行号核对）
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
  gen_tracking VERSIONS 登记

## 开发序列

- **C0**（本文档集）
- **P1 机械**：D-3①（recorder render 待回填段文案）
- **P3 内容**：D-1（SKILL.md R0/R3 条款）+ D-2（SKILL.md 收尾条款）+
  D-3②（SKILL.md R6 条款）+ D-3③（skill-optimizer 阶段 0 DDL 条款）
- **P4 文档+版本链**：SKILL.md 增量段 + TOOLING/守卫/tracking/test_v3210

## 测试守卫约束

- 必须保持绿：全量 423 基线、test_evidence_ledger.py（门禁名不增）、
  test_doc_lint.py（资产计数零变化——本轮不新增计数资产）
- 新增 tests/test_v3210.py（约 7 用例，文件名避让 v3.2.1 套件 tests/test_v321.py）：recorder 渲染无"待回填"字样且无
  W6_MORE_LANGS_FINDINGS 指向 / SKILL.md 含 empirical_feasibility 条款+
  用户决策点+static-only 轨价值明示 / 含矛盾扫描条款+固定 grep 清单 /
  含 lessons 同周期绑定条款 / skill-optimizer SKILL.md 含 DDL 条款
  （路径 $HOME 探测）/ TOOLING 3.21 / 反面分支（recorder 渲染仍含"审计
  轨迹"语义、低价值条目保留路径不消失）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck /root/WebKit
bash install.sh
```

## 边界声明

- **不做**：新门禁/新阶段/新工具/新强制 schema/自动改写；empirical_feasibility
  为笔记级产物（不落 schema、不进队列）；矛盾扫描为 grep 清单辅助（语义
  判定不可机械化，主代理裁决）；skill-optimizer 侧只改阶段 0 一段条款。
- WebKit §一补五条全部消化完毕（5/6→v3.20，7/8/9→v3.21），v3.21 为
  WebKit 批次收官版。
