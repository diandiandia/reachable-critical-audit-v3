# v3.5.2 修改评估报告（AUDIT_EVAL_V3_5_2）

> 评估方式: **未审计过的新项目实战验收**（第一原则验收判据）——puma v8.0.1
> （Ruby/Rack HTTP 服务器, Rails 默认服务器, mature 稳定标签）。
> 评估日期: 2026-08-23。本文件是追溯/评估记录（项目名仅出现于本类文档,
> 未进入任何运行时资产——selfcheck 去项目化扫描 0 命中确认）。

## 0. 验收判据对照（第一原则自检）

| 判据 | 结果 | 证据 |
|---|---|---|
| 未审计过的新项目 | ✓ | puma 为首个 v3.5.2 发布后全链路审计（R0→R5 完整走通）|
| 覆盖格 +1（REQ-V3.4-008）| ✓ +4 | coverage-ledger 回填 AUTHN/MEMORY-SAFETY/OTHER/RESOURCE-DOS × ruby 4 格 |
| 运行时资产零项目名 | ✓ | `selfcheck <puma>` = `non-fixture repo -> integrity OK: 20 signatures (lang/cwe/deproject/runtime-assets/manual 对齐完备)`, exit 0 |
| 六门禁全 PASS | ✓ | 八门禁（含 ③c 复活完成度与 ⑧ target_kind）全 PASS, NEEDS_REVIEW 空 |

## 1. v3.5.2 修改点逐项验证

### P1 残留中项（去项目化）
- 自检闭环在**新项目**工作树成立: integrity OK + hit_rate=0% testable=0（非 fixture 语义正确触发）。
- 审计全程无项目名泄漏进任务书/脚本（verifier/refuter 任务书仅含机制描述与 puma 自身源码引用, 源码引用是审计对象内容, 非 skill 资产）。

### P2 过设计 B 裁决 10 项
- 工具链全链路可用性: surface_mapper / batch_verify / evidence_ledger / workflow_export /
  checklist_binder / harness_runner 在新项目全部正常（grade-recheck 降级为可选维修工具后
  未走强制路径, collect 内联重算承担; r05 裁除后 R0.5 由 surface_mapper.py:940 scope_diff
  承担, scope_snapshot.json 正常产出）。
- **B9 CK-EMPIRICAL-SCOPE 真实绑定: 实现正确但注入时点错位（详见 §2.5, 本轮零注入）**。
- 先例库 16 条: self_refutation_hints 在候选 CAND-001/002 上按需匹配, 无悬空引用。

### P3 偏见机械项
- 形态双轨语义并存: `project_kind=library`（R1 context 信号）‖ `target_kind=application`
  （R0 门禁签收, target_kind.json + verify_queue.target_kind）正交无冲突, 报告首部明示。
- 语言归一: ruby 面 43 个 surface 正常入账, 账本写入归一正确（无幻影列）。
- 本审计为 ruby 单语言项目, 多语言 alias 一致性测试点不在本次触发面（保持测试绿即可）。

### 版本链
- `TOOLING_VERSION "3.5.2"`: workflow_verify.js:25 / workflow_refutation.js:41 双导出脚本
  均含 `tooling_version: "3.5.2"`（已读取确认）; 报告 head 记录传导验证点。

## 2. 机制运行观察（评估素材, 按价值排序）

### 2.1 ⚠️ R2 过滤质量信号: 「防御已到位」drop 被 R4 实证推翻
- R2 将 HYP-005（控制端点 token 鉴权）/ HYP-006（state 文件权限）判为「防御到位
  （默认 token 随机）」drop——**误判**。R4 H5/H6 实证推翻: 默认权限 state 0644 +
  控制 unix socket 0777（binder umask||=0 死配置）使随机 token 形同虚设, 无需篡改
  任何文件即跨用户接管（uid=65534 端到端实证停掉 root 实例, H6-F1 High）。
