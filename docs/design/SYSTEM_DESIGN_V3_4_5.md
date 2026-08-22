# Reachable Critical Audit v3.4.5 — 系统设计

> 日期：2026-08-23
> 定位：gRPC 全流程审计（2026-08-22，56 surface / 87 假设 / 1 候选 UNREACHABLE，六门禁全 PASS）暴露缺陷的修复版。
> 教训回填：`lessons/SKILL_LESSONS_grpc.md`（安装副本，本设计连同 lessons 同步回开发仓库）。验收记录：`ACCEPTANCE_V3_4_5.md`（待验收后落盘）。
> v3.4.5 是缺陷修复版：**不新增阶段、不改六门禁①-⑧判据语义、不重排流水线**——把 gRPC 审计暴露的 3 项机制缺陷就地修复 + 2 项制度沉淀。

## 1. 问题域（全部来自真实验收/审计运行）

### P-A：机制缺陷（3 项——主代理在审计中人工补救的机械缺口）

| 证据（gRPC 审计） | 缺陷 | 后果 |
|---|---|---|
| 主代理先写 28 条 LLM 假设至 `hypotheses.json`，随后 `signature_matcher.py gen`（佐证器）将 59 条 SIG 假设写入**同一文件**，抹掉 LLM 主路径产物 | gen 输出路径硬编码 `hits.json` 同目录 `hypotheses.json`（signature_matcher.py:323-326），与 LLM 主路径共享文件名 | 合并需手工重建 28 条 LLM 假设（本次实际发生）；文件所有权无分离，任何"先 LLM 后佐证"顺序都会触发静默覆盖 |
| resurrect 首次派发以裸数组传 args，脚本返回 `args.candidates 缺失 (W6 §5)` 报错，主代理改包装后重跑（wave_registry 记录一次失败波） | `next_step` 已声明 `args={"candidates": <payload>}`（workflow_export.py:454-455），但脚本顶层对裸数组**不容忍**——形态误传直接失败而非自动纠正 | 一次无谓的失败波 + 派发侧依赖人工纪律；W6 §5 的 "args 防御" 只覆盖缺失，不覆盖形态 |
| boundary 域 agent 产出 id 001,002,004..013（缺 003），merge 后 12/13 条在册，校验器静默放行 | `merge_surfaces`（surface_mapper.py:762-816）有 seen_ids 去重，但无**域内 id 序列空洞检测** | 缺号不告警，主代理不复核遗漏；本次仅 1 条但缺号可能是 agent 整段漏报的信号 |

### P-B：制度沉淀（2 项——正面经验 + 纪律补强）

| 证据（gRPC 审计） | 项 | 处置位置 |
|---|---|---|
| R3 verifier 对 BoringSSL 钉住 commit 的实证方式（bazel/grpc_deps.bzl 解析 → 下载 pin 源码 → 核对 `ssl_max_handshake_message_len=16384`）；复活复核独立实证 BIO pair 17KiB——跨仓库依赖审计的完整模式 | 该模式无 checklist 载体：清单库 28 条无 vendored/钉住依赖条目，同类审计形态依赖 verifier 现场发挥 | `resources/checklist_library.json` 新增 CK-PINNED-DEP（按义务三问②有消费者：checklist_binder → verifier 任务书） |
| resurrect args 裸数组误传属派发侧纪律问题，机械兜底（P-A）之外需要纪律条款 | 编排层铁律现有三条（写读竞态/schema 契约/证据裁决），无 args 形态纪律 | SKILL.md 编排层铁律新增第四条 + README 同步 |

### 裁剪说明（明确不进 v3.4.5 代码）

- **protobuf/upb 覆盖盲区**（third_party 子模块未物化 / upb vendored 上游 drop）：属**范围决策**而非机制缺陷，已有 coverage_bridge 通道（basis 签收）处理；CK-PINNED-DEP 提供未来对 vendored 依赖的审计指引。
- **mature 库 R4/R3 双通道确认**（HPACK skip-before-allocate 等防御形态被两通道独立验证）：v3.3 并行机制已覆盖，无新需求。
- **无 REACHABLE 审计形态**（1 候选 → 复活全量 → revived=false → R5 无触发）：六门禁流程已覆盖，无新需求。

## 2. 设计方案（每域论证「为什么能解决」）

### 2.1 P-A1：文件所有权分离——佐证器不再写主路径文件

**修复策略**：`signature_matcher.py gen` 输出文件名从 `hypotheses.json` 改为 **`hypotheses_gen.json`**（与 hits.json 同目录）。同时 gen 启动前检查 `hypotheses.json` 是否已存在——存在则打印 warn（提示该文件属 LLM 主路径，主代理需合并而非覆盖）。

论证：
- 文件所有权分离是唯一能**根除**覆盖类问题的结构手段——改名后两种产物物理上不可互相覆盖，合并责任显式落在主代理（R2 流程本就有合并步骤）。
- 下游零影响：`hypothesis_filter.md` 经 `{hypotheses}` 占位符渲染（不读文件路径）；batch_verify 的 hypotheses 引用全为 R4 归一化逻辑，与 gen 无关。
- 同步面：`tests/test_signature_matcher.py:124` 断言输出名（须改）；README.md:149 与 SKILL.md 数据模型速查段注明双文件形态。

### 2.2 P-A2：脚本顶层 args 形态容忍——防呆而非纪律依赖

**修复策略**：workflow_export.py 四处 JS 模板（verify/refutation/resurrect/shipped-config）顶层防御改为：

```js
if (Array.isArray(args)) { args = { candidates: args }; }   // 裸数组自动包装
else { args = args || {}; }
```

