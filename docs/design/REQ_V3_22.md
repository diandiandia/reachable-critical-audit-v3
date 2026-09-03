# REQ V3.22 — Firefox 验收审计复盘缺陷修复（2026-09-04）

## 上下文

Firefox 验收审计（2026-09-03/04, v3.19-v3.21 联合验收）闭合后 lessons 落盘
`/root/firefox/.audit_results/lessons.md`（唯一读入口, 已按纪律读取）。
DDL 消化结果：V8 全部条目 → v3.19 已消化；WebKit §一 3/4 条 + §一补 5-9
→ v3.19/v3.20/v3.21 已消化（§一 2 条 tracked-ids 改名裁除：本次审计
111/111 零歧义, 语义已内化, 改名多消费方风险>收益；§一 1 条以 D-10 形态
吸收）；Firefox §一 6 条 + §一补 7 条 → 本版入库 10 项 + 裁除 1 项 +
正向保持 3 条。

缺陷全部经代码取证核实（编辑点行号 dev 树实测, 2026-09-04）。修法全部为
机械规则/提示级/导出形态——不自动改写 verifier 输出、无新门禁、无新阶段。

## 修复清单（10 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | size_tier 多语言提前返回遮蔽 super-large——`n_langs > 2` 分支在 `count > 2000` 判断之前返回 large, 3+ 语言大仓永远走不到两阶段测绘（Firefox 20 万文件手工绕行实录, lessons §一.1） | 分支调序: super-large 判断前移（该分支 domains_split 已用 mixed_domains, 多语言兼容零语义损失） | surface_mapper.py:787-815 |
| D-2 | claim=other 结构性可达按 CWE 机械映射虚高——34 例 claim=other 被 cwe 映射到严重/高, 主代理批量 override=medium（lessons §一.4） | _mechanical_severity 加 claim=other 封顶: claim_type=='other' 时 cwe 命中分支返回 medium + source 注明（severity_override 仍绝对优先; R4 finding 走申报值归一化不受影响） | tools/batch_verify.py:1798-1827 |
| D-3 | ~~签收字段名契约漂移~~ **取证裁除**: SKILL.md 与 r35-collect 一致用单数 `attribution_correction`, 主代理签写脚本误用复数属操作失误; 代码 :2246-2249 已双形态容忍——既有机制在位, 不重造 | 无代码修复; 数据模型速查补存储键注记（单数） | SKILL.md 数据模型速查 |
| D-4 | 复活未选中候选簿记义务无机制承载——resurrect workflow 只写 dispatched, 3 例未选中靠主代理手工补写才过 ③c（lessons §一补.12） | r35n-collect 完成后自动为 UNREACHABLE 且无 resurrection_review 的候选写 `{revived:false, outcome:"复活抽样未选中 (规则见 _resurrect_sample.json)"}`（幂等; 与抽样文件 selected 集对账, 在 selected 却无 journal 记录的不写未选中） | tools/batch_verify.py stage_r35n_collect（:609 起） |
| D-5 | refutation 任务书证据预算 800 字符致全链截断自愈 3 例——证伪者靠"见 verify_queue.json"注记自救（lessons §一补.7; SWR-V3.4.3-020 预算设计对边真实性视角不足） | evidence budget 800→3000 + chain 截断阈值 8→12（注记保留）; 根治形态见 D-9 taskFile 化 | workflow_export.py:379-384 |
| D-6 | R4 任务书缺落盘契约致 default_value_table 证据丢失——R1/R2 有落盘拦截契约, R4 没有, 主代理转写时 H4 15 行/H5 11 项/H6 8 域表被精简为 []（lessons §一补.9） | biz_hypothesis.md 加 canonical 落盘路径（`.audit_results/_r4_hN.json`, N=假说号）+ 落盘拦截契约（UNWRITTEN 标注）+ 主代理 merge 全量保留 default_value_table 条款 | task_templates/biz_hypothesis.md |
| D-7 | 用户决策点无落盘记录——v3.21 D-1 三选一决策只存于会话对话, empirical_feasibility.json 无 decision 字段, 问责链断裂（lessons §一补.10） | SKILL.md D-1 条款增: feasibility 表落盘形态含 `decision {by, date, choice}`——用户决策必须签入工件, 主代理不得代选 | SKILL.md R5 变更节 D-1 条款 |
| D-8 | ~~R4 任务书 severity 分派指引不完整~~ **取证裁除**: biz_hypothesis.md:98-103 已有分派（High/Critical 声称类 → null）——H3 写 SOURCE_FACT 源于主代理派发简写提示词与模板不一致（操作失误, 非模板缺陷）; 失败模式并入 D-11 清单 | 无代码修复 | 裁除 |
| D-9 | taskFile 薄封装未默认化——verify 波已薄封装（payload 104KB→8KB, lessons §一.6）, refutation/resurrect 导出仍内嵌全量 prompt | workflow_export refutation/resurrect 导出同形 taskFile 化（脚本已支持 c.taskFiles, 导出器落盘任务书文件 + slim payload）; SKILL.md workflow 规范条款明示薄封装为默认派发形态 | workflow_export.py refutation/resurrect 导出 + SKILL.md workflow 规范条款 |
| D-10 | 面覆盖前置纪律未固化——Firefox 假设生成阶段即 111/111 全覆盖零缺口闭合轮, 而前一验收项目缺口闭合三连重派（Firefox lessons §二.2 + WebKit §一.1 的实战吸收） | SKILL.md R2 节加条款: 假设生成完成后机械核对 hypothesis surface_ids 集合 ⊇ input_surface 全集, 缺面即补生成假设（门禁⑦ 前置化） | SKILL.md R2 节（:148-150 后） |
| D-11 | lessons 蒸馏缺失败模式清单——本轮报漏集中于跨机制契约（落盘/签收/簿记/截断）, 每轮漏同族项（lessons §一补.13） | SKILL.md R6 加蒸馏 checklist 条款: 收官蒸馏必须逐项过已知失败模式（截断自愈/契约漂移/簿记缺位/签收错名/落盘契约/决策记录/严重度映射） | SKILL.md R6 节 |

