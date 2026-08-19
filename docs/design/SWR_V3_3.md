# Reachable Critical Audit v3.3 — 软件需求规格书（Software Requirements）

> 从 `SW_DESIGN_V3_3.md` 组件 M1~M12 导出的软件开发需求。
> 编号规则：SWR-V3.3-xxx；状态：未开发 / 开发中 / 已完成。
> 状态追踪：`REQUIREMENTS_TRACKING.md`（v3.3 段）。日期：2026-08-19

## M1: signature_library.json 资产扩充（REQ-V3.3-001/002/003）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-001 | L2 词族新增 `c`：grep 词覆盖 malloc/realloc 无上限家族（无预算检查的分配点）、varint/长度字段计数驱动分配形态；lang 必填 c | 已完成 |
| SWR-V3.3-002 | L2 词族新增 `go`：流式累积/无界 reader 消费词（io.Copy 无 limit/append 无总量预算）；lang 必填 go | 已完成 |
| SWR-V3.3-003 | L2 词族新增 `rust`：unsafe 块特征词、FFI 指针逃逸（transmute/from_raw_parts 无边界）、Vec 无界增长；lang 必填 rust | 已完成 |
| SWR-V3.3-004 | L2 词族新增 `java`：流式无界读取（InputStream.read 循环无 limit）、反序列化 sink（ObjectInputStream/readObject 不可信源）；lang 必填 java | 已完成 |
| SWR-V3.3-005 | L3 新增 SIG-STATE-RACE：cwe=[CWE-362, CWE-367]，semantic=检查与使用分离（TOCTOU/check-then-act）、跨线程共享状态无同步；grep 词去项目化 | 已完成 |
| SWR-V3.3-006 | L3 新增 SIG-CRYPTO-WEAK：cwe=[CWE-327, CWE-330]，semantic=非密码学随机源作安全用途、可预测种子（时间戳/地址）、弱哈希替代完整性校验；grep 词去项目化 | 已完成 |
| SWR-V3.3-007 | L3 既有族 hints 扩充：PREALLOC-LEN 补声明计数→分配类词（newvector 类/checked 分配前无预算）；TRUNC-CAST 补 C 窄化 cast 形态；BUFFER-ACCUM 补流式无界读形态；去项目化扫描 0 命中 | 已完成 |

## M2: signature_lib.py（REQ-V3.3-001/002/004）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-010 | VALID_LANGS 扩充 c/go/rust/java；validate 对新 L2 族执行 lang 必填 + 去项目化检查（与既有族同路径） | 已完成 |
| SWR-V3.3-011 | integrity_selfcheck 自动覆盖新签名（无签名数硬编码）；L2 词族 ↔ harness_manuals 对齐检查（c/go/rust/java 手册存在性）输出 | 已完成 |

## M3: signature_matcher.py（REQ-V3.3-001）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-020 | lang 过滤对新 4 族生效（由 VALID_LANGS 驱动，无硬编码语言表）；命中落盘沿用 .audit_results/ 路径 | 已完成 |

## M4: surface_mapper.py 分类器重构（REQ-V3.3-005/006/008）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-030 | `_classify_project_kind` 四值返回 {framework, library, infra, app}；library 判据=公共 API 主导（导出符号密度/头文件率/无 main/无监听器）且无独立可执行入口 | 已完成 |
| SWR-V3.3-031 | 构建文件信号加权：原硬映射表降为 SIG 权重表（framework 标志文件 +x、infra 标志文件 +y、公共 API 信号 +z），阈值决策并输出 signals 证据列表 | 已完成 |
| SWR-V3.3-032 | BUILD_FILES 检出修复：确认 Makefile/CMakeLists 等根目录构建文件的扫描路径正确（Lua 审计实测 build_files=[] 根因修复） | 已完成 |
| SWR-V3.3-033 | context 新增 maturity 信号对象 {level: mature|developing|unknown, signals: [...]}；与 project_kind 解耦；mature 判据=版本标签语义（≥1.0 或稳定发布）+ 已知框架对照表命中 | 已完成 |
| SWR-V3.3-034 | trust_boundary normalize/validate 接受 host_api（枚举扩充为加性变更；旧文件不受影响） | 已完成 |

