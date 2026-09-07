# SWR_V3.27 — 引擎形态知识基座补种

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.27-001 | 矩阵 C×RESOURCE-DOS 格 patterns 追加资源门禁旁路条目 | D-1。QuickJS 三站点实录（worker 子 rt/SAB backing/消息队列拷贝）；条目机制形态零项目名 | test_v327: cells c 输出含新 pattern 串 + deproject 扫描 |
| SWR-V3.27-002 | 矩阵 C×RESOURCE-DOS 格 pitfalls 追加子上下文继承条目 | D-2。--memory-limit/--stack-size 不继承 + 哨兵 fail-open 实录 | test_v327: cells c 输出含新 pitfall 串 |
| SWR-V3.27-003 | 矩阵 C×MEMORY-SAFETY 格 pitfalls 追加反序列化计数回绕条目 | D-3。H2-F1 int 回绕确定性 SIGSEGV 实录（4KB 载荷） | test_v327: cells c 输出含新 pitfall 串 |
| SWR-V3.27-004 | 清单库新增 CK-LIMIT-BYPASS-ENUM（44→45） | D-4。binding cwe 770/789 + 多词短语 keywords（禁裸词：限额/CJK 子串语义；ASCII 用多词短语）；applies_to verifier/refuter；steps 5 条枚举（强制点/裸分配站点/子上下文继承/哨兵语义/检查点先后） | test_v327: 条目结构完整 + id 全局唯一 + 去项目化 + 资产计数断言同步 |
| SWR-V3.27-005 | biz_hypothesis 模板补正向确认条目惯例 | D-5。H7 非枚举 claim_type + H3 severity="none" 实录；惯例=核实类条目 severity=low、claim_type 仅枚举值（无枚举置 null）、evidence 注明核实结论 | test_v327: 模板含惯例段文本 |

## 取证裁除（已存在机制/无消费者）

- QuickJS lessons 1（R4 通道发现力高于 R2）→ **裁除**：R4 时序与发现无关（R4 反正会跑，时序不影响发现力）；机制化无消费者增益（义务三问②无消费者）；根因由 D-1~D-3 知识补种系统性修复。注记：下一场库型/引擎目标验收时观察 R2 假设空间是否因新种格扩展（不建度量义务）。

## 四缺陷评估

- ①盲目带入：新条目全部机制形态（"计数分配器包装层/子执行上下文/序列化读取器"），项目名零入正文；source_lessons 标 "quickjs lessons 2026-09-07" 追溯 ✓
- ②设计偏见：无自动改写；全部提示级/数据级 ✓
- ③死代码：新清单条目消费者=binder cwe 绑定管线；矩阵条目消费者=R2 cells 读取 ✓
- ④过设计：零新门禁/零新阶段/零 binder 改动；R4 时序机制化已裁除 ✓
