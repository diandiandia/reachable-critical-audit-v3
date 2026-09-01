# SOFTWARE DESIGN V3.17 — 函数级设计与开发序列（2026-09-01）

## P1 机械层

### 1.1 resources/generation_registry.json（新）

```json
{
  "description": "生成层注册表 — 源码扩展名默认视图 + 通用 DSL 族映射（去项目化: 仅多项目通用 DSL 可入库）",
  "default_extensions": [".c", ".h", ".cc", ".cpp", ".hpp", ".rs", ".rb", ".py",
    ".js", ".ts", ".java", ".go", ".php", ".swift", ".kt", ".scala", ".cs",
    ".pl", ".pm", ".sh", ".ps1", ".m", ".mm", ".sql"],
  "dsl_entries": [
    {"ext": ".proto", "role": "dsl", "lang_family": ".c", "generates": [".pb.cc", ".pb.h"]},
    {"ext": ".y",   "role": "dsl", "lang_family": ".c", "generates": [".c"]},
    {"ext": ".l",   "role": "dsl", "lang_family": ".c", "generates": [".c"]},
    {"ext": ".fbs", "role": "dsl", "lang_family": ".c", "generates": [".cc", ".h"]},
    {"ext": ".rl",  "role": "dsl", "lang_family": ".c", "generates": [".c"]},
    {"ext": ".asn1", "role": "dsl", "lang_family": ".c", "generates": [".c", ".h"]},
    {"ext": ".idl", "role": "dsl", "lang_family": ".c", "generates": [".c", ".h"]}
  ]
}
```

### 1.2 扩展名合并视图

- 新 `generation_registry.py`（skill 根，与 surface_mapper 平级）：
  `load() -> dict`（读 resources/generation_registry.json）；
  `merged_view(profile_generation_layers=None) -> set[str]`（默认 ∪ profile
  局部条目 ext）；`lang_family_for(ext)`；`provenance_for(ext)`（dsl→生成物
  反向映射）。
- surface_mapper.language_inventory / size_tier、signature_matcher 的
  CODE_EXTENSIONS 消费点改调 `merged_view`（无 profile 时 = 现状集合，保证
  零行为变化）；生成物 ext（.pb.cc 等）直接并入对应 lang_family 组。
- batch_verify `_EXT_LANG` 补生成物 ext → lang_family 映射。

### 1.3 scaled_caps（signature_matcher.py）

```python
def scaled_caps(indexed_file_count):
    """SWR-V3.17-007: 佐证器 cap 随索引文件数缩放（上限常数化）。"""
    if indexed_file_count > 8000:  return 180, 80, 900
    if indexed_file_count > 2000:  return 120, 60, 600
    return ENTRY_LINE_CONTEXT, LAYER_CAP, WINDOW_CAP
```

build_project_index 末尾返回/附记文件数；expand_window 增 caps 参数缺省现状。

### 1.4 清单族（resources/checklist_library.json，纯数据）

新增 5 条：CK-GC-WRITE-BARRIER / CK-GC-ROOT-SCAN / CK-TIER-TRANSITION /
CK-ALLOC-ESCAPE（family: runtime-memory-model）、CK-GENERATED-CODE
（family: generated-code）。applicability_signals.text 用多词短语
（"write barrier"/"generational collector"/"managed heap"/"gc root"/
"tier transition"/"generated file"），禁裸词 gc/barrier/collector
（v3.12 词边界纪律）。

## P2 结构层

### 2.1 tools/target_profile.py（新）

```python
usage: python3 tools/target_profile.py <project_root> [--write]

信号（全部机制形态, 零项目名）:
  S1 源文件数（生成层合并视图）→ scale_class 建议
  S2 扩展名普查: dsl 扩展名命中 → generation_layers 建议（从 dsl_entries
     拷贝命中项; 未命中条目录入 suggestion 供主代理补全）
  S3 构建清单 hits: BUILD.gn/BUILD.bazel/CMakeLists.txt/meson.build/
     MODULE.bazel 存在性 → 两阶段测绘信号
  S4 README/顶层文档关键词: interpreter/virtual machine/runtime/bytecode/
     compiler/jit（词边界）→ surface_model=semantic 推荐信号
  S5 目录信号: gc/gc-common/memory（目录名机制形态）→ managed-runtime 提示
  S6 沙箱信号: 构建旗标文本（sandbox 配置开关类关键词, 词边界）→
     containment_default 推荐信号

输出: {"recommended": {surface_model, generation_layers, scale_class,
       containment_default, empirical_modes}, "signals": [{"id","evidence"}],
       "confidence": ...}
--write → .audit_results/target_profile.json（含 recommended + signed_by
       null 占位; 主代理复核后写入 signed_by/overrides）
```

