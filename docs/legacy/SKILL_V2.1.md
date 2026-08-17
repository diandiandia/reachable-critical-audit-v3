---
name: reachable-critical-audit
description: 专门针对项目进行严重漏洞（RCE, SQLi, SSRF, Bypasses, UAF, OOB, 未控内存分配）的可达性分析审计。六阶段漏斗模型（R0 工具自检含锚点召回 + R0.5 安全修复差异考古 + R1 静态规则 + R1.5 框架感知扩展 + R3 双向回溯 + R4 业务逻辑深钻），双平台兼容（Antigravity define_subagent / opencode task / agy CLI 可选），规则库源自 CodeQL 官方模型清洗 + 项目 wrapper 自识别 + 危险谓词 LOGIC_PATTERN。忽略代码规范、弱随机数等低风险噪音。
---

# Reachable Critical Audit Skill v2.1 (可达性严重漏洞审计)

> [!IMPORTANT]
> **本 Skill v2 旨在替代 pre-v2 在两次真实审计（tirreno / Android Bluetooth）中暴露的盲区**：规则库只覆盖原生 sink 漏掉 `osi_*alloc` / `STREAM_TO_*` / Android `ContentResolver.query`；要求"本仓库闭环"漏掉跨进程信任边界破坏；`verify_queue.json` 从未落盘；ast_scanner.py 形同虚设；Coverage Rate 公式导致造假。v2 通过五阶段漏斗 + 平台兼容层 + CodeQL 双源 + 跨边界终结四项核心改动系统修复。
>
> **v2.1 由两次新实测驱动（phpMyAdmin 4.8.5 漏 CVE-2018-12613 LFI、fastjson2 2.0.62 漏 checkAutoType hash 白名单绕过）追加四项**：① **锚点召回自检**（`anchor_registry.json`，<100% 阻止审计启动）；② **R0.5 安全修复差异考古**（git 历史中安全修复 commit 的 diff 即漏洞特征源）；③ **LOGIC_PATTERN 危险谓词规则**（第三类规则类型，表达"授权/白名单被弱化"语义缺陷）；④ **提取器完整性修复**（`semgrep_extractor.py` 支持 taint-mode 规则 + 增量合并 + `--reconcile` 对账）。Agent 必须严格遵守本规范，忽略代码规范与合规性噪音，只聚焦"外部可控输入是否能真实到达高危 Sink 点（含跨进程边界）"的真实严重漏洞。

---

## 🎯 核心使命

- **无 Key 自治**：完全使用 Agent 自身的 LLM 能力与本地工具，无需任何第三方大模型 API Key。
- **双平台兼容**：保留 Antigravity `define_subagent`/`invoke_subagent` + `agy` CLI，自动降级到 opencode `task` 工具。
- **CodeQL 双源规则库**：规则源自 CodeQL 官方模型清洗（L0，含 `.qll` / `.model.yml` / Swift `SinkModelCsv`）+ 项目 wrapper 自识别（L1）+ 非预设语言生成（L2）。
- **跨边界 sink 终结**：调用链到达 IPC/DSO/Provider 边界即判定 sink 达成，不要求追溯外部实现。
- **量化指标可问责**：区分 L0/L1/L2 候选来源，Sink Discovery Rate 量化规则库盲区。

---

## 🔌 平台兼容层 (Platform Adapter)

Skill 必须在 R0 阶段探测平台能力，选择执行模式并写入 `.audit_results/execution_mode.json`。

| 模式 | 平台 | 编排原语 | Subagent 类型 | 探测条件 |
|---|---|---|---|---|
| **A** | Antigravity | `define_subagent` + `invoke_subagent` | `vulnerability-verifier` / `business-logic-verifier` / `framework-sink-extractor` | 工具列表含 `define_subagent` 或 `REACHABLE_AUDIT_MODE=native` |
| **A'** | opencode 等 | `task(subagent_type="general"/"explore")` | 通用子智能体（task 的 description + prompt 承载角色） | 工具列表含 `task` 或 `OPENCODE=1`；或 Mode A 不可用 |
| **B** | **Claude Code / Antigravity CLI / Codex CLI** | `run_workflow.js` 多平台自适应 + `claude -p` / `agy --prompt` / `codex --full-auto` spawn | 独立 CLI 子进程会话（物理隔离 context，解决注意力下降） | `node run_workflow.js --check-availability` 返回检测到的 CLI；或环境变量 `AGENT_CLI=claude\|agy\|codex` |

**Mode B 多 CLI 自适应**：`run_workflow.js` 自动按 `claude → agy → codex` 优先级探测环境中可用的 CLI 工具，也可通过 `AGENT_CLI` 环境变量强制指定。每个候选点 spawn 独立子进程执行（物理隔离 LLM context），彻底解决长序列审计中的注意力下降问题。支持环境变量 `BATCH_SIZE`（并发数，默认 4）和 `TIMEOUT_MS`（单次超时，默认 300000ms）。

