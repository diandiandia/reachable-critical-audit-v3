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

**目标**：本 skill 是**通用型代码审计 skill**——对任意语言、任意项目形态（application/library/hybrid/infra）、任意平台的任意代码库均可审计。审计能力必须来自通用机制（阶段骨架 / 门禁 / 数据模型 / CWE 锚定的语义族 / 通用检查清单），而不是来自"我们审过哪个项目"。

**禁止项**（违反即视为缺陷，必须修复）：
1. 禁止为已审计的具体项目做专门优化：项目名、项目目录结构、项目专属 API 名不得进入运行时资产（签名 grep 列表、任务书例证、harness 模板、先例/清单正文）
2. 禁止让运行时机制依赖单一语言特征：语言相关内容必须按 `lang` 字段分派，或写入语言手册（assets/harness_manuals/）
3. 禁止用历史项目目录做运行时锚定：known_instances 等回归锚点只允许存在于测试 fixture（tests/），不得影响 R0 自检等运行时路径

**提炼经验的正确方式（两段式）**：具体审计发现 → **去项目化提炼**（抽象到 CWE 类 / 语言无关模式 / 通用检查步骤）→ 入库。项目名只允许出现在追溯字段（lessons / 来源列）。

**测试与回归的边界**：回归 fixture 可以来自具体项目（三锚点基线），但 fixture 只用于验证"通用机制未回退"，不得成为运行时行为依据。

> **审计架构**：LLM 子智能体是主分析引擎（测绘/回溯/判断）；规则库只是**提示器**（语义签名 grep hints + 检查清单），不再是判定器。审计起点是**输入面测绘**（R1），全库规则轰炸不再是默认路径。v2.1 遗产仅 `docs/legacy/SKILL_V2.1.md`（备份）；规则案例溯源见 `docs/history/FIRST_PRINCIPLES.md`。

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
   python3 <skill_dir>/src/surface_mapper.py scope snapshot <project>
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
   python3 <skill_dir>/src/signature_lib.py selfcheck <project>
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
③d **R4 confirmed 独立复核（v3.9, REQ-V3.9-010）**：confirmed 假说中
High/Medium/Critical 且 empirical_result 前缀 CONFIRMED 的 finding 须有
`independent_review {by, method, artifacts}` 或非空 r3_link（放行方向对抗复核）。
5. **target_profile 判定**（v3.17, SWR-V3.17-008）：
   ```bash
   python3 <skill_dir>/tools/target_profile.py <project> [--write]
   ```
   → 形态画像推荐 {surface_model, generation_layers, scale_class, containment_default, empirical_modes} + 逐信号证据。主代理复核签收（写入 signed_by/overrides）；**未签收 → 各消费者按全默认装载 = 现状行为**（零强制义务；与 target_kind 不同——profile 无门禁承载）。
6. 初始化空 `verify_queue.json`：`{"candidates":[]}`。

## 🗺️ R1：输入面测绘（审计起点，禁止全库轰炸）

**目标**：产出 `input_surface.json`（surface 列表）。每个 surface = 一个外部数据入口，附 entry_points 源码证据。

1. **架构上下文**：`python3 surface_mapper.py context <project>` → 语言/构建文件/README 摘要。
   **测绘规模档位网格（size_tier）**：<100 文件 2 agents；100-500 档 4 agents
   无限时；>500 档 4 agents + 45min 硬时限 + 10min 中间产物落盘；super-large
   两阶段见下。
   context 输出另含 `project_kind ∈ {framework, library, infra, app}`（机械）与
   `maturity ∈ {developing, mature}`（git 版本标签语义: ≥1.0 稳定标签=mature）——
   project_kind 是测绘期上下文提示, maturity 是 R4 并行触发条件之一,
   主代理复核后可手动覆盖 maturity（四轴职责表, v3.31 SWR-V3.31-006）。
2. **4 域并行测绘**（network/data/process/storage）：拉起 4 个子智能体，任务书模板 `assets/task_templates/surface_map_domain.md`。
   **boundary 第五域（v3.2, 多语言目标）**：语言清单 ≥2 时加派 boundary 域测绘
   （跨语言桥接/FFI/编解码通道面, 面 type=`boundary`）——size_tier 的
   domains_split 已含该域, 正文 schema 的 type 枚举同步含 boundary。
   boundary 面必填附加字段：`boundary_kind`（FFI 方向/桥接形态）与
   `lang_pair`（双方语言对）。
   > **派发能力指引（v3.14, SWR-V3.14-007）**：优先派发具备写盘能力的子智能体
   > （允许写 `.audit_results/_r1_<域>.json`）；只读代理（如 Explore）会按落盘
   > 拦截契约以 UNWRITTEN 形态返回完整 JSON，由主代理恢复（写 recovered_by）——
   > 可用但产生主代理转写负担（protobuf 审计 4/5 域 UNWRITTEN 实录）。完成通知
   > 后先 `json.load` 校验文件已落盘（铁律 1）再采信。
   > ⚠️ **任务书 schema 契约（W5 教训 ②）**：任务书必须内嵌下述 canonical schema，禁止让子智能体自定格式：
   > ```json
   > [{"id":"SURF-<域>-NNN","name":"...","type":"network|data|process|storage|boundary",
   >   "lang":"<面代码语言: c/cpp/go/rust/java/python/... 必填, 从架构上下文继承>",
   >   "entry_points":[{"file":"<相对项目根路径>","line":N,"function":"...",
   >                     "evidence":{"snippet":"<该行代码, 可含上下文注释>"}}],
   >   "taint_channels":["..."],"trust_boundary":"unauthenticated_remote|trusted_channel|gated|host_api|local|environment|unknown",
   >   "confidence":"high|medium|low","downstream_hints":["..."]}]
   > ```
   > 子智能体落盘到 `.audit_results/_r1_<域>.json`，最终回复同 JSON。
> **super-large 两阶段测绘（v3.17, SWR-V3.17-002）**：size_tier 返回 super-large
> （>2000 源文件）时，先落盘组件清单（tier 输出 components）→ 按（组件 × 域）
> 派发，任务书注入「组件约束段」（{component_scope}），面 id 带组件缩写前缀，
> 45min 硬时限按组件给——禁止对超大仓做全仓单域单 agent 测绘（引擎/内核量级
> 失控实录, W6 §17.1）。
> **语义轴测绘（v3.17, SWR-V3.17-005）**：target_profile 签收
> surface_model=semantic/hybrid 时额外派发语义轴测绘子智能体（任务书
> 「语义轴测绘段」）——轴 = 目标语言语义命名空间族（builtins 族/字节码族/
> 语法产生式族），面附 semantic_axis 字段；R2 假设生成沿轴采样（一轴一族
> 假设义务）；门禁⑦ tracked 计算轴即面（机械并入，无需手工 bridge）。

