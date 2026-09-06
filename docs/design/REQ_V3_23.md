# REQ_V3_23 — Firefox real-target 验证轮 + CVE-2026-85046 召回复盘缺陷修复

版本: v3.23 | 日期: 2026-09-06 | 驱动: Firefox real-target 验证轮（H3-F1 反证）+
v8 召回复盘（CVE-2026-85046）+ 战略欠账（召回率回归集）

## 缺陷清单表

| # | 缺陷（代码核实） | 案例支撑 | 修复 | 编辑点（阶段 1 实测） |
|---|---|---|---|---|
| D-1 | fidelity=equivalent 判定只保证机制复刻（函数形态），不核实所有权/生命周期复刻——等价 harness 可在真实代码不可达的释放时序上构造人为交错，六门禁/独立复核/R5 均放过 | Firefox lessons §三.1: H3-F1 gfxUserFontEntry UAF 误报（真实构建 1033+752 次 OTS 派发零中途释放；gfxUserFontFamily::AddFontEntry(RefPtr) 家族强引用层被 harness 遗漏） | fidelity 三档条款补「所有权模型核实」要求（equivalent 档判定与使用前逐层核对引用持有图）；harness 编写侧加核对步骤 | SKILL.md:1051（SWR-V3.10.2-001~004 段）+ harness_manuals/ENVIRONMENT_PROBES.md 或 R5 段 |
| D-2 | 发现包络边界未声明：JIT 优化正确性层（map 追踪/类型格/deopt）与闭源依赖内部（CFNetwork/libsoup）在审计包络外，报告却无该声明——构成隐含的"全覆盖"误导 | v8 lessons 召回复盘 1（CVE-2026-85046: 审计时漏洞在树、触达同文件区域、六门禁 PASS 仍漏）；WebKit HYP-B-009 drop（GTK 构建无调用者）+ Safari 实测冻结补证 CFNetwork 边界 | R6/报告层加「发现包络边界声明」条款：报告必含包络外声明段（提示级，无新门禁） | SKILL.md 报告段:305-347 + R6 段:582 |
| D-3 | JIT 优化正确性假设族缺失：假设空间无"编译器类型追踪不一致→类型混淆"（CWE-843）族；严重度机械映射表亦无 843 | v8 召回复盘 1（85046 类型混淆 CVSS 8.8；审计假设集 0 命中该族） | ① 严重度映射表 MEMORY-SAFETY 严重档补 CWE-843；② 语义轴测绘段补「JIT 优化正确性层」轴（profile 门控: generation_layers 含 jit 时注入）；③ target_profile.py generation_layers 建议逻辑补 jit 信号（源码目录信号: src/compiler/maglev|turbofan、*jit* 目录） | SKILL.md:338-347；task_templates/surface_map_domain.md:63-73；tools/target_profile.py:102-129 |
| D-4 | differential 探针仅定位为 R5 实证模板（"配置轴类声称首选"），未作为引擎类目标的 R2 假设生成补充扫描通道——85046 类的发现通道（同输入多配置差分）在发现阶段不存在 | v8 召回复盘 1（85046 由差分/模糊测试发现；skill 无发现级 fuzzing 通道） | differential 模板头部说明 + SKILL.md R2 假设生成段补「引擎类目标 differential 扫描通道」提示（profile 门控、提示级） | SKILL.md:268 + R2 段（:160 附近）+ templates/harness/differential_probe.py 头部 |
| D-5 | 召回率回归集缺失：验收/评估只测流程健壮性（六门禁），无"已知缺陷语料→假设生成应命中率"基线 | v8 召回复盘 1 + 记忆索引战略欠账（召回率回归集待用户裁定，本周期裁定入库） | tests/fixtures/recall_regression_set.json 建语料（首样本: CVE-2026-85046 形态特征+预期假设族），阶段 0 必读清单引用为评估输入；不建运行时度量工具（过设计防线） | tests/fixtures/（第一原则：回归锚点仅限测试）+ skill-optimizer 阶段 0 段 + SKILL.md 评估判据处 |
| D-6 | R4 与 R2 并行时 R4 任务书不注入 R2 进行中结论——同一事实双通道矛盾直到 gate ③b 才暴露 | WebKit lessons 二.1（R4 H1 WebSocket deflate 无上限 finding 与 R2 drop 结论冲突实录） | biz_hypothesis.md 补注入条款：R4 任务书须携带与本假说相关的 R2 进行中结论（keep/drop 及理由）；主代理派发时无进行中结论则标注「R2 未出结论」 | task_templates/biz_hypothesis.md |

## 测试守卫约束

- 每条 SWR ≥1 测试用例（含反面分支）
- 版本链五件 + 资产计数守卫同步
- 旧队列复跑（v8/WebKit/firefox）assert_ledger 零新增告警
- 去项目化扫描 0 命中（D-3/D-4 模板正文零项目名——"JIT"是通用技术术语非项目名）

## 开发序列

D-5（fixture 数据）→ D-1（条款）→ D-2（条款）→ D-3（表+轴+profile 信号）→
D-4（提示）→ D-6（模板注入）→ P4 版本链 → 测试验收 → 安装提交

## 验证命令

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -x -q
python3 tools/batch_verify.py /root/v8 --stage assert-ledger
python3 tools/batch_verify.py /root/WebKit --stage assert-ledger
python3 tools/batch_verify.py /root/firefox --stage assert-ledger
python3 tests/run_deproject_scan.sh  # 或等价去项目化扫描
```
