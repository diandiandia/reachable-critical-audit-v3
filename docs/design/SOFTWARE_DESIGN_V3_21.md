# SOFTWARE DESIGN V3.21 — 函数级设计与分层序列（2026-09-03）

## P1 机械（先做——recorder 文案，独立可测）

### lessons_recorder.render 待回填段（D-3①）

现文（:118-120）：
```
lines += ["## 待回填", "",
          "- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；",
          "  低价值条目保留在本文件作为审计轨迹。", ""]
```
改写为：
```
lines += ["## 价值判定（v3.21, SWR-V3.21-003）", "",
          "- 本文件是机械证据：价值判定由主代理在审计收官落盘",
          "  `<project>/.audit_results/lessons.md` 时同步完成（蒸馏与收官同周期",
          "  绑定）——高价值条目去项目化后并入「对 skill 的教训」节（skill-optimizer",
          "  唯一读入口），低价值条目保留本文件作为审计轨迹。", "",
          "- 本文件不承载待办事项。", ""]
```
约束：渲染模板文本零项目名、零硬编码路径（`<project>` 为占位符形态）。

## P3 内容（次做——SKILL.md 条款 ×3 + 跨 skill 条款）

### 1. SKILL.md R0 探针段后（D-1，SWR-V3.21-001）

在"环境能力探针（v3.3.2, SWR-V3.3.2-060）"条款所在的 R5 变更节之外，
在 R0 段（探针落盘处）增三句条款（措辞见 SWR）。注意：探针清单本体
（harness_manuals/ENVIRONMENT_PROBES.md）不动——改动是流程条款不是探针内容。

### 2. SKILL.md 报告定稿前（D-2，SWR-V3.21-002）

六门禁节前或报告节内增条款 + 固定 grep 清单（谓词关键词 × finding sink
文件），引用缺口闭合流程做反向测绘。

### 3. SKILL.md R6 节（D-3②）

"未执行 R6 的审计不得闭合"条款旁增：蒸馏与收官同周期绑定；SKILL_LESSONS_*.md
只作机械证据不承载待办。

### 4. skill-optimizer/SKILL.md 阶段 0（D-3③）

"必读 lesson 义务"段尾增 DDL 条款：机械清单每份 lessons.md 的「对 skill 的
教训」条目必须在本次评估缺陷清单中出现或显式裁除（附理由），不得静默
跳过——消化记录对照 REQUIREMENTS_TRACKING 最新 SWR 的 source 引用可核。

## P4 版本链（三做）

1. workflow_export.py:22 TOOLING_VERSION → "3.21"。
2. 版本守卫 ×11（test_v310:276 / test_v312:180 / test_v313:191 /
   test_v39:266 / test_v314:219 / test_v315:253 / test_v316:120 /
   test_v317:345 / test_v318:125 / test_v319:130 / test_v320 守卫行）→
   "3.21"（逐处实测行号）。
3. SKILL.md v3.21 增量段（列 SWR 号 + 验收判据）。
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking.py VERSIONS 登记。

## tests/test_v3210.py（约 7 用例，文件名避让 v3.2.1 套件 tests/test_v321.py）

- recorder: render 产物无"待回填"、无"W6_MORE_LANGS_FINDINGS"、含
  "审计轨迹"与"唯一读入口"；反面（低价值条目保留路径语义仍在）。
- SKILL.md: 含 empirical_feasibility / 决策点 / static-only 轨价值明示 /
  矛盾扫描条款 + grep 关键词清单 / 蒸馏同周期绑定。
- skill-optimizer: SKILL.md 阶段 0 含 DDL 条款（路径 $HOME 探测读取，
  断言"显式裁除"与"静默跳过"字样）。
- 反面分支: SKILL.md 新条款段零项目名（grep 项目名断言）。
- TOOLING == "3.21"。
