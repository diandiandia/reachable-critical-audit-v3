
## V3.23（2026-09-06，手工段——禁止运行 gen_tracking 再生成）

### 缺陷清单（REQ_V3_23）

| # | 缺陷 | 案例支撑 |
|---|---|---|
| D-1 | fidelity=equivalent 缺所有权模型核实 | firefox lessons §三.1（H3-F1 反证） |
| D-2 | 发现包络边界未声明 | v8 lessons 召回复盘 1（85046） |
| D-3 | JIT 正确性假设族缺失 + 严重度表无 843 | 同上 |
| D-4 | differential 探针未发现化 | 同上 |
| D-5 | 召回率回归集缺失 | 同上 + 战略欠账 |
| D-6 | R4 任务书不注入 R2 进行中结论 | WebKit lessons 二.1 |

### SWR

- SWR-V3.23-001（D-1）fidelity 所有权模型核实条款
- SWR-V3.23-002（D-2）发现包络边界声明条款
- SWR-V3.23-003（D-3）JIT 正确性假设族 + CWE-843 入表 + profile jit 信号
- SWR-V3.23-004（D-4）differential 通道发现化（提示级）
- SWR-V3.23-005（D-5）召回率回归集（fixture，无运行时机制）
- SWR-V3.23-006（D-6）R4 任务书注入 R2 进行中结论

### 取证裁除（已存在机制）

- v8 追记 1（claim=other 豁免）→ SWR-V3.19-003 已入库，裁除
- v8 追记 3/dcheck 波 1（dcheck-off 变体）→ SWR-V3.19-005 已入库，裁除
- v8 追记 4（构建配置矩阵）→ SWR-V3.19-006 已入库，裁除
