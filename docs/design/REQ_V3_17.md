# REQ V3.17 — 运行时/引擎形态能力补全（2026-09-01）

## 上下文

Chrome V8 审计可行性评估（2026-09-01 会话，评估结论为案例支撑）暴露 7 项
缺陷：六项为数据模型"硬编码轴"与运行时/引擎形态的系统性错配，一项为佐证器
规模封顶。全部经代码取证核实（编辑点行号为 dev 树实测）。V8 本地实例数据
（/root/v8，src 下 3325 源文件 / 249 .tq）为缺陷②的量级佐证。

**通用化判据**：修复对象是"哪类项目会撞上同一根轴"——运行时/引擎形态
（语言运行时/JIT/解释器/编译器/超大型多组件 C/C++ 工程），不是 V8 专属。
按惯例不改阶段骨架、六门禁①-⑧判据语义、队列数据模型主体。所有新字段
默认值 = 现状行为（旧队列复跑零新增告警不变式）。

## 修复清单（7 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | 生成物/DSL 文件不可见——`_SRC_EXTS`（surface_mapper.py:224，21 扩展名）与 `CODE_EXTENSIONS`（signature_matcher.py:51，23 扩展名）均无 .tq/.inc/.pb.cc 类；语言清单/规模档位/候选语言三处消费端（surface_mapper.py:352、batch_verify.py:520）恒盲 | 新增 `resources/generation_registry.json`（默认条目 = 现扩展名集语义，通用 DSL 族：proto/yacc/lex/fbs/ragel/asn1 等，每条 role:dsl|generated + generates 映射）；surface_mapper/signature_matcher/batch_verify 读注册表合并扩展名与 provenance；项目局部 DSL（如 .tq）经 `target_profile.generation_layers` 审计期局部署名（两段式：机制入库，项目专属扩展名不入运行时资产） | surface_mapper.py:224/352、signature_matcher.py:51、batch_verify.py:520、resources/generation_registry.json（新） |
| D-2 | 规模档位封顶两个数量级——size_tier 最高档 >500 文件 = 4 agents + 45min（surface_mapper.py:735-777）；V8 src 单目录 3325 文件 | size_tier 新增 super-large 档（>2000 文件）：输出组件清单（顶层模块目录 × 构建清单信号，通用探测：BUILD.gn/CMakeLists/meson.build/BUILD.bazel）+ 按组件预算建议；R1 派发两阶段（组件清单 → 组件×域测绘），SKILL.md R1 编排文本与 surface_map_domain.md 模板段承载 | surface_mapper.py:735、SKILL.md R1 节、task_templates/surface_map_domain.md |
| D-3 | 严重度机械映射无视防护边界——SEVERITY_BY_CWE（batch_verify.py:1653）纯 CWE 静态表；沙箱收敛的 CWE-787/416 恒判 critical，报告口径系统性高估 | 候选新增 `containment` 字段（none|language|process_sandbox|hardware_isolated，缺省 none = 现状）；severity_for/_mechanical_severity 增 containment 调整步（process_sandbox 下 critical→high、high→medium 单档；language 下仅 critical→high）；containment 经 verifier 任务书提问 + collect 缺省推导（mirror _derive_attacker_tier 管线，batch_verify.py:390）+ 主代理签收；报告行渲染 `[sandbox 收敛]` 标记；override 仍为唯一权威 | batch_verify.py:390/418/1653/1687/1701/1953、workflow_export.py:610（注入块）、SKILL.md 数据模型与严重度表节 |
| D-4 | 实证管线无引擎/差分形态——harness TEMPLATES 5 项（harness_runner.py:25）全部为网络解析器/RSS 形态；harness_manuals 构建指导为 cmake/make 生态，无 gn/ninja/bazel/meson 系；"对照矩阵"只存在于 verifier prompt 文本（v3.1 §21.1/§16.10）非一等 R5 模式 | 新增通用差分执行模板 `differential_probe.py`（argv 驱动：N 组运行配置 × 共享输入语料 × 比较器规格，零项目名）；TEMPLATES 注册 differential（langs:["any"]）；mixed_build.md 补"生成物重超大型构建"章节（gn/ninja/bazel/meson/depot_tools 类通用流程） | templates/harness/differential_probe.py（新）、harness_runner.py:25、harness_manuals/mixed_build.md、SKILL.md R5 节 |
| D-5 | 输入面概念错配——R1 面 = 入口点 file:line 单一形态；运行时/引擎真实面为语言语义轴，入口枚举退化为 parser/wasm 粗粒度面，门禁⑦覆盖率假性满足 | 新增 `target_profile.surface_model`（entry|semantic|hybrid，缺省 entry）；semantic 模式下 R1 增派语义轴测绘子智能体（轴 = 语义命名空间 × 锚点实现文件，surface 增可选 `semantic_axis` 字段）；R2 沿轴采样；门禁⑦ tracked_ids 轴当面计数 | tools/target_profile.py（新）、surface_mapper.py validate/merge 字段容忍、task_templates/surface_map_domain.md、SKILL.md R1/R2/门禁⑦节 |
| D-6 | 领域深度无机制承载——checklist_library 39 条零 GC/write-barrier/JIT 条目（全库 grep 实测零命中）；可达性判定靠 LLM 裸知识不可问责 | checklist_library 新增 `runtime-memory-model` 族 4 条（CK-GC-WRITE-BARRIER/CK-GC-ROOT-SCAN/CK-TIER-TRANSITION/CK-ALLOC-ESCAPE）+ `generated-code` 族 CK-GENERATED-CODE 1 条——纯数据，applicability_signals 词边界门控（禁裸词 gc/barrier），v3.12/v3.13 零 binder 改动先例 | resources/checklist_library.json |
| D-7 | 佐证器规模封顶——ENTRY_LINE_CONTEXT 60/LAYER_CAP 40/WINDOW_CAP 300 常量（signature_matcher.py:42-44），超大仓全库命中瞬间封顶 | cap 随索引文件数缩放（`scaled_caps(file_count)`：file_count>2000 时窗口/层 cap ×2、>8000 ×4，上限常数化）；默认参数路径零变化 | signature_matcher.py:42-44 |

