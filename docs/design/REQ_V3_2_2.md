# Reachable Critical Audit v3.2.2 — 系统需求规格书（System Requirements）

> 从 `SYSTEM_DESIGN_V3_2_2.md`（问题域 P-A~P-F）导出的系统开发需求。每条附来源追溯与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.2.2 段）。日期：2026-08-17
> 编号规则：REQ-V3.2.2-xxx；优先级：P0=影响结论正确性，P1=影响效率/文档一致性
> 最高判据：SKILL.md「第一原则：通用型 Skill」

## 1. 资产去项目化与 lang 维度（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-001 | 资产入库门禁（去项目化检查器）：签名 semantic/grep 命中项目专属名黑名单（DEPROJECT_BLACKLIST）即 validate 拒绝 | 设计 §2.1 | P0 | validate 对含 "multer" 的 grep 报错；现有 13 签名全通过 |
| REQ-V3.2.2-002 | 签名数据模型 v2：L2 词族 lang 必填（VALID_LANGS）；L3 语义族 cwe 非空 + semantic 抽象形态非空；污染签名重构（PY-PICKLE 拆分、TS/KT/AUTHZ/HEADER-INJ 删项目专属名） | 设计 §2.1 | P0 | 13 签名 lang/cwe 完备；mbedtls 复跑 PY-PICKLE 零命中 |
| REQ-V3.2.2-003 | match 阶段强制 surface.lang 过滤 + tests/test 路径段排除 | 设计 §2.1 | P0 | mbedtls 36 hits 复跑无跨语言命中、tests/ sites=0 |
| REQ-V3.2.2-004 | gen 只从 L3 语义族命中生成假设；L1/L2 命中仅 reading_hints 佐证 | 设计 §2.1 | P0 | mbedtls 复跑 gen 无 L2 词族假设 |
| REQ-V3.2.2-005 | R0 冒烟语义修正：fixture 仓库保持 anchor recall hit_rate 检查；非 fixture 仓库改为签名库完整性自检（validate+lang 完备+去项目化 0 命中+grep 可编译），失败阻止启动；回归锚点移入 tests/fixtures/known_instances.json | 设计 §2.1 | P0 | selfcheck 对 mbedtls 输出 integrity OK 且 exit 0 |
| REQ-V3.2.2-006 | verifier 任务书步骤 0.5 按候选 lang 分派模板（python/c/cpp/go/rust/java/default 各一版）；例证去项目名 | 设计 §2.1 | P0 | C 候选任务书不含 find_spec 文本 |
| REQ-V3.2.2-007 | 先例库/清单库运行时字段脱敏：项目名只允许出现在追溯字段（applications/source_lessons） | 设计 §2.1 | P1 | grep 运行时字段无项目名残留 |

## 2. harness 按声称类别覆盖（P-B）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-008 | harness_runner 新增 parser_fuzz 模板（C/C++：ASan+UBSan 骨架，mbedtls 实战模板化），绑定 crash 声称类 | 设计 §2.2 | P0 | 模板存在；对 asn1_get_len 提取体可复现 DEFENSE_CONFIRMED |
| REQ-V3.2.2-009 | harness 覆盖矩阵（claim × 语言）落盘 resources/harness_coverage_matrix.json；R5 现场构造引用矩阵缺口 | 设计 §2.2 | P1 | 矩阵文件存在且与 TEMPLATES 一致 |

## 3. 契约同步（P-C）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-010 | signature_lib 新增 selfcheck CLI 子命令（R0 单一事实源）；SKILL.md 只保留该命令；新增 doc-lint 测试从 SKILL.md 抽取代码块真实执行 | 设计 §2.3 | P0 | 照抄 SKILL.md R0 命令在非 fixture 项目 exit 0；doc-lint 入测试套件 |
| REQ-V3.2.2-011 | surface_mapper merge 默认落盘 input_surface.json（--out 可选） | 设计 §2.3 | P1 | merge 后文件自动存在 |
| REQ-V3.2.2-012 | r2_guard drops 输入归一化（drop/dropped 双键） | 设计 §2.3 | P0 | mbedtls r2_filter_output.json 复跑报 dropped=3 |
| REQ-V3.2.2-013 | r2_guard anchor 支持 hit_sites 数组形态（假设文件批量检查） | 设计 §2.3 | P1 | hypotheses.json 直接过 anchor 检查 |
| REQ-V3.2.2-014 | batch_verify r4 假说 id 归一化（H1/H-1 双向，内部统一 H-N） | 设计 §2.3 | P0 | r4-collect 后直接 r4-assert PASS |
| REQ-V3.2.2-015 | lessons_recorder resurrection_review lenient 加载（str→dict 包装）；SKILL.md R3.5-N 写明候选级 dict 落盘契约 | 设计 §2.3 | P1 | str 形态不再崩溃 |

