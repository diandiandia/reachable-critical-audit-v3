# Reachable Critical Audit v3.4.3 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_4_3.md` 组件 M1~M9 导出的软件开发需求。
> 编号规则：SWR-V3.4.3-xxx；状态：未开发 / 开发中 / 已经完成开发。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.4.3 段）。日期：2026-08-20

## M1: batch_verify 收集链（REQ-V3.4.3-001/002/007）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-001 | stage_r4_collect 自适应解包：输入为 dict 且含 `hypotheses` 对象（非列表）时按键遍历；findings 在顶层数组（id=FX + hypothesis 字段）时按 hypothesis 归位；evidence 为字符串数组时 join（'; ' 分隔）；r3_link 为 {candidate,note} dict 时展平为 "candidate (note)"；severity 大小写归一；发生任一类归一化 → 条目写 schema_normalized_by=[...]；0 提取告警附形态诊断（顶层 keys + hypotheses 类型） | 已经完成开发 |
| SWR-V3.4.3-002 | tracked_surfaces 前缀模糊映射：id 不在 input_surface 已知集时按规则映射（SURF-DATA-0XX↔SURF-DAT-0XX 等域前缀互转；映射命中 → 替换 + mapped_ids 记入条目；仍未知 → 保留原 id 并告警） | 已经完成开发 |
| SWR-V3.4.3-003 | `--mode resurrect`：转调 workflow_export.export_script_resurrect，输出同 workflow-script 规范（script_path/payload/next_step），scope_diff 段保持一致 | 已经完成开发 |
| SWR-V3.4.3-004 | `--stage r35n-collect --from-journal <dir>`：读 resurrect journal 的 decisions，逐候选落盘 resurrection_review={revived, outcome}；已有 resurrection_review 的候选跳过（幂等）；--expect 对账同 collect 段 | 已经完成开发 |
| SWR-V3.4.3-005 | collect（verify 模式）写入 grade_self_reported（verifier 自报 grade）+ evidence_grade 机械重算 + grade_recomputed_by 标记；旧队列缺 grade_self_reported 不报错 | 已经完成开发 |

## M2: evidence_ledger 门禁判定（REQ-V3.4.3-004/005）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-010 | gate ③b（r4_findings 与候选双侧）结构判定优先：empirical_result 非空且匹配实证特征（\d+ 数字 + 实测动词/命令输出/exit code 形态之一）→ 视为有实证；不匹配再走关键词 fallback（实证/已实证/confirmed/source_fact/**实测/measured**）；原误报场景（含「实测」的 g++ 复跑文本）转 PASS | 已经完成开发 |
| SWR-V3.4.3-011 | grade 口径注释对齐：grade_verdict/collect 调用链注释写明「collect 机械重算为唯一权威，verifier 自报存 grade_self_reported 仅追溯」 | 已经完成开发 |

## M3: workflow_export 导出链（REQ-V3.4.3-003/006/011）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-020 | 截断协议统一：新增 _truncate_evidence(evidence, budget, keep_segments) 共用函数——承重前提/实证/阻断关键段必保留，次要段截断且必带「[截断: 全文 N 字符, 见 verify_queue.json]」；resurrect_prompt 与 refute_prompt 均改调该函数（消灭 1200 字符静默截断） | 已经完成开发 |
| SWR-V3.4.3-021 | export lang 推断优先级：候选 lang 字段 → source_file 扩展名 → language_inventory；输出 payload 逐候选带 lang 元数据 | 已经完成开发 |
| SWR-V3.4.3-022 | VERDICT_SCHEMA claim_type 枚举加 "leak"（合法值集 crash/panic/oom/unbounded/xss/protocol_dos/rce/leak/other）；refute_prompt 的 REFUTER_TOOLBOX 增加 leak 类建议 | 已经完成开发 |

## M4: surface_mapper 测绘链（REQ-V3.4.3-002/008）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-030 | merge 前缀归一化：已知域前缀集（SURF-DATA/SURF-DAT/SURF-NET/SURF-PROC/SURF-STOR 等变体）统一到标准前缀；归一化映射写 merge 输出 normalized_ids；归一化后 id 冲突时后缀避让 | 已经完成开发 |
| SWR-V3.4.3-031 | BOUNDARY_KINDS 加 "capi"（描述：C-API 扩展模块胶水，通用，覆盖 Python C-API/Lua C-API/N-API 等）；validate 接受 capi 词族（capi/capi-ext/capi-glue） | 已经完成开发 |