- 含义: R2 对「默认值防御」的判断过乐观。「防御已到位」类 drop 应要求核查
  **默认权限上下文**（文件权限/umask/环境变量默认值/启动命令注入点）,
  或将该类 drop 的复活复核（R3.5-N）优先级上调。
- 处置: 本报告已按 R4 实证修正（r4_feedback 裁决机制正常发挥——warn 不阻断, 主代理裁决纠正）。

### 2.2 ✓ R3.5 强制触发 + 视角差异化
- 双 REACHABLE edge_proven 自动入证伪池（无人工干预）; 2 候选 × 2 证伪者 = 4 votes,
  **0 证伪, 均 survived**, 无 KILL 无降级。
- 视角差异化的直接价值: 视角 #1（前提维度）产出 CAND-002 归属修正——queue_requests=true
  默认模式下无界结构是 reactor selector 注册集（@timeouts + NIO monitors）而非 @todo
  队列; strengthened 4 条（滑动 30s 定时器无限维持 / fast_write_str 无限重试 / chunked
  无条件落盘 / 408 无超时阻塞写）。修正后两种模式 DoS 结论一致, 证据链更精确。

### 2.3 ✓ 同事实去重（SWR-V3.4.3-060）真实家族应用
- 家族 A（控制通道权限链: state 0644 + socket 0777 + umask 死代码）5 条 finding
  → 主申报方 H6-F1（High）承载 severity, H4-F2/H5-F2/H7-F1/H7-F2 标「同事实共享实证」。
- 家族 B（body 无上限）→ 主申报方 CAND-001, H1-F1/H7-F3 同事实。
- 报告第 54 行「同事实去重」段为机械渲染结果。

### 2.4 ✓ R5 实证全链路（环境从零搭建）
- apt ruby 3.3.8 + ruby-dev + build-essential → nio4r 2.7.5 编译 → rack 3.2.7 →
  puma C 扩展本地编译 → 冒烟 → v8.0.1 纯净树（git archive, 排除工作树 tag 后加固干扰）。
- CAND-001 CONFIRMED: 4 连接 × 声明 1GB 实发 192MB 停驻 → tempfile 占用 805,306,962 B
  ≈ 发送量 1:1, 关闭即释放。
- CAND-002 CONFIRMED: 速率型灌注 600 连接/40s → RSS +1,572 kB 单调增长, 全程 0 拒绝 0 背压;
  量化边界如实记录（~2.6kB/连接, systemd fd 1024 封顶效果受限, docker/高 nofile 可达 GB 级）。
- 实证回填合规（SWR-V3.4.3-061）: `backfilled_by: main-agent` + 实测数字, 无无依据回填。
- 环境陷阱自检价值实证: nohup 包装进程导致观测 PID 错误, 经 ps 核实纠正; stale 进程清理
  机制收尾正常。

### 2.5 ⚠️ B9 CK-EMPIRICAL-SCOPE 真实绑定: 实现正确, 注入时点错位（本轮零注入）
- 实现验证: 对最终队列候选 live 运行 `bind()` → 返回
  `[('CK-CHECKPOINT-AFTER-ACCUM', [cwe-match CWE-770]), ('CK-EMPIRICAL-SCOPE', ['r5-semantic'])]`,
  `_in_r5_semantic_space` = True（claim_type=unbounded/oom ∈ R5 强制集）——**B9 语义正确**。
- 但 verify 波次 payload（workflow 实际派发的任务书）**0 条清单段**:
  导出时（export_script:548 `_checklist_section(c)`）候选处于 PENDING, cwe/claim_type
  均为空（二者由 collect 从 verifier 结构化输出落盘, batch_verify.py:423-432）→ 绑定恒空。
- refutation 分支（export_script:546 `if mode == "verify"` 守卫）**不注入清单段**——
  此时信号已齐全（collect 后）, 但注入点不存在。
