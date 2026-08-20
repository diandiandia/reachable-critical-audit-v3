# SWR V3.4.4 — 验收暴露缺陷修复批（10 条）

> 来源：v3.4.3 验收项目 jsrsasign 全流程实测暴露。设计文档见
> `ACCEPTANCE_V3_4_3.md` 与 `lessons/SKILL_LESSONS_jsrsasign.md`。
> 通用性自检（第一原则）：全部修复为语言无关/项目无关机制，无项目专属名。

## 代码级机制缺陷（1-4）

### SWR-V3.4.4-001 信号关键词词边界匹配
- **缺陷**: checklist_binder/precedent_library `_signals_ok` 用裸子串
  `k.lower() in text` 匹配 applicability_signals.text——"ws" 误配
  "jws.verify"（jsrsasign CAND-001 误绑 CK-WS-MATERIALIZE 实测）。
- **修复**: ASCII 关键词（`k.isascii()`）改用词边界正则
  `(?<![a-z0-9])<kw>(?![a-z0-9])`；CJK 关键词保持子串语义（无词边界概念）。
  requires_lang 同改（"c" 误配 "scala" 同类缺陷）。
- **验收**: 单测构造 "jws" 文本 + ["ws"] 信号 → 不匹配；"ws server" → 匹配。

### SWR-V3.4.4-002 r4-collect 保留主代理裁决字段
- **缺陷**: `stage_r4_collect` 按 hypothesis_id 整体替换（`existing[hid] = f`），
  重复 collect 会抹掉主代理裁决（jsrsasign H7-F5 claim 置空被第二次 collect
  覆盖，实测事故）。
- **修复**: 按 finding title 匹配旧记录，保留裁决字段
  `{claim_type, claim_nulled_by, empirical_verified_by, empirical_result,
    correction_record, mapped_surface_ids, evidence}` 中旧值非空而新值缺失的项。
  仅当新输入显式携带该字段时允许覆盖（agent 新产出优先）。
- **验收**: 单测先裁决（claim 置 null）→ 重新 collect（claim=crash）→ 置空保留。

### SWR-V3.4.4-003 refutation 导出截断告警（qualified_total）
- **缺陷**: 资格池 9 候选默认 batch_size=4 静默截断为 4，导出结果无任何
  资格全集信息（jsrsasign R3.5 波次 1 实测误判"只有 4 个合格"）。
- **修复**: export_script 在截断前记录 `qualified_total`；截断时结果附
  `"truncated": true, "exported": N, "qualified_total": M`（refutation 模式；
  verify 模式波次截断为设计行为，同样附计数）。
- **验收**: 单测 6 资格 batch_size=4 → qualified_total=6 + truncated=true。

### SWR-V3.4.4-004 collect 报错指引 r35-collect
- **缺陷**: 对 refutation journal 跑 `--stage collect` 时报"无 schema-validated
  结果 (id+verdict)"，不提示正确入口（jsrsasign R3.5 收集时实测绕路）。
- **修复**: journal 提取为空时检测行内是否存在 refutation schema
  （`id + refuted`），存在则报错追加"该 journal 为 refutation 结果,
  请用 --stage r35-collect"。
- **验收**: 单测构造 refutation 形态 journal → 错误信息含 r35-collect。

## 任务书级防误报（5-7）

### SWR-V3.4.4-005 R4 任务书部署布局义务
- **缺陷**: H7 agent 对 pkcs5pkey 的实证为 vm 全量加载 src，非部署布局——
  模块不在任何发布产物（npm lib/all-min/Makefile 零命中）却被判 REACHABLE
  crash（主代理裁决 claim 置空的根因）。
- **修复**: biz_hypothesis.md 增加强制条款：
  ①实证必须在部署布局执行（npm main/bundle/官方构建产物），vm 全量加载
  src 不构成部署布局实证；②模块不在任何发布产物 → 不构成可达声称，按
  源码卫生缺陷记录（claim_type 置空）。
- **验收**: 模板 grep 断言条款存在。

### SWR-V3.4.4-006 R4 empirical_result 确认标记契约
- **缺陷**: 门禁③b 结构判定要求 empirical_result 含 "CONFIRMED/实证" 等
  关键词，5 条真实实证的 findings 因缺标记被机械拦截（jsrsasign 实测）。
- **修复**: biz_hypothesis.md 约定 empirical_result 以
  `CONFIRMED:`/`REFUTED:`/`SOURCE_FACT:` 前缀开头（门禁③b 识别，
  消除整类误拦截）。
- **验收**: 模板 grep 断言前缀契约存在。

### SWR-V3.4.4-007 verifier 任务书计数类证据规范
- **缺陷**: CAND-010 的 Miller-Rabin 计数 79/48 被证伪者实测 55/69 且方向
  翻转（几何随机变量单次观测）——verifier 把它当可复现证据引用。
- **修复**: verifier 任务书 v3 强制规则增加：计数类观测（素性试除次数等
  几何随机变量）不做可复现证据引用，只标注"单次观测，数量级参考"。
- **验收**: 任务书渲染 grep 断言。

## 守卫/杂项（8-10）

### SWR-V3.4.4-008 tooling 版本一致性守卫
- **缺陷**: jsrsasign 验收中 payload 由 workspace v3.4.3 导出、collect 误用
  installed v3.4.2 执行——版本不一致无任何机械提示（主代理流程事故的
  廉价防线缺失）。
- **修复**: workflow_export 增加 `TOOLING_VERSION` 常量并嵌入导出 JS
  （`const TOOLING_VERSION = '...'`）；batch_verify collect/r35-collect 读取
  项目 `.audit_results/` 下 workflow JS 的版本号，与本模块不一致时输出
  warn（不阻断，主代理裁决）。
- **验收**: 单测构造版本不符 JS → collect 输出 warn。

### SWR-V3.4.4-009 lessons_recorder 项目名绝对化
- **缺陷**: `os.path.basename(project_root.rstrip("/"))` 对相对路径 "."
  产出空/异常名（实测生成 SKILL_LESSONS_..md 事故）。
- **修复**: `os.path.basename(os.path.abspath(project_root)) or
  os.path.basename(os.getcwd())`。
- **验收**: 单测相对路径 "." → cwd basename。

### SWR-V3.4.4-010 workflow_export CLI 支持 resurrect
- **缺陷**: docstring 与 main() 只认 verify/refutation，`--mode resurrect`
  抛 ValueError（resurrect 入口仅在 batch_verify 路由，两入口不一致）。
- **修复**: main() 路由 mode=="resurrect" → export_script_resurrect；
  docstring 增补用法行。
- **验收**: 单测 CLI resurrect 空池 → WORKFLOW_NOTHING_TO_DO。
