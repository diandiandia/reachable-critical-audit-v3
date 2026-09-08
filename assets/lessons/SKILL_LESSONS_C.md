# Reachable Critical Audit Skill — C 语言审计暴露的缺陷与改进建议

> **文档性质**：基于 lighttpd 1.4.85（HEAD `2ddc5138`）实测审计对 `reachable-critical-audit`
> skill 的回顾性缺陷分析。驱动 skill 规则库改进，非项目审计报告。
>
> **审计日期**：2026-08-15
> **测试目标**：/root/lighttpd1.4（纯 C Web 服务器，195 个源文件，单线程事件驱动）
> **执行模式**：Mode A'（Agent 工具 + batch_verify.py 状态机，~200 个簇级验证任务，157 个 collect 批次）
> **量化背景**：R1 原始命中 10,097 → 物理过滤后保留 1,096；R3 全量验证 0 REACHABLE；
> 8 个 R4 findings 全部来自业务深钻。Sink Discovery Rate 95.77%，但该指标被噪声占比放大，
> 见 §2.8。

---

## 0. 摘要

C 是 skill 规则库覆盖的语言之一，但 lighttpd 实测暴露的缺陷与 Java（Dubbo/fastjson2）审计
呈镜像关系：**Java 的问题是"语义误标"（把反射当 XXE、把 remove 当越权），C 的问题是
"pattern 伪影"（把每个指针解引用当 NULL deref、把每个 free 当 UAF）**。两类缺陷的共同
根因相同——规则以关键字/结构形态匹配，缺少数据流与语义上下文。

本次暴露的 6 类缺陷：

1. **L0 C 规则 AST pattern 大面积伪影**：CWE-476 `(pointer_expression)` 命中所有解引用、
   CWE-416 命中每个 `free()`、CWE-908 正则命中注释行——10,097 原始命中中 ~9,000 为伪影
   （89% 噪声率，与 Dubbo 的 89.15% 高度一致）。
2. **规则库平台错配**：CWE-125 STREAM_TO_* / CWE-789 osi_alloc 系列是 Android Bluetooth
   专属 pattern，在 lighttpd 中命中 `p+=3;` 指针推进与任意 malloc。
3. **路径过滤有洞**：`src/t/`（目录名 "t" 而非 "test"）、`src/lemon.c`（构建时代码生成器）、
   `packdist.sh`（打包脚本）、`NEWS`（文档）均未被过滤。
4. **R1.5 wrapper_detection 平台错配**：r15 任务书模式（osi_*/STREAM_TO_*/Unretained）对
   lighttpd 无用，真实 wrapper（buffer_append_* 家族、gw_backend 协议编码器、
   fdevent_fork_execve、ck_* 分配器）全靠提取器 agent 自行发挥。
5. **工具链缺陷**：`--cand-` 参数只接受 CAND- 前缀 id（R05-* 候选无法 collect）、
   ast_scanner 覆写 verify_queue、assert 对"常规 free 无单点阻断"的 null blocking_point 报错、
   depth<3 门禁与死代码冲突。
6. **子智能体输出格式漂移**：1 个 agent 返回裸字符串 verdict，合并多任务书 agent 格式不一，
   部分调用链引用了不存在的文件名。

---

## 1. 关键缺陷

### 1.1 R1 L0 规则库 C 噪声逐类分解（最严重）

R1 原始命中 10,097 条，物理过滤后保留 1,096（过滤明细见项目
`.audit_results/r1_noise_filter.json`）。噪声类别逐条：

| CWE | 命中数 | 伪影根因 | 处置 |
|---|---|---|---|
| CWE-476 NULL deref | 7,062 | AST pattern `(pointer_expression) @ptr` 匹配**每一个**指针解引用（`->`/`*`），无 NULL 检查/来源语义 | 物理忽略 |
| CWE-908 未初始化 | 1,551+ | 正则 `send\|write` 命中**注释行**（sink_content 直接是注释文本） | 物理忽略 |
| CWE-352 CSRF | 1,032 | Web 应用类别规则（post/put/delete）在 C 服务端无意义——profile 自带 notes 已承认 | 物理忽略 |
| CWE-125 OOB 读 | 163 | STREAM_TO_* 是 Android Bluetooth 专属，lighttpd 不存在 → 命中 `p+=3;` 指针推进 | 物理忽略 |
| CWE-22 路径穿越 | 93 regex-only | 正则 `put\s*\(\|write\s*\(` 命中任意 `write()` 调用 | 仅保留 6 个 AST 确认的 fopen/open |
| CWE-787 OOB 写 | 113 | for_statement pattern 命中 `for(i=0;i<n;i++) arr[i]=0;` 循环初始化（lemon.c 生成器内居多） | lemon.c 丢弃，其余逐点验证 |
| CWE-416 UAF | 373 | `free(` 正则命中**每个** free 调用，无释放后使用语义 | 逐点验证（全部 UNREACHABLE） |
| CWE-134 格式串 | 80 | 命中固定格式串 `printf("%s%s%s%s\n")` 等，无 taint 判定 | 逐点验证 |

