# Reachable Critical Audit Skill — Swift/Go 审计暴露的缺陷与改进建议

> **文档性质**：基于两次真实审计（container: Swift 容器运行时、gvisor: Go 用户态内核）对
> `reachable-critical-audit` skill 的回顾性缺陷分析。本文档用于驱动 skill v3 设计，不作为
> 具体项目审计报告。
>
> **审计日期**：2026-08-12
> **关联审计**：
> - `/home/zjamg/container`（Apple macOS 容器运行时，Swift，8 发现）
> - `/home/zjamg/gvisor`（Google gVisor 沙箱，Go，4 发现）
> - 对照组（有效基线）：`/home/zjamg/xquic`（C QUIC 库）、`/home/zjamg/tengine`（C nginx 分支）

---

## 0. 摘要

skill v2 的五阶段漏斗对 **C/C++ 系统库** 有效（xquic/tengine 的 L0 规则命中率高、REACHABLE
转化率合理），但在 **Go/Swift 现代语言项目** 上暴露了 10 类系统性缺陷。核心根因：

1. 规则库是 **C/C++ 规则的伪通用移植**，未按语言语义适配
2. `--self-check` 的覆盖率指标度量"字符串存在性"而非"模式有效性"
3. 无 CWE 领域适用性机制、无候选量预算、无项目成熟度评估
4. L2 fallback 触发标准模糊，执行流程与"主 Agent 复核"机制自相矛盾
5. 量化指标在规则盲区时失真，无规则库有效性独立指标

---

## 1. 规则库语言覆盖缺陷（L0 盲区）

### 1.1 Swift 规则库形同虚设（仅 1 条规则）

**现象（container）**：
- `resources/security_profiles.json` 中 `swift` 段仅 1 条规则（CWE-89 SqlInjection），sink 为
  `sqlite3_exec`/`sqlite3_prepare_v2`，对容器运行时领域完全无关
- L0 扫描 1070 候选**全部来自 `.venv` 的 Python**；321 个 Swift 源文件零命中
- 审计被迫完全依赖 L2 fallback + 手工测绘（3 个 explore 代理）

**根因**：`R1` 声称覆盖 15 种预设语言，但 Swift 的"覆盖"是名义上的。规则数量与语言真实
攻击面严重脱节，且无"每条语言规则数/覆盖率"的最低门槛检查。

**证据**：
```
self-check 报告: {"swift": True, "ast_patterns_coverage_pct": 100.0}
实际: swift rules = [{"cwe_id": "CWE-89", "category": "SqlInjection"}]  (仅此 1 条)
```

### 1.2 Go 规则是 C/C++ 模式的伪通用移植

**现象（gvisor）**：
- CWE-113（header injection）regex 命中 `.Add(` → 误报 `atomicbitops.Add`/`time.Add`（974 条）
- CWE-89（SQLi）regex 命中 `.Exec(` → 误报 `bpf.Exec`/`sbA.Exec`（48 条）
- CWE-643（XPath）regex 命中 `MustCompile` → 误报正常正则编译（44 条）
- CWE-352（CSRF）regex `post|put|delete` → Go 无 web 场景（2498 条）

**根因**：Go 是**方法调用**语言，`\bsend\b`/`\bAdd\b`/`\bExec\b` 匹配任意方法名/标识符；
C 语言中这些词几乎只在裸函数/系统调用出现。**同一 regex 在不同语言误报率差 1-2 个数量级**，
skill 无"语言适用性"或"标识符上下文"约束（如方法名、包名、字段名的排除）。

---

## 2. AST pattern 与语法树错配

### 2.1 Swift AST pattern 节点名不匹配

**现象（container）**：Swift 规则 AST 为 `(call_expression (simple_identifier) @fn)`，但
Swift tree-sitter 的调用表达式节点是 `call_expression` + `call_suffix`/`decl_reference`，
**不存在 `simple_identifier`**。结果即使有规则，AST 校验也永远不命中；唯一 SQL 规则退化为
纯 regex，而 regex 也不匹配 Swift 源码。

**根因**：`--self-check` 只验证"grammar 可加载"+"每条规则有 AST 字符串"，**从不验证 AST
pattern 是否真的匹配该语言真实语法树**。`ast_patterns_coverage_pct: 100%` 是虚假的确定性
保证——度量字符串存在性，非模式有效性。

**建议修复**：self-check 应对每种语言的每条 AST pattern 做**冒烟匹配测试**（用该语言若干
典型 sink 片段编译为语法树后跑 pattern），报告"AST pattern 真实命中率"，不达标则降级该
规则为 NEEDS_REVIEW 或标记规则库缺口。

