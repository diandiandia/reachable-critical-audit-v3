# Reachable Critical Audit Skill v3（可达性严重漏洞审计）

## 🥇 第一原则：通用型 Skill（最高优先，一切修改的第一判据）

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
   "树外不可验证"类 drop 理由作废（mbedtls 审计实战形态），R3 入队前
   batch_verify 自动 diff 并输出 `scope_changed` 提示，受影响 drop
   （`scope_dependent: true`）按 R3.5-N 复活流程重开。
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
   `verify_queue.target_kind`。存在性规则按型装载（PREC-TARGET-KIND-001）：
   - **application**：默认可达三层检查含 shipped 配置实际值 + 运行时注册核实 + platform_precondition 显式标注
   - **library**：公共 API 即信任边界（Newtonsoft.Json 先例）；仓内调用者缺失不是阻断；死代码豁免不适用
   - **hybrid**：按组件分别装载；无法确定归属时按 application（保守）
   未签收 → 门禁⑧ target_kind_required 不放行（旧队列复跑以 `require_target_kind=False` 豁免）。
5. 初始化空 `verify_queue.json`：`{"schema_version":"3.0","candidates":[]}`。

## 🗺️ R1：输入面测绘（审计起点，禁止全库轰炸）

**目标**：产出 `input_surface.json`（surface 列表）。每个 surface = 一个外部数据入口，附 entry_points 源码证据。

1. **架构上下文**：`python3 surface_mapper.py context <project>` → 语言/构建文件/README 摘要。
2. **4 域并行测绘**（network/data/process/storage）：拉起 4 个子智能体，任务书模板 `task_templates/surface_map_domain.md`。
   > ⚠️ **任务书 schema 契约（W5 教训 ②）**：任务书必须内嵌下述 canonical schema，禁止让子智能体自定格式：
   > ```json
   > [{"id":"SURF-<域>-NNN","name":"...","type":"network|data|process|storage",
   >   "entry_points":[{"file":"<相对项目根路径>","line":N,"function":"...",
   >                     "evidence":{"snippet":"<该行代码, 可含上下文注释>"}}],
   >   "taint_channels":["..."],"trust_boundary":"unauthenticated_remote|trusted_channel|gated",
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

## 🎯 R2：面内签名匹配 → 假设 → LLM 筛选

1. **项目索引**：`python3 signature_matcher.py index <project>`（粗粒度调用索引，窗口展开用）。
2. **窗口匹配**：`python3 signature_matcher.py match .audit_results/input_surface.json <index.json>`。
   窗口有界（entry 行 ±60 邻域 + BFS 逐层 cap 40 + 总 cap 300）。命中产出 Hit。
3. **假设生成**：`python3 signature_matcher.py gen <hits.json>` → HYP-xxx（携带语义族/检查清单/sink 提示，**不是**最终候选）。
4. **LLM 筛选**（REQ-V3-037）：拉起 hypothesis-filter 子智能体（模板 `task_templates/hypothesis_filter.md`），按排除规则（常量参数/死代码/测试代码/语义不匹配/防御已到位）判定 keep/drop；**必须 Read/Grep 抽查 hit 真实代码，禁止只看 line_text**。筛选理由中的 focus sink（file:line）是后续簇化依据。

## 🔄 R3：候选验证（Mode W 默认）

**入队**：筛选 kept 的假设按 focus sink 簇化（同 sink 合并为一条簇级候选），写入 `verify_queue.json`：
```json
{"id":"CAND-001","source_file":"...","source_line":N,"sink_type":"CWE-xxx",
 "members":[{"id":"HYP-xxx"}],"status":"PENDING","priority":0}