消费者装载契约（各模块统一）：`profile = load_target_profile(project_root)`
——文件不存在或 `signed_by` 缺失 → 返回全默认 dict（现状行为）。

### 2.2 size_tier super-large 档（surface_mapper.py:735）

阈值 >2000 → `{"tier": "super-large", "agent_count": 4,
"time_limit_min": 45, "checkpoint_every_min": 10, "two_phase": True,
"components": [...]}`；components = 深度 1 目录（排除 SKIP_DIRS）按文件数
降序取前 30，每项 {dir, file_count, build_signal_hits}。501-2000 档输出
补 `"components": []` 与 `"two_phase": False`（字段级零漂移，旧消费方读
tier/agent_count 不受影响）。

### 2.3 containment 管线（tools/batch_verify.py）

- `_derive_containment(v, c)`（mirror _derive_attacker_tier :390）：
  显式合法值 → 直取；非法值 warn + none；未给 → none（零告警）。
- stage_collect（:418 区块）落盘 `entry["containment"]`。
- `_mechanical_severity` 末尾加调整步：

```python
def _apply_containment(sev, containment):
    m = {"process_sandbox": 1, "language": 1, "hardware_isolated": 2}
    step = m.get(containment, 0)
    if containment == "language" and sev != "critical":
        step = 0  # language 仅 critical→high
    order = {"critical": 3, "high": 2, "medium": 1}
    while step > 0 and order[sev] > 1:
        sev = {"critical": "high", "high": "medium", "medium": "medium"}[sev]
        step -= 1
    return sev
```

来源串 `containment:process_sandbox`（调整发生时）或不变。severity_for 的
override 分支不变（override 绝对优先）。_r4_severity 同源调整
（R4 confirmed findings 渲染一致性）。

- 报告渲染：问题清单行 `containment != none` 时渲染标记
  `[沙箱收敛]/[语言防护]/[硬件隔离]`（映射表 SEVERITY_LABELS 旁新增
  CONTAINMENT_LABELS）。
- workflow_export verifier 注入块：profile.containment_default 非 none
  或候选已带 containment 时注入提问句（默认零注入）。
- tracked-ids（--stage tracked-ids）：input_surface surfaces 含
  semantic_axis 时轴 id 并入 tracked（门禁⑦语义不变, 轴即面）。

### 2.4 surface_model 字段链

- surface_mapper.validate / merge：容忍 `semantic_axis` 可选字段透传
  （归一化不剥离未知键——核对 validate 现有键白名单, 若有剥离则加白）。
- SKILL.md R1/R2/门禁⑦节：semantic 条款（见 P4 文档项）。

## P3 内容层

### 3.1 templates/harness/differential_probe.py（新）

参数契约（argv 必传, 缺参数 usage exit 2, harness_runner 家族惯例）：
`--configs N` + 每配置一命令（`--cmd-0/--cmd-1`...）；`--corpus DIR`
或 `--gen SCRIPT`；`--compare exit_code[,output_hash,stderr_hash,rss_delta]`；
`--rounds N`；`--timeout S`。执行模型：每输入 × 每配置跑一轮，汇总分歧表；
判定输出 JSON：`{divergent: [{input, configs, diff}], consistent, summary}`。
docstring 明示：分歧确认 ≠ 漏洞成立（供 verifier 定级），R5 SAMPLING_PROTOCOL
沿用（RSS 采样/环境记录）。

### 3.2 task_templates/surface_map_domain.md

新增两段（占位符注入, 未注入时不渲染）：
- `{semantic_axis_section}`：surface_model=semantic 时注入——轴 schema 与
  轴锚点证据义务（锚点文件 file:line 必附, 一轴一 id, cardinality 估值）；
- `{two_phase_section}`：super-large 时注入——本 agent 只测 `{component}` 组件
  目录, 面 id 带组件前缀（SURF-<域>-<组件缩写>-NNN）, 产出写
  `_r1_<域>_<组件>.json`。

### 3.3 harness_manuals/mixed_build.md 增章节

「生成物重超大型构建（gn/ninja/bazel/meson/depot_tools 类）」：工具存在性
探测（which gn/ninja/bazel/meson）；生成物目录约定（out/ 系——以项目构建
清单声明为准不臆断）；增量构建计时与首次全量构建成本提示；目标产物路径
（二进制/库）从构建清单推导；实证时限预对齐（R5 环境能力探针配合）。

## P4 版本链（见 REQ 版本链节）

TOOLING_VERSION → "3.17"；SKILL.md v3.17 增量段；守卫 5 处行号逐处实测
核对后 sed；tracking 手工段；test_v317.py；全量回归；旧队列复跑；install。