---

## 3. CWE 适用性未按语言/项目类型区分

**现象**：
- gvisor（Go 网络栈/用户态内核）被打上 2498 条 CWE-352（CSRF）、44 条 CWE-643（XPath），
  这些 CWE 类别在项目领域**结构性不适用**
- container（Swift 容器运行时）被唯一规则 CWE-89（SQLi）——同样结构性无关

**根因**：`security_profiles.json` 无"按项目类型/领域过滤 CWE"机制。R1 的"过滤低风险噪音"
依赖 Agent 事后人工判断，非规则库前置的适用性声明。

**建议修复**：规则库为每个语言标注**适用 CWE 领域**（网络栈 / Web 服务 / 桌面 / 嵌入式 /
容器运行时 / 数据库），扫描时按项目域（由 README/Manifest 识别）过滤，在入队前排除。

---

## 4. 噪音量与验证成本失衡（可扩展性问题）

### 4.1 候选量远超验证能力

**现象（gvisor）**：15157 候选（P0=7693）。按 `batch_verify.py` 每批 4 个、每候选一个
子智能体验证的模型，需 **3800+ 批 / ~4000 次子智能体调用**，单次会话不可能完成。

**实际应对**：偏离 skill 设计——用 explore 子智能体按攻击面聚类做启发式测绘，手工验证
少量高价值点；1558 个剩余高价值候选只能批量标注 NEEDS_REVIEW。

**根因**：
- `batch_verify.py` 无聚类/优先级分组，`--stage next` 按 priority 逐条出队，无法按
  文件/模块/攻击面打包验证
- R3 的"3~5 子智能体/批"模型在候选量 >1000 时失效
- 无"候选量-验证资源"预算机制（如抽样验证 + 统计推断）

### 4.2 候选去重与噪音比缺失

**现象**：gvisor CWE-119 563 条大量为同一 unsafe 模式（`unsafe.Pointer(&x)` 转换）在不同
调用点的重复命中；container 攻击面依赖探索测绘而非候选队列。

**建议修复**：
- `ast_scanner.py` 增加"模式归一化去重"（同一函数/同一模式合并为 1 个候选，记录 count）
- 增加 **SNR（Sink Noise Ratio = 候选总数 / 确认 REACHABLE+NEEDS_REVIEW 数）** 作为规则库
  质量指标，入队时即估算

---

## 5. 成熟安全项目与规则扫描不匹配

### 5.1 对严格审计过的项目，泛化规则几乎全误报

**现象（gvisor）**：gvisor 有 CVE 流程、OSS-Fuzz、sentry 内存面逐候选核对后确认防御严密
（所有 guest 数据→切片/索引均有 bounds check）。563 条 CWE-119 候选（unsafe 指针）绝大多数
是 gvisor 规范合法用法（`unsafe.Pointer` 系统调用封装）。

**根因**：skill 假设"规则命中 = 真实候选需验证"，但对成熟安全项目，命中≈噪音。

**建议修复**：扫描前做**项目成熟度评估**（是否 CVE 流程 / 主流安全投入 / 是否安全关键项目），
据此决定投入粒度：成熟项目直接威胁模型驱动深钻，规则扫描仅作广度兜底。

---

## 6. L2 fallback 规范不清

### 6.1 触发条件与流程模糊

**现象（container）**：Swift 是预设语言但规则不足——L2 fallback 定义为"非预设语言"，导致
规则不足时无明确规范路径。实际执行：手动触发 explore 代理测绘 + 手工 grep 建候选 + 自建
extended_profile（且未严格走"主 Agent 显式复核签名"落盘流程）。

**根因**：
- L2 触发标准缺失："预设语言规则数 < N 或命中率 < 阈值"应自动触发
- L2 流程要求 `extended_profile.json` 经主 Agent 签名，但执行 Agent 无法自我"显式复核签名"，
  该机制未区分"主 Agent"与"执行 Agent"是否为同一实例
- 无"规则不足时的攻击面测绘模板"（explore 代理分工、sink 清单）

---

## 7. unsafe/FFI 代码处理缺失

**现象**：gvisor 563 条 CWE-119 全是 `unsafe.Pointer`/`syscall.RawSyscall` 的 C 互操作；
container 有大量 Swift 的 C 边界。规则把"出现 unsafe 指针"当候选，但无法区分规范封装 vs
真实越界。

**根因**：无"unsafe 代码安全审查规则"。