```

**Mode W 波次**：
```bash
python3 tools/batch_verify.py <project> --stage workflow-script --mode verify
# → .audit_results/workflow_verify.js + payload（含逐候选任务书 prompt）
# 1) 用 Workflow 工具运行: scriptPath=<js> args={"candidates":<payload>}
# 2) 返回 verified 逐条 --stage collect 落盘（grade 自动重算: REACHABLE+边证据→edge_proven）
# 3) missing 中的 id 执行 --stage bump-attempt（attempt≥3 → ESCALATED 主代理裁决）
# 4) 循环直到队列无 PENDING
```
- workflow 内 agent 无文件系统：**不要把心跳契约写进 Mode W 任务书**（心跳是 Mode A' 机制）；结构化输出由 schema 强校验（自动重试）。
- `--stage collect` 落盘字段含 v3 必需项：`claim_type`、`edge_evidence`（实证门禁与分级依赖）。

**Mode A' 降级**（无 Workflow 工具时）：`--stage next` 出队 3~4 候选 → Agent 工具逐候选验证（任务书含心跳契约：先写 `.pending` 占位，完成后写 `_verify_<id>.json`，目标存在且非本人 pending → 追加 `.agent-<id>` 后缀）→ `--stage collect` → 循环。

## ⚖️ R3.5：独立复核（REACHABLE 且 grade≥edge_proven 强制）

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

任务书模板 `task_templates/biz_hypothesis.md`。锚点 = R1 测绘的相关 surface（file:line 可直接 grep）。
收集：`python3 tools/batch_verify.py <project> --stage r4-collect --file <合并 findings json>`；
断言：`--stage r4-assert`（H1-H7 全部 VERIFIED，exit 0）。

## 🧪 R5：实证抽验（声称类强制，REQ-V3-004/060）

**触发判定**：verdict=REACHABLE 且 `claim_type ∈ {crash,panic,oom,unbounded,xss,protocol_dos}` 且 `evidence_grade ≠ empirically_confirmed` → **强制实证，否则六门禁 ③ 不放行**（可选路径：主代理裁决降级 NEEDS_REVIEW，不实证不申报）。

1. harness 模板（`templates/harness/`）：ws_frame_alloc / ws_frame_accum / xss_path_sim；无匹配模板时现场构造（采样协议通用：RSS/存活/exit code + delivery-rate 确认）。
2. 实证程序落盘 `.audit_results/empirical/<name>/`（含 Cargo.toml/源码 + EMPIRICAL_REPORT.md：工具链版本/输入/输出/判定）。
3. 实测确认 → `empirical` 字段 + grade=empirically_confirmed；证伪 → correction_record 降级并回溯 verifier 错误（REQ-V3-051）。

## 🔒 六门禁（队列关闭判据，全部通过才允许出报告）

```bash
python3 -c "
import sys; sys.path.insert(0,'<skill_dir>'); sys.path.insert(0,'<skill_dir>/tools')
import evidence_ledger as el, batch_verify as bv, json
q=bv.load_queue('<project>')
surfaces=json.load(open('<project>/.audit_results/input_surface.json'))['surfaces']
tracked=...  # R2 假设覆盖 ∪ R4 假说追踪的 surface id
ok,v=el.assert_ledger(q, dispatched=[c['id'] for c in q['candidates']],
                      surface_data={'total':len(surfaces),'tracked':len(tracked)})
