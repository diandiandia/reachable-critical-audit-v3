# REQ_V3_37: Caddy 验收复盘三缺陷修复

## 缺陷清单 (代码核实)

| # | 缺陷 | 案例支撑 | 修复 | 编辑点 |
|---|---|---|---|---|
| D-1 | workflow_export 落盘 payload 的 taskFile/taskFiles 为相对路径 (`.audit_results/_tasks/...`)——Workflow agent 的 cwd 非项目根, Read 该路径失败; 主代理未人工补绝对路径时, verify 侧按 taskFile 读取失败产伪 NEEDS_REVIEW, refutation 侧产 refuted:false | Caddy 验收实录: 证伪波/复活波派发前主代理手工把 args 里 taskFiles 补成绝对路径 (verify 波因 verify payload 落盘恰为绝对路径而幸免; refutation 三处全相对)。若未发现 → 任务书读取失败全线伪裁决 | 三处落盘字段改绝对路径 (project_root join) | src/workflow_export.py:599 (resurrect), :811 (verify), :854 (refutation) |
| D-2 | 检查清单缺"切片越界声称容量语义"条目——静态声称 `buf[:N]` 无守卫即 panic 时必须先核对输入缓冲的**容量** (2-index 切片边界 = cap 非 len; ReadAll/ReadFile 类输入 cap≥初始缓冲恒不越界) | CAND-011 verifier 误判 (fileloader.go:100 keyData[:40] panic 声称, real-target 20B key 实测无 panic; H2 独立复证 10B 双路径+59B 对照)——语言语义前提错误致整候选误报, R5 实证才拦截 | 新清单条目 CK-SLICE-CAPACITY (family=memory-safety) | assets/resources/checklist_library.json |
| D-3 | 检查清单缺"量级驱动权"条目——资源类声称 (oom/unbounded) 的量级必须由攻击者输入维度驱动: 单请求上界=部署内容尺寸、聚合上界=平台连接上限的形态不得报 remote oom | CAND-002 证伪 1/2 (量级前提幻觉) → 主代理裁决降级 NEEDS_REVIEW; H1-F1/F2 同族按加固缺口口径申报 | 新清单条目 CK-MAGNITUDE-OWNERSHIP (family=empirical) | assets/resources/checklist_library.json |
| D-4 | caddy lessons.md 缺"对 skill 的教训"蒸馏节 (主代理 R6 收官遗漏) | 价值判定节注明该节为 skill-optimizer 唯一读入口, 本审计教训 3 条未蒸馏 | 补写蒸馏节 (去项目化) | /root/caddy/.audit_results/lessons.md |

## 测试守卫 (tests/test_v337.py)

- T-1: workflow_export 三形态 payload (verify/refutation/resurrect) 的 taskFile/taskFiles 均为绝对路径 (以 project_root 前缀断言);
- T-2: CK-SLICE-CAPACITY 条目存在 + family=memory-safety + steps 含容量语义判据 + 去项目化扫描零项目名;
- T-3: CK-MAGNITUDE-OWNERSHIP 条目存在 + family=empirical + 去项目化;
- T-4: 资产计数守卫同步 (45→47) + 全量回归绿 + 旧队列复跑零新增告警。

## 开发序列

P1 (D-1 绝对路径) → P3 (D-2/D-3 清单条目) → P4 版本链五件 → 安装。
阶段 6 验收: 无新项目——按 v3.25 先例由用户裁定暂缓。
