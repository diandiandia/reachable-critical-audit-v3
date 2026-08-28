# SKILL Lessons — common（2026-08-28）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = application

### R3
- [grade_recomputed] CAND-001: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-002: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-003: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-006: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-008: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-009: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-010: 机械分级重算 (collect-mechanical-recompute)

### R3.5
- [verdict_correction] CAND-003: {'target': 'CAND-003', 'reason': 'R5 强制实证触发(声称类)但环境探针 blocker(无 qemu/clang/KASAN) — 主代理裁决 NEEDS_REVIEW 保守路径, 不实证不申报 (v3.3 明示条款); claim=oom (hashlimit 表耗尽): 静态证据充分(cfg.max==0 时无上限/单表~100MB/多表), 但无内核运行环境实证; 部署门禁=CAP_NET_ADMIN 规则安装组合前提; 保守裁决', 'demote_to': 'NEEDS_REVIEW'}
- [verdict_correction] CAND-004: {'target': 'CAND-004', 'reason': 'claim_type unbounded→protocol_dos (R3.5 证伪者论证 conntrack 表满 NF_DROP 使树有界, 主代理核实 hook 优先级与表满路径属实); severity_override=medium', 'claim_corrected_by': 'main-agent-r35-adjudication'}
- [verdict_correction] CAND-004: {'target': 'CAND-004', 'reason': 'R5 强制实证触发(声称类)但环境探针 blocker(无 qemu/clang/KASAN) — 主代理裁决 NEEDS_REVIEW 保守路径, 不实证不申报 (v3.3 明示条款); claim=protocol_dos (conncount 有界放大~70MB+新流功能阻断): 静态证据充分, 无内核运行环境实证; 保守裁决', 'demote_to': 'NEEDS_REVIEW'}
- [verdict_correction] CAND-005: {'target': 'CAND-005', 'reason': 'R5 强制实证触发(声称类)但环境探针 blocker(无 qemu/clang/KASAN) — 主代理裁决 NEEDS_REVIEW 保守路径, 不实证不申报 (v3.3 明示条款); claim=protocol_dos (SYN 洪泛/reqsk churn): 通用洪泛类, syncookies 默认开, 无内核运行环境实证; 保守裁决', 'demote_to': 'NEEDS_REVIEW'}
- [verdict_correction] CAND-007: {'target': 'CAND-007', 'reason': 'R3.5 1/2 证伪, 主代理逐条回源码采信: ts_recent 推进要求 in-window seq (slow path tcp_input.c:4092 !after(seq,rcv_wup); fast path 6511/6551 seq==rcv_nxt 且 rcv_nxt==rcv_wup, 均核实属实) — 满足前提的攻击者仅对端/on-path, 两者本就能停滞连接(RST/不发送/丢包), 零边际能力增益; 属 RFC7323 设计属性而非内核缺陷, 攻击相关不可达', 'demote_to': 'UN
- [verdict_correction] CAND-007: {'target': 'CAND-007', 'reason': '复活重验裁定: 复活 gap 属实但边际增益≈0, 终局 UNREACHABLE 维持 (重验 agent 逐行核实 7013/6832/6988/6300/6418)', 'reverified_by': 'r3-reverify-agent'}

### R3.5-N
- [resurrection] CAND-007: 复活成立(gap 真实)但重验终局维持 UNREACHABLE: 零边际能力增益, 无独立可修复性

## 主代理过程观察（人工补充）

- 过程观察 1（kernel 级项目首例）: 36k 文件规模下 R1 五域测绘的模块优先级采样纪律有效——152 面全部高置信、validate 零行号漂移; 45 分钟级预算内五域 agent 均完成 21-39 面
- 过程观察 2（冲突裁决）: boundary agent 报「Rust binder 已替换 C binder」与 process 域 6 个 binder C 面冲突——逐条回源码裁决: Kconfig 互斥(IPC_RUST depends on !IPC) + gki_defconfig 实况=C binder 编译; 14 条 Rust binder 边界标 not_compiled_gki 前瞻面
- 过程观察 3（实证路线）: 无 qemu/clang/KASAN 环境下 parser_fuzz 用户态复刻两次成功——RFCOMM skb 下溢(确定性输入 [00 ef ce])与 f2fs 越页读(slot 213+name_len 255)均获 ASAN heap-buffer-overflow 实测; sk_buff/dentry folio 的最小 stub 复刻是无内核环境实证的关键手法
- 过程观察 4（复活波）: 第一次出现复活攻击成功找到证伪论证真实缺口(tcp_input.c:7013 SYN_SENT 无 seq 门禁 ts_recent 写入)——但重验以「零边际能力增益」(同枚不带 TS 的伪造 SYN 已杀~100% 连接尝试)维持 UNREACHABLE; 教训: 复活 gap ≠ 复活成功, 边际增益分析是终局裁决关键维度
- 过程观察 5（上游修复佐证）: 两条实证候选均有上游修复存在(RFCOMM: Muhammad Bilal/yaojiale02 补丁; f2fs: 90e02a8e1b68 Trail of Bits)——audited 快照恰落于修复前窗口; 上游补丁存在性是候选可信度的强旁证, 值得在 R3 任务书预埋「搜索 upstream 修复」提示
- 
首发归属核查（同日增补, 2026-08-28 在线核实实录）: 最高价值候选经公开列表检索为双首发已发现（公开补丁 v1-v4 + KMSAN 报告佐证, 均未合并; 兄弟缺陷已有独立 CVE）——审计独立发现≠首发, 收尾动作从「申报」改为「推补丁合并 + 佐证材料」; 教训: R3.5 证伪者顺带发现的补丁记录必须在收尾阶段做在线归属核查, 申报口径以核查结果为准
过程观察 6（LDM 编译面裁决）: LDM 簇代码级机制真实(16B 头拷入小分配+负 size memcpy)但 GKI 未编译 PARTITION_ADVANCED——scope_dependent drop + 报告配置面注记; microdroid_defconfig 含该选项, 配置扩展面需另行评估

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
