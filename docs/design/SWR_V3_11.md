# SWR_V3_11 — 软件需求（v3.11 设计缺陷修复）

> 对应文档：REQ_V3_11.md（需求语义）/ SOFTWARE_DESIGN_V3_11.md（改动点）。
> SWR 为可测契约：每条含断言式描述，测试实现见 test_v311.py（11 测试）。
> 原则：旧队列零行为变化；新增行为全部有触发条件或缺省兼容。

## 1. 攻击者主体层级（REQ-V3.11-001）

- **SWR-V3.11-001**：`attacker_tier` 合法值仅 `same_process|same_device_cross_app|
  system_broker|remote`；非法值回退推导 + stderr 告警。
- **SWR-V3.11-002**：缺省推导规则——reachability_type=DIRECT 且 trust_boundary
  含 host_api → same_process；ACROSS_BOUNDARY 且 evidence 含平台组件注入信号
  （导出组件/意图参数/跨应用调用）→ same_device_cross_app；evidence 含网络内容
  信号（远程字节/URL 内容/网络响应）→ remote；无法判定 → 主代理裁决（不机械兜底）。
- **SWR-V3.11-003**：报告问题清单每行尾附 tier 标注（`[tier: x]`）；NEEDS_REVIEW
  候选不标注（终态非 REACHABLE 无申报口径需求）。

## 2. 平台 API 契约库（REQ-V3.11-002）

- **SWR-V3.11-004**：`platform_api_contracts` 条目 schema 含必填 `source`；
  加载时无 source 条目拒收 + stderr 告警（防幻觉契约入库）。
- **SWR-V3.11-005**：条目 `api_pattern` 为平台机制描述形态（具体平台 API 类名
  仅进 probe 位）；去项目化扫描 0 命中。
- **SWR-V3.11-006**：detect_platforms 信号驱动注入——verify/refutation/resurrect
  三层 prompt 均含契约条目（零平台信号零注入，与 v3.10.2 PTM 同管线对称）。

## 3. 模板产物面（REQ-V3.11-003）

- **SWR-V3.11-007**：surface_map_domain 任务书含「生成器/模板产物面」指引段
  （路径信号：tmpl/template/scaffold/generator）。
- **SWR-V3.11-008**：entry_points 可选标记 `instantiated_artifact`（布尔）；
  verifier 步骤 0.5 含「模板 → 实例化产物」存在性判定条款。

## 4. 审计树差异声明（REQ-V3.11-004）

- **SWR-V3.11-009**：scope snapshot 含「构建差异声明」段（构建清单声明的依赖/
  生成物 vs 树内物化状态；空差异也落盘）。
- **SWR-V3.11-010**：报告附录 B 渲染「审计树与部署物差异」段（读 scope snapshot；
  无该段时旧快照兼容跳过）。

## 5. 运行时版本条件（REQ-V3.11-005）

- **SWR-V3.11-011**：verifier 任务书步骤 4 含「运行时版本条件」检查项（版本
  API 级判断/构建变体差异对攻击面维度的影响；按受影响版本区间陈述阻断论证）。

## 6. H4 时序子项与逻辑镜像（REQ-V3.11-006/007）

- **SWR-V3.11-012**：biz_hypothesis 模板 H4 检测要点含「初始化时序注入面」子项；
  SKILL.md H4 表同步。
- **SWR-V3.11-013**：surface_mapper merge 在 language_inventory ≥2 时输出
  `mirror_candidates` 提示（语义相似 + 跨 lang 的面组；仅提示不组族）。
- **SWR-V3.11-014**：hypothesis_filter 任务书含「逻辑镜像枚举」条款（同逻辑面
  多语言实现全覆盖核实）。

## 7. 版本与兼容

- **SWR-V3.11-015**：TOOLING_VERSION=3.11；SKILL.md v3.11 增量段齐备（数据模型
  速查含 attacker_tier/instantiated_artifact/构建差异段/契约族）。
- **SWR-V3.11-016**：v3.10.2 及更早队列样本复跑：六门禁零新增告警、零误判
  （attacker_tier 缺省推导、契约族零注入、旧 scope snapshot 无差异段兼容）。
- **SWR-V3.11-017**：新增测试 test_v311.py 全绿且既有测试全绿（288 基线）；
  源仓库同步分 commit + install + 安装版测试全绿。

## 8. 明确不建（回归护栏）

- 不改 reachability_type 枚举、不加新门禁、不自动组族、不做运行时版本自动检测。
- 契约库唯一「拒收」级校验仅约束新清单族（不触及既有 30 条 CK 清单）。
