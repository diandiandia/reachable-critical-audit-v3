# Reachable Critical Audit v3.1 — 可达性严重漏洞审计 Skill

> 一个以 LLM 为主分析引擎、以**输入面测绘 → 假设 → 证据链 → 证伪 → 实证**为流水线的
> 通用安全审计 skill：只回答一个问题——**外部可控输入能否真实到达高危 sink 点**。
> 15 种编程语言战役验证（17 项目、六门禁全 PASS），产出的每个结论都携带证据分级
> （static_only / edge_proven / empirically_confirmed）与逐跳调用边证据。

**本目录是开发主仓库（v3.1-dev 分支）**：设计文档 + 完整运行时 + 测试 + 机器资产。
运行时权威在 Claude skill 目录（由 `install.sh` 安装）。

## 当前状态

| 阶段 | 状态 |
|---|---|
| v3.1 开发 | ✅ 完成（SWR-V3.1 49/49，73 测试全绿） |
| v3.1 验收 | ✅ Phase 3.1.3 PASS：拦截率 75%/66.7%/66.7% → 0%/20%/0%；零丢失 + 4 净增；六门禁全 PASS（详见 docs/design/ACCEPTANCE_V3_1.md） |
| 发布 | ✅ 已合并 main + install 到 skill 目录（运行时权威 = v3.1） |
| v3.2~v3.14 | ✅ 版本链持续演进（状态机/数值/错误处理族、平台信任模型清单、复活重验链、复审计幂等；各版设计件见 docs/design/） |
| v3.15 | ✅ 完成（2026-08-30）：五项目批次收官缺陷修复 14 项，TOOLING 3.15，全量回归 356 passed，install 双副本同步 |

---

**近期战绩**（2026-08-30 五项目批次收官，六门禁全 PASS）：libarchive 15 REACHABLE /
s2n-tls 1 / nghttp2 3 / gpac 11 / freetype 1——含 hardlink 写穿族、静态票钥 mTLS 绕过、
媒体脚本 RCE 主代理独立复现、gzip 解压 ~1000x CPU DoS 等 e2e 实证确认项。

## 1. 环境要求

### 1.1 平台（必需）

| 项 | 要求 |
|---|---|
| 运行平台 | Claude Code（或其他提供 `Workflow`/`Agent` 子智能体编排能力的平台） |
| 编排模式 | **Mode W**（`Workflow` 工具，默认）：pipeline/parallel + schema 强校验 + 断点续传；无 Workflow 时自动降级 **Mode A'**（`Agent` 工具手工循环，`--stage next/collect`） |
| LLM 能力 | 完全使用宿主 Agent 自身能力，**无需任何第三方 API Key** |

Mode B（独立 CLI 子进程）为 v2.1 机制，v3 起不再需要。

### 1.2 运行时（必需，核心模块零第三方依赖）

| 项 | 要求 | 说明 |
|---|---|---|
| Python | ≥ 3.8 | 核心模块（surface_mapper / signature_lib / signature_matcher / evidence_ledger / harness_runner / workflow_export / checklist_binder / precedent_library / r2_guard + tools/）仅用标准库（json/re/os/subprocess 等），不装任何包即可运行 |
| 测试（开发时） | pytest | `pip install pytest`（或使用 skill 自带 `.venv`） |

### 1.3 目标语言工具链（仅 R5 实证阶段按需）

skill 本体不依赖任何语言工具链；**只有 R5 实证抽验被触发时**才需要对应语言的工具链。
工具链缺失不阻塞审计——按 §17.7 源事实级规则降级并记录 blocker（哨兵值/算术类主张接受
源事实级；网络阻断同理）。15 种语言的工具链探测、陷阱清单与阳性模式见
`harness_manuals/<lang>.md`，速览：

| 语言 | 工具链 | 战役验证的关键事实 |
|---|---|---|
| C | gcc/make | `./configure && make` 实机构建可行；harness 失败先怀疑模块接管顺序 |
| C# | dotnet SDK | 现场可装 SDK；`-p:LibraryFrameworks=net8.0` 单 TFM 构建；net8 运行时影响 ReDoS 利用性 |
| Go | go | proxy.golang.org 可能不可达 → 源事实级 + 阻断记录 |
| Java | JDK + maven | `mvn -pl` 单模块 + dependency:build-classpath；JDK 22+ 变更 Inflater 语义 |
| Kotlin | kotlinc/JDK | 锁版本 jar 从 Maven Central 直取 + verbatim 函数提取（KMP 全量编译常失败） |
| PHP | php | define 常量 + 按 include 图补全局变量的最小真实环境 |
| PowerShell | pwsh | 7.5.2 实测可用 |
| Python | python3 | venv + sys.path 导入审计源码即可跑全链路（成本接近零） |
| Ruby | ruby | `ruby -Ilib` + Rack::MockRequest 零依赖探针 |
| Rust | cargo | PATH 检查 + dev-dep 可见性（transitive 不可用）+ 不盲从编译器 help 文本 |
| Scala | sbt/coursier | 495 文件规模舒适区 |
| Shell | zsh/bash | 原生 shell 即实证环境 |
| Swift | swift | 工具链代际/路径遮蔽是最常见陷阱；记录 `swift --version` |
| TypeScript | node/tsc | tsc 编译 + esbuild 降级链；函数体级提取标注 scope |
| Perl | perl | 系统 perl 即可 |

