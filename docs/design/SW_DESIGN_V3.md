# Reachable Critical Audit v3 — 软件设计文档（Software Design）

> **文档性质**：满足 `REQ_V3.md` 系统需求的软件级设计。定义模块分解、接口签名、关键算法、数据流。
> 软件开发需求（SWR-V3-xxx）由此文档导出，见 `SWR_V3.md`；状态追踪见 `REQUIREMENTS_TRACKING.md`。
> **日期**：2026-08-16

## 1. 模块总览

```
┌───────────────┐   ┌────────────────┐   ┌─────────────────┐   ┌────────────────┐
│ M1 surface    │   │ M3 signature   │   │ M6 batch_verify │   │ M5 harness     │
│    _mapper    │──▶│    _matcher    │──▶│    (队列/断言)   │──▶│    _runner     │
│ (R1 测绘编排) │   │ (R2 假设生成)  │   │  + M4 evidence  │   │ (R5 实证)      │
└───────────────┘   └────────────────┘   │    _ledger      │   └────────────────┘
        │                    │           └─────────────────┘           │
        ▼                    ▼                  ▲                      ▼
  input_surface.json   hypotheses.json   verify_queue.json   empirical 结果写回
        │                    │                  ▲
        └────────┬───────────┘                  │
                 ▼                              │
          M9 任务书模板库（测绘/筛选/验证/H1-H7/harness 任务书）─────────┘
                 ▲
  M2 signature_library.json（签名数据 + 冒烟测试）
  M7 r05_diff_archaeology.py（R0.5）  M8 ast_scanner.py（深度模式+过滤+字段填充）
```

模块与需求覆盖：

| 模块 | 职责 | 覆盖 REQ-V3 |
|---|---|---|
| M1 surface_mapper.py | R1 测绘任务书生成、产出校验、合并 | 020-026 |
| M2 signature_library.json | 签名数据模型 + 冒烟测试 | 010, 030-033 |
| M3 signature_matcher.py | 窗口展开、hints 匹配、假设生成、筛选任务书 | 034-038 |
| M4 evidence_ledger.py | 证据分级校验、前提维度、账本写回、断言 | 003, 040-052, 070-073 |
| M5 harness_runner.py | R5 触发判定、模板注册、执行、写回 | 004, 060-064 |
| M6 batch_verify.py | 队列状态机（v2.1 迁移+改造） | 047, 080-086 |
| M7 r05_diff_archaeology.py | R0.5 考古（--cross-tags 等） | 012-016 |
| M8 ast_scanner.py | 深度模式/过滤映射/字段填充/merge | 081, 086-088 |
| M9 task_templates/ | 全部子智能体任务书模板 | 021, 040, 043-044, 048-049 |

## 2. M1 surface_mapper.py

```python
DOMAINS = ["network", "data", "process", "storage"]

def gen_surface_tasks(project_root: str, lang: str, ctx: ArchitectureContext) -> list[TaskSheet]:
    """按 4 域生成测绘任务书。ctx 由 build_architecture_context() 从
    README/依赖清单(Package.swift|Cargo.toml|pom.xml|CMakeLists)/目录树生成。"""

def build_architecture_context(project_root: str) -> ArchitectureContext:
    """产出 {lang, deps[], entry_hints[], maturity, build_files[]}"""

def validate_surfaces(data: dict) -> tuple[bool, list[str]]:
    """校验 input_surface.json: 每 surface 的 entry_points 非空且含
    evidence(file:line+代码片段)、trust_boundary 枚举合法、confidence 合法。"""

def merge_surfaces(files: list[str]) -> dict:
    """多 agent 产出合并: 同 entry_point 多域归属 → 多域 tags; 冲突 → conflicts[]"""
```

**关键算法——入口证据强制**：validate 对每个 entry_point 检查 `evidence.snippet` 非空且 `file:line` 可定位到源码真实行（行内容含 snippet 前 40 字符的模糊匹配），不满足即拒收（REQ-V3-022）。

## 3. M2 signature_library.json

```json
{"schema_version": "3.0",
 "signatures": [{
   "sig_id": "SIG-BUFFER-ACCUM-001",
   "semantic": "远端投递数据的无界累积（帧/body/流）在大小校验之前发生",
   "cwe": ["CWE-770"],
   "platform_profiles": ["server-framework"],
   "detection_hints": {"grep": ["extend_from_slice", "writeFully", "readRemaining", "++= payload"],
                       "checklist": ["累积点在哪?", "flush/对齐条件?", "上限在累积前还是后?"]},
   "known_instances": [
     {"project": "actix-web", "file": "actix-web-actors/src/ws.rs", "line": 771, "confirmed": true},
     {"project": "ktor", "file": "ktor-websockets/.../SimpleFrameCollector.kt", "line": 23, "confirmed": true}],
   "empirical_harness": "ws_frame_accum"}],
 "smoke_test": {"mode": "anchor_recall", "required_hit_rate": 1.0}}
```

