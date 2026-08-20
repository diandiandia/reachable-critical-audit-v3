# Reachable Critical Audit v3.4.3 — 软件设计（组件级）

> 从 `SYSTEM_DESIGN_V3_4_3.md` 导出的组件修改设计。日期：2026-08-20
> 最高判据：SKILL.md「第一原则：通用型 Skill」——本版全部组件修改都必须通过
> 自检四问（去项目名 / 语言无关或按 lang 分派 / 无具体项目路径 / 新项目验收）。
> 版本主题：**缺陷闭环**——P0/P1/P2 暴露的 17 项缺陷（12 代码 + 5 制度）就地制度化。

## 组件影响清单

| 组件 | 修改点 | 承载 REQ |
|---|---|---|
| M1 tools/batch_verify.py | ①stage_r4_collect schema 自适应解包（四类漂移：hypotheses 对象形态 / findings 顶层数组 / evidence 数组 join / r3_link dict 展平；severity capitalize；归一化写 schema_normalized_by；0 提取告警含形态诊断）②tracked_surfaces 前缀模糊映射（未知 id 按 SURF-DAT-*↔SURF-DATA-* 等规则映射到已知 id 后才告警）③新命令 `--mode resurrect`（转调 workflow_export.export_script_resurrect）④新命令 `--stage r35n-collect --from-journal <dir>`（落盘候选级 resurrection_review dict，对齐 REQ-V3.2.2-015） | REQ-V3.4.3-001/002/007 |
| M2 evidence_ledger.py | ①gate ③b 结构判定优先：empirical_result 非空 + 实证特征（数字/命令输出/exit code 正则）判为有实证，关键词（实证/已实证/confirmed/**实测/measured**）仅 fallback ②grade 判定文档对齐：collect 侧直接调用机械重算的约定写入注释（行为在 M1/M3） | REQ-V3.4.3-004/005 |
| M3 workflow_export.py | ①resurrect_prompt 截断协议统一（1200 字符静默截断 → 分级截断：关键段必保留，次要段带标记「[截断: 全文 N 字符, 见 verify_queue.json]」；与 refute_prompt 共用同一截断函数）②export lang 推断优先读候选 lang 字段（候选级分片），回退语言清单 ③VERDICT_SCHEMA claim_type 枚举加 "leak"（refute_prompt 工具箱同步） | REQ-V3.4.3-003/006/011 |
| M4 surface_mapper.py | ①merge 时 surface id 前缀归一化（SURF-DAT-* → 域标准前缀；归一化映射写 merge 元数据 normalized_ids）②BOUNDARY_KINDS 加 "capi"（通用 C-API 扩展词，覆盖 Python C-API/Lua C-API/N-API） | REQ-V3.4.3-002/008 |
| M5 checklist_binder.py + precedent_library.py | ①checklist_binder 复用 applicability_signals（text/requires_lang/requires_claim 形态）过滤：候选 evidence/sink 上下文不匹配 → 不绑定；无匹配时绑通用资源类清单（新增 CK-GENERIC-RESOURCE）或空 ②_self_refutation_section（workflow_export 内）同款 signals 过滤 ③先例库 +1 条：PREC-FAMILY-CONSISTENCY-001（跨项目同族裁决判据：放大比是否常数因子 × 物化责任在库侧还是宿主侧） | REQ-V3.4.3-009/012 |
| M6 task_templates/biz_hypothesis.md | ①R4 任务书注入实际 surface id 清单（模板占位符 {surface_id_list}，主代理导出时填充）②附 canonical 输出示例段（列表形态 + 单 finding 完整字段示例）③H7 默认值全表预算 800→1200 字 | REQ-V3.4.3-002/010 |
| M7 SKILL.md | ①R4 收集段加同事实去重流程（title 同事实 → r3_link 标共享实证，主申报方承载 severity）②兼容回填规范条款（backfilled_by + 实测数字，v3.4.2 兼容模式文档化）③claim_type 枚举表加 "leak" ④契约同步（本版全部 SWR） | REQ-V3.4.3-012/006/004 |
| M8 harness_manuals/go.md + c.md | 陷阱清单追加：pgrep -f 自匹配（fd 计数用 /proc/<pid>/fd）；ss 缺失替代（netstat/lsof）；CLI 密码交互静默挂起（stdin 喂空）；getrusage 替代 /usr/bin/time | REQ-V3.4.3-012 |
| M9 tests/ | 全 REQ 的回归测试（见 SWR M9 表）：schema 自适应四形态、前缀映射、r35n-collect、截断标记、grade 自报字段、gate 结构判定、leak 枚举、capi 校验、signals 门控、lang 优先、H7 预算模板 | REQ-V3.4.3-001..012 |

## 数据模型变更

1. verify_queue 候选新增 `grade_self_reported` 字段（collect 时存 verifier 自报值；机械重算结果仍写 evidence_grade + grade_recomputed_by）——旧队列无此字段，读取用 .get
2. r4_findings 条目新增 `schema_normalized_by`（自适应归一化标记，仅当发生归一化时写）
3. merge 元数据新增 `normalized_ids`（surface_mapper merge 的前缀归一化映射）
4. claim_type 枚举 +"leak"；BOUNDARY_KINDS +"capi"；checklist_library +CK-GENERIC-RESOURCE；precedent_library +PREC-FAMILY-CONSISTENCY-001
5. 无 schema_version 变更（全部向后兼容，读取侧 .get 兜底）

## 兼容性

- 六门禁①-⑧判据不变；assert_ledger 签名不变；旧队列豁免路径（require_target_kind/require_resurrection=False）不变
- r4-collect 自适应只对**非 canonical 形态**生效；canonical 输入零变化（回归锚：P2 四项目已落盘的 _r4_merged.json 复跑结果不变）
- gate ③b 结构判定是**放宽误报**（原误报场景转 PASS），不引入新拦截——已有 PASS 队列零回退
- claim_type "leak" 仅新增枚举值；旧队列 claim_type=other 的 leak 类候选不自动改写（记录型处理）
- resurrect CLI 与既有 workflow_export 直调路径并存；r35n-collect 对已落盘 resurrection_review 的候选幂等跳过

## 实施顺序

| 步骤 | 内容 | 依赖 |
|---|---|---|
| 1 | M4 前缀归一化 + capi（上游根因先行） | 无 |
| 2 | M3 截断协议 + lang 优先 + leak 枚举 | 无（与 1 并行） |
| 3 | M1 r4-collect 自适应 + 前缀映射 + resurrect CLI + r35n-collect | 1-2 |
| 4 | M2 gate ③b 结构判定 + grade 文档对齐 | 3 |
| 5 | M5 signals 门控 + 先例条目 | 无（与 2-4 并行） |
| 6 | M6 任务书（surface id 清单注入 + canonical 示例 + H7 预算） | 1 |
| 7 | M7 SKILL.md 制度四项 + 契约同步 | 1-6 |
| 8 | M8 手册陷阱 | 无（与 7 并行） |
| 9 | M9 测试 + 全量回归 + 三锚点复跑 + 新项目验收 + install | 1-8 |