3. **收集与校验**：`python3 surface_mapper.py validate .audit_results/_r1_<域>.json --root <project>`。
   校验器已内置归一化（裸数组/字符串 trust_boundary/HTML 实体/相对路径/空白折叠均容忍）与行号漂移裁决：
   - `[suggested_line=N]`（唯一命中）→ 主代理应用修正并写 `line_corrections`；
   - `[suggested_lines=a,b,c]`（多命中）→ 主代理按定义形态启发式裁决；
   - 内容完全不匹配 → 主代理重写 snippet 为源行实际内容并标 `evidence_rewritten_by`。
   > **漂移裁决依据条款（v3.33, SWR-V3.33-010，提示级）**：裁决依据固定为
   > snippet 首行实际锚点（定义形态）——`suggested_line` 的语义是"距声称行最近
   > 的全文命中"，多语句 snippet 会错锚（命中 snippet 中段/函数内他处同名调用），
   > 13 处漂移中 3 处需定义形态裁决的实战形态（servo 复盘 N-2）。
   > ⚠️ **铁律 1（W5 教训 ①）**：agent 完成通知与文件落盘之间存在写读竞态。读任何子智能体产出文件前必须 `json.load` 重试（失败等 1-2s 重试至多 3 次）；重试后仍损坏才按"产出损坏"处理（重派或主代理修复），禁止把竞态误判为 agent 幻觉。
4. **合并**：`python3 surface_mapper.py merge .audit_results/_r1_*.json --root <project>` → `input_surface.json`（含 conflicts 标注）。主代理复核后写 `reviewed_by`。
   > **同 id 碰撞与域覆盖对账（v3.33, SWR-V3.33-001/002，提示级）**：merge 对
   > 跨文件同 id 碰撞落 conflicts（resolution=`kept-first-same-id`，静默覆盖曾致
   > 18 面丢失——碰撞时按组件前缀纪律改名后重 merge），并对未测绘且无空域签收的
   > 域输出 `domain_unmapped` warn（process/storage 零派发形态，主代理裁决重派或
   > 补签收 reviewed_by+empty_domain_reason）。收口必做机械对账：
   > Σ域文件面数 == merged 面数。

## 🎯 R2：假设生成（LLM 主路径）→ LLM 筛选

**假设生成主路径**：LLM 直接基于 surface 图生成假设（主代理或限时 agent）。
**复审计场景（W6 §22.2）**：R2 上下文自动注入旧审计终稿摘要（同目标复审计时）。
**shipped-config 盘点（v3.2.1, REQ-V3.2.1-030/031）**：含 config 目录的组件跑
`export_script_shipped_config` → 提交值 vs 代码零值对照 → 落盘
`.audit_results/shipped_config.json`——R2『默认可达』类声称必须引用 shipped
实际值而非代码零值（W6 §25.4 第三层检查）。
**面覆盖前置核对（v3.22, SWR-V3.22-010）**：假设生成完成后机械核对
`hypotheses[].surface_ids` 集合 ⊇ input_surface 全集——缺面即补生成假设
（门禁⑦ 前置化；111/111 零缺口闭合轮 vs 缺口闭合三连重派的对照实录）。
**语言问题矩阵提示（v3.18, SWR-V3.18-002 + v3.31/32）**：生成假设前执行
```bash
python3 <skill_dir>/src/language_issue_matrix.py hints <surface.lang> [--kind <target_kind>]
   配套命令: `cells <lang>`（已种格提示）与 `inventory <lang>`（排序问题条目,
   含 external_seeded 档）——external_seeded 条目只作假设空间提示, 裁决必须以
   源码证据为准（SWR-V3.29-005 语义）。
```
**对抗枚举条款（v3.32, SWR-V3.32-001, 提示级）**：hints 装载后，对该语言
inventory 的各族 Top 条目逐一做缺陷形态展开——"该缺陷形态在本目标中可能
藏在哪些 sink 形态"（对抗枚举 = 以缺陷形态为输入维度的假设生成；库型/
引擎目标该步为强制建议——R4 族深挖 7/9 与 R2 面图 0/9 的对照实录）。
**修复驱动假设条款（v3.32, SWR-V3.32-002, 提示级）**：目标为 git 仓库且有
近期安全修复史时，执行 `python3 <skill_dir>/tools/fixminer.py <project>
[--since N]`——按族分类的修复 commit 是该代码库缺陷形态的 ground truth，
每族生成"同款缺陷在树内其他位置可能残留"的假设（修复变体复核先例，
SKILL_LESSONS_C §1.4.5）；fixminer 只挖不判，假设由主代理生成。
——返回该语言已种格的族条目（典型漏洞形态/关键 sink/判定要点），作为
假设空间提示（提示级，无强制义务；未种格 pending 零注入零提示）。
矩阵回填纪律（SWR-V3.18-003）：每版本验收审计收官时把验收项目覆盖的
语言×族格两段式回填进矩阵（去项目化提炼 + source_lessons 含日期）——
账本记覆盖计数，矩阵供知识，两者互补。签名匹配是**可选佐证器**（SWR-V3.3.2-053）：
- 库型/非服务端框架目标签名命中率趋近 0（七项目批次 7/7 项目 0 命中实测），**R2 不强制跑 index/match 链路**；
- 如需佐证（服务端框架目标、或主代理判断签名面相关），按序运行：
  1. `python3 signature_matcher.py index <project>`（粗粒度调用索引，窗口展开用）
  2. `python3 signature_matcher.py match .audit_results/input_surface.json <index.json>`（窗口有界：entry 行 ±60 邻域 + BFS 逐层 cap 40 + 总 cap 300）
  3. `python3 signature_matcher.py gen <hits.json>` → 佐证 hints（**不是**最终候选）
- R0 `signature_lib.py selfcheck` 不受影响（回归锚点 + 去项目化扫描是第一原则守卫，仍强制）。

**同族不一致防御枚举（v3.38, SWR-V3.38-001, 提示级）**：hints 装载后，对目标中同族多实例功能面（同路由表其余端点/同模块接口其余实现/同解析族其余路径）做防御维度对比矩阵（体量封顶/鉴权门/超时/输入校验）——任一兄弟有防御而本面没有即假设（修复残留形态，差分证据强于绝对声称）。

**公开面关联检索（v3.38, SWR-V3.38-003, 提示级）**：网络可用时，假设生成前对目标做公开面关联（已知 CVE/GHSA 检索 + 上游 master 对账，落盘 `.audit_results/upstream_recon.json` 可无）——已修形态直接降级或改口径，未修形态附佐证；**上游后修 = 快照缺陷候选**（时间差假设，直接进假设空间）；网络不可用零阻塞跳过。upstream「已修复/已包含」结论必须附树内 commit 佐证（git log -S / merge-base --is-ancestor），无法佐证时按未修复处理——版本号声称与树内事实不符是时间差发现的直接来源（SWR-V3.42-004）。

**differential 发现通道（v3.23, SWR-V3.23-004，提示级）**：surface_model=semantic/hybrid
且 generation_layers 含 jit 的目标，R2 可（可选）对语义轴关键操作跑 `differential`
探针（`assets/templates/harness/differential_probe.py`：解释器 vs JIT / 多 JIT 层 / 元素类型
变体等运行配置比对）——比对分歧即假设（类型混淆/去优化错误类缺陷的发现通道，
静态假设生成对该层天然弱覆盖）。实证模板复用，无新义务、无新门禁。