**强制约束**：无论何种模式，R0 工具自检（含锚点召回）、R0.5 差异考古、`verify_queue.json` 落盘、R1.5 强制触发条件、R4 6 类固化假说、REQ-10 量化公式必须一致执行。

> 在 opencode 等 fallback 平台上，SKILL.md 后文中所有出现的 `define_subagent`/`invoke_subagent` 调用描述在 Mode A' 下等价于 `task(subagent_type="general", description="<role>: <id>", prompt=<任务书>)`；在 Mode B 下由 `run_workflow.js` 自动编排。详见附录 A 任务书模板。

> ⚠️ **AGENT 强制自查**：执行本 skill 的 Agent 必须在 R0 阶段确认已完整阅读以下各阶段规则。**禁止跳过 R0 工具自检**、**禁止用手工 grep 替代 R1 ast_scanner.py 全量扫描**、**禁止不创建 verify_queue.json 直接分析**、**禁止在 R4 启动前不执行 R3 assertion**。pre-v2 两次审计（tirreno、Android Bluetooth）的根因就是 Agent 跳过了这些步骤——用"捡重要的看"替代了系统性验证，导致候选不全、降噪率虚高、关键 sink 漏审。**本 v2 的 R0/R1/R1.5/R3/R4 五阶段漏斗设计是强制串行的，不得重排或跳过任何阶段。**


---

## 🛠️ R0：依赖 Bootstrap + 工具自检 + 平台探测 + 目录守卫

Skill 启动后**第一步必须**执行以下四件事，任何一步失败即 fail-fast 终止审计：

1. **依赖 bootstrap**：优先使用 **skill 安装目录** 下的 `.venv/bin/python3`。若该 `.venv` 不存在，先运行 `python3 -m venv <skill_dir>/.venv`；若 `ast_scanner.py --self-check` 报告 `tree-sitter` 或 grammar 缺失，则在 skill-local `.venv` 中安装以下依赖后重试一次：
   ```bash
   <skill_dir>/.venv/bin/python3 -m pip install \
     tree-sitter tree-sitter-java tree-sitter-cpp tree-sitter-python \
     tree-sitter-javascript tree-sitter-go tree-sitter-rust tree-sitter-c-sharp \
     tree-sitter-php tree-sitter-ruby tree-sitter-swift tree-sitter-kotlin \
     tree-sitter-scala
   ```
   不允许在被审计项目根目录创建 `.venv`，不允许把依赖安装到系统 Python；遇到 PEP 668 / externally-managed-environment 时必须改用 skill-local `.venv`。Mode B 的 `run_workflow.js` 会优先使用 skill 安装目录下的 `.venv/bin/python3`；也可由 `REACHABLE_AUDIT_VENV` 覆盖 venv 目录，或由 `PYTHON_BIN` 覆盖解释器。
2. **AST 工具自检**：运行 `<skill_dir>/.venv/bin/python3 tools/ast_scanner.py --self-check`（或 `PYTHON_BIN` 指定的 Python），确认 `tree-sitter` + 有规则语言的对应 grammar 可用，并确认 AST pattern 覆盖率达到阈值。**锚点召回自检（REQ-24，v2.1）**：self-check 加载 `resources/anchor_registry.json`，对每语言 ground-truth CVE 锚点（如 PHP `include $_GET['x']` → CVE-2018-12613；Java `checkAutoType` hash 白名单 → fastjson2）做命中测试，**AnchorRecall < 100% 该语言判 FAIL**（输出 `anchor_recall_pct`），阻止审计启动。失败绝不允许降级为 LLM 脑补 AST。
3. **平台模式探测**：按"平台兼容层"表格顺序探测，结果写入 `.audit_results/execution_mode.json`：
   ```json
   {"mode": "A_NATIVE_ANTIGRAVITY|A_NATIVE_OPENCODE|B_ANTIGRAVITY_CLI",
    "reason": "...", "detected_at": "ISO8601"}
   ```
4. **目录守卫（REQ-12 前置守卫）**：`mkdir -p .audit_results/`，所有后续产物（`verify_queue.json` / `extended_sinks.json` / `extended_profile.json` / `execution_mode.json` / `reachable_vulnerabilities_report.{md,json}` / `architecture_view.json`）路径必须以 `.audit_results/` 为前缀。任何对项目源码根目录的直接报告写入视为流程违规，立即终止。同时初始化空的 `verify_queue.json`。**R3 阶段开始时，如果 `.audit_results/verify_queue.json` 不存在或其 `candidates` 为空数组，禁止进入 R3，须回退到 R1 重新扫描。**
   ```json
   {"schema_version": "2.0", "candidates": []}
   ```

---

## 🔬 R0.5：安全修复差异考古（REQ-25，v2.1 新增）

**R0 通过后、R1 之前执行**。利用 git 历史中安全修复 commit 的 diff 作为漏洞特征源，定位规则库无法表达的**语义逻辑缺陷**（如 fastjson2 `checkAutoType` 只比 64 位滚动 hash 不完整校验类名、tengine 远端计数无上限循环）。

