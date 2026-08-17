# Reachable Critical Audit v3.1 — 软件设计文档（Software Design）

> **文档性质**：满足 `REQ_V3_1.md` 系统需求的软件级设计（v3.1 增量）。定义新增/变更模块的
> 分解、接口签名、关键算法、数据流。软件开发需求（SWR-V3.1-xxx）由此文档导出，见 `SWR_V3_1.md`。
> v3 基线的模块设计见 `SW_DESIGN_V3.md`——本文档只描述 v3.1 增量。
> **日期**：2026-08-17

## 1. v3.1 模块增量总览

```
v3 基线 (SW_DESIGN_V3.md)                        v3.1 新增/变更
┌──────────────────┐        ┌───────────────────────────────┐
│ M1 surface_mapper │──变更──▶ +repair 修复器/+tier 档位/       │
│ M2 signature_lib  │──变更──▶ +三层 tier/L1 退役/贡献度        │
│ M3 signature_m    │──变更──▶ +tier 消费(L1 零假设)            │
│ M4 evidence_ledger│──变更──▶ +lenient/标记提取/一致性断言/     │
│ M5 harness_runner │──变更──▶ +手册装载/范围分级/陷阱自检/      │
│ W1 workflow_export│──变更──▶ +resume 防御/lint/工具箱/清单注入 │
│ M9 task_templates │──变更──▶ +verifier v3.1/biz v3.1/filter   │
└──────────────────┘        └───────────────────────────────┘
       新增: M10 checklist_binder.py（清单绑定）
       新增: M11 precedent_library.py（先例检索+自证伪提示）
       新增: M12 r2_guard.py（假设 schema 守卫: surface_ids/锚点/落盘）
       数据: resources/precedent_library.json / checklist_library.json
             harness_manuals/<lang>.md × 15
```

| 模块 | 职责 | 覆盖 REQ-V3.1 |
|---|---|---|
| M1+ surface_mapper | repair 修复器/tier 档位/project_kind | 020-027, 010 |
| M2+ signature_library | 三层 tier/退役区/runtime_prereq/贡献度 | 004, 005 |
| M3+ signature_matcher | tier 消费（L1 不生成假设） | 004 |
| M4+ evidence_ledger | lenient/单遍转义/实证标记提取/一致性断言/correction schema/gate③→R4 | 045, 052, 053, 081, 090, 091 |
| M5+ harness_runner | 手册装载/范围分级强制/陷阱自检/对照矩阵/源事实级降级 | 070-076 |
| M10 checklist_binder | 结构化绑定（cwe/keywords/verdict_context） | 041, 042 |
| M11 precedent_library | 先例检索/自证伪提示生成/回填 | 006, 007, 043 |
| M12 r2_guard | 假设 schema 守卫（surface_ids 数组/锚点行/keep-drop 落盘） | 030-033 |
| W1+ workflow_export | resume 防御/lint_script/工具箱/清单注入/strengthened | 050, 055, 080, 082, 083 |
| M9+ task_templates | verifier v3.1（步骤0+清单+自证伪）/biz v3.1（tracked_surfaces+H7 模板）/filter v3.1 | 040, 060-064 |

## 2. M1+ surface_mapper v3.1 增量

```python
# 已有 (v3 基线): normalize/validate/merge/gen_surface_tasks/build_architecture_context
# v3.1 新增:

def size_tier(project_root: str) -> dict:
    """SWR-V3.1-001: 规模自适应档位。源码文件计数（CODE 扩展名白名单，
    排除 .git/node_modules/.venv/target/build）→
    {tier: small|medium|large, agent_count, time_limit_min, checkpoint_every_min,
     domains_split, rationale}。
    small: <100 文件 2 agents（network+data / process+storage 双分域）
    medium: 100-500 文件 4 agents 无限时
    large: >500 文件 4 agents + 45min 硬时限 + 10min 中间产物落盘"""

def repair_surfaces(data, project_root=None) -> tuple[dict, dict]:
    """SWR-V3.1-002/003: 行号漂移自动修复器。
    算法（单遍，幂等）:
      1. normalize（相对路径→绝对）
      2. 逐 entry: 已有 suggested_line/paraphrased → 跳过（幂等契约 W6 §9.5）
      3. ±2 主窗口折叠空白包含匹配 → 命中则不动
      4. 未命中: 首行键（多行 snippet 首行 [:50]）全文件匹配（±80 语义）
         - 唯一命中 → ep['suggested_line']=旧行号; ep['line']=命中行; stats.fixed++
         - 零命中 → ep['paraphrased']=True; stats.paraphrased++（主代理必须人工复核）
         - 多命中 → 不动（stats.unchanged++，留给主代理裁决）
    返回 (repaired_data, stats{fixed,paraphrased,unchanged})"""

def _classify_project_kind(root, ctx) -> str:
    """SWR-V3.1-004: 项目形态判定 framework|library|infra|app。
    依据: 构建文件类型（Gemfile/Cargo.toml/Package.swift 等 → framework;
    Makefile/CMakeLists 且无框架文件 → infra; 否则 app）"""
```

