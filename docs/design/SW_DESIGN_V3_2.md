# Reachable Critical Audit v3.2 — 软件设计文档（Software Design）

> **文档性质**：满足 `REQ_V3_2.md` 系统需求的软件级设计（v3.2 增量）。
> v3.1 基线的模块设计见 `SW_DESIGN_V3_1.md`——本文档只描述 v3.2 增量。
> 软件开发需求（SWR-V3.2-xxx）由此文档导出，见 `SWR_V3_2.md`。
> **日期**：2026-08-17

## 1. v3.2 模块增量总览

```
v3.1 基线                                    v3.2 增量
┌──────────────────┐        ┌───────────────────────────────────┐
│ M1+ surface_mapper│──变更──▶ +language_inventory/+boundary 域/    │
│ M3+ signature_m   │──变更──▶ +L2 词族按 surface.lang 过滤        │
│ W1+ workflow_exp  │──变更──▶ +R3.5-N 复活攻击模式                │
│ M4+ evidence_ledg │──变更──▶ +R3.5-N 门禁/一致性按 lang 分组     │
│ M5+ harness_runner│──变更──▶ +混合项目多组件构建提示              │
│ M11 precedent     │──变更──▶ +PREC-MULTI-LANG/lang 维度 match    │
│ M12 r2_guard      │──变更──▶ +假设 schema lang 字段              │
└──────────────────┘        └───────────────────────────────────┘
       资产: checklist 第 21 条 CK-FFI-BOUNDARY
             precedent 第 21 条 PREC-MULTI-LANG-001
             harness_manuals/mixed_build.md（混合构建总纲）
```

| 模块 | 职责 | 覆盖 REQ-V3.2 |
|---|---|---|
| M1+ surface_mapper | language_inventory/boundary 域/lang 字段 | 001-003, 010 |
| M3+ signature_matcher | L2 词族 lang 过滤 | 004 |
| M10 checklist_binder | CK-FFI-BOUNDARY 绑定（语言无关保持） | 012 |
| M11 precedent_library | PREC-MULTI-LANG + lang 维度 match | 013 |
| W1+ workflow_export | R3.5-N 复活攻击模式 | 020-022, 024 |
| M4+ evidence_ledger | R3.5-N 门禁 + 一致性按 lang 分组 + 分级条款 | 023, 013, 030 |
| M5+ harness_runner | 候选.lang 手册装载 + 混合构建提示 | 005 |
| M12 r2_guard | lang 字段校验 | 002 |
| 资产 | checklist/precedent 第 21 条 + mixed_build.md | 012-014 |

## 2. M1+ surface_mapper v3.2 增量

```python
def build_architecture_context(project_root) -> ctx:
    # 新增: language_inventory
    # 算法: CODE_EXTENSIONS 计数 → {lang: {file_count, dirs}};
    # component_hint 启发式: 绑定层目录名 (bindings/ffi/ctypes/ext/csrc/native)/
    # 头文件目录 (include/) / 脚本目录 (scripts/) → "bindings|core|frontend|scripts"
    # 单语言项目 inventory 长度 1 (向后兼容: lang 字段仍输出)

def gen_surface_tasks(project_root, ctx) -> tasks:
    # 新增第 5 域 boundary:
    #   guide = "跨语言 FFI 边界: extern \"C\"/ctypes/cffi/N-API/JNI/CPython 嵌入/JS addon"
    #   任务书附 language_inventory 全表 + 每语言分片背景
    #   boundary 域 output_schema 增加 boundary_kind 枚举 + 调用方向
    # 4 域任务书 architecture_context 改按语言分片 (每语言组件摘要段)

def normalize_surfaces(data, project_root):
    # surface/entry_point lang 字段透传 + 默认从 project 主语言继承
def validate_surfaces(data, project_root):
    # boundary surface 必填 boundary_kind; lang ∈ language_inventory 或 "unknown"
def size_tier(project_root):
    # 混合项目 tier 判定: 文件总数不变; 新增 languages>2 时 large 档保底
```

## 3. M3+ signature_matcher v3.2 增量

```python
def match_signatures(surfaces, signatures, project_index, depth=DEFAULT_DEPTH):
    # v3.2: L2 词族按 surface.lang 过滤
    # for sig in signatures:
    #   if sig.get("tier") == "L2" and sig.get("lang") and surface.lang != sig["lang"]:
    #       continue   # C 词族不打 Rust surface
    # Hit 增加 lang 字段
```

## 4. W1+ workflow_export v3.2 增量（R3.5-N 复活攻击）

