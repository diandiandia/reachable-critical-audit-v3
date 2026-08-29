---
name: reachable-critical-audit
description: >-
  对任意语言、任意项目形态（application/library/hybrid/infra）的代码库进行可达性
  严重漏洞审计：输入面测绘、假设生成与筛选、LLM 候选验证、独立证伪复核、实证抽验、
  六门禁与报告。当用户要求审计代码、查找可达性漏洞、梳理攻击面，或做 CVE 评估的
  前置分析时使用。
---

# Reachable Critical Audit Skill v3（可达性严重漏洞审计）

## 🥇 第一原则：通用型 Skill（最高优先，一切修改的第一判据）

> **义务入库三问（v3.3.2, REQ-V3.3.2-022）**：本 skill 此后新增任何强制义务
> （检查步骤/产出字段/门禁检查）前必须回答：①触发条件是什么（什么目标/语言/
> 场景才执行）——无条件默认不建；②消费者是谁（哪个 gate/工具/报告段落读它）
> ——无消费者不建，或先建消费者；③裁掉丢什么（有可回溯的失误案例支撑吗）
> ——无案例支撑的防御性义务降为 checklist 提示。历史教训：H7 五维全表
> （有义务无消费者）与步骤 0.5 无条件强制（无触发条件）是义务棘轮的直接产物
> （W6 §28）。

**目标**：本 skill 是**通用型代码审计 skill**——对任意语言、任意项目形态（application/library/hybrid/infra）、任意平台的任意代码库均可审计。审计能力必须来自通用机制（阶段骨架 / 门禁 / 数据模型 / CWE 锚定的语义族 / 通用检查清单），而不是来自"我们审过哪个项目"。

**禁止项**（违反即视为缺陷，必须修复）：
1. 禁止为已审计的具体项目做专门优化：项目名、项目目录结构、项目专属 API 名不得进入运行时资产（签名 grep 列表、任务书例证、harness 模板、先例/清单正文）
2. 禁止让运行时机制依赖单一语言特征：语言相关内容必须按 `lang` 字段分派，或写入语言手册（harness_manuals/）
3. 禁止用历史项目目录做运行时锚定：known_instances 等回归锚点只允许存在于测试 fixture（tests/），不得影响 R0 自检等运行时路径

**提炼经验的正确方式（两段式）**：具体审计发现 → **去项目化提炼**（抽象到 CWE 类 / 语言无关模式 / 通用检查步骤）→ 入库。项目名只允许出现在追溯字段（lessons / 来源列）。

**测试与回归的边界**：回归 fixture 可以来自具体项目（三锚点基线），但 fixture 只用于验证"通用机制未回退"，不得成为运行时行为依据。

**每次修改 skill 的自检**（违反任一条 = 修改不合格）：
- [ ] 新资产（签名/先例/清单/模板）是否已去除项目专属名称？
- [ ] 新机制在任何语言上是否有语义，或已按 lang 分派？
- [ ] 新代码是否读取了具体项目路径/目录名（tests/ fixture 除外）？
- [ ] 验收是否包含"未审计过的新项目"场景（每版本至少一个新项目验收，防止向历史项目收敛）？
      且 v3.4 起验收项目**优先选补覆盖账本缺口格的项目**（语言 × CWE 族），
      验收判据含"覆盖格 +1"（REQ-V3.4-008）？

> 来源：2026-08-17 mbedtls 审计复盘——签名库携带 Django/NestJS/Ktor/lighttpd/WordPress 专属 API 名（get_host/read_body/multer/maxDecodedContentLength/good_origin/CleanXSS）、verifier 任务书是 Python 思维定式（find_spec）、harness 按历史战役配置（4 模板 6/15 语言）、R0 冒烟仅对历史 fixture 有意义（非 fixture 项目恒放行）。修复方案见 v3.2.2 设计（P-A 资产去项目化问题域）。

> [!IMPORTANT]
> **v3 取代 v2.1**。v3 由三锚点回归测试（sinatra/lighttpd/actix-web 对照归档基线，2026-08-16）实战验证：候选规模下降 98~99.98%、闭合率 100%、独立复核机制三次实战拦截"代码路径可达≠攻击相关"误判、产出 2 个实证确认的 REACHABLE。v2.1 唯一遗产为 `docs/legacy/SKILL_V2.1.md`（规范备份，供对照历史）。
>
> **架构转变**：LLM 子智能体是主分析引擎（测绘/回溯/判断）；规则库只是**提示器**（语义签名 grep hints + 检查清单），不再是判定器。审计起点是**输入面测绘**（R1），全库规则轰炸不再是默认路径。

## 🎯 核心使命（不变）

- **无 Key 自治**：完全使用 Agent 自身的 LLM 能力与本地工具（python3 标准库），无需第三方 API Key。
- **语言通用**：语义签名语言无关 + LLM 主引擎——15 种预设语言之外的项目同样可审。
- **可问责**：每个结论可追溯到证据文件与分级证据链，无证据断言被门禁拦截。

## 🔌 平台兼容层（探测顺序）

| 模式 | 条件 | 编排原语 | 适用范围 |
|---|---|---|---|
| **W**（默认） | `Workflow` 工具可用（Claude Code） | workflow 脚本（pipeline/parallel + schema 强校验 + 断点续传） | R2 筛选 / R3 验证 / R3.5 复核 |
| **A'**（降级） | Workflow 不可用 | `Agent`/`task` 工具手工循环（`--stage next/collect`） | 同上，手工驱动 |
| **裁决层** | 始终 | 主 Agent 自身 | R0 自检、R1 复核、R5 实证、冲突裁决、报告 |

Mode B（独立 CLI 子进程）为 v2.1 机制，v3 不再需要。

## 🛠️ R0：目录守卫 + 自检（任一步失败即终止）

1. **目录守卫**：`mkdir -p <project>/.audit_results/`；所有产物必须以 `.audit_results/` 为前缀。
1.5 **scope 快照**（v3.2.2, REQ-V3.2.2-018）：
   ```bash
   python3 <skill_dir>/surface_mapper.py scope snapshot <project>
   ```
   落盘 `.audit_results/scope_snapshot.json`（子模块状态 + 关键目录存在性）。
   scope 是各阶段判定的隐含前提——子模块中途物化/依赖目录出现会使
   "树外不可验证"类 drop 理由作废（C 库审计实战形态: 子模块中途物化），R3 入队前
   batch_verify 自动 diff 并输出 `scope_changed` 提示，受影响 drop
   （`scope_dependent: true`）按 R3.5-N 复活流程重开。
   **版本基线佐证**（v3.8, SWR-V3.8-014）：`git describe --tags` 只作参考，
   审计基线版本必须用构建清单佐证（pom.xml/Cargo.toml/package.json/setup.py/
   Makefile.am 等）；两者不一致以构建清单为准并回填签收记录——旧标签残留会使
   git describe 写错基线（shardingsphere 实录: describe 返回 4.0.0-RC2 而
   pom 实为 5.5.4-SNAPSHOT）。
2. **签名库自检**（REQ-V3-010, v3.2.2 起单一事实源：只引用 selfcheck 命令）：
   ```bash
   python3 <skill_dir>/signature_lib.py selfcheck <project>
   ```
   exit 0 = 放行。两种语义：fixture 仓库（回归锚点可定位）→ anchor recall
   `hit_rate ≥ required_hit_rate`；非 fixture 仓库 → **签名库完整性自检**
   （validate + L2 词族 lang 必填 + 去项目化扫描 0 命中 + grep 可编译，REQ-V3.2.2-005）。
   完整性自检失败同样阻止启动（第一原则：资产必须通用，不得携带项目专属名）。
   回归锚点库已移入 `tests/fixtures/known_instances.json`（第一原则三禁止③）。
3. **harness 自检**（REQ-V3-011）：`harness_runner.list_templates()` ≥ 1；否则 R5 阶段降级为静态 + 告警。
4. **target_kind 判定**（v3.2.1, REQ-V3.2.1-001/002, W6 §25.1）：
   ```bash
   python3 <skill_dir>/tools/target_kind.py <project> --write
   ```
   → 机械推荐 {application, library, hybrid} + 信号证据。主代理复核后**签收**写入
   `verify_queue.target_kind`。存在性规则按型装载（先例规则文本，v3.5.2 起不设 PREC id）：
   - **application**：默认可达三层检查含 shipped 配置实际值 + 运行时注册核实 + platform_precondition 显式标注
   - **library**：公共 API 即信任边界（库型先例）；仓内调用者缺失不是阻断；死代码豁免不适用
   - **hybrid**：按组件分别装载；无法确定归属时按 application（保守）
   未签收 → 门禁⑧ target_kind_required 不放行（旧队列复跑以 `require_target_kind=False` 豁免）。
5. 初始化空 `verify_queue.json`：`{"candidates":[]}`。

## 🗺️ R1：输入面测绘（审计起点，禁止全库轰炸）

**目标**：产出 `input_surface.json`（surface 列表）。每个 surface = 一个外部数据入口，附 entry_points 源码证据。

1. **架构上下文**：`python3 surface_mapper.py context <project>` → 语言/构建文件/README 摘要。
2. **4 域并行测绘**（network/data/process/storage）：拉起 4 个子智能体，任务书模板 `task_templates/surface_map_domain.md`。
   > ⚠️ **任务书 schema 契约（W5 教训 ②）**：任务书必须内嵌下述 canonical schema，禁止让子智能体自定格式：
   > ```json
   > [{"id":"SURF-<域>-NNN","name":"...","type":"network|data|process|storage",
   >   "lang":"<面代码语言: c/cpp/go/rust/java/python/... 必填, 从架构上下文继承>",
   >   "entry_points":[{"file":"<相对项目根路径>","line":N,"function":"...",
   >                     "evidence":{"snippet":"<该行代码, 可含上下文注释>"}}],
   >   "taint_channels":["..."],"trust_boundary":"unauthenticated_remote|trusted_channel|gated|host_api|local|environment|unknown",
   >   "confidence":"high|medium|low","downstream_hints":["..."]}]
   > ```
   > 子智能体落盘到 `.audit_results/_r1_<域>.json`，最终回复同 JSON。
3. **收集与校验**：`python3 surface_mapper.py validate .audit_results/_r1_<域>.json --root <project>`。
   校验器已内置归一化（裸数组/字符串 trust_boundary/HTML 实体/相对路径/空白折叠均容忍）与行号漂移裁决：
   - `[suggested_line=N]`（唯一命中）→ 主代理应用修正并写 `line_corrections`；
   - `[suggested_lines=a,b,c]`（多命中）→ 主代理按定义形态启发式裁决；
   - 内容完全不匹配 → 主代理重写 snippet 为源行实际内容并标 `evidence_rewritten_by`。
   > ⚠️ **铁律 1（W5 教训 ①）**：agent 完成通知与文件落盘之间存在写读竞态。读任何子智能体产出文件前必须 `json.load` 重试（失败等 1-2s 重试至多 3 次）；重试后仍损坏才按"产出损坏"处理（重派或主代理修复），禁止把竞态误判为 agent 幻觉。
