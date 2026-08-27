# v3.8 实战缺陷修复 — 系统方案 / 系统需求 / 软件方案 / 软件需求

> 输入: elasticsearch/quarkus 双项目验证审计暴露的 4 项 skill 机械层缺陷
> （已记入 lessons/SKILL_LESSONS_elasticsearch.md 与 SKILL_LESSONS_quarkus.md）。
> 本文只收这 4 项 + 仓库一致性；nacos #7 同源项一并闭环。

## 一、系统方案

**目标**: 关闭双项目验证审计暴露的 4 项机械层缺陷，全部为通用机制修复。

**四条纪律（用户约束，逐项自查）**:
- 无偏见: 4 项修复均为语言无关机制（规模扫描界 / 契约字段 / JDK 机制枚举 / 几何偏好），
  零项目名、零语言专属逻辑、零审计史带入。
- 通用型: 每项修复作用于机制层（grep 扫描语义 / collect 契约 / 枚举值 / 修正流排序），
  不改变任何语言/项目形态的行为分支。
- 无死代码: 不改动既有调用契约（_grep 新参数带默认值，旧调用零变化）；r35-collect
  只补字段不删字段。
- 可落地: 每 SWR = 代码 + 回归测试。

## 二、系统需求 (REQ)

| id | 需求 | 证据 |
|---|---|---|
| REQ-V3.8-D1 | 大仓库形态判定无假阴性: listener 信号扫描不以文件数截断（hit 驱动 + 全树兜底） | ES 31k java 文件下 Netty4HttpServerTransport.java:183 真命中但机械未报（_scan_files 400 上限） |
| REQ-V3.8-D2 | refutation 收集契约完备: survived/votes/refute_count 落盘，与渲染器 _refutation_line 一致 | ES 8 候选 summary 列恒「未复核」，主代理手工归一（nacos #7 同源闭环） |
| REQ-V3.8-D3 | boundary_kind 枚举覆盖 Panama FFM（java.lang.foreign）形态 | ES libs/native 6 条 boundary 被迫归一 ffi-other |
| REQ-V3.8-D4 | 锚点修正流: 多命中时 suggested_line 取离声称行最近的命中 | ES 锚点裁决 4 处 / quarkus 17 处，同分取首候选误导修正 |
| REQ-V3.8-D5 | 仓库一致性: elasticsearch/quarkus 两份新 lesson 同步进 v3 开发仓库 | lessons_recorder 写入部署副本，v3 落后 |

## 三、软件方案

| REQ | 文件 → 函数 | 改动 |
|---|---|---|
| D1 | tools/target_kind.py → `_scan_files` / `_grep` | `max_files=None` 语义 = 全树扫描（不截断）；`_grep` 透传该参数（默认 400 保持旧契约）；listener 调用点传 `max_files=None`——命中 max_hits=12 即早退，最坏全树无 token 时为一次性秒级全扫描（R0 单次成本） |
| D2 | tools/batch_verify.py → `stage_r35_collect` | refutation dict 补 `votes=len(decs)` / `refute_count=len(kills)` / `survived=len(kills)<2`（与 demote 语义互斥一致，KILL=2 阈值不变） |
| D3 | surface_mapper.py → `BOUNDARY_KINDS` + boundary 域 guide | 枚举补 `panama`（义务入库三问已过: 触发=Java FFM 项目渐成主流; 消费者=boundary validate + 报告 B.3 FFI 表; 裁掉丢什么=Panama 与 JNI 风险形态差异） |
| D3 | task_templates/surface_map_domain.md | boundary 行示例枚举补 panama |
| D4 | surface_mapper.py → `validate_surfaces` | 全文件多命中时按 \|line-claimed\| 升序，suggested=最近命中、suggested_all=其余按距离序；错误消息两行并显 |
| D5 | lessons/ | 拷贝 SKILL_LESSONS_elasticsearch.md / SKILL_LESSONS_quarkus.md + README 表补行 |

## 四、软件需求 (SWR)

| id | 可测断言 | 测试落点 |
|---|---|---|
| SWR-V3.8-030 | 401+ 文件仓库、listener token 位于 walk 序末位文件 → listener app 信号命中（旧版假阴性） | tests/test_v38.py |
| SWR-V3.8-031 | journal 2 证伪者 0 证伪 → refutation{votes:2, refute_count:0, survived:true}; 2 证伪 → demote=true + survived=false | tests/test_v38.py |
| SWR-V3.8-032 | validate 接受 boundary_kind="panama" | tests/test_v38.py |
| SWR-V3.8-033 | snippet 多命中（近/远各一）→ suggested_line=近命中 | tests/test_v38.py |
| SWR-V3.8-034 | surface_map_domain.md 含 panama 枚举 | tests/test_v38.py |

## 五、验收

- `pytest tests/` 全绿（基线 238 + 5 组新用例）。
- 既有 fixture 行为零变化（_grep 默认参数不变；r35-collect 只增字段；BOUNDARY_KINDS 只增枚举值）。