论证：
- W6 §5 现有防御只防「缺失」（`!args || !args.candidates` 报错），本次事故是「形态误传」——裸数组同样通过 `!args` 检查为假，报错信息正确但浪费一波。
- 形态容忍是**零歧义**的机械兜底：三种模式 payload_key 均为 `candidates`（shipped-config 为 `components`，数组语义同为「任务列表」），自动包装不改变任何合法用法。
- 与铁律四（制度）形成双保险：机器不拒绝 → 人工纪律管习惯。

### 2.3 P-A3：merge 域内 id 序列空洞告警

**修复策略**：`merge_surfaces` 收尾阶段对**每个域前缀**（SURF-NETWORK-/SURF-DATA-/SURF-PROCESS-/SURF-STORAGE-/SURF-BOUNDARY-，按 canonical_surface_id 归一化后）检测编号序列空洞，输出 warn（**非阻断**）：

```
[merge] warn: surface id 序列空洞 SURF-BOUNDARY-003 missing (13 条在册)
```

论证：
- 空洞检测语义：编号是 agent 产出痕迹，缺号 = 可能的漏报信号（agent 整段跳过）；但删除/重编号也可能合法 → **warn 而非 fail**，主代理复核决定是否重派。
- 复用 canonical_surface_id 归一化结果，不新增解析路径；validate_surfaces 不重复实现（merge 是跨域聚合点，检测一次覆盖全）。
- 缺号与 SWR-V3.3.2-040 归一化同层处理，无新状态字段。

### 2.4 P-B4：CK-PINNED-DEP 检查清单（第 29 条）

**条目设计**（checklist_library.json，family=`vendored-deps`，binding 关键词：`pin|vendored|submodule|锁定版本|依赖版本|钉住`）：

步骤（去项目化提炼）：
1. 定位依赖声明点：构建文件/依赖清单（go.mod/Cargo.lock/package-lock/bazel deps）中的**钉住版本/commit**
2. 解析 pin → 获取**确切版本源码**（本地 vendored 或下载对应 commit），禁止用任意最新版核对
3. 核对声称机制涉及的**常量/上限/开关**在 pin 版本源码中的实际值（条件值注意分支语义，如仅某配置生效）
4. 记录 pin 值 + 源码出处，作为阻断点证据（不可用 README 声明替代源码事实）

论证：按义务三问——①触发条件：候选声称机制位于第三方钉住依赖（checklist_binder 关键词绑定，不自动全绑）；②消费者：R3 verifier 任务书（checklist 注入，现有机制）；③案例：grpc BoringSSL 正向案例（非失误，checklist 级沉淀合规——义务棘轮规则只约束强制义务）。grpc 条目以「BoringSSL pinned commit 核对 ssl_max_handshake_message_len」为来源列（追溯字段，符合去项目化第一原则）。

### 2.5 P-B5：编排层铁律四——args 派发形态纪律

SKILL.md 编排层铁律新增第四条：

> **4. args 形态纪律（v3.4.5）**：派发 Workflow 时 args 必须按导出 `next_step` 声明的形态（对象包裹，`args={"candidates": <payload>}`）传递；裸数组是派发错误——脚本已容忍自动包装（机械兜底），但纪律上禁止依赖兜底（W6 §5 + gRPC 复活波失败实录）。

论证：事故根因是派发侧纪律，机制兜底（2.2）防「跑不了」，纪律条款防「习惯性裸传」；条款含可追溯案例（gRPC 复活波）。

## 3. 验证策略

### 3.1 单测（tests/ 全绿门槛，预计新增 4 用例）

| SWR | 测试 | 落点 |
|---|---|---|
| 001 | gen 产出 `hypotheses_gen.json`（改现有断言）+ 前置 hypotheses.json 存在时 warn 输出 | test_signature_matcher.py |
| 002 | 导出 JS 含 `Array.isArray(args)` 包装行；构造裸数组调 JS 顶层逻辑不报 `args.candidates 缺失` | test_workflow_export.py |
| 003 | merge 构造缺号 fixture → 输出含 `SURF-BOUNDARY-003 missing` 且 exit 0 | test_surface_mapper.py |
| 004 | checklist_library 加载含 CK-PINNED-DEP（id/family/steps 结构校验，对齐 test_doc_lint 既有条目校验） | test_doc_lint.py 或现有资源校验 |

### 3.2 回归与发布（三条件同时满足才合并 main + install）

1. **单测全绿**：tests/ 14 文件全绿（含既有 73+ 用例，不得回退）
2. **三锚点回归零回退**：`signature_lib.py selfcheck` 对 fixture 三锚点（sinatra/lighttpd/actix-web）anchor recall 达基线；R0 完整冒烟通过
3. **新项目验收**：选覆盖账本缺口格项目跑全流程（优先语言×CWE 未覆盖格，判据含「覆盖格 +1」）——候选项目从 `resources/issue_coverage_matrix.json` 缺口格选取，验收记录落 `ACCEPTANCE_V3_4_5.md`

## 4. 版本影响

| 文件 | 改动 |
|---|---|
| signature_matcher.py | gen 输出名 → hypotheses_gen.json + 存在性 warn |
| workflow_export.py | 四处 JS 模板顶层 args 形态容忍 |
| surface_mapper.py | merge_surfaces 尾部 id 空洞检测（warn） |
| resources/checklist_library.json | +CK-PINNED-DEP |
| SKILL.md | 编排铁律四 + 数据模型速查双文件形态说明 |
| README.md | R2 段双文件说明 |
| tests/test_signature_matcher.py | gen 断言更新 + warn 用例 |
| tests/test_workflow_export.py | 形态容忍断言 |
| tests/test_surface_mapper.py | 空洞 fixture 用例 |
| lessons/SKILL_LESSONS_grpc.md | 从安装副本同步入开发仓库（需求溯源） |