- 结论: B9 从「永不绑定」（v3.5.2 前 matched=[] 特判）变为「collect 后绑定」, 但
  唯一注入点（verify 任务书）在 collect 前 → **消费者零到达**。主代理 R5 手工完成了
  范围分级（e2e 级观测 / 机制级+量化边界）, 流程未受损, 但机械绑定未生效。
- 修复建议（入 v3.6 候选）:
  a. refutation 分支同样调用 `_checklist_section(c)`（此时 cwe/claim_type 已落盘,
     refuter 任务书可携带 CK-EMPIRICAL-SCOPE）;
  b. 或 R5 阶段主代理任务书（biz_hypothesis 模板/实证清单选择处）渲染
     `applies_to_phase=="R5"` 的清单——消费者本就是 R5 主代理而非 verifier;
  c. 或入队时携带簇级 cwe（HYP 假设的 cwe 合并, 而非 collect 后）, 使 verify 导出
     即有信号。

### 2.6 ✓ coverage-ledger 回填与缺口
- 回填 4 格（AUTHN/MEMORY-SAFETY/OTHER/RESOURCE-DOS × ruby）, 首跑
  LEDGER_WRITTEN（new_counts 7/4/13/9）。
- INJECTION × ruby 缺口（如实）: H4-F3（pumactl CWD 隐式 eval 配置 = CWE-94 注入族）的
  cwe 补标发生在回填快照之后 → 重跑 LEDGER_IDEMPOTENT_SKIP（`_ledger_source_key` =
  sha256(abspath)[:16], 每项目只回填一次是机制语义）。CWE-94 标注保留在队列中供未来批次。
  → 机制观察: 回填时点宜放在全部 cwe 修正（含 r4_feedback 裁决）之后, 或账本支持显式
  force 重写（当前设计有意不提供, 防重复记账）。
- RACE × ruby 缺口（如实）: 本批无真实竞态 finding（H3 主假说 CWE-416 在 MRI GVL 下不可达,
  仅 2 个 Low）→ 不凑数。
- 两格均留给下批 ruby 选题（账本机制自然闭合路径）。

### 2.7 ✓ 门禁与对账
- wave_registry.jsonl 双波登记（wf_8c6b7f10-4c8 verify / wf_15320b8a-c7e refutation）,
  collect `--from-journal --expect` 对账零差异。
- 八门禁全 PASS; r4_feedback warn 级裁决纠正机制正常（§2.1）。

## 3. 结论

**v3.5.2 修改在新项目实战验收通过**: P1 去项目化、版本链传导、双轴形态、R3.5 强制触发、
同事实去重、账本回填（+4 格）全部按设计工作; 六门禁全 PASS, 闭合率 2/2（100%）,
产出 2 个 REACHABLE High 实证确认 + 19 条 R4 findings。

**遗留两处机制观察（不阻断发布, 建议入 v3.6）**:
1. B9 绑定注入时点错位 → R5 阶段清单零注入（§2.5, 修复三选一）。
2. R2「防御已到位」类 drop 缺默认权限上下文核查 → 误判实证推翻（§2.1,
   建议: drop 理由模板加「默认权限上下文已核查」步骤, 或复活复核优先）。

**审计成果摘要**（完整报告见 /root/puma/.audit_results/reachable_vulnerabilities_report.md）:
- CAND-001 请求体 tempfile 磁盘耗尽（CWE-400, unbounded, High, 实测 805MB 1:1 增长）
- CAND-002 连接积压内存无界增长（CWE-400, oom, High, 实测 600 连接单调增长零拒绝）
- 最高价值发现 H6-F1: 控制通道缺归属校验——uid=65534 跨用户端到端停掉 root 实例
  （state 0644 泄 token + socket 0777 组合, 默认配置即中招）
- 上游佐证: v8.0.1 tag 后已加 wait_until_not_full 背压, 反向确认 v8.0.1 缺防御