**建议修复**：针对语言定义**精确模式**而非泛化 CWE-119：
- Go：`unsafe.Pointer` → `uintptr` 保留、`Syscall6` 长度参数、切片头重建后无界索引
- Swift：`withUnsafeBytes`/`UnsafeMutablePointer` C 边界、`Data` 生命周期
- 这些模式需经安全专家维护，非从 C 规则移植

---

## 8. 量化指标失真

### 8.1 指标在规则盲区时无意义

**现象**：
- container：`rule_coverage_rate_pct: 0`、`sink_discovery_rate_pct: 0`、`false_negative_risk_pct: 100%`
  ——但报告仍照填，指标退化为空转
- gvisor：`sink_discovery_rate: 99.5%` 看似高，实际 99% 候选是误报

**根因**：REQ-10 公式假设"候选来自规则库"，规则盲区时公式无意义；无规则库有效性独立指标。

**建议修复**：
- 增加 **L0→REACHABLE 转化率**（L0 候选中被确认 REACHABLE 的比例），量化规则库精确度
- 增加 **SNR（候选/真实 sink）** 作为核心质量指标
- 报告强制标注**规则库语言覆盖**（如 "swift: 1 rule, 0 effective"），而非隐藏在注释

---

## 9. 安全边界项目 vs 通用漏洞定位

### 9.1 关键风险被规则库结构性错过

**现象**：
- container 最重要发现（XPC 鉴权仅 EUID、copyOut 任意 host 路径、rootFsOverride）**完全不在**
  任何 CWE 规则中——它们是**架构/信任边界**问题，非代码级 sink
- gvisor 最有价值发现（cgroup 路径穿越）来自对 `filepath.Join` 语义的独立 Go 测试，而非
  规则命中

**根因**：skill 聚焦"外部可控输入→高危 sink"，但安全边界项目（沙箱、容器运行时、权限代理）
的致命漏洞常在信任边界/鉴权/路径语义，不在经典 sink。

**建议修复**：R4 的 6 类假说偏"业务逻辑"，应增加**信任边界/鉴权模型专项假说**（如
"同 UID/同进程组 IPC 是否可触发宿主高危操作"、"路径语义（`..` 上溯/symlink）是否越界"）。

---

## 10. 构建验证可行性假设

### 10.1 跨平台可验证性未预检

**现象（container）**：macOS 专用项目（Virtualization.framework）在 Linux 环境**无法编译
运行**，R0/R3 的"运行时验证"路径直接失效，全部退化为源码级确认。

**根因**：无"项目可构建性/目标平台"预检。

**建议修复**：R0 增加平台/构建可行性探测；对不可构建项目明确"验证降级策略"（源码确证 +
最小环境隔离测试），而非默认假设可构建。

---

## 11. 有效基线对照

| 维度 | C 项目（xquic/tengine） | Go/Swift 项目（gvisor/container） |
|---|---|---|
| L0 规则命中率 | 高（regex/AST 匹配 C 语法） | 低（方法名误报 / 无规则） |
| 候选噪音 | 中（CWE-476/908 误报可控） | 极高（方法名/unsafe 泛化） |
| 真实漏洞定位 | 经典 sink（memcpy/alloc/exec） | 信任边界/路径语义/鉴权 |
| 运行时验证 | 可构建（C 交叉编译容易） | 受平台限制（macOS 不可构建） |
| 可扩展性 | 候选量数百，可全验证 | 候选量数千，需聚类/抽样 |

**结论**：skill v2 的漏斗设计以 C/C++ 为目标优化；对 Go/Swift 需做规则库、指标、流程三层
适配才能有效。

---

## 12. 改进优先级总表

| # | 缺陷 | 严重度 | 优先级 |
|---|---|---|---|
| 1 | 规则库语言适配（Swift 仅 1 条、Go 伪通用） | 规则库盲区 | **P0** |
| 2 | AST pattern 有效性校验（self-check 假覆盖率） | 规则库盲区 | **P0** |
| 3 | CWE 领域过滤（项目类型） | 噪音控制 | **P0** |
| 4 | 候选量预算机制（聚类/抽样/SNR） | 可扩展性 | **P1** |
| 5 | 项目成熟度评估（成熟项目直接深钻） | 流程 | **P1** |
| 6 | L2 触发标准 + 攻击面测绘模板 | 流程 | **P1** |
| 7 | unsafe/FFI 精确规则 | 规则库 | **P1** |
| 8 | 量化指标补强（SNR/L0→REACHABLE 转化率/语言覆盖） | 指标 | **P2** |
| 9 | 信任边界/鉴权专项假说 | 方法论 | **P2** |
| 10 | 跨平台验证降级策略 | 流程 | **P2** |

---

*文档结束。供 skill v3 设计参考。*