1. **运行考古工具**：`<skill_dir>/.venv/bin/python3 tools/r05_diff_archaeology.py <repo> [--tag <tag>]`。该工具对 `--grep`（默认 `security|autotype|rce|bypass|cve|deny|fix|safe|exploit|gadget|hardening|sanitize`）匹配的安全 commit 执行 `git diff parent..commit`，提取 `added_guards`（新增校验特征，如 `if (hasIllegalTypeNameChars(typeName))`）与 `removed_paths`（被删/弱化路径）。
2. **主 Agent 判定**：读取输出，对每个候选 commit，判断**目标审计版本**是否含该漏洞特征：
   - 含特征 → 输出为 `.audit_results/r05_diff_archaeology.json`，标注 `verdict: "疑似未修复"`，`origin=R05` 并入 R3 验证队列。
   - 不含（已修复/回退修复） → 标注 `verdict: "已修复"`，仅记录。
3. **无 git 历史**：跳过并记录 `skipped_reason`，不阻塞审计。
4. **设计动机**：fastjson2 实测——`checkAutoType` hash 白名单绕过（2.0.63 修复 commit `ec47e24c4`）无法被任何 sink/污点规则表达，只有 diff 修复 commit 才能确认漏洞特征。对 AutoType/RCE 这类"迭代修 N 轮"的库，本阶段产出价值高于静态规则阶段。

---

## 📊 R1：静态规则扫描（L0）

加载 `resources/security_profiles.json` 的 `rules.<lang>` 段（L0 规则）。

1. **基准规则对齐**：Agent 首先读取并解析 `resources/security_profiles.json`。`rules.<lang>` 段已由 CodeQL 模型清洗产出（`codeql_revision` 字段记录版本），覆盖 15 种预设语言（Python、C/C++、Java、JS/TS、C#、Go、Rust、PHP、Ruby、Swift、Kotlin、Scala、Shell、Perl、PowerShell）。Go 规则必须检查 `sinks.go_models[]`，Swift 规则必须检查 `sinks.swift_models[]`；这两类结构化模型来自 CodeQL MaD / Swift `SinkModelCsv`。**第三类规则类型 LOGIC_PATTERN（v2.1，REQ-26）**：匹配"授权/白名单被弱化"的语义缺陷（hash-only 白名单 + `loadClass`、远端计数无上限循环、前缀校验代替全名校验），不依赖污点链。
2. **混合双层扫描**：运行 `python3 tools/ast_scanner.py <workspace>`（队列**缺省落盘到 `<workspace>/.audit_results/verify_queue.json`**，与 `batch_verify.py` 的读取路径契约一致；如显式传第二参数，脚本会规范到其下的 `.audit_results/` 子目录，**绝不写入源码根目录**，满足 REQ-12）。脚本用 tree-sitter AST S-expression 或 Go/Swift 结构化模型上下文命中候选，同时保留正则粗筛作为召回兜底。Go/Swift 结构化规则不得用裸 `Exec` / `Query` / `init` / `write` regex 作为高置信初筛；正则命中但缺乏 AST/结构化上下文支撑的候选点降级为 `NEEDS_REVIEW`，不能直接计入 REACHABLE 候选。
3. **过滤低风险噪音**：不在 Top-N 规则内的 CWE 类别物理忽略。代码风格、命名规范、非安全场景弱随机数物理过滤。超 1000 字符行强制截断。
4. **测试/构建/工具代码丢弃**：路径含 `test/`/`tests/`/`mock/`/`tools/`/`build/`/`scripts/`/`vendor/`/`node_modules/`/`third_party/`/`libs/`/`.agents/`/`.codex/`/`.venv/`/`reachable-critical-audit/` 的候选直接丢弃，不入队列。该条件语言无关—对所有 15 种预设语言统一生效，避免审计 skill 自身或其依赖环境。
5. **优先级标记**：每个候选入队时根据 `cwe_id` 标记 `priority` 字段（语言无关）。P0（高严重：RCE/注入/内存破坏/反序列化）→ P1（中严重：跨边界/授权/路径穿越）→ P2（低严重：需上下文判定）。`batch_verify.py` 按优先级出队，确保高价值候选优先验证。
6. **入队**：每个命中候选写入 `verify_queue.json` 的 `candidates[]`，`origin` 字段标记 `L0`：
   ```json
   {"id": "CAND-001", "source_file": "...", "source_line": 123,
    "sink_type": "CWE-789", "source_pattern": "STREAM_TO_UINT16",
    "origin": "L0", "priority": 0, "status": "PENDING"}
   ```

---

## 🔍 R1.5：框架感知扩展（L1）— *新增阶段*

R1 完成后**必须无条件执行**。R1.5 与 R1 互补：R1 聚焦预设 L0 规则（CodeQL 清洗的函数签名），R1.5 通过框架感知 wrapper_detection 捕获项目自定义的封装 API、IPC 边界和跨进程入口。两者覆盖不同的攻击面，不可互相替代。即使 R1 在目标语言上命中率很高，框架感知扩展仍会发现 L0 规则未覆盖的项目特有 wrapper、自定义封装函数、内部 IPC 边界。该阶段不可跳过。

