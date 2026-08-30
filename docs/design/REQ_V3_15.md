# REQ V3.15 — 五项目批次收官缺陷修复（2026-08-30）

## 上下文

v3.14 在五项目验收批次（libarchive → s2n-tls → nghttp2 → gpac → freetype，
2026-08-30 收官）中暴露 14 项缺陷。全部经代码取证核实（本设计件各编辑点行号
为当前 dev 树实测），案例支撑全部来自批次会话内实录（各项目 lessons.md 与
队列/门禁输出），零凭记忆转述。按「审计复盘→缺陷修复版」惯例（v3.9 起同款）：
不改阶段骨架、六门禁判据语义、队列数据模型主体；每项过义务入库三问
（触发条件/消费者/案例支撑）。

验收硬性项（用户要求）：四缺陷评估（过设计/设计偏见/死代码/盲目带入历史
审计信息）随设计件交付（BIAS_EVAL_V3_15.md），每缺陷条目过四轴。

## 修复清单（14 项，按分层）

### P1 机械小修（未修缺陷）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | 报告防覆盖守卫判定「（主代理补充）」而机械模板第三节占位为「> 本段由主代理补充；…」（无全角括号标记）→ 未编辑重跑被 REFUSED（libarchive/s2n-tls/nghttp2/gpac 四项目四次实录） | 守卫双形态识别（「（主代理补充）」或「本段由主代理补充」），模板占位同步补标记 | tools/batch_verify.py:1704（守卫条件）、:2381 附近（模板第三节体） |
| D-2 | resurrect 采样池与门禁③c 判定函数不一致——池扫 (claim_type,evidence,summary,sink_type)，门禁扫 (claim_type,evidence,summary)（workflow_export.py:461-463 vs evidence_ledger.py:281-284）→ 三次漏选（s2n CAND-009/nghttp2 CAND-011/gpac CAND-011），主代理三次手写复核兜底 | 统一为单一 claim 判定函数：claim_type 字段优先命中 EMPIRICAL_CLAIMS，否则同字段集（claim_type+evidence+summary）文本扫描降级；两处调用同一函数 | workflow_export.py:450-470（resurrect_pool）、evidence_ledger.py:281-284（③c） |
| D-3 | r4-collect 对非法 verdict/severity 仅 warn，无结构化指引（nghttp2 H2/H4 产出 NO_REACHABLE_CONFIRMED/NOT_CONFIRMED/informational，主代理手工归一化两次） | warn 附结构化建议映射（verdict 非法→reviewed_clean 建议、severity informational→low 建议），不自动改写（D-4 先例：误猜风险>收益） | tools/batch_verify.py:999-1019（R4_ENUM_WARNING 构建） |
| D-4 | post-resurrect 强制复核静默空转——候选带旧 refutation 字段被 refutation 资格排除，导出器无提示（libarchive CAND-020/011 实录，主代理手工归档 refutation_history 才恢复） | 导出结果附 advisory：带 re_verify_gap 且 REACHABLE 且带陈旧 refutation 的候选清单 + 归档指引 | workflow_export.py:631-637（refutation 资格判定） |

### P2 结构修复 + 测试守卫补全（已热修复但无守卫）

| # | 缺陷 | 修复 | 编辑点 |
|---|---|---|---|
| D-5 | _truncate_evidence 全 minor 切净——证伪者收 0 字证据（gpac CAND-001/freetype CAND-002 同日双触发，热修首尾拼接兜底但 key 集未扩展、无测试） | key 集扩展：方括号段头（`[G\d+]/[PREC-*]/[CK-*]`）+ 平文 VERDICT: 头 + 「复活 gap 逐条核实」头；保留全 minor 首尾拼接兜底 | workflow_export.py:301-328（_TRUNC_KEY_HEAD + 分段逻辑） |
| D-6 | hypothesis_tracked_surfaces dict 富形态 → _tracked_ids unhashable 崩溃（gpac H2，热修提取 surface_id 但字段契约未化、无测试） | 契约化：canonical=字符串 id 列表；富形态改 sweep_records；_tracked_ids 容忍 dict 条目（保留热修）；两形态测试 | tools/batch_verify.py:1852-1860（_tracked_ids）、task_templates/biz_hypothesis.md（字段名条款） |
| D-7 | scope_diff changes 为字符串条目（生产者设计形态，docstring 明示「[描述]」），消费者原假定 dict（.get("path")）→ AttributeError（nghttp2 实录，热修 _chg_dir 解析字符串） | 消费契约化：消费者优先 diff.affected_dirs（机器通道），字符串解析降级 fallback；测试字符串/混合形态 | tools/batch_verify.py:2469-2495（scope_reopen_advice）、surface_mapper.py:1052（docstring 契约注） |
| D-8 | agent 自报落盘失真（gpac H2 通知称「tracked_surfaces 6/6 落盘」实际文件缺 canonical 字段，富形态写在非 canonical 字段）——门禁⑦机械核对兜住，任务书无 canonical 字段名指引 | biz_hypothesis 模板加一行：canonical 字段名与形态（tracked_surfaces=字符串 id 列表，富形态额外写 sweep_records） | task_templates/biz_hypothesis.md |

