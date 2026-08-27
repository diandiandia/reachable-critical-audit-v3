# v3.8 批次硬化 — 系统方案 / 系统需求 / 软件方案 / 软件需求

> 来源: 2026-08 五项目 JVM 批次审计 (zookeeper/kafka/tomcat/nacos/shardingsphere) 的
> 5 份 lesson (lessons/SKILL_LESSONS_*.md)。lesson 共暴露 ~15 类缺陷, 本文只收
> **机械层工程缺陷** (8 类); 方法论沉淀 (复活波/威胁模型裁决/实证模板/佐证器降噪等)
> 不入本文, 留在 lesson 与 memory。

## 一、系统方案

**目标**: 关闭批次审计暴露的机械层缺陷——即「六门禁零违规、但判定/收集/渲染的
机械实现误导结论」这一类风险 (最坏实例: zookeeper 渲染器静默丢弃整档 Critical)。

**三条设计纪律 (本文所有需求的裁决标准)**:
- **C1 通用性**: 修复必须是语言无关机制。禁止把单项目/单语言形态写死进通用资产
  (SKILL.md 第一原则: 资产不得携带项目专属名, mbedtls 复盘先例)。
- **C2 最小化**: 优先「任务书一句话 / 现有流程复用」。不为可避免的问题新建机制;
  收集类校验只 warn 不阻断 (阻断需要新重试机制 = 违反 C2, 且批次流会被打断)。
- **C3 可落地**: 每个软件需求 = 代码改动 + 回归测试; 每条改动带 SWR id 注释。

**已否决的候选修复** (按纪律裁决, 记录在案):
| 候选 | 否决理由 |
|---|---|
| L1 词族按语言排除 `<<`/`getName` (zookeeper 佐证器噪音建议) | 违反 C1: 单项目噪音观察驱动的语言特调; 佐证器低边际价值已由方法论沉淀覆盖, 不影响判定 |
| 机械合并边拆分器 (shardingsphere edge-split 工具化) | 违反 C2: 边应由 verifier 按契约产出; 拆分器是重复机制。改为任务书契约 + 降级报错附计数 |
| r4-collect 非法枚举**拒收** | 违反 C2: 拒收需要重试/重派机制; lesson 明示的正确语义是「warn + 强制主代理归一」 |

## 二、系统需求 (REQ)

| id | 需求 | 证据 (lesson) |
|---|---|---|
| REQ-V3.8-B1 | 形态判定盲区: target_kind 监听模式覆盖 NIO channel 服务器形态; maturity 标签识别 `release-X.Y.Z` 形态 | tomcat【形态判定】/zookeeper【形态判定】 |
| REQ-V3.8-B2 | R4 收集枚举完整性: 非法 verdict/severity 枚举必须显式告警, 不得静默入库或静默兜底误导 | tomcat【skill 缺陷·未修】①② |
| REQ-V3.8-B3 | 验证任务书契约: edge_evidence 逐跳契约明示; 混合语言项目跨语言调用点搜索义务; 机械降级报错附计数 | kafka【skill 缺陷】①② + shardingsphere #5 |
| REQ-V3.8-B4 | R1 测绘任务书: 五域 canonical 包裹形态 + boundary 域示例 + 路径白名单逐字符核实 checklist | nacos #1/#2 |
| REQ-V3.8-B5 | 锚点证据硬化: 声称行是注释/空行时不得放行, 走修正流 | zookeeper【skill 缺陷·未修】③ |
| REQ-V3.8-B6 | R0 版本基线: git describe 仅参考, 构建清单佐证 | shardingsphere #1 |
| REQ-V3.8-B7 | 任务书韧性: R4 findings 增量落盘指令固化 | tomcat【韧性教训】 |
| REQ-V3.8-B8 | 仓库一致性: 回填部署副本已修 2 项 + 批次 lesson 同步进 v3 | diff 审计 |

## 三、软件方案

