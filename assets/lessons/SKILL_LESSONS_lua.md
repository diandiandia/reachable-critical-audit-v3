# SKILL Lessons — lua（2026-08-19）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = {'value': 'hybrid', 'signed_by': 'main-agent', 'rationale': 'core lua_* interpreter library (lapi/lvm/lparser/lundump/lstate...) = library component, public C API + untrusted script/bytecode inputs are the trust boundary; lua.c standalone CLI interpreter = application component (reads scripts from file/stdin/-e). Existence rules loaded per component.', 'machine_recommendation': 'library', 'components': {'core_library': 'library', 'lua.c_cli': 'application'}}

### R3.5
- [verdict_correction] CAND-001: {'target': 'CAND-001', 'kind': 'line_drift+severity_scope', 'note': '行号修正 lauxlib.c:857→851, lapi.c:1115→1120 (不影响边真实性); 影响表述修正: 默认 overcommit 下为纯虚拟映射 (0 页提交/微秒级/干净错误), 提交内存严格受输入流限制, n 字段无实际内存放大 → severity 应定 Low (机制 REACHABLE + 影响有限); 受限环境 (overcommit=2/ulimit) 下为可捕获 LUA_ERRMEM', 'demote_to': None,
- [verdict_correction] CAND-002: {'target': 'CAND-002', 'kind': 'trust_boundary', 'note': '主代理裁决: 1/2 分歧按 v3 规则保留 REACHABLE (机制 4/4 实证属实, 双方均确认)。采纳证伪者#1 的边界纠正: reachability_type ACROSS_BOUNDARY→DIRECT (env 控制者=启动者本人, 同主体环境输入); 跨主体利用需 setuid/包装器部署 — 仓库内无证据, 属假设性部署。severity=Low, 定位为『未文档化 env→dlopen 攻击面』(5.5.1 新增, manual 0 命中; 与 LUA_I

## 主代理过程观察（人工补充）

- 【过程观察 1 - C 项目签名库 0 hits 的 R2 承载形态】签名库 L2 词族 6 语言无 C、L3 语义族面向 server-framework (bodyBuffer/writeFully/extend_from_slice 等)——对 C 解释器 0 hits 是结构性空白而非异常。LLM 主路径 (v3.1) 完全承载 R2 (20 假设全 LLM 来源)。启示: C/Rust/系统级项目的 L3 语义族应补 memory-unsafe 侧签名 (luaM_newvectorchecked 无上限分配/varint 计数驱动 alloc 家族), 否则佐证器在系统语言项目上空转。
- 【过程观察 2 - 子智能体受 plan mode 限制的落盘路径】R2 filter agent 运行中途会话进入 plan mode, 其产出 JSON 无法写入 .audit_results/, 只能存于自身 plan 文件。主代理按『铁律 1 重试+产物定位』从 plan 文件完整恢复 (20 条全量, 无截断)。skill 目前未定义『子智能体产出被权限层拦截』的处理契约——建议: 任务书加一条『若无法落盘, 最终回复必须是完整 JSON 且明确标注未落盘』, 主代理恢复时写 recovered_by 字段。
- 【过程观察 3 - 5.5 chunk 布局三连变】5.4→5.5 二进制 chunk 格式三处变更: ① header 移除 sizeof(size_t) (40B→新布局, checknum 改 size+value 双字段) ② Proto 字段 source 移到末尾、is_vararg 被 flag 字节替换 ③ 新增 loadAlign/dumpAlign 对齐填充 (分配前读 padding)。首版 patch 因忽略 loadAlign 在对齐步 EOF——实证程序反而精确捕获了防御机制的位置。启示: 二进制解析器审计时, 实证 harness 必须双向核实 (dump 侧写什么/undump 侧读什么), 单一侧假设会产生错误 chunk。
- 【过程观察 4 - varint 字节序双实现】dumpVarint 写 MSB 组先 (带 0x80)、loadVarint 读 x=(x<<7)|group 同序——wire 格式与常见 LEB128 (LSB 先) 相反。首版生成器按 LEB128 写 5 字节 (FF FF FF FF 07) 被 loadVarint 中间限制 (x≤limit>>7 每次折叠前检查) 拒绝, 唯一通过编码为 87 FF FF FF 7F。启示: 畸形输入生成器必须用被测代码的真实解码逻辑验证编码 (对照推演), 而非库函数直觉。
- 【过程观察 5 - R4 文件结构 vs r4-collect 期望】R4 agent 按任务书写 {"hypotheses":[...], "tracked_surfaces":[...]} 包裹结构, 而 batch_verify r4-collect 期望裸列表 (每元素带 hypothesis_id)。首跑 collect 静默收集 0 条 (top-level dict 无 hypothesis_id 被跳过) 无报错——需要主代理发现。启示: collect 类 stage 静默空收应至少输出 warning (items=1 but 0 hypothesis_id extracted)。
- 【过程观察 6 - journal collect 目录语义】--from-journal 期望 transcript 目录 (内部 glob journal.jsonl), 传文件路径时 os.path.join 静默拼接失败→『journal 无 schema-validated 结果』误导性报错。启示: 错误信息应区分『目录不存在』与『有 journal 但无 schema 结果』。
- 【过程观察 7 - R3.5 拦截价值实证】CAND-002 的 ACROSS_BOUNDARY 判据 (env=进程边界外部输入) 是 verifier 的 trust_boundary 惯例假设, 被证伪者#1 用『同审计 LUA_INIT 先例 + shipped 配置无 setuid』双证据拦截, 主代理采纳边界修正 (DIRECT+Low)。这再次验证 R3.5 的核心价值=拦截『代码路径可达≠攻击相关』(v3 回归三连的第四次实战拦截)。
- 【过程观察 8 - 行号漂移双源】本次 4 处行号修正来源双类: ① R1 agent 对未直接读的文件凭结构推断 (onelua.c:17→22) ② verifier 调用点行号与定义行号混淆 (lauxlib.c 857→851)。R3.5 证伪者逐跳 grep 复核机制有效兜底。
- 【过程观察 9 - CWE 枚举无 RCE 类】claim_type 枚举 {crash,panic,oom,unbounded,xss,protocol_dos,other} 无代码执行类, CAND-002 判 null 后主代理归一化为 other。启示: env→dlopen/RCE 类声称应纳入枚举 (rce), 否则实证门禁触发与报告口径都需手工修补。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
