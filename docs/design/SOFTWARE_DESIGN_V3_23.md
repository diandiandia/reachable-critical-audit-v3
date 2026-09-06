# SOFTWARE_DESIGN_V3_23 — 函数级设计 + P 分层序列

## 开发序列（依赖序）

D-5 → D-1 → D-2 → D-3 → D-4 → D-6 → P4 版本链

## 各缺陷函数级设计

### D-5（P2 结构）: tests/fixtures/recall_regression_set.json

```json
{
  "description": "召回率回归集 — 已知真实缺陷语料（fixture, 仅测试/评估引用, 不进运行时）",
  "entries": [
    {
      "id": "RECALL-001",
      "defect_class": "JIT compiler type-tracking inconsistency (array map transition)",
      "family": "MEMORY-SAFETY",
      "cwe": ["CWE-843"],
      "profile_signals": {"surface_model": "semantic", "generation_layers": ["jit"]},
      "expected_hypothesis": "compiler reduction/inlining alters elements-kind assumptions -> type confusion",
      "case_source": "CVE-2026-85046; v8 audit 召回复盘 1 (lessons.md 追记)"
    }
  ]
}
```

- 消费者：skill-optimizer 阶段 0 必读清单（评估输入）+ 阶段 6 验收判据引用；
  **不建运行时度量工具**（过设计防线，消费者不足）。
- 字段即契约：test_v323 断言 schema。

### D-1（P3 内容）: fidelity 条款所有权核实

编辑点 SKILL.md:1051（SWR-V3.10.2-001~004 段）追加：

> `equivalent` 档的 fidelity 判定必须含**所有权模型核实**：harness 须列出目标对象在
> 真实代码中的引用持有图（谁 AddRef/谁释放/释放时机），并证明 harness 的破坏/交错
> 时序映射到该持有图的真实释放路径；无法映射的时序不得作为缺陷前提（Firefox 实案：
> 家族强引用层使"OTS 期间释放"不可达，harness 人为交错致误报）。

R5 段（:256 后实证规范处）补一行 harness 编写核对步骤：
「equivalent harness 自检：释放时序↔真实持有图映射表」。

### D-2（P3 内容）: 报告层边界声明

报告结构段（SKILL.md:305-347）补：

> **修复建议与结论（主代理补充）**段须附「发现包络边界声明」：本审计覆盖输入处理
> 缺陷（输入面→语义轴→sink）；不覆盖（a）JIT/编译器优化正确性层（类型追踪/去优化
> 正确性——需差分/模糊测试通道），（b）闭源依赖内部实现，（c）非目标平台变体。
> 缺失 = warn 注记（不阻断）。

### D-3（P3 内容）: 三处

1. 严重度表：`MEMORY-SAFETY（787/125/416/415/476/190/129/843）`
2. surface_map_domain.md 语义轴段追加（profile 门控注入段）：

```
## JIT 优化正确性层轴（v3.23, SWR-V3.23-003 —— 仅 generation_layers 含 jit 时注入）
- 轴 = JIT 优化正确性命名空间族：map/类型追踪、去优化帧正确性、归约/内联的
  elements-kind 假设、speculation 回退；
- 一轴一族假设义务：如「归约/内联改变 elements-kind 假设 → 类型混淆 CWE-843」；
- 轴锚点证据义务同语义轴（file:line 可 grep 核实）。
```

3. target_profile.py：generation_layers 建议逻辑追加 jit 信号：

```python
JIT_SIGNALS = ["src/compiler/maglev", "src/compiler/turbofan", "src/jit",
               "jit_compiler", "src/backend"]
# 目录/文件名命中 → recommends generation_layers+jit（仅建议，主代理签收）
```

（实现时放 `_suggest_layers()` 内，复用现有"两段式局部署名"输出形态。）

### D-4（P3 内容）: differential 发现化提示

SKILL.md R2 假设生成段追加（提示级）：

> surface_model=semantic/hybrid 且 generation_layers 含 jit 的目标，R2 可（可选）对
> 语义轴关键操作跑 `differential` 探针（解释器 vs JIT / 多 JIT 层 / 元素类型变体）
> 比对分歧——分歧即假设。实证模板复用，无新义务。

differential_probe.py docstring 追加用途段（逻辑零改动）。

### D-6（P3 内容）: biz_hypothesis.md 注入条款

模板追加：

```
## R2 进行中结论注入（v3.23, SWR-V3.23-006）
主代理派发本任务书时须附与本假说相关 surface 的 R2 进行中结论（keep/drop 条目+
理由）；R2 未完成时标注「R2 未出结论」。R4 与 R2 并行时此段防止同一事实双通道
矛盾至 gate ③b 才暴露（WebKit 实案）。
```

## P 分层序列

```
P1 机械: 无（本版无判定函数缺陷）
P2 结构: D-5 fixture + test_v323 schema 守卫
P3 内容: D-1/D-2/D-3/D-4/D-6（条款与模板注入）
P4 版本链: TOOLING_VERSION 3.23 + 版本守卫 + SKILL.md 增量段 +
          REQUIREMENTS_TRACKING 手工段 + 资产计数守卫
```
