# Reachable Critical Audit Skill v3 — 系统架构设计文档

> **文档性质**：v3 架构设计（草案 0.1）。上游输入：`../history/ARCHITECTURE_EVAL_v3.md`（31 类缺陷评估）
> 与 8 份实测 lesson。v2.1 现行设计见本仓库 `SYSTEM_DESIGN.md`。
> **日期**：2026-08-16
> **设计目标**：解决 v2.1 的三类架构级根因（规则库-输入面匹配矛盾、验证信任缺独立证据源、
> 指标体系建立在错误假设上），保留 v2.1 中被 11 次审计验证有效的机制。

---

## 1. 设计原则

从 11 次审计的实证数据提炼（15.5 万+ L0 命中产出 0 REACHABLE；全部真实发现来自 L1/R4/R0.5/人工）：

| 原则 | 含义 | 数据支撑 |
|---|---|---|
| P1 **LLM 是主分析引擎** | 测绘、回溯、判断由 LLM 承担 | extractor 产出 100% 真实发现 |
| P2 **规则库降为提示器** | 规则只提示"该看什么"，不做判定 | L0→REACHABLE 转化率 <1% |
| P3 **输入面测绘先行** | 先回答"数据从哪里进来"，再找 sink | Dubbo/lighttpd/Vapor 的真实输入面全靠人工背景注入才兜住 |
| P4 **证据分级可问责** | 每个 verdict 附证据类型与来源，不采信裸断言 | H3-L1 幻觉被实证证伪 |
| P5 **实证是终结裁判** | DoS/崩溃/内存类声称必须 harness 实测 | 4 次实测：3 确认 1 证伪 |
| P6 **工具链是证据账本** | 队列/落盘/断言的全部职责是保存证据链，不是统计命中 | 4 次断言不一致复现的教训 |

---

## 2. 总体架构

```
                        ┌────────────────────────────────────────────┐
                        │            审计编排器 Orchestrator           │
                        │  阶段状态机 │ 任务书下发 │ 证据账本 │ 指标    │
                        └────────────────────────────────────────────┘
                          ↑ 产出回写            │ 任务书下发（含输入面背景）
        ┌─────────────────┴──────────┐   ┌─────┴──────────────────────────┐
        │  R1 输入面测绘层            │   │  R2 签名提示匹配层               │
        │  (LLM 子智能体 × 分域)      │   │  (signature_matcher + LLM 筛选)  │
        │  产出 input_surface.json   │→ │  产出 hypotheses.json           │
        └────────────────────────────┘   └────────────────────────────────┘
                                                    ↓
        ┌───────────────────────────────────────────────────────────────┐
        │  R3 证据链回溯层 (verifier × 候选簇)                            │
        │  每跳调用边 grep 证据 │ 平台/受信前提检查 │ evidence_grade 分级   │
        └───────────────────────────────────────────────────────────────┘
                                                    ↓
        ┌───────────────────────────────────────────────────────────────┐
        │  R4 业务假说层（H1-H6 + 信任边界专项 H7）                       │
        └───────────────────────────────────────────────────────────────┘
                                                    ↓
        ┌───────────────────────────────────────────────────────────────┐
        │  R5 实证抽验层 (harness 模板库 + 执行器)                        │
        │  DoS/崩溃/内存类强制 │ 结果写回 verdict │ 证伪触发回溯修正       │
        └───────────────────────────────────────────────────────────────┘
```

**与 v2.1 的本质差异**：数据流从"规则扫描 → 候选队列 → 逐条验证"变为
"输入面 → 假设 → 证据链 → 实证"；队列中的对象从"规则命中"变为"带证据的假设"。

---

## 3. 核心数据模型

### 3.1 input_surface.json（R1 产出，审计的主索引）

```json
{
  "schema_version": "3.0",
  "project": {"name": "awstats", "language": "perl", "maturity": "mature"},
  "surfaces": [
    {
      "id": "S-001",
      "type": "network_endpoint",
      "name": "CGI query parameters",
      "entry_points": [{"file": "wwwroot/cgi-bin/awstats.pl", "line": 17593,
                         "function": "main", "evidence": "QueryString 解析入口"}],
      "taint_channels": ["query_string", "http_headers"],
      "downstream_hints": ["config file selection", "log parsing", "HTML report rendering"],
      "trust_boundary": {"type": "unauthenticated_remote", "gate": "none"},
      "confidence": "high"
    }
  ]
}
```

