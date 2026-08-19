# Reachable Critical Audit Skill v3.3 — 系统架构设计文档

> **文档性质**：v3.3 架构设计（v3.2.2 + v3.2.3 修复批次的增量设计）。上游输入：
> ① Lua 5.5.1 审计 lessons（`lessons/SKILL_LESSONS_lua.md` 过程观察 1/9，2026-08-19）
> ② 用户偏见审查（5 大类 13 子项；主代理逐条用运行时资产取证裁决：2 项完全属实、
> 3 项方向属实但程度夸大、0 项虚构——裁决详情见本文件 §0）
> ③ v3.2.3 修复批次（7 项工具缺陷，已实现已提交 `4b8b512`，本文档记录为已闭环输入）
> v3.2.2 现行设计见 `SYSTEM_DESIGN_V3_2_2.md`（运行时权威）。
> **日期**：2026-08-19
> **设计目标**：消除审计能力的语言/形态/漏洞类型偏见——把 v3.2.2「去项目化」的成果
> 延伸到「去 Web 化/去单一形态化」：签名资产覆盖系统语言与并发/密码学族、
> 项目形态判定从构建文件启发式升级为信号加权、信任边界分类补宿主 API 边界。
> v3 骨架（输入面 → 假设 → 证据链 → 证伪 → 实证）不动。

---

## 0. 事实基础（v3.3 的问题证据，含偏见审查裁决）

### 0.1 偏见审查裁决表（主代理取证，2026-08-19）

| 审查项 | 裁决 | 取证结论 |
|---|---|---|
| L2 词族缺 C/C++/Go/Rust/Java | **属实** | signature_library.json 实测 L2 仅 powershell/shell/cs/python/typescript/kotlin；Lua 审计 C 项目 0 hits 即此结构性空白 |
| L3 主要关注 Web 特征 | 夸大 | 7 个 L3 中 Web 强相关仅 3 个（HEADER-INJ/AUTHZ-BOUND/BUFFER-ACCUM）；另 4 个（PATH-WHITELIST/PREALLOC-LEN/TRUNC-CAST/LOGIC-WEAKEN）通用 |
| lessons 深度绑定动态语言 | 部分属实 | 15 语言战役覆盖 C/Rust/Go，但 lessons 深度向动态语言倾斜 |
| CWE-770/789 占 40% 以上 | 数字不实 | 实测携带 770/789 的签名 4/13=31%（按标签 6/23=26%）；DoS/分配倾斜方向属实 |
| 缺 CWE-362/367/327/330 静态签名 | **属实** | 签名库 CWE 全集无此四类（R4 H3/H7 有假说层覆盖，无静态层） |
| 4+1 域对非网络项目难映射 | 部分属实 | Lua 审计反证 4 域可用；真实缺口 = trust_boundary 无宿主 API 边界类型 |
| project_kind 启发式硬划分 | **属实** | `_classify_project_kind` 仅返回 framework/infra/app 三值（文档声称四值含 library）；Cargo.toml 等 8 种构建文件硬映射 framework；Lua 实测 build_files=[] 未检出 Makefile |
| 黑名单 19 token 事后补救 | 机制属实 | 黑名单是回归 tripwire 而非唯一防线：配套 selfcheck 完整性 + 验收强制每版本一个新项目（过程控制）；维持设计 |
| 先例 22/清单 23 依赖历史战役 | 数字属实 | LLM 主引擎架构下先例库是裁决一致性辅助而非判定器（v3 设计本意）；异构架构一致性保障弱是真 |
| 实证门禁致保守倾向 | 机制成立 | 对冲：NEEDS_REVIEW 合法终态 + R3.5-N 复活攻击；Lua 审计反例（verifier 主动实证）；残余风险=难搭 harness 语言 |

### 0.2 新增证据（本设计编写时取证）