## M5: 提示资产门控（REQ-V3.4.3-009/012）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-040 | checklist_binder 适用性门控：checklist_library 条目带 applicability_signals 时（text 关键词/requires_lang/requires_claim），候选 evidence+sink 上下文不匹配 → 不绑定；无任何匹配清单 → 绑 CK-GENERIC-RESOURCE（新增通用资源类清单：累积点/上限检查点/背压三问） | 已经完成开发 |
| SWR-V3.4.3-041 | _self_refutation_section 同款 signals 过滤：PREC 提示带适用前提标注的不匹配不注入 | 已经完成开发 |
| SWR-V3.4.3-042 | checklist_library +CK-GENERIC-RESOURCE；CK-WS-MATERIALIZE 补 applicability_signals（requires_claim: ws/分片/流式协议累积类） | 已经完成开发 |
| SWR-V3.4.3-043 | precedent_library +PREC-FAMILY-CONSISTENCY-001（跨项目同族裁决判据：放大比是否常数因子 × 物化责任在库侧还是宿主侧；案例：PyJWT vs jsonwebtoken） | 已经完成开发 |

## M6: R4 任务书（REQ-V3.4.3-002/010）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-050 | biz_hypothesis.md 模板加 {surface_id_list} 占位符（主代理导出时以 input_surface.json 实际 id 列表填充，替代「原样引用」指令）+ canonical 输出示例段（列表形态完整字段样例） | 已经完成开发 |
| SWR-V3.4.3-051 | H7 默认值全表预算 800→1200 字（任务书 + 校验器同步） | 已经完成开发 |

## M7: SKILL.md 制度项（REQ-V3.4.3-004/006/012）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-060 | R4 收集段加同事实去重流程：跨假说 title 同事实 → 主申报方承载 severity，其余条目 r3_link 标「同事实共享实证」 | 已经完成开发 |
| SWR-V3.4.3-061 | 兼容回填规范条款：主代理回填 empirical 必须带 backfilled_by + 实测数字依据；禁止无依据回填 | 已经完成开发 |
| SWR-V3.4.3-062 | claim_type 枚举表加 "leak"（数据模型速查段） | 已经完成开发 |
| SWR-V3.4.3-063 | 契约同步：本版 SWR 全部条款同步进 SKILL.md 相应机制段 | 已经完成开发 |

## M8: 语言手册陷阱（REQ-V3.4.3-012）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-070 | harness_manuals/go.md 陷阱清单追加：pgrep -f 自匹配（fd 计数用 /proc/<pid>/fd）；ss 缺失替代；CLI 密码交互静默挂起（stdin 喂空）；getrusage 替代 /usr/bin/time | 已经完成开发 |
| SWR-V3.4.3-071 | harness_manuals/c.md 同款环境陷阱段（连接洪泛实证的黄金证据：合法请求饿死 + fd 数≈连接数） | 已经完成开发 |

## M9: tests（承接全部 REQ）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.4.3-080 | test_r4_collect_adaptive：四类漂移形态各一 fixture（hypotheses 对象 / 顶层 findings / evidence 数组 / r3_link dict）→ collect 后 canonical 字段正确 + schema_normalized_by 标记；canonical 输入零变化 | 已经完成开发 |
| SWR-V3.4.3-081 | test_surface_prefix_map：SURF-DAT-003 等未知 id → 映射到已知 id；真正未知 id 保留+告警 | 已经完成开发 |
| SWR-V3.4.3-082 | test_resurrect_cli：--mode resurrect 导出 payload 与直调等价；r35n-collect 落盘候选级 dict + 幂等跳过 | 已经完成开发 |
| SWR-V3.4.3-083 | test_grade_self_reported：collect 后 evidence_grade=机械值 + grade_self_reported=自报值 + recomputed_by 标记 | 已经完成开发 |
| SWR-V3.4.3-084 | test_gate_structural：含「实测」+数字的 empirical_result → gate ③b PASS；空 empirical_result + Medium → 仍拦截 | 已经完成开发 |
| SWR-V3.4.3-085 | test_claim_leak：claim_type=leak 通过 schema 校验；旧值集不受影响 | 已经完成开发 |
| SWR-V3.4.3-086 | test_boundary_capi：boundary surface capi-* 词族通过 validate | 已经完成开发 |
| SWR-V3.4.3-087 | test_checklist_gating：CWE-400 非 WS 候选不再绑 CK-WS-MATERIALIZE（绑 CK-GENERIC-RESOURCE 或空）；WS 候选仍绑 | 已经完成开发 |
| SWR-V3.4.3-088 | test_truncate_protocol：resurrect_prompt 输出含标记段且承重前提/实证段完整 | 已经完成开发 |
| SWR-V3.4.3-089 | test_export_lang_priority：候选 lang 字段被优先采用 | 已经完成开发 |
| SWR-V3.4.3-090 | 全量回归：现有 149+ 测试全绿；三锚点旧队列六门禁零回退 | 已经完成开发 |
