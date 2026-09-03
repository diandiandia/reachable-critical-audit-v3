# BIAS EVAL V3.20 — 四缺陷评估（设计期，2026-09-03）

> 实现期必须重跑（v3.16 教训：设计件零违规≠实现零违规）。

## ① 盲目带入历史审计信息

- **案例支撑**：全部五条缺陷指向 /root/WebKit/.audit_results/lessons.md
  §一补第 5/6 条（2026-09-03 补记）+ 会话内机械产物（verify_queue.json
  grade_recomputed_by ×15 / SKILL_LESSONS_WebKit.md [grade_recomputed]×15、
  [resurrection]×3 / resurrect_CAND-001.md·006.md 命中维度记录）——均为
  会话内实录，零凭记忆转述。
- **数字核实**：15/20 漂移、9 例 static_only→edge_proven、6 例实证升档
  （4 static_only→empirically_confirmed + 2 edge_proven→empirically_confirmed）
  由 python 直读队列实测（2026-09-03 会话）。
- **去项目化**：运行时正文（任务书文本/collect 输出/lessons_recorder
  detail/SKILL.md 条款）零项目名、零候选 id、零引擎名——案例只进
  source_lessons/追溯字段与设计件；测试注释允许引用（非运行时资产）。
  SWR 文案中的"复活维度 7 前移"为机制引用（维度编号是 skill 自身资产），
  非项目带入。
- 机器守卫：本轮不新增计数资产；任务书文本经 tests/test_deproject_assets.py
  PROJECT_TOKENS 扫描（既有守卫，无需扩）。

## ② 设计偏见

- **不自动改写**：全部修复为提示级/warn 级/optional schema；collect 条件
  校验只产 warnings 不跳过条目、不改 verdict、不补字段值；反面分支断言
  进测试。
- **编排便利 ≠ skill 义务**：drift_summary 是信号不是义务（主代理可忽略）；
  两字段条件触发（空数组合法），不复制"强制必填"语义。
- **修法层级**：agent 行为偏差（verifier 未结构化边证据/未枚举守卫子集）
  以任务书措辞 + 字段契约承载（容忍契约优先），不设硬失败。
- **不重造机制**：evidence_grade 机械权威已在位（SWR-V3.4.3-011）——
  D-1 只补口径明示，不动 evidence_ledger.py；edge_gap 信号（SWR-V3.10-006）
  不动。

## ③ 死代码

- **新字段消费者**（每个都有）：
  - guard_pass_subsets / premises_verified → collect 条件校验 warn +
    主代理 resurrect 派发评估 + queue 追溯落盘（三消费者）。
  - drift_summary → 主代理收波对账（collect 结果 JSON 消费）；
    lessons_recorder 不消费它（无依赖，保持解耦）。
- **新函数**：无——全部改动在既有函数内（stage_collect/_build_prompt/
  recorder issue 生成）；`_GRADE_RANK` 为模块级常量（两处引用：重算块统计）。
- **无死参数**：新参数均为函数内统计变量。

## ④ 过设计

- **无新门禁名**（warn 不进 assert_ledger）、**无新阶段**、**无新强制义务**
  （字段 optional、条件触发、warn 不阻断）。
- **义务三问**已逐项过（REQ 表）：guard_pass_subsets/premises_verified
  条件触发有明确消费者；drift_summary 零成本无条件；三值枚举为输出格式节
  固有文本修订。
- **取证裁除**：S1 原方案中的"双轨校准（任务书注入 grade_verdict 规则全文
  强制自报=机械）"经取证裁除——自报与机械的结构性时间差（collect 期回填）
  使"自报=机械"不可达，注入规则全文徒增长度；改为"仅追溯"口径明示。
  S2 原方案中的"缺失拒收（硬失败）"降级为 warn——修法形态纪律
  （建议映射/warn 优先，v3.14 D-3 先例）。
- **排队声明**：§一补 7/8/9（探针→路由 / R1 矛盾扫描 / lessons 回填 DDL）
  本版不实现——避免一版多事（v3.15 波次纪律）。

## 实现期重跑清单

- [ ] 任务书文本零项目名（grep WebKit/CAND-00x/GLib 于 batch_verify.py 新段）
- [ ] drift_summary/warnings 不落盘进队列文件（只在 collect stdout 结果）
- [ ] 反面分支测试真跑（不改写断言）
- [ ] 旧队列复跑零新增告警
