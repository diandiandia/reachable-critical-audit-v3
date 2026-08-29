# SOFTWARE_DESIGN_V3_13 — 软件方案（v3.13 错误路径处理族 + 数值语义族 + 锚点修复）

> 对应需求文档：REQ_V3_13.md（5 条 REQ）。只增改不重写：模块改动点、数据模型变更、测试计划。
> 原则：改动最小面；旧队列零告警；新增行为全部有触发条件（cwe/关键词命中）。
> 评估：BIAS_EVAL_V3_13.md（H-0 自纠 + 4 处核验修正随本方案落实）。

## 1. 模块改动点

### 1.1 `resources/issue_coverage_matrix.json`（纯数据）
- `families` 加 NUMERIC（191/369/681/697）与 ERROR-HANDLING（457/665），置于
  STATE 后 OTHER 前；WEB cwe += 436/444；RESOURCE-DOS cwe += 1333。
- `rows` 加两族空行（STATE 空行后 OTHER 行前——缺口扫描只遍历 rows）。
- 效果：fam_map 数据驱动自动生效，9 个 CWE 全部脱离 OTHER（零代码改动）。

### 1.2 `tools/batch_verify.py`（纯映射追加）
- `SEVERITY_BY_CWE`：critical += {191}；high += {369, 457, 444, 1333}；
  medium += {681, 697, 665, 436}（注释按族同步）。
- override 优先级/claim_type 回退/default medium 语义零变化。

### 1.3 `resources/checklist_library.json`（纯数据，`checklists` 数组尾插 4 条）
- **CK-NUMERIC-TRUNCATION**（numeric-semantics，cwe 191/681）：截断先于检查/
  回绕过检/哨兵算术 3 步。
- **CK-NUMERIC-SEMANTICS**（numeric-semantics，cwe 369/697）：除零路径/比较不一致/
  取模边界 3 步。
- **CK-ERROR-BRANCH**（error-handling，无 cwe 锚定关键词绑定）：条件反转/死代码/
  吞没转正常路径 3 步。
- **CK-ERROR-CLEANUP**（error-handling，cwe 457/665）：未初始化残留/清理完整性/
  宿主复用残留 3 步。
- 形态纪律：无 `applications` 字段；禁裸 异常/error/cleanup（子串/下划线误配）；
  source_lessons 实证队列核验后书写（gson 665 只作假说级锚点——BIAS_EVAL H-1）。

### 1.4 `workflow_export.py`
- `TOOLING_VERSION = "3.13"`。

### 1.5 `SKILL.md`
- 严重度表三行补 NUMERIC/ERROR-HANDLING/WEB/RESOURCE-DOS 注记（9 码）；
- 资产地图：34→38 条检查清单（v3.13 增补 4 条数值语义/错误路径族）；17 先例不变；
- R3 段 34→38 条 CK-*；
- 文末追加「🆕 v3.13 增量」段（背景六缺口/机制新增 5 项/明确不做/验收判据）。

### 1.6 `tools/gen_tracking.py` + `docs/design/REQUIREMENTS_TRACKING.md`
- VERSIONS 登记 `("V3.13", "docs/design/REQ_V3_13.md", "docs/design/SWR_V3_13.md")`；
- REQUIREMENTS_TRACKING.md 尾手工追加 V3.13 REQ（5 条）+ SWR（6 条）段（表格形态）；
- ⚠️ 禁止运行 `tools/gen_tracking.py` 再生成（V3.4.4-V3.7 手工段不在 VERSIONS）。

### 1.7 既有守卫更新（6 处）
- test_v39.py:253（34→38）、:266（"3.12"→"3.13"）、:269（34→38 条检查清单）；
- test_v310.py:274-276（"3.12"→"3.13" 含注释）；
- test_v312.py:178（"3.12"→"3.13"）、:181（34→38 条检查清单——v3.13 设计初稿
  遗漏点，Plan 代理核验补入）。

## 2. 数据模型变更（向后兼容）

```
resources/issue_coverage_matrix.json:
  families: +NUMERIC{191,369,681,697} +ERROR-HANDLING{457,665}
            WEB cwe += 436,444; RESOURCE-DOS cwe += 1333
  rows:     +两族空行
resources/checklist_library.json:
  checklists: +4 条 (numeric-semantics ×2 + error-handling ×2)
tools/batch_verify.py:
  SEVERITY_BY_CWE: critical +191; high +369/457/444/1333; medium +681/697/665/436
precedent_library: 零改动 (436/444/1333 既有 map 可达)
队列/候选/surface schema: 零变更
```

## 3. 测试计划（tests/test_v313.py，14 用例）

| 测试 | 断言 |
|---|---|
| test_ledger_new_families_and_rows | 两族 cwe 集 + WEB/RESOURCE-DOS 补码 + 两空行 |
| test_ledger_reanchor_aggregation | 436/444→WEB、1333→RESOURCE-DOS、191→NUMERIC、457→ERROR-HANDLING，均非 OTHER |
| test_ledger_gap_scan_shows_new_families | 缺口含 NUMERIC x /ERROR-HANDLING x |
| test_severity_numeric_cwes | 191→critical、369→high、681/697→medium |
| test_severity_error_handling_cwes | 457→high、665→medium |
| test_severity_reanchor_cwes | 436→medium、444→high、1333→high + 841/670 回归 + override/回退不变 |
| test_ck_numeric_bind_via_cwe | 191/681→TRUNCATION；369/697→SEMANTICS（唯一锚定精确断言） |
| test_ck_numeric_bind_via_keyword | CJK 与 ASCII 多词双路径命中 |
| test_ck_error_branch_keyword_binding | 6 关键词命中；负例「异常处理 catch 分支」不绑新条目 |
| test_ck_error_cleanup_bind | 457/665 cwe 路径 + 未初始化/uninitialized 关键词路径 |
| test_no_bare_word_false_binds | error_handler/cleanup()/裸 error/裸 异常 不绑新条目（限定形态） |
| test_new_checklists_deproject | 4 条零黑名单 token（含 lersosa）/零 /root//无 applications 键 |
| test_tooling_version_and_skillmd_counts | 3.13 + v3.13 段 + 38/17 计数 + 严重度表 9 码 |
| test_verify_prompt_injects_new_checklists | 导出 verify 脚本含新清单段 |

## 4. 开发顺序（C0 + P18-P21 提交序列，延续 v3.12 P17 惯例）

- **C0 设计件**：REQ/SWR/SYSTEM_DESIGN/SOFTWARE_DESIGN_V3_13 + BIAS_EVAL_V3_13
- **P18 机制级**：账本两族+空行+锚定修正 + SEVERITY_BY_CWE 9 码 + SKILL.md 严重度表
- **P19 清单族**：4 条 CK（零 binder/注入代码改动）
- **P20 版本链**：TOOLING 3.13 + SKILL.md 增量段/资产地图 + gen_tracking 登记 +
  tracking 手工段 + 守卫 6 处
- **P21 测试与验收**：test_v313.py（14 用例）+ 全量回归 + selfcheck + 账本干跑 + install

## 5. 验证

```bash
python3 -m pytest tests/ -q            # 315 基线 + test_v313 全绿
python3 signature_lib.py selfcheck /root/phpseclib   # R0 自检（去项目化扫描绿）
python3 tools/batch_verify.py /root/Pillow --stage coverage-ledger   # 新族×16 缺口格
# 禁止: python3 tools/gen_tracking.py（见 §1.6）
```