## 4. 语义收敛（P-D）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-016 | collect 机械规则：verdict≠REACHABLE → claim_type=null + claim_nulled_by 标记 | 设计 §2.4 | P0 | UNREACHABLE 候选不触发 empirical_required |
| REQ-V3.2.2-017 | VERDICT_SCHEMA 声明 claim_type 仅 REACHABLE 有意义（enum 含 null） | 设计 §2.4 | P1 | 新队列无 UNREACHABLE+claim 组合 |

## 5. scope 与覆盖传播（P-E）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-018 | R0 落盘 scope_snapshot.json（submodule status+关键目录存在性）；batch_verify 入队前自动 diff → scope_changed 输出 | 设计 §2.5 | P0 | mbedtls 快照 diff 可检出物化变化 |
| REQ-V3.2.2-019 | R2 drop 条目支持 scope_dependent 标记（"树外不可验证"类理由强制 true）；scope 变更时提示复活流程 | 设计 §2.5 | P0 | filter 模板含该字段；scope_changed 附复活建议 |
| REQ-V3.2.2-020 | merge 落盘 mirror_pairs；assert_ledger 门禁⑦ tracked 计算自动传播镜像面 | 设计 §2.5 | P0 | mbedtls 复跑 15 冲突对无需手写镜像 bridge |
| REQ-V3.2.2-021 | coverage_bridge 文档化为 relay 面正式通道（SKILL.md 门禁⑦） | 设计 §2.5 | P1 | SKILL.md 门禁⑦写明 |

## 6. 机械信号（P-F）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-022 | target_kind listener/startup-chain 信号路径分域：非产品段（tests/scripts/tools/docs）不计；库段（library/lib）与示例段（examples/demos/programs）计 lib 方向 | 设计 §2.6 | P0 | mbedtls 机械推荐 library |
| REQ-V3.2.2-023 | tier 语言混合度只计 component_role=server-side；language_inventory 运行时占比修正（>90% 非运行时目录 → build-config） | 设计 §2.6 | P1 | mbedtls .sh/.py/.pl=build-config；tier 归因不含语言混合 |
| REQ-V3.2.2-024 | batch_verify collect --from-journal 自动提取 schema-validated 结果落盘（result/value 双字段） | 设计 §2.6 | P1 | 无手工拼 --cand-XXX 参数 |

## 7. 附带项

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-030 | evidence_ledger r4_feedback 冲突支持 resolved 标记位（{candidate,key,resolved_by,note}），已裁决冲突不再重复告警 | 设计 §2.7 | P1 | 标记后 r4_feedback 不重复输出 |

## 8. 验收需求（Phase 3.2.2.3）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.2.2-040 | mbedtls 本树机械复跑：8 缺陷对应手工绕过全部消失（selfcheck/merge 落盘/drops=3/anchor 直过/r4 直连 PASS/lessons 不崩/UNREACHABLE 无 empirical 违规/镜像免手写桥） | 设计 §4 | P0 | 全部绕过消失 + 六门禁 PASS |
| REQ-V3.2.2-041 | mbedtls 复跑结论零丢失（0 REACHABLE / 6 R4 findings / 4 UNREACHABLE 复活未复活） | 设计 §4 | P0 | 与 2026-08-17 审计终态一致 |
| REQ-V3.2.2-042 | 三锚点回归（tests）+ 新增契约测试全绿 + install.sh 安装完成 | 设计 §4 | P0 | 全测试绿 + install 完成 |
| REQ-V3.2.2-043 | 第一原则验收条款：本版验收对象 mbedtls 为 v3 首审 C 库项目（此前无 C 库先例），满足"每版本至少一个新项目验收"约束并在 ACCEPTANCE 明示 | 设计 §4 | P1 | ACCEPTANCE 文档写明 |
