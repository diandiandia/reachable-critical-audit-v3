# quic-go 审计 lessons（v3.4.5 验收项目，2026-08-23）

> 来源: /root/quic-go v0.61.0 全流程审计（R0-R6, 41 surfaces / R3 空队 / R4 3 条 confirmed finding）。
> 追溯字段用途: 项目名仅允许出现在 lessons/来源列, 不进入运行时资产（第一原则）。

## 1. 机制缺陷: coverage-ledger lang fallback（SWR 素材 → v3.4.6）

**现象**: `stage_coverage_ledger --write` 在 R3 空队（R2 keep 0, 全防御确认）时,
候选级 lang 无可推主导语言 → `dom = "other"`, 纯 Go 项目 quic-go 的 R4 findings
全部记入 `*xother` 格而非 `*xgo` 格, 覆盖账本失真（本次已人工修正数据）。

**根因**: `lang_of` 只读队列候选 (`c.get("language")/lang/source_file 扩展名`);
候选为空时无回退到 R1 产物 (input_surface.json 的 surface lang /
scope_snapshot 的 language_inventory / context 输出)。

**修复方向（v3.4.6 SWR）**: dom 推导链改为:
候选 lang_freq → input_surface.json surface lang 多数 → language_inventory 主导 →
最后才 "other"。附单测: 空队 + R4 findings + surface lang=go → 账本写 go 格。

**为什么这次能跑通**: R3 空队是合法终态（成熟库全防御确认, 参见 quic-go
filter 24 条 boundary_confirmations）——账本必须能正确处理空队项目,
否则空队项目越多账本 other 格越膨胀。

## 2. R2 filter 全 drop 形态的流程验证点

quic-go 是首个 R2 keep 0 的项目（28 条假设: 0 keep / 4 drop / 24 boundary
confirmations）。流程闭环验证:
- `workflow-script --mode verify` 空队 → `WORKFLOW_NOTHING_TO_DO` (SWR-V3.4.4-003
  机制实战验证) ✓
- 门禁⑦ tracked 计算在空队下的正确形态: tracked_ids = R2 全部假设 surface_ids
  (含 drop 与 boundary_confirmations, 不能只计 keep) ∪ R4 findings tracked_surfaces
  ∪ coverage_bridge; mirror_pairs 传播由 assert_ledger 自动做 ✓
- **注意**: R2 假设的 surface_ids 必须从 hypotheses.json 反查——筛选结果落盘时
  drop/boundary_confirmations 条目若只存 id 会丢覆盖簿记（本次数据质量问题实录,
  主代理落盘时需保留 surface_ids 或落盘后反查补齐）

## 3. filter agent 全防御裁决的主代理复核义务

filter agent 对 28 条假设全判"防御已到位"时, 主代理必须抽样复核最重的
防御确认（本次抽 3 条: header.go:145 先检查后切片 / transport_parameters.go:136
paramLen 先于切片 / receive_stream.go:454 流控先于重组——全部属实）。
抽样复核是"证据裁决"铁律在空队形态下的必要延伸: 全 keep 0 的结论若失真,
R3 会整体放行缺陷; 抽样 3 条 + R4 深度验证 (H1 7 条防御确认逐点与 R2 交叉)
构成双保险。

## 4. R4 深度验证可升级 R2 快筛裁决（合法裁决差异）

H2 的 NewLRUTokenStore finding (0/负值参数 → 远端 NEW_TOKEN 触发 panic) 在
R2 filter 的 HYP-L19 确认里标注"需应用显式传 0, 非攻击者可达"。R4 H2 深度
验证论证: 公共 API 无参数校验 + 文档未禁止 0 语义 + 远端可触发 → 升级为
confirmed (Medium)。快筛 (排除判据) 与深度验证 (前置条件论证) 是不同深度层,
裁决差异合法; 主代理合并时记录差异原因（本次记入 ACCEPTANCE 与报告）。

## 5. 实证双轨: CONFIRMED 探针 vs SOURCE_FACT（环境限制）

- H2/H4/H5 用独立探针实测 (slice panic 复现 / pprof 200 / 除零与空指针) → CONFIRMED
- H3/H7 因环境离线 (模块缓存空, Go proxy 不可达, go build/test 不可行) → SOURCE_FACT
  (源码级事实, 带可复跑测试方案说明)
- 全库 frame_sorter 2600 万+ 次模糊零 panic (H2 附带) 是源码级最强的实证
- 教训: 库型 Go 项目在离线环境, 依赖 stdlib-only 探针 + 提取无外部依赖源码
  文件 (如 token_store.go + linkedlist) 做最小复现是可行路径

## 6. R1 mirror_pairs 覆盖传播的一次缺失实录

SURF-DATA-010 (data 域 token LRU) ↔ SURF-STORAGE-008 (storage 域 token LRU)
是同一 lruTokenStore 实现的两侧, R1 merge 未自动成对 (12 对 mirror 无此对) →
HYP-L19 覆盖 DATA-010 后 STORAGE-008 未自动传播 → 主代理以 coverage_bridge
补桥 (basis: 同一实现两侧)。教训: 多域测绘同一文件时, mirror_pairs 事后人工
核对一次（storage/data 域 token_store.go 同文件双面是最常见形态）。
