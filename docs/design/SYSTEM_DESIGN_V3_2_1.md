# Reachable Critical Audit v3.2.1 — 系统设计

> 日期：2026-08-17
> 定位：v3.2 验收（Phase 3.2.3）暴露缺陷的修复版。验收记录：`ACCEPTANCE_V3_2.md`；教训回填：lessons/W6 §25。
> v3.2.1 是补丁版：**不新增阶段、不改六门禁语义、不重排流水线**——只把验收暴露的四个缺陷就地制度化。

## 1. 问题域（全部来自 v3.2 验收真实失败）

### P-A：R0 缺 target_kind 判定 → verifier 用错"存在性规则"

两次验收同根因（fixture key_finding + Lersosa 三处前提错误）：

| 证据 | 后果 |
|---|---|
| fixture：同一形状的两个库型候选，一个判 REACHABLE 一个判 UNREACHABLE，2/2 证伪 + 4/4 复活全部指向"未定目标类型" | 同批裁决矛盾，需主代理按 Newtonsoft.Json 先例事后纠偏 |
| Lersosa CAND-001/008：verifier 用"代码零值"推定明文可达，实际 shipped config 显式 `tls_enable: true` | 部署前提错误 → 攻击面形态误述（PoC 参数错一个量级） |
| Lersosa CAND-004/009：verifier 用"路由自动注册"推定存在，实际模块导入断裂 → 404 | 9 跳全真的静态链被判 REACHABLE，两条候选事后降级 |

根因：**v3 的 verifier 任务书只写了一种"存在性规则"（应用型：要求部署前提 + 运行时注册），没有按审计目标类型装载规则**。库型目标（公共 API 即信任边界）与应用型目标（默认部署即攻击面）的存在性判据相反，混用必然产生系统性误判。

### P-B：verifier 两盲区（均造成 REACHABLE 过度声称，事后降级）

- **P-B1「模块存在≠被导入」**：CAND-004/009 的 verifier 逐行核实了 9 跳调用链（全部为真），但从未检查链首模块能否被导入——顶层 `common`/`infrastructure` 包不存在 + DI 扫描器 `except Exception: logger.warning` 吞错 → 爬虫组件零注册。静态链真实 ≠ 运行时存在。
- **P-B2「缓存/门闩层漏枚举」**：CAND-007 的 verifier 沿调用链直查 adapter→domain→repo，整层漏掉 GetDefaultOssConfig 的 Redis 前置门闩——且该门闩错误分支写反（`if err==nil` 块内处理错误分支=死代码）+ SetDefault/GetDefault JSON 形状不匹配 → 消费端在默认态永不可达。

### P-C：判据①未区分客户端组件语言

REQ-V3.2-100 判据①"每语言 ≥1 surface 且非零候选"对纯浏览器前端（Lersosa TS，32 文件）在字面上不可满足——客户端组件没有服务端可达攻击面，其覆盖面经边界面裁决 + cross_evidence 达成。判据措辞缺陷导致验收靠 qualification 补丁，属文档级缺陷。

### P-D：R4 H-7 默认值盘点与 R3 gate 证据无反馈通道

Lersosa 中 H-7 f1（tls fail-open 明文，R4 层）在 CAND-001 原判定出错处是对的——**R4 捕获了 R3 verifier 漏掉的部署层真实形态**，但反馈发生在 R3.5 证伪波（事后、昂贵）。若 H-7 的"shipped config 实际值"在 R3 前可用，CAND-001/008 的前提错误可被前置拦截。

## 2. 设计方案（每域论证"为什么能解决"）

### 2.1 P-A：R0 target_kind 判定 + 按型装载存在性规则

**判定（R0，机械信号 + 主代理签收）**：

```
target_kind ∈ {application, library, hybrid}
机械信号（tools/target_kind.py）：
  library 信号：包清单声明为库（setup.py/POM<artifactId>/Cargo.toml 无 [[bin]]/package.json "main"+无 server 入口）、
                无监听器/服务启动链（0.0.0.0 bind/Listen/Serve/uvicorn.run 缺失）、README 自称 SDK/库、
                发布物含 API 文档而非部署文档
  application 信号：存在服务启动链（main+wire/bootstrap+kratos/axum Server）、监听配置、Dockerfile 服务端、
                    部署文档（compose/k8s）
  hybrid：多组件项目按组件分别判定（component_hint → per-component target_kind）
```

**按型装载存在性规则（verifier 任务书 + R2 guard 提示）**：

| 维度 | application 规则 | library 规则 |
|---|---|---|
| 信任边界 | 部署面（监听点/默认配置即攻击面） | 公共 API 即边界（Newtonsoft.Json 先例） |
| "默认可达"三层检查 | 代码零值 / 模块加载 / **shipped 配置实际值 + 部署前提**（三层全开才可达） | 仅前两层；部署前提不适用 |
| 仓内调用者缺失 | 可能是阻断（死代码 → UNREACHABLE） | **不是**阻断（库的调用者在仓外；死代码豁免规则不适用） |
| 运行时注册 | 必须核实（DI 扫描/路由注册真实发生） | 不要求（API 静态存在即面） |
| platform_precondition | 必须显式标注（Windows 证书路径类） | 标注为记录型 |

**为什么能解决**：fixture 同批矛盾的两个候选按 library 规则（公共 API 即边界）同判 REACHABLE；Lersosa 三处前提错误全部落在 application 规则的"shipped 配置实际值 + 运行时注册"强制项上——verifier 不再能跳过部署前提直接判"默认可达"。

### 2.2 P-B1：verifier 任务书新增"模块可导入性"预检（必做步骤）

