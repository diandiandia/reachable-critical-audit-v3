# SKILL Lessons — elasticsearch（2026-08-27）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = application

### R3
- [grade_recomputed] CAND-002: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-004: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-007: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-008: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-010: 机械分级重算 (collect-mechanical-recompute)
- [grade_recomputed] CAND-011: 机械分级重算 (collect-mechanical-recompute)

### R3.5
- [verdict_correction] CAND-002: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: 算术类定量模型已备 (消息≤0.3×heap × deflate~1032), 机制级静态证据完整; e2e 需发行版构建 (JDK26+gradle 全量) (claim=oom 保留供追溯)'}
- [verdict_correction] CAND-003: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: 异常路径确定性已静态证明 (NFE 两级 catch 逃逸→WARN), 洪泛影响量级未实测 (claim=protocol_dos 保留供追溯)'}
- [verdict_correction] CAND-004: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'claim_type', 'frm': 'rce', 'to': 'other', 'reason': '沙箱成立 (verifier/证伪者共识), 无逃逸证据; 可达性不申报 RCE 后果 (zookeeper CAND-008 先例: 实证驱动 claim 修正)'}
- [verdict_correction] CAND-005: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: 无界性相对上游 cap (http.max_content_length), 未实测 (claim=unbounded 保留供追溯)'}
- [verdict_correction] CAND-006: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: 无界性相对上游 cap, 未实测 (claim=unbounded 保留供追溯)'}
- [verdict_correction] CAND-007: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: 无界性相对上游 cap, 未实测 (claim=unbounded 保留供追溯)'}
- [verdict_correction] CAND-008: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: Rust 原生内存破坏为 sink 类型推断, 未实测; 可达性 edge-proven 完整 (claim=crash 保留供追溯)'}
- [verdict_correction] CAND-010: {'at': 'R5', 'decided_by': 'main-agent', 'rule': '不实证不申报 (v3.3 明示条款) / 证据裁决', 'field': 'verdict', 'frm': 'REACHABLE', 'to': 'NEEDS_REVIEW', 'reason': '证据不足: zstd 原生解压不可信页未实测 (claim=oom 保留供追溯)'}

### R3.5-N
- [resurrection] CAND-008: 复活维度3(部署层前提被当默认关)+维度5(凭惯例假设)。Release 路径的全部承重前提逐一核实为真：distribution/build.gradle:234 排除(commit 93cf0b9d26a8, HEAD)、FeatureFlag.java:72-78(snapshot 默认开/release 默认关, 仅系统属性可开)、FormatNameResolver.java:66-73

## 主代理过程观察（人工补充）

- 【v3.8 验证审计】本审计以验证 v3.8 批次硬化与偏向性修复为目的。8/8 观测点生效见报告结论段。
- 【skill 缺陷·新发现·已记档】target_kind _scan_files 400 文件上限致大仓库 listener 信号假阴性: 31k java 文件下 modules/transport-netty4 排不进前 400, ServerBootstrap token (SWR-V3.8-024) 真命中但机械未报 (Netty4HttpServerTransport.java:183)。建议: listener 信号改用 max_hits 优先策略或按模块目录加权扫描, 而非固定 os.walk 顺序截断。
- 【skill 缺陷·新发现·已记档】r35-collect 落盘 refutation 时缺 survived/votes/refute_count, 渲染器 summary 复核列 (batch_verify._refutation_line:1436) 恒显示『未复核』——nacos lesson #7 同源缺陷的新形态 (workflow decisions 有这三个字段, collect 只读 journal 逐条记录未聚合)。建议: r35-collect 聚合时写入 votes=len(decs)/refute_count=len(kills)/survived=kills<2。本次主代理手工归一 (normalized_by=main-agent)。
- 【skill 缺陷·新发现·已记档】BOUNDARY_KINDS 无 panama 枚举: elasticsearch libs/native 全为 java.lang.foreign FFM (Panama) 桥接 (8 条 boundary surface 中 6 条), 被迫归一为 ffi-other 并记录 boundary_kind_note。建议: BOUNDARY_KINDS 增 panama (义务入库三问: 触发=Java FFM 项目渐成主流; 消费者=boundary validate + 报告 B.3 FFI 表; 裁掉丢什么=Panama 与 JNI 的边界风险形态差异)。
- 【机制价值】复活波第三次实战成功: CAND-008 的 verifier 以『snapshot 非 shipped 布局』未实证断言封死死代码豁免, 复活者枚举 snapshot/nightly 工件 (每日 Docker 镜像/nightly tarball/CI 构建) 为真实部署布局, 8 跳链+9 边重验改判 REACHABLE 并通过 post-resurrect 证伪 (2/2 存活, https:// 零配置向量被补强)。与 kafka 3/3 同源: UNREACHABLE 的部署布局类承重前提必须核实构建系统的默认分支 (snapshotBuild 默认 true)。
- 【机制价值】证伪者产出质量: 8/8 存活但 5 个候选附 poc_evidence 级定量模型 (CAND-002: 0.3×heap × ~1032 deflate 比 = 9.7MB→10GB 单连接堆耗尽模型), 复核价值从 kill/keep 二元扩展为定量加固。
- 【裁决实录】claim 修正两例: CAND-004 rce→other (沙箱成立共识) + severity_override=medium; 7 条声称类 NEEDS_REVIEW (证据不足: ES 9.6 需 JDK26+gradle 全量构建, 不实证不申报)。zookeeper CAND-008 先例 (实证驱动 claim 修正) 再次适用。
- 【覆盖率闭合】62 surfaces 中 32 个经 relay 分类闭合 (门禁⑦), 覆盖依据按 v3.5 语义写入 H-7 finding evidence 文本 (coverage_relay_basis 块)。前缀归一化 (SURF-DAT- vs SURF-DATA-) 是主代理计算 tracked 时的易错点。
- 【编排】薄封装 fileref 模式在 verify/refutation/resurrect 三种波次复用成功 (3 个 thin wrapper 脚本, args 均 <1KB); 复用导出脚本 SCHEMA 常量与返回契约/tooling_version 的纪律未破坏 collect 链。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