4. **合并**：`python3 surface_mapper.py merge .audit_results/_r1_*.json --root <project>` → `input_surface.json`（含 conflicts 标注）。主代理复核后写 `reviewed_by`。

## 🎯 R2：假设生成（LLM 主路径）→ LLM 筛选

**假设生成主路径**：LLM 直接基于 surface 图生成假设（主代理或限时 agent）。签名匹配是**可选佐证器**（SWR-V3.3.2-053）：
- 库型/非服务端框架目标签名命中率趋近 0（七项目批次 7/7 项目 0 命中实测），**R2 不强制跑 index/match 链路**；
- 如需佐证（服务端框架目标、或主代理判断签名面相关），按序运行：
  1. `python3 signature_matcher.py index <project>`（粗粒度调用索引，窗口展开用）
  2. `python3 signature_matcher.py match .audit_results/input_surface.json <index.json>`（窗口有界：entry 行 ±60 邻域 + BFS 逐层 cap 40 + 总 cap 300）
  3. `python3 signature_matcher.py gen <hits.json>` → 佐证 hints（**不是**最终候选）
- R0 `signature_lib.py selfcheck` 不受影响（回归锚点 + 去项目化扫描是第一原则守卫，仍强制）。

**LLM 筛选**（REQ-V3-037）：拉起 hypothesis-filter 子智能体（模板 `task_templates/hypothesis_filter.md`），按排除规则（常量参数/死代码/测试代码/语义不匹配/防御已到位）判定 keep/drop；**必须 Read/Grep 抽查 hit 真实代码，禁止只看 line_text**。其中『防御已到位』类裁决必须核查默认权限上下文（文件/目录/umask/监听 socket 权限、环境变量默认值、启动命令注入点）并引用源码证据行（v3.6 实录：默认 token 随机 + state 0644/socket 0777 使防御失效，R4 实证推翻 R2 误 drop）。筛选理由中的 focus sink（file:line）是后续簇化依据。

> **keep=0 抽样复核条款（v3.4.6, SWR-V3.4.6-004）**：筛选结果 keep=0（或
> boundary_confirmations ≥ 全量 80%）时, 主代理**必须**抽样复核 ≥3 条
> boundary_confirmations 的真实代码防御点（逐条 Read 防御点源码确认成立;
> 抽样清单落盘 `r2_filter_result.spot_checked`）。筛选全防御裁决若失真
> （防御性偏差的另一方向: 过度放行）, R3 空队会整体放过缺陷——抽样复核是
> "证据裁决"铁律在空队形态下的必要延伸; R4 深度验证与 R2 交叉核对构成
> 双保险（成熟网络库 28 条全防御、主代理抽样 HYP-L1/L12/L27 复核属实实录）。
> 落盘保真: 筛选结果落盘为 `r2_filter_result.json` 后跑
> `python3 <skill_dir>/r2_guard.py fidelity .audit_results/r2_filter_result.json`
> （SWR-V3.4.6-002: bc/drop 缺 surface_ids 自动从 hypotheses.json 反查补齐）。

## 🔄 R3：候选验证（Mode W 默认）

**批次选题规则（v3.4, REQ-V3.4-006）**：多项目批次开题时，先跑
`batch_verify.py <任一项目> --stage coverage-ledger` 读覆盖账本缺口格
（CWE 族 × 语言，`resources/issue_coverage_matrix.json`），**优先选未覆盖
（语言 × CWE 族）格的项目**；可实证性降为可行性约束而非第一判据。
审计闭合（R6）时执行 `--stage coverage-ledger --write` 回填账本
（前置与时序见 R6 条款，v3.6 起强制）。

**入队**：筛选 kept 的假设按 focus sink 簇化（同 sink 合并为一条簇级候选），写入 `verify_queue.json`：
```json
{"id":"CAND-001","source_file":"...","source_line":N,"sink_type":"CWE-xxx",
 "status":"PENDING","priority":0}
```

**Mode W 波次**（SWR-V3.3.2-050 编排条款：每波派发后登记 wave_registry）：
```bash
python3 tools/batch_verify.py <project> --stage workflow-script --mode verify
# → .audit_results/workflow_verify.js + payload（含逐候选任务书 prompt）
# 1) 用 Workflow 工具运行: scriptPath=<js> args={"candidates":<payload>}
# 2) 返回 verified 逐条 --stage collect 落盘（grade 自动重算: REACHABLE+边证据→edge_proven）
# 3) missing 中的 id 执行 --stage bump-attempt（attempt≥3 → ESCALATED 主代理裁决）
# 4) 循环直到队列无 PENDING
```

**wave registry 簿记（强制）**：每波 Workflow 派发后向
`.audit_results/wave_registry.jsonl` append 一行
`{"run_id": <Workflow 返回 runId>, "mode": "verify|refutation|resurrect",
  "project": "<绝对路径>", "dispatched": [<候选 id...>], "payload_hash": "<sha256>"}`；
collect 时 `--from-journal <dir> --expect CAND-001,CAND-002,...` 以注册表全集对账
（防 journal 张冠李戴/部分落盘，七项目批次教训）。
- workflow 内 agent 无文件系统：**不要把心跳契约写进 Mode W 任务书**（心跳是 Mode A' 机制）；结构化输出由 schema 强校验（自动重试）。
- `--stage collect` 落盘字段含 v3 必需项：`claim_type`、`edge_evidence`（实证门禁与分级依赖）。

**Mode A' 降级**（无 Workflow 工具时）：`--stage next` 出队 3~4 候选 → Agent 工具逐候选验证（任务书含心跳契约：先写 `.pending` 占位，完成后写 `_verify_<id>.json`，目标存在且非本人 pending → 追加 `.agent-<id>` 后缀）→ `--stage collect` → 循环。

## ⚖️ R3.5：独立复核（REACHABLE 且 grade≥edge_proven 强制）

**触发范围（SWR-V3.3.2-051）**：除常规 REACHABLE 外，**复活重验改判 REACHABLE
且 grade≥edge_proven 的候选强制入池**（REQ-V3.2-021 修订：放行方向必须对抗复核；
gate post_resurrect_refutation 强制，无 refutation 字段不放行）。

```bash
python3 tools/batch_verify.py <project> --stage workflow-script --mode refutation
# N=2 证伪者 × 每候选（视角差异化: #0 调用边真实性 / #1 前提维度与阻断幻觉），KILL=2
# 证伪者 prompt 必须不同（相同 prompt 会命中框架缓存 → 伪独立）
```
- **多数决**：2/2 证伪 → 主代理降级（`evidence_ledger.commit` 写 `correction_record` + `demote_to`）；1/2 → 保留但记录分歧理由，主代理裁决。
- 复核的核心价值是拦截"**代码路径可达 ≠ 攻击相关**"（前提维度/信任边界幻觉）——v3 回归中三次实战拦截均为此类。

## 🧠 R4：业务假说 H1-H7（每类三选一：confirmed / reviewed_clean / not_applicable）

| 假说 | 检测要点 |
|---|---|
| H1 | 远端控制分配大小无上限（CWE-789：缓存/累积/预留 × sizeof） |
| H2 | 远端控制解引用长度/索引（CWE-125/787：截断 cast/下标/切片） |
| H3 | 异步对象生命周期竞态（CWE-416：回调持引用/池复用状态残留） |
| H4 | 跨进程信任边界破坏（CWE-20+89/78：输入拼进 exec/路径/转发头） |
| H5 | 暴露组件鉴权缺失（CWE-862/926：调试端点/状态页/目录列表） |
| H6 | 多租户 owner 比对缺失（CWE-639/285：锁/会话/缓存归属） |
| H7 | **信任边界专项（v3 新增）**：① 同 UID/IPC 高危操作 ② 路径语义（.. 上溯/symlink/空路径回退）越界 ③ 鉴权谓词弱化（前缀/子串/hash 替代全名） |

任务书模板 `task_templates/biz_hypothesis.md`（v3.4.3 起注入实际 surface id 清单
`{surface_id_list}` + canonical 输出示例；H7 默认值全表预算 ≤1200 字）。
锚点 = R1 测绘的相关 surface（file:line 可直接 grep）。
收集：`python3 tools/batch_verify.py <project> --stage r4-collect --file <合并 findings json>`；
断言：`--stage r4-assert`（H1-H7 全部 VERIFIED，exit 0）。
**同事实去重（v3.4.3, SWR-V3.4.3-060）**：r4-collect 后主代理按 title 跨假说
同事实去重——主申报方承载 severity，其余条目 `r3_link` 标「同事实共享实证」
（java-jwt H2/H7 双 agent 各自发现同一 DateTimeException 逃逸的实战形态）。

## 🧪 R5：实证抽验（声称类强制，REQ-V3-004/060）

**触发判定**：verdict=REACHABLE 且 `claim_type ∈ {crash,panic,oom,unbounded,xss,protocol_dos,rce,leak}` 且 `evidence_grade ≠ empirically_confirmed` → **强制实证，否则六门禁 ③ 不放行**（可选路径：主代理裁决降级 NEEDS_REVIEW，不实证不申报——v3.3 起此为明示条款：NEEDS_REVIEW 是合法终态而非降级耻辱，成因须注明「保守裁决」或「证据不足」）。源事实级降级规则（哨兵值/算术类，网络阻断记录 blocker，W6 §21.4）继续有效。
**实证回填规范（v3.4.3, SWR-V3.4.3-061；v3.10, SWR-V3.10-005 键名规范化）**：主代理回填
`empirical` 结构化 dict 只允许发生在 verifier/证伪者证据文本含真实实测的场景——必须带
`backfilled_by` 标记 + 实测数字依据（成本曲线/RSS/exit code/请求计数）；禁止无依据回填。
**canonical 键集**：保留键 `outcome`/`evidence_numbers`/`report`（报告渲染既有消费键）+
标准键 `harness`/`method`/`input`/`result`/`verdict`/`backfilled_by`（自建 harness 回填用）；
渲染器容错读双形态（保留键优先，缺失回退标准键）。