### 1.4 网络可达性（影响实证分级，不影响审计主流程）

| 域名 | 状态（本环境实测） | 影响 |
|---|---|---|
| github.com / repo1.maven.org / crates.io | 可达 | 源码拉取、jar/crate 依赖下载 |
| proxy.golang.org / google.golang.org | 可能不可达 | Go 实证降为源事实级并记录 blocker |

---

## 2. 安装

### 2.1 从开发仓库安装（本仓库 → Claude skill 目录）

```bash
cd /root/reachable-critical-audit-v3
./install.sh                          # 默认安装到 /root/.claude/skills/reachable-critical-audit
./install.sh ~/.claude/skills/reachable-critical-audit   # 或指定目标目录
```

install.sh 行为：
- 复制 SKILL.md + 9 个核心模块 + tools/ + resources/ + task_templates/ + templates/ +
  harness_manuals/ + lessons/ + tests/ + docs/legacy/SKILL_V2.1.md
- **同步删除**目标目录中已不在开发仓库的文件（单一权威：开发仓库是唯一事实源）
- 清理目标目录 `__pycache__`
- 冒烟验证：`python3 -m pytest <dst>/tests/ -q`（`PYTHON_BIN` 环境变量可覆盖解释器）

### 2.2 用户级安装（Claude Code skill 标准方式）

```bash
# 方式 A: 从开发仓库
./install.sh ~/.claude/skills/reachable-critical-audit

# 方式 B: 手工（只要 SKILL.md + 运行时文件）
mkdir -p ~/.claude/skills/reachable-critical-audit
cp SKILL.md ~/.claude/skills/reachable-critical-audit/
# 其余文件按 install.sh 的清单复制（模块/tools/resources/task_templates/templates/harness_manuals/lessons）
```

安装后 Claude Code 自动发现该 skill（`SKILL.md` 位于
`~/.claude/skills/<name>/SKILL.md`）。

### 2.3 安装验证

```bash
# 1) 模块可用
python3 -c "import sys; sys.path.insert(0,'<skill_dir>'); import surface_mapper, evidence_ledger; print('ok')"

# 2) 资产完整（v3.1 三资产）
python3 -c "import json; json.load(open('<skill_dir>/resources/precedent_library.json')); json.load(open('<skill_dir>/resources/checklist_library.json')); print('ok')"
ls <skill_dir>/harness_manuals/ | wc -l    # 期望 18

# 3) 测试全绿
python3 -m pytest <skill_dir>/tests/ -q
```

---

## 3. 快速开始（审计一个项目）

```bash
# 对 <project> 执行完整 v3 流程（在 Claude Code 会话中向 Agent 发出）:
# "使用 reachable-critical-audit skill 审计 <project>"

# skill 内部流水线（各阶段产物落 <project>/.audit_results/）:
# R0   目录守卫 + 签名库冒烟 (hit_rate<1.0 且 testable>0 才阻止) + maturity 判定
# R1   输入面测绘: surface_mapper.py context/tasks → 分域 agent → validate/merge
#      → input_surface.json (每 surface 附 entry_points 源码证据)
# R2   假设: signature_matcher 窗口匹配(佐证) + LLM 假设(主路径)
#      → hypotheses.json (LLM 主路径) + hypotheses_gen.json (佐证器 gen, v3.4.5 文件所有权分离)
# R3   验证: Workflow 波次 → verify_queue.json (边证据/证据分级/家族清单/自证伪)
# R3.5 复核: N=2 证伪者多数决 → 裁决(先例库匹配 + 同族一致性断言)
# R4   业务假说 H1-H7 (mature framework 与 R3 并行; H7=默认值全表五维盘点)
# R5   实证: 声称类强制 (crash/panic/oom/unbounded/xss/protocol_dos)
# 六门禁 → 报告 reachable_vulnerabilities_report.md
```

审计产物全部以 `.audit_results/` 为前缀，不写入项目源码根目录。

---

## 4. 目录结构