设计要点：
- **surface 是审计的原子单位**：R2 只对 surface 的 entry_points 做下游追踪，不再全库扫描
- `downstream_hints` 由测绘 agent 给出"这个输入面下游可能到哪"，供签名匹配定向
- `trust_boundary` 显式记录每个通道的信任状态（v2.1 的 Dubbo"受信边界惯例假设"教训）

### 3.2 hypotheses.json（R2 产出，替代候选队列的"规则命中"）

```json
{
  "hypotheses": [
    {
      "id": "HYP-001",
      "surface_id": "S-001",
      "signature_id": "SIG-PATH-WHITELIST-002",
      "cwe": ["CWE-22"],
      "sink_hint": "awstats.pl:1776 configdir 门禁",
      "semantic_family": "whitelist-bypass-unanchored",
      "checklist": ["校验是否锚定", "规范化缺失点", "下游文件操作形态"],
      "status": "PENDING"
    }
  ]
}
```

设计要点：
- **hypothesis 携带语义家族与检查清单**（v2.1 只有 sink 位置 + CWE 标签，verifier 从零开始）
- 签名命中只是"生成假设"，假设的真实性由 R3 判定——规则盲区不再等于漏报

### 3.3 verify_queue.json（R3 候选，扩展证据字段）

```json
{
  "candidates": [
    {
      "id": "CAND-001",
      "hypothesis_id": "HYP-001",
      "verdict": "REACHABLE",
      "evidence_grade": "edge_proven",
      "call_chain": ["f1:10", "f2:20", "f3:30"],
      "edge_evidence": [
        {"edge": "f1:10->f2:20", "proof": "grep -n 'fn2(' f1: caller at line 10"},
        {"edge": "f2:20->f3:30", "proof": "grep -n 'fn3(' f2: caller at line 20"}
      ],
      "platform_precondition": "linux_only",
      "platform_evidence": "CI matrix: ubuntu/macos runners only",
      "empirical": null,
      "status": "VERIFIED"
    }
  ]
}
```

**evidence_grade 分级**（P4 的落地形态）：

| 级别 | 含义 | 升/降级规则 |
|---|---|---|
| `static_only` | 仅静态数据流链，无逐跳证据 | 默认起点；不得直接用于 CVE 申报 |
| `edge_proven` | 每跳调用边有 grep 证据 | 任务书强制要求；REACHABLE 的最低可申报级别 |
| `empirically_confirmed` | harness 实测确认 | R5 强制（DoS/崩溃/内存类）；证伪则回溯修正 |

### 3.4 signature library（签名提示库，替代规则库）

```json
{
  "sig_id": "SIG-BUFFER-ACCUM-001",
  "semantic": "远端投递数据的无界累积（帧/body/流）在大小校验之前发生",
  "cwe": ["CWE-770", "CWE-789"],
  "platform_profiles": ["server-framework"],
  "detection_hints": {
    "grep": ["extend_from_slice", "writeFully", "append(", "readRemaining", "++= payload"],
    "ast": [],
    "checklist": [
      "累积点在哪里？",
      "flush/对齐条件是什么？",
      "上限在累积之前还是之后检查？"
    ]
  },
  "known_instances": [
    {"project": "actix-web", "file": "actix-web-actors/src/ws.rs:771"},
    {"project": "ktor", "file": "ktor-shared/ktor-websockets/jvm/.../SimpleFrameCollector.kt:23"},
    {"project": "akka-http", "file": ".../Http2StreamHandling.scala:584"}
  ],
  "empirical_harness": "ws_frame_accum"
}
```

设计要点：
- **签名按语义族表达，语言无关**——一个签名覆盖 actix/ktor/akka 三家同源缺陷（10 语言战役的"家族同源"教训制度化）
- `known_instances` 是活字段：每次审计确认一个新实例就回填（签名库随审计进化，而非等待专家维护）
- `empirical_harness` 指向 R5 的 harness 模板

---

## 4. 阶段流程详述

