# REQ_V3_40 — Hadoop 验收复盘缺陷修复需求（v3.40）

来源: /root/hadoop/.audit_results/lessons.md「对 skill 的教训」7 条（2026-09-10, TOOLING 3.39 下执行）

## 缺陷清单表（# / 缺陷（代码核实） / 修复 / 编辑点 / 分层）

| # | 缺陷（取证核实） | 修复 | 编辑点（实测） | 分层 |
|---|---|---|---|---|
| D-1 | grade_verdict 判级段不读 fidelity: status=confirmed 的 mechanism 档 empirical 被机械升 empirically_confirmed, 违反 SKILL.md「mechanism 档不得升」条款 | fidelity 分支: mechanism 档 → 判级落 edge_proven + errors 注记; equivalent/real_target 维持现行为 | src/evidence_ledger.py:146-148 (empirical 判级三元) | P1 机械 |
| D-2 | verifier 任务书无「攻击者字节到达 sink」独立义务: CAND-024 四边全真仍为触发器链非数据流链, 2/2 证伪 | 步骤 3 后插「步骤 3.5 攻击者字节承载判定」: 实证类 claim 必须标注承载跳 | tools/batch_verify.py 任务书构建段 (步骤 3 跨边界判定 与 步骤 4 阻断检测 之间, ~3056-3060 行区) | P3 内容 |
| D-3 | 修复驱动假设只挖单点 (SWR-V3.32-002), 无「同族实例×加固状态」矩阵枚举: ZK 已修/LevelDB 未修、内层修/外层漏 两例均源出此模式 | checklist +1 条 CK-SIBLING-FIX-AUDIT (修复触发型, 与 CK-SIBLING-CONSISTENCY 端关键词触发型互补非重造) | assets/resources/checklist_library.json 尾部 (48→49) | P3 内容 |
| D-4 | filter 判「位域 ordinal 越界」无 bit 长度证据义务: TYPE 3bit 声称与源码 2bit 不符, 锚点错到 real_target 才纠正 | hypothesis_filter 排除判据 4 后增位域证据条款: 判 ordinal 越界前必须 Read 枚举声明行核对 bit 长度与枚举值数 | assets/task_templates/hypothesis_filter.md:23-24 之间 | P3 内容 |
| D-5 | setuid 辅助二进制 real_target 部署拓扑无手册指引: CAND-001 实证 12 轮失败日志收敛, 成本全在部署拓扑长尾 | ENVIRONMENT_PROBES.md 增「setuid 辅助二进制部署拓扑」段 (五要素清单 + 失败日志→修复映射) | assets/harness_manuals/ENVIRONMENT_PROBES.md 尾部 | P3 内容 |
| D-6 | 「防御已到位」核查不区分两种默认关方向: feature 默认关=降可达性, 鉴权 gate 默认关=升可达性; B2 批次 13 条全 keep 的根因 | hypothesis_filter 排除判据 5 增默认关方向判定句 | assets/task_templates/hypothesis_filter.md:24-26 段内 | P3 内容 |
| D-7 | r35-collect 采集 refutation 实测数字但不机械扫描: AXFR 4 rrsets/fd-hold 3/3 使 2 候选恢复全靠主代理手工发现 | r35-collect 输出 empirical_backfill_candidates (warn 级清单, 主代理裁决, 不自动改写) | tools/batch_verify.py r35-collect 段 (~1575-1595 strengthened 收集块后) | P2 结构 |

## 测试守卫约束（每 SWR ≥1 用例，含反面分支）

- SWR-V3.40-001: mechanism 档 + status=confirmed → grade==edge_proven + errors 含注记; real_target/缺省 fidelity → empirically_confirmed 不变（回归面）
- SWR-V3.40-002: 任务书含「攻击者字节承载」义务文本（字符串断言）
- SWR-V3.40-003: checklist 49 条 + 新 id 存在 + source_lessons 追溯字段格式
- SWR-V3.40-004/006: hypothesis_filter.md 含两条款关键词
- SWR-V3.40-005: ENVIRONMENT_PROBES.md 含五要素段落
- SWR-V3.40-007: refutation 含实测数字 → collect 输出含该候选提示; 无实测数字 → empirical_backfill_candidates 为空（反面分支）

## 开发序列

P1 (D-1) → P2 (D-7) → P3 (D-2/D-3/D-4/D-5/D-6) → P4 版本链五件

## 验证命令

```bash
cd /root/reachable-critical-audit-v3 && python3 -m pytest tests/ -x -q   # 全量回归
python3 -m pytest tests/test_v340.py -v                                  # 新守卫
python3 src/signature_lib.py selfcheck /root/hadoop                       # 资产通用性
python3 tools/batch_verify.py /root/hadoop --stage assert                 # hadoop 队列复跑零新增
# 代表旧队列 (gpac/freetype/av 等按存在性) 复跑 assert_ledger 零新增告警
```