**LLM 筛选**（REQ-V3-037）：拉起 hypothesis-filter 子智能体（模板 `assets/task_templates/hypothesis_filter.md`），按排除规则（常量参数/死代码/测试代码/语义不匹配/防御已到位）判定 keep/drop；**必须 Read/Grep 抽查 hit 真实代码，禁止只看 line_text**。其中『防御已到位』类裁决必须核查默认权限上下文（文件/目录/umask/监听 socket 权限、环境变量默认值、启动命令注入点）并引用源码证据行（v3.6 实录：默认 token 随机 + state 0644/socket 0777 使防御失效，R4 实证推翻 R2 误 drop）。筛选理由中的 focus sink（file:line）是后续簇化依据。

> **keep=0 抽样复核条款（v3.4.6, SWR-V3.4.6-004）**：筛选结果 keep=0（或
> boundary_confirmations ≥ 全量 80%）时, 主代理**必须**抽样复核 ≥3 条
> boundary_confirmations 的真实代码防御点（逐条 Read 防御点源码确认成立;
> 抽样清单落盘 `r2_filter_result.spot_checked`）。筛选全防御裁决若失真
> （防御性偏差的另一方向: 过度放行）, R3 空队会整体放过缺陷——抽样复核是
> "证据裁决"铁律在空队形态下的必要延伸; R4 深度验证与 R2 交叉核对构成
> 双保险（成熟网络库 28 条全防御、主代理抽样 HYP-L1/L12/L27 复核属实实录）。
> 落盘保真: 筛选结果落盘为 `r2_filter_result.json` 后跑
> `python3 <skill_dir>/src/r2_guard.py fidelity .audit_results/r2_filter_result.json`
> （SWR-V3.4.6-002: bc/drop 缺 surface_ids 自动从 hypotheses.json 反查补齐）。

## 🔄 R3：候选验证（Mode W 默认）

**taskFile 薄封装默认派发（v3.22, SWR-V3.22-009）**：Mode W 各波 payload 默认
taskFile 薄封装（任务书落盘 _tasks/, payload 只带 id+taskFile 引用）——
大任务书不进入 Workflow args, 波次 args 体积与截断面同时下降; 内嵌回退形态
保留兼容。
**verifier 任务书固定步骤（v3.2.1, REQ-V3.2.1-010~012）**：步骤 0.5 模块可
导入性预检（顶层包解析 + DI 吞错路径审查, broken_edge → NEEDS_REVIEW）；
步骤 5.5 消费端中间层枚举。
**upstream 检索申报口径（v3.10, SWR-V3.10-011）**：命中公开补丁/已有 CVE →
标注发现链, 不得以首发口径申报。

**批次选题规则（v3.4, REQ-V3.4-006）**：多项目批次开题时，先跑
`batch_verify.py <任一项目> --stage coverage-ledger` 读覆盖账本缺口格
（CWE 族 × 语言，`assets/resources/issue_coverage_matrix.json`），**优先选未覆盖
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

**补强签收层级指引（v3.14 SWR-V3.14-008 文案补全）**：证伪者/复活者补强**R3.5-N 复活攻击抽样（REQ-V3.2-021）**：声称类 UNREACHABLE 全量 + 其他类
20% 抽样（最少 2, 上限 8）做 N=1 复活复核；抽样决策落盘
`.audit_results/_resurrect_sample.json`；revived → 回 R3 重验。
**sibling 回显（v3.32, SWR-V3.32-003）**：r35-collect 输出 strengthened_notes
+ sibling_advisory——补强中含机制静态确证的 sibling 向量时主代理裁决立候选
（SWR-V3.19-003 实质机制优先；不自动立候选）。

（strengthened/attribution_correction）进报告/申报前须主代理逐条签收——
签收字段为候选级 `refutation` dict 内的 `strengthened_verified_by` /
`attribution_correction_verified_by`（与 `strengthened[]` 平级，**非 entry
内部**）；demote 裁决须落 `adjudication_verification`（回源码核实证伪者承重
前提主张）。均为 warn 级不阻断。

**Mode A' 降级**（无 Workflow 工具时）：`--stage next` 出队 3~4 候选 → Agent 工具逐候选验证（任务书含心跳契约：先写 `.pending` 占位，完成后写 `_verify_<id>.json`，目标存在且非本人 pending → 追加 `.agent-<id>` 后缀）→ `--stage collect` → 循环。

## ⚖️ R3.5：独立复核（REACHABLE 且 grade≥edge_proven 强制）

**correction_record 双形态注记（v3.19, SWR-V3.19-004 系）**：correction_record
条目允许 dict（demote 裁决形态）与 str（主代理自然写法）双形态——消费端
（assert_ledger/lessons_recorder）对 str 条目跳过不改写，dict 条目读
demote_to/adjudication_verification 字段。

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

**R4 触发轴（REQ-V3.3-007 + v3.31 SWR-V3.31-004）**：`maturity==mature` **或
`target_kind ∈ {library, hybrid}`** → R4 与 R3 并行启动，H1/H7 深度上调；
project_kind==framework 不再单独触发；maturity 由 git 版本标签语义判定
（≥1.0 稳定标签=mature），主代理复核后可手动覆盖。

| 假说 | 检测要点 |
|---|---|
| H1 | 远端控制分配大小无上限（CWE-789：缓存/累积/预留 × sizeof） |
| H2 | 远端控制解引用长度/索引（CWE-125/787：截断 cast/下标/切片） |
| H3 | 异步对象生命周期竞态（CWE-416：回调持引用/池复用状态残留） |
| H4 | 跨进程信任边界破坏（CWE-20+89/78：输入拼进 exec/路径/转发头；初始化时序注入面 v3.11——启动窄窗/冷启动注入/初始化时序竞态） |（含 site-isolation/资源归因子条 v3.24：跨进程资源（纹理/缓存/下载/导航目标/worker 等）绑定到错误 origin 即信任边界破坏——检查资源创建与归因的 origin 上下文一致性）
| H5 | 暴露组件鉴权缺失（CWE-862/926：调试端点/状态页/目录列表） |
| H6 | 多租户 owner 比对缺失（CWE-639/285：锁/会话/缓存归属） |
| H7 | **信任边界专项（v3 新增）**：① 同 UID/IPC 高危操作 ② 路径语义（.. 上溯/symlink/空路径回退）越界 ③ 鉴权谓词弱化（前缀/子串/hash 替代全名） |