1. harness 模板（`templates/harness/`）：ws_frame_alloc / ws_frame_accum / xss_path_sim / parser_fuzz（C/C++ 解析器 crash 声称类）/ resource_rate_probe（v3.6 通用协议级速率灌注探针，langs:["any"]，protocol_dos/unbounded/oom 声称）；无匹配模板时现场构造（采样协议通用：RSS/存活/exit code + delivery-rate 确认）。
2. 实证程序落盘 `.audit_results/empirical/<name>/`（含 Cargo.toml/源码 + EMPIRICAL_REPORT.md：工具链版本/输入/输出/判定）。
3. 实测确认 → `empirical` 字段 + grade=empirically_confirmed；证伪 → correction_record 降级并回溯 verifier 错误（REQ-V3-051）。

## 🔒 六门禁（队列关闭判据，全部通过才允许出报告）

```bash
python3 -c "
import sys; sys.path.insert(0,'<skill_dir>'); sys.path.insert(0,'<skill_dir>/tools')
import evidence_ledger as el, batch_verify as bv, json
q=bv.load_queue('<project>')
surfaces=json.load(open('<project>/.audit_results/input_surface.json'))['surfaces']
tracked_ids=...  # R2 假设 surface_ids ∪ R4 findings.tracked_surfaces ∪ relay 中继面
ok,v=el.assert_ledger(q, dispatched=[c['id'] for c in q['candidates']],
                      surface_data={'total':len(surfaces['surfaces']),
                                    'tracked_ids':sorted(tracked_ids),
                                    'mirror_pairs':surfaces.get('mirror_pairs') or []})
print(ok, v)"
```
① no_pending ② REACHABLE 无 static_only ③ 实证类声称 100% empirically_confirmed ④ H1-H7 全 VERIFIED
⑤ 对账零差异（dispatched 全部终态）⑥ escalated=0 或主代理签收 ⑦ surface 覆盖率 100%
（v3.5：tracked_ids = R2 假设 surface_ids ∪ R4 findings.tracked_surfaces ∪
relay 中继面[套接字层/示例程序中转]直接并入 tracked_ids——覆盖依据写入 R4 finding
evidence 文本；`mirror_pairs` 镜像由 assert_ledger 自动传播；coverage_bridge
字段已删，REQ-V3.2.2-020/021 语义保留）
⑧ target_kind_required（v3.2.1：R0 未签收 target_kind 不放行；旧队列复跑
`require_target_kind=False` 豁免）。
③c 复活攻击完成度（v3.2：声称类 UNREACHABLE 必须有 resurrection_review；复跑 v3.2
机制发布前的旧队列（无 resurrection_review 字段）以 `require_resurrection=False`
豁免——产出 warn 注记不阻断，禁止伪造复活记录，同 ⑧ 先例，v3.4.2）。
另输出 `r4_feedback` 告警（warn 级不阻断 PASS）：
R4 H-7 默认值盘点与 R3 REACHABLE gate 证据的 key:value 冲突 → 主代理裁决纠正（W6 §25.6）。

## 📊 报告

`--stage report` 机械生成 `.audit_results/reachable_vulnerabilities_report.md`
（队列派生，REQ-V3.3.2-007：verify_queue.json 是唯一事实源；写入状态走 stderr，
stdout 保持纯 JSON 契约）。结构（v3.7，SWR-V3.7-002）：

- **一、问题清单**（确认问题全集，按严重程度排序）：严重 → 高 → 中三节。
  来源 = R3 REACHABLE 候选（机械映射，见下表；行内渲染 severity 来源 →
  可问责，REQ-V3-006）**∪ R4 confirmed findings（severity 申报值归一化
  High/Medium 并入，行内标 R4:H-x-Fn；Low 留附录 B 表；r3_link 指向候选的
  同事实条目不重复列，清单尾注去重说明，SWR-V3.4.3-060）**。
  每行 `ID | 问题摘要(claim_type+evidence 首 120 字) | 位置 file:line | CWE |
  证据等级 | 复核(证伪者结果/R4 确认（无 R3.5 复核）)`
- **二、问题详情**：确认问题全集每条一节——R3 条目：位置/语言、CWE/claim_type、
  verdict+证据分级（grade_recomputed_by 如有）、调用链逐跳+depth+
  reachability_type、证据、blocking_point 前提逐条（PREC-CONDITIONAL-REACHABLE-001）、
  独立复核 refutation{}、实证记录 empirical{}、修复建议（R4 finding fix 命中，
  否则「（主代理补充）」）；R4 条目：来源（R4 假说确认，无 R3.5 独立复核）、
  CWE/claim_type、要点、证据、实证结果 empirical_result、追踪 surface、修复建议
- **三、修复建议与结论（主代理补充）**：仅此段 + 头部审计基线由主代理补写；
  **补充后不得重跑 `--stage report`**（机械渲染会覆盖本段）
- **附录 A：NEEDS_REVIEW 清单与同事实映射**（REQ-V3.1-092）：成因双分
  （`保守裁决`（防御证据充分但门禁压力下保守）vs `证据不足`（前提/调用边无法
  取证）；未注明交主代理确认）+ correction_record 理由 + NEEDS_REVIEW ↔
  R4 hypothesis/finding 映射行
- **附录 B：审计过程信息**：B.1 规模对照（候选/假设/surface 数、闭合率）→
  B.2 语言覆盖表（v3.2.1 `组件角色` 列：server-side/client-only/build-config，
  `language_inventory` 现场重算；判据①：服务端组件语言 ≥1 surface 且非零候选；
  客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据）→ B.3 FFI 边界表 →
  B.4 R4 假说 verdict 表 → B.5 六门禁断言（机械调用 assert_ledger 渲染
  ①-⑧+③c，未过 → FAIL 行）→ B.6 覆盖账本（coverage_ledger 字段机械渲染，
  REQ-V3.4-007——本批新增覆盖格与仍存缺口格，为下批选题依据）

严重程度机械映射（cwe 列表 + sink_type 全量 `CWE-(\d+)` 提取取 max；
`severity_override` 合法值 {critical,high,medium} + reason 优先，非法值回退
机械值 + 告警行）：
| 级别 | 账本族（CWE） |
|---|---|
| 严重 | 注入/反序列化（78/94/77/502）+ MEMORY-SAFETY（787/125/416/415/476/190/129） |
| 高 | SQLi/路径/SSRF（89/74/22/918）+ 鉴权主体（862/863/639/306）+ RESOURCE-DOS（400/770/789/409/833/834）+ RACE（362/366/367） |
| 中 | XSS/弱鉴权（79/601/352/285/287/926）+ CRYPTO/DATA-INTEGRITY（327/326/338/347/330/310/311/295/345/351/829） |

无 cwe 命中 → claim_type 回退（rce/leak→严重，crash/panic/oom/unbounded/
protocol_dos→高，xss→中）→ medium 默认。leak→严重已入表（REQ-V3.4.3-006）。

## 📏 数据模型速查

- **verify_queue.json**：`{candidates:[{id,source_file,source_line,sink_type,status:PENDING|VERIFIED|ESCALATED|NEEDS_REVIEW,verdict,reachability_type,call_chain[],call_chain_depth,edge_evidence[{edge,proof}],evidence_grade:static_only|edge_proven|empirically_confirmed,grade_self_reported,blocking_point,claim_type∈{crash,panic,oom,unbounded,xss,protocol_dos,rce,leak,other},severity_override∈{critical,high,medium}?,severity_override_reason?,attempt,escalated_reason,correction_record[],empirical{},resurrection_review{revived,outcome}}], r4_findings:[{hypothesis_id,verdict,findings[]}], escalated_signed_off}`
- **input_surface.json**：`{surfaces:[{id,name,type,entry_points[],taint_channels[],trust_boundary:{type},confidence,downstream_hints[]}], conflicts[], mirror_pairs[]}`
- **hypotheses.json**：`{hypotheses:[{id,surface_id,signature_id,semantic_family,cwe[],hit_sites[],checklist[]}], logic_hypotheses:[]}`（v3.4.5 起佐证器 gen 输出独立文件 `hypotheses_gen.json`——文件所有权分离，LLM 主路径产物不得被覆盖，主代理合并两文件）
- **语言词汇两轴（v3.5.2 注）**：① 签名标签 = 签名侧内部名，允许 superset（`cs`/`typescript`/`js` 等，校验白名单 VALID_LANGS）；② 账本/任务书/队列输出 = 归一化到账本 16 规范名（`cs↔csharp`、`ts`/`typescript`↔`javascript`、`ps↔powershell`）。跨模块 alias map 取值一致（有测试守卫），签名 L2 过滤双侧归一化后等值比较。
- **形态判定两轴（v3.5.2 注）**：`project_kind`（R1 上下文信号，4 值 {framework, library, infra, app}）与 `target_kind`（R0 门禁签收，3 值 {application, library, hybrid}）是**两个独立轴**——前者是测绘期上下文提示，后者是验证期门禁判据；不要混用（surface_mapper.py docstring 交叉引用）。

## ⚠️ 编排层四条铁律（W5 回归教训，强制执行）

1. **写读竞态**：读子智能体产出前必须重试校验；通知到达 ≠ 文件已 flush。
2. **schema 契约**：任务书内嵌 canonical schema（见 R1），校验器归一化是兜底不是依赖。
3. **证据裁决**：证据不匹配时不静默放行也不盲目拒收——suggested_line/suggested_lines 交主代理裁决，证据重写必带 `*_by: main-agent` 标记。
4. **args 形态纪律（v3.4.5, SWR-V3.4.5-005）**：派发 Workflow 时 args 必须按导出 `next_step` 声明的形态（对象包裹，`args={"candidates": <payload>}`）传递；裸数组是派发错误——脚本已容忍自动包装（机械兜底，SWR-V3.4.5-002），纪律上禁止依赖兜底（gRPC 复活波裸数组误传失败实录）。

## 📚 附录：资产地图

- 核心模块（skill 根）：`surface_mapper.py`（R1）/ `signature_lib.py`+`signature_matcher.py`（R0/R2）/ `evidence_ledger.py`（分级+六门禁+一致性断言）/ `harness_runner.py`（R5）/ `workflow_export.py`（Mode W）/ `checklist_binder.py`（清单绑定）/ `precedent_library.py`（先例裁决）/ `r2_guard.py`（假设 schema 守卫）
- `tools/batch_verify.py`：队列编排 CLI（collect/bump-attempt/workflow-script/r4-*/assert/status）
- `tools/gen_tracking.py`：需求追踪矩阵重建（文档工具）
- `resources/signature_library.json`：25 个签名（9 L3 语义族 + 16 L2 语言词族；回归锚点库在 `tests/fixtures/known_instances.json`，R0 完整性自检 + fixture 仓库 anchor recall；v3.6 起 L2 无确认锚点以 confirmed:false 占位诚实簿记）；`resources/precedent_library.json`：16 条裁决先例（v3.5.2 裁 9 条永不可达先例）；`resources/checklist_library.json`：30 条检查清单
- `task_templates/`：3 个任务书模板（surface_map_domain/hypothesis_filter/biz_hypothesis）；`templates/harness/`：5 个实证模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/parser_fuzz/resource_rate_probe）；`harness_manuals/`：16 语言工具链手册 + ENVIRONMENT_PROBES/mixed_build（共 18 个）
- `tests/`：243+ 个单测/集成测试（改模块后必须全绿）；`lessons/`：全部历史教训 + W5 回归发现
- v2.1 遗产：仅 `docs/legacy/SKILL_V2.1.md`（规范备份）

