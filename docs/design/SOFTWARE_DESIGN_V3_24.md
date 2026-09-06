# SOFTWARE DESIGN V3.24 — 函数/文本级设计 + P 分层序列

## D-1（SWR-V3.24-001）H4 site-isolation 子条

- 文件：`task_templates/biz_hypothesis.md`
- 插入点：第 40 行（平台信任模型对照条）之后、第 41 行（H5）之前；
  缩进与既有 H4 子条（35-40 行）一致（三空格接 `平台信任模型对照` 同级）。
- 插入文本（去项目化，零项目 token）：
  ```
    site-isolation/资源归因 (v3.24, SWR-V3.24-001): 跨进程资源（纹理/缓存/
    下载/导航目标/worker 等）绑定到错误 origin 即信任边界破坏——检查资源
    创建与归因的 origin 上下文一致性
  ```
- 反面分支守卫：文本不含「强制/必须」义务词。

## D-2（SWR-V3.24-002）JIT 根因归属条款

- 文件：`task_templates/surface_map_domain.md`
- 插入点：第 90 行（「该轴生成的候选按既有 R3 流程验证（CWE-843 已入严重度
  映射表）。」）之后追加一行，与轴段既有条目（`- ` 前缀）同形态。
- 插入文本（去项目化）：
  ```
  - 根因归属条款（v3.24, SWR-V3.24-002）: 缺陷根因无法在 runtime 实现与
    编译器正确性之间归属时，标注归属未知并保持 [ambig]——不得默认归编译器
    正确性; CWE-843 映射仅适用于归属成立的候选。
  ```
- 反面分支守卫：文本不含「强制/必须」。

## D-3（SWR-V3.24-003）边界声明补两族

- 文件：`SKILL.md` 第 341-344 行（报告段声明）
- 编辑：`（c）非目标平台变体。缺失 = warn 注记不阻断。` 替换为
  `（c）非目标平台变体，（d）UI 信任指示层（地址栏/界面欺骗类——UI 信任
  逻辑非代码缺陷），（e）移动端平台集成层。缺失 = warn 注记不阻断。`
- 不动：v3.23 增量节（1582 行区）历史记录保持原样；新 v3.24 增量节声明扩展。

## D-4（SWR-V3.24-004）回归集追加三样本

- 文件：`tests/fixtures/recall_regression_set.json`
- entries 数组追加（字段集对齐 RECALL-001）：
  - RECALL-002：defect_class "async object lifecycle race (callback-held
    reference freed across task/process boundary)"，family "MEMORY-SAFETY"，
    cwe ["CWE-416"]，profile_signals {"surface_model":"hybrid",
    "generation_layers":[]}，expected_hypothesis "H3 异步对象生命周期竞态 →
    回调持引用跨任务释放"，case_source "Chrome 2025-2026 critical L0b 族
    （188 critical 中 107 条=57%；recall_eval §2.3）"；
  - RECALL-003：defect_class "cross-process resource origin misattribution
    (texture/cache/download/navigation target bound to wrong origin)"，
    family "TRUST-BOUNDARY"，cwe ["CWE-863"]，profile_signals
    {"surface_model":"entry","generation_layers":[]}，expected_hypothesis
    "H4 跨进程信任边界 → 资源归因错误 origin"，case_source "三引擎 L0d 412
    条（firefox Graphics 组件 site-isolation 族/Chrome Site Isolation 组件族；
    recall_eval §2.2）"；
  - RECALL-004：defect_class "graphics pipeline boundary condition (GPU
    command buffer/shader validation integer overflow leading to OOB write)"，
    family "MEMORY-SAFETY"，cwe ["CWE-787","CWE-190"]，profile_signals
    {"surface_model":"hybrid","generation_layers":[]}，expected_hypothesis
    "H2 远端控制解引用长度 + H4 跨进程信任边界 → GPU 命令缓冲越界"，
    case_source "Chrome ANGLE/Skia/GPU 族 + Firefox WebGPU 族（recall_eval
    L0c 63 条）"。
- 纪律：case_source 是追溯字段（允许引擎名）；其余字段零项目名。

## D-5（SWR-V3.24-005）equivalent 档抽验提示句

- 文件：`SKILL.md` 第 281 行（「`mechanism` 档不得升 `empirically_confirmed`；
  申报材料按档位标注，不混级申报。」）后补一行：
  ```
  equivalent 档结论强度低于 real_target——真实目标环境可及时，对 equivalent
  实证候选做抽验（建模失真曾致等价实证结论被真实目标推翻的实录）；
  提示级，不强制不阻断。
  ```

## P 分层序列

- **P1**：无（本轮无判定函数/守卫条件级机械缺陷——取证确认五缺陷全为
  内容文本与 fixture 层）；
- **P3 内容**：D-1 → D-2 → D-3 → D-4 → D-5 依序；随后 test_v324.py；
- **P4 版本链五件**：
  1. `workflow_export.py:22` TOOLING_VERSION = "3.24"；
  2. 14 个测试文件版本断言行 sed（模式 `TOOLING_VERSION == "3.23"` → "3.24"），
     改后 grep 核对 `SWR-V3.23-` 历史 ID 串零变化；
  3. SKILL.md 增量段：v3.24 节插入 v3.23 节上方（列五 SWR + 验收判据）；
  4. `docs/design/REQUIREMENTS_TRACKING.md` 手工追加 V3.24 段（禁止运行
     gen_tracking 再生成）；`tools/gen_tracking.py` VERSIONS 登记
     ("V3.24", "docs/design/REQ_V3_24.md", "docs/design/SWR_V3_24.md")；
  5. 资产计数守卫核对：本轮无先例/清单条数变化（fixture 条目数无 SKILL.md
     正文计数消费）——核对 test_doc_lint 附录行即可。