### P3 任务书义务强化（method 层，均过义务入库三问）

| # | 缺陷（批次实录） | 修复 | 编辑点 |
|---|---|---|---|
| D-9 | OOM/资源类实证无基线对照——gpac CAND-001「27,000x 放大」实为 ~105MB 环境启动基线伪影，真实增量 ~12MB，强制复核轮受控复现才拦截 | CK-EMPIRICAL-SCOPE steps 增「基线对照」条目：对照组（无攻击输入）+攻击组双测；资源类实证必须报告基线值/增量 | resources/checklist_library.json（CK-EMPIRICAL-SCOPE steps） |
| D-10 | 「守卫封顶」阻断主张只测拒绝路径——gpac CAND-007（avilib 短读守卫被真实内容文件绕过）/CAND-001（1MB 档经 AUTO→TCP_ONLY 自动切换）双例，复活波 2/2 推翻首轮 UNREACHABLE | 新 PREC-GUARD-SUBSET-001：阻断主张必须枚举守卫通过子集（文件真实包含声明尺寸/自动切换 tier/重试路径），写入自证伪提示库 | resources/precedent_library.json + precedent_library.py（匹配词） |
| D-11 | 第三方 vendored 解析器/绑定库契约建模缺失——llhttp 状态机死代码误判（nghttp2 CAND-002，复活者逐转移行推翻）、libcrypto 契约两次生效（s2n-tls X25519/DH） | 新 CK-VENDORED-CONTRACT：绑定依赖库契约检查列为阻断维度之一，注入 verifier/证伪者（经 checklist 绑定）+ 复活者维度清单一行 | resources/checklist_library.json + workflow_export.py（复活维度清单 ~483-487） |
| D-12 | 平台条件性候选未列未测平台——freetype CAND-002 的 32 位回绕唯一实证由复活者自发补测（强制 32 位类型重建+ASAN），verifier 未显式列「未实测平台」 | verifier 任务书 PTM 段加一行：平台条件性前提必须显式列未实测平台/构建清单，供复活波定向补测 | workflow_export.py（PTM 注入块 ~660-690） |

### P4 流程条款（SKILL.md/模板）

| # | 修复 | 编辑点 |
|---|---|---|
| D-13 | R1 铁律 3 补「多行 snippet 块匹配以首行键为锚」（libarchive 53/83 行号漂移根因） | SKILL.md R1 节 |
| D-14 | 域空签收路径模板化（freetype 网络域空数组+理由为 agent 自发行为，制度化：surface_map_domain 模板「域空时输出 {"surfaces":[]}+理由，主代理签收 empty_domain_reason」） | task_templates/surface_map_domain.md + SKILL.md R1 节 |

## 版本链 v3.15

- workflow_export.py:22 TOOLING_VERSION → "3.15"
- SKILL.md v3.15 增量段 + D-13/D-14 文案同步
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、test_v39.py:266 → "3.15"
- gen_tracking VERSIONS 登记 + REQUIREMENTS_TRACKING 手工段（禁 gen_tracking 再生成）

## 开发序列

- **C0**（本文档集）：REQ + SWR + SYSTEM_DESIGN + SOFTWARE_DESIGN + BIAS_EVAL
- **P1 机械小修**：D-1~D-4
- **P2 结构修复**：D-5~D-8
- **P3 任务书义务**：D-9~D-12
- **P4 流程条款**：D-13/D-14
- **P5 版本链+测试**：TOOLING 3.15 + SKILL.md 增量段 + 守卫 4 处 + tracking + test_v315.py + 全量回归 + 旧队列复跑零新增告警（gpac/freetype/protobuf 队列）+ install 双副本同步

## 测试守卫约束（取证已列）

- 必须保持绿：tests/test_v314.py 全量（v3.14 八用例）、test_v3102.py:125-139（D-1 相关 report 路径）、test_batch_verify_v3.py（collect/幂等）、test_evidence_ledger.py:66-221（六门禁名不增）、test_surface_mapper.py（scope_diff 字符串形态既有测试）
- 新增 tests/test_v315.py：D-1 守卫双形态（含未编辑模板重跑不 REFUSED）/D-2 统一判定函数两处等值（含 sink_type 字段差与否定语境词两用例）/D-3 建议映射输出/D-4 advisory 输出/D-5 截断矩阵（方括号段头保留/全 minor 首尾拼接/单段无 key 头）/D-6 tracked_surfaces 双形态/D-7 scope_diff 消费优先 affected_dirs/D-9/D-10/D-11 清单文本存在断言/D-14 空域模板文案

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q            # 基线 + test_v315 全绿
python3 signature_lib.py selfcheck <任一非 fixture 项目>   # 资产通用性不回退
# 旧队列复跑: gpac/freetype/protobuf 六门禁零新增告警 (统一判定函数后 ③c 语义不变)
# 禁止: python3 tools/gen_tracking.py
```

## 验收审计

按 REQ-V3.4-008 每版本需未审计新项目验收（补覆盖账本缺口格），项目待用户指派
（缺口格见各队列 B.6 覆盖账本：CRYPTO×{csharp,java,kotlin,...} 等 79 格）。
