# SOFTWARE_DESIGN_V3_42

函数级设计 + P 分层序列。全部编辑点行号为取证实测值（2026-09-13）。

## P1 机械

### D-1 workflow_export.py refutation 资格判定

```python
# 新增 helper（模块级，紧邻 export_script 前）
def _has_refutation_result(c):
    """refutation 为 dict 且含 votes 或 summary 才视为已复核。
    空 dict / 仅签收字段 (strengthened_verified_by 等) = 未复核
    (SWR-V3.42-001: 键存在语义曾致静默空转, 主代理签收脚本 setdefault
    形态实录)。"""
    r = c.get("refutation")
    return isinstance(r, dict) and ("votes" in r or "summary" in r)

# export_script mode == "refutation" 分支 (~:700):
#   qualified 判定 "refutation" not in c → not _has_refutation_result(c)
#   空转分支 (~:720 WORKFLOW_NOTHING_TO_DO 处) advisory 追加:
#   empty_refutation_keys = [c["id"] for c in candidates
#       if c.get("verdict") == "REACHABLE" and "refutation" in c
#       and not _has_refutation_result(c)]
#   (空列表时不输出该字段)
```

### D-2 batch_verify.py r4-collect diagnosis

```python
# R4_COLLECT_WARNING 的 diag 构造处 (~:1308):
#   在现有 diag 后追加:
#   near_keys = [k for k in (items[0] if items else {}).keys()
#                if k in ("hypothesis", "hypothesisId", "hypID")]
#   若 near_keys 且无 "hypothesis_id" in items[0]:
#     diag += f" [字段名提示: 检测到近似键 {near_keys}, 预期 hypothesis_id]"
```

## P3 内容（提示级，全部去项目化表述）

### D-3 verifier 任务书（_build_prompt verifier 段，步骤 0 承重前提验证后）

追加段：
```
### 分支级声称标注（v3.42, SWR-V3.42-003, 提示级）
证据中的**分支级声称**（isAbsolute/fallback/else-branch/条件分支行为）须
标注为「待实证子断言」，不得作为结论性证据——门禁与复核均基于同一源码，
只有部署布局实证能拦截此类误差（实录：绝对路径旁路断言被 real-target
证伪，真实缺口在 CWD 回退分支）。
```

### D-4 SKILL.md（公开面关联检索段追加）

```
上游「已修复/已包含」结论必须附树内 commit 佐证（git log -S /
merge-base --is-ancestor），无法佐证时按未修复处理——版本号声称与
树内事实不符是时间差发现的直接来源（SWR-V3.42-004）。
```

### D-5 hypothesis_filter.md（排除判据段追加）

```
5.5. **信息暴露/跨信任域维度核对（v3.42, SWR-V3.42-005, 提示级）**：
『无权限提升』方向的 drop 前，必须核对 (a) 信息暴露（枚举 oracle/存在性
判定）与 (b) 跨信任域完整性（第三方信任域消费合成事件/数据）两个维度——
R2 filter 与 R4 假说的判据差集是真实发现空间（实录：弱门被 filter drop 后
R4 从用户 oracle 维度重发现为 High）。
```

### D-6 SKILL.md（实证回填规范段追加）

```
回填前缀语义（SWR-V3.42-006）：CONFIRMED 前缀触发 ③d independent_review
要求（无 independent_review/r3_link 即违规）；机制级静态确证写 SOURCE_FACT
前缀（has_confirmed 判定包含 source_fact 关键词）。回填前预判 gate 链级联。
```

## P4 版本链

1. workflow_export.py TOOLING_VERSION "3.41" → "3.42"
2. 版本守卫测试行（grep 3.41 的测试断言）逐处更新
3. SKILL.md 增量段 + 版本历史表新增 v3.42 行
4. REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+ VERSIONS 登记
5. 资产计数守卫同步（SKILL.md 附录清单条数如有变化）