### R0 工具自检（保留 + 扩展）
- 保留：依赖 bootstrap、锚点召回门禁（改名"签名库冒烟测试"：每个签名必须有 known_instance 可复现）
- 新增：harness 执行器可用性检查（R5 的前置）

### R0.5 考古（保留 + --cross-tags）
- 保留：安全修复 diff 考古
- 新增：`--cross-tags t1,t2,t3` 输出"修复 commit 是否在 tag"矩阵（AWStats 三 tag 模式制度化）
- 新增：HEAD 审计自动切"变体复核"模式（C 篇 1.4.5 教训）

### R1 输入面测绘（新阶段，替代全库规则扫描）

**输入**：项目源码 + 构建清单（README/Package.swift/Cargo.toml/pom.xml/CMakeLists）
**分域测绘**（每域一个子智能体，任务书含项目背景——v2.1 中被证明是 L1 产出的决定性因素）：

| 域 | 探测内容 |
|---|---|
| 网络面 | HTTP/WS/RPC 端点、协议解码器、管理端口 |
| 数据面 | 文件上传/下载、配置加载、日志文件解析 |
| 进程面 | IPC、环境变量注入、命令行参数、信号 |
| 存储面 | 数据库查询入口、缓存键来源、模板加载 |

**质量门禁**：每个 surface 必须附 entry_points 的源码证据（file:line + 代码片段）；测绘产出由主 Agent 复核。

### R2 签名提示匹配（替代全库扫描）

1. `signature_matcher.py` 对每个 surface 的 entry_points 做**下游窗口扫描**（沿调用图展开 N 层，仅窗口内匹配签名的 grep hints）——候选量从 5 万级降到百级
2. 每个签名命中生成 hypothesis（含语义家族 + 检查清单）
3. LLM 快速筛选：假设是否值得进 R3（排除明显常量/白名单场景）
4. LOGIC_PATTERN 类签名（授权谓词弱化、修复-再暴露）独立匹配，不依赖污点链

### R3 证据链回溯（verifier 升级）

- **每跳调用边 grep 证据强制**：任务书要求 call_chain 每相邻两跳附调用点证据；缺证据自动降级 `static_only`（v2.1 的 H3-L1 幻觉制度化防御）
- **前提维度检查**：platform_precondition（CI matrix/Package 平台声明）、trust_boundary（每通道验证"远端数据确实无法流入"，禁止惯例假设）、gate（可降级配置门控显式记录）
- **死代码豁免**：`blocking_point: "no production callers"` 是合法阻断，不强制 3 层链（C 篇 1.4.4 教训）

### R4 业务假说（H1-H6 + H7）

- 保留 H1-H6（6 类假说在 lighttpd/django 等成熟项目是唯一真实发现来源）
- **新增 H7 信任边界专项**："同 UID/进程组/IPC 是否可触发宿主高危操作""路径语义（.. 上溯/symlink/空路径）是否越界""鉴权谓词是否可被弱化"（gvisor/container 教训）
- 规模自适应档位：小项目 3×2 / 大项目 6 / 战役模式 1×6 + `r4_consolidated` 标注

### R5 实证抽验（新阶段，强制触发条件）

| 触发条件 | harness 模板 |
|---|---|
| verdict 声称 crash/panic/trap | 进程存活 + exit code 观测 |
| verdict 声称 OOM/无界分配/累积 | RSS/VmRSS 时序采样（逐秒） |
| verdict 声称 XSS/注入 | 代码路径模拟（perl/python 复刻精确路径） |
| verdict 声称协议级 DoS | 裸 socket 构造畸形帧/头 |

**harness 模板库**（本次 4 个实测的沉淀）：
- `ws_frame_alloc`（ktor 1GB 帧头 → RSS +1GB，PoC: /root/10LANG_PoC/）
- `ws_frame_accum`（actix 4GB 声明 + 流式，RSS 线性增长采样）
- `xss_path_sim`（AWStats diricons perl 路径模拟）
- `multipart_align`（django 累积模式 + 解析器节奏插桩）

**结果写回**：`empirical` 字段 + evidence_grade 升级/证伪回溯（证伪 → verifier 错误记录 → 任务书反例注入）。

---

## 5. 量化指标（过程问责制）