---

## 🆕 v3.1 增量（2026-08-17，15 语言战役 lessons W6 §1-24 的制度化）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_1.md`。v3.1 不改变阶段骨架，只把战役中主代理
> 手工补救的动作机械化。开发已完成（SWR-V3.1 43/43，73 测试全绿），Phase 3.1.3 验收通过后随 install 生效。

### R0 新增: maturity 判定
- `surface_mapper.py context` 输出 `project_kind ∈ {framework, library, infra, app}`
  与独立 `maturity` 信号（W6 §23.6/§24.6: 成熟框架 R4 产率三连超 R3）
- **v3.3 触发条件（REQ-V3.3-007）**: `maturity==mature` → R4 与 R3 并行启动，
  H1/H7 深度上调；project_kind==framework 不再单独触发；maturity 由 git 版本标签
  语义判定（≥1.0 稳定标签=mature），主代理复核后可手动覆盖

### R1 新增: validate v3.1 + 预算档位
- `surface_mapper.py repair` 行号漂移自动修复器（首行键全文件匹配 ±80 语义 +
  `suggested_line` + `paraphrased` 标记；幂等: 已修复 entry 不重标，W6 §18.7/§22.1/§9.5）
  **（v3.5.2 已裁除，行号漂移裁决为 R1.3 主代理手工职责——见 SKILL.md R1 铁律 3；v3.9 补注）**
- `surface_mapper.py tier` 规模档位: <100 文件 2 agents / 100-500 4 agents 无限时 /
  >500 4 agents + 45min 硬时限 + 10min 中间产物落盘（W6 §17.1/§18.6/§20.5/§24.7）

### R2 变更: LLM 主路径 + schema 强制
- **LLM 假设生成是正式主路径**（主代理或限时 agent 基于 surface 图生成）；签名命中
  降为佐证器（L1 通用危险词不再生成假设，W6 §14.1/§17.3 退役先例制度化）
- 假设 schema 强制 `surface_ids: []` 数组 + 锚点行 Read 验证 + keep/drop 全量落盘
  （W6 §9.6/§16.7/§23.7）
- 复审计: R2 上下文自动注入旧审计**终稿**摘要（W6 §22.2）

### R3 变更: verifier v3.1（步骤 0 + 清单 + 自证伪）
- **步骤 0 承重前提验证**（W6 §17.10）——前提断裂立即终止
- `checklist_binder.py` 按 cwe/关键词自动绑定家族检查清单（checklist_library.json
  29 条 CK-*，16 语言证伪者攻击面固化）；未执行清单的 REACHABLE 会被 R3.5 同款证伪
- 自证伪提示: 候选附先例库匹配的最可能证伪论据，verifier 自查（目标: R3.5 拦截率
  从 ~50% 收敛到 <30%）
- 轻量实证白名单 + `empirical` 字段结构化 + 范围分级
  `mechanism|function_body|full_chain|e2e`（机制级只能支撑 edge_proven，W6 §17.7）

### R3.5 变更: 工具箱 + 裁决先例库
- 证伪者实证工具箱按声称类别注入（区间类=参照模型+百万对拍 §21.1 / 解析类=真实
  构件+畸形矩阵 §19.4 / 代理分歧类=标准部署实测 §16.10）
- `precedent_library.json`（25 条先例）裁决匹配 + `evidence_ledger.py consistency`
  同族一致性断言（W6 §18.3 从证伪者武器升级为系统断言）
- refutation 结果 schema 新增 strengthened/attribution_correction/note（W6 §13.6/§12.5）

### R5 变更: 语言手册 + 环境陷阱自检 + 对照矩阵
- `harness_manuals/<lang>.md` × 15（工具链探测/版本义务/陷阱清单/阳性模式/网络依赖）
- 环境陷阱自检（stale 进程清理 + diag 路由 / daemon 线程 / env 传播验证 / PATH 检查）
- **环境能力探针（v3.3.2, SWR-V3.3.2-060）**：实证前按声称机制跑
  `harness_manuals/ENVIRONMENT_PROBES.md` 探针清单（syscall/依赖物化/工具替代/
  shell 陷阱）——探针失败记录 blocker 并触发 R5 可选路径裁决，不实证不申报
- 对照矩阵模式（默认拒绝 + 弱化接受，W6 §24.4）；源事实级降级规则（哨兵值/算术类，
  网络阻断记录 blocker，W6 §21.4）

### 门禁变更
- gate ③ 扩展至 R4 confirmed findings（W6 §18.9）
- 报告模板: NEEDS_REVIEW ↔ R4 finding 同事实映射表 + 前提逐条列出（W6 §24.9/§6）

### workflow 规范条款（强制）
- 顶层 const 模板字面量禁 `${}` 插值（`lint_script` 静态检查，W6 §17.2）
- resume 必须携带与首跑一致 args（脚本内 `args ?? {}` 防御，W6 §5）
- args 从落盘文件整读整传，禁止复制预览截断（W6 §10.3）
- journal 提取兼容 result/value 双字段；半程输出作废，只采信 schema-validated 最终返回
- collect 全家族 lenient load + 单遍转义修复（`evidence_ledger.load_lenient`，W6 §3.1-3.3）

### 验收判据（Phase 3.1.3）
akka-http / etcd / actix-web 三项目复跑对照:
① R3.5 拦截率下降（R3 质量上升） ② 原 REACHABLE 结论零丢失 ③ 六门禁全 PASS。
三条件同时满足才合并 main + install 到 skill 目录。

---

## 🆕 v3.2 增量（2026-08-17，混合语言项目能力 + 防漏放，已验收发布）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_2.md`。v3.2 不改变阶段骨架，把语言从
> 项目级属性降为候选级属性，并新增 R3.5-N 复活攻击。

### R0/R1: 语言清单 + boundary 第五域
- `surface_mapper.py context` 输出 `language_inventory`（每语言文件数/组件角色）
- R1 测绘 4 域 → **4+1 域**（boundary: 跨语言 FFI 边界调用表——extern/ctypes/cffi/
  cgo/N-API/JNI/embed/C-API 胶水，boundary surface 必填 boundary_kind + lang_pair）
- surface/entry_point/候选均带 lang 字段；任务书背景按语言分片
- `size_tier`: 2 语言项目 domains 含 boundary；3+ 语言保底 large 档（5 agents）

### R2/R3: 语言维度
- L2 词族按 surface.lang 过滤（C 词族不打 Rust surface）
- verifier 上下文语言按候选.lang 取；分级机械复核条款（v3.5.2 起 collect 内联
  重算为默认路径，`batch_verify.py <project> --stage grade-recheck` 降为可选
  维修工具——批量重算历史队列，差异写 grade_recomputed_by）
- CK-FFI-BOUNDARY（第 21 条清单）绑定 ffi/ctypes/extern 类候选

### R3.5-N（新）: UNREACHABLE 复活攻击
- 声称类（crash/panic/oom/unbounded/xss/protocol_dos）UNREACHABLE 全量 + 其他 20%
  抽样（最少 2，上限 8）做 N=1 尽力复活复核；抽样决策落盘 `_resurrect_sample.json`
  （selected/unselected/rule）——未入池候选无复活复核义务
- `workflow_export.export_script_resurrect` 导出；revived=true 回 R3 重验（附 gap），
  不直接改 verdict；全部候选落盘 resurrection_review（六门禁新增检查）
- **落盘契约（v3.2.2 文档化，REQ-V3.2.2-015）**：`resurrection_review` 必须写为
  **候选级 dict** `{"revived": bool, "outcome": "<理由>"}`——队列级 list 形态只作
  汇总记录，lessons_recorder 只读候选级字段（lenient 加载兜底，str 自动包装）。

### 裁决
- 同族一致性断言按 lang 分组（PREC-MULTI-LANG-001）；同 lang 组保持 v3.1 断言
- 报告新增语言覆盖表 + FFI 边界表

### 验收（Phase 3.2.3）
混合项目试审（≥3 语言 + FFI 边界）+ akka-http 单语言零回退回归。

## 🆕 v3.2.1 增量（2026-08-17，验收暴露四缺陷修复）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_2_1.md`。补丁版：不新增阶段、不改门禁语义。

### R0: target_kind 判定（REQ-V3.2.1-001~005）
见 R0 步骤 4：`tools/target_kind.py` 六类信号 → 推荐值 + 主代理签收 →
`verify_queue.target_kind`；门禁⑧ 未签收不放行。存在性规则按型装载（M2-3）：
application=三层检查含 shipped 实际值+运行时注册核实；library=公共 API 即边界
（仓内调用者缺失非阻断，死代码豁免不适用）；hybrid 按组件。

### R1: shipped-config 盘点（REQ-V3.2.1-030/031）
4+1 域合并后、R2 之前，对含 config 目录的组件跑 `workflow_export.export_script_shipped_config`
→ 每组件 1 agent 提取 tls/auth/监听/密码类键的**提交值 vs 代码零值** →
落盘 `.audit_results/shipped_config.json`。R2 gate 声称"默认可达"的假设强制引用
（r2_guard 提示）。动机: Lersosa CAND-001/008 的 `tls_enable` 代码零值误判 (W6 §25.4)。

### R3: verifier 任务书三段扩展（REQ-V3.2.1-010~012）
- 步骤 0.5 **模块可导入性预检**：顶层包解析 + DI 扫描器吞错路径审查 + broken_edge
  → NEEDS_REVIEW（模块存在≠被导入，Lersosa CAND-004/009 404 先例）
- 步骤 5.5 **消费端中间层枚举**（write→read 注入族）：缓存/门闩/降级层逐层列出
  + 三查（错误分支方向/写读形状/缓存键写路径，Lersosa CAND-007 Redis 门闩先例）
- target_kind 存在性规则段（由 verify_queue.target_kind 选择装载）
- 新清单 CK-IMPORT-REGISTRATION / CK-CACHE-GATE-LAYER（第 22/23 条）；
  新先例 PREC-TARGET-KIND-001 / PREC-IMPORT-BREAK-001

