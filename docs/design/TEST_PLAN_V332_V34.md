# v3.3.2 + v3.4 + v3.4.1 测试计划（P0/P1/P2）

> 目标：用真实开源项目验证三批修改（v3.3.2 义务裁剪+缺陷修复 / v3.4 范围守护 / v3.4.1 旧队列兼容热修复）。
> 原则：每个改动必须有对应项目特征把它真实走到；优先低成本方式（旧队列复跑 < 新项目全流程）。
> 日期：2026-08-20

## 0. 被测修改总清单（测试追踪依据）

### v3.3.2（24 REQ / 43 SWR）
| 类别 | 修改 | 承载 SWR |
|---|---|---|
| 正确性 | gate ③ verdict 条件 / demote 清 claim / empirical status 归一化+告警 | 001/002/003 |
| 正确性 | ③b 结构化+收窄（Medium+/forced-claim 强制，Low 接受 source_fact/机制级） | 004 |
| 正确性 | 复活改判检查（post_resurrect_refutation gate） | 005 |
| 正确性 | r4_feedback 结构化 default_value_table 输入 + 单字符键守卫 | 006 (+v3.4.1) |
| 正确性 | verifier 任务书 claim 与实证自洽条款 | 033 |
| 载体 | `--from-journal --expect` 全集校验 | 010 |
| 载体 | `--stage coverage`（tracked 计算+归一化+unknown 告警+读 _r2_filter） | 012 (+v3.4.1) |
| 载体 | `--stage grade-recheck`（旧 empirical schema 无 status 按 scope 推断） | 013 (+v3.4.1) |
| 载体 | `--stage r35-collect --from-journal`（refutation decisions 落候选） | 011 |
| 载体 | 步骤 0.5 按型门控（动态语言完整段/静态语言一行核对） | 014 |
| 载体 | r4-collect unknown surface id 告警 | 015 |
| 载体 | verify 模式 re_verify_gap 自动渲染 gap 段 | 020 |
| 载体 | resurrect 抽样决策落盘（_resurrect_sample.json） | 021 |
| 载体 | workflow script 返回 project + dispatched_ids | 022 |
| 载体 | PREC 自证伪提示精度门（applicability_signals） | 023 |
| 载体 | norm_surface_id 共享纯函数 | 040 |
| 裁剪 | H7 default_value_table 收缩 schema（≤10 项） | 030 |
| 裁剪 | R4 finding claim_type 字段 | 031 |
| 裁剪 | 义务入库三问段（任务书） | 032 |
| 文档 | SKILL.md：wave registry 簿记 / R3.5 触发条款 / 抽样口径 / grade-recheck 引用 / R6 幂等 / 三问 / R2 签名降佐证器 | 050-054 |
| 环境 | harness_manuals/ENVIRONMENT_PROBES.md | 060 |

### v3.4（8 REQ / 14 SWR）
| 修改 | 承载 SWR |
|---|---|
| `--stage coverage-ledger --write`（聚合/幂等/merge）与无参缺口打印 | 001-003 |
| stage_report 的 coverage_ledger 段 | 004 |
| resources/issue_coverage_matrix.json（9 族 × 16 语言，30 项目回填） | 010/011 |
| 4 条问题类清单（CK-CRYPTO-MISUSE/AUTHN-BYPASS/BIZ-LOGIC/DATA-INTEGRITY）+ 绑定 | 020/021 |
| SKILL.md 选题规则 / 报告尾注 / 第一原则验收强化 | 030-032 |

---

## 1. P0 — 三锚点复跑（旧队列 × 新工具链，零克隆）

**验证方向**：v3.4.1 兼容修复的批量验证 + v3.3.2 门禁在三种语言（Ruby/C/Rust）旧产物上的回归。Lua 已先行跑通并暴露 3 缺口——这三家预期还能找出差异。

| 项目 | 路径 | 语言 | 附加验证点 |
|---|---|---|---|
| sinatra | /root/sinatra | ruby | gate ③ verdict 条件（有裁决降级候选→demote 清 claim 路径） |
| lighttpd1.4 | /root/lighttpd1.4 | c | C 旧 schema、coverage _r2_filter 读取 |
| actix-web | /root/actix-web | rust | Rust 旧 schema、③b 对旧 R4 findings 的 fallback warn |