1. **加载 wrapper_detection**：从 `security_profiles.json` 的 `wrapper_detection.<lang>` 段加载项目 wrapper 识别模式。例如：
   - C++: `allocator_pattern` (osi_*/`*alloc*`) / `parser_macros` (STREAM_TO_*/`*_TO_STREAM`) / `lifecycle` (`*_delete`/`*::reset`) / `async_ownership` (`*::Unretained`)
   - Java: `sql_wrappers` (`*query*`/`raw*`) / `ipc_sinks` (`ContentResolver.*`/`Intent.*`) / `android_ipc_getter` (`getFilter*`/`getExtra*`)
2. **拉起 framework-sink-extractor 子智能体**：通过平台兼容层（Mode A/A'/B）拉起，任务书见附录 A.3。子智能体扫描全项目，找出名字匹配模式的、本项目自定义的函数/宏/方法。**各模式下的具体编排如下（工具已内置，禁止手工替代）**：
   - **Mode A'（`task` / Claude Code `Agent` 工具）**：
     ```
     1. python3 tools/batch_verify.py <workspace> --stage r15
        → 输出各主要语言的 framework-sink-extractor 任务书 (含 wrapper_detection 模式)
     2. 对每个 task 用 task/Agent 工具拉起子智能体，收集其 extended_sinks JSON
     3. 汇总写入一个文件 (如 .audit_results/_r15_raw.json)，然后:
        python3 tools/batch_verify.py <workspace> --stage r15-collect --sinks-file <该文件>
        → 以 origin=L1 并入 verify_queue.json (自动去重 file+line+wrapper)
     ```
   - **Mode B（`run_workflow.js`）**：阶段 1.5 自动执行（AST 扫描后、R3 验证前），逐语言 spawn 子进程、产出 `extended_sinks.json` 并以 `origin=L1` 并入队列，幂等（`extended_sinks.json` 存在则断点续传时不重复）。
   - **Mode A（Antigravity）**：`define_subagent` + `invoke_subagent` 拉起 `framework-sink-extractor`，产出同上。
3. **落盘并入队**：产出 `.audit_results/extended_sinks.json`，并入 `verify_queue.json` 的 `candidates[]`，`origin` 字段标记 `L1`，`priority` 默认 P1。
4. **L2 fallback（非预设语言）**：若项目包含 15 种预设之外的语言（如 Erlang），Agent 必须基于 `security_profiles.json` 的 `l2_fallback_rules` Top 10 高危规则生成该语言的漏洞映射，落盘 `.audit_results/extended_profile.json`，**经主 Agent 显式复核签名**（写入 `reviewed_by: "main-agent"`）后才并入候选队列，`origin` 标记 `L2`。Mode B 会在 R1.5 后自动读取该配置，对非预设源码扩展执行保守高危模式扫描并入队。

---

## 🔄 R3：双向数据流追踪与可达约束验证

`verify_queue.json` 中所有 `status=PENDING` 候选分批并发验证。每次 3~5 个子智能体（按平台兼容层选定的模式），单批完成立即落盘。

**按优先级出队**：`batch_verify.py --stage next` 按候选 `priority` 字段升序出队（P0 先验证），确保高严重性 CWE（RCE/注入/内存破坏）优先处理。优先级语言无关，由 `ast_scanner.py` 在入队时根据 `cwe_id` 自动标记。

**Mode A' (opencode `task` 工具) 分批验证——用 `batch_verify.py` 编排**（**前置**：进入本循环前必须已完成 R1.5 `--stage r15` + `--stage r15-collect`，确保 L1 候选已并入队列）：
```
循环:
  1. python3 tools/batch_verify.py <workspace> --stage next
     → 输出下一批 3~4 个候选的任务书（含 file/line/CWE/自定义 prompt）
     → 若返回 {"status":"ALL_DONE"} 则跳出循环
  2. 对每个 task 并发执行:
     task(subagent_type="general",
          description="vulnerability-verifier: CAND-xxx",
          prompt=<任务书中的 prompt 字段>)
  3. 收集所有 task 返回的 JSON verdict
  4. python3 tools/batch_verify.py <workspace> --stage collect \\
       --batch <n> --cand-<num>='{"verdict":"REACHABLE",...}' ...
     → 写入 verify_queue.json
     → 返回 {"status":"BATCH_COLLECTED"} 全部成功;
       {"status":"BATCH_COLLECTED_WITH_ERRORS","errors":[...]} 时: 合法结果已落盘,
       errors 中列出的候选保持 PENDING, 下一轮 next 会自动重新出队重试
       (绝不会因个别坏 verdict 丢弃整批已完成工作；缺少 `verdict` / `reachability_type` /
       `call_chain` / `call_chain_depth` / `evidence` 的结果保持 PENDING 重试)
  5. python3 tools/batch_verify.py <workspace> --stage status
     → 检查进度

直到 python3 tools/batch_verify.py <workspace> --stage assert 通过
(无 PENDING 残留，exit 0)
```