### 验收（Phase 3.2.1.3）
fixture→library、Lersosa→application 判定准确 + Lersosa 复跑零回退 + 六门禁⑧ PASS + install。

## 🆕 v3.3 增量（2026-08-19，偏见审查 5 大类裁决 + Lua 审计教训的制度化）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_3.md`（问题域 P-A~P-F）。
> 需求: `docs/design/REQ_V3_3.md`（14 条系统需求）/ `docs/design/SWR_V3_3.md`
> （35 条软件需求）。上游: 用户偏见审查（语言/CWE/形态/黑名单/保守倾向 5 大类,
> 主代理取证裁决 2 完全属实 + 3 部分属实）+ Lua 审计 SKILL_LESSONS_lua.md。

### 签名资产: 去 Web 化/系统语言扩充（P-A）
- L2 词族新增 **c/go/rust/java** 4 族（malloc 无上限家族/流式累积/unsafe-FFI/
  反序列化）；L3 新增 **SIG-STATE-RACE**（CWE-362/367）与 **SIG-CRYPTO-WEAK**
  （CWE-327/330）；既有 L3 补系统形态 grep hints——签名库 20 条
- integrity_selfcheck 新增 L2 词族 ↔ harness_manuals 覆盖对齐检查
  （cs↔csharp 命名不一致存量缺陷已修）

### 项目形态判定: 四值 + 信号加权（P-B）
- `project_kind` 四值 {framework, library, infra, app}——构建文件降为弱信号
  （权重 1），可执行入口（main/监听, 权重 3）与公共 API 主导（权重 2）为强信号；
  小写构建文件变体（makefile）检出修复
- `maturity` 独立信号（git 版本标签语义），R4 并行触发条件改为 maturity==mature

### 信任边界: host_api（P-C）
- trust_boundary.type 枚举补 **host_api**（宿主对公共 API 的调用进入；library
  组件默认）；R1 任务书增补「非网络/离线项目」映射指引（宿主 API 输入 →
  data_input + host_api，不得过度归 local/environment）
- verifier 任务书步骤 3 明示：跨库边界 ≠ 跨主体边界（R3.5 惯例假设拦截制度化）

### 保守倾向明示化（P-D）
- 「不实证不申报」（NEEDS_REVIEW 合法终态）为明示条款；报告 NEEDS_REVIEW 双成因
  （保守裁决 / 证据不足）；claim_type 枚举含 rce/other（v3.2.3 已入）

### 先例库（P-E）
- +PREC-ALLOC-VIRTUAL-001（分配请求≠资源耗尽：提交内存受输入限制→Low）、
  +PREC-ENV-SAME-PRINCIPAL-001（env→代码加载同主体边界几何→DIRECT+Low）

### 契约同步（P-F）
- tools/gen_tracking.py 扫描泛化至全部版本段；REQUIREMENTS_TRACKING.md 含
  v3~v3.3 全部需求；验收判据强制每版本一个新项目且须覆盖非 Web 形态

## 📝 R6：lessons 回写（审计闭合前置，v3.2 新增）

六门禁通过后、报告定稿前，强制生成代码审计问题文档：

```bash
python3 lessons_recorder.py <project> --write
# → lessons/SKILL_LESSONS_<project>.md（机械提取: 裁决纠正/降级/复活/分级重算/
#   paraphrased 标记/验收记录——全部来自 .audit_results/ 产物证据）
```

1. 主代理必须**人工补充过程观察段**（agent 行为/工具链陷阱/workflow 缺陷——
   非结构化数据无法机械提取），用 `write_lesson(project, process_notes=[...])`。
   幂等语义：write_lesson 全量重渲染（机械提取段 + 过程观察段），
   与 `--write` 调用顺序无关、重复调用不丢内容
2. 价值判定：高价值条目（新缺陷模式/语言盲区/裁决先例）当日并入
   W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；低价值条目留审计轨迹
3. 索引 lessons/README.md 自动更新；**未执行 R6 的审计不得闭合**（报告阶段门禁）

> **覆盖账本回填时序（v3.6 强制）**：`--stage coverage-ledger --write` 带两道机械前置——
> r4-assert（H1-H7 全 VERIFIED）与 r4_feedback 无未决冲突，不满足输出
> `LEDGER_WRITE_BLOCKED_*` 且不烧 sources key。正确时序：全部 cwe 修正
> （含 r4_feedback 裁决与 `r4_feedback_resolved` 落盘）→ r4-assert PASS →
> 六门禁全 PASS → `--write`。`LEDGER_IDEMPOTENT_SKIP` 会附打印本队将产生的
> new_counts；先回填后补标 cwe 的缺口格不回写（puma 审计 INJECTION×ruby 实录）。

## 🆕 v3.4.3 增量（2026-08-20，P0/P1/P2 验收缺陷闭环）

> 设计文档：`docs/design/SYSTEM_DESIGN_V3_4_3.md`（12 REQ）+ `SW_DESIGN_V3_4_3.md` + `SWR_V3_4_3.md`。
> 缺陷修复版：不新增阶段、不改六门禁①-⑧判据语义。17 项缺陷（12 代码 + 5 制度）制度化，
> 教训回填 lessons/W6 §32/§33。

### 收集链（P-A 修复）
- **r4-collect 自适应**（REQ-V3.4.3-001）：hypotheses 对象形态 / findings 顶层数组 /
  evidence 数组 / r3_link dict 四类漂移自动归一（v3.5 起不落 schema_normalized_by
  标记字段）；0 提取告警含形态诊断。canonical 输入零变化
- **surface id 前缀归一化**（REQ-V3.4.3-002）：surface_mapper merge 统一域前缀
  （SURF-DAT-*→SURF-DATA-* 等，写 normalized_ids）；r4-collect tracked_surfaces
  前缀模糊映射（写 mapped_surface_ids）；R4 任务书注入实际 id 清单 `{surface_id_list}`
  + canonical 输出示例
- **截断标记协议统一**（REQ-V3.4.3-003）：resurrect/refute 共用 `_truncate_evidence`——
  承重前提/实证/阻断/结论关键段必保留，次要段截断必带标记；消灭 1200 字符静默截断
- **grade 口径对齐**（REQ-V3.4.3-004）：collect 机械重算 `grade_verdict` 为唯一权威，
  verifier 自报值存 `grade_self_reported` 仅追溯；回填规范（backfilled_by + 实测数字）明示条款

### 门禁判定链（P-B 修复）
- **gate ③b 结构判定优先**（REQ-V3.4.3-005）：empirical_result 非空 + 实证特征
  （数字/输出/exit code）判定有实证，关键词表补「实测/measured」仅作 fallback
- **claim_type 加 "leak"**（REQ-V3.4.3-006）：信息泄露/env 反射类结构化表达
- **resurrect CLI**（REQ-V3.4.3-007）：`--stage workflow-script --mode resurrect` 导出 +
  `--stage r35n-collect --from-journal` 落盘候选级 resurrection_review（幂等）
- **boundary_kind 加 "capi"**（REQ-V3.4.3-008）

### 提示资产链（P-C 修复）
- **清单/PREC 适用性门控**（REQ-V3.4.3-009）：applicability_signals
  （text/requires_lang/requires_claim）作用于 checklist_binder 与先例自证伪提示；
  资源族信号不匹配 → 绑 CK-GENERIC-RESOURCE 兜底
- **H7 默认值全表预算 800→1200 字**（REQ-V3.4.3-010）
- **export lang 优先候选 lang 字段**（REQ-V3.4.3-011，_build_context 修复）

### 制度项（P-D）
- R4 同事实去重流程（SWR-V3.4.3-060）；实证回填规范（SWR-V3.4.3-061）；
  go/c 手册环境陷阱（SWR-V3.4.3-070/071）；先例 PREC-FAMILY-CONSISTENCY-001
  （跨项目同族判据：放大比是否常数因子 × 物化责任归属）

### 验收判据（Phase 3.4.3）
三锚点复跑零回退 + 17 缺陷各自可测闭环 + 一个未审新项目全流程（选题优先
coverage-ledger 缺口格），三条件满足才合并 main + install。

## 🆕 v3.4.4 增量（2026-08-21，v3.4.3 验收项目实测暴露缺陷修复）

> 设计文档: `docs/design/SWR_V3_4_4.md`（10 SWR）。修复批：不改变阶段骨架与门禁语义。

### R3/R3.5: 导出与收集契约修补
- **信号关键词词边界匹配**（SWR-V3.4.4-001）：checklist/precedent 的
  applicability_signals.text 与 requires_lang——ASCII 关键词按词边界
  （`(?<![a-z0-9])kw(?![a-z0-9])`），CJK 关键词保持子串语义
  （"ws" 不再误配 "jws"；"c" 不再误配 "scala"）
- **refutation 导出截断告警**（SWR-V3.4.4-003）：结果附 `qualified_total`
  与截断时 `truncated/exported/advice`——batch_size 静默截断曾致主代理
  误判资格全集
- **collect 报错指引**（SWR-V3.4.4-004）：对 refutation journal 误跑 collect
  时指引 `--stage r35-collect`
- **tooling 版本守卫**（SWR-V3.4.4-008）：导出脚本内嵌 TOOLING_VERSION，
  collect/r35-collect/r35n-collect 比对本地版本，漂移输出 warn
  （导出/收集两端代码版本不一致的机械防线）
- workflow_export.py CLI 支持 `--mode resurrect`（SWR-V3.4.4-010）

### R3.5: 任务书防误报条款
- verifier 任务书新增：**计数类观测不做可复现证据**（SWR-V3.4.4-007）——
  几何随机变量（素性试除次数等）单次观测方向可翻转，只标"数量级参考"

### R4: 收集语义与任务书修补
- **r4-collect 保留主代理裁决字段**（SWR-V3.4.4-002）：按 finding title 匹配，
  已裁决 finding（claim_nulled_by/empirical_verified_by/correction_record）
  的裁决字段强制保留、empirical_result 的 CONFIRMED/REFUTED 标记强制保留、
  evidence 裁决尾追加——重复 collect 不再抹掉主代理裁决
- R4 任务书新增**部署布局义务**（SWR-V3.4.4-005）：实证必须在部署布局
  （npm main/bundle/官方构建产物）执行，vm 全量加载 src 不构成部署布局实证；
  模块不在任何发布产物 → 不构成可达声称（claim_type 置空，源码卫生缺陷）
- R4 任务书 **empirical_result 前缀契约**（SWR-V3.4.4-006）：
  `CONFIRMED:`/`REFUTED:`/`SOURCE_FACT:` 前缀——gate ③b 结构判定只识别该前缀，
  消除真实实证缺标记被误拦截整类问题

