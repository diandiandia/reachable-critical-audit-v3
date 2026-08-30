# SOFTWARE_DESIGN_V3_15 — 软件设计（2026-08-30）

函数级设计，编辑点行号为 dev 树 2026-08-30 实测。实现序 P1→P4，每步跑
`python3 -m pytest tests/ -q`。

## P1 机械小修

### D-1 报告守卫双形态（batch_verify.py）

```python
# ~1704 (stage_report 内)
if "（主代理补充）" not in tail[:400] and "本段由主代理补充" not in tail[:400]:
    # REFUSED...
```
模板第三节体（render_report_md ~2381 后）占位行改为：
`> （主代理补充）本段由主代理补充；补充后**不得重跑 \`--stage report\`**（机械渲染会覆盖本段）。`

### D-2 统一 claim 判定（evidence_ledger.py + workflow_export.py）

```python
# evidence_ledger.py 新增 (EMPIRICAL_CLAIMS 同模块已有)
def is_claim_like(cand, fields=("claim_type", "evidence", "summary")):
    """声称类判定单真相 (SWR-V3.15-002): claim_type 字段优先, 文本扫描降级。
    复活池选样与门禁③c 同调此函数——字段集一致是义务/选样同源的机械保证。"""
    ct = str(cand.get("claim_type") or "").lower()
    if ct and any(k in ct for k in EMPIRICAL_CLAIMS):
        return True
    text = " ".join(str(cand.get(k) or "") for k in fields).lower()
    return any(k in text for k in EMPIRICAL_CLAIMS)
```
- ③c 调用点（evidence_ledger.py:281-284）改：`if is_claim_like(c) and not c.get("resurrection_review")`
- workflow_export.py:450-470 resurrect_pool 改：`claimed = [c for c in pool if el.is_claim_like(c)]`
  （workflow_export 顶部 `import evidence_ledger as el`——若现有导入形态不同按现状接入）
- 附带裁决：20% 抽样保留（SWR-V3.15-002 测试覆盖两处等值）。

### D-3 R4 枚举建议映射（batch_verify.py:999-1019）

R4_ENUM_WARNING 的 warning dict 增 `suggestion` 字段：
- illegal_hypothesis_verdict：`{"suggested": "reviewed_clean", "note": "非法 verdict 归一化建议 (nghttp2 H2/H4 实录形态: NO_REACHABLE_CONFIRMED/NOT_CONFIRMED)"}`
- illegal_finding_severity：`{"suggested": "low", "note": "informational 归一化建议 (gpac H3-F1 实录形态)"}`
不改 verdict 自动改写（SWR-V3.15-003）。

### D-4 post-resurrect advisory（workflow_export.py:631-637）

export_script refutation 分支 result 增：
```python
advisory = [c["id"] for c in candidates
            if c.get("re_verify_gap") and c.get("verdict") == "REACHABLE"
            and "refutation" in c]
if advisory:
    result["post_resurrect_advisory"] = {
        "ids": advisory,
        "note": "带 re_verify_gap 的 REACHABLE 候选含陈旧 refutation 字段, "
                "被本波资格排除 (W6 排除条件)——重验后须归档旧 refutation 至 "
                "refutation_history 再导出强制复核波 (libarchive CAND-020/011 实录形态)"}
```

## P2 结构修复

### D-5 截断 key 集（workflow_export.py:301-328）

```python
_TRUNC_KEY_HEAD = re.compile(
    r"^【?(?:步骤 ?0|承重前提|实证|阻断|结论|claim 与实证|gap 核实|核对)"
    r"|^\[(?:G\d+|PREC-[\w-]+|CK-[\w-]+)\]"
    r"|^VERDICT"
    r"|^复活 gap 逐条核实")
```
分段逻辑与全 minor 首尾拼接兜底保留（热修代码不变）。

### D-6 tracked_surfaces 契约（batch_verify.py:1852-1860 + 模板）

_tracked_ids 保留热修（dict 提取 surface_id）；biz_hypothesis.md 输出契约段加：
`tracked_surfaces: 字符串 id 列表 (canonical, 门禁⑦/渲染器消费); 富形态
(逐面 {surface_id, verdict, evidence}) 写 sweep_records 字段, 不得混入 canonical。`

### D-7 scope_diff 消费（batch_verify.py:2469-2495 + surface_mapper.py docstring）

scope_reopen_advice 构建顺序改：`changed_dirs = diff.get("affected_dirs") or []`
优先；空时走 `_chg_dir` 字符串解析 fallback（热修保留）。surface_mapper.py:1052
docstring 改注：`changes: [人读描述字符串, 机器消费请用 affected_dirs]`。

