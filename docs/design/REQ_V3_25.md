# REQ V3.25 — MaintainWise 验收审计复盘缺陷修复

日期：2026-09-06。驱动：v3.24 阶段 6 验收审计（MaintainWise）lessons 5 条 +
用户"R1-R6 重复功能裁剪"追问取证（4 候选经代码核实裁除 3、降级 1——裁决记录
见下）。DDL 消化：MaintainWise lessons §一.1-5 全部入库，§一.6/§二 保持。

## 缺陷清单（代码核实完成，编辑点行号实测）

| # | 缺陷（代码核实） | 修复 | 编辑点（实测） |
|---|---|---|---|
| D-1 | verify 导出 payload 内嵌 prompt 不 taskFile 化——111KB 超 Workflow args 上限, 主代理手工转封装（v3.22 D-9 只覆盖 refutation/resurrect, 取证: export_script verify 分支 payload.append 内嵌 prompt, resurrect 分支已 taskFile 化） | P1: verify 分支默认 taskFile 化（与 resurrect 同契约） | `workflow_export.py:683-129`（export_script verify 分支 payload 构建） |
| D-2 | r35-collect 只认 workflow journal——Mode A' 证伪需主代理合成 journal.jsonl（本审计手工合成 88 行实录） | P2: 接受 A' 证伪 JSON 目录（journal 缺失时 glob `_refute_*.json`）+ CLI `--from-refute-files` | `batch_verify.py:1416`（stage_r35_collect 决策装载段）+ `:3220`（CLI） |
| D-3 | verifier 任务书无路径穿越编码矩阵义务——"编码不穿越"误判被证伪者+主代理实测双重推翻（%2e%2e/%2F/混合编码全穿越, 仅 %252e 双编码不穿） | P3: 步骤 5 路径覆盖补编码矩阵固定维度条款 | `batch_verify.py:2877+`（_build_prompt 步骤 5） |
| D-4 | r3_link 同事实去重后 R4 申报 severity 丢失——CAND-018/014 两处需手工 override（R4 双假说 Critical 事实落 中/高） | P2: r4-collect 落盘时 R4 severity > 候选机械值时 warn 建议 override（不自动改写） | `batch_verify.py:1158+`（stage_r4_collect, 复用 severity_for:1784） |
| D-5 | storage 域任务书无预置数据文件面——工作树预置库（admin FCP=0+公开默认口令）成为 linux_local 首启接管路径 | P3: surface 模板补条件段「预置数据文件面指引」（storage 域注入） | `task_templates/surface_map_domain.md`（生成器/模板产物面指引之后） |
| D-6 | R5 核取代理重复实测 R4/verifier 已有数字（23 条 backfill 大半为转写）——执行层冗余 | P3: SKILL.md R5 补提示句「补测前先核取已有实测数字」（backfill 规范已允许, 明示即可） | `SKILL.md` R5 回填规范段（v3.24 抽验句后） |

案例支撑来源（逐条会话内实录）：
- D-1/D-2：v3.24 验收审计（MaintainWise）——workflow 8 候选 API ENOTFOUND →
  A' 降级 + 111KB payload 手工 taskFile 化 + 合成 journal 88 行；
- D-3：CAND-014 verifier 精度修正被 refuter-1 补强与主代理六形态矩阵实测
  双重推翻（483,328B cmp 一致）；
- D-4：CAND-018（R4 H-7-F1 Critical 同事实）与 CAND-014（R4 H-5-F1/H-6-F1
  Critical 同事实）两处 severity_override 手工补写实录；
- D-5：H-7-F4/H5 实测——预置 maintainwise.db admin FCP=0+checkpw=True
  首启免改密直登 ADMIN；
- D-6：R5 核取代理 56 tool uses 中大半为复测已有数字（其回执自述"引用
  R4/verifier 实测"）。

## 用户追问取证裁决记录（2026-09-06，"R1-R6 重复功能裁剪"四候选）

| 候选 | 取证结论 | 裁决 |
|---|---|---|
| r3_link 实证自动传递 | backfill 规范（v3.4.3-061）已允许 verifier 证据引用实测数字；重复实证为执行层冗余 | 降级为 D-6 提示句 |
| CK-* 与 H5/H7 清单合并 | CK 条目自带「(H7③ 同族)」显式交叉引用, 是注释化单一事实源；合并只增耦合 | 裁除 |
| legacy SKILL_LESSONS_*.md 清理 | lessons_recorder.py:132 仍主动写该路径（R6 机械骨架）；旧文件为战役期追溯档案 | 裁除 |
| signature_id/sources 降级 | signature_lib.py:361 retire_low_contribution（SWR-V3.1-052）为活消费者 | 裁除 |

## DDL 消化状态

- MaintainWise lessons §一.1→D-1、§一.2→D-2、§一.3→D-3、§一.4→D-4、
  §一.5→D-5 全部入库；§一.6（正向确认）保持不入运行时；§二（审计自身教训）
  不入运行时 ✓
- v3.24 遗留：无（阶段 6 验收审计已完成）

## 开发序列

P1（D-1）→ P2（D-2/D-4）→ P3（D-3/D-5/D-6 + test_v325）→ P4 版本链五件
（TOOLING 3.25 / 版本守卫 ×15 / SKILL.md 增量段 / tracking 手工段 /
gen_tracking VERSIONS）→ 阶段 4 测试 → 阶段 5 安装提交 → 阶段 6 验收审计
（未审计新项目, 候选待定）。

## 验证命令

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
# 旧队列复跑: v8/WebKit/firefox/MaintainWise assert_ledger 零新增告警
bash install.sh
```