### R6: lessons_recorder 项目名绝对化（SWR-V3.4.4-009）
相对路径 "." 不再产出空/异常文件名。

### 验收判据（Phase 3.4.4）
test_v344.py 10 项全绿 + 全量回归零失败 + jsrsasign 队列受影响阶段复跑零回退，
三条件满足才合并 main + install。

---

## 🆕 v3.5 增量（2026-08-23，三项体检修复：偏见 / 过设计 / 项目残留）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_5.md` + `docs/design/SWR_V3_5.md`（15 SWR）。
> 评估报告: `docs/history/HEALTHCHECK_EVAL_V3_5.md`（含 B 裁决 10 项，本轮不修，只记入报告）。
> 范围: 高优先级发现（残留 3 + 偏见 5）+ 过设计 A 清单死资产 + 文档漂移。
> 修复后三项体检逐条机器守卫（tests/test_deproject_assets.py 等），防回退。

### 去项目化（三禁止机器化）
- **先例库形状抽象**（SWR-V3.5-001）：precedent_library 五字段
  （name/criterion/counterexample/applicability_scope/applications）零项目 token——
  self_refutation_hints() 注入 verifier 任务书的内容全部为机制形态描述，
  项目名只留 source_lessons 追溯字段
- **xss_path_sim 去项目化**（SWR-V3.5-002）：AWStats 专属复刻整文件移入
  `tests/fixtures/xss_path_sim_awstats_anchor.pl`（fixture 豁免区）；
  templates/harness/xss_path_sim.pl 重写为参数化通用骨架（argv 读 JSON 链描述）；
  模板名不变，全部接线保持
- **手册抽象**（SWR-V3.5-003）：harness_manuals 项目名 → 机制形态 + W6 § 引用；
  6 处 /root/ 绝对路径 → $HOME/环境变量占位
- **运行时资产残留扫描**（SWR-V3.5-015）：signature_lib `_scan_runtime_assets()`
  遍历 templates/ + harness_manuals/（黑名单 token 大小写不敏感 + /root/ 路径），
  挂入 R0 selfcheck 完整性分支——模板/手册残留回退被机器拦截

### 偏见修复
- **harness 端口参数化**（SWR-V3.5-004）：ws_frame_alloc/accum 的 ktor/actix
  历史端口 18083/18084 → `python3 ws_frame_*.py <host> <port>` 必传参数
- **step 0.5 static_short 按语言家族分派**（SWR-V3.5-005）：c/cpp 措辞保留；
  go/rust/jvm（sourceSet）/dotnet（.csproj）/swift（Package.swift）/script 族
  （require/include/use/source 加载闭包核对）各得语义——不再对库型候选派发
  纯 C 系词汇（CMake/GOPATH/cargo/Makefile）
- **R0 形态分类语言门补全**（SWR-V3.5-006/007）：target_kind 扩展名白名单补
  .swift/.kt/.cs/.pl/.pm/.ps1/.sh，包清单解析补 pom.xml/composer.json/
  Gemfile/gemspec；surface_mapper _SRC_EXTS 补 6 扩展名、main 模式补
  Kotlin `fun main(`/C# `static void Main`/Swift `@main`（MULTILINE 移入
  compile）、listen 模式补 HttpListener/TCPServer/stream_socket_server/
  IO::Socket::INET；Go/Java 独享无-main 特判 → LANG_NO_MAIN_LIBRARY 泛化
  11 语言（排除 shell/c/cpp 保持保守，go/java 行为不变）
- **签名 fixture 全覆盖**（SWR-V3.5-008）：20/20 签名 confirmed 锚点
  （tests/fixtures/known_instances.json，L3 系补 7、L2 词族 6 个 line=1 假占位
  换真实项目锚点、4 条漂移锚点重定位）；smoke_test 多实例回退；存量正则缺陷
  `[ScriptBlock]::Create` 转义修复
- **覆盖账本格压力提示**（SWR-V3.5-009）：pressure_cells（count≥15 标
  saturated）+ family_skew（top_share 降序）+ 选题提示「优先补零格；
  saturated 格不建议再选题」——无新门禁/无新持久字段/无新强制义务

### 过设计 A 清单死资产删除
- 死 stage（next-cluster/cluster-collect/coverage + r15 分支 + 4 CLI 参数）
  / 死函数（bind_all/h7_template_bind/record_application/add_precedent/
  emit_filter_tasks）/ 死字段 13（含 coverage_bridge）/ 死模板 4/7 /
  multipart_align 悬空注册 / repair_stats 死读（SWR-V3.5-010~013）
- **门禁⑦ 语义保留**（SWR-V3.5-012）：coverage_bridge 载体删除但覆盖率簿记
  保留——门禁代码块改传 `tracked_ids` + `mirror_pairs`（此前文档路径只传计数
  导致镜像传播被静默跳过）；relay 中继面直接并入 tracked_ids，覆盖依据写入
  R4 finding evidence 文本

### 文档与测试
- 资产地图/README 计数更新为磁盘实况：20 签名（9 L3 + 11 L2）、25 先例、
  29 清单、4 实证模板、3 任务书、18 手册、190 测试（SWR-V3.5-014）；
  TOOLING_VERSION → "3.5"
- 新增 tests/test_deproject_assets.py 5 用例 + 各模块防回退断言
  （SWR-V3.5-015）——文档计数、家族措辞、语言门、ledger 压力、fixture 全
  覆盖全部有测试守

### 验收判据（Phase 3.5）
190 测试全绿（172 + 18 新增/改写）+ `signature_lib.py selfcheck` 对 18 个
锚点项目 `hit_rate=100% testable=20` + 自身仓库完整性零违规 + phpseclib
新项目验收（六门禁全 PASS + coverage-ledger --write 回填 php×CRYPTO 零格）
三条件满足才 install + 提交。

---

## 🆕 v3.5.2 增量（2026-08-23，残留中项清零 + 过设计 B 裁决执行 + 偏见机械修复）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_5_2.md` + `docs/design/SWR_V3_5_2.md`。
> 范围（用户确认）：①残留中项全部 ②过设计 B 裁决 10 项（按评估倾向执行）
> ③偏见中「机械可修」项。内容补全类（L2 词族 5 语言 / env 陷阱 9 语言 /
> L3 语义族脚本 token）留 v3.6 已处理（见下节 v3.6 增量）；8 语言 harness
> 模板 v3.6 按用户裁决改为裁减 + 提炼 1 个通用协议级模板；锚点 swift 已由
> v3.5 覆盖（SWR-V3.5-011）。

### 残留中项清零（去项目化）
- checklist_library steps 4 处 → 机制形态（框架 CAND-001 对照 etcd CAND-004 双实测量级对照法 /
  脚本语言过滤回调类 / 哈希缓存键未注册先例）；binding keywords "netty" 删；
  uwebsockets/hikaricp 在 source_lessons = 合法来源列保留
- task_templates / parser_fuzz_c.py docstring / target_kind.py 启动链正则
  （删 BeanContainerManager/ActixSystem::new，补 SpringApplication.run）→ 机制形态
- SKILL.md 主文例证 → 机制形态；`_scan_runtime_assets` 扫描扩 task_templates（注入违规测试闭环）

### 过设计 B 裁决执行（10 项）
| # | 裁决 | 执行 |
|---|---|---|
| B1 | **全裁 ast_scanner 三联体**（与评估倾向差异见下） | 裁 ast_scanner.py + anchor_registry.json + security_profiles.json；REQ-V3-002 tracking → 已裁除 |
| B2 | 裁 r05_diff_archaeology.py | 裁文件 + 2 测试；R0.5 现役 = surface_mapper scope_diff |
| B3 | grade-recheck 降可选维修工具 | collect 内联重算为默认；stage 处理器 + CLI 保留 |
| B4 | 裁 repair_surfaces | 裁函数 + CLI（零调用零测试） |
| B5 | 裁 signature_tier/empirical_harness 字段 | 裁 20 签名字段 + REQUIRED_FIELDS + matcher 输出；**needs_harness 保留偏差见下** |
| B6 | 裁 harness_coverage_matrix.json | 裁文件（零读者） |
| B7 | parser_fuzz 保留 | SKILL.md R5 枚举补 parser_fuzz + 防回退测试 |
| B8 | 裁 9/25 条永不可达先例 | 25→16；`test_precedents_all_matchable` 双向断言（match() 可达集 == 库 id 集） |
| B9 | CK-EMPIRICAL-SCOPE 真实绑定 | 删 binder matched=[] 特判 → R5 语义空间（empirical dict / claim_type ∈ R5 强制集）触发绑定 |
| B10 | 文档漂移 | v3.5 已修，无动作 |

### 偏见机械修复
- 语言词汇归一：账本 16 规范名（cs↔csharp、ts/typescript/js↔javascript）；签名标签
  保留 superset 内部名；L2 过滤双侧归一化等值比较；跨模块 alias 一致性测试
- harness_runner manual/traps 缺 lang 参数报 usage exit=2（删默认 rust）；
  lang_pair 白名单 {c,py,rust,js,ts} 删除（任意语言小写接受）
- boundary_kind +cgo（描述文补 cgo/capi）；步骤 5.5 Go 习语中立化；
  双轨词汇文档（project_kind 上下文信号 vs target_kind 门禁判据两轴注）

### 与评估倾向的差异（批准本方案即同意）
- **B1**：评估倾向「保留 ast_scanner、裁 security_profiles」。探查证据推翻——
  security_profiles.json 唯一读取方是 ast_scanner 自身（:928/:1186），ast_scanner
  零生产调用方（v3.1→v3.5「按需使用」零触发）；保扫描器裁其唯一功能输入 = 保空壳。
  **实际执行：三联体全裁**。
- **B5**：评估「确认 needs_harness 后裁决」。探查发现 needs_harness 并非零调用方——
  tests/test_integration.py:82 将其用作 R5 触发判定（步骤 6）。**实际执行：保留
  needs_harness + 其 3 个单元测试 + 集成测试；仅裁 `check` CLI 入口**。

### 验收（回归）
193 测试全绿 + `signature_lib.py selfcheck /root/phpseclib` exit 0 + install 后 DST
pytest 全绿（phpseclib R0 复跑回归，不新增完整项目验收——用户确认）。

---

## 🆕 v3.6 增量（2026-08-23，评估驱动机制修复 + 内容补全，无设计膨胀）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_6.md` + `docs/design/SWR_V3_6.md`。
> 范围（用户三约束）：**保持通用性 / 不携带审计历史信息 / 不出现无用设计**——
> 所有机制改动以 puma 实战验收（AUDIT_EVAL_V3_5_2.md）暴露缺口为准绳。

