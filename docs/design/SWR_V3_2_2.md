# Reachable Critical Audit v3.2.2 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_2_2.md` 组件 M1~M16 导出的软件开发需求。
> 编号规则：SWR-V3.2.2-xxx；状态：未开发 / 开发中 / 已经完成开发。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.2.2 段）。日期：2026-08-17

## M1: signature_lib 数据模型 v2（REQ-V3.2.2-001/002/005/010）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-001 | validate(): L2 词族 lang 必填（VALID_LANGS 集合，any 不接受）；L3 缺省 any 不强制 | 已经完成开发 |
| SWR-V3.2.2-002 | validate(): cwe 非空 + semantic 非空 + 去项目化扫描（DEPROJECT_BLACKLIST 大小写不敏感子串命中即报错） | 已经完成开发 |
| SWR-V3.2.2-003 | DEPROJECT_BLACKLIST 常量（mbedtls 复盘取证 24 token）+ VALID_LANGS 常量 | 已经完成开发 |
| SWR-V3.2.2-004 | known_instances 非空强制退役；validate 对空列表不报错 | 已经完成开发 |
| SWR-V3.2.2-005 | load_fixture_instances() 读 tests/fixtures/known_instances.json（{instances:[...]} 形态，缺失返回空表） | 已经完成开发 |
| SWR-V3.2.2-006 | smoke_test 锚点源改为 fixture；testable=0 时执行 integrity_selfcheck 并挂 results["__integrity__"] | 已经完成开发 |
| SWR-V3.2.2-007 | integrity_selfcheck(): validate + L2 lang 完备 + 去项目化 0 命中 + grep 可编译 | 已经完成开发 |
| SWR-V3.2.2-008 | CLI selfcheck 子命令：validate 失败 exit 2；fixture 仓库 hit_rate<required exit 2；非 fixture 完整性失败 exit 2；其余 exit 0 | 已经完成开发 |

## M2: 签名库重构（REQ-V3.2.2-002）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-010 | 13 签名重构：L3 加 lang=any；L2 加具体语言；PY-PICKLE 拆纯 pickle（pickle\\.loads/pickle\\.load\\b/Unpickler）；TS 去 multer/replyTo；KT 去 maxFrameSize/maxDecodedContentLength/respondRedirect/Cookie.parse；AUTHZ-BOUND 去 get_host/good_origin/request_origin/session_secret 加 X-Real-IP；HEADER-INJ 去 CleanXSS；LOGIC-WEAKEN 去 checkAutoType；PATH-WHITELIST 去 configdir/serve_from/valid_path 加 realpath/canonicalize | 已经完成开发 |
| SWR-V3.2.2-011 | 24 条 known_instances 迁入 tests/fixtures/known_instances.json（'XPC 鉴权' 条目移除）；platform_profiles 去重 | 已经完成开发 |

## M3: signature_matcher（REQ-V3.2.2-003/004）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-020 | match(): site 文件路径含 tests/test 段时跳过 | 已经完成开发 |
| SWR-V3.2.2-021 | gen(): tier != L3 命中全部降为 reading_hints（附 tier 与 note），仅 L3 生成假设 | 已经完成开发 |

## M4: surface_mapper（REQ-V3.2.2-011/018/020/023）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-030 | merge CLI 默认落盘 input_surface.json（--out 可选）；stderr 输出落盘路径 | 已经完成开发 |
| SWR-V3.2.2-031 | merge_surfaces 产出 mirror_pairs（kept-first 冲突对，无序去重） | 已经完成开发 |
| SWR-V3.2.2-032 | tier 语言混合度只计 component_role=server-side | 已经完成开发 |
| SWR-V3.2.2-033 | language_inventory 运行时占比修正：core/scripts hint 且 runtime_files/file_count<0.1 → build-config | 已经完成开发 |
| SWR-V3.2.2-034 | scope snapshot/diff 子命令：git submodule status + .gitmodules 路径存在性；diff 输出 changed/changes/affected_dirs | 已经完成开发 |