| 指标 | 定义 | 门禁 |
|---|---|---|
| 输入面覆盖率 | 已做下游追踪的 surface / 测绘 surface 总数 | =100%（同 v2.1 PENDING 清零） |
| 证据分级分布 | edge_proven / static_only / empirical 计数 | REACHABLE 且 static_only ≤ 0（不得裸申报） |
| 实证验证率 | empirically_confirmed / 可实证类声称总数 | DoS/崩溃类 =100% |
| verdict 修正记录 | 证伪/降级/跨 CWE 冲突修正清单 | 报告中显式列出 |
| L0 噪音率（参考） | 签名命中 → 假设 → 真实候选的转化率 | >80% 时提示签名库修整 |

SDR/SNR 降为参考指标（v2.1 教训：规则盲区时它们衡量的是幻觉）。

---

## 6. 与 v2.1 的组件映射（迁移成本）

| v2.1 组件 | v3 处置 | 说明 |
|---|---|---|
| ast_scanner.py 全库扫描 | **替换**为 signature_matcher 面内扫描 | 保留其 tree-sitter 能力作为可选深度模式 |
| security_profiles.json 规则库 | **降级**为 signature library 的初始数据源 | 现有规则转写为语义签名（方法名→语义族） |
| verify_queue.json | **保留+扩展**（hypothesis_id/evidence_grade/edge_evidence） | 状态机语义不变 |
| batch_verify.py | **保留+修复**（C1-C10 全部工程项） | 队列/collect/assert 逻辑复用 |
| r05_diff_archaeology.py | **保留+扩展**（--cross-tags、NO_GIT、变体复核模式） | |
| R1.5 framework-sink-extractor | **升格**为 R1 输入面测绘（其任务书模板复用） | 本战役证明的"背景注入"制度化 |
| R3 vulnerability-verifier | **升级**（调用边证据+前提维度+证据分级） | 任务书模板改写 |
| R4 business-logic-verifier | **保留+扩展**（H7 信任边界） | |
| 新增：surface_mapper.py | R1 测绘任务书生成 + input_surface.json 校验 | ~300 行（现有 r15 生成器同构） |
| 新增：signature_matcher.py | 面内窗口扫描 + hypothesis 生成 | ~400 行（grep+简单调用图） |
| 新增：evidence_ledger.py | verdict 证据字段校验 + 分级检查 + 断言 | collect/assert 的扩展 |
| 新增：harness_runner.py | R5 harness 模板调度 + 结果采集 | 本次 4 个 harness 的脚本化 |

---

## 7. 实施路线图

**Phase 1（v2.2，1-2 周）**：全部 18 类工程修复（工具链 C1-C12 + 机械降噪层 + 簇验证官方化 + 心跳/冲突检测 + --cross-tags）——v3 的证据账本与队列语义在此阶段打底。

**Phase 2（v3 核心，2-3 周）**：
1. input_surface.json + surface_mapper.py（R1 测绘，复用 r15 任务书模板）
2. signature library 初版（现有规则转写 + 本战役 33 个家族的 known_instances 回填）
3. signature_matcher 面内扫描 + hypotheses 队列
4. verifier 任务书升级（边证据 + 前提维度 + 分级）

**Phase 3（v3 完备，1 周）**：
5. R5 harness 模板库 + 强制触发规则
6. 指标重构 + 报告模板
7. 回归验证：用本战役已审计的 3 个项目（sinatra/lighttpd/actix）复跑，对照已知结论校准

---

## 8. 可行性论证与风险

**可行性**：核心构件全部在 v2.1 或本战役中有工作原型——
- 输入面测绘 = 现有 R1.5 extractor（已被 11 次审计验证产出 100% 真实发现）
- 签名匹配 = grep 级别（提示不需要 AST 精度）
- 证据账本 = 现有 collect 校验的扩展（已拦下 4 次断言不一致）
- harness = 本战役 4 个实测脚本（各 <1h 成本）
- 无任何新引入的技术依赖（无 LLM API 之外的组件）

**风险与缓解**：

