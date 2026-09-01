# SOFTWARE DESIGN V3.18 — 函数级设计与开发序列（2026-09-01）

## P1 数据 + 加载器

### 1.1 resources/language_issue_matrix.json（新）

```json
{
 "description": "语言问题矩阵 (v3.18, SWR-V3.18-001) — per-language 知识基座...",
 "langs": [16 与账本逐位一致],
 "families": [12 与账本逐位一致],
 "cells": [
  {"lang":"python","family":"INJECTION","status":"seeded",
   "cwes":["CWE-502"],
   "patterns":["反序列化输入面 (pickle/yaml.load 类): 不可信字节流 → 任意代码执行"],
   "sinks":["pickle.loads","yaml.load","eval","exec"],
   "pitfalls":["『仅受信输入』声称必须给出信源链证据, 不得以文件来源推定; 序列化边界≠信任边界"],
   "source_lessons":["SIG-PY-PICKLE-001 (签名库)"]},
  {"lang":"python","family":"STATE","status":"pending"}
 ]
}
```

首版种格 ~28（每格 source_lessons 指向仓内证据：签名 L2/清单/先例/
SKILL.md 实录），其余格 pending 空内容。

### 1.2 language_issue_matrix.py（新，skill 根）

```python
LANGS/FAMILIES 常量从 json 读取
load() -> dict                      # 进程内缓存
_lang_alias(lang)                   # cs↔csharp, ts/typescript↔javascript (+账本名直通)
cells_for(lang, family=None)        # 只返回 status=seeded; 未知语言 → []
stats() -> {seeded, pending, per_lang}
main: cells <lang> [family] | stats  # JSON stdout, exit 0
```

### 1.3 install.sh 模块清单

cp 行追加 `"$SRC"/language_issue_matrix.py`。

## P2 SKILL.md 条款

- R2 节新增条款（假设生成主路径段后）：
  > **语言问题矩阵提示（v3.18, SWR-V3.18-002）**：主代理（或限时 agent）
  > 生成假设前执行
  > `python3 <skill_dir>/language_issue_matrix.py cells <surface.lang>`
  > ——返回该语言已种格的族条目（典型漏洞形态/关键 sink/判定要点），作为
  > 假设空间提示；提示级无强制义务，pending 格零注入。
- 验收判据（Phase 3.18）含：**矩阵回填**——验收审计收官时主代理把验收
  项目覆盖的语言×族格两段式回填进矩阵（去项目化提炼 + source_lessons
  含日期），与 coverage-ledger --write 互补（账本记覆盖，矩阵供知识）。
- v3.18 增量段 + 资产地图补一行（resources/ 列表加 language_issue_matrix）。

## P3 版本链 + 测试

- TOOLING_VERSION "3.17"→"3.18"（workflow_export.py:22）+ 守卫 7 处：
  test_v310.py:276、test_v312.py:180、test_v313.py:191、test_v39.py:266、
  test_v314.py:219、test_v315.py:253、test_v316.py:120（实测行号逐处核对）。
- REQUIREMENTS_TRACKING.md 手工段 + gen_tracking VERSIONS 登记（禁再生成）。
- tests/test_v318.py（约 10 用例）：
  schema 合法 / langs、families 与账本逐位一致 / 种格全字段 / pending 零内容 /
  cells_for 只含 seeded + 别名归一 + 未知语言空 / stats 形态 / CLI 两命令 /
  DEPROJECT_BLACKLIST 扫描种格正文 / SKILL.md 条款存在 / TOOLING 3.18。
- 全量回归 + install.sh + installed diff 干净。