| 维度 | 实测数据 | 结论 |
|---|---|---|
| 追踪矩阵漂移 | tools/gen_tracking.py DOCS 字典与提取正则仅覆盖 v3/v3.1（`REQ-V3-\d{3}` 形态）；v3.2/3.2.1/3.2.2 段的 `REQ-V3.2.2-xxx` 从未进入 REQUIREMENTS_TRACKING.md | v3.2 起需求追踪工具失同步——契约工具自身成为漂移源 |
| maturity 信号 | `surface_mapper.py context` 输出 maturity="unknown"（Lua 实测）；SKILL.md §v3.1 的「mature framework → R4 并行」触发条件无机械信号支撑 | 文档承诺的触发条件在代码中无实现 |
| host_api 边界缺失 | trust_boundary.type 枚举 8 类（unauthenticated_remote/authenticated_remote/trusted_channel/local/environment/unknown + gate）；库组件的「宿主 C API 喂入不可信数据」无对应类型 | Lua CAND-002 的边界争议（ACROSS_BOUNDARY 被 R3.5 拦截）部分源于分类缺失 |

---

## 1. 六大问题域与 v3.3 对策

### P-A 签名库系统语言与漏洞类型覆盖缺口 → L2 +4 族、L3 +2 族

**现象**：L2 词族 6 语言无 C/Go/Rust/Java；L3 语义族无并发竞态（CWE-362/367）与
密码学弱化（CWE-327/330）族；既有 L3 的 grep hints 是 server-framework 形态
（bodyBuffer/writeFully/extend_from_slice），系统语言项目的 memory-unsafe 形态
（声明计数驱动无上限分配、窄化 cast、unsafe 块）无佐证词。

**v3.3 设计变更**：
1. **L2 词族 +4**：`c`（malloc/realloc 无上限分配家族、varint/长度字段驱动 alloc）、
   `go`（流式累积/无界 reader 消费）、`rust`（unsafe 块/FFI 指针逃逸/vec 无界增长）、
   `java`（流式无界读取/反序列化 sink）。每族 1-2 签名、lang 必填（VALID_LANGS 扩充）。
2. **L3 新增 SIG-STATE-RACE**（CWE-362/367）：检查与使用分离（check-then-act）、
   TOCTOU 形态、跨线程共享状态无同步；**SIG-CRYPTO-WEAK**（CWE-327/330）：
   非密码学随机种子、可预测时间戳种子、弱哈希替代校验。
3. **L3 既有族补系统形态 grep hints**：PREALLOC-LEN 补「声明计数→newvector 类」词
   （去项目化：`newvectorchecked/new_vector/calloc 前无预算`）；TRUNC-CAST 补 C 形态
   （`(u16)/(int)` 截断转储）；BUFFER-ACCUM 补流式无界读形态。

**为什么能解决**：签名库仍是提示器（LLM 主引擎不变），但佐证器在系统语言项目
不再结构性空转——C/Go/Rust/Java 项目的假设生成获得与 Web 项目同级的签名佐证。

### P-B 项目形态判定启发式缺陷 → 四值分类重构 + maturity 解耦

**现象**：`_classify_project_kind` 仅三值返回（framework/infra/app），与文档声明的
四值（framework/library/infra/app）不一致；8 种构建文件硬映射 framework——
纯库项目含 Cargo.toml 即被误判，进而按 SKILL.md 触发 R4 并行与 H1/H7 深度上调；
Lua 实测 build_files=[]（Makefile 未被检出）。

**v3.3 设计变更**：
1. **四值分类 + 信号加权**：构建文件降为信号之一（带权重），新增公共 API 主导信号
   （导出符号密度/头文件率/无 main 入口/无监听器）与框架扩展标志信号
   （插件注册机制/中间件挂载点/生命周期钩子）。`library` 判据 = 公共 API 主导且
   无独立可执行入口。分类器必须覆盖文档声明的全部四值。
2. **maturity 解耦**：context 新增独立 maturity 信号（版本标签语义/成熟标志文件/
   已知框架名对照表），不再与 project_kind 绑定；maturity=unknown 时 R4 并行降级
   为常规串行（保守）。
