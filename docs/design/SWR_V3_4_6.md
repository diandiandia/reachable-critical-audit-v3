# SWR-V3.4.6 需求（4 条）

> 设计: SYSTEM_DESIGN_V3_4_6.md。来源: quic-go 空队验收实录（lessons/SKILL_LESSONS_quic_go.md）。
> 里程碑: M1 = 代码级（001/002/003）, M2 = 制度级（004）。

---

## SWR-V3.4.6-001: coverage-ledger 主导语言推导链回退（M1）

**缺陷**: `stage_coverage_ledger --write` 在队列候选为空（R3 空队, R2 keep 0）
时 `dom = "other"`, 项目真实主导语言（R1 产物已携带）被丢弃, 账本失真
（quic-go 全 Go 项目误记 other 格实录）。

**修复**: `stage_coverage_ledger` 的 dom 推导链改为:
1. 队列候选 lang_freq 多数（既有行为, 候选非空时不变）
2. 回退 1: `input_surface.json` surfaces[].lang 多数（`--write` 时读
   `<project>/.audit_results/input_surface.json`, 缺文件则跳过）
3. 回退 2: `architecture_context.json` language_inventory 主导（文件数加权;
   scope_snapshot.json 无 language_inventory 字段, 来源为 R1 context 产物）
4. 最后: "other"（仅当上述全缺）

R4 findings 聚合沿用 dom; 空队时 dom 来自回退链而非 "other"。

**验收**:
- 单测 1: 空队 + input_surface lang=go → 账本写 go 格, other 零新增
- 单测 2: 候选非空（lang=rust）→ 仍按候选 rust 计（回退不破坏既有行为）
- rpcx 验收: `--stage coverage-ledger --write` 输出 `*xgo` 格计数,
  `*xother` 无新增

---

## SWR-V3.4.6-002: R2 filter 产出 surface_ids 保真（M1）

**缺陷**: filter 模板 canonical 输出中 boundary_confirmations/drop 条目未强制
surface_ids 字段（keep 有）; 主代理落盘/工具聚合时无保真校验, 丢字段 →
门禁⑦ tracked 覆盖虚低（quic-go 41→31 假缺口实录）。

**修复**:
- ① `task_templates/hypothesis_filter.md` canonical 输出 schema 扩展:
  keep/drop/boundary_confirmations 三组条目均强制 `surface_ids` 数组
  （缺字段拒收, 模板注明）
- ② `r2_guard.py`（或新增落盘 helper）: 落盘后校验 bc/drop 条目
  surface_ids 存在; 缺失时自动从同目录 hypotheses.json 按 id 反查补齐
  （对旧产出兼容, 补后写 `restored_from_hypotheses` 标记）

**验收**:
- 单测: 构造缺 surface_ids 的 bc 条目 → 落盘后补齐且与 hypotheses.json
  反查一致
- 集成: r2_filter_result 全量条目 surface_ids 非空（quic-go 实录产物
  用新代码重验零缺失）

---

## SWR-V3.4.6-003: merge 同文件跨域未成对提示（M1）

**缺陷**: merge 的 mirror 检测基于冲突启发式（同入口多域）; "同文件双面
但 entry_points 不重叠"形态（token_store.go 被 data/storage 两域测绘
不同函数）不产生冲突 → 不生成 mirror 对 → 覆盖传播缺口, 且无人工核对
提示（quic-go SURF-DATA-010↔SURF-STORAGE-008 实录）。

**修复**: `surface_mapper.py merge` 输出追加
`same_file_cross_domain_pairs`: 同文件、不同域、entry_points 无重叠的
surface 对清单（含各自 entry 位置）。**提示不自动成对**——主代理裁决
补 mirror 或 coverage_bridge（跨域同实现语义判定属主代理）。

**验收**:
- 单测: 同文件双面 fixture → 清单非空; 不同文件/同域 → 空
- quic-go 实录: 用新代码重跑 merge → 清单含 DATA-010↔STORAGE-008

---

## SWR-V3.4.6-004: R2 全 keep 0 抽样复核条款（M2, 制度级）

**缺陷**: SKILL.md R2 段无"keep=0 时主代理抽样复核"条款; filter 全防御
裁决若失真（过度放行）, R3 空队会整体放过缺陷（quic-go 主代理手动抽样
3 条复核属自觉行为, 未制度化）。

**修复**: SKILL.md R2 段追加条款:
> 筛选结果 keep=0（或 boundary_confirmations ≥ 全量 80%）时, 主代理必须
> 抽样复核 ≥3 条 boundary_confirmations 的真实代码防御点（抽样清单落盘
> r2_filter_result.spot_checked）; R4 深度验证与 R2 交叉核对构成双保险。
> 抽样复核是"证据裁决"铁律在空队形态下的必要延伸（quic-go 实录）。

**验收**:
- 文档 lint: SKILL.md 含条款文本
- quic-go 实录可对照（spot_checked 已存在: HYP-L1/L12/L27）

---

## 验收总判据

1. 单测 170+4 全绿（新增 4 用例见设计 §验证策略）
2. 既有机制零回退（fixture 基线对照, stash 验证）
3. rpcx 新项目验收通过（M1 实战验证 + 覆盖账本缺口格回填 + 六门禁全 PASS）
4. ACCEPTANCE_V3_4_6.md 落盘后 install + 提交