| REQ | 落点 (file → 函数) | 改动 |
|---|---|---|
| B1 | `tools/target_kind.py` → `LISTEN_PATTERN` | 加 token `ServerSocketChannel\.open\|new\s+ServerSocket` (LISTEN_PATTERN 本就是多语言 token 库, 补缺是覆盖而非语言特调) |
| B1 | `surface_mapper.py` → `_detect_maturity` | 正则 `v?(\d+)\.(\d+)` → `(?:v\|release-)?(\d+)\.(\d+)` |
| B2 | `tools/batch_verify.py` → `stage_r4_collect` | 新增 `_warn_r4_enums(items)`: 假设级 verdict 白名单 {confirmed, reviewed_clean, not_applicable}、finding 级 severity 白名单 {critical, high, medium, low} (大小写不敏感)、title 匹配 `[refuted]`/`informational` → stderr JSON warn, 不阻断 |
| B3 | `tools/batch_verify.py` → `_build_prompt` 步骤 1 | 加 edge 契约段 (逐跳一条, 条数 ≥ 链长-1, 禁止合并边) + 跨语言调用点段 (别名/桥接/绑定层; 函数存在≠被调用) |
| B3 | `workflow_export.py` → `refute_prompt` lens 0 | 调用边真实性视角补跨语言 grep 一句 |
| B3 | `evidence_ledger.py` → `grade_verdict` | 降级错误附 `edges={n} chain={m} 需≥{m-1}` + 合并边提示 (保留原错误前缀, 防既有断言漂移) |
| B4 | `task_templates/surface_map_domain.md` | 五域一律 canonical 包裹形态声明 + boundary 行示例 (B-xxx/boundary_kind/lang_pair) + 路径白名单 checklist |
| B5 | `surface_mapper.py` → `validate_surfaces` | 窗口命中但声称行是注释/空行且自身未命中 → 转 mismatch + suggested_line (复用现有修正流, 与 r2_guard.anchor_check 分层不重叠: R1 validate 管 surface 证据, R2 anchor_check 管假设锚点) |
| B6 | `SKILL.md` → R0 步骤 1.5 | 加版本佐证一句 (构建清单 pom.xml/Cargo.toml/package.json/setup.py 等) |
| B7 | `task_templates/biz_hypothesis.md` | 落盘契约段加「每 2-3 条 finding 覆盖写盘」; verdict 段加部分证伪语义 + [refuted] 条目规则 + severity 枚举说明 |
| B8 | `evidence_ledger.py` / `tools/batch_verify.py` / `lessons/` | 从部署副本回填 `(?<![\w.])` 正则与 critical 白名单; 拷贝 5 份批次 lesson; 修 lessons/README.md 表 |

## 四、软件需求 (SWR)

| id | 可测断言 | 测试落点 |
|---|---|---|
| SWR-V3.8-001 | LISTEN_PATTERN 命中 `ServerSocketChannel.open()` 与 `new ServerSocket(` → app 方向信号 | tests/test_target_kind.py (新) |
| SWR-V3.8-002 | tag `release-3.9.5` → mature; `release-0.2.0` → developing | tests/test_surface_mapper.py |
| SWR-V3.8-003 | r4-collect 收到非法 verdict (PARTIAL 等) → stderr 告警含原文, 落盘不阻断 | tests/test_batch_verify_v3.py |
| SWR-V3.8-004 | r4-collect 收到非法 severity (informational 等) → stderr 告警 | 同上 |
| SWR-V3.8-005 | r4-collect 收到 title 标 [refuted]/informational 的 finding → stderr 告警 | 同上 |
| SWR-V3.8-006 | `_build_prompt` 输出含 edge 契约与跨语言调用点段 (文本断言) | 同上 |
| SWR-V3.8-007 | grade 降级错误含 `edges=`/`chain=` 计数, 原错误前缀保留 | tests/test_evidence_ledger.py |
| SWR-V3.8-008 | validate: 声称行是注释而窗口邻行命中 snippet → 拒收 + suggested_line | tests/test_surface_mapper.py |
| SWR-V3.8-009 | surface_map_domain.md 含五域声明 + boundary 示例 + 白名单 checklist | tests/test_doc_lint.py 或 test_v344.py |
| SWR-V3.8-010 | biz_hypothesis.md 含 [refuted] 规则与增量落盘句 | 同上 |

## 五、验收

- `pytest tests/` 全绿 (基线 216 passed + 新增 SWR 用例)。
- 六门禁/既有 fixture 行为零变化 (本方案只动机械告警与任务书文本, 不动裁决逻辑)。