print(ok, v)"
```
① no_pending ② REACHABLE 无 static_only ③ 实证类声称 100% empirically_confirmed ④ H1-H7 全 VERIFIED
⑤ 对账零差异（dispatched 全部终态）⑥ escalated=0 或主代理签收 ⑦ surface 覆盖率 100%
（v3.2.2：tracked 计算 = R2/R4 直接覆盖 ∪ input_surface.json `mirror_pairs` 镜像自动传播
∪ 主代理签收的 `verify_queue.coverage_bridge`——relay 中继面[套接字层/示例程序中转]的正式通道，
每条 bridge 必附 basis 说明，REQ-V3.2.2-020/021）
⑧ target_kind_required（v3.2.1：R0 未签收 target_kind 不放行；旧队列复跑
`require_target_kind=False` 豁免）。另输出 `r4_feedback` 告警（warn 级不阻断 PASS）：
R4 H-7 默认值盘点与 R3 REACHABLE gate 证据的 key:value 冲突 → 主代理裁决纠正（W6 §25.6）。

## 📊 报告

落盘 `.audit_results/reachable_vulnerabilities_report.md`，必须含：
- 规模对照（候选/假设/surface 数、闭合率）
- **语言覆盖表**（v3.2.1 增加 `组件角色` 列：server-side/client-only/build-config；判据①：服务端组件语言 ≥1 surface 且非零候选；客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据）
- 每个 REACHABLE：verdict + 证据分级 + 调用链 + 独立复核结果 + 实证记录（如有）
- NEEDS_REVIEW 显式清单（含 correction_record 理由）
- R4 假说 verdict 表、六门禁断言结果、修复建议

## 📏 数据模型速查

- **verify_queue.json**：`{schema_version:"3.0", candidates:[{id,source_file,source_line,sink_type,members[],status:PENDING|VERIFIED|ESCALATED|NEEDS_REVIEW,verdict,reachability_type,call_chain[],call_chain_depth,edge_evidence[{edge,proof}],evidence_grade:static_only|edge_proven|empirically_confirmed,blocking_point,claim_type,attempt,correction_record[],empirical{}}], r4_findings:[{hypothesis_id,verdict,findings[],coverage_note}], escalated_signed_off}`
- **input_surface.json**：`{schema_version:"3.0", surfaces:[{id,name,type,entry_points[],taint_channels[],trust_boundary:{type},confidence,downstream_hints[]}], conflicts[]}`
- **hypotheses.json**：`{hypotheses:[{id,surface_id,signature_id,semantic_family,cwe[],hit_sites[],checklist[]}], logic_hypotheses:[]}`

## ⚠️ 编排层三条铁律（W5 回归教训，强制执行）

1. **写读竞态**：读子智能体产出前必须重试校验；通知到达 ≠ 文件已 flush。
2. **schema 契约**：任务书内嵌 canonical schema（见 R1），校验器归一化是兜底不是依赖。
3. **证据裁决**：证据不匹配时不静默放行也不盲目拒收——suggested_line/suggested_lines 交主代理裁决，证据重写必带 `*_by: main-agent` 标记。

## 📚 附录：资产地图

- 核心模块（skill 根）：`surface_mapper.py`（R1）/ `signature_lib.py`+`signature_matcher.py`（R0/R2）/ `evidence_ledger.py`（分级+六门禁+一致性断言）/ `harness_runner.py`（R5）/ `workflow_export.py`（Mode W）/ `checklist_binder.py`（清单绑定）/ `precedent_library.py`（先例裁决）/ `r2_guard.py`（假设 schema 守卫）
- `tools/batch_verify.py`：队列编排 CLI（collect/bump-attempt/workflow-script/r4-*/assert/status）
- `tools/r05_diff_archaeology.py`：R0.5 差异考古（REQ-V3-012~016，非默认路径）；`tools/ast_scanner.py`：L0 扫描器（REQ-V3-002 禁止其作为默认路径，按需使用）；`tools/gen_tracking.py`：需求追踪矩阵重建（文档工具）
- `resources/signature_library.json`：13 个签名（7 L3 语义族 + 6 L2 语言词族，含 known_instances，R0 冒烟强制可复现）；`resources/precedent_library.json`：19 条裁决先例；`resources/checklist_library.json`：19 条检查清单
- `task_templates/`：7 个任务书模板；`templates/harness/`：3 个实证模板；`harness_manuals/`：15 语言工具链手册
- `tests/`：73 个单测/集成测试（改模块后必须全绿）；`lessons/`：全部历史教训 + W5 回归发现
- v2.1 遗产：仅 `docs/legacy/SKILL_V2.1.md`（规范备份）

---

## 🆕 v3.1 增量（2026-08-17，15 语言战役 lessons W6 §1-24 的制度化）

> 设计文档: `docs/design/SYSTEM_DESIGN_V3_1.md`。v3.1 不改变阶段骨架，只把战役中主代理
> 手工补救的动作机械化。开发已完成（SWR-V3.1 43/43，73 测试全绿），Phase 3.1.3 验收通过后随 install 生效。

### R0 新增: maturity 判定
- `surface_mapper.py context` 输出 `project_kind ∈ {framework, library, infra, app}`
  （W6 §23.6/§24.6: 成熟框架 R4 产率三连超 R3）
- **mature framework → R4 与 R3 并行启动**，H1/H7 深度上调

### R1 新增: validate v3.1 + 预算档位
- `surface_mapper.py repair` 行号漂移自动修复器（首行键全文件匹配 ±80 语义 +
  `suggested_line` + `paraphrased` 标记；幂等: 已修复 entry 不重标，W6 §18.7/§22.1/§9.5）
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
  19 条 CK-*，15 语言证伪者攻击面固化）；未执行清单的 REACHABLE 会被 R3.5 同款证伪
- 自证伪提示: 候选附先例库匹配的最可能证伪论据，verifier 自查（目标: R3.5 拦截率
  从 ~50% 收敛到 <30%）
- 轻量实证白名单 + `empirical` 字段结构化 + 范围分级
  `mechanism|function_body|full_chain|e2e`（机制级只能支撑 edge_proven，W6 §17.7）

### R3.5 变更: 工具箱 + 裁决先例库
- 证伪者实证工具箱按声称类别注入（区间类=参照模型+百万对拍 §21.1 / 解析类=真实
  构件+畸形矩阵 §19.4 / 代理分歧类=标准部署实测 §16.10）
- `precedent_library.json`（19 条先例）裁决匹配 + `evidence_ledger.py consistency`
  同族一致性断言（W6 §18.3 从证伪者武器升级为系统断言）
- refutation 结果 schema 新增 strengthened/attribution_correction/note（W6 §13.6/§12.5）

### R5 变更: 语言手册 + 环境陷阱自检 + 对照矩阵
- `harness_manuals/<lang>.md` × 15（工具链探测/版本义务/陷阱清单/阳性模式/网络依赖）
- 环境陷阱自检（stale 进程清理 + diag 路由 / daemon 线程 / env 传播验证 / PATH 检查）
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
  N-API/JNI/embed，boundary surface 必填 boundary_kind + lang_pair）
- surface/entry_point/候选均带 lang 字段；任务书背景按语言分片
- `size_tier`: 2 语言项目 domains 含 boundary；3+ 语言保底 large 档（5 agents）

### R2/R3: 语言维度
- L2 词族按 surface.lang 过滤（C 词族不打 Rust surface）
- verifier 上下文语言按候选.lang 取；分级机械复核条款（collect 后强制
  grade_verdict 重算，差异写 grade_recomputed_by）
- CK-FFI-BOUNDARY（第 21 条清单）绑定 ffi/ctypes/extern 类候选

### R3.5-N（新）: UNREACHABLE 复活攻击
- 声称类 UNREACHABLE 全量 + 其他 20% 抽样（最少 2，上限 8）做 N=1 尽力复活复核
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

## 📝 R6：lessons 回写（审计闭合前置，v3.2 新增）

六门禁通过后、报告定稿前，强制生成代码审计问题文档：

```bash
python3 lessons_recorder.py <project> --write
# → lessons/SKILL_LESSONS_<project>.md（机械提取: 裁决纠正/降级/复活/分级重算/
#   paraphrased 标记/验收记录——全部来自 .audit_results/ 产物证据）
```

1. 主代理必须**人工补充过程观察段**（agent 行为/工具链陷阱/workflow 缺陷——
   非结构化数据无法机械提取），用 `write_lesson(project, process_notes=[...])`
2. 价值判定：高价值条目（新缺陷模式/语言盲区/裁决先例）当日并入
   W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；低价值条目留审计轨迹
3. 索引 lessons/README.md 自动更新；**未执行 R6 的审计不得闭合**（报告阶段门禁）
