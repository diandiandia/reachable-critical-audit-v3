# SYSTEM_DESIGN_V3_10 — kernel 级项目首例审计复盘缺陷修复

> 版本链：v3.9（2026-08-28，Pillow 复盘）→ **v3.10（2026-08-28，kernel 级项目首例复盘）**。
> 缺陷修复版：不改变阶段骨架 R0-R6、不改变六门禁①-⑧判据语义、不改变队列数据模型主体。
> 背景审计：2026-08-28 首次 kernel 级项目全流程审计（五波、109 假设、10 候选、六门禁全 PASS）。
> 复盘发现 13 项问题 → 本版修复 12 项、撤销 2 项（含 1 项复盘误报）。

## 0. 第一原则自检（v3.3.2 义务入库三问 + 去项目化）

本版所有新义务逐条过三问（触发条件 / 消费者 / 案例支撑），无案例支撑的防御性义务不建。
所有新资产按机制形态书写，背景项目名只出现在追溯字段（source_lessons / 案例段），
不得进入运行时资产（签名 grep 列表、任务书正文、harness 模板、先例/清单）。
验收含"未审过的新项目"场景与 `_scan_runtime_assets` 去项目化扫描。

## 1. 问题域（P-A ~ P-H，13 项复盘发现）

| 编号 | 问题 | 复盘案例（追溯） | 形态 |
|---|---|---|---|
| P-A | 覆盖率簿记在**多波批次形态**下提取源不全：①`_tracked_ids` 只读主 filter 文件，波次分文件（`r2_filter_result_{wave}.json`）不合并；②`logic_hypotheses` 的 surface_ids 不计入（SKILL.md 门禁⑦语义明说"R2 假设 surface_ids"，假设含 logic 组，实现与语义漂移）；③**reviewed_clean 假说的审查触及面无结构化载体**（无 findings → 无 tracked_surfaces，审查记录只存在于 verdict_evidence 文本） | 六门禁覆盖率从 27/152 假失败起步；主代理手工合并 4 个 filter 文件 + 补 5 条 logic 记录 + 手工构造 tracked 才到 152/152 | 批次编排形态缺口 |
| P-B | empirical 回填 dict 无键名 schema：回填规范（SWR-V3.4.3-061）只要求 backfilled_by + 实测数字，未规定 dict 键；报告渲染器读 outcome/evidence_numbers 键 | 两条 ASAN 实证的实测数据（确定性输入、ASAN 报告）在报告里全部渲染为 None | 契约缺口 |
| P-C | 边证据"禁止合并多跳"条款无机械检查点：workflow schema 校验不知道 call_chain 长度，违反只能靠 collect 降级 static_only 事后暴露，且降级无 reason | 最高价值候选 12 跳链交 10 条边被静默降级；主代理回源码拆边手工重算才恢复 | 检测滞后 |
| P-D | shipped-config workflow 返回形态疑似与文档漂移 | 复盘核实：**误报**——脚本本就返回 `{mode, inventories, missing}` 包装，主代理收集时误读 per-agent journal 行 | ~~缺陷~~ → 撤销 |
| P-E | R4 任务书 empirical_result 指引与 gate 豁免逻辑冲突：任务书说"纯静态分析结论填 null"，但 gate 的 Low+声称类豁免要求文本含"静态/机制级"关键词——agent 按任务书填 null 反而触发违规 | Low+leak finding 违规，主代理改写为机制级描述才豁免 | 任务书与门禁不一致 |
| P-F | 任务书资产的语言生态偏见：①部署布局义务是 npm 系措辞（npm files/Makefile/bundle 三查）——非 JS 生态目标需主代理手工映射"编译面"语义；②shipped-config 键映射是服务端框架措辞（tls/auth/token 清单）——编译开关类配置（config/features 键的提交值 vs 代码默认值）无原生形态；③filter 的 focus_sink 无格式契约（带说明后缀致簇化解析失败）；④verifier 任务书无路径格式统一条款（绝对/相对路径混入报告） | 编译面查询（defconfig =y/=m）全靠主代理手工注入任务书 addendum；LDM 出圈与 BPF 非特权面两条关键裁决依赖这份手工映射；簇化入队解析失败一次 | 偏见（语言生态） |
| P-G | 提示资产缺口：①verifier 任务书无"搜索 upstream 修复/已知报告"步骤——上游补丁存在性是候选可信度最强旁证；②parser_fuzz 模板对有状态 sink（内核结构体/解析上下文）无 stub 注入指引 | 两条实证候选的上游修复都是证伪者顺带发现；两次 ASAN 实证的 stub 均为主代理手工构造 | 提示资产缺口 |
| P-H | 低价值项：①batch-size 默认截断（advice 字段已显式提示，主代理两次均依提示重导出，无失误）；②payload_hash 手工计算（三次零错误，消费者仅主代理） | — | → 撤销×2 |