| 风险 | 缓解 |
|---|---|
| 签名库重蹈规则库覆辙（盲区） | 签名是"提示"非"判定"；盲区代价从漏报降为"未提示"；known_instances 随审计回填自进化 |
| R1 测绘质量依赖 LLM | 测绘证据强制（entry_points 附源码证据）+ 主 Agent 复核 + 分域并行互相交叉 |
| 逻辑类漏洞（鉴权绕过）难实证 | 证据分级不强制所有类型；edge_proven 是可申报下限 |
| 面内窗口扫描漏掉长链 sink | 窗口深度可配 + R4 假说兜底（v2.1 的 R4 已证明是成熟项目的兜底网） |

---

## 附录：与 v2.1 的差异速查

| 维度 | v2.1 | v3 |
|---|---|---|
| 主引擎 | 规则库（静态签名） | LLM（测绘+回溯+判断） |
| 规则库角色 | 判定器 | 提示器 |
| 审计起点 | 全库扫描 | 输入面测绘 |
| 队列对象 | 规则命中（5 万级） | 带语义家族的假设（百级） |
| verdict 依据 | 调用链深度 | 证据分级（链+边证据+实证） |
| 幻觉防御 | 深度门禁 | 边证据强制 + 实证抽验 + 证伪回溯 |
| 指标 | 规则库覆盖（SDR/SNR） | 过程问责（面覆盖/证据分级/修正记录） |
| 规则库维护 | 专家手工 | 审计回填（known_instances 自进化） |

---

## 9. 组件接口规格（D-COMP，供需求导出）

### D-COMP-01 surface_mapper.py（R1 输入面测绘编排）

| 接口 | 签名 | 说明 |
|---|---|---|
| 生成任务书 | `gen_surface_tasks(project_root, lang) -> list[TaskSheet]` | 按 4 域（网络/数据/进程/存储）生成测绘任务书，任务书携带项目背景（架构线索：README/依赖清单/构建文件摘要） |
| 校验测绘产出 | `validate_surfaces(path) -> (ok, errors)` | 校验 input_surface.json schema；每个 surface 必须有 entry_points 证据（file:line + 代码片段），否则拒收 |
| 合并 | `merge_surfaces(files) -> input_surface.json` | 多 agent 产出合并、去重（同一 entry_point 多域归属）、冲突标注 |

### D-COMP-02 signature_library.json（语义签名库）

| 字段 | 类型 | 说明 |
|---|---|---|
| sig_id | str | SIG-<FAMILY>-<NNN> |
| semantic | str | 语义族描述（语言无关） |
| cwe | list | 关联 CWE |
| platform_profiles | list | 适用平台 profile（server-framework/desktop/embedded/cli-tool） |
| detection_hints.grep | list | 面内匹配用 grep 模式 |
| detection_hints.checklist | list | verifier 检查清单（假设的一部分） |
| known_instances | list | 真实审计实例（{project, file:line, confirmed}）——新增签名强制非空 |
| empirical_harness | str\|null | 关联 R5 harness 模板 id |

### D-COMP-03 signature_matcher.py（R2 面内签名匹配）

| 接口 | 签名 | 说明 |
|---|---|---|
| 窗口展开 | `expand_window(entry, depth) -> list[call_site]` | 从 entry_point 沿调用图展开 N 层（默认 3），产出窗口内调用点集合 |
| 签名匹配 | `match_signatures(surfaces, signatures, depth) -> list[Hit]` | 对窗口内调用点跑 grep hints；命中产出 {surface_id, sig_id, site, matched_pattern} |
| 假设生成 | `gen_hypotheses(hits) -> hypotheses.json` | 去重（同 surface×sig 合并）、填充检查清单、生成 HYP-xxx |
| LLM 筛选接口 | `emit_filter_tasks(hypotheses) -> list[TaskSheet]` | 每批假设生成 LLM 快速筛选任务书（排除常量/白名单场景） |

### D-COMP-04 evidence_ledger.py（证据账本/verdict 分级）

| 接口 | 签名 | 说明 |
|---|---|---|
| 分级校验 | `grade_verdict(v) -> (grade, errors)` | 按 evidence_grade 规则校验：REACHABLE 且无 edge_evidence → 强制 static_only；边证据缺 proof → 拒收 |
| 前提维度校验 | `check_preconditions(v) -> list[Issue]` | platform_precondition 必须有 platform_evidence；trust_boundary 必须逐通道验证记录；gate 显式记录 |
| 账本写回 | `commit(queue, verdict) -> queue` | 落盘含证据字段；证伪/修正时写 correction_record |
| 断言 | `assert_ledger(queue) -> (ok, violations)` | 无 PENDING；REACHABLE 无 static_only（可申报性门禁）；实证类声称全部 empirically_confirmed |

