# Reachable Critical Audit v3.2.1 — 软件设计文档

> 从 `SYSTEM_DESIGN_V3_2_1.md` / `REQ_V3_2_1.md` 导出的实现级设计。
> 原则：补丁版——不新增阶段、不改门禁语义、不重排流水线。日期：2026-08-17

## M1: target_kind 判定器（tools/target_kind.py，新）

```
determine_target_kind(project_root) -> {
  recommendation: "application"|"library"|"hybrid",
  signals: [{signal, evidence, direction}],   # direction: lib/app/neutral
  component_kinds: {component_hint: kind},     # hybrid 时按组件
  confidence: "high"|"medium"
}
```

- 信号源（只读，无第三方依赖）：
  - 包清单：setup.py 无 console_scripts / Cargo.toml 无 `[[bin]]` / package.json `"main"` 无 `"scripts"."start"` → lib；反之 → app
  - 监听器：grep `0.0.0.0`/`Listen(`/`Server::builder`/`uvicorn.run`/`app.listen` → app
  - 服务启动链：main + wire/bootstrap/kratos → app
  - Dockerfile：EXPOSE + ENTRYPOINT 服务端 → app
  - README：自称 SDK/库/组件 → lib；部署文档（compose/k8s/nginx）→ app
  - 发布物：docs/api vs docs/deploy 比例
- CLI：`target_kind.py <root> [--write]` → 落盘 `.audit_results/target_kind.json`
- hybrid：多组件且 component_hint 分组信号相斥时（如 C 核心库 + 服务端壳），按组件给出
- 主代理签收：确认/覆写后写入 `verify_queue.target_kind`（REQ-V3.2.1-002）

## M2: verifier 任务书扩展（tools/batch_verify.py::_build_prompt）

插入三段（在"强制分析步骤"内）：

1. **步骤 0.5 模块可导入性预检**（target_kind=application 时强制，library 时记录型）：
   - 链首模块所属顶层包在部署布局下能否解析（find_spec / go.mod 依赖 / crate 在 Cargo.toml / import 语法）
   - DI/组件扫描器吞错路径审查：注册器含 `except Exception: log/continue` 模式时，必须验证目标模块实际注册成功（注册表/路由表/扫描日志），不得以"框架设计如此"推定
   - import 失败 → 边记 broken_edge，verdict=NEEDS_REVIEW（修复即可达条件候选）
2. **步骤 5.5 消费端中间层枚举**（write→read 注入族候选强制）：adapter↔domain 间缓存/门闩/降级/拦截器逐层列出；缓存层三查：错误分支方向（`if err==nil` 内处理错误=死代码）/写读形状一致/缓存键写路径存在性；状态依赖写入 evidence
3. **target_kind 存在性规则段**（REQ-V3.2.1-003）：application 版（三层默认检查含 shipped 配置实际值+运行时注册+platform_precondition 显式标注）vs library 版（公共 API 即边界、仓内调用者缺失非阻断、死代码豁免不适用）——由 verify_queue.target_kind 选择装载

实现：`_build_prompt(cand, ctx, project_root)` 读 `verify_queue.json` 顶层 target_kind（缺省回退 .audit_results/target_kind.json；两者均缺 → 不注入，兼容旧队列）。workflow_export 经 `bv._build_prompt` 自动获得（Mode A'/W 共用）。

## M3: shipped-config 盘点 workflow（workflow_export.py 扩展）

- `SHIPPED_CONFIG_SCHEMA` + `export_script_shipped_config(project_root)`：
  - 输入：语言清单中含 config 目录的组件（configs/、*.toml/.*env 命中）
  - 每组件 1 agent，任务书：提取监听地址/tls_enable/认证开关/端口绑定的**提交值**与**代码零值**对照
  - 产出 `.audit_results/shipped_config.json`：{component, items:[{file, key, committed_value, code_default, mismatched}]}
- r2_guard（M6）与 verifier 三层检查（M2-3）引用该文件

## M4: 检查清单库 + 先例库增补（checklist_library.json / precedent_library.json）

- `CK-IMPORT-REGISTRATION`：顶层包解析/构建包含/DI 扫描器吞错路径/扫描日志核对 4 步
- `CK-CACHE-GATE-LAYER`：中间层横向枚举/错误分支方向/写读形状/缓存键写路径 4 步
- `PREC-TARGET-KIND-001`：存在性规则矩阵（application vs library），Newtonsoft.Json 先例
- `PREC-IMPORT-BREAK-001`：模块导入断裂 → broken_edge → 条件候选（Lersosa CAND-004/009 先例）
- 绑定机制复用现有 `checklist_binder.bind`（关键词 + CWE 匹配），新增测试用例固化（REQ-V3.2.1-011/013）

## M5: evidence_ledger 扩展（evidence_ledger.py）

- **门禁⑧ target_kind_required**：`verify_queue.target_kind` 缺失 → violation（R3 前门禁；旧队列兼容开关 `--legacy-no-target-kind` 仅复跑时用）
- **r4_feedback 断言**（warn 级，REQ-V3.2.1-032）：遍历 r4_findings H-7 findings，提取其 key:value 断言（如 "tls_enable 仓库配置=true"），与 R3 REACHABLE 候选 gate 证据做关键词冲突检测（同 key 相反值）→ `r4_feedback_conflicts[]` 输出，主代理裁决（写 gate 证据纠正或说明）

## M6: r2_guard gate 提示扩展（r2_guard.py）

- `validate_hypotheses`：gate 字段含"默认开启/默认可达"语义时，若 `.audit_results/shipped_config.json` 存在 → 提示强制追加"第三层检查引用 shipped_config.json 实际值"条款（REQ-V3.2.1-031）

## M7: 组件角色派生（surface_mapper.py::language_inventory）

- component_hint → `component_role`：frontend → client-only；scripts/headers → build-config；其余 → server-side（含 bindings，因绑定层通常服务端进程内）
- 输出项增加 `component_role` 字段（向后兼容：旧消费方忽略新字段）

## M8: SKILL.md 与报告模板

- R0：target_kind 判定 + 签收条款（REQ-V3.2.1-001/002）
- R1.5：shipped-config 盘点子任务（REQ-V3.2.1-030）
- R3：verifier 任务书三段扩展说明（M2）
- 门禁清单：⑧ target_kind_required
- 报告：语言覆盖表组件角色列（REQ-V3.2.1-021）；REQ-V3.2-100 判据①措辞修正（REQ-V3.2.1-020，文档级）

## M9: 测试（tests/）

- target_kind：fixture（hybrid：C 核心 lib + bindings）→ hybrid；Lersosa → application；空目录/单文件库 → library
- batch_verify：target_kind 段注入/缺省回退；broken_edge 判定路径
- checklist_binder：CK-IMPORT-REGISTRATION/CK-CACHE-GATE-LAYER 绑定命中（import/DI/缓存关键词候选）
- evidence_ledger：门禁⑧ 缺失拦截；r4_feedback 冲突检测（构造 H-7 断言与候选 gate 冲突 fixture）
- surface_mapper：component_role 派生（frontend→client-only 等）
- r2_guard：shipped_config 引用条款注入
- workflow_export：shipped-config 模式导出 + lint