### 第一步：自底向上（Bottom-Up）追踪调用链（语言无关）
对每个候选 sink，使用 `grep` / `Grep` 工具反向查找调用者（Callers）：
1. **强制最小深度 3 层**：`Sink` ← `Caller_L1` ← `Caller_L2`。不足 3 层必须继续向上搜索。
2. 逐层逆向往上直到追溯到外部输入源（网络请求/文件读取/用户输入/IPC 调用/HCI 事件等）。
3. **多态穿透**：遇接口/抽象类/特征(trait)/虚函数必须搜索所有具体实现类继续回溯。

### 第二步：跨边界 sink 终结（REQ-19，语言无关）
调用链到达任何进程/模块/IPC 边界时，**边界即 sink**，不要求在当前仓库内闭环追溯外部实现：

| 边界类型 | 典型 API（语言示例） | 判定 |
|---|---|---|
| 跨进程 IPC | Java: `ContentResolver.query`/`Binder.transact`/`sendBroadcast` | 自由文本（selection/command/extra）含拼接 OR 参数化字段为 null → `REACHABLE_ACROSS_BOUNDARY`；强制 `?` 占位 + 绑定 → `UNREACHABLE` |
| 跨 DSO/FFI | C/C++: `dlopen`/dlsym 外部库；Rust: `extern "C"` FFI | 自由文本参数含外部输入 → `REACHABLE_ACROSS_BOUNDARY` |
| 跨 Provider authority | Java: URI authority 切换到第三方 ContentProvider | 同 ContentResolver 规则 |
| 跨进程调用携带自由文本 | Java: `Intent.putExtra`/`Bundle`；C/Python: `write`/`send` 到 IPC socket | 自由文本含外部输入 → `REACHABLE_ACROSS_BOUNDARY` |
| 子进程执行 | Python: `subprocess.Popen`/`os.system`；JS: `child_process.exec`；C: `system`/`popen` | 命令字符串含外部输入拼接 → `REACHABLE_ACROSS_BOUNDARY` |
| 动态代码执行 | Python: `eval`/`exec`；JS: `eval`/`Function`；Java: `MethodHandle.invoke` | 代码字符串含外部输入 → `REACHABLE_ACROSS_BOUNDARY` |

### 第三步：可达性约束验证
回溯过程中分析入参是否被截断或净化：
- **安全阻断**：强类型转换（int/UUID）、白名单、参数化绑定、`if (offset+N>p_pkt_end)` 显式边界检查 → `UNREACHABLE`，记录 `blocking_point` 入 `verify_queue.json`。
- **特权提升**：`setuid`/`seteuid`/`capng_*`/`prctl` 等特权切换后，若指令参数仍混入低特权用户可控变量 → `REACHABLE`；完全硬编码 → `UNREACHABLE`。守护进程（如蓝牙 UID 1002）等系统服务同样适用。
- **参数可控**：参数无阻拦溯源到外部 Source → `REACHABLE`，`reachability_type=DIRECT`。

### 状态机推进

每个候选 `status` 推进：`PENDING → VERIFIED`，并写入 `verdict` ∈ {`REACHABLE`, `UNREACHABLE`, `NEEDS_REVIEW`}，外加 `reachability_type` ∈ {`DIRECT`, `ACROSS_BOUNDARY`}、`call_chain`、`blocking_point`、`cwe`、`verified_at`。

子智能体返回模糊或拒绝时**强制** `NEEDS_REVIEW`，不允许默认判定或静默丢弃。

### R3 完成守卫
R4 启动前必须 Assert：`verify_queue.json` 中无 `PENDING` 节点，否则 `exit(2)` 强制中断。`NEEDS_REVIEW` 节点必须在最终报告显式列出。

---

## 🧠 R4：启发式项目感知与业务逻辑深钻

针对缺乏显式 sink 点的复杂业务逻辑隐患（状态机越权、并发竞争、身份校验绕过）。

### 1. 项目架构自动感知（REQ-14）
解析 README、Manifest、Proto、AIDL、系统设计等顶层文件，自动识别项目业务领域与核心功能点，写入 `.audit_results/architecture_view.json`。

### 2. 固化 6 类业务威胁假说（REQ-15，*禁止自由发散*）
必须推演并回应以下 6 类固定假说，每类必须给出三选一明确结论：`confirmed` / `reviewed_clean` / `not_applicable`，禁止默默跳过：