```python
RESURRECT_SCHEMA = {"type": "object",
  "required": ["id", "revived", "reason"],
  "properties": {"id": {"type": "string"},
                 "revived": {"type": "boolean"},   # true = 清除判定被推翻
                 "reason": {"type": "string"},
                 "gap": {"type": "string"}}}        # 枚举到的 verifier 缺口

def resurrect_pool(queue, batch_size):
    """REQ-V3.2-020 抽样规则:
    (1) 声称类 UNREACHABLE (claim_type 匹配 EMPIRICAL_CLAIMS 或其 evidence
        含 unbounded/oom/xss 等) → 全量;
    (2) 其他类 UNREACHABLE → 20% 抽样, 最少 2, 上限 8;
    已有 resurrection_review 的候选排除 (多波不重复)。"""

def resurrect_prompt(c):
    """尽力复活任务书: 默认立场 = 找到一条 verifier 未枚举的阻断缺口或错误前提
    即 revived=true; 枚举维度: 阻断是否覆盖全部攻击者可控维度/前提三层语义/
    死代码豁免是否误用/平台前提是否有实证。"""

REFUTATION_RESURRECT_SCRIPT:  # N=1, pipeline over args.candidates
    # decisions: {id, revived, reason, gap}
    # note: revived=true 由主代理回 R3 重验 (附复活者证据), 不直接改 verdict
```

## 5. M4+ evidence_ledger v3.2 增量

```python
def consistency_check(queue):
    # 变更: 分组键 (source_file, sink_type) → (source_file, sink_type, lang)
    # 跨语言同 sink 形态不触发一致性告警 (PREC-MULTI-LANG-001)

def assert_ledger(queue, ...):
    # 新增 gate resurrection_required:
    #   声称类 UNREACHABLE 且无 resurrection_review → 违规 (REQ-V3.2-023)
    #   (resurrection_review 由主代理在 R3.5-N 后落盘)

def grade_verdict(v):  # 不变 (分级机械复核条款化在 SKILL 流程层, 见 §7)
```

## 6. 资产 v3.2 增量

### checklist_library.json 第 21 条

```json
{"id": "CK-FFI-BOUNDARY", "name": "跨语言 FFI 边界检查",
 "family": "ffi-boundary",
 "binding": {"cwe": [], "keywords": ["ffi", "ctypes", "extern", "jni", "n-api", "cffi", "绑定", "所有权", "addon", "嵌入"]},
 "applies_to": ["verifier", "H4"],
 "steps": [
   "边界调用方向与所有权转移方向（哪侧分配/哪侧释放）",
   "unsafe 桥接不变量逐条验证（指针有效性窗口/生命周期）",
   "ABI 与结构体布局两侧一致性（打包/对齐/枚举值）",
   "跨语言内存释放责任（ctypes 指针 vs 原库分配器）",
   "引用计数对称性（嵌入场景：借出/归还配平）",
   "跨语言序列化格式一致性（两侧编解码器版本/默认值分歧）"
 ]}
```

### precedent_library.json 第 21 条

```json
{"id": "PREC-MULTI-LANG-001", "name": "多语言裁决分组",
 "criterion": "同 sink 家族一致性断言按 lang 维度分组——裁决按每个组件所属语言的生态惯例分别进行（Rust 侧按内存安全先例、C 侧按缓冲区先例、动态语言侧按注入先例）；跨语言组不强制一致",
 "counterexample": "同 lang 组内的同 sink 形态仍强制一致性（v3.1 §18.3 先例继续生效）",
 "applicability_scope": "混合语言项目（language_inventory 长度 ≥2）"}
```

### harness_manuals/mixed_build.md

混合项目构建总纲：组件级构建矩阵（每组件 {lang, build_cmd, 产物, 测试入口}）、
跨语言实证编排（宿主进程 + 动态库加载）、FFI harness 模板（ctypes 驱动 C 核心 /
cargo cdylib + Python 导入）。

## 7. 流程条款变更（SKILL.md 承载，无代码）

- **分级机械复核条款**（REQ-V3.2-030）：R3 collect 后必须对全部 REACHABLE 跑
  `evidence_ledger.grade_verdict` 重算；verifier 任务书加注"evidence_grade 是证据
  的机械函数，非自我评估——证据齐全自标 static_only 会被机械升级"。
- **R3.5-N 编排**：R3.5 REACHABLE 复核完成后 → workflow-script --mode refutation-resurrect
  → decisions 落盘 → revived=true 候选回 R3 重验（新 attempt，附复活者 gap）。
