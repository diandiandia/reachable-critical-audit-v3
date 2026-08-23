# SWR-V3.7 修复记录（报告格式重构：机械生成 + 严重程度排序 + 附录化）

> 设计: SYSTEM_DESIGN_V3_7.md。来源: 用户重新设计审计报告格式（AskUserQuestion
> 三项决策: 机械映射+可覆盖 / 扩展 --stage report / 过程信息入附录）。
> 版本链: 本文件 + SKILL.md「🆕 v3.7 增量」段 + TOOLING_VERSION "3.7"。
> 基线: `1efc456`（v3.6），204 测试 → 214（+10）。

---

## 一、实现内容

### 1.1 严重程度机械映射（SWR-V3.7-001，tools/batch_verify.py:1246-1300）

- `SEVERITY_ORDER`/`SEVERITY_LABELS`（严重/高/中）/`SEVERITY_BY_CWE` 按账本族
  分组（critical=注入/反序列化+MEMORY-SAFETY；high=SQLi/路径/SSRF+鉴权主体+
  RESOURCE-DOS+RACE；medium=XSS/弱鉴权+CRYPTO/DATA-INTEGRITY）；
- `CLAIM_TYPE_SEVERITY` 8 类回退（rce/leak→critical，crash/panic/oom/unbounded/
  protocol_dos→high，xss→medium），对齐 EMPIRICAL_CLAIMS 与 REQ-V3.4.3-006；
- 优先级链 `severity_for()`: override（合法值+reason）> cwe 映射（cwe 列表 +
  sink_type 全量 `CWE-(\d+)` 提取取 max）> claim_type > medium(default)；
  override 非法值 → 回退机械值 + source="invalid_override"（渲染告警行）。

### 1.2 机械渲染 render_report_md（SWR-V3.7-002~006/008，:1439-1748）

- `--stage report` 末尾 stdout 纯 JSON 打印后写
  `.audit_results/reachable_vulnerabilities_report.md`；写入状态走 **stderr**
  （`REPORT_MD_WRITTEN`/`REPORT_MD_ERROR`），stdout 纯 JSON 契约不破；
- 六段结构：一、问题清单（REACHABLE only，严重/高/中三节表，行内 severity
  来源可问责 REQ-V3-006）；二、问题详情（位置/语言、CWE/claim_type、
  verdict+分级（grade_recomputed_by 如有）、调用链逐跳+depth+reachability_type、
  证据、blocking_point 前提、独立复核 refutation{}、实证记录 empirical{}、
  修复建议——R4 finding fix 命中（r3_link 同事实共享 fix），否则占位）；
  三、修复建议与结论（主代理补充，补充后不得重跑 report 覆盖）；附录 A =
  NEEDS_REVIEW 成因双分（`_needs_review_cause` 关键词启发式）+ correction_record
  + 同事实映射（REQ-V3.1-092）；附录 B = B.1 规模对照（闭合率）/ B.2 语言覆盖表
  （角色由 language_inventory 现场重算）/ B.3 FFI 边界 / B.4 R4 verdict /
  B.5 六门禁断言（assert_ledger 机械调用 ①-⑧+③c，断言失败兜底降级不阻断）/
  B.6 覆盖账本（coverage_ledger 渲染，REQ-V3.4-007）；
- **铁律：所有可选输入缺失时降级渲染占位，绝不抛异常**（test_end_to_end
  最小队列形态实测缺全部可选输入）。

### 1.3 stage_collect 透传（SWR-V3.7-007，:435-437）

cwe 拷贝块后白名单透传 `severity_override`/`severity_override_reason`；
`_validate_verdict_payload` 不校验未知字段（已核实），队列 JSON 仍是唯一
事实源（主代理可直接编辑）。

### 1.4 问题摘要改用 claim_type + evidence 首 120 字符

`summary` 字段 collect 不落盘（Plan agent 数据源核查确认）——`_problem_summary`
以 `[claim_type] evidence[:120]` 渲染，无 evidence 时占位「(无 evidence)」。

## 二、测试（tests/test_v37_report.py ×10，214 全绿）

test_severity_mapping_precedence / test_severity_override_invalid_ignored /
test_report_md_written_with_structure（stdout 仍纯 JSON）/
test_report_md_severity_sorted_and_needs_review_excluded /
test_report_md_minimal_queue_degrades / test_report_md_gates_table
（PENDING→FAIL 行）/ test_report_md_deprojected（REPORT_BLACKLIST 零命中
零 /root/）/ test_collect_persists_severity_override /
test_language_coverage_table_roles / test_tracked_ids_includes_coverage_bridge。
既有锁不动：test_report_outputs / test_end_to_end 保持原样全绿。