**skill 缺陷**：
- AST pattern 匹配"结构形态"而非"危险操作"——`(pointer_expression)` 在 C 中等于全量命中，
  没有把"该指针是否可能为 NULL / 是否来自分配失败路径"纳入规则。
- 正则 sink 没有排除注释与字符串字面量（CWE-908 的命中行是注释）。
- C 规则缺失 C 生态最常见的 sink 家族：`buffer_append_*`（变长拼接）、协议编解码
  （FCGI/SCGI/AJP 长度字段写缓冲）、`fork+execve`（spawn）——这些全部由 R1.5 L1 提取器
  兜住，L0 零覆盖。

**根因**：与 Java 侧一致（见 `SKILL_LESSONS_JAVA.md` §0 与 Dubbo 复盘问题 1）——
规则以"关键字/sink 名称/结构形态"匹配，缺少语义上下文与污点参与。数据流分析没有真正
参与初筛，导致初筛既漏（真实 sink 家族无规则）又滥（伪影 89%）。

### 1.2 路径过滤缺陷（4 个漏网点）

`_IGNORE_PATH_PARTS` 含 `test/tests/tools/build/scripts/...`，但实际漏网：

1. **`src/t/`**：lighttpd 单元测试目录名为 `t`，不匹配 `test` 词元 → 26 个测试代码候选入队，
   主代理按 R1.4 规则手工丢弃。
2. **`src/lemon.c` + `src/lempar.c`**：LEMON 解析器**生成器**（构建时代码生成器，非运行时
   服务端代码）位于 src/ 下，~332 个候选（CWE-416 free 站点 + CWE-787 循环）需手工丢弃。
3. **`packdist.sh`**：仓库根的打包脚本产生 14 个 shell 候选（CWE-78/352），手工丢弃。
4. **`NEWS`**：文档文件产生 2 个候选（规则对无扩展名文本文件也跑正则）。

**改进建议**：路径过滤应支持 ① glob 配置（如 `src/t/**`、`**/lemon.c`、`*lemon*`）；
② 构建系统感知——从 CMakeLists/Makefile 提取"参与运行时构建的目标列表"，排除代码生成器
（lemon.c 出现在 CMake 的 `add_executable(lemon ...)` 而非库列表）。这条对任何带生成器的
C 项目（yacc/lex/ragel）通用。

### 1.3 R1.5 wrapper_detection 平台错配

`--stage r15` 生成的 cpp 任务书模式为：`osi_*`、`STREAM_TO_*`、`*::Unretained`、
`*_delete`——**全部是 Android Bluetooth 栈的 wrapper 生态**。lighttpd 的真实 wrapper 生态是：

- 分配器：`ck_malloc`/`ck_calloc`/`ck_realloc_u32`（ck.c）
- 写缓冲：`buffer_append_string_len`/`buffer_append_str2/3`/`buffer_append_path_len`（buffer.c）
- 协议编码：`fcgi_create_env`/`ajp13_env_add`/`scgi_env_add_scgi`（跨进程写 sink）
- 进程 spawn：`cgi_create_env` + `fdevent_fork_execve`（CWE-78 sink）
- SQL 拼接：`mod_vhostdb_mysql_query`（CWE-89 sink，L0 完全不可见）

上述 34 个 L1 候选全部由提取器 agent 在主代理 prompt 补充的"项目背景"下自行发挥产出。
**若主代理不补充背景，R1.5 在本项目将产出空集。**

**改进建议**：`wrapper_detection.<lang>` 应按"平台 profile"拆分（嵌入式/服务端/桌面），
或至少要求主代理在 r15 阶段前写入项目输入面描述（并入 architecture_view），任务书模板
显式携带该描述。lighttpd 这类的 C 服务端 wrapper 规则（`*_create_env`、`*_write_request`、
`*_fork_execve`、`buffer_append_*`）应固化为 profile。

