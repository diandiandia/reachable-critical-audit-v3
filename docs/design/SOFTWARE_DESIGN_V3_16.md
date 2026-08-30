# SOFTWARE_DESIGN_V3_16 — 软件设计（2026-08-30）

函数级设计，编辑点行号为 dev 树 2026-08-30 实测。实现序 P1→P3。

## P1 机械

### D-1 gate ③ audit_constraint 建议（evidence_ledger.py:250-258）

```python
# 现有 violations.append({"gate": "empirical_required", ...}) 之后:
constraint = c.get("audit_constraint")
if constraint:
    violations.append({"gate": "empirical_required_constraint",
                       "severity": "warn", "id": c.get("id"),
                       "suggestion": {"kind": "batch_demote",
                                      "reason_template": (
                                          f"audit_constraint={constraint}: 实证类 claim 无实测支撑"
                                          " → 按 v3.3 条款降 NEEDS_REVIEW (证据不足/环境受限),"
                                          " 主代理逐条确认落盘, 不自动改写")}})
```
（violations 主条目保留阻断；建议条目 warn 级附在主条目后。）

### D-2 模板枚举强化（task_templates/biz_hypothesis.md:55/112 附近）

输出契约段与 canonical 示例行改为：
```
## 强制: 三选一 verdict —— **confirmed / reviewed_clean / not_applicable**
> 反面示例: REACHABLE/UNREACHABLE/NEEDS_REVIEW 是 R3 候选的 verdict，
> 不是本假说 verdict——写入这些值会被 r4-collect 报 R4_ENUM_WARNING。
```

### D-5 账本漂移 warn（tools/batch_verify.py:1516 写入后）

```python
# write 成功后:
_drift = _detect_ledger_copy_drift(_parent)
if _drift:
    print(json.dumps({"status": "LEDGER_COPY_DRIFT", "severity": "warn",
                      "note": "另一 skill 副本账本 sources 与本副本不一致——"
                              "双副本并集修复见 REQ_V3_16 D-5"},
                     ensure_ascii=False), file=sys.stderr)
```
`_detect_ledger_copy_drift(skill_dir)`：从 skill_dir 推导 sibling 副本路径
（dev ↔ installed 双活形态），存在且 sources 集合不等 → 返回 True。

## P2 内容

### D-3（resources/checklist_library.json CK-CHECKPOINT-AFTER-ACCUM steps）

```
"无界计数类候选的量级必须以对象图内部急切分配为准——枚举构造器链的成员
 缓冲/嵌套对象 (每 Stream 192KB 急切缓冲实录, 顶层对象尺寸低估 3-4 个
 数量级), 量级声明写最大成员分配"
```

### D-4（workflow_export.py:710-716 注入块后）

```python
prompt += ("\n多树/框架树目标必须显式列『树外层清单』: 绑定依赖库 / 框架语言层"
           " (如 Java 侧门禁) / 系统策略层 (如 SELinux 域) —— 阻断论证引用树外"
           " 门禁时须写层名与契约 (树外层不可枚举时如实注明)。\n")
```

## P3 版本链与测试

- workflow_export.py:22 → "3.16"；守卫 5 处测试行 → "3.16"
- SKILL.md v3.16 增量段（列 SWR-V3.16-001..005）
- gen_tracking VERSIONS 登记；REQUIREMENTS_TRACKING.md 手工追加 V3.16 段
- tests/test_v316.py 约 7 用例（清单见 REQ_V3_16）
- 全量回归 + gpac/freetype/av 队列门禁复跑零新增告警 + install 双副本同步