```
├── SKILL.md                  ★ skill 规范（v3 流程 + v3.1 变更摘要）
├── install.sh                安装脚本（开发仓库 → skill 目录）
├── *.py  × 9                 运行时模块（v3 六核心 + v3.1 三件套）
├── tools/                    batch_verify（队列编排）/ gen_tracking（文档工具）
├── resources/                signature_library（25 签名）/ precedent_library（16 先例）
│                             / checklist_library（29 清单）
├── harness_manuals/          16 语言 + 2 通用实证手册，共 18 个（v3.1 机器资产）
├── task_templates/  ×3       子智能体任务书（测绘/筛选/验证——v3.4 起按需组装）
├── templates/harness/  ×5    实证模板（ws_frame_alloc / ws_frame_accum / xss_path_sim
│                             / parser_fuzz / resource_rate_probe）
├── tests/  ×16               190 个测试（改模块后必须全绿）
├── lessons/                  全部历史教训（W5/W6/按语言）——机器资产的上游证据源
└── docs/
    ├── design/               文档级联: SYSTEM_DESIGN → REQ → SW_DESIGN → SWR → TRACKING
    │                         （v3 与 v3.1 各一套, 每条需求带编号/状态/验收判据）
    ├── history/              设计期评估（ARCHITECTURE_EVAL_v3 / GENERALITY_EVAL / WORKFLOW_EVAL）
    └── legacy/               SKILL_V2.1.md（v2.1 规范备份, 历史对照）
```

### 机器资产（v3.1 核心概念）

| 资产 | 内容 | 作用 |
|---|---|---|
| `precedent_library.json` | 16 条裁决先例（criterion/counterexample/applicability_scope/applications） | R3.5 裁决与自证伪提示的机器化依据——同一前提形态在 16 语言给出同一裁决 |
| `checklist_library.json` | 29 条检查清单（结构化 binding: cwe/keywords/verdict_context） | verifier 强制自查项——16 语言证伪者攻击面固化 |
| `harness_manuals/*.md` | 16 语言 + 2 通用手册（共 18 个） | 实证成本从"每项目重付陷阱清单"降为一次性入册 |

三者随审计进化（先例 applications 回填 / 新先例追加 / 清单回填），是 skill 的知识层。

---

## 5. 测试

```bash
# 全量（模块纯 stdlib; tree-sitter 相关测试需 .venv）
/root/.claude/skills/reachable-critical-audit/.venv/bin/python3 -m pytest tests/ -q

# 单模块
python3 -m pytest tests/test_evidence_ledger.py tests/test_surface_mapper.py -q
```

---

## 6. 文档级联索引

| 文档 | 内容 |
|---|---|
| `docs/design/SYSTEM_DESIGN_V3.md` | v3 架构设计（输入面→假设→证据链→实证） |
| `docs/design/SYSTEM_DESIGN_V3_1.md` | v3.1 设计（十大问题域 P-A~P-J 与论证） |
| `docs/design/REQ_V3.md` / `REQ_V3_1.md` | 系统需求（75/72 条，编号+来源+优先级+验收判据） |
| `docs/design/SW_DESIGN_V3.md` / `SW_DESIGN_V3_1.md` | 软件设计（模块分解/接口签名/算法） |
| `docs/design/SWR_V3.md` / `SWR_V3_1.md` | 软件需求（满足追溯 REQ + 状态 未开发/开发中/已完成） |
| `docs/design/REQUIREMENTS_TRACKING.md` | 需求追踪矩阵（状态汇总） |
| `lessons/W6_MORE_LANGS_FINDINGS.md` | 15 语言战役 130+ 条缺陷发现（资产的上游证据） |

---

## 7. 常见问题

**Q: 没有目标语言工具链能审计吗？**
能。审计主流程（R0-R4）不依赖工具链；R5 实证缺失时按源事实级规则降级（哨兵值/算术类
主张）或 NEEDS_REVIEW，blocker 必须记录在案。

**Q: 网络被阻断怎么办？**
依赖拉取失败记录 blocker 后走源事实级/verbatim 提取路径（harness_manuals 各语言手册有
对应阳性模式）；github/maven/crates 可达性见 §1.5。

**Q: v3.1 和 v3 什么关系？**
v3.1 是 v3 的增量升级（不改变阶段骨架），把 15 语言战役中主代理手工补救的动作机械化
（先例库/检查清单库/语言手册 + verifier 步骤 0/自证伪）。开发完成待验收，验收判据见
`docs/design/SYSTEM_DESIGN_V3_1.md` §8。

**Q: 在哪里看历史版本？**
v2.1 规范备份在 `docs/legacy/SKILL_V2.1.md`；全部设计期评估在 `docs/history/`。