### 机制修复（P1，评估驱动）
- **B9 清单注入时点修复**（`workflow_export.py` refutation 分支）：旧实现
  `_in_r5_semantic_space` 在 verify 导出时恒空（PENDING 无 cwe/claim_type）且
  refutation 分支不注入 → 家族检查清单零到达。v3.6 起 refutation 时点复用
  `_checklist_section`（此时 cwe/claim_type 已由 collect 落盘），CK-EMPIRICAL-SCOPE
  以 r5-semantic 绑定注入两个证伪者 prompt。resurrect 分支与 Mode A' 不加代码
  （语境/成本裁决，见 SWR_V3_6）。
- **R2「防御已到位」核查义务**（`task_templates/hypothesis_filter.md`）：bc/防御
  已到位类 drop 前必须核查**默认权限上下文**（文件/目录/umask/监听 socket 权限、
  环境变量默认值、启动命令注入点）并引用源码证据行（file:line）——只看 gate
  存在性不算核查（puma HYP-005/006 误 drop 实录：默认 token 随机 + 权限上下文
  使防御失效）。不做 r2_guard 机械 warn（误报>收益裁决）。
- **EMPIRICAL_CLAIMS 8 类对称**（`harness_runner.py`/`evidence_ledger.py`）：
  旧 6 类集缺 rce/leak → 对齐 binder R5_CLAIM_TYPES 8 类。rce/leak 声称现在
  强制实证（此前能绑清单却不触发 harness——对称缺口）。
- **账本回填机械前置**（`tools/batch_verify.py` coverage-ledger `--write`）：
  幂等检查后两道前置——r4_findings 全 VERIFIED（缺即 `LEDGER_WRITE_BLOCKED_R4`）
  + r4_feedback 无未决冲突（`LEDGER_WRITE_BLOCKED_FEEDBACK`），不满足 exit 1
  **不烧 sources key**（puma 实录：先回填后补标 cwe 使缺口不可回写）。
  幂等分支附打印 `would_be_new_counts`。**回填时序强制**：cwe 修正（含
  r4_feedback 裁决）→ r4-assert PASS → 六门禁 → `--write`。

### 内容补全（P2，v3.5.2 遗留 + 用户裁决）
- **L2 词族 5 语言**：signature_library 20→25（SIG-RB-EVAL-001 / SIG-PHP-EVAL-001 /
  SIG-PERL-EXEC-001 / SIG-SCALA-UNSAFE-001 / SIG-SWIFT-UNSAFE-001）。新签名无
  确认锚点 → fixtures 以 `confirmed:false` 占位诚实簿记（不伪造 confirmed）。
- **env 陷阱 9 语言**：`PER_LANG_ENV_TRAPS` 7→16 语言（对齐 harness_manuals/）。
- **L3 语义族脚本 token**：5 个 L3 签名 grep 补 PHP/JS/ruby/shell/python 形态
  （佐证器粗粒度 hint 设计，非判定器）。
- **8 语言 harness 模板 → 裁减 + 提炼 1 个通用协议级模板**（用户裁决）：
  `templates/harness/resource_rate_probe.py`（langs:["any"]）——并发连接灌注 +
  逐秒 VmRSS + 拒绝计数 + delivery-rate 确认 + 停止后回落验证 + 单调性判定，
  完全去项目化（argv 必传 host/port）。

### 验收判据（Phase 3.6）
204 测试全绿（193 基线 + 11 新增）+ `signature_lib.py selfcheck /root/phpseclib`
exit 0 + install 后 DST pytest 全绿 + 分阶段 commit（P1→P2→P3→P4）。新在线
项目实战验收（覆盖账本缺口格）另行启动。

## 🆕 v3.7 增量（2026-08-23，报告格式重构：问题清单按严重程度排序 + 机械生成 + 附录化）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_7.md`。用户要求重新设计
> `reachable_vulnerabilities_report.md`：简单明了说明有哪些代码问题、按严重程度
> 排序、提供相关细节。三项决策：① 严重程度 = 机械映射（cwe/claim_type）+ 主代理
> 可覆盖；② 生成方式 = 扩展 `--stage report` 机械生成完整报告（队列派生，
> REQ-V3.3.2-007）；③ 审计过程信息移入附录。

- **严重程度机械映射**（`tools/batch_verify.py` 模块级）：`SEVERITY_BY_CWE` 按
  账本族分组（严重=注入/反序列化 + MEMORY-SAFETY；高=SQLi/路径/SSRF + 鉴权主体 +
  RESOURCE-DOS + RACE；中=XSS/弱鉴权 + CRYPTO/DATA-INTEGRITY）；cwe 列表 +
  sink_type 全量 `CWE-(\d+)` 提取取 max → claim_type 回退（rce/leak→严重，
  crash/panic/oom/unbounded/protocol_dos→高，xss→中）→ medium 默认。
  `severity_override`（合法值 {critical,high,medium} + reason）优先，非法值回退
  机械值 + 告警行。问题摘要改用 claim_type + evidence 首 120 字（summary 字段
  collect 不落盘）。
- **机械渲染 render_report_md**（SWR-V3.7-002）：`--stage report` 末尾写
  `.audit_results/reachable_vulnerabilities_report.md`（写入状态走 stderr，
  stdout 保持纯 JSON 契约）。结构：一、问题清单（REACHABLE only，严重/高/中
  三节表）；二、问题详情（每条一节：调用链/前提/复核/实证/修复建议）；三、
  修复建议与结论（主代理补充，补充后不得重跑 report 覆盖）；附录 A =
  NEEDS_REVIEW 成因双分 + 同事实映射；附录 B = 规模对照/语言覆盖表（角色现场
  重算）/FFI 边界/R4 verdict/六门禁断言（机械调用 assert_ledger）/覆盖账本。
  **铁律：所有可选输入缺失时降级渲染占位，绝不抛异常**（test_end_to_end
  最小队列形态）。
- **stage_collect 透传**：severity_override/severity_override_reason 白名单
  落盘（队列 JSON 仍是唯一事实源，可直接编辑）。
- **R4 confirmed 并入问题清单（SWR-V3.7-009/010）**：确认问题全集 = R3
  REACHABLE 候选 ∪ R4 confirmed findings（High/Medium，申报值归一化；
  Low 留附录 B——含「正向确认」非漏洞条目自动排除；r3_link 指向候选的同事实
  条目不重复列，清单尾注去重说明）。puma 实录: no_token 控制端点零鉴权
  （H-5-F1）与跨用户停服（H-6-F1）从附录表升入「高」节。

### 验收判据（Phase 3.7）
218 测试全绿（204 基线 + 14 新增 tests/test_v37_report.py）+ `signature_lib.py
selfcheck /root/phpseclib` exit 0 + puma 真实队列临时副本冒烟（分级/排序/附录
真实性人工检查，不覆盖既有报告）+ install 后 DST pytest 全绿 + 分阶段 commit
（渲染+测试 → 文档+版本链 → R4 并入增强）。

## 🆕 v3.9 增量（2026-08-28，Pillow 审计复盘缺陷修复）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_9.md` + `REQ_V3_9.md` + `SWR_V3_9.md`。
> 缺陷修复版：不改变阶段骨架、不改变门禁①-⑧判据语义（③ 新增子判据 ③d）。

### 收集与渲染（P0）
- **r4-collect 前置守卫**（REQ-V3.9-001/002）：`_adapt_r4_finding` 归一化扩展
  （cwe 字符串/call_chain 字符串/location 别名/surfaces 别名，写 flags）；
  tracked_surfaces 缺失且不可恢复 → `R4_TRACKED_MISSING` 硬失败、该 hypothesis
  不合并（原子性）——静默缺簿记导致门禁⑦ 假失败反向制造手工补救（Pillow H7 实录）
- **报告渲染三修**（REQ-V3.9-003/004/005）：附录 A 改双语义过滤
  （status=VERIFIED 且 verdict=NEEDS_REVIEW——collect 终态语义）；
  B.2 双侧 lang 经 `_norm_lang` 归一后 join（surface 规范名 vs inventory 扩展名
  词汇不匹配致计数恒 0）；R4 行位置列取 `call_chain[0]`/location（`_r4_location`）
- **tracked-ids 机械化**（REQ-V3.9-006）：新 `--stage tracked-ids`——优先
  r2_filter_result.json 三组 surface_ids（SWR-V3.4.6-002 保真契约）∪ R4 ∪
  coverage_bridge，落盘 `_tracked_ids.json`，覆盖率 <100% exit 1
- **export 落盘 payload**（REQ-V3.9-007）：`<mode>_payload.json` 落盘，
  next_step 引用该路径（"整读整传"条款此前无文件可读）

### 门禁与提示资产（P1/P2）
- **门禁 ③d**（REQ-V3.9-010）：R4 confirmed finding（High/Medium/Critical 且
  empirical_result 前缀 CONFIRMED）须有 `independent_review {by,method,artifacts}`
  或非空 r3_link——放行方向对抗复核（REQ-V3.2-021 精神）在 R4 通道补位；
  `require_r4_independent=False` 豁免旧队列复跑（warn 注记，同 ⑧/③c 先例）；
  B.5 增行、问题详情渲染该字段
- **R1 任务书双向核实条款**（REQ-V3.9-008）：命中共享 helper/allocator/工厂时，
  边界声称须沿调用链双向核实（两次误报同模式：漏看调用者前置守卫/漏看被调者
  前置检查）
- **新清单 CK-POSTOP-INVARIANT**（REQ-V3.9-009，库 29→30）：后置检查+循环
  不变量论证——判缺陷前须证明不变量破坏（两次将"检查在操作后但靠对齐不变量
  兜底"的形态误判为缺陷）
- **文档漂移**（REQ-V3.9-011）：SKILL.md repair 裁除注记；
  workflow_export.TOOLING_VERSION 3.7→3.9（版本守卫数据本身漂移两版）
- **cve-ghsa-draft**（REQ-V3.9-012）：新 `tools/check_no_cjk.py` 零中文检查脚本

### 撤销记录（防义务棘轮）
- 原 P1-6（assert_ledger 逐门输出）：代码复查确认现有 `(ok, violations)` 契约
  已枚举全部 blocking 违规，无失误案例支撑，不做修改。

### 验收判据（Phase 3.9）
243 基线全绿 + 新增 test_v39 ≥12 用例 + `signature_lib.py selfcheck /root/Pillow`
exit 0（去项目化扫描绿）+ Pillow 真实队列复跑（六门禁含 ③d 全 PASS、报告三处
渲染缺陷消失且主代理零手工编辑）。