3. **触发条件明确**：SKILL.md「R4 与 R3 并行启动」的触发条件改为
   `maturity==mature`（机械信号），主代理复核后可手动覆盖。

### P-C 信任边界分类缺口 → host_api 枚举 + 域映射指引

**现象**：trust_boundary.type 无「宿主 API 边界」类型；库组件中「宿主通过公共 C API
喂入不可信脚本/字节码/数据」的输入面被过度归类 local/environment——Lua CAND-002 的
ACROSS_BOUNDARY 判定（后被 R3.5 按惯例假设拦截）部分源于分类表缺位。

**v3.3 设计变更**：
1. **枚举补 `host_api`**：语义 = 数据经宿主应用对本库公共 API 的调用进入（库的公共
   API 即信任边界，Newtonsoft.Json 先例制度化）。R1 任务书 schema 与 surface_mapper
   normalize/validate 同步；library 组件的默认边界建议 host_api。
2. **域映射指引增补**：R1 任务书 4 域 guide 增加「非网络/离线项目」段——解析引擎、
   数据处理库、硬件协议栈的映射示例（宿主 API 喂数据 → data_input 而非 local；
   文件/持久化 → storage；进程控制 → process；无 socket 时 network 域写
   empty_domain_reason 为合法产出而非缺漏）。

### P-D 保守倾向残余 → 明示化对冲路径（设计确认，非新机制）

**现象**：门禁②③的实证压力真实存在；难搭 harness 的语言（嵌入式/硬件）下
假阴性风险最大。审查裁决：机制成立，但已有对冲设计（NEEDS_REVIEW 合法终态、
R3.5-N 复活、v3.1 拦截率收敛目标），且 Lua 审计存在 verifier 主动实证的反例。

**v3.3 设计变更**（仅文档化，不新增机制）：
1. SKILL.md R5 段明示「不实证不申报」路径与源事实级降级规则（W6 §17.7/§21.4 已有，
   明示为 verifier 可引用条款）；
2. 报告模板 NEEDS_REVIEW 段注明「保守裁决」与「证据不足」两种成因的区分写法。

### P-E 先例库系统级覆盖 → +2 条去项目化裁决先例

**现象**：22 条先例高度来源动态语言战役；系统级裁决（C 解析器分配声称的分级、
env→dlopen 类信任边界几何）无先例可依，靠 LLM 自由裁量。

**v3.3 设计变更**：新增 2 条先例（Lua 审计教训去项目化）：
- **PREC-ALLOC-VIRTUAL-001**：分配请求类声称的「实际提交内存」判据——虚拟分配
  （overcommit 惰性提交）不构成资源耗尽，severity ≤ Low；提交内存严格受输入流
  限制时无放大。
- **PREC-ENV-SAME-PRINCIPAL-001**：env→代码加载/执行类声称的信任边界几何——env
  控制者=进程启动者本人（同主体）时与 LD_PRELOAD 等效，无 shipped 特权部署证据
  → 边界类型 DIRECT + Low，非 ACROSS_BOUNDARY。

### P-F 追踪矩阵漂移 → gen_tracking 扫描泛化

**现象**：tools/gen_tracking.py 的 DOCS 字典与提取正则停留在 v3.1 形态，
v3.2/3.2.1/3.2.2 的 REQ/SWR 从未进入 REQUIREMENTS_TRACKING.md——契约同步工具
自身失同步。

**v3.3 设计变更**：DOCS 字典覆盖全部版本段；提取正则泛化为
`(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`；REQUIREMENTS_TRACKING.md 重建含 v3.2~v3.3 全部段。

---

## 2. 变更边界（不动的部分）

- v3 阶段骨架（R0-R6）、六门禁语义、数据模型核心（verify_queue/input_surface/hypotheses）
- LLM 主引擎 + 规则提示器架构（先例/清单库的辅助定位不变）
- 去项目化机制（DEPROJECT_BLACKLIST tripwire + selfcheck 完整性 + 验收新项目判据）
- v3.2.3 修复批次成果（7 项工具缺陷，已提交）