**每项目执行步骤**（Lua 模式复用）：
1. `--stage grade-recheck` → 记录 changed/warnings（旧 schema 推断是否工作）
2. `--stage coverage` → 若 missing ≠ 0：检查是否旧 schema 面，主代理写 coverage_bridge（basis 引用 R2/R4 既有记录）
3. `--stage r4-assert`
4. `assert_ledger`（dispatched 全集 + surface_data）→ 目标 PASS 无告警（告警需逐条可解释）
5. `--stage coverage-ledger --write` → 期望 LEDGER_IDEMPOTENT_SKIP（已在 sources）
6. `--stage report` → coverage_ledger 段渲染
7. 新发现的兼容缺口 → v3.4.2 热修复 + W6 §31 记录

**判据**：三锚点复跑零回退（REACHABLE 结论不变、六门禁 PASS）；每个旧队列告警清零或写 correction_record 解释。

## 2. P1 — 主验证批次（3 新项目：CRYPTO 补格 + Mode W 全链 + 混合语言）

**克隆**：`git clone` 到 /root/（PyJWT、node-jsonwebtoken、orjson）。

### 2.1 共同流程（每项目全 R0-R6）

| 阶段 | 挂测修改 | 检查点 |
|---|---|---|
| R0 | selfcheck / target_kind / scope 快照 | 新工具链无回归 |
| R1 | 4+1 域测绘 | orjson 必须产出 boundary 域 surfaces（PyO3 FFI，lang_pair 字段） |
| R2 | LLM 主路径 + **签名可选佐证器**（SWR-053） | R2 不强制跑 index/match（库型目标） |
| R3 | Mode W verify 波 | **wave registry 簿记**（SWR-050）+ collect `--expect`（SWR-010）真实使用；0.5 门控按语言形态（python/js 完整段）；CK-CRYPTO-MISUSE 绑定入任务书（CWE-327 类候选） |
| R3.5 | refutation 波（N=2） | 视角分化 prompt 无缓存复用；refutation 结果 |
| R3.5-N | resurrect 波 | **抽样落盘**（SWR-021：_resurrect_sample.json 存在）；声称类全量规则 |
| 复活重验 | 复活候选回 R3 | **gap 渲染**（SWR-020：prompt 含"复活复核 gap"段）——必须真实触发至少一次 |
| 重验后 | 复活改判 REACHABLE | **post_resurrect_refutation gate 触发**（SWR-005：断言违规 → 补 R3.5 → 放行）——必须真实走一遍 |
| R3.5 收集 | refutation 波后 | **r35-collect**（SWR-011：refutation 字段落候选） |
| R4 | biz 假说 H1-H7 | **H7 收缩 schema**（SWR-030：表 ≤10 项）；finding claim_type（SWR-031）；**③b 结构化**（SWR-004：Medium+ 无实证阻断、Low 放行）；**r4_feedback**（SWR-006）；r4-collect unknown id 告警（SWR-015） |
| R5 | 实证 | **ENVIRONMENT_PROBES 探针段**写入 EMPIRICAL_REPORT；claim 与实证自洽条款（SWR-033） |
| 门禁 | 六门禁 | **coverage CLI**（SWR-012）出 surface_data → assert_ledger 全 PASS（含 gate ③ verdict 条件、复活改判检查） |
| 闭合 | R6 + 账本 | `--stage coverage-ledger --write` 回填（SWR-001/002 幂等）+ 覆盖格 +1；report 含 coverage_ledger 段（SWR-004） |

### 2.2 项目分工

| 项目 | 语言 | 专项验证 | 补格 |
|---|---|---|---|
| **PyJWT**（CVE-2017-11424 算法混淆实锤） | python | CK-CRYPTO-MISUSE 绑定实证（算法/签名校验类候选）；动态语言 0.5 完整段；纯静态审计路径 | CRYPTO×python |
| **jsonwebtoken**（npm，CVE-2022-23529） | javascript | JS 生态面；同清单绑定第二例 | CRYPTO×javascript |
| **orjson**（PyO3） | rust+python | **混合语言全链**：boundary 域（FFI surfaces + lang_pair）、候选 lang 分派（rust sink vs python sink）、0.5 门控双形态同项目对照、Mode W 全链真实派发（wave registry/--expect/gap 渲染/r35-collect/复活改判 gate 全部在真实波次中使用） | CRYPTO×rust 深度 + INJECTION×rust |