| 序号 | 假说 | CWE | 检测要点 |
|---|---|---|---|
| 1 | 远端控制 allocation size | CWE-789 | 远端字段乘 `sizeof` 进 `*alloc`/`new[]`/`osi_*alloc` 无上限 |
| 2 | 远端控制解引用长度/索引 | CWE-125/787 | 远端字段进数组下标/`memcpy` 长度/`STREAM_TO_*` 无边界检查 |
| 3 | 异步对象生命周期竞态（UAF） | CWE-416 | 异步回调/队列/alarm 持 `Unretained(this)`/raw ptr，对象先释放 |
| 4 | 跨进程信任边界破坏 | CWE-20+89/78 | 远端输入拼字符串进 ContentResolver.query/Binder/Intent 且参数化字段 null |
| 5 | Exported component 鉴权缺失 | CWE-862/926 | manifest `exported=true` 且无 permission，或动态启用窗口期被第三方触达 |
| 6 | 多租户/owner 比对缺失 | CWE-639/285 | 写/删/查资源方法体无 session vs owner 相等性比对 |

### 3. Subagent 专项并发深钻（REQ-16）
通过平台兼容层拉起 `business-logic-verifier` 子智能体（任务书见附录 A.2），并发深钻 H1-H6 六个固定假说。即使没有文件名锚点，也必须按全项目审查 6 类假说。结果落 `verify_queue.json` 的 `r4_findings` 段，`origin=R4`。R4 完成后也必须 Assert：H1-H6 全部存在且 `status=VERIFIED`。

---

## 📊 量化指标与结构化报告

分析结束后，Agent 必须输出可量化的度量数据，并严格在 `.audit_results/reachable_vulnerabilities_report.md` 及 `.audit_results/reachable_vulnerabilities_report.json` 体现（严禁直接写入源码根目录）：

### 量化公式（REQ-10，*修订*）

```
Rule Coverage Rate    = (R1 + R1.5 + L2 + R4) 已验证候选  /  (R1 + R1.5 + L2 + R4) 总候选
Reachability Rate     = REACHABLE                                  /  已验证候选
Noise Reduction Rate  = UNREACHABLE                                /  已验证候选
Sink Discovery Rate   = R1(L0) 命中                                /  (R1 + R1.5 + L2 + R4) 总候选
                                                            ↑ 越接近 1 说明 L0 规则库越完备
False Negative Risk   = L1 占比 + R4 REACHABLE 占比
                                                            ↑ 越高说明仅靠 L0 漏报越多,督促规则库补齐
Anchor Recall (v2.1)  = 锚点命中数 / anchor_registry.json 该语言锚点总数
                                                            ↑ 规则库对真实 CVE 攻击面的召回,<100% 禁止声称覆盖率有效
```

**强制约束**：
- 分母 = `verify_queue.json` 中所有候选数（L0+L1+L2+R4），含 `NEEDS_REVIEW`。
- 采样策略必须在报告中明示。
- `NEEDS_REVIEW` 节点必须在报告中显式列出，不允许静默丢弃。
- **v2.1**：报告 `quantified_metrics` 必须包含 `anchor_recall_pct`（全局 + 按语言）；`Anchor Recall < 100%` 时禁止报告 Coverage/Reachability 有效性结论。

### 报告必须包含的字段

```json
{
  "report_meta": {...},
  "quantified_metrics": {
    "total_candidates": N,
    "verified": N,
    "reachable": N,
    "unreachable": N,
    "needs_review": N,
    "rule_coverage_rate_pct": ...,
    "reachability_rate_pct": ...,
    "noise_reduction_rate_pct": ...,
    "sink_discovery_rate_pct": ...,
    "false_negative_risk_pct": ...,
    "anchor_recall_pct": ...,           // v2.1, REQ-24
    "anchor_recall_by_lang": {...},     // v2.1, 按语言
    "origin_breakdown": {"L0": N, "L1": N, "L2": N, "R4": N, "R05": N}
  },
  "reachable_vulnerabilities": [...],
  "needs_review": [...],
  "unreachable_verified": {...},
  "defense_in_depth_gaps": [...]
}
```

---

## 📋 附录 A：子智能体任务书模板（三模式共用）

### A.1 vulnerability-verifier 任务书（语言无关通用版本）