**冒烟测试**：R0 对每个签名取 1 个 known_instance，在源码副本上验证 detection_hints 可命中该位置；命中率 <100% 阻止启动（REQ-V3-010，v2.1 锚点召回语义的扩展）。

## 4. M3 signature_matcher.py

```python
def expand_window(entry: EntryPoint, project: ProjectIndex, depth: int = 3) -> list[CallSite]:
    """沿调用图展开: 第 0 层 = entry 所在函数; 每层用项目函数索引
    (预建 {callee_name: [caller_sites]}) 找调用者。产出窗口内全部调用点。"""

def match_signatures(surfaces: list[Surface], signatures: list[Signature],
                     project: ProjectIndex, depth: int = 3) -> list[Hit]:
    """对窗口内调用点的源码行跑 detection_hints.grep。
    Hit = {surface_id, sig_id, site(file:line), matched_pattern}"""

def gen_hypotheses(hits: list[Hit]) -> dict:
    """去重(同 surface×sig 合并)、附签名 checklist 与 semantic_family、
    生成 HYP-xxx、status=PENDING。LOGIC_PATTERN 签名独立队列。"""

def emit_filter_tasks(hypotheses: dict, batch: int = 12) -> list[TaskSheet]:
    """LLM 快速筛选任务书: 排除明显常量/白名单/死代码场景"""
```

**ProjectIndex**（预建轻量索引，一次性）：`{callee_name: [(file, line, caller_func)]}` 由 grep 全库函数定义+调用点构建；只服务于窗口展开（深度≤3），不需要完整调用图精度。

## 5. M4 evidence_ledger.py

```python
GRADES = ["static_only", "edge_proven", "empirically_confirmed"]

def grade_verdict(v: dict) -> tuple[str, list[str]]:
    """规则: REACHABLE 且 call_chain 每跳无 edge_evidence → static_only;
    边证据项缺 proof 文本 → 报错; empirical 字段非空 → empirically_confirmed。
    返回 (grade, errors)。"""

def check_preconditions(v: dict) -> list[Issue]:
    """platform_precondition 无 platform_evidence → Issue(需 NEEDS_REVIEW);
    trust_boundary 无 per-channel 验证记录 → Issue;
    gate 可降级配置未记录 → Issue(warn)。"""

def commit(queue: dict, verdict: dict) -> dict:
    """merge 语义写回; 证伪/降级时追加 correction_record[]"""

def assert_ledger(queue: dict) -> tuple[bool, list[dict]]:
    """门禁: ①无 PENDING; ②REACHABLE 无 static_only(可申报性);
    ③实证类声称全部 empirically_confirmed; ④H1-H7 全部 VERIFIED"""
```

## 6. M5 harness_runner.py

```python
EMPIRICAL_CLAIMS = {"crash", "panic", "oom", "unbounded", "xss", "protocol_dos"}

def needs_harness(candidate: dict) -> bool:
    """verdict claim ∈ EMPIRICAL_CLAIMS 且 evidence_grade < empirically_confirmed"""

def register(name: str, spec: HarnessSpec) -> None:
    """spec = {langs[], check_cmd, run_cmd, attack_scripts[], sampler}"""

def run(harness: str, target: Target, budget: Budget) -> EmpiricalResult:
    """启动 target → 采样基线 → 执行 attack → 时序采样(RSS/存活/exit) → 采集结果"""

def apply_result(candidate: dict, result: EmpiricalResult) -> dict:
    """confirmed → grade=empirically_confirmed; refuted → correction_record
    + verdict 降级 + 候选标记 superseded_by"""
```

**内置模板**（REQ-V3-061）：`ws_frame_alloc`、`ws_frame_accum`、`xss_path_sim`、`multipart_align`（规格：攻击脚本、基线指标、判据阈值、环境记录字段）。

**时序采样算法**（本战役 R5 验证）：对目标进程每 1s 读 /proc/<pid>/status VmRSS + `kill -0` 存活；判据 = RSS 增量与投递字节的相关性（如 +64KB/块 = 累积确认；+1GB/单帧头 = 预分配确认）。**前提检查**：沙箱代理可能限流——先慢速采样确认投递速率，以"服务器实测到达量"为准而非客户端发送量（vapor/actix 教训）。

