# SWR V3.4.5 — gRPC 审计暴露缺陷修复批（5 条）

> 来源：gRPC 全流程审计（2026-08-22）运行实录。设计文档见
> `SYSTEM_DESIGN_V3_4_5.md` 与 `lessons/SKILL_LESSONS_grpc.md`。
> 通用性自检（第一原则）：全部修复为语言无关/项目无关机制，无项目专属名；
> CK-PINNED-DEP 来源列为追溯字段，正文不含项目名。

## 代码级机制缺陷（1-3）

### SWR-V3.4.5-001 gen 输出独立文件 hypotheses_gen.json
- **缺陷**: `signature_matcher.py gen` 输出路径硬编码为 hits.json 同目录
  `hypotheses.json`（signature_matcher.py:323-326），与 R2 LLM 主路径共享
  文件名——本次审计中佐证器 59 条 SIG 假设覆盖了主代理先写的 28 条 LLM
  假设，合并需手工重建（lessons grpc 观察 #2）。
- **修复**: gen 输出改为 `hypotheses_gen.json`；gen 启动前检查
  `hypotheses.json` 已存在则打印 warn（"属 LLM 主路径产物，请合并而非覆盖"）。
  SKILL.md 数据模型速查与 README.md R2 段注明双文件形态。
- **验收**: test_signature_matcher.py gen 用例断言产出
  `.audit_results/hypotheses_gen.json`（原断言改）；构造前置
  hypotheses.json → 输出含 warn 且不写该文件。

### SWR-V3.4.5-002 workflow 脚本 args 形态容忍
- **缺陷**: verify/refutation/resurrect/shipped-config 四处 JS 模板顶层防御
  只覆盖 args 缺失（`!args || !args.candidates` 报错），本次 resurrect 派发
  以裸数组传 args 直接失败（`args.candidates 缺失 (W6 §5)`），浪费一波
  （wave_registry 记录 wf_e3316a79 失败波；lessons grpc 观察 #1）。
- **修复**: 四处模板顶层统一改形态容忍：
  `if (Array.isArray(args)) { args = {candidates: args}; } else { args = args || {}; }`
  （shipped-config 模式 payload_key=components 同改）。next_step 契约声明保留。
- **验收**: test_workflow_export.py 导出断言 JS 含 `Array.isArray(args)` 包装；
  裸数组形态走顶层逻辑不报 `args.candidates 缺失`。

### SWR-V3.4.5-003 merge 域内 id 序列空洞告警
- **缺陷**: boundary 域 agent 产出缺号（001,002,004..013 无 003），
  `merge_surfaces` 有去重无空洞检测，静默放行（lessons grpc 观察 #3）。
- **修复**: merge 收尾按归一化域前缀（SURF-NETWORK-/DATA-/PROCESS-/STORAGE-/
  BOUNDARY-）检测编号序列空洞，输出 warn（非阻断）：
  `[merge] warn: surface id 序列空洞 SURF-BOUNDARY-003 missing (13 条在册)`。
- **验收**: test_surface_mapper.py 构造缺号 fixture → 输出含空洞行且
  exit 0（不阻断合并）。

## 制度沉淀（4-5）

### SWR-V3.4.5-004 清单库新增 CK-PINNED-DEP
- **缺陷**: 清单库 28 条无 vendored/钉住依赖条目，跨仓库依赖审计
  （钉住 commit 常量核对）依赖 verifier 现场发挥（gRPC BoringSSL 实证
  模式为正面案例，无失误案例——checklist 级沉淀，非强制义务）。
- **修复**: resources/checklist_library.json 新增 CK-PINNED-DEP（family=
  vendored-deps，关键词 pin/vendored/submodule/锁定版本/依赖版本/钉住，
  applies_to verifier），四步：①定位依赖声明点（构建文件/锁文件钉住版本）
  ②解析 pin 取确切版本源码（禁止任意最新版核对）③核对声称机制常量/上限/
  开关的 pin 版实际值（注意条件分支语义）④pin 值 + 源码出处作为阻断点证据。
- **验收**: 资源加载校验通过（结构对齐既有条目）；关键词
  "vendored"/"submodule" 命中绑定；去项目化扫描 0 命中。

### SWR-V3.4.5-005 编排层铁律四：args 派发形态纪律
- **缺陷**: resurrect 裸数组误传的根因是派发侧纪律缺失（next_step 已声明
  契约），机械兜底（SWR-002）之外需要纪律条款防止依赖兜底。
- **修复**: SKILL.md 编排层铁律新增第四条——args 必须按导出 next_step
  声明的对象包裹形态传递，裸数组是派发错误（脚本容忍仅为机械兜底，
  禁止依赖兜底），附 gRPC 复活波失败实录为可追溯案例。
- **验收**: test_doc_lint.py（或 SKILL 结构校验）断言铁律四条款存在。