### D-COMP-05 harness_runner.py（R5 实证抽验）

| 接口 | 签名 | 说明 |
|---|---|---|
| 触发判定 | `needs_harness(candidate) -> bool` | verdict 声称 crash/OOM/无界/XSS/协议 DoS 且 evidence_grade < empirically_confirmed → 触发 |
| 模板注册 | `register(name, spec)` | harness 模板：{语言, 依赖检查, 执行脚本, 结果解析器} |
| 执行 | `run(harness, target) -> EmpiricalResult` | 启动目标、发送攻击载荷、时序采样（RSS/存活）、结果采集 |
| 写回 | `apply_result(candidate, result) -> verdict` | confirmed → evidence_grade=empirically_confirmed；refuted → 回溯标记 + correction_record |

### D-COMP-06 batch_verify.py 改造（v2.1 状态机迁移）

改造项（来自 lessons C1-C12 全部工程项）：collect 字面 id 契约、merge 语义、assert/collect 校验统一、depth 门禁死代码豁免、--batch-size、--group-by-file、簇级 verdict_map、R4 collect/assert/report stage、JSON 容错加载、字段填充。

### D-COMP-07 r05_diff_archaeology.py 改造

--cross-tags（修复 commit 在 tag 矩阵）、NO_GIT 状态、HEAD 变体复核模式、默认落盘 -o、grep 词表分级。

### D-COMP-08 ast_scanner.py 改造

路径过滤语言映射表（spec/tst/*_tests.rs/.Tests/*.spec.ts）、source_pattern/language 字段填充、入队 merge 语义、噪音自检（规则误报率抽样 >80% 自动降权提示）。

---

## 10. 阶段输入输出契约与状态机（D-STAGE）

| 阶段 | 输入 | 产出 | 完成判据（门禁） |
|---|---|---|---|
| R0 | 项目路径、签名库、harness 执行器 | execution_mode.json、自检报告 | 签名库冒烟 100%；harness 执行器可用 |
| R0.5 | git 历史 | r05_diff_archaeology.json | 修复核验矩阵完整（--cross-tags 时） |
| R1 | 项目源码+构建清单 | input_surface.json | 每 surface 有 entry_points 证据；主 Agent 复核通过 |
| R2 | input_surface.json + 签名库 | hypotheses.json | 假设有语义家族+检查清单；无孤儿假设（无 surface 归属） |
| R3 | hypotheses → 候选队列 | verify_queue（证据分级） | 无 PENDING；REACHABLE 无 static_only；前提维度齐备 |
| R4 | 队列 + 项目背景 | r4_findings（H1-H7） | H1-H7 全部 VERIFIED |
| R5 | 触发判定 | empirical 结果 | 实证类声称 100% 已实证 |
| 报告 | 全阶段产物 | 报告 + 指标 | 过程问责指标齐备 |

**队列状态机**（v2.1 语义保留）：`PENDING → VERIFIED`，verdict 附 evidence_grade；证伪回溯路径：`empirically_confirmed → (refuted) → correction_record + 候选降级 + 任务书反例注入`。

---

## 11. 需求导出指引

- **系统需求编号**：`REQ-V3-xxx`，覆盖 §1-§10 的系统级行为；每条附"来源"列（设计章节/组件 ID）
- **软件需求编号**：`SWR-V3-xxx`，覆盖 §9 组件的实现级行为；每条附"满足"列（REQ-V3 追溯）
- **状态字段**：`status ∈ {未开发, 开发中, 已完成}`，另有 `note` 列（如"继承 v2.1 已实现"）
- **追踪矩阵**：`REQUIREMENTS_TRACKING.md` 汇总全部编号与状态，开发过程中实时更新
- **验收**：Phase 完成判据 = 该 Phase 覆盖的 REQ/SWR 全部转"已完成"且通过对应测试
