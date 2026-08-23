# v3.4.6 系统设计：quic-go 空队验收暴露机制缺陷修复批

- 版本: v3.4.6（补丁版，不改变阶段骨架与门禁语义）
- 日期: 2026-08-23
- 来源: quic-go 验收审计（2026-08-23）运行实录暴露缺陷
  （lessons/SKILL_LESSONS_quic_go.md 问题 1/2/3 + 制度缺口）
- 上一版: v3.4.5（gRPC 缺陷修复批，已验收安装）

## P-A 机制缺陷（3 项）

### P-A-1: coverage-ledger 空队 lang 失真（SWR-V3.4.6-001）

**实录**: `batch_verify.py --stage coverage-ledger --write` 在 R3 空队（R2 keep 0）
时, 候选级主导语言无可推 → `dom = "other"`, 纯 Go 项目 quic-go 的全部 R4
findings 记入 `*xother` 格而非 `*xgo` 格。验收时 MEMORY-SAFETY×go 缺口格
回填依赖人工修正（ledger_fix）, 账本机制自身失真。

**根因**: `stage_coverage_ledger` 的 `lang_of` 只读队列候选
(`c.language/lang/source_file 扩展名`); 候选为空时无回退来源。
R1 产物携带语言信息: `input_surface.json` 每 surface 有 `lang` 字段
(任务书 schema 必填), `architecture_context.json` 有 `language_inventory`
(R1 context 输出, 含每语言 file_count; scope_snapshot.json 无此字段)。
这些来源在空队形态下仍可用, 是"项目主导语言"的正确事实源。

**空队是新常态**: 成熟库/框架经 R2 全防御确认 → keep 0 合法终态
(quic-go 24/28 boundary confirmations; test_export_verify_empty_pool 用例
即为此设计)。账本必须正确处理空队项目, 否则空队项目越多 other 格越膨胀,
缺口格判据失真。

### P-A-2: R2 filter 落盘丢 surface_ids（SWR-V3.4.6-002）

**实录**: 主代理把 filter agent 产出落盘为 r2_filter_result.json 时,
boundary_confirmations/drop 条目只保留了 id（surface_ids 字段丢失）→
门禁⑦ tracked 覆盖虚低（41→31 假缺口）→ 事后从 hypotheses.json 反查补齐。

**根因双面**:
- ① `task_templates/hypothesis_filter.md` 的 canonical 输出 schema:
  keep 条目要求 surface_ids, 但 boundary_confirmations/drop 条目未强制
  （模板第 29-32 行 bc/drop 形态无 surface_ids 义务）
- ② 无落盘层保真校验: 主代理落盘/工具聚合时无自动反查补齐机制

**影响**: 任何含 bc/drop 的筛选结果（几乎所有项目）都可能丢覆盖簿记;
门禁⑦ 假失败会阻断收尾, 假通过会掩盖覆盖缺口。

### P-A-3: merge 同文件跨域缺 mirror 对（SWR-V3.4.6-003）

**实录**: SURF-DATA-010（data 域 token LRU）↔ SURF-STORAGE-008
（storage 域 token LRU）是同一 lruTokenStore 实现的两侧, R1 merge 的
12 对 mirror_pairs 无此对 → HYP-L19 覆盖 DATA-010 后 STORAGE-008 未自动
传播 → 主代理人工 coverage_bridge 补桥。

**根因**: merge 的 mirror 检测基于 conflicts（同入口多域）启发式;
"同文件双面但 entry_points 不重叠"的形态（token_store.go 两个域各自
测绘不同函数）不产生冲突 → 不生成 mirror 对, 且无人工核对提示。

**设计决策**: 只加**提示不自动成对**。跨域同实现语义判定属主代理裁决
（自动成对会引入误耦合——同文件不同入口可能是完全独立的两个面）;
merge 输出 `same_file_cross_domain_pairs` 建议清单, 主代理裁决补
mirror/bridge。

## P-B 制度缺口（1 项）

### P-B-1: 全 keep 0 形态抽样复核义务未制度化（SWR-V3.4.6-004）

**实录**: quic-go filter 28 条假设全判"防御已到位"（keep 0）; 主代理
手动抽样 3 条最重确认复核（header.go:145 先检查后切片 /
transport_parameters.go:136 paramLen 先于切片 /
receive_stream.go:454 流控先于重组）全部属实, 结论可信。

**缺口**: SKILL.md R2 段无"keep=0 时主代理必须抽样复核"条款——若 filter
结论失真（防御性偏差的另一方向: 过度放行）, R3 空队会整体放过缺陷。
R4 深度验证（H1 7 条防御确认逐点与 R2 交叉）构成第二保险, 但 R4 任务书
按假说分配, 对 R2 假设的交叉核对不系统。

**设计**: R2 段补条款——keep=0 时主代理抽样复核 ≥3 条 boundary_confirmations
（抽样清单落盘 `spot_checked` 字段）; 条款只落 SKILL.md 不落代码
（执行纪律, 无 gate 消费者, 义务入库三问: 触发条件=keep 0, 消费者=
主代理执行, 案例支撑=quic-go 实录）。

## 裁剪说明

1. P-A-3 不做自动成对 mirror（主代理裁决是必需的人工环节）
2. P-B-1 不落代码（纪律条款无机械消费者; 落代码即义务棘轮）
3. 空队流程其余环节验证机制正确, 不修改:
   - `WORKFLOW_NOTHING_TO_DO`（SWR-V3.4.4-003, quic-go 实战验证）
   - 门禁⑦ tracked_ids 模式 + assert_ledger 自动镜像传播
   - R3.5 空队无触发对象（无 REACHABLE）
4. rpcx 验收不覆盖 protobuf 范围决策（v3.4.5 已裁）

## 验证策略

### 单测（+4 用例）
1. `test_coverage_ledger_empty_queue_lang_from_surface`（M1）:
   空队 + input_surface lang=go → 账本写 go 格, other 零新增
2. `test_coverage_ledger_derivation_chain`（M1）: 候选 lang 优先于
   surface lang（候选非空时行为不变——防回退破坏既有数据）
3. `test_filter_result_surface_ids_fidelity`（M2）: r2_guard 落盘后
   bc/drop 均含 surface_ids 且与 hypotheses.json 反查一致
4. `test_merge_same_file_cross_domain_hint`（M3）: 同文件双面 fixture
   → merge 输出 same_file_cross_domain_pairs 非空; 不同文件 → 空

### 新项目验收（rpcx）
- 项目: /root/rpcx（Go RPC 框架, 122 文件, go 1.26, hybrid 形态）
- 判据: ① M1 实战验证——rpcx 验收回填账本时 lang 落 go 格（无论
  keep 0 或 keep>0 形态）; ② 覆盖账本缺口格优先: INJECTION×go、
  DATA-INTEGRITY×go 仍为 0, rpcx 补格预期（RPC 框架序列化面）;
  ③ 六门禁全 PASS; ④ 覆盖格 +1 判据达成
- 回归: 170 单测全绿 + 安装副本基线（168+2skip+3 环境基线失败）
- 全流程: R0-R6 + 报告归档 reachable-critical-audit-scan-results/rpcx/

### 发布三条件
① 单测全绿（170+4） ② 既有机制零回退（fixture 基线对照）
③ rpcx 验收通过 + 六门禁 PASS
三条件同时满足才 install + 提交。