### D-8（并入 D-6 模板条款，见上）

## P3 任务书义务

### D-9 CK-EMPIRICAL-SCOPE +基线对照条目（resources/checklist_library.json）

steps 增：
```
- 资源类 (oom/unbounded/protocol_dos) 实证必须双测: 对照组 (无攻击输入/基线
  运行) + 攻击组; 报告基线值/增量与驻留时长观测——单次绝对读数不可作证据
  (gpac CAND-001 实录: 108MB 读数为 ~105MB 环境基线伪影, 真实增量 ~12MB)
```

### D-10 PREC-GUARD-SUBSET-001（resources/precedent_library.json + precedent_library.py）

```json
{"id": "PREC-GUARD-SUBSET-001",
 "title": "守卫封顶阻断主张必须枚举守卫通过子集",
 "family": "blocking",
 "match": {"keywords": ["封顶","上限","有界","拒绝","守卫","short","guard"]},
 "hint": "阻断主张『守卫封顶/上限已封』只实证拒绝路径 = 不成立——必须枚举守卫"
         "通过子集: 文件真实包含声明尺寸/自动切换 tier (AUTO→TCP_ONLY)/重试路径/"
         "配置档位 (gpac CAND-007 短读守卫被真实内容绕过, CAND-001 1MB 档自动切换实录)",
 "applies_to": ["verifier","refuter","resurrect"]}
```
precedent_library.py 若 self_refutation_hints 匹配依赖固定字段名，按现状扩展
匹配词（以实测为准，不破坏既有 PREC 匹配）。

### D-11 CK-VENDORED-CONTRACT（resources/checklist_library.json + workflow_export.py）

```json
{"id": "CK-VENDORED-CONTRACT",
 "name": "绑定依赖库/第三方 vendored 解析器契约检查",
 "family": "blocking",
 "binding": {"cwe": [], "keywords": ["vendored","llhttp","libcrypto","绑定","第三方","openssl"],
             "applies_to_phase": "R3"},
 "applies_to": ["verifier","refuter"],
 "steps": [
  "目标树内缺校验 ≠ 缺陷成立——先查绑定层契约: vendored 状态机 (llhttp pause/resume/"
  "upgrade 转移) 是否补上校验、加密库低阶点/对等端校验 (X25519 kZeros/DH Ys=p-1)、"
  "流层 count>size 拒绝等 (nghttp2 llhttp 死代码误判/s2n-tls 绑定层两次生效实录)",
  "阻断论证引用『绑定层补全校验』时必须写绑定层 file:line, 不得只写目标树行号"]}
```
workflow_export.py 复活维度清单（~483-487 五条）追加一行：
`6. 绑定依赖库契约是否漏查（vendored 解析器状态机/加密库校验——复活维度五条之外的本批新高频阻断误判源）`

### D-12 未测平台清单（workflow_export.py PTM 注入块 ~660-690）

注入块末追加一行：
`平台条件性前提 (32 位回绕/LLP64/平台 API 语义) 必须在 evidence 显式列出
未实测平台/构建清单——复活波按此清单定向补测 (freetype CAND-002 实录:
复活者强制 32 位类型重建+ASAN 补上 verifier 唯一未测维度)。`

## P4 流程条款

### D-13 SKILL.md R1 铁律 3 追加

「多行 snippet 块匹配以首行键为锚（首行文本全文件匹配），块体其余行按连续
性归并；HTML 实体先解码再比对（libarchive 53/83 漂移实录）」。

### D-14 SKILL.md R1 + surface_map_domain.md

模板落盘契约加：`域无面时输出 {"surfaces": []} 并附空域理由 (zero syscall/
无监听器等证据)；主代理复核后写 reviewed_by + empty_domain_reason 签收
(freetype 网络空域实录)。` SKILL.md R1 同步一句。

## P5 版本链与测试

- workflow_export.py:22 → "3.15"；守卫 4 处测试行 → "3.15"
- SKILL.md v3.15 增量段（列 SWR-V3.15-001..012 + D-13/D-14 文案）
- gen_tracking VERSIONS 登记；REQUIREMENTS_TRACKING.md 手工追加 v3.15 段
  （禁 gen_tracking 再生成）
- tests/test_v315.py 约 15 用例（清单见 REQ_V3_15 测试守卫约束）
- 全量回归 + gpac/freetype/protobuf 队列门禁复跑零新增告警 + install 同步