## M5: task_templates 增补（REQ-V3.3-008/009/010）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-040 | surface_map_domain.md：schema trust_boundary.type 枚举补 host_api；4 域 guide 增补「非网络/离线项目」映射段（解析引擎/数据处理库/硬件协议栈示例；network 空域 + empty_domain_reason 合法）；library 组件默认边界建议 host_api | 已完成 |
| SWR-V3.3-041 | biz_hypothesis.md：H7 五维表模板补密码学/随机数默认值行（seed/随机源）为红旗项 | 已完成 |
| SWR-V3.3-042 | verifier 任务书步骤 3 跨边界判定补 host_api 边界语义（库组件：公共 API 即边界；跨边界≠跨主体——R3.5 惯例假设拦截的制度化预防） | 已完成 |

## M6: precedent_library.json（REQ-V3.3-012）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-050 | PREC-ALLOC-VIRTUAL-001 入库：分配请求类声称的提交内存判据（虚拟分配≠资源耗尽；提交内存受输入流限制→无放大→severity ≤ Low）；applicability_scope=allocation/oom 类 | 已完成 |
| SWR-V3.3-051 | PREC-ENV-SAME-PRINCIPAL-001 入库：env→代码加载类声称的同主体边界几何（env 控制者=启动者本人→LD_PRELOAD 等效；无 shipped 特权部署证据→DIRECT+Low）；applicability_scope=env-driven 代码执行类 | 已完成 |

## M7: tools/gen_tracking.py（REQ-V3.3-013）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-060 | DOCS 字典覆盖 v3/v3.1/v3.2/v3.2.1/v3.2.2/v3.3 全部 REQ/SWR 文档；提取与 load_status 正则泛化为 `(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`（兼容旧 REQ-V3-001 形态） | 已完成 |
| SWR-V3.3-061 | 重建 REQUIREMENTS_TRACKING.md：含全部版本段；保留既有状态列；v3.2~v3.3 新段初始状态=未开发 | 已完成 |

## M8: SKILL.md 契约同步（REQ-V3.3-007/008/010/011）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-070 | v3.1 段「mature framework → R4 并行」触发条件改写为 maturity==mature（机械信号 + 主代理复核可覆盖）；project_kind==framework 不再单独触发 | 已完成 |
| SWR-V3.3-071 | R5 段明示「不实证不申报」路径（NEEDS_REVIEW 合法终态）与源事实级降级规则引用（W6 §17.7/§21.4） | 已完成 |
| SWR-V3.3-072 | R1 段 trust_boundary 枚举表补 host_api（语义：宿主对公共 API 的调用进入；library 组件默认） | 已完成 |
| SWR-V3.3-073 | 报告段 NEEDS_REVIEW 双成因字段（保守裁决 / 证据不足） | 已完成 |
| SWR-V3.3-074 | SKILL.md 新增 v3.3 增量段（P-A~P-F 摘要 + SYSTEM_DESIGN/REQ/SW_DESIGN/SWR 文档指针） | 已完成 |

## M9: tests/（REQ-V3.3-005/006/013/014）

| 编号 | 需求 | 状态 |
|---|---|---|
| SWR-V3.3-080 | test_surface_mapper 四值分类用例：纯库 Cargo.toml→library / main+监听→app / 无构建文件→app / CMakeLists→infra；maturity 信号用例 | 已完成 |
| SWR-V3.3-081 | test_signature_lib：新 4 L2 族 lang 必填 + 去项目化；新 2 L3 族 cwe 完备；对齐检查输出 | 已完成 |
| SWR-V3.3-082 | test_signature_matcher：新族按 surface.lang 过滤命中用例 | 已完成 |
| SWR-V3.3-083 | test_v33.py：gen_tracking 泛化重建用例（REQ-V3.2.2-001 与 REQ-V3.3-001 均被提取） | 已完成 |
| SWR-V3.3-084 | fixture 扩充：非 Web 系统语言 fixture（C 解析器/系统库形态）作为 v3.3 验收新项目锚点 | 已完成 |
