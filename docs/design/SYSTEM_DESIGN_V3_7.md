# v3.7 系统设计：审计报告格式重构（问题清单按严重程度排序 + 机械生成 + 附录化）

> 日期：2026-08-23。来源：用户要求重新设计 `reachable_vulnerabilities_report.md`
> ——「简单明了的说明有哪些代码问题，按照严重程度排序，提供相关细节」。
> 基线：HEAD `1efc456`（v3.6），204 测试全绿。

## 1. 背景与三项决策

旧报告（SKILL.md v3.6 报告段）规定「必须含什么」却**不规定排序与生成方式**——
主代理手工拼装，段落顺序随人而异，严重程度靠人工判断不可问责。用户三项决策
（AskUserQuestion 确认）：

1. **严重程度定级 = 机械映射**（cwe/claim_type → 严重/高/中）+ 主代理可覆盖
   （`severity_override` 字段 + reason）；
2. **生成方式 = 扩展 `--stage report` 机械生成完整报告**（队列派生，REQ-V3.3.2-007
   唯一事实源原则），主代理只补修复建议/结论；
3. **审计过程信息**（规模对照/语言覆盖表/六门禁/R4 假说表）**移入附录**——
   正文只讲「有哪些代码问题 + 多严重 + 细节」。

## 2. 严重程度机械映射（SWR-V3.7-001）

### 2.1 分级表按账本族论证

`SEVERITY_BY_CWE` 的族划分与覆盖账本（`resources/issue_coverage_matrix.json`）
的 CWE 族分组同源，保证选题粒度与报告分级粒度一致：

| 级别 | 账本族（CWE） | 论证 |
|---|---|---|
| 严重 | 注入/反序列化（78/94/77/502）+ MEMORY-SAFETY（787/125/416/415/476/190/129） | 注入=远程代码执行面（CWE-78/77/94）+ 反序列化（502）直接代码执行；MEMORY-SAFETY 全族在非内存安全语言即任意代码执行/越界读写（CVSS 高危惯例） |
| 高 | SQLi/路径/SSRF（89/74/22/918）+ 鉴权主体（862/863/639/306）+ RESOURCE-DOS（400/770/789/409/833/834）+ RACE（362/366/367） | 数据泄露/越权/拒绝服务主体；鉴权缺失（862/863/639）是越权根因；RACE 条件常为 UAF 前提 |
| 中 | XSS/弱鉴权（79/601/352/285/287/926）+ CRYPTO/DATA-INTEGRITY（327/326/338/347/330/310/311/295/345/351/829） | 非内存破坏、需交互/降级类（XSS 需浏览器侧；弱鉴权 285/287/926 依赖上下文；CRYPTO 弱化类 327/326 等） |

优先级链：`severity_override`（合法值 {critical,high,medium} + reason）>
cwe 映射（candidate.cwe **列表** + sink_type 全量 `CWE-(\d+)` 提取取 max）>
claim_type 回退（rce/leak→critical，crash/panic/oom/unbounded/protocol_dos→high，
xss→medium，对齐 EMPIRICAL_CLAIMS 8 类与 REQ-V3.4.3-006 leak→critical）>
medium 默认。override 非法值 → 回退机械值 + 渲染告警行（source="invalid_override"）。

### 2.2 数据源核查（Plan agent 验证）

- `summary` 字段 collect **不落盘** → 问题摘要改用 `claim_type + evidence 首 120 字符`；
- cwe 在真实队列中是**列表**（puma 实录 `['CWE-770','CWE-400']`），`_parse_cwes`
  同时扫 cwe 字段与 sink_type；
- `coverage_bridge` 在真实队列中**实际存在**（puma 19 条）→ `_tracked_ids` 必须
  容忍消费（SKILL.md:247 旧文称已删与实况不符——勘误记 SWR_V3_7）。

## 3. render_report_md 结构与铁律（SWR-V3.7-002~006, 008）

`--stage report` 末尾（stdout 纯 JSON 打印后）机械渲染
`.audit_results/reachable_vulnerabilities_report.md`；写入状态打印到 **stderr**
（保住 stdout 纯 JSON 契约——test_report_outputs 整段 json.loads）。

- **一、问题清单**（REACHABLE only，严重→高→中三节）：`ID | 问题摘要 |
  位置 file:line | CWE | 证据等级 | 复核(证伪者结果/未复核)`；行内渲染 severity
  来源（cwe:/claim_type()/override/default）→ 可问责（REQ-V3-006）
- **二、问题详情**（每条一节）：位置/语言、CWE/claim_type、verdict+证据分级
  （grade_recomputed_by 如有）、调用链逐跳+depth+reachability_type、证据、
  blocking_point 前提（PREC-CONDITIONAL-REACHABLE-001）、独立复核 refutation{}、
  实证记录 empirical{}、修复建议（R4 finding fix 命中——含 r3_link 同事实共享，
  SWR-V3.4.3-060；否则「（主代理补充）」）
- **三、修复建议与结论（主代理补充）**：占位段；补充后**不得重跑 --stage
  report**（机械渲染覆盖）——规范写入 SKILL.md