对每条链的首跳模块：
1. **顶层包解析**：链首模块所属顶层包在部署布局下能否解析（find_spec/`go list`/crate 是否被依赖树包含/`require` 是否被 main 传递包含）；
2. **DI/组件扫描器吞错路径审查**：注册器若含 `except Exception: log/continue` 模式，必须验证目标模块实际被扫描成功（扫描日志/注册表/路由表），不能以"框架设计如此"推定；
3. 链上任何模块 import 失败 → 该边记为 **broken_edge**，候选按"修复即可达"处理（NEEDS_REVIEW 条件候选，不是 REACHABLE）。

**为什么能解决**：CAND-004/009 的根因是 verifier 从未执行第 1/2 步。404 实证在 R3 就能出现，两条候选在 R3 即落 NEEDS_REVIEW，R3.5 无需事后降级。

### 2.3 P-B2：verifier 任务书新增"消费端中间层枚举"（必做步骤）

对"写路径→消费路径"复合链（write→read 注入族）：
1. 消费端每层**横向枚举**：adapter 与 domain 之间的缓存/门闩/降级/拦截器层必须逐层列出（不只是直查调用链）；
2. **缓存层三查**（CK-CACHE-GATE-LAYER）：
   - 错误分支方向（`if err==nil` 块内处理错误分支=死代码）；
   - 写入方/读取方形状一致性（writer 单对象 vs reader 切片）；
   - 缓存键写入路径存在性（Save/Modify 是否失效/回填缓存键——不回填则 DB 行进不了读路径）。
3. 状态依赖面（缓存命中的条件态 vs 默认态）必须写入 evidence 的 blocking_point 候选。

**为什么能解决**：CAND-007 的 verifier 若执行第 1/2 步，Redis 门闩 + 三查直接给出"默认态消费端不可达"，static_only 的过度声称在 R3 即被纠正，不依赖 2/2 证伪波事后发现。

### 2.4 P-C：判据①措辞修正 + 语言覆盖表加组件角色列

- 判据①改为：**"语言覆盖表每服务端组件语言 ≥1 surface 且非零候选；客户端组件语言以 ≥1 边界面 + cross_evidence 落盘为等价判据"**。
- 报告语言覆盖表新增 `组件角色` 列（server-side / client-only / build-config），由 R0 语言清单的 component_hint 派生。

**为什么能解决**：TS 前端的覆盖面（BFF 边界面 + cross_evidence + Go 侧归因）直接满足判据，不再需要 qualification 补丁；客户端组件的审计边界（边界面裁决）被显式定义。

### 2.5 P-D：R4 H-7 前置化 + 机械反哺通道

- **前置化（R1.5 轻量子任务）**：R1.5 框架感知扩展阶段追加"shipped config 实际值盘点"子任务——对含 config 文件的组件，提取监听地址/tls_enable/认证开关的**实际提交值**，写入 `shipped_config.json`；R2 guard 对任何带"默认可达/默认开启"gate 的假设强制引用该文件（三层检查的第三层直接有据可查）。
- **后置反哺（机械）**：evidence_ledger 新增 `r4_feedback` 断言（warn 级）：R4 H-7 findings 与 R3 REACHABLE 候选 gate 证据冲突时告警——主代理裁决或纠正 gate 证据，确保报告一致性。

**为什么能解决**：CAND-001/008 的"tls_enable 零值 vs shipped 显式 true"矛盾在 R2 就被 shipped_config.json 拦截（第三层检查有据）；任何漏网冲突在门禁断言时被机械兜底。

## 3. 组件影响清单

| 组件 | 改动 |
|---|---|
| `tools/target_kind.py`（新） | R0 target_kind 机械判定（信号提取 + 推荐值 + 证据），输出 `.audit_results/target_kind.json` |
| `SKILL.md` R0 | target_kind 判定步骤 + 签收条款（主代理确认写入 verify_queue.target_kind） |
| `workflow_export.py` | verifier 任务书按 target_kind 装载存在性规则段；新增模块可导入性预检段 + 消费端中间层枚举段；R1.5 任务书追加 shipped-config 盘点子任务 |
| `checklist_library.json` | 新增 CK-IMPORT-REGISTRATION、CK-CACHE-GATE-LAYER（绑定 import/DI/缓存/门闩类候选） |
| `precedent_library.json` | 新增 PREC-TARGET-KIND-001（库型/应用型存在性规则矩阵）、PREC-IMPORT-BREAK-001（模块导入断裂=条件候选先例） |
| `evidence_ledger.py` | `r4_feedback` 断言（H-7 与 R3 gate 证据冲突告警） |
| `r2_guard.py` | gate 提示追加"shipped 配置实际值必查"（shipped_config.json 存在时强制引用） |
| `surface_mapper.py` | 语言清单 component_hint 增加组件角色字段（server-side/client-only/build-config） |
| 报告模板 / REQ 文档 | 语言覆盖表组件角色列；REQ-V3.2-100 判据①措辞修正 |

## 4. 验收方案（Phase 3.2.1.3）

1. **target_kind 判定准确**：fixture（库型 hybrid：C 核心+Python/Rust 绑定）判 library/hybrid、Lersosa 判 application——与两次验收的人工结论一致；
2. **复跑零回退**：Lersosa 313 复跑结论与 v3.2 验收一致（5 REACHABLE / 2 条件 / 4 UNREACHABLE），且 R3 阶段即捕获 CAND-004/009 broken_edge 与 CAND-007 门闩（不依赖 R3.5 事后降级）；
3. **六门禁 PASS + 新增断言生效**（r4_feedback 无冲突）+ install。
