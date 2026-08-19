# Reachable Critical Audit v3.3 — 系统需求规格书（System Requirements）

> 从 `SYSTEM_DESIGN_V3_3.md`（问题域 P-A~P-F）导出的系统开发需求。每条附来源追溯与验收判据。
> 状态追踪见 `REQUIREMENTS_TRACKING.md`（v3.3 段）。日期：2026-08-19
> 编号规则：REQ-V3.3-xxx；优先级：P0=影响结论正确性/覆盖率，P1=影响效率/契约一致性
> 最高判据：SKILL.md「第一原则：通用型 Skill」（全部需求去项目化）

## 1. 签名库系统语言与漏洞类型覆盖（P-A）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-001 | L2 词族新增 c/go/rust/java 4 族（每族 ≥1 签名、lang 必填、去项目化扫描 0 命中）；VALID_LANGS 同步扩充 | 设计 §1 P-A.1 | P0 | validate 通过；4 族签名可被 match 按 surface.lang 命中；含项目专属名的 grep 被 validate 拒绝 |
| REQ-V3.3-002 | L3 新增 SIG-STATE-RACE（CWE-362/367：check-then-act/TOCTOU/跨线程无同步）与 SIG-CRYPTO-WEAK（CWE-327/330：非密码学随机种子/可预测种子/弱哈希替代校验）语义族 | 设计 §1 P-A.2 | P0 | 2 族入库且 cwe/semantic/lang 完备；R0 selfcheck 完整性 PASS |
| REQ-V3.3-003 | L3 既有族补系统形态 grep hints：PREALLOC-LEN 补声明计数→分配类词、TRUNC-CAST 补 C 窄化 cast 形态、BUFFER-ACCUM 补流式无界读形态（全部去项目化） | 设计 §1 P-A.3 | P0 | hints 无项目专属名；对 C 测试 fixture 能产生命中（佐证器非空转） |
| REQ-V3.3-004 | L2 词族与 harness_manual 覆盖语言对齐检查：新 4 族对应语言手册已存在（c/go/rust/java 在 harness_manuals/ 中） | 设计 §1 P-A | P1 | 对齐表生成无缺项 |

## 2. 项目形态判定重构（P-B）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-005 | `_classify_project_kind` 返回四值 {framework, library, infra, app}（补 library 返回路径）；构建文件降为加权信号之一；新增公共 API 主导信号（导出符号/头文件率/无 main/无监听）与框架扩展标志信号 | 设计 §1 P-B.1 | P0 | 纯库 Cargo.toml 项目判 library；有 main+监听项目判 app；四值均有测试用例 |
| REQ-V3.3-006 | context 新增独立 maturity 信号（版本标签语义/成熟标志文件/已知框架对照表）；maturity 与 project_kind 解耦；unknown 时保守 | 设计 §1 P-B.2 | P1 | Lua 项目 context 输出 maturity 非 unknown（Makefile 检出后按信号判定）或明确 unknown 原因 |
| REQ-V3.3-007 | SKILL.md「R4 与 R3 并行启动」触发条件改为 maturity==mature（机械信号），主代理复核后可手动覆盖；project_kind==framework 不再单独触发 | 设计 §1 P-B.3 | P0 | SKILL.md 措辞与实现一致；doc-lint 测试抽取该段验证实现存在 |

## 3. 信任边界分类与域映射（P-C）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-008 | trust_boundary.type 枚举补 `host_api`（语义：数据经宿主对公共 API 的调用进入；library 组件默认建议值）；surface_mapper normalize/validate 与 R1 任务书 schema 同步 | 设计 §1 P-C.1 | P0 | 含 host_api 的 surface 通过 validate；library target_kind 项目测绘产物 host_api 占比 >0 |
| REQ-V3.3-009 | R1 任务书 4 域 guide 增补「非网络/离线项目」映射段（解析引擎/数据处理库/硬件协议栈示例；network 空域 + empty_domain_reason 为合法产出） | 设计 §1 P-C.2 | P0 | 任务书含该段；离线库 fixture 测绘不再将宿主 API 输入归 local/environment |

## 4. 保守倾向明示化（P-D）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-010 | SKILL.md R5 段明示「不实证不申报」路径（NEEDS_REVIEW 合法终态）与源事实级降级规则引用（W6 §17.7/§21.4）为 verifier 可引用条款 | 设计 §1 P-D | P1 | SKILL.md 含该段；verifier 任务书引用一致 |
| REQ-V3.3-011 | 报告模板 NEEDS_REVIEW 段注明「保守裁决」与「证据不足」两种成因的区分写法 | 设计 §1 P-D | P1 | 报告模板含双成因字段 |

## 5. 先例库系统级覆盖（P-E）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-012 | 先例库新增 PREC-ALLOC-VIRTUAL-001（分配请求类声称的提交内存判据）与 PREC-ENV-SAME-PRINCIPAL-001（env→代码加载类声称的同主体边界几何）；全部去项目化（项目名仅入追溯字段） | 设计 §1 P-E | P1 | 2 条先例入库；grep 运行时字段无项目名 |

## 6. 契约同步与验收判据（P-F）

| 编号 | 需求 | 来源 | 优先级 | 验收判据 |
|---|---|---|---|---|
| REQ-V3.3-013 | tools/gen_tracking.py DOCS 字典覆盖全部版本段（v3~v3.3 的 REQ/SWR 文档）；提取正则泛化为 `(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`；重建 REQUIREMENTS_TRACKING.md 含 v3.2~v3.3 全部段 | 设计 §1 P-F | P1 | 重建后 tracking 含 REQ-V3.2.2-xxx 与 REQ-V3.3-xxx 全部条目 |
| REQ-V3.3-014 | 验收判据强化：每版本至少一个新项目验收 + 该新项目须覆盖非 Web 形态（系统库/解析引擎/CLI 工具类） | 设计 §0.1 黑名单裁决 | P1 | v3.3 验收记录含非 Web 新项目场景 |

## 7. 排除项（明确不做）

- 不修改 v3 阶段骨架与六门禁语义
- 不新增判定器角色（规则库保持提示器定位）
- 不扩充黑名单（tripwire 定位不变；防线依赖验收过程控制）

## 修订记录（v3.3.2, SWR-V3.3.2-071）

- **H7 默认值表义务收缩**（2026-08-19, 依据七项目批次复盘 §28 O1）：
  原"每默认值 × 五维全表"义务收缩为**安全相关默认值清单**（tls/auth/listen/
  password/limits/timeouts 类，≤10 项，五维仅风险行填）——旧表 80% 行零信息量
  且消费方 r4_feedback 从未机械运行。结构化 schema 与 r4_feedback 接线见
  REQ-V3.3.2-013/018。本文件 H7 相关条文按此修订解释。