validate 增量（SWR-V3.1-005）：双态匹配已有；新增首行键 fallback 与 paraphrased 标记
（与 repair 共用匹配逻辑）；相对路径解析已有（normalize）。

## 3. M2+/M3+ signature_library 三层重构

```json
{
  "tier": "L1|L2|L3",
  "runtime_prereq": null | {"runtime": "ruby>=3.2", "effect": "Oniguruma 线性化, ReDoS 先验下调"},
  "contribution": {"batches_seen": 3, "hypotheses_contributed": 0, "last_batch": "sinatra"},
  "retired_signatures": [{"sig_id": "...", "retired_at": "...", "reason": "连续 2 批次贡献度<10%"}]
}
```

- **L1 通用危险词**（append/encode/join/::class 类）: signature_matcher 命中 → 仅作
  verifier 上下文提示，不生成假设（SWR-V3.1-051）
- **L2 语言词族 / L3 框架语义族**: 生成假设（v3 基线行为）
- matcher 输出附 tier; r2_filter 统计贡献度（hypothesis.sources）回填（SWR-V3.1-052）

## 4. M4+ evidence_ledger v3.1 增量

```python
def load_lenient(path) -> dict:
    """SWR-V3.1-010: lenient JSON load + 单遍转义修复。
    算法（W6 §3.1-3.3, 单遍不重审防振荡）:
      扫描 JSON 文本, 字符串内遇 '\\':
        - 后接合法转义（"\\/bfnrt）→ 原样保留
        - 后接 'u' 且 4hex → 原样保留（'\\user' 不满足 → 走非法分支）
        - 否则 → 双写 '\\\\' + 原样附加下一字符, 跳过（不重审下一字符）
    幂等性: fix(fix(x)) == fix(x)（测试断言）"""

def _fix_escapes_single_pass(text) -> str: ...

def extract_empirical_marker(v) -> dict|None:
    """SWR-V3.1-011: 从 evidence 文本提取实证标记（实测/实证/empirically/harness/
    rack-test/cargo test/curl/e2e/端到端/probe/pytest）→ empirical 字段
    {status: marker_found_unverified, markers[], extracted_by}。
    不自动升级 grade（升级需 status ∈ CONFIRMED_EMPIRICAL_STATUSES, §17.7 范围纪律）"""

def consistency_check(queue) -> list[Issue]:
    """SWR-V3.1-012: 同族一致性断言（PREC-CONSISTENCY-001）。
    按 (source_file, sink_type) 分组; 组内 REACHABLE 与 UNREACHABLE 并存且
    任一路径均无 blocking_point/correction_record/r35_adjudication 解释 → warn"""

def check_correction_schema(queue, precedent_lib=None) -> list[Issue]:
    """SWR-V3.1-013: correction_record schema 校验。降级裁决无 correction_record
    落盘 → warn; 引用未知 precedent_ids → warn"""

def grade_verdict(v):  # 变更: empirical.status ∈ CONFIRMED_EMPIRICAL_STATUSES 才升 empirically_confirmed
def assert_ledger(q):  # 变更: + gate empirical_required_r4（R4 findings 同受 gate③）
```

## 5. M10 checklist_binder.py（新组件）

```python
DEFAULT_LIB = resources/checklist_library.json

def bind(candidate, lib=None) -> list[tuple[str, list[str]]]:
    """SWR-V3.1-020: 结构化绑定。binding 形态:
      dict: {cwe:[...], keywords:[...], verdict_context?, applies_to_phase?}
        - cwe 并集（candidate.cwe 解析 str/list 两形态）
        - keywords 任一命中（斜杠/顿号拆备选, 任一词项子串匹配 candidate
          summary/sink_type/snippet/title/claim 文本）
        - verdict_context 不匹配当前 verdict → 不绑定
        - applies_to_phase=R5 → 不自动绑定（R5 显式）
      str: 兼容旧格式（引号/『』/括号提取 + cwe∈{} 提取）"""

def bind_all(queue, lib=None) -> queue:  # checklist_ids 写回（不覆盖已有）
def h7_template_bind() -> list[str]:     # H7 固定绑定: DEFAULT-VALUE-TABLE/DEFAULT-3LAYER/SENTINEL-SEMANTICS
```

## 6. M11 precedent_library.py（新组件）