## 🆕 v3.10 增量（2026-08-28，kernel 级项目首例审计复盘缺陷修复）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_10.md` + `REQ_V3_10.md` + `SWR_V3_10.md`。
> 缺陷修复版：不改变阶段骨架、不改变六门禁①-⑧判据语义、不改变队列数据模型主体。
> 复盘来源：2026-08-28 首次 kernel 级项目全流程审计（五波、109 假设、10 候选、
> 六门禁全 PASS）。13 项复盘发现 → 修复 12 项、撤销 2 项（含 1 项复盘误报）。

### 覆盖率簿记（P-A）
- **tracked 提取源扩展**（REQ-V3.10-001）：①`r2_filter_result*.json` 全波次文件
  glob 合并三组 surface_ids（多波批次形态，主文件与分波文件同权）②
  `logic_hypotheses[].surface_ids` 恒并入（与门禁⑦语义对齐："R2 假设 surface_ids"
  含 logic 组——防御裁决面的覆盖簿记）③兜底路径不变
- **R4 假说级 tracked_surfaces**（REQ-V3.10-002/003）：reviewed_clean/not_applicable
  （或 confirmed 但 findings 空）假说的审查触及面结构化落盘——条件触发（有 finding
  载体不重复），r4-collect 幂等合并为 `hypothesis_tracked_surfaces`，防"审查触达与
  覆盖率簿记脱节"（reviewed_clean 假说审大量面却零簿记, 覆盖率假失败实录）
- **r2_guard fidelity 波次回退**（REQ-V3.10-004）：主 hypotheses.json 缺失时
  glob `_r2_hypotheses_*.json` 合并反查，全部缺失才 WARN

### 实证回填契约（P-B）
- **empirical dict 键名规范化**（REQ-V3.10-005）：canonical 键集（保留键
  outcome/evidence_numbers/report + 标准键 harness/method/input/result/verdict/
  backfilled_by）；渲染器容错读双形态（缺失回退，绝不抛异常）——修复报告渲染
  把实测数据全部渲染为 None 的契约缺口

### 边证据检测（P-C）
- **edge_gap 显式信号**（REQ-V3.10-006）：collect 时 grade 重算 static_only 且
  自报更高 → 输出 `edge_gap`（边数 vs 跳数-1 + "疑似合并边"补拆指引）——
  修复"禁止合并多跳"条款无机械检查点、违反只能静默降级事后暴露的问题

### 任务书与门禁一致性（P-E）
- **R4 empirical_result 指引与 gate 豁免一致**（REQ-V3.10-007）：Low+声称类
  必须填机制级描述文本（含"静态/机制级/源码级"措辞）——填 null 会触发
  empirical_required_r4 违规；High/Medium/Critical 声称类沿用不实证不申报

### 任务书资产中立化（P-F，去项目化）
- **部署布局义务生态中立化**（REQ-V3.10-008）：发布面三查按构建系统分派
  （包清单 files/构建产物/发布面入口）+ 编译开关面查询（Kconfig 提交值/Cargo
  features/CMake 选项/Gradle buildTypes 等作分派例）——"不在发布产物/编译面 →
  不构成可达声称"语义不变，措辞不再单吊一种生态
- **shipped-config 编译开关键通用形态**（REQ-V3.10-009）：config/features/开关类
  键的"提交值 vs 代码默认值"（含显式关闭为提交值）与服务端框架键清单并列按
  形态分派
- **focus_sink 纯格式契约**（REQ-V3.10-010）：`path:line` 纯格式（相对项目根），
  说明入 note——修复带后缀格式致簇化入队失败
- **verifier/refuter 任务书补两步**（REQ-V3.10-011）：路径格式统一条款 +
  upstream 修复搜索步骤（git log -S / CVE 补丁核对 / "快照落于修复前/后窗口"
  写进证据——上游补丁存在性是候选可信度最强旁证）。**首发归属增补**（同日
  增补，2026-08-28 发现链核查实录）：命中"公开补丁未合并"或"已有 CVE"时
  标注发现链（发现者/补丁作者/时间）与补丁状态，evidence 写明"非首发发现"
  ——主代理收尾按"推补丁合并 + 佐证材料"路径，申报不得以首发口径

### 提示资产（P-G）
- **parser_fuzz 有状态 stub 指引**（REQ-V3.10-012）：无符号下溢语义保留/边界
  指针语义/分配布局模拟/逐字提取纪律/消费侧复刻——模板 docstring + c 手册第 7 节

### 版本链（收尾）
- TOOLING_VERSION → "3.10"；tests/test_v310.py 覆盖全部可测需求

### 撤销记录（防义务棘轮）
- P-D 撤销（复盘误报）：shipped-config workflow 返回契约本就正确（`{mode,
  inventories, missing}` 包装），误报根源是主代理收集时读了 per-agent journal
  行——形态差异补入 collect 指引文档，不改代码
- P-H 撤销：batch-size 截断已有 advice 显式提示（两次均依提示重导出，无失误
  案例）；payload_hash 辅助无失误案例支撑——均不建

### 验收判据（Phase 3.10）
全量回归测试全绿（243 基线 + test_v310 新增）+ kernel 受影响阶段复跑零回退
（tracked-ids 152/152 无手工补丁、collect 输出 edge_gap 信号、报告渲染实证数据
完整）+ `_scan_runtime_assets` 去项目化扫描绿 + 三锚点 fixture 复跑零回退
（新项目全流程验收随下一在线项目进行）。

## 🆕 v3.10.2 增量（2026-08-29，多媒体系列 7 项目批次复盘缺陷修复）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_10_2.md` + REQ/SOFTWARE_DESIGN/SWR_V3_10_2。
> 背景审计: 2026-08-29 多媒体系列批次（7 项目、双并行 × 4 波、六门禁 7/7 全 PASS）。
> 复盘发现 13 项问题（Q-A~Q-M）→ 本版修复 13 项、维持撤销 2 项。
> 不改变阶段骨架、六门禁判据语义、队列数据模型主体。

### 机制新增（机械层）

1. **实证保真度三档（SWR-V3.10.2-001~004）**：`empirical.fidelity` 枚举
   `real_target | equivalent | mechanism`（缺省 real_target，旧队列零行为变化）。
   `equivalent`（等价语义复现）满足 gate ③ 但报告行首渲染 `等价复现:` 前缀、
   gate 输出 `fidelity_hint` 分列；`mechanism` 不得升 `empirically_confirmed`。
   申报材料必须按档位标注（真实构建物与复刻证据分列，不混级申报）。
2. **workflow args fail-fast（SWR-V3.10.2-005）**：导出脚本（verify/refutation/
   resurrect）在 agent 任务内首步校验输入键（`c.prompt`/`c.taskFile` 至少其一
   非空），缺失时不派发 agent、返回结构化错误——「undefined prompt 幻觉
   verdict」事故的制度化拦截；collect 后验 `journal_anomaly` 告警（同 id 多
   result 内容各异）。
3. **R4 簿记容错（SWR-V3.10.2-007/008）**：r4-collect 兼容 finding 级
   `surfaces` 别名（canonical hypotheses-list 形态此前不经别名映射）；空
   findings 假说须声明假说级全量扫掠 tracked（完全无 tracked 仍拦截）。
4. **报告防覆盖（SWR-V3.10.2-009）**：`--stage report` 检测主代理段落已存在
   时拒绝重跑（exit 1），`--force` 显式重生成并告警。
5. **NEEDS_REVIEW 重开（SWR-V3.10.2-012）**：`--stage reopen --id <id>` +
   `REOPEN_REASON` 环境变量——环境 blocker 解除后回 PENDING（保留全部历史
   字段与 correction_record）。
6. **裁决核验与补强签收 warn（SWR-V3.10.2-014/015）**：主代理采纳证伪者
   结论 demote 时须对证伪者承重前提主张逐条回源码核实并落盘
   `adjudication_verification`；证伪者/复活者补强（strengthened/
   attribution_correction）进报告/申报前须主代理逐条签收
   （`*_verified_by`）——两者均为 warn 级不阻断，旧队列复跑以
   `require_adjudication_verify=False` / `require_strengthen_verify=False` 豁免。
7. **NEEDS_REVIEW 成因三分（SWR-V3.10.2-013）**：`保守裁决 | 证据不足 |
   环境受限`（环境受限=无目标平台运行面）；环境受限 + 上游公开佐证 →
   附录 A 渲染「佐证注记」列（申报走佐证材料路径，终态不变）。
8. **渲染四标记（SWR-V3.10.2-002/010/011）**：实证行 fidelity 前缀、harness
   路径非 `.audit_results/` 前缀 → `[产物目录违规 warn]`、补强未签收 →
   `（未复核）` 标记。

### 机制新增（知识/契约层）

9. **平台信任模型清单（SWR-V3.10.2-016）**：checklist_library 新增
   `platform_trust_models` 清单族（按平台分派：mobile/desktop/web/
   embedded_kernel，平台机制级条目零项目 API 名）——「同主体」判定前必须
   对照平台清单（同设备其他应用经导出组件/意图参数注入是异主体；平台鉴权
   中介存在时「未认证通道」判据不成立）。R1 surface 信号驱动
   `detect_platforms` → verifier/refuter prompt 注入；零平台信号零注入。
10. **依赖 CVE 对账可选步（SWR-V3.10.2-017）**：R1 context 含 pinned 依赖
    清单时，verifier 步骤 1.5 可选对账关键依赖（解码器/解析器执行主体）的
    已知 CVE 状态 → `dependency_cve_notes` 注记（不改变 verdict，报告附录 B
    与申报语境引用）。
11. **物化增量面重审（SWR-V3.10.2-018）**：scope_changed 时输出受影响面
    重开建议（物化目录 × R1 面路径交叉）；主代理裁决后
    `write_scope_review` 落盘 `scope_review.jsonl`。
12. **实证防误伤样板（SWR-V3.10.2-019）**：parser_fuzz 模板与 c 手册 §8
    资源防护样板（ulimit/setrlimit 双形态）——GB/TB 级分配 harness 无防护
    环境复跑会 OOM-kill 整机。

### 维持撤销（义务棘轮防护）

- batch-size 默认截断提示、payload_hash 辅助命令：v3.10 撤销后本批次复评
  无失误案例再现——维持撤销。
- severity override 逐条复核义务：现有 override+reason 可问责，无失误案例
  ——不建。

### 验收判据（Phase 3.10.2）

全量回归全绿（273 基线 + test_v3102 15 新增）+ 去项目化扫描 0 命中（平台
清单族）+ 旧队列复跑零新增 blocking（新增 warn 以豁免参数关闭）+ 未审计过
的新项目验收随下一在线项目进行。
