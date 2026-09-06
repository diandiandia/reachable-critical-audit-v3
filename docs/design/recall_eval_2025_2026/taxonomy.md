# 2025-2026 三引擎 CVE 全景 — 发现包络判定分类法

用途：对 WebKit/Firefox/Chrome 2025-2026 medium/high/critical CVE 逐条判定
reachable-critical-audit 发现包络归属，产出 v3.24 优化需求输入。
本文件是分类子代理的**唯一判定契约**。

## 判定口径（先读）

- **判定单位**：CVE（点缺陷）。度量的是**族覆盖**（该缺陷的 defect_class ×
  surface 是否可由当前 skill 机制生成假设），不是点命中。
- **判定问题**：给定该 CVE 的组件与机制描述，skill 的输入面测绘（R1）→
  假设生成（R2/H1-H7）能否产出该方向的候选？能 → 包络内；不能 → 盲区。
- **证据需求**：description 含机制关键词即可判定；关键词缺失（rollup 类）
  → L2a，禁止猜测补全。
- **同一 CVE 多产品**：已按唯一 CVE 合并。

## 层级定义

### L0 包络内可达（skill 现状机制可生成该方向假设）

| 子类 | 定义 | 典型关键词 | skill 机制锚点 |
|---|---|---|---|
| L0a 数据面内存安全 | 解析/解码/反序列化类 OOB/UAF/整数溢出 | out-of-bounds, use-after-free, integer overflow + (parser/codec/ImageLib/MIME/XSLT/XML/IPC message/audio/video decode) | R1 data_input surface → CWE-125/787/190 假设 |
| L0b 生命周期内存安全 | DOM/GC/绑定层异步生命周期 UAF、竞态 | use-after-free + (DOM/GC/Bindings/IndexedDB/WebRTC/Worker) | H3 异步对象生命周期竞态假说；R2 CWE-416 假设 |
| L0c 图形/GPU 边界条件 | WebGL/Canvas/WebGPU/WebRender 越界与沙箱逃逸 | boundary conditions/overflow + (Canvas2D/WebGL/WebGPU/WebRender/shaders/textures) | R1 graphics surface → H4 跨进程信任边界 |
| L0d 信任边界逻辑 | 沙箱逃逸、site isolation、SOP 绕过、可达组件特权提升 | sandbox escape, same-origin policy bypass, site isolation, privilege escalation（组件为 web 可达面时） | H4/H7 信任边界专项假说 |
| L0e 资源耗尽 | 无界分配/放大/DoS | denial of service, unbounded, exhaustion | H1 远端控制分配大小假说 |

### L1 JIT 优化正确性层（v3.23 已声明边界 + 已加轴/假设族/差分通道）

| 子类 | 定义 | 典型关键词 |
|---|---|---|
| L1a 编译正确性 | JIT miscompilation/类型混淆/去优化错误/表示假设破坏 | JIT miscompilation, type confusion, incorrect compilation, partial return value, truncated instruction |
| L1b 引擎 GC 屏障 | GC/写屏障正确性缺陷 | GC barrier, write barrier, concurrent delazification（JIT 相关时） |

判定为 L1 时同时记 `v3.23_covered: true`（该缺陷落在 v3.23 新增机制的
族覆盖内）——L1 合计 = v3.23 修复需求份额的真实规模证据。

### L2 盲区（按需整理优化需求）

| 子类 | 定义 | 判据 |
|---|---|---|
| L2a 无信息汇总 | "Memory safety bugs fixed in X" 类 rollup，无逐 bug 机制描述 | desc 无机制关键词；不猜 |
| L2b UI 信任指示层 | 地址栏欺骗/tapjacking/全屏通知/下载面板欺骗等浏览器 UI 信任逻辑 | 组件为 UI chrome 且缺陷为欺骗类；skill 是代码可达性审计 skill，不狩猎 UI 信任指示 |
| L2c 移动端平台专属 | iOS WKWebView 集成层/Android 组件层 | 组件为 iOS/Android 专属且不映射到引擎内代码面 |
| L2d 内部组件特权提升 | Telemetry/Remote Settings/Netmonitor/Enterprise Policies/Updater/WebDriver 等组件 | 组件非 web 可达面；**个案判定**：若 desc 表明 web 内容可触发（如 Messaging System sandbox escape）→ 归 L0d 而非 L2d |
| L2e 第三方/闭源依赖 | VPN 客户端等闭源组件；vendor 开源库（libvpx 等）不归此类 | 闭源才归 L2e |
| L2f 安全 UX/人类学 | WebAuthn 蓝牙邻近钓鱼、passkey 欺骗、加密邮件 UI 误解 | 缺陷本质在 UX 协议层而非代码正确性 |

## 输出契约（分类子代理强制）

每引擎产出一个 JSON 数组（写入
`recall_eval_2025_2026/classify_<engine>.json`），逐条：

```json
{"cve":"CVE-xxxx-xxxx","sev":"critical|high|moderate|medium",
 "layer":"L0a|L0b|L0c|L0d|L0e|L1a|L1b|L2a|L2b|L2c|L2d|L2e|L2f",
 "rationale":"判定依据关键词（引用 desc 中 1-2 个机制词）"}
```

规则：
1. 每引擎条目数必须等于输入文件条目数（`len(in) == len(out)`，脚本断言）；
2. rationale 必须来自该条 desc 原文关键词，禁止编造；
3. 摇摆条目（L0d vs L2d 类）取保守值并标 `rationale` 末尾 `[ambig]`；
4. 完成后自跑 `python3 -c "import json; ..."` 校验 JSON 合法与计数相等。

## 聚合统计口径（主代理在分类完成后执行）

- 每引擎：L0a-e / L1a-b / L2a-f 计数 × severity 交叉表；
- **包络内召回上限** = (L0+L1) / (总数 − L2a)（rollup 不可判，从分母剔除）；
- **L1 占比** = v3.23 JIT 修复覆盖的真实需求份额（验证/证伪 v3.23 假设族规模）；
- **L2b/c/f 占比** = 「是否需要浏览器分支」问题的量化判据：若 L0+L1 占比
  高且 L2b/c/f 占比低，主线吸收成立；若 UI 层占比显著，评估是否为
  reachable-critical-audit 使命外（产品线扩展另议）；
- 输出：`recall_eval_2025_2026/recall_eval.md` 全景报告 + v3.24 优化需求清单
  + 回归集扩充建议（每 L1/L0 高价值盲区类取代表样本）。