## 横切结构：target_profile 签收工件（D-2/D-3/D-5 载体）

- 新 `tools/target_profile.py`（mirror target_kind.py 先例）：机械信号 →
  推荐值 + `--write` 落盘 `.audit_results/target_profile.json`；
  主代理复核签收（`signed_by`）后各阶段装载；未签收 = 全默认 = 现状行为。
- 字段：surface_model / generation_layers / scale_class /
  containment_default / empirical_modes——每个字段一个消费者
  （R1 派发/文件普查/规模档位/严重度/R5 模板选择），义务入库三问逐字段过。

## 版本链 v3.17

- workflow_export.py:22 TOOLING_VERSION → "3.17"
- SKILL.md v3.17 增量段 + 资产地图计数（清单 39→44、实证模板 5→6）
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、
  test_v39.py:266、test_v314.py:219 → "3.17"（实测行号，P4 逐处核对）
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
  gen_tracking VERSIONS 登记

## 开发序列

- **C0**（本文档集）：REQ + SWR + SYSTEM_DESIGN + SOFTWARE_DESIGN + BIAS_EVAL
- **P1 机械**：D-1（注册表）+ D-7（cap 缩放）+ D-6（清单族，纯数据）
- **P2 结构**：target_profile.py + D-2（super-large 档）+ D-3（containment 管线）
  + D-5（surface_model 字段链）
- **P3 内容**：differential_probe.py + surface_map_domain.md 语义轴段 +
  mixed_build.md 章节
- **P4 版本链**：TOOLING 3.17 + SKILL.md 增量段 + 守卫 5 处 + tracking +
  test_v317.py + 全量回归 + 旧队列复跑零新增告警（gpac/freetype/av）+
  install 双副本同步

## 测试守卫约束

- 必须保持绿：tests/test_v315.py（19 用例）、test_v314.py、test_v316.py（9 用例）、
  test_evidence_ledger.py（门禁名不增）、test_doc_lint.py（资产计数断言同步后）、
  test_v39.py:253（清单 39 条断言 → 44）
- 新增 tests/test_v317.py（约 18 用例，见 SWR 各条测试约束）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck <非 fixture 项目>
python3 tools/target_profile.py /root/v8            # 机械推荐 smoke（不落盘）
bash install.sh
```

## 边界声明

- **不做**：新门禁、新强制义务、H8、语义轴自动聚类、containment 自动改写
  severity、.tq 入运行时资产（两段式局部署名）。
- **案例支撑来源**：2026-09-01 会话 V8 评估六缺陷（取证行号已实测）+
  仓内先例（W6 §17.1 审计失控实录、v3.8 扩展名单事实源、v3.11 attacker_tier
  管线、v3.12/v3.13 纯数据族先例）。本环境 lessons.md 与记忆索引为空
  （项目目录无 .audit_results），案例支撑以本会话实录为准。
- **验收审计**：待用户指令后对 /root/v8 执行（runtime×cpp 缺口格，首个
  运行时/引擎形态验收项目）。
