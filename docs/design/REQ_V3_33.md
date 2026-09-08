# REQ_V3_33: Servo 验收复盘缺陷修复需求

来源: Servo 验收审计 (v3.32, 2026-09-07~08) 六门禁 PASS 后的阶段 0 复盘 + 教训队列。
案例支撑全部指向 /root/servo/.audit_results/lessons.md (N-1..N-5 过程注记 + 机械提取段)。
DDL 核对: V8/WebKit/Firefox/MaintainWise/QuickJS 五份 lessons 已带消化注记入库
(v3.20~v3.31 各周期), 本周期唯一未消化集 = servo lessons。

## 缺陷清单

| # | 缺陷 | 分层 | 代码核实 (2026-09-08 取证) | 修复 |
|---|---|---|---|---|
| D-1 | merge 跨文件同 id 静默 first-wins, 无冲突标注 — 18 面静默丢失 (servo 实录: script 7 面 + urlimg 11 面被 netw 同 id 覆盖, 靠面总数手工对账才抓到) | P1 | surface_mapper.py:860-868 dedup 块静默 continue | merge 检测跨文件同 id 碰撞, 落 conflicts 列表 (resolution="kept-first-same-id", 附双方 surface 摘要); 保留去重行为不变 |
| D-2 | R1 域覆盖无机械守卫 — servo process/storage 两域零派发零记录, layout 组件零面 (fixminer 显示 layout 有真实崩溃修复史) | P1 | surface_mapper.py:608-620 empty_domain_reason 契约仅在 validate 空文件时生效; merge 无域计数 | merge 收口时按 DOMAINS 计数, 域无文件且无空域签收 → warn violations (提示级, 主代理裁决重派或签收) |
| D-3 | filter 产出的 focus_sink 路径无存在性自检 — HYP-043 路径段漂移 (html/contenteditable → execcommand/contenteditable) 直到主代理抽查才发现 | P1 | r2_guard.py fidelity 只补缺失 surface_ids, 不查 focus_sink 路径 | fidelity 增加 keep 条目 focus_sink 的路径存在性校验 (project_root 解析, 缺失 → error 拒收补查) |
| D-4 | filter 重写 surface_ids 无机械拦截 — B 批 15 处重写 (4 处编造不存在 id 如 SCR-012) 违反"原样继承"义务 | P1 | r2_guard.py fidelity restore 只处理缺失 | fidelity 增加一致性校验: keep/drop/bc 的 surface_ids 必须与 hypotheses.json 原样一致, 不一致 → error (含 verbatim 规则说明) |
| D-5 | reviewed_clean 假说下 severity≥Medium 的实质 findings 不进问题清单 — servo:config 点击劫持 (M) / TrustedPromise 滞留 (M) 被 verdict 语义吞掉 | P1 | batch_verify.py r4-collect 无该检查; 渲染器 SWR-V3.10.1-001 按设计跳过非 confirmed | r4-collect 对 reviewed_clean 假说的 Medium+ findings 输出 warn (主代理裁决归位: 升 confirmed 承载/主代理段/明确留档); SKILL.md R4 段补条款 |
| D-6 | 报告同事实去重不看承载候选终态 — H-1 四条 High/Medium finding 因 r3_link 候选降 NEEDS_REVIEW 而整体消失 (主代理手工 r3_link 置空修复) | P1 | batch_verify.py:2224-2232 dupes 无条件 continue | 去重条件加承载候选 verdict==REACHABLE; 否则 finding 自列且行尾注「候选已 NEEDS_REVIEW, 见附录 A」 |
| D-7 | lessons_refs 检索面仅 dev 仓 lessons/ 文件名+族头前 2000 字符 — rust 目标 lessons_refs=0 (D-4 杠杆证伪观察点) | P1 | language_issue_matrix.py:199-214 | hints 增加该语言种格 source_lessons 条目通道 (矩阵两段式回填的知识基座, 不读任何项目路径, 第一原则三禁止合规) |
| D-8 | fixminer 召回仅 subject 关键词净分 — 无安全关键词的修复 commit 漏采 (召回上限) | P1 | fixminer.py _security_score 仅 subject 计分 | 增加文件路径信号通道 (安全敏感路径模式低权重加分: 密码学/解析器/内存管理/安全目录), 净分>0 门槛与精度护栏不变 |
| D-9 | 生成码 (构建期生成物) 未列入发现包络边界声明 — WebIDL codegen 磁盘无源, 静态审计无通道 | P3 | SKILL.md 报告段包络声明 (a)-(e) 无生成码类 | 包络声明增 (f) 构建期生成物类: 审计生成器源码 + 生成物按依赖边界处理, 可构建则物化审计 |
| D-10 | 行号漂移裁决依据未固定 — suggested_line 语义是"距声称行最近命中", 多语句 snippet 错锚 (3/13 处需定义形态裁决) | P3 | surface_mapper.py:688-736 suggested 取 |suggested-claimed| 最近命中 | SKILL.md R1 段补裁决条款: 漂移裁决依据=snippet 首行实际锚点, suggested_line 仅作候选 |
| D-11 | empirical harness 版本漂移无条款 — 独立 harness 解析不走 workspace Cargo.lock (CSP Destination E0004), lib 名≠包名两次踩坑, --offline 被 git 依赖阻断 | P3 | SKILL.md R5 段无 harness 依赖条款 | R5 落盘规范补 harness 条款: 版本敏感依赖对照目标仓 Cargo.lock 钉死; lib 名与包名分开核对; 离线可行性含 git 依赖面 |

## 测试守卫约束 (阶段 4)

- 每条 P1 至少一用例含反面分支 (D-1: 同 id 碰撞产生 conflicts 条目 / 无碰撞零条目; D-2: 缺域无签收 warn / 有签收零 warn; D-3/D-4: 坏路径/重写拒收 / 合规零 error; D-5: reviewed_clean Medium+ warn / Low 零 warn; D-6: 承载 REACHABLE 去重 / 承载 NEEDS_REVIEW 自列; D-7: rust refs 非空 / 未知语言零注入; D-8: 路径信号命中 / 精度护栏不回退)
- 全量回归全绿; 旧队列复跑零新增告警 (servo/quickjs 队列 assert_ledger blocking=0)
- test_deproject_assets 零命中 (新条款文本去项目化)

## 开发序列

P1: D-1 → D-2 → D-3/D-4 → D-5 → D-6 → D-7 → D-8 → P3 条款 D-9/D-10/D-11 → P4 版本链五件

## 验证命令

```bash
python3 -m pytest tests/ -x -q           # 全量
python3 tests/test_v333.py               # 新用例
python3 tools/batch_verify.py /root/servo --stage coverage-ledger  # 账本不回退
```
