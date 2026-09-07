# REQ_V3.27 — 引擎形态知识基座补种（2026-09-08，QuickJS 阶段 6 验收审计复盘）

> 本周期触发：v3.26 阶段 6 验收审计（QuickJS，六门禁全 PASS）复盘。
> 性质：**内容型增量**——零新机制（无新门禁/无新阶段/无新强制义务/
> binder 零改动），全部为知识基座补种与任务书文本修正。
> 案例支撑：/root/quickjs/.audit_results/lessons.md §一 5 条（2026-09-07）。

## DDL 消化（v3.21, SWR-V3.21-003）

| lessons 条目 | 处置 |
|---|---|
| 1. R4 通道发现力高于 R2（P3 候选） | **取证裁除**：R4 时序与发现无关（R4 反正会跑），时序机制化无消费者增益（义务三问②）；R2 弱覆盖的根因在知识基座形态盲区，由 D-1~D-3 系统性修复 |
| 2. 未计数裸分配族（P2 结构候选） | → D-1（矩阵 pattern）+ D-4（清单条目） |
| 3. 反序列化计数回绕（P3 内容候选） | → D-3（矩阵 pitfall） |
| 4. 同事实三连发现（正向确认） | 保持（claim_nulled_by 机制零缺陷实录） |
| 5. 证伪者 sibling 升级（正向确认） | 保持（strengthened 通道第三次实证） |

## 缺陷清单（代码核实）

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | 矩阵 C×RESOURCE-DOS 种格缺"资源门禁旁路"pattern | QuickJS 三站点（worker 子 rt 4088/SAB backing 3965/消息队列 4274）全部命中同一族，R2 假设未主动覆盖（CAND-001 靠主代理提级、CAND-003 靠证伪者补强、H1-F1 靠 R4） | patterns 追加一条"资源门禁强制点=计数分配器包装层; 裸 malloc/mmap/第三方分配器站点逐一枚举" | resources/language_issue_matrix.json C×RESOURCE-DOS 格 |
| D-2 | 矩阵 C×RESOURCE-DOS 种格缺"子上下文继承"pitfall | --memory-limit/--stack-size 均不继承 worker 子 rt + 哨兵值 fail-open（H7-F2/F3 实录） | pitfalls 追加"子执行上下文（worker/线程/子 rt）的资源参数继承矩阵逐项核对；哨兵值（0/-1/非法）语义 fail-open 还是 fail-closed" | 同上格 |
| D-3 | 矩阵 C×MEMORY-SAFETY 种格缺"反序列化计数回绕"pitfall | H2-F1：cpool_count=2^28 使 int 算术回绕 → 136B 分配 + 越界写 → 确定性 SIGSEGV（4KB 载荷） | pitfalls 追加"序列化/反序列化读取器的尺寸计算必须 size_t 且逐项溢出检查；计数 ≤ 剩余输入/单元素最小占用" | resources/language_issue_matrix.json C×MEMORY-SAFETY 格 |
| D-4 | 检查清单缺"限额旁路枚举"条目 | 同 D-1 三站点 + 哨兵 fail-open——verifier 自查面无此维 | 新增 CK-LIMIT-BYPASS-ENUM（family=resource-dos，binding cwe 770/789 + 多词短语 keywords，applies_to verifier/refuter，5 steps） | resources/checklist_library.json（44→45） |
| D-5 | R4 任务书缺正向确认书写惯例 | H7 代理产出非枚举 claim_type（default_reachability 等）+ H3 代理对核实类条目用 severity="none"（r4-collect 告警按设计拦截，但偏差应源头减少） | 模板补"正向确认条目惯例"段（核实类/防御到位类：severity=low + evidence 注明核实结论；claim_type 仅枚举值，缺枚举值置 null） | task_templates/biz_hypothesis.md |

## 义务入库三问（逐项）

- D-1~D-3：①触发=R2 假设生成读 cells（既有消费端，SWR-V3.18-002）；②消费者=主代理假设空间提示；③裁掉丢什么=同族三站点靠三条兜底通道撞出（QuickJS 实录）。
- D-4：①触发=checklist_binder cwe/keywords 绑定（既有管线）；②消费者=verifier/refuter 自查注入；③裁掉丢什么=限额旁路维度零自查面。
- D-5：①触发=R4 任务书派发；②消费者=R4 代理；③裁掉丢什么=枚举偏差依赖 collect 兜底告警（H7 实录）。

## 修法形态纪律

- 零自动改写：全部提示级/数据级 ✓
- 零新机制：binder/loader/门禁/队列零改动 ✓
- 去项目化：新条目全部机制形态，项目名只进 source_lessons（机器守卫 test_deproject 扫描覆盖矩阵与清单——新条目必须过） ✓

## 召回率回归集评估

本周期缺陷属知识基座/任务书文本类，回归集（发现力 fixture）方向零重叠——不适用；回归集将用于下一场新项目验收审计的发现力对照。

## 开发序列

P3 内容（矩阵/清单/模板）→ P4 版本链 → 测试 → 安装提交。

## 验证命令

```bash
python3 -m pytest tests/ -q                     # 全量回归（472 基线 + test_v327 新增）
python3 -m pytest tests/test_deproject_assets.py -q   # 去项目化扫描（新条目必过）
python3 language_issue_matrix.py cells c        # 新条目可读
./install.sh ~/.claude/skills/reachable-critical-audit
```

## 验收判据（Phase 3.27）

全量回归全绿 + test_v327 新增用例全绿（每 SWR ≥1 用例含反面分支）+
去项目化扫描 0 命中 + install 双副本同步 + 资产计数守卫同步（清单 44→45
正文节与附录计数同步更新）。
