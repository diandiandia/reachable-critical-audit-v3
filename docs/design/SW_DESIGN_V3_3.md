# Reachable Critical Audit v3.3 — 软件设计（组件级）

> 从 `SYSTEM_DESIGN_V3_3.md` 导出的组件修改设计。日期：2026-08-19
> 最高判据：SKILL.md「第一原则：通用型 Skill」——本版全部组件修改都必须通过
> 自检四问（去项目名 / 语言无关或按 lang 分派 / 无具体项目路径 / 新项目验收）。

## 组件影响清单

| 组件 | 修改点 | 对应 REQ |
|---|---|---|
| M1 resources/signature_library.json | ①L2 词族新增 c/go/rust/java 4 族（每族 1-2 签名：c=malloc 无上限/varint 计数驱动分配；go=流式无界累积；rust=unsafe 块/FFI 指针；java=流式无界读取/反序列化 sink；全部去项目化）②L3 新增 SIG-STATE-RACE（CWE-362/367）与 SIG-CRYPTO-WEAK（CWE-327/330）③L3 既有族（PREALLOC-LEN/TRUNC-CAST/BUFFER-ACCUM）grep hints 补系统形态词 | REQ-V3.3-001/002/003 |
| M2 signature_lib.py | VALID_LANGS 扩充 c/go/rust/java；validate 对新 L2 族执行与既有族相同的 lang 必填/去项目化检查；smoke/integrity 自检自动覆盖新签名 | REQ-V3.3-001/002 |
| M3 signature_matcher.py | lang 过滤自动覆盖新 4 族（VALID_LANGS 驱动，无硬编码）；hits 落盘路径沿用 v3.2.3 修复（.audit_results/） | REQ-V3.3-001 |
| M4 surface_mapper.py | ①`_classify_project_kind` 重构：四值返回 {framework, library, infra, app}；构建文件降为加权信号（新增 SIG 权重表）；新增公共 API 主导信号（导出符号密度/头文件率/无 main/无监听器探测）与框架扩展标志信号（插件注册/中间件挂载/生命周期钩子词）②context 新增 maturity 信号（版本标签语义/成熟标志文件/已知框架对照表；unknown 为合法值）③build_files 检出修复（Makefile/CMakeLists 未检出根因：BUILD_FILES 扫描范围）④trust_boundary normalize/validate 接受 host_api | REQ-V3.3-005/006/008 |
| M5 task_templates/surface_map_domain.md | ①schema trust_boundary.type 枚举补 host_api ②4 域 guide 增补「非网络/离线项目」映射段（解析引擎/数据处理库/硬件协议栈示例；network 空域 + empty_domain_reason 为合法产出）③library 组件默认边界建议 host_api | REQ-V3.3-008/009 |
| M6 task_templates/biz_hypothesis.md | H7 五维表模板微调：密码学/随机数默认值行（seed/随机源）纳入红旗项；不改假说编号 | REQ-V3.3-002（佐证） |
| M7 resources/precedent_library.json | 新增 PREC-ALLOC-VIRTUAL-001（分配请求类声称：虚拟分配≠资源耗尽、提交内存受输入限制则无放大 → severity ≤ Low）与 PREC-ENV-SAME-PRINCIPAL-001（env→代码加载类声称：同主体=LD_PRELOAD 等效，无 shipped 特权部署证据 → DIRECT+Low）；追溯字段写来源 | REQ-V3.3-012 |
| M8 tools/gen_tracking.py | DOCS 字典覆盖 v3~v3.3 全部 REQ/SWR 文档；提取正则泛化 `(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`；load_status 同正则；重建 REQUIREMENTS_TRACKING.md | REQ-V3.3-013 |
| M9 SKILL.md | ①v3.1 段「mature framework → R4 并行」触发条件改为 maturity==mature（机械信号+主代理可覆盖）②R5 段明示「不实证不申报」路径与源事实级降级规则引用③R1 段 trust_boundary 枚举表补 host_api ④新增 v3.3 增量段（P-A~P-F 摘要 + 需求文档指针） | REQ-V3.3-007/010/008 |
| M10 task_templates（verifier 相关） | verifier 任务书步骤 3 跨边界判定补充 host_api 边界语义（库组件：公共 API 即边界，跨边界≠跨主体） | REQ-V3.3-008 |
| M11 report 模板（SKILL.md 报告段） | NEEDS_REVIEW 段注明「保守裁决」与「证据不足」双成因字段 | REQ-V3.3-011 |
| M12 tests/ | ①test_surface_mapper：四值分类用例（纯库 Cargo.toml→library / main+监听→app / 无构建文件→app / CMakeLists→infra）②test_signature_lib：新 4 族 lang 必填/去项目化；新 2 L3 族 cwe 完备 ③test_signature_matcher：新族 lang 过滤命中 ④test_v33.py：maturity 信号用例 + gen_tracking 泛化重建用例 ⑤fixture 扩充：C/系统语言 fixture（非 Web 新项目验收锚点，REQ-V3.3-014） | REQ-V3.3-005/006/013/014 |

## 数据模型变更

1. **签名资产 v3.3**：`signature_library.json` 签名数 13 → 19~21（L2 +4~6、L3 +2）；全部沿用 v2 数据模型（lang/cwe/semantic/detection_hints/known_instances 退役）
2. **context 输出**：新增 `maturity: {level: mature|developing|unknown, signals: [...]}`；`project_kind` 取值域扩为四值
3. **input_surface.json**：trust_boundary.type 枚举 +`host_api`（schema_version 不变，validate 兼容）
4. **REQUIREMENTS_TRACKING.md**：重建后含 v3.2/3.2.1/3.2.2/3.3 全部段

## 兼容性

- 旧 surface 文件（无 host_api）validate 照常通过（枚举扩充是加性变更）
- 旧签名资产不受影响；VALID_LANGS 扩充后旧 L2 族行为不变
- project_kind 三值 → 四值：依赖旧三值的调用点（R4 并行触发）已由 REQ-V3.3-007 改为 maturity 驱动，无残留三值假设
- gen_tracking 泛化后旧 ID（REQ-V3-001 形态）仍被识别（正则兼容）