## M5: r2_guard（REQ-V3.2.2-012/013/019）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-040 | drops CLI 双键归一（dropped 优先，drop 兜底） | 已经完成开发 |
| SWR-V3.2.2-041 | anchor_check 兼容 hit_sites[0] 回退；新增 anchor_check_all 批量检查（假设文件含 hypotheses 键时 CLI 自动批量） | 已经完成开发 |
| SWR-V3.2.2-042 | hypothesis_filter 模板 drop 条目 scope_dependent 字段 + 说明段 | 已经完成开发 |

## M6: batch_verify（REQ-V3.2.2-006/014/016/018/024）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-050 | IMPORTABILITY_STEPS 常量（python/c/cpp/go/rust/java/default）；_build_prompt 按 ctx language 分派步骤 0.5 | 已经完成开发 |
| SWR-V3.2.2-051 | 任务书例证脱敏（Newtonsoft.Json 先例→库型先例；Lersosa 例证→抽象形态；步骤 5.5 先例抽象化） | 已经完成开发 |
| SWR-V3.2.2-052 | collect: verdict≠REACHABLE 且带 claim → claim_type=null + claim_nulled_by 标记 | 已经完成开发 |
| SWR-V3.2.2-053 | _norm_hypothesis_id（H1↔H-1）；r4-collect/assert 双向归一 | 已经完成开发 |
| SWR-V3.2.2-054 | --from-journal 参数 + _extract_journal_verdicts（result/value 双字段，只采信 schema-validated） | 已经完成开发 |
| SWR-V3.2.2-055 | workflow-script 阶段：scope_snapshot 存在时输出 scope_changed + scope_advice | 已经完成开发 |

## M7: evidence_ledger（REQ-V3.2.2-020/030）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-060 | 门禁⑦ tracked_ids + mirror_pairs 镜像传播（计数型调用保持原语义） | 已经完成开发 |
| SWR-V3.2.2-061 | r4_feedback resolved 标记位（r4_feedback_resolved 队列字段，冲突按 (candidate,key) 抑制） | 已经完成开发 |

## M8: lessons_recorder（REQ-V3.2.2-015）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-070 | resurrection_review lenient：str→{revived:False, outcome:str}；list→{} | 已经完成开发 |

## M9-M10: harness（REQ-V3.2.2-008/009）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-080 | templates/harness/parser_fuzz_c.py（ASan+UBSan 包装/随机矩阵/截断形态/极值前缀） | 已经完成开发 |
| SWR-V3.2.2-081 | TEMPLATES 注册 parser_fuzz（langs c/cpp） | 已经完成开发 |
| SWR-V3.2.2-082 | resources/harness_coverage_matrix.json（claim × 语言 + coverage 摘要） | 已经完成开发 |

## M11: target_kind（REQ-V3.2.2-022）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-090 | listener/startup-chain 路径分域四类（nonproduct/libdir/examples/product）：product→app 2.0；examples-only→lib 0.8；libdir-only→lib 0.8；startup-chain 排除 nonproduct | 已经完成开发 |

## M12-M15: 资产脱敏与文档（REQ-V3.2.2-007/010/015/017/021）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-100 | precedent/checklist 运行时字段脱敏（12 处替换，追溯字段保留） | 已经完成开发 |
| SWR-V3.2.2-101 | VERDICT_SCHEMA claim_type enum（含 null）+ 语义注释 | 已经完成开发 |
| SWR-V3.2.2-102 | SKILL.md：R0 1.5 scope 快照步；R0 自检命令收敛 selfcheck；门禁⑦ coverage_bridge；R3.5-N 落盘契约 | 已经完成开发 |

## M16: tests（REQ-V3.2.2-010/040~043）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.2.2-110 | test_doc_lint.py：R0 命令单一事实源断言 + selfcheck 对非 fixture 项目真实执行 exit 0 + 三元组契约 | 已经完成开发 |
| SWR-V3.2.2-111 | test_signature_lib 契约更新：lang 必填/去项目化/完整性自检/fixture 锚点（4 新测 + 2 改造） | 已经完成开发 |
| SWR-V3.2.2-112 | tests/fixtures/known_instances.json 回归锚点库 | 已经完成开发 |