```
你是一个 vulnerability-verifier 子智能体。你必须通过逆向数据流追踪确定候选 sink 点是否外部可控。

任务上下文:
- 目标项目: <path>
- 候选 ID: <id>
- sink 类型: <CWE-xxx> <category>
- 上下文摘要: <5 行内的关键信息: sink file:line, sink 调用, 参数来源候选项>

任务:
1. **强制调用链回溯（最小深度 3 层）**:
   - 以 sink 为终点，用 grep/Grep 反向查找所有直接调用者（Caller_L1）
   - 对每个 Caller_L1，追踪其参数来源找到 Caller_L2
   - 继续向上直到追溯到外部输入源（网络请求/文件读取/用户输入/Binder IPC/蓝牙 HCI 事件等）
   - **输出 call_chain 必须包含至少 Sink ← Caller_L1 ← Caller_L2 三层，不足 3 层必须向上继续搜索**
   
2. **多态穿透**: 遇接口/抽象类/虚函数，必须搜索所有具体实现类继续回溯

3. **跨边界判定（语言无关）**:
   - 调用链到达进程边界/IPC/跨模块调用时，边界即 sink
   - 若边界 API 的自由文本参数来自外部输入拼接，判定 REACHABLE_ACROSS_BOUNDARY
   - 若强制参数化/白名单校验/类型安全约束，阻断 UNREACHABLE
   - 对 Java: ContentResolver.query/Binder.transact/Intent/sendBroadcast
   - 对 C/C++: 外部动态库调用/IPC write/sendmsg
   - 对 Python/JS: exec/eval/subprocess 调用

4. **阻断检测（语言无关）**:
   - 强类型转换（如 `int(value)`、`(uint16_t)` 掩码 `& 0xFF`）
   - 白名单校验、参数化绑定（`?` 占位符）、边界检查（`if (offset + len <= total)`）
   - 任何这些阻断点记录为 `blocking_point`，判定 UNREACHABLE
   - **关键**: 阻断必须覆盖所有攻击者可控制维度。如果参数有多个维度但只检查了部分，仍为 REACHABLE

5. **路径覆盖要求（语言无关）**:
   - 对每个 Sink 点，列出所有到达该点的调用路径
   - 对每条路径上的阻断/校验，验证其是否覆盖了攻击者可控的所有入参维度
   - 若存在多条路径，只要有一条路径无阻断 → 该点 REACHABLE
   - 对状态机（switch/match/state pattern）场景标注当前覆盖的状态

6. **若无法明确判定** → verdict=NEEDS_REVIEW（不允许默认判定或静默丢弃）

输出格式(强制 JSON, 不要其他文字):
{
  "id": "<id>",
  "verdict": "REACHABLE | UNREACHABLE | NEEDS_REVIEW",
  "reachability_type": "DIRECT | ACROSS_BOUNDARY",
  "call_chain": ["file:line:function", "file:line:function", "file:line:function", ...],
  "call_chain_depth": <int>,
  "blocking_point": "file:line / null",
  "path_count": <int>,
  "paths_analyzed": ["path1 description", ...],
  "evidence": "<一段说明，包含调用链和每层的数据流分析>",
  "cwe": ["CWE-xxx"]
}

**质量门禁**: 缺少必需 JSON 字段的输出保持 PENDING 并进入下一轮重试；`REACHABLE` / `UNREACHABLE` 但 `call_chain_depth < 3` 的输出会自动降级为 `NEEDS_REVIEW` 并显式列入报告。
```

### A.2 business-logic-verifier 任务书

```
你是一个 business-logic-verifier 子智能体。

任务上下文:
- 目标项目: <path>
- 假说 ID: <H-1~H-6>
- 假说类型: <CWE-789 / CWE-125-787 / CWE-416-UAF / 跨进程 / 导出无权 / 越权-多租户>
- 业务领域: <architecture_view.json 中的领域>
- 锚点: <入口 file:line 列表>

任务:
1. 对分配的假说类型, 在锚点代码中寻找匹配模式:
   - CWE-789: 远端字段 * sizeof 进 *alloc/new[]/osi_*alloc 无上限
   - CWE-125/787: 远端字段进数组下标/memcpy 长度/STREAM_TO_* 无边界检查
   - CWE-416 UAF: 异步回调/队列/alarm 持 Unretained(this)/raw ptr, 对象先释放
   - 跨进程: 远端输入拼字符串进 ContentResolver.query/Binder/Intent 且参数化字段 null
   - 导出无权: manifest exported=true 且无 permission 或动态启用窗口
   - 越权-多租户: 写/删/查资源方法体无 session vs owner 相等性比对
2. 不限于锚点, 可在全项目搜索该假说的同类模式
3. 每个坐实的漏洞给出完整调用链(file:line)
4. 若已审查无问题, 给出 reviewed_clean 与覆盖范围说明
5. 若该假说不适用本业务领域, 给出 not_applicable 与判断理由

输出格式(强制 JSON):
{
  "hypothesis_id": "<H-x>",
  "verdict": "confirmed | reviewed_clean | not_applicable",
  "findings": [
    {
      "title": "...",
      "cwe": ["CWE-xxx"],
      "severity": "Critical|High|Medium|Low",
      "call_chain": ["file:line", ...],
      "evidence": "...",
      "fix": "..."
    }
  ],
  "coverage_note": "<若 reviewed_clean, 说明审查范围; 若 not_applicable, 理由>"
}
```

### A.3 framework-sink-extractor 任务书