```python
DEFAULT_LIB = resources/precedent_library.json

def load() -> dict:
def match(candidate) -> list[dict]:
    """SWR-V3.1-030: 按候选前提形态检索先例。
    匹配键: cwe 家族（Host 采信族 CWE-436/601 → HOST-FAMILY/VICTIM-TRIGGER 等）、
    summary 关键词（默认/gate → DEFAULT-3LAYER; 引擎 → ENGINE-MATRIX;
    能力/前提 → CAPABILITY; 文档 → DOC-DESIGN）、claim_type。
    命中先例的 criterion 与 counterexample 都返回（counterexample 是适用性反查）"""

def self_refutation_hints(candidate) -> list[str]:
    """SWR-V3.1-031: 自证伪提示生成。取 match() 命中的先例 criterion,
    模板化为『最可能的证伪论据』列表（每候选 ≤2 条），注入 verifier 任务书"""

def record_application(precedent_id, application: dict) -> None:
    """SWR-V3.1-032: 审计后回填 applications[]（库随审计进化, 幂等按 application id）"""

def add_precedent(precedent: dict) -> None:  # 主代理自由裁量后回填新先例（schema 校验）
```

## 7. M5+ harness_runner v3.1 增量

```python
EMPIRICAL_SCOPES = ("mechanism", "function_body", "full_chain", "e2e")

def load_manual(lang) -> str:
    """SWR-V3.1-040: 装载 harness_manuals/<lang>.md 要点注入实证任务书"""

def check_scope(candidate) -> list[str]:
    """SWR-V3.1-041: 范围分级强制。empirical 存在时:
      - scope 必填且 ∈ EMPIRICAL_SCOPES, 缺 scope_note → 违规
      - scope=mechanism 且 evidence_grade=empirically_confirmed → 违规
        （机制级只能支撑 edge_proven, W6 §17.7）"""

def env_trap_checklist(lang) -> list[str]:
    """SWR-V3.1-042: 环境陷阱自检清单（按语言手册）:
      stale 进程清理 + diag 路由自检 / daemon 采样线程 / env 传播验证
      (comm 验证 PID) / PATH 检查 / 测量点放服务端 / 语义前提先验证"""

def contrast_matrix_prompt(target) -> str:
    """SWR-V3.1-043: 对照矩阵实证模式（默认配置拒绝 + 弱化配置接受）模板"""

def source_fact_rule(candidate, blocker: str|None) -> str:
    """SWR-V3.1-044: 源事实级降级。网络阻断 → source_fact + blocker 记录;
    哨兵值/算术类主张（claim_type ∈ sentinel/arithmetic）接受源事实级"""
```

## 8. M12 r2_guard.py（新组件）

```python
def validate_hypothesis(h, surface_ids_known) -> list[str]:
    """SWR-V3.1-050: surface_ids 强制数组（单值/缺失 → 拒收）;
    surface_id 必须存在于 input_surface.json"""

def anchor_check(hypothesis, project_root) -> dict:
    """SWR-V3.1-051: 锚点行验证。Read 源文件行, 匹配 doc block/注释/空行
    （//!、/*、#、--、''' 开头）→ 拦截标记 anchor_invalid"""

def audit_filter_drops(kept, dropped) -> dict:
    """SWR-V3.1-052: keep/drop 全量落盘（dropped_by + reason 必填）"""
```

## 9. W1+ workflow_export v3.1 增量

```python
REFUTATION_SCHEMA:  # + strengthened/attribution_correction/note
VERIFY_SCRIPT/REFUTATION_SCRIPT:  # + args 缺失防御（resume 契约 W6 §5）
def lint_script(js) -> list[str]:   # 顶层 const 模板 `${}` 检查（W6 §17.2）
def refute_prompt(c, idx):          # + 工具箱注入（interval/parser/proxy 三类）
def export_script(...):
    # v3.1: verify payload 构建时调用 checklist_binder.bind + precedent.self_refutation_hints,
    # 注入逐候选 prompt（清单步骤 + 自证伪提示, SWR-V3.1-060/061）
    # next_step 附规范条款: args 整读整传/resume 一致/result|value 双字段/半程作废
```

## 10. M9+ 任务书模板 v3.1 增量

- `task_templates/verifier_edge_proof.md`（已完成）: 步骤 0 承重前提 + 清单执行记录段 +
  自证伪自查段 + 轻量实证白名单 + 实证范围纪律
- `task_templates/biz_hypothesis.md`（未开发）: + tracked_surfaces 强制（SURF- 前缀 id）+
  r3_link + empirical_result/mechanism_correction + H7 默认值全表模板（五维 × 每默认值）
- `task_templates/hypothesis_filter.md`（未开发）: + surface_ids 数组 + sources 字段 +
  boundary-confirmation 单独归类 + keep/drop 落盘义务

## 11. R0 门禁修正与报告模板

- R0 smoke 门禁: `hit_rate < 1.0 AND testable > 0` 才阻止（W6 §7）——修改 smoke 判定
  逻辑（SWR-V3.1-070）
- 报告模板条款（SKILL.md 承载）: NEEDS_REVIEW ↔ R4 同事实映射表 + 条件式 REACHABLE
  前提逐条列出（SWR-V3.1-071）