### 1.4 工具链缺陷

#### 1.4.1 `--cand-` 解析器强制 CAND- 前缀（本次最痛的工具问题）

`batch_verify.py` 的参数解析：
```python
num = parts[0].replace("--cand-", "")
cand_id = f"CAND-{num}"   # ← 强制前缀, 无法表达 R05-* 等自定义 id
```
R0.5 差异考古入队的候选 id 形如 `R05-8c62a890`，**无法通过 collect CLI 落盘**（拼出的
`CAND-R05-8c62a890` 在队列中不存在）。本次 7 个 R05 候选全部靠主代理写直接改 JSON 的
脚本落盘。**影响结论正确性**：任何 origin=R05 的"疑似未修复"候选若无手工脚本就无法进入
状态机闭环。

#### 1.4.2 ast_scanner 覆写 verify_queue.json

重跑 `ast_scanner.py` 会**整体覆写** verify_queue.json——R0.5 阶段先入队的 7 个 R05 候选
被静默冲掉（`by origin` 从 L0+R05 变为纯 L0），主代理靠差异检查发现后手工重新并入。
REQ-12 只约束了路径，没约束"入队语义必须是合并而非覆写"。

#### 1.4.3 assert 对 null blocking_point 报错（与 Dubbo 复盘问题 5.1 同源）

`--stage assert` 要求 UNREACHABLE 候选的 `blocking_point` **非空**。但"常规同步 free/清理，
释放后无后续使用"这类判定**没有单点阻断**——69 个候选被断言拒绝，主代理回填语义化文案
（"无单点阻断: 常规同步释放…"）才通过。建议：collect 阶段前置校验，或允许
`blocking_point: "N/A"` + `evidence` 解释的合法组合。

#### 1.4.4 call_chain_depth<3 门禁与死代码冲突（与 Dubbo 复盘问题 5.5 同源）

死代码候选（vector.c 零调用者、`#if 0` 块、`#ifdef _WIN32` 分支）**结构上无法构造 3 层
调用链**，被门禁自动降级 NEEDS_REVIEW——语义上它们应判 UNREACHABLE
（`blocking_point: "no production callers"`）。本次 ~5 个此类候选混入 NEEDS_REVIEW 清单。

#### 1.4.5 R0.5 工具问题

- 输出默认只打 stdout，**不传 `-o` 不落盘**（第一次运行无产物，重跑才拿到 JSON）；
- 输出经管道 `| head` 时 SIGPIPE 导致 exit 1（误判为失败）；
- 默认 grep 词表（含 "fix"/"safe"）过宽：lighttpd 1688 个 commit 被标记"安全相关"，
  439 个提取出 guards，绝大部分是普通重构（如 `[core] move con throttling`）——
  **考古噪声与 L0 扫描噪声同构**；
- 对 HEAD 审计，"疑似未修复"判定需要版本意识：所有修复 commit 都是 HEAD 的祖先
  （修复必然已在树内），真正的价值是"修复变体复核"（兄弟路径是否残留同类缺陷），
  本次 7 个变体复核全部确认修复完整。

#### 1.4.6 子智能体输出格式漂移

- 1 个 agent 返回 `{"CAND-022": "UNREACHABLE", ...}` 裸字符串 verdict（缺必需字段），
  靠 SendMessage 追补才拿到完整对象——collect 的 REQUIRED_VERDICT_KEYS 校验救场，
  但重试机制在 Mode A' 下是"主代理手工追补"，建议任务书模板加"输出必须经
  python3 -c 'import json,sys; json.load(sys.stdin)' 校验后提交"式自查提示。
- 合并多任务书的 agent 偶尔漏候选（本应 8 个只回 8 个但顺序混乱）或调用链引用不存在的
  文件名（如 `src/connection.c:connection_state_machine_loop`，实际是 connections.c）。
  质量换效率的代价——建议合并批次时限制单 agent 候选数 ≤ 6。

#### 1.4.7 并发与批次规模

skill 文本要求"每次 3~5 个子智能体"，但 200 簇 × 862 候选按该节奏需 60+ 轮。
本次实际按 10~20 并发 + 簇级任务书（每 agent 一个 file×CWE 簇）执行，157 个 collect
批次无丢失。建议把**簇级批量模式**（一个 agent 验证一个 file×CWE 簇，返回 per-candidate
verdicts）写入 SKILL.md 作为 Mode A' 的官方形态，并标注环境并发上限
（CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=20 会被撞顶）。