## 2. 修复策略（12 项 REQ，详见 REQ_V3_10.md）

1. **覆盖率簿记三源合一**（P-A）：`_tracked_ids` 提取源扩展为——①全部波次 filter 文件（`r2_filter_result*.json` glob 合并 keep/drop/bc 三组）②`logic_hypotheses.surface_ids`（hypotheses.json logic 组）③R4 **假说级** tracked_surfaces（新字段，见 2）
2. **R4 假说级 tracked_surfaces**（P-A③）：任务书新增假说级可选字段，触发条件=verdict 非 confirmed 或 findings 空（有 finding 级载体时不重复）；r4-collect 幂等合并，不覆盖 finding 级
3. **r2_guard fidelity 波次回退**（P-A 收尾）：主 hypotheses.json 缺失时 glob `_r2_hypotheses_*.json` 合并反查
4. **empirical 键名规范化**（P-B）：canonical 键集（outcome/evidence_numbers/report 既有键保留；harness/method/input/result/verdict/backfilled_by 标准键入规范）；渲染器容错读双形态
5. **边缺口显式信号**（P-C）：collect 时 grade 重算 static_only 且自报 edge_proven → 输出 `edge_gap` 显式 reason（边数 N vs 跳数-1，疑似合并边，补拆后重 collect）
6. **R4 empirical_result 指引与 gate 豁免一致**（P-E）
7. **部署布局义务生态中立化**（P-F①）：按构建系统/语言分派的发布面三查 + 编译开关面查询（Kconfig 提交值 / Cargo features / CMake 选项 / Gradle buildTypes 等作分派例）
8. **shipped-config 编译开关键通用形态**（P-F②）：config/features/开关类键的"提交值 vs 代码默认值"语义为通用形态，服务端框架键清单降为分派例
9. **focus_sink 纯格式契约**（P-F③）：`path:line` 纯格式，说明入 note
10. **verifier/refuter 任务书补两步**（P-F④ + P-G①）：路径格式统一条款 + upstream 修复搜索步骤
11. **parser_fuzz 有状态 stub 指引**（P-G②）：模板 docstring + C 手册小节
12. **版本链与文档漂移**：TOOLING_VERSION → 3.10、SKILL.md v3.10 增量段、测试 test_v310

## 3. 义务入库三问（新义务逐条）

| 新义务 | ①触发条件 | ②消费者 | ③案例支撑 |
|---|---|---|---|
| 波次 filter 文件 glob | 存在 `r2_filter_result_*.json` 时（无分波文件零行为变化） | gate⑦ / tracked-ids CLI | kernel 27/152 假失败 |
| logic 组计入 tracked | 恒（实现与 SKILL.md 语义对齐） | gate⑦ | 同案（21+13 条防御裁决面簿记险些作废） |
| 假说级 tracked_surfaces | verdict≠confirmed 或 findings 空（有载体不重复） | r4-collect / gate⑦ | H4/H5/H6 审 ~30 面零簿记 |
| empirical 键集 | 回填时按规范填写；渲染器恒容错 | report 渲染 | 报告丢实证数据 |
| edge_gap 信号 | 降级发生且自报更高级时 | 主代理 collect 输出 | 最高价值候选被静默降级 |
| upstream 搜索步骤 | verifier 全部候选（无新数据模型字段） | verifier 证据 | 两条实证候选补丁均顺带发现 |

## 4. 撤销记录（义务棘轮防护）

- **P-D 撤销**：复盘误报——shipped-config workflow 脚本（`workflow_export.py` SHIPPED_CONFIG_SCRIPT）本就返回 `{mode, inventories, missing}` 包装；误报根源是主代理收集时读了 per-agent journal 行而非 workflow 级返回。不改代码，将该形态差异补入 collect 指引文档。
- **P-H① batch-size 截断**：advice 字段已显式提示（"若需全集请 --batch-size N"），两次均依提示重导出成功，无失误案例支撑新义务。
- **P-H② payload_hash 辅助**：三次手工 sha256 零错误；消费者仅主代理本人；无失误案例。

## 5. 验收判据（Phase 3.10）

1. 全量回归测试全绿（243 基线 + 新增 test_v310 用例）
2. kernel 受影响阶段复跑零回退：`--stage tracked-ids` 152/152（无手工补丁）、collect 输出 edge_gap 信号、报告渲染实证数据完整（outcome/evidence_numbers 非 None 或标准键透传）
3. `_scan_runtime_assets` 去项目化扫描绿（新资产无项目专属名）
4. 三锚点（sinatra/lighttpd/actix-web fixture）复跑零回退（不新增完整项目验收——受影响阶段均为机械层，与 v3.5.2 先例一致；新项目全流程验收随下一在线项目进行）