```
你是一个 framework-sink-extractor 子智能体 (R1.5 阶段)。

任务上下文:
- 目标项目: <path>
- wrapper_detection 配置: <security_profiles.json 中 wrapper_detection.<lang> 段>

任务:
1. 按 wrapper_detection.<lang>.allocator_pattern / parser_macros / lifecycle / async_ownership
   / sql_wrappers / ipc_sinks / android_ipc_getter 等模式名, 用 grep/Grep 扫描全项目
2. 找出名字匹配模式的、本项目自定义(非第三方库)的函数/宏/方法
3. 对每个 wrapper, 判断:
   - 是否 wrapping 了 sink 性质(分配内存/执行命令/拼接 SQL/跨进程调用/释放对象)
   - 远端数据是否能流入该 wrapper
4. 产出 extended_sinks.json, 每条含 file:line + wrapper 名 + 推断的 sink 性质 + CWE 类别

输出格式(强制 JSON):
{
  "extended_sinks": [
    {
      "file": "...", "line": 123,
      "wrapper_name": "osi_calloc",
      "matched_pattern": "allocator_pattern:osi_*",
      "inferred_sink_type": "CWE-789 UncontrolledMemoryAllocation",
      "remote_data_reachable": true|unknown,
      "evidence": "..."
    }
  ]
}
```

---

## 📋 附录 B：执行流程速查

```
R0  依赖 bootstrap + 工具自检(含锚点召回) + 平台探测 + mkdir .audit_results/ + 初始化 verify_queue.json
     │  失败即 fail-fast; 锚点召回 <100% 阻止启动 (v2.1)
     ↓
R0.5  安全修复差异考古 (v2.1, REQ-25):
     │  r05_diff_archaeology.py <repo> [--tag]
     │  git log --grep security + diff parent..commit → added_guards/removed_paths
     │  主 Agent 判定目标版本是否含漏洞特征 → 疑似未修复 origin=R05 入 R3
     │  无 git 历史则跳过并记录
     ↓
R1  静态规则扫描 (L0):
     │  ast_scanner.py tree-sitter AST 高置信命中 + regex 召回兜底
     │  第三类规则 LOGIC_PATTERN (危险谓词) 同步匹配 (v2.1)
     │  测试/构建/第三方路径候选丢弃 (语言无关)
     │  按 CWE 标记 priority 字段 (P0/P1/P2)
     │  候选入队 origin=L0, priority=0~2, status=PENDING
     │  非预设语言 → L2 fallback (主 Agent 复核)
     ↓
R1.5  框架感知扩展 (L1) — 无条件执行, R1 完成后进行:
     │  Mode A':  batch_verify.py --stage r15 → 子智能体扫 wrapper → --stage r15-collect 并入
     │  Mode B:   run_workflow.js 阶段1.5 自动 spawn (幂等)
     │  wrapper_detection 扫描项目自有 wrapper, 产出 extended_sinks.json
     │  候选入队 origin=L1, priority=1, status=PENDING
     ↓
R3  双向回溯验证 (按优先级出队):
     │  分批并发 3~5 子智能体 (平台兼容层选定模式)
     │  batch_verify.py 按 priority ASC 出队 (P0 先验证)
     │  每批立即落盘 verify_queue.json
     │  状态机: PENDING → VERIFIED → {REACHABLE|UNREACHABLE|NEEDS_REVIEW}
     │         + reachability_type ∈ {DIRECT, ACROSS_BOUNDARY}
     │  跨边界按 REQ-19 终结判定
     │  强制 call_chain_depth ≥ 3
     │  Assert: 无 PENDING 才能进 R4
     ↓
R4  业务逻辑深钻:
     │  解析业务领域 → architecture_view.json
     │  6 类固化假说 (H-1~H-6), 每类三选一结论
     │  business-logic-verifier 子智能体并发深钻
     │  r4_findings 入队 origin=R4
     │  Assert: 所有 R4 候选已 VERIFIED
     ↓
最终 量化报告 (L0/L1/L2 区分):
     │  reachable_vulnerabilities_report.{md,json}
     │  MUST 包含: Sink Discovery Rate + False Negative Risk + AnchorRecall (v2.1)
     │  MUST 列出 NEEDS_REVIEW (不允许静默丢弃)
```

---

## 📋 附录 C：与 pre-v2 阶段命名映射

| pre-v2 | v2 | 变化 |
|---|---|---|
| 阶段 1 (规则固化 + Fallback) | R0 + R0.5 + R1 + R1.5 | R0 强制工具自检 + 锚点召回; R0.5 差异考古 (v2.1); R1.5 框架扩展是新增阶段 |
| 阶段 2 (双向回溯) | R3 | 增加跨边界 sink 终结 + verify_queue 状态机 |
| 阶段 3 (量化报告) | 最终报告 | 公式重做,区分 L0/L1/L2,新增 Sink Discovery Rate + AnchorRecall (v2.1) |
| 阶段 4 (业务逻辑深钻) | R4 | 假说从自由 3~5 个改为固化 6 类必选 |
| — | 平台兼容层 | 新增,双平台适配 |

**v2.1 变更摘要**：R0.5 阶段新增；锚点召回自检；LOGIC_PATTERN 第三类规则；`semgrep_extractor.py` taint-mode + 增量合并 + `--reconcile`；PHP CWE-98 LFI 规则（锚点 CVE-2018-12613）。详见 `REQUIREMENTS.md`（REQ-24~28）与 `SYSTEM_DESIGN.md`（§4.5/§4.6）。