## 7. M6 batch_verify.py（改造规格）

| 改造点 | 规格 |
|---|---|
| collect id 契约 | `--cand-<full-id>=...` 按字面 id 查队列（REQ-V3-080） |
| merge 语义 | 所有入队阶段（r05/r1/r15/collect）只增改不覆写（REQ-V3-081） |
| 校验统一 | collect 与 assert 共用 `_validate_verdict_payload()`；UNREACHABLE 允许 blocking_point ∈ {"N/A","no production callers"}（REQ-V3-082） |
| 簇模式 | `--stage next-cluster`：file×sink 族聚合任务书；`--cluster <id> --verdict ...` 广播；簇成员标记 clustered_verified（REQ-V3-047） |
| 批参数 | `--batch-size N` + `--group-by-file`（REQ-V3-083） |
| R4 stages | `--stage r4-collect --file f.json` / `--stage r4-assert` / `--stage report`（REQ-V3-084） |
| JSON 容错 | 加载失败→非法反斜杠转义修复重试→仍失败记 errors 不丢批（REQ-V3-085） |
| 心跳契约 | 任务书要求先写 `<out>.pending`（含 started_at）；collect 对账"簇清单 vs 产出文件"；落盘冲突→`.agent-<id>` 后缀（REQ-V3-049/050） |

## 8. M7/M8 改造规格

**M7 r05_diff_archaeology.py**：`--cross-tags` 用 `git merge-base --is-ancestor <fix> <tag>` 生成矩阵；无 `.git` → `{"status":"NO_GIT"}`；HEAD 模式任务书为"变体复核"；默认落盘；grep 词表 `security` 与 `fix` 分级。

**M8 ast_scanner.py**：`--mode deep`（tree-sitter 深度模式，供 verifier 佐证用，非默认路径）；路径过滤语言映射表 `LANG_TEST_PATH_MAP = {ruby: ["/spec/"], powershell: ["tst/", "*.Tests.*"], rust: ["*_tests.rs","/benches/"], ts: ["*.spec.*","*.test.*"]}`；入队填 source_pattern/language；merge 语义；`--noise-check`（规则误报率抽样）。

## 9. M9 任务书模板库（task_templates/）

| 模板 | 用途 | 强制字段 |
|---|---|---|
| surface_map_domain.md | R1 测绘（4 域变体） | 项目背景、域、产出 schema、证据强制 |
| hypothesis_filter.md | R2 假设筛选 | 假设清单、排除判据（常量/白名单/死代码） |
| verifier_edge_proof.md | R3 验证 | 边证据要求、前提维度（platform/trust/gate）、死代码豁免、分级规则 |
| biz_hypothesis.md | R4 H1-H7 | 三选一 verdict、H7 信任边界检查项 |
| empirical_test.md | R5 执行说明 | 采样协议、环境记录、判据 |
| self_json_guard | 全部模板尾部 | "输出必须经 json.load 校验通过后提交" |

## 10. 数据流（端到端）

```
项目源码 ──M1──▶ input_surface.json ──M3(窗口展开+hints)──▶ hypotheses.json
   │                                                        │
   │                                                        ▼
   │                                          M9 verifier 任务书 ──▶ 子智能体 ──▶ verdict
   │                                                        │
   │                                                        ▼
   │                                          M4 分级/前提校验 ──▶ verify_queue.json
   │                                                        │
   │                                          M5 needs_harness? ──是──▶ harness 执行 ──▶ 结果写回
   │                                                        │
   └─────────────── M7(R0.5 考古) ──▶ r05 产物 ──────────────┴──▶ M4 assert_ledger ──▶ 报告
```

## 11. 测试策略

| 模块 | 测试要点 |
|---|---|
| M1 | schema 校验拒收（缺证据/非法枚举）、合并去重 |
| M3 | 窗口展开深度正确、hits 去重、LOGIC_PATTERN 独立 |
| M4 | 分级规则（无证据→static_only）、前提 Issue、断言门禁 |
| M5 | 触发判定、采样解析、写回/证伪路径 |
| M6 | v2.1 回归 + 新契约（字面 id/merge/簇/容错） |
| M7 | --cross-tags 矩阵正确性（AWStats 三 tag 已知结论对照）、NO_GIT |
| M8 | 路径映射 5 形态全拦截、字段填充、merge |
| 集成 | sinatra/lighttpd/actix 三个已审计项目复跑对照（Phase 3 判据） |
EOF