### 1.5 值得固化到 skill 的实战技巧

1. **gcc -E 预处理验证死代码**：lshpack 簇 agent 用 `gcc -E -P -I src -I src/ls-hpack
   lshpack.c` 验证 `#if LS_HPACK_USE_LARGE_TABLES` 等宏分支是否编译进产物，把
   "死代码"判定从猜测升级为实证。建议写入 C 语言 verifier 任务书。
2. **上游逐字节比对**：mod_dirlisting/mod_auth 簇 agent 直接 diff 上游 master 确认
   "无修复缺口"（1.4.85 vs upstream 1.4.86），对开源项目是低成本的负向验证。
3. **L1 提取器 prompt 注入项目背景**：本次 34 个 L1 候选全部依赖主代理在 prompt 中补充
   lighttpd 的 buffer/协议/spawn 生态——证明"框架感知扩展"的实际质量由主代理的领域知识
   决定，而非规则库。

---

## 2. 改进建议（按优先级）

### P0 —— 影响结论正确性
1. **C 规则语义化改造**：CWE-476 移除裸 `(pointer_expression)`（或要求配 NULL 检查模式）;
   CWE-416 从"free 调用点"改为"free 后引用/异步持有"模式; CWE-908/22 的 regex 排除注释与
   字符串字面量; CWE-352 对非 Web 语言物理禁用。
2. **C 服务端 sink profile**：新增 buffer_append_*/协议编码/spawn/SQL 拼接规则族（对应
   L1 提取器本次发现的所有真实 sink）。
3. **collect 支持任意 id 前缀**：`--cand-<full-id>=...` 按字面 id 匹配，不再拼 CAND- 前缀;
   ast_scanner 入队改为 merge 语义（REQ-12 扩展）。
4. **assert 规则修正**：blocking_point 允许 `"N/A"`（常规释放类）与
   `"no production callers"`（死代码类），collect 前置校验与 assert 统一。

### P1 —— 影响效率
5. **路径过滤可配置**：glob 白名单/黑名单 + 构建系统感知（区分运行时目标 vs 代码生成器）。
6. **簇级批量模式官方化**：`--stage next-cluster` 按 file×CWE 出队，任务书直接含全簇候选;
   batch size 参数化。
7. **R0.5 输出语义修正**：默认落盘 `-o`; grep 词表分级（security 关键词 vs 通用 fix 词）;
   对 HEAD 审计自动切换为"变体复核"模式。

### P2 —— 可用性
8. **wrapper_detection 平台 profile 化**（嵌入式/服务端/桌面），r15 任务书自动携带。
9. 死代码/宏分支判定技巧（gcc -E、上游 diff）写入 C verifier 任务书附录。

---

## 3. 本次审计中 skill 表现良好的部分（保持）

1. **锚点召回门禁**：cpp 锚点 100% 通过，R0 正常放行（对比 Dubbo 审计中该门禁真实拦下过
   cpp 0/1 盲区——机制在两次审计中都起了作用）。
2. **R3 质量门禁的调用链质量**：867 个 UNREACHABLE 平均深度 4.18（最深 7），verifier 对
   "分配与长度同源"（buffer_extend 自洽）、"引用计数配对"（chunk/kp/stat_cache）、
   "fdevent_sched_close 置 NULL"等防御的定位精确到行，全量 0 REACHABLE 的结论可信。
3. **R0.5 变体复核价值**：7 个高价值近期修复（后端 CL 校验、trailer 拒绝、extforward
   OOB、Range UAF、alias 穿越、Connection split）全部确认完整——对成熟加固项目是低成本
   高置信的负向验证。
4. **R1.5 不可跳过性被再次证明**：CWE-89 SQL 拼接点（vhostdb_mysql）、CWE-78 exec 链
   （cgi_create_env→fdevent_fork_execve）、CWE-130 协议写族——全部来自 L1，L0 零覆盖。
5. **R4 六类固化假说的兜底价值**：8 个 findings 全部来自 R4（ssi.exec 默认开启、
   WebDAV 锁 refresh 无 owner 校验等）——静态阶段全绿的成熟项目，业务深钻是唯一能产出
   真实发现的位置。

---

*本 lesson 随 lighttpd 审计归档（/root/lighttpd1.4/.audit_results/）；与 Java 侧经验
（Dubbo 复盘问题 1~7）共同构成 skill v2.2 规则库与工具链改进的输入。*