任务书模板 `assets/task_templates/biz_hypothesis.md`（v3.4.3 起注入实际 surface id 清单
`{surface_id_list}` + canonical 输出示例；H7 默认值全表预算 ≤1200 字）。
锚点 = R1 测绘的相关 surface（file:line 可直接 grep）。
收集：`python3 tools/batch_verify.py <project> --stage r4-collect --file <合并 findings json>`；
断言：`--stage r4-assert`（H1-H7 全部 VERIFIED，exit 0）。
**同事实去重（v3.4.3, SWR-V3.4.3-060）**：r4-collect 后主代理按 title 跨假说
同事实去重——主申报方承载 severity，其余条目 `r3_link` 标「同事实共享实证」
（java-jwt H2/H7 双 agent 各自发现同一 DateTimeException 逃逸的实战形态）。
**reviewed_clean 归位裁决（v3.33, SWR-V3.33-005，提示级）**：r4-collect 对**R4 empirical_result 前缀契约（v3.4.4, SWR-V3.4.4-009）**：CONFIRMED: /
REFUTED: / SOURCE_FACT: 三前缀——gate ③b 结构判定识别。
**假说级 tracked_surfaces（v3.10, SWR-V3.10-002/003）**：reviewed_clean/
not_applicable 假说的审查触及面结构化落盘 hypothesis_tracked_surfaces
（r4-collect 幂等合并）, 防覆盖率脱节。

reviewed_clean 假说下 severity≥Medium 的 findings 输出 warn（`reviewed_clean_
medium_plus`）——实质发现被 verdict 语义留在 B.4 计数而不进问题清单的形态
（servo 复盘：特权页点击劫持 Medium / promise 滞留 Medium）。主代理裁决归位三选一：
升 confirmed 承载 / 主代理段补报 / 明确留档；不自动改写 verdict。
**报告去重承载终态（v3.33, SWR-V3.33-006）**：报告同事实去重仅在 r3_link 承载
候选 verdict=REACHABLE 时成立——承载候选降 NEEDS_REVIEW/UNREACHABLE 时 finding
自列承载 severity（去重曾致 High finding 整体消失的形态，servo 复盘）。

## 🧪 R5：实证抽验（声称类强制，REQ-V3-004/060）

**探针→可行性路由前移（v3.21, SWR-V3.21-001）**：R0 探针落盘后、R3 派发前输出**部署布局义务（v3.4.4, SWR-V3.4.4-008）**：实证必须在部署布局执行（vm
全量加载 src 不构成部署布局实证；模块不在任何发布产物 → 不构成可达声称）。

empirical_feasibility 表（三轨 = real-target / equivalent-harness / static-only）；
R5 harness 目标清单在 R3 定；探针含 no-*
运行面缺失时向用户报预期 NEEDS_REVIEW 占比 + 三选一决策点（补装运行库 / 借运行面 /
接受上限）——决策权在用户，主代理不得代选。该表为笔记级产物（不落 schema、
不进队列）；落盘形态须含 `decision {by, date, choice}`——用户三选一决策必须
签入工件（主代理不得代选），未签入即审计问责链不完整（v3.22, SWR-V3.22-007）。
static-only 轨候选的证伪票价值=机制静态确证（非浪费），派发时明示。

**触发判定**：verdict=REACHABLE 且 `claim_type ∈ {crash,panic,oom,unbounded,xss,protocol_dos,rce,leak}` 且 `evidence_grade ≠ empirically_confirmed` → **强制实证，否则六门禁 ③ 不放行**（可选路径：主代理裁决降级 NEEDS_REVIEW，不实证不申报——v3.3 起此为明示条款：NEEDS_REVIEW 是合法终态而非降级耻辱，成因须注明「保守裁决」或「证据不足」）。源事实级降级规则（哨兵值/算术类，网络阻断记录 blocker，W6 §21.4）继续有效。
**audit_constraint 批量裁决（v3.16, SWR-V3.16-001）**：候选携带 audit_constraint
（no-build/no-device/tree-incomplete）且未实证时, gate ③ 附 warn 级 batch_demote
建议——主代理逐条确认落盘, 不自动改写。

**实质机制优先实证提示（v3.19, SWR-V3.19-003）**：claim=other 但机制静态确证
（0 票证伪+补强）的候选优先纳入复活波实证池（V8 CAND-013/049 升格实录）。
**实证回填规范（v3.4.3, SWR-V3.4.3-061；v3.10, SWR-V3.10-005 键名规范化）**：主代理回填
`empirical` 结构化 dict 只允许发生在 verifier/证伪者证据文本含真实实测的场景——必须带
`backfilled_by` 标记 + 实测数字依据（成本曲线/RSS/exit code/请求计数）；禁止无依据回填。
回填前缀语义（SWR-V3.42-006）：CONFIRMED 前缀触发 ③d independent_review 要求（无 independent_review/r3_link 即违规）；机制级静态确证写 SOURCE_FACT 前缀（has_confirmed 判定包含 source_fact 关键词）。回填前预判 gate 链级联。
**canonical 键集**：保留键 `outcome`/`evidence_numbers`/`report`（报告渲染既有消费键）+
  `status:"confirmed"`（v3.20, SWR-V3.20-006: 机械判级条件键——缺 status 的
  canonical 回填会被 grade_verdict 按保留键推断 empirically_confirmed 并附
  回填提示，但回填时直接写 status 才是正解；status/scope 缺省且三保留键
  不全的 dict 不判 empirically_confirmed）+
标准键 `harness`/`method`/`input`/`result`/`verdict`/`backfilled_by`（自建 harness 回填用）；
渲染器容错读双形态（保留键优先，缺失回退标准键）。

**fidelity 保真度判定（v3.10.2, SWR-V3.10.2-001~004；v3.23, SWR-V3.23-001
所有权模型核实）**：`empirical.fidelity` 枚举 `real_target | equivalent |
mechanism`（缺省 real_target，旧队列零行为变化）。`equivalent` 档必须做**所有权
模型核实**——harness 须列出目标对象在真实代码中的引用持有图（谁 AddRef/谁释放/
释放时机）并证明 harness 的破坏/交错时序映射到该持有图的真实释放路径；无法映射
的时序不得作为缺陷前提（实录：家族强引用层使「后台期间释放」不可达，harness
人为交错致误报——门禁与复核均无法拦截该形态，核实义务落在 harness 编写侧）。
`mechanism` 档不得升 `empirically_confirmed`；申报材料按档位标注，不混级申报。
equivalent 档结论强度低于 real_target——真实目标环境可及时，对 equivalent 实证候选做抽验（建模失真曾致等价实证结论被真实目标推翻的实录）；提示级，不强制不阻断。
补测前先核取 verifier/证伪者证据中已有实测数字——backfill 规范（v3.4.3-061）以证据文本实测为依据，同事实重复实证是执行层浪费（提示级）。