## 义务入库三问（每条新义务）

| 义务 | ① 触发条件 | ② 消费者 | ③ 裁掉丢什么 |
|---|---|---|---|
| claim=other 封顶 | 条件触发: claim_type=='other' 且机械分级 | 报告渲染（severity_for 唯一消费者） | 34 例批量手工 override 重演（lessons §一.4） |
| 未选中簿记 | 条件触发: r35n-collect 后 UNREACHABLE 无簿记 | 门禁 ③c | 主代理手工补写 + 门禁假 FAIL 重演 |
| 决策签入 | 条件触发: v3.21 D-1 决策点被触发 | 复审计问责 + skill-optimizer 复盘 | 问责链断裂（无法证明用户裁定） |
| R4 落盘契约 | 条件触发: R4 派发（每次审计） | 主代理 merge + r4-collect | 高密度防御证据丢失重演（H4/H5/H6 表） |
| 面覆盖前置核对 | 条件触发: R2 假设生成完成 | 门禁⑦ + 主代理收尾 | 缺口闭合重派轮次重演 |
| taskFile 默认化 | 条件触发: Mode W 导出 | 主代理派发 + workflow agent | 100KB 级 payload 内联成本 + 截断面 |

## 版本链 v3.22

- workflow_export.py:22 TOOLING_VERSION → "3.22"
- SKILL.md v3.22 增量段 + 数据模型速查注记
- 版本守卫更新：test_v310/312/313/39/314/315/316/317/318/319/320/3210 → "3.22"（P4 逐处实测）
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+ gen_tracking VERSIONS 登记

## 开发序列

- **C0**（本文档集）
- **P1 机械**：D-1（分支调序）+ D-2（claim=other 封顶）+ D-4（未选中簿记）+ D-5（budget/阈值）
- **P2 结构**：D-9（refutation/resurrect 导出 taskFile 化）
- **P3 内容**：D-6/D-8（biz_hypothesis.md）+ D-7/D-10/D-11（SKILL.md 条款）+ D-3 注记
- **P4 文档+版本链**：SKILL.md 增量段 + TOOLING/守卫/tracking/test_v322

## 测试守卫约束

- 必须保持绿：全量 431 基线、test_evidence_ledger.py（门禁名不增）、test_doc_lint.py（资产计数零变化）
- 新增 tests/test_v322.py（约 12 用例）：D-1 调序后 super-large 多语言路径命中 /
  D-2 claim=other 封顶 medium（含 override 仍优先反面） / D-4 未选中自动簿记 +
  幂等 + selected-无记录不写反面 / D-5 budget 3000 与阈值 12 / D-9 refutation
  导出 taskFiles 形态 / D-6 模板含落盘契约 / D-8 模板含 severity 分派 /
  D-7/D-10/D-11 SKILL.md 条款存在 / 反面分支（D-2 不改写 claim_type、
  D-4 不覆盖已有簿记）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck /root/WebKit
bash install.sh
```

## 边界声明

- **不做**：新门禁/新阶段/自动改写/新强制 schema；D-3 取证裁除（既有机制）；
  WebKit §一.2 tracked-ids 改名裁除（语义已内化, 风险>收益）。
- Firefox §一.2/3/5（正向确认）与 §二.1/3/4（审计自身教训）保持, 不入运行时。