### 2.3 P1 判据

1. Mode W 全链在 orjson 上真实走通：wave_registry.jsonl 有记录、--expect 对账过、gap 段渲染过、_resurrect_sample.json 存在、r35-collect 产出 refutation 字段、复活改判 gate 至少触发一次并被 R3.5 复核放行
2. PyJWT/jsonwebtoken 的 CWE-327/347 类候选任务书含 CK-CRYPTO-MISUSE 段
3. coverage-ledger 回填后 CRYPTO×python 与 CRYPTO×javascript 覆盖格 +1；重复 --write 幂等
4. 六门禁全 PASS；报告含覆盖账本尾注

**风险与回退**：
- 复活流依赖项目真实产生声称类 UNREACHABLE——若 P1 无此形态，从 actix-web/akka 旧队列找一个真实候选人工构造重验波（用真实数据 + gap 注入），保证 SWR-020/005 至少真实走过
- orjson 构建（maturin/cargo）：离线 cargo 可用；若 R5 实证需要构建失败 → 降级静态 + 记录 blocker（ENVIRONMENT_PROBES 场景本身即验证）
- jsonwebtoken 需 npm install（容器有网络，apt 已验证）；失败则纯静态审计（不跑 JS harness）

## 3. P2 — 第二批次（4 项目：AUTHN/DATA-INTEGRITY 补格 + PREC 回归）

**开题动作本身即验证选题规则**（SWR-030）：从 `--stage coverage-ledger` 缺口清单选题（P2 清单即按此生成）。

| 项目 | 语言 | 补格 | 专项验证 |
|---|---|---|---|
| cpp-httplib | cpp | AUTHN×cpp + MEMORY-SAFETY×cpp 深度 | CK-AUTHN-BYPASS 绑定；C++ 0.5 短段（SWR-014 静态侧）；header-only 静态审计 |
| devise | ruby | AUTHN×ruby + WEB×ruby 深度 | CK-AUTHN-BYPASS 第二例；ruby 低深度升级 |
| cosign | go | DATA-INTEGRITY×go | CK-DATA-INTEGRITY 靶心（签名/校验语义）；go 0.5 短段 |
| java-jwt | java | CRYPTO×java | **PREC 精度门回归**（SWR-023：Java 配置类候选不得注入 Host 族等无关先例——对照 hikaricp 旧 prompt 快照） |

**P2 判据**：4 覆盖格 +1；PREC 精度门回归（Java 候选自证伪提示零"不适用"命中）；同批双语言 0.5 形态对照（cpp/go 短段 vs 既有动态语言完整段）。

## 4. 批次间依赖与顺序

```
P0（三锚点复跑，~半天） → 若有新兼容缺口 → v3.4.2 热修复
P1（3 项目全流程，首个项目当模板）
P1 闭合 = coverage-ledger 回填 + "覆盖格+1" 验收判据
P2（4 项目，选题规则驱动的第一个正式批次）
```

## 5. 总验收判据（三批完成时）

1. **旧数据方向**：三锚点 + Lua 共 4 家旧队列复跑零回退
2. **新数据方向**：P1/P2 共 7 个新项目六门禁全 PASS
3. **机制真实走过**：wave registry / --expect / gap 渲染 / r35-collect / 复活改判 gate / coverage CLI / coverage-ledger / 0.5 门控 / PREC 精度门 / 4 条新清单——10 项修改全部在真实波次中至少使用一次（无单测-only 项）
4. **范围守护生效**：P1+P2 合计覆盖格 +7（CRYPTO×python/js/rust/java、AUTHN×cpp/ruby、DATA-INTEGRITY×go），缺口清单收缩可测
5. 测试过程发现的缺陷 → W6 §31+ 记录 + 热修复版本