1. harness 模板（`assets/templates/harness/`）：ws_frame_alloc / ws_frame_accum / xss_path_sim / parser_fuzz（C/C++ 解析器 crash 声称类）/ resource_rate_probe（v3.6 通用协议级速率灌注探针，langs:["any"]，protocol_dos/unbounded/oom 声称）/ differential（v3.17 通用差分执行探针——共享语料 × N 组运行配置比对分歧, langs:["any"]，配置轴类声称首选）/ paired_control_probe（v3.30 通用双测对照探针——对照 vs 攻击命令 VmHWM 峰值差分, langs:["any"]，资源类声称配对测量）；无匹配模板时现场构造（采样协议通用：RSS/存活/exit code + delivery-rate 确认）。
   **harness 回收条款（v3.38, SWR-V3.38-005, 提示级）**：收官复盘对现场构造的实证程序做通用化评审——形态跨项目可复用则去项目化入库`assets/templates/harness/`（paired_control_probe 入库先例）。
2. 实证程序落盘 `.audit_results/empirical/<name>/`（含 Cargo.toml/源码 + EMPIRICAL_REPORT.md：工具链版本/输入/输出/判定）。
   **harness 依赖条款（v3.33, SWR-V3.33-011，提示级）**：(a) 独立 harness crate
   的依赖解析不与目标仓 workspace Cargo.lock 共享——版本敏感依赖必须对照目标仓
   Cargo.lock 钉死（`=x.y.z`，版本漂移曾致 E0004 非穷尽 match）；(b) lib 名≠包名
   （`[lib] name` 段）是常见形态，import 按 lib 名；(c) `--offline` 可行性探测须含
   git 依赖面（workspace 根清单的 git 源会阻断离线解析）。
3. 实测确认 → `empirical` 字段 + grade=empirically_confirmed；证伪 → correction_record 降级并回溯 verifier 错误（REQ-V3-051）。
   **实证降级簿记（v3.19, SWR-V3.19-004）**：主代理把候选实证降级为
   UNREACHABLE 时，必须同步写候选级 `resurrection_review {revived:false,
   outcome:"实证证伪原因"}`（gate ③c 簿记契约——机制 v3.2.2 已存在，本条明示
   裁决动作与簿记字段的对应关系，V8 审计门禁 FAIL→补记→PASS 实录）。

## 📝 R6：lessons 回写（审计闭合前置，v3.2 新增）

**R6 命中率条款（v3.29, SWR-V3.29-005，提示级）**：收官时执行
`python3 <skill_dir>/src/language_issue_matrix.py hitrate <lang> <本次确认问题
cwe 列表>` 并把命中率记入 lessons 过程观察段（传导度量）。

六门禁通过后、报告定稿前，强制生成代码审计问题文档：

**R1 谓词矛盾扫描（v3.21, SWR-V3.21-002，报告定稿前义务）**：对每个
REACHABLE finding，检查其是否否定任一 R1 surface 条目的阻断谓词（拒绝/
拦截/白名单/过滤/仅允许/不允许类结论）。命中即生成 contradiction record
（surface id + 被否定谓词 + finding 证据引用），并按缺口闭合流程反向测绘
该面。机械辅助清单（固定 grep 形态）：谓词关键词
`拒绝|拦截|白名单|过滤|仅允许|不允许|禁止` × 每个 REACHABLE finding 的
sink 文件与调用链文件，逐对复核——语义判定由主代理裁决，不做自动改写。

```bash
python3 <skill_dir>/src/lessons_recorder.py <project> --write
# 机械提取: 裁决纠正/降级/复活/分级重算/paraphrased 标记/验收记录——
# 全部来自 .audit_results/ 产物证据
```

**lessons 统一落盘位置（v3.16.1，用户裁定）**：`<project>/.audit_results/lessons.md`
（项目本地）——审计收官时主代理在此写「对 skill 的教训」+「审计自身教训」两段；
**skill-optimizer 从各项目 `.audit_results/lessons.md` 读取**（唯一读入口）。
仓库 `assets/lessons/` 目录为战役期历史档案（不再写入）；`lessons_recorder.py` 的
仓库 lessons 写入路径为遗留机制，保留兼容但不再作为惯例。

1. 主代理必须**人工补充过程观察段**（agent 行为/工具链陷阱/workflow 缺陷——
   非结构化数据无法机械提取），用 `write_lesson(project, process_notes=[...])`。
   幂等语义：write_lesson 全量重渲染（机械提取段 + 过程观察段），
   与 `--write` 调用顺序无关、重复调用不丢内容
2. 价值判定：高价值条目（新缺陷模式/语言盲区/裁决先例）经去项目化提炼后
   入库清单/先例（两段式：具体发现 → 去项目化 → 入库，来源留追溯字段）；
   低价值条目留项目 lessons 轨迹
3. **未执行 R6 的审计不得闭合**（主代理义务, 提示级——无机械门禁承载;
   审计契约以 lessons.md 落盘为准, 六门禁判据不包含本项）
5. **蒸馏失败模式清单（v3.22, SWR-V3.22-011）**：收官蒸馏必须逐项过
   已知失败模式 checklist——截断自愈 / 契约漂移 / 簿记缺位 / 签收错名 /
   落盘契约 / 决策记录 / 严重度映射 / 派发简写与模板不一致——任一模式
   在本审计发生即必须蒸馏（报漏补记周期实录：跨机制契约类漏项每轮重现）
4. **蒸馏与收官同周期绑定（v3.21, SWR-V3.21-003）**：价值判定必须在报告
   闭合前完成——高价值条目去项目化后并入 lessons.md「对 skill 的教训」节
   （skill-optimizer 唯一读入口），低价值条目留项目 lessons 轨迹；
   SKILL_LESSONS_*.md 只作机械证据、不承载待办，禁止留下悬空"待回填"

> **覆盖账本回填时序（v3.6 强制）**：`--stage coverage-ledger --write` 带两道机械前置——
> r4-assert（H1-H7 全 VERIFIED）与 r4_feedback 无未决冲突，不满足输出
> `LEDGER_WRITE_BLOCKED_*` 且不烧 sources key。正确时序：全部 cwe 修正
> （含 r4_feedback 裁决与 `r4_feedback_resolved` 落盘）→ r4-assert PASS →
> 六门禁全 PASS → `--write`。`LEDGER_IDEMPOTENT_SKIP` 会附打印本队将产生的
> new_counts；先回填后补标 cwe 的缺口格不回写（puma 审计 INJECTION×ruby 实录）。

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
                                    'mirror_pairs':surfaces.get('mirror_pairs') or []},
                      r2_filter=_r2_filter_or_none())