- **附录 A**（REQ-V3.1-092）：NEEDS_REVIEW 成因双分（`_needs_review_cause`
  关键词启发式：保守/防御充分→保守裁决；证据不足/无法取证/前提无法/调用边
  无法→证据不足；else 未注明交主代理确认）+ correction_record 理由 + 同事实
  映射行
- **附录 B**：B.1 规模对照（闭合率=终态/总数）→ B.2 语言覆盖表（组件角色由
  `surface_mapper.language_inventory(project_root)` **现场重算**——未持久化于
  input_surface，已核实）→ B.3 FFI 边界表（boundary_kind/lang_pair surfaces）→
  B.4 R4 verdict 表（r4_findings 原样渲染）→ B.5 六门禁断言（`assert_ledger`
  机械调用渲染 ①-⑧+③c，未过 → FAIL 行；断言失败兜底降级不阻断报告）→
  B.6 覆盖账本（复用 coverage_ledger JSON 渲染 gap/pressure cells，REQ-V3.4-007）

**铁律：所有可选输入（input_surface/hypotheses/r4_findings/target_kind）缺失时
降级渲染占位，绝不抛异常**（test_end_to_end 最小队列形态实测缺全部）。
渲染失败兜底：stage_report 捕获异常打印 `REPORT_MD_ERROR` 到 stderr，JSON
报告不受影响。

## 4. stage_collect 透传（SWR-V3.7-007）

cwe 拷贝块后加：

```python
if v.get("severity_override"):
    entry["severity_override"] = v["severity_override"]
    entry["severity_override_reason"] = v.get("severity_override_reason", "")
```

主代理也可直接编辑队列 JSON（队列唯一事实源）。数据模型速查补
`severity_override∈{critical,high,medium}?, severity_override_reason?`。

## 5. 义务入库三问（severity_override / 映射表 / render 函数）

| 义务 | 触发条件 | 消费者 | 裁掉丢什么 |
|---|---|---|---|
| severity_override 字段 | 主代理认为机械分级与真实影响不符（仅 REACHABLE 语境） | render_report_md 排序 + 行内来源渲染 | 悔例=机械表漏族（新 CWE 未分组）时无逃生口，主代理只能改队列证据伪造 |
| SEVERITY_BY_CWE 表 | 任何 REACHABLE 候选渲染 | 问题清单排序 + 详情来源行 | 悔例=人工排序不可问责（用户本次要求的直接动机） |
| render_report_md | 每次 `--stage report` | 用户/读者；主代理补充段 | 悔例=报告段落随人而异、无机械可复现性 |

## 6. 测试（tests/test_v37_report.py ×10）

1. severity 映射优先级（override > cwe max > claim_type > default + source 返回）
2. 非法 override → 机械值 + md 告警行
3. 全流程六段结构 + stdout 仍纯 JSON
4. 严重节在高中前；NEEDS_REVIEW 不进清单进附录 A 带成因+映射行
5. 最小队列降级不抛异常 + 占位文本
6. 六门禁表 ①-⑧+③c 渲染，PENDING → FAIL 行
7. 去项目化（REPORT_BLACKLIST = DEPROJECT_BLACKLIST + 已知项目名，零 /root/）
8. stage_collect 透传 severity_override/severity_override_reason
9. 语言覆盖表角色列（server-side/client-only/build-config）
10. _tracked_ids 合并 hypotheses ∪ r4 tracked_surfaces ∪ coverage_bridge

既有锁不动：test_report_outputs（stdout 纯 JSON）/ test_end_to_end（最小队列
形态）保持原样全绿。

## 7. 版本链 v3.7

1. 本文件 + SWR_V3_7.md 双件套
2. SKILL.md 三处：报告段重写 / 数据模型速查补字段 / 文末 v3.7 增量段
3. `workflow_export.py:22` TOOLING_VERSION "3.6" → "3.7"
4. REQUIREMENTS_TRACKING.md 手工追加 SWR-V3.7 段（gen_tracking 只覆盖到 V3.4，
   v3.4.5+ 段均手工维护——已核实）

## 8. 验收（Phase 3.7）

1. pytest 全绿（204 基线 + 10 新增 = 214）
2. `signature_lib.py selfcheck /root/phpseclib` exit 0（未动签名资产，防回退）
3. puma 真实队列临时副本冒烟（`--stage report` 渲染到**临时副本**，不覆盖
   既有报告），人工检查分级/排序/附录真实性
4. ./install.sh → DST pytest 全绿
5. 分阶段 commit（P1 渲染+测试 → P2 文档+版本链）

## 9. 关键风险

- **R1**：stdout 契约破坏（test_report_outputs 整段 json.loads）→ 状态打印走
  stderr，渲染异常捕获兜底（已做）。
- **R2**：降级铁律被破坏（test_end_to_end 最小队列实测缺全部可选输入）→
  所有可选输入读取带 try/except + 占位渲染（已做）。
- **R3**：cwe 形态漂移（list vs str）→ `_parse_cwes` 双扫 cwe + sink_type
  全量正则提取，形态无关（已做）。
- **R4**：coverage_bridge 渲染契约（SKILL.md 旧文称已删）→ 渲染侧按实况容忍，
  勘误记 SWR_V3_7（已做）。
- **R5**：去项目化——模板静态文本 + 渲染内容零项目名零 /root/，测试断言
  REPORT_BLACKLIST（已做）。