## 三、裁决记录（义务入库三问执行证据）

| # | 裁决 | 理由 |
|---|---|---|
| R1 | severity_override 字段只接受 3 合法值，非法值回退机械值+告警行 | 触发=主代理认为机械分级与真实影响不符；消费者=render 排序+来源行；悔例=无逃生口时主代理只能伪造证据；非法值不静默吞（可问责）也不采用（防错字改判） |
| R2 | 修复建议占位「（主代理补充）」而非机械空串 | 占位语义向主代理声明义务（SKILL.md 补充后不得重跑覆盖的规范配套）；空串会被误读为「无建议」 |
| R3 | _needs_review_cause 关键词启发式 + else「未注明（主代理确认）」 | 机械近似非判定器——成因双分是主代理裁决义务的提示器，不是新的机械判据（无触发条件无消费者的义务不建） |
| R4 | B.5 六门禁断言渲染失败 → 降级输出错误行不阻断报告 | 报告生成优先级高于门禁诊断；JSON 报告仍完整；六门禁本身仍是队列关闭判据（不因渲染降级而放行） |
| R5 | 问题清单只含 REACHABLE（NEEDS_REVIEW 移附录 A） | 用户要求「有哪些代码问题」= 已确认问题；NEEDS_REVIEW 是待裁决状态，保留显式清单+成因（REQ-V3.3-011 语义不丢） |
| R6 | 语言覆盖表角色现场重算（language_inventory）不持久化 | 未持久化是既有事实（已核实），渲染侧现场重算零新增存储义务 |
| R7 | 严重程度用三级（严重/高/中）不加 P0-P3 数字轴 | 用户决策「严重程度排序」= 可问责分级；P0-P3 是任务优先级轴（stage_next 用），混用会引入第二套排序语义 |

## 三、补充：R4 confirmed findings 并入问题清单（SWR-V3.7-009/010）

用户反馈（2026-08-23）：scan-results 归档报告里 R4 确认的漏洞（no_token
控制端点零鉴权等）散落在按假说分组的表里，未集中、未按危险程度排列。用户两项
裁决：① 并入 High+Medium（r3_link 指向候选的同事实条目不重复列）；② 分级
口径 = **R4 申报值归一化**（High→高, Medium→中；Low 不入清单——含「正向确认」
类非漏洞条目自动排除；申报值缺失/非法回退机械映射）。

- `_r4_severity(fi)`：申报值归一化（用户裁决理由：R4 agent 按实际影响裁定比
  机械 cwe 映射准——CWE-476/125 族 Low 影响条目走机械映射会误提级）；
- `_confirmed_issues(queue, cands)`：确认问题全集 = R3 REACHABLE ∪ R4
  High/Medium，条目带 kind/source（`r4:{hypothesis_id}`）/fid（`{hyp}-F{n}`，
  findings 无 id 字段，渲染侧按索引编号，可复现）；r3_link 以 CAND- 开头 →
  记入 dupes 不占清单行，清单尾注「同事实去重（SWR-V3.4.3-060）」；
- 清单/详情两段同步消费全集；R4 详情含来源标注（R4 业务假说确认，**无 R3.5
  独立复核**）、要点、证据、实证结果 empirical_result、追踪 surface、修复建议；
- 测试 +4（R4 并入/同事实去重/Low 排除/详情渲染），218 全绿。

## 四、勘误

- **SKILL.md 旧文「coverage_bridge 已删除」与实况不符**：puma 真实队列
  `coverage_bridge` 实际存在 19 条。v3.7 渲染侧按实况容忍消费
  （`_tracked_ids` 并入 queue.coverage_bridge[].surface）；SKILL.md 七门禁段
  v3.2.2 原文（coverage_bridge 正式通道条款）与实况一致，报告段勘误在
  v3.7 增量段注明。

## 五、验收

218 测试全绿（204 基线 + 14 新增）+ `signature_lib.py selfcheck /root/phpseclib`
exit 0 + puma 真实队列临时副本冒烟（`--stage report` 渲染到临时副本不覆盖
既有报告，分级/排序/附录真实性人工检查——R4 并入后「高」节含 CAND-001/002 +
H-5-F1/H-6-F1 共 4 条实证确认漏洞）+ ./install.sh → DST pytest 全绿 +
分阶段 commit（P1 渲染+测试 34d8877 → P2 文档+版本链 → P3 R4 并入增强）。