# _r2_filter_or_none(): r2_filter_result.json 存在时读
# {'keep':len(keep),'bc':len(boundary_confirmations),'total':keep+drop+bc,
#  'spot_checked':spot_checked}——门禁①b (v3.31) 消费; 文件缺失返回 None (skip)
print(ok, v)"
```
① no_pending ② REACHABLE 无 static_only ③ 实证类声称 100% empirically_confirmed ④ H1-H7 全 VERIFIED（③b: R4 finding 实证判定的结构规则——empirical_result 非空 + 数字特征主判,『实测』类关键词仅 fallback）
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
  每行 `ID | 问题摘要(claim_type+evidence 首 120 字) | 位置 file:line | CWE |（行尾附 attacker_tier 标注, v3.11）
  证据等级 | 复核(证伪者结果/R4 确认（无 R3.5 复核）)`
- **二、问题详情**：确认问题全集每条一节——R3 条目：位置/语言、CWE/claim_type、
  verdict+证据分级（grade_recomputed_by 如有）、调用链逐跳+depth+
  reachability_type、证据、blocking_point 前提逐条（PREC-CONDITIONAL-REACHABLE-001）、
  独立复核 refutation{}、实证记录 empirical{}、修复建议（R4 finding fix 命中，
  否则「（主代理补充）」）；R4 条目：来源（R4 假说确认，无 R3.5 独立复核）、
  CWE/claim_type、要点、证据、实证结果 empirical_result、追踪 surface、修复建议
- **三、修复建议与结论（主代理补充）**：仅此段 + 头部审计基线由主代理补写；
  **补充后不得重跑 `--stage report`**（机械渲染会覆盖本段）。
  **发现包络边界声明（v3.23, SWR-V3.23-002，提示级）**：该段须附「发现包络
  边界声明」——本审计覆盖输入处理缺陷（输入面→语义轴→sink）；**不覆盖**
  （a）JIT/编译器优化正确性层（类型追踪/去优化正确性——需差分/模糊测试通道），
  （b）闭源依赖内部实现，（c）非目标平台变体，（d）UI 信任指示层（地址栏/界面欺骗类——UI 信任逻辑非代码缺陷），（e）移动端平台集成层，
  （f）构建期生成代码（v3.33, SWR-V3.33-009：codegen/DSL 编译产物、宏展开产物等磁盘无源物——审计生成器源码与调用契约，生成物按依赖边界处理；构建环境可行时应物化（build 后读 OUT_DIR/生成目录）纳入面图。缺失 = warn 注记不阻断。
- **附录 A：NEEDS_REVIEW 清单与同事实映射**（REQ-V3.1-092）：**重开通道（v3.10.2, SWR-V3.10.2-017）**：`--stage reopen --id <id>` +
`REOPEN_REASON` 环境变量——环境 blocker 解除后回 PENDING 重验（历史保留）。
成因双分
  （**三分（v3.10.2, SWR-V3.10.2-013）**：`保守裁决`（防御证据充分但门禁压力下保守）/ `证据不足`（前提/调用边无法取证）/ `环境受限`（无目标平台运行面；环境受限+上游公开佐证 → 附录 A 佐证注记列）；未注明交主代理确认）+ correction_record 理由 + NEEDS_REVIEW ↔
  R4 hypothesis/finding 映射行
- **附录 B：审计过程信息**：B.1 规模对照（候选/假设/surface 数、闭合率）→
  B.2 语言覆盖表（v3.2.1 `组件角色` 列：server-side/client-only/build-config，
  `language_inventory` 现场重算；判据①：服务端组件语言 ≥1 surface 且非零候选；
  客户端组件语言以 ≥1 边界面 + cross_evidence 为等价判据）→ B.3 FFI 边界表 →
  B.4 R4 假说 verdict 表 → B.5 六门禁断言（机械调用 assert_ledger 渲染
  ①-⑧+③c，未过 → FAIL 行）→ B.6 覆盖账本（coverage_ledger 字段机械渲染，
  REQ-V3.4-007——本批新增覆盖格与仍存缺口格，为下批选题依据）

严重程度机械映射（cwe 列表 + sink_type 全量 `CWE-(\d+)` 提取取 max；
`severity_override` 合法值 {critical,high,medium} + reason 优先，非法值回退；**字段形态（v3.39, SWR-V3.39-004）**: `severity_override` 为字符串，理由写独立字段 `severity_override_reason`（dict 形态会被机械归一化并告警）
机械值 + 告警行）：
| 级别 | 账本族（CWE） |
|---|---|
| 严重 | 注入/反序列化（78/94/77/502）+ MEMORY-SAFETY（787/125/416/415/476/190/129/843）+ NUMERIC 整数下溢（191，与 190 对称） |
| 高 | SQLi/路径/SSRF（89/74/22/918）+ 鉴权主体（862/863/639/306）+ RESOURCE-DOS（400/770/789/409/833/834）+ RACE（362/366/367）+ STATE 状态机序对/协议类（841/696）+ NUMERIC 除零（369）+ ERROR-HANDLING 未初始化（457）+ WEB 请求走私（444）+ RESOURCE-DOS ReDoS（1333） |
| 中 | XSS/弱鉴权（79/601/352/285/287/926）+ CRYPTO/DATA-INTEGRITY（327/326/338/347/330/310/311/295/345/351/829）+ STATE 状态机控制流（670）+ NUMERIC 截断/不一致比较（681/697）+ ERROR-HANDLING 初始化不完整（665）+ WEB 双解析器前提（436） |

无 cwe 命中 → claim_type 回退（rce/leak→严重，crash/panic/oom/unbounded/
protocol_dos→高，xss→中）→ medium 默认。leak→严重已入表（REQ-V3.4.3-006）。

**containment 调整（v3.17, SWR-V3.17-003）**：机械映射后按候选 `containment`
降档——`language` 仅 critical→high；`process_sandbox` 逐档（critical→high→
medium）；`hardware_isolated` 两档；medium 封底；none/缺失零变化；
`severity_override` 仍绝对优先。调整时来源串写 `containment:xxx`，问题清单
行尾渲染 `[语言防护]/[沙箱收敛]/[硬件隔离]` 标记。

## 📏 数据模型速查

- **verify_queue.json**：`{candidates:[{id,source_file,source_line,sink_type,status:PENDING|VERIFIED|ESCALATED|NEEDS_REVIEW,verdict,reachability_type,call_chain[],call_chain_depth,edge_evidence[{edge,proof}],evidence_grade:static_only|edge_proven|empirically_confirmed,grade_self_reported,blocking_point,claim_type∈{crash,panic,oom,unbounded,xss,protocol_dos,rce,leak,other},severity_override∈{critical,high,medium}?,severity_override_reason?,containment∈{none,language,process_sandbox,hardware_isolated}?,attacker_tier∈{same_process,same_device_cross_app,system_broker,remote}?,attempt,escalated_reason,correction_record[],empirical{},resurrection_review{revived,outcome},guard_pass_subsets[]?,premises_verified[]?}], r4_findings:[{hypothesis_id,verdict,findings[]}], escalated_signed_off}`
  （v3.22 注：refutation 签收字段存储键为**单数**
  `attribution_correction`/`strengthened_verified_by`/
  `attribution_correction_verified_by`——主代理签写脚本须以队列实际
  存储键为准（复数误写两段式清理实录）
（v3.19 注：`correction_record[]` 双形态——str 为注记、dict 为 demote 裁决
  {demote_to, reason, adjudication_verification}，assert_ledger 对 str 条目
  lenient 跳过；`resurrection_review` 为主代理实证降级 UNREACHABLE 时的同步
  簿记 {revived:false, outcome}）
- **input_surface.json**：`{surfaces:[{id,name,type,entry_points[],taint_channels[],trust_boundary:{type},confidence,downstream_hints[],semantic_axis?{namespace,anchor_files[],cardinality}}], conflicts[], mirror_pairs[]}`
- **target_profile.json**：`{recommended:{surface_model:entry|semantic|hybrid,generation_layers[],scale_class,containment_default,empirical_modes[]},signals[],confidence,signed_by,overrides{}}`（v3.17 形态画像签收物；未签收 = 全默认 = 现状行为）
- **hypotheses.json**：`{hypotheses:[{id,surface_id,signature_id,semantic_family,cwe[],hit_sites[],checklist[]}], logic_hypotheses:[]}`（v3.4.5 起佐证器 gen 输出独立文件 `hypotheses_gen.json`——文件所有权分离，LLM 主路径产物不得被覆盖，主代理合并两文件）
- **语言词汇两轴（v3.5.2 注）**：① 签名标签 = 签名侧内部名，允许 superset（`cs`/`typescript`/`js` 等，校验白名单 VALID_LANGS）；② 账本/任务书/队列输出 = 归一化到账本 16 规范名（`cs↔csharp`、`ts`/`typescript`↔`javascript`、`ps↔powershell`）。跨模块 alias map 取值一致（有测试守卫），签名 L2 过滤双侧归一化后等值比较。
- **形态判定四轴职责表（v3.31, SWR-V3.31-006）**：
  | 轴 | 值域 | 判定时点 | 消费者 | 门禁承载 |
  |---|---|---|---|---|
  | project_kind | framework/library/infra/app | R1 context（机械） | 测绘期上下文提示 | 无 |
  | maturity | developing/mature | R1 context（git 标签语义） | R4 并行触发之一 | 无 |
  | target_kind | application/library/hybrid | R0 签收 | 存在性规则装载 + R4 并行触发之一 | ⑧ |
  | target_profile | 五轴推荐 | R0 签收（未签收=全默认） | 语义轴/super-large 目标专用 | 无 |
  四轴各司其职不互代：context 两轴是测绘期提示，R0 两轴是验证期判据（v3.5.2 注）。
- **R2/R4 通道边界条款（v3.31, SWR-V3.31-006）**：R2 主通道=面图驱动假设
  （surface→sink→缺陷机制）；R4 通道=族假说深挖（H1-H7 按族枚举，不依赖面图
  粒度）。两通道发现力有重叠是设计内形态（库型目标 R2 面图粗、R4 深挖出
  7/9 实录），同事实由 claim_nulled_by 主申报方承载消化——**重叠不重造机制，
  边界模糊时以 R4 为准补盲**（R4 是深度通道，R2 是广度通道）。
- **形态判定两轴（v3.5.2 注）**：`project_kind`（R1 上下文信号，4 值 {framework, library, infra, app}）与 `target_kind`（R0 门禁签收，3 值 {application, library, hybrid}）是**两个独立轴**——前者是测绘期上下文提示，后者是验证期门禁判据；不要混用（surface_mapper.py docstring 交叉引用）。

## ⚠️ 编排层四条铁律（W5 回归教训，强制执行）

1. **写读竞态**：读子智能体产出前必须重试校验；通知到达 ≠ 文件已 flush。
2. **schema 契约**：任务书内嵌 canonical schema（见 R1），校验器归一化是兜底不是依赖。
3. **证据裁决**：证据不匹配时不静默放行也不盲目拒收——suggested_line/suggested_lines 交主代理裁决，证据重写必带 `*_by: main-agent` 标记。
4. **args 形态纪律（v3.4.5, SWR-V3.4.5-005）**：派发 Workflow 时 args 必须按导出 `next_step` 声明的形态（对象包裹，`args={"candidates": <payload>}`）传递；裸数组是派发错误——脚本已容忍自动包装（机械兜底，SWR-V3.4.5-002），纪律上禁止依赖兜底（gRPC 复活波裸数组误传失败实录）。

## 📟 附录：CLI 速查（命令面全集）

> 审计执行所需的完整命令面。用法细节以各模块 docstring 为准；此处为
> 阶段归属索引。R 段正文已展开的命令（fidelity/hints 等）不重复展开。

| 命令 | 阶段 | 用途 |
|---|---|---|
| `surface_mapper.py scope snapshot/context/validate/merge` | R0/R1 | 范围快照/架构上下文(maturity·project_kind)/面校验/面合并 |
| `signature_lib.py selfcheck` | R0 | 签名库自检（fixture 召回 vs 完整性自检双语义） |
| `target_kind.py / target_profile.py --write` | R0 | 目标形态/画像判定 |
| `signature_matcher.py index/match/gen` | R2 | 签名佐证器（可选链路） |
| `r2_guard.py validate/anchor/drops/fidelity` | R2 | 假设 schema/锚点/筛选落盘/保真校验 |
| `batch_verify.py --stage next/collect/bump-attempt` | R3 A' 降级 | 手工波次驱动 |
| `batch_verify.py --stage workflow-script [--mode verify|refutation]` | R3/R3.5 | Mode W 脚本导出 |
| `batch_verify.py --stage r35-collect/r35n-collect` | R3.5 | 证伪多数决/复活收集 |
| `batch_verify.py --stage r4-collect/r4-assert` | R4 | 业务假说收集/断言 |
| `batch_verify.py --stage grade-recheck` | R5 | 分级机械重算 |
| `batch_verify.py --stage coverage-ledger [--write]` | R6/选题 | 覆盖账本读/回填 |
| `batch_verify.py --stage assert/status/report/reopen/scope-review/tracked-ids` | 收尾 | 门禁断言/队列状态/报告/重开/范围裁决/覆盖对账 |
| `language_issue_matrix.py hints/cells/inventory` | R2 | 假设空间提示 |
| `language_issue_matrix.py hitrate/stats/goal/seed` | R6 | 命中率记账/知识库状态/目标/回填（维护工具链） |
| `harness_runner.py templates/env` | R5 | 实证模板注册表/环境探针 |
| `fixminer.py <project> [--since N]` | R2 | 安全修复挖掘（修复驱动假设） |
| `lessons_recorder.py <project> --write` | R6 | lessons 机械提取落盘 |

## 📚 附录：资产地图

- 核心模块（L1 src/）：`surface_mapper.py`（R1）/ `signature_lib.py`+`signature_matcher.py`（R0/R2）/ `generation_registry.py`（生成层注册表）/ `language_issue_matrix.py`（语言问题矩阵, v3.18）/ `evidence_ledger.py`（分级+六门禁+一致性断言）/ `harness_runner.py`（R5）/ `workflow_export.py`（Mode W）/ `checklist_binder.py`（清单绑定）/ `precedent_library.py`（先例裁决）/ `r2_guard.py`（假设 schema 守卫）
- `tools/batch_verify.py`：队列编排 CLI（collect/bump-attempt/workflow-script/r4-*/assert/status）
- `tools/gen_tracking.py`：需求追踪矩阵重建（文档工具）
- `assets/resources/signature_library.json`：25 个签名（9 L3 语义族 + 16 L2 语言词族；回归锚点库在 `tests/fixtures/known_instances.json`，R0 完整性自检 + fixture 仓库 anchor recall；v3.6 起 L2 无确认锚点以 confirmed:false 占位诚实簿记）；`assets/resources/precedent_library.json`：19 条裁决先例（v3.5.2 裁 9 条永不可达先例；v3.12 增补 1 条状态机族；v3.15 增补 1 条守卫子集族；v3.41 增补 1 条逃生舱等价族）；`assets/resources/checklist_library.json`：50 条检查清单（v3.27 增补 1 条限额旁路枚举族; v3.40 增补 1 条修复残留同族枚举族; v3.41 增补 1 条通道转义对账族）（v3.12 增补 4 条状态机族；v3.13 增补 4 条数值语义/错误路径族；v3.15 增补 1 条 vendored 契约族；v3.17 增补 4 条运行时内存模型族 + 1 条生成物溯源族）
- `assets/task_templates/`：3 个任务书模板（surface_map_domain/hypothesis_filter/biz_hypothesis）；`assets/templates/harness/`：7 个实证模板（ws_frame_alloc/ws_frame_accum/xss_path_sim/parser_fuzz/resource_rate_probe/differential/paired_control_probe）；`assets/harness_manuals/`：16 语言工具链手册 + ENVIRONMENT_PROBES/mixed_build（共 18 个）
- `tests/`：555 个单测/集成测试（改模块后必须全绿）；`assets/lessons/`：全部历史教训 + W5 回归发现
- v2.1 遗产：仅 `docs/legacy/SKILL_V2.1.md`（规范备份）

---

## 🕰️ 附录：版本历史（增量段索引）

历史增量段全文已迁至 `docs/history/SKILL_INCREMENTS.md`（零内容损失,
追溯入口）；本表为版本链漂移守卫的机械锚点（最新行版本 == TOOLING）。
TOOLING 3.42。

| 版本 | 日期 | 主题 |
|---|---|---|
| v3.1 | 2026-08-17 | 15 语言战役 lessons W6 §1-24 的制度化 |
| v3.2 | 2026-08-17 | 混合语言项目能力 + 防漏放，已验收发布 |
| v3.2.1 | 2026-08-17 | 验收暴露四缺陷修复 |
| v3.3 | 2026-08-19 | 偏见审查 5 大类裁决 + Lua 审计教训的制度化 |
| v3.4.3 | 2026-08-20 | P0/P1/P2 验收缺陷闭环 |
| v3.4.4 | 2026-08-21 | v3.4.3 验收项目实测暴露缺陷修复 |
| v3.5 | 2026-08-23 | 三项体检修复：偏见 / 过设计 / 项目残留 |
| v3.5.2 | 2026-08-23 | 残留中项清零 + 过设计 B 裁决执行 + 偏见机械修复 |
| v3.6 | 2026-08-23 | 评估驱动机制修复 + 内容补全，无设计膨胀 |
| v3.7 | 2026-08-23 | 报告格式重构：问题清单按严重程度排序 + 机械生成 + 附录化 |
| v3.9 | 2026-08-28 | Pillow 审计复盘缺陷修复 |
| v3.10 | 2026-08-28 | kernel 级项目首例审计复盘缺陷修复 |
| v3.10.2 | 2026-08-29 | 多媒体系列 7 项目批次复盘缺陷修复 |
| v3.11 | 2026-08-29 | Android 系审计设计缺陷修复 |
| v3.12 | 2026-08-29 | 状态机分析能力补强 |
| v3.13 | 2026-08-29 | 错误路径处理族 + 数值语义族 + 账本锚点一致性修复 |
| v3.14 | 2026-08-30 | protobuf 复审计复盘缺陷修复 |
| v3.15 | 2026-08-30 | 五项目批次收官缺陷修复 |
| v3.16 | 2026-08-30 | v3.15 验收审计复盘缺陷修复 |
| v3.17 | 2026-09-01 | 运行时/引擎形态能力补全 |
| v3.18 | 2026-09-01 | 语言问题矩阵：per-language 知识基座 |
| v3.19 | 2026-09-02 | V8 审计复盘缺陷修复 |
| v3.20 | 2026-09-03 | WebKit 审计复盘缺陷修复 |
| v3.25 | 2026-09-06 | MaintainWise 验收审计复盘 |
| v3.24 | 2026-09-06 | 三引擎全景召回评估驱动 |
| v3.23 | 2026-09-06 | real-target 验证轮 + CVE-2026-85046 召回复盘缺陷修复 |
| v3.22 | 2026-09-04 | Firefox 验收审计复盘缺陷修复 |
| v3.21 | 2026-09-03 | WebKit 审计复盘缺陷修复·第二批次 |
| v3.26 | 2026-09-07 | 三轮评估 P0 交付链与防漂移修复 |
| v3.27 | 2026-09-08 | QuickJS 验收审计复盘·知识基座补种 |
| v3.28 | 2026-09-08 | Top15×Top10 目标物化 |
| v3.29 | 2026-09-08 | 闭环接线:控制器/执行器/反馈信号 |
| v3.30 | 2026-09-08 | paired_control_probe 双测对照探针 |
| v3.31 | 2026-09-08 | 人因闭环点机械化 |
| v3.32 | 2026-09-08 | 发现力四杠杆 |
| v3.33 | 2026-09-08 | Servo 验收复盘十一缺陷修复 |
| v3.34 | 2026-09-08 | 文件分层重构 |
| v3.35 | 2026-09-08 | SKILL.md 净化重构: 增量段迁档 + 只留审计设计 + 17 条规范性归位 |
| v3.36 | 2026-09-08 | Caddy 验收发现: trust_boundary 规范枚举透传修复 |
| v3.37 | 2026-09-09 | Caddy 验收复盘三修复: 任务书引用绝对化 + 切片容量/量级驱动权清单 |
| v3.38 | 2026-09-09 | 模型能力利用五机制: 同族不一致/自证伪轮/公开面前置/实证机会/harness 回收 |
| v3.39 | 2026-09-10 | haproxy 验收复盘四修复: 关键词词边界/seed 双写扩展/计数守卫集中/severity_override 契约 |
| v3.40 | 2026-09-12 | Hadoop 验收复盘七修复: fidelity 判级分支/攻击者字节承载/修复残留枚举/位域证据/setuid 拓扑手册/默认关方向/实证回填候选 |
| v3.41 | 2026-09-13 | hibernate-orm 审计复盘七修复: 复活 gap 字段契约分离/报告 import 路径对齐/claim_type 枚举告警/方言平台矩阵条款/通道转义对账清单/逃生舱等价先例/java 矩阵两格 |
| v3.42 | 2026-09-13 | Keycloak 审计复盘六修复: refutation 资格判定健壮化(空 dict=未复核)/r4-collect 近似键字段名诊断/verifier 分支级声称提示/upstream 已修声称树内核实/信息暴露跨信任域 drop 维度/实证回填前缀级联提示 |
