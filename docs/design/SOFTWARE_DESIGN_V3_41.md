# SOFTWARE_DESIGN_V3_41 — 函数级设计 + 分层序列（v3.41）

## D-1（P1）gap 渲染字段分离 — src/workflow_export.py:810-818

```python
# 现状 (缺陷): gap = c.get("re_verify_gap"); if gap: ... + gap   → bool 拼接 TypeError
# 修复后:
gap_text = c.get("resurrect_gap") or ""
if c.get("re_verify_gap") or gap_text:
    prompt += ("\n\n## 复活复核 gap（主代理注入, REQ-V3.2-021）\n"
               "<段落前导文本>" + gap_text)
```
- `resurrect_gap` 为字符串契约（复活者 gap 原文）；`re_verify_gap` 保持 bool 语义（资格排除/advisory 消费点 675-707 不变）
- 两者皆缺失时：不渲染该段（现状 if gap 已保证，保留）
- 无新函数/无新字段（字段已在队列中被主代理写入，属既有数据契约的消费侧修复）

## D-2（P1）import 路径对齐 — tools/batch_verify.py:2210, 2553

```python
# 现状 (缺陷): sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 修复后 (与 545/1189/1458/1490/1724 同形):
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _parent)
sys.path.insert(0, os.path.join(_parent, "src"))
```

## D-3（P2）claim_type 枚举告警 — tools/batch_verify.py

- 常量区（1071 行附近）新增:
  `R4_CLAIM_TYPES = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos", "rce", "leak", "other", "null")`
  （与 verifier schema 枚举、R4 任务书枚举一致——双侧归一后等值比较）
- `_warn_r4_enums` finding 循环体（severity 检查后）新增:
  ```python
  ct = (fi.get("claim_type") or "")
  if ct == "":
      warnings.append({kind: "empty_claim_type", ..., suggestion: {"suggested": "null", ...}})
  elif str(ct).strip().lower() not in R4_CLAIM_TYPES:
      warnings.append({kind: "illegal_claim_type", ..., suggestion: {"suggested": "other", note: "source_fact/empirical_mechanism 类实证描述词 → other (无声称) 或按声称改枚举值"}})
  ```
- 只 warn 不改写；suggestion 为建议映射（纪律 #4）

## D-4（P3）步骤 4 方言矩阵条款 — tools/batch_verify.py verifier 任务书段

- 运行时版本条件 bullet 之后追加（提示级）:
  「- 方言/平台语义矩阵（v3.41, SWR-V3.41-004）: 阻断论证引用单一方言/平台
    实测时，须逐格核实同族方言/平台的语义差异（转义字符/引号/空值语义等）——
    单格实测不得外推到语义相异方言族；同库对照证据（各方言自身实现，如
    appendLiteral 系）是逐格核实的廉价锚点；外推必须显式标注覆盖格数」
- 无新义务字段、无新门禁（提示级）

## D-5（P3）checklist +1 — assets/resources/checklist_library.json

```json
{"id": "CK-CHANNEL-ESCAPE-LEDGER",
 "name": "转义责任下沉型设计的全通道对账",
 "family": "injection",
 "binding": {"cwe": ["CWE-89", "CWE-74", "CWE-116"],
             "keywords": ["appendFormat", "appendSql", "escape", "转义", "literal", "comment", "hint", "quote"]},
 "steps": ["同一函数族全部宿主文本通道（注释/提示/字面量/标识符/格式模式类）逐条列渲染点与转义点",
           "单通道防御 ≠ 全族防御：一条通道有转义而兄弟通道没有即假设（不对称缺陷）",
           "渲染分支逐个枚举：字面量化路径（QueryLiteral/appendLiteral）之外的直出分支（硬编码引号包裹）是最常被漏的通道"],
 "source_lessons": ["2026-09-12 hibernate-orm: comment 有转义/hint 无/format 非复合路径绕过 appendLiteral (CAND-006 复活)"]
}
```

## D-6（P3）precedent +1 — assets/resources/precedent_library.json

```json
{"id": "PREC-ESCAPE-HATCH-EQUIV",
 "title": "逃生舱等价性: 与既有无校验通道等价的 sink 零能力增量",
 "cwe": ["CWE-89"],
 "rule": "逃生舱类 sink（如 function('sql 片段')）与库内既有无校验通道（如原生 SQL 透传 createNativeQuery）语义等价的形态, 不立候选/归宿主 API 设计内能力边界; 边界论证本身写入申报材料",
 "source_lessons": ["2026-09-12 hibernate-orm CAND-005 复活实录: safe mode 默认关 + function('sql') 等价 createNativeQuery 零能力增量"]
}
```

## D-7（P3）矩阵 seed — language_issue_matrix.py seed_entries

- java×MEMORY-SAFETY: patterns=越界索引/截断 cast（枚举 ordinal 下标无界、long→int 窄化静默错值、文本构造器绕过校验门禁）; sinks=enumConstants[ordinal]/intValue() 窄化/parse 后下标; pitfalls=JVM 边界检查把后果限制为 AIOOBE/异常但静默错值无告警; source_lessons 去项目化+日期追溯
- java×TRUST-BOUNDARY: patterns=白名单 fail-open（URI 解析失败即放行、字符串拆分路径绕过门禁）; sinks=scheme 白名单判定点/前缀校验点; pitfalls=守卫实现与解析器语义不等价（严格 URI vs 词法 scheme 检测）; source_lessons 去项目化+日期追溯

## 分层序列与提交分组

1. `v3.41 C0: 设计五件套`（本目录）
2. `v3.41 P1-P2: gap 渲染字段分离 + 报告 import 路径对齐 + claim_type 枚举告警`（D-1/D-2/D-3 + test_v341 三守卫）
3. `v3.41 P3: 方言矩阵条款 + 清单/先例各一 + java 矩阵两格`（D-4/D-5/D-6/D-7 + 守卫）
4. `v3.41 P4: 版本链`（TOOLING 3.41 + 守卫行 + SKILL.md 增量段 + REQUIREMENTS_TRACKING 手工段 + 计数同步）
