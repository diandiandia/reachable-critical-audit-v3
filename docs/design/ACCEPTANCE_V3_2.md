# v3.2 验收记录 — Phase 3.2.3（混合项目试审 + 零回退回归 + 发布）

> 日期：2026-08-17
> 验收依据：REQ-V3.2-100（混合项目试审）、REQ-V3.2-101（单语言零回退回归）、REQ-V3.2-102（合并发布）
> 前置：v3.2 开发完成（SWR 21/21，73 测试绿），fixture 试审与 akka 回归均已完成

## 1. 混合项目试审（REQ-V3.2-100）

### 1.1 自造最小 fixture（ground-truth 对照）— PASS

| 判据 | 结果 |
|---|---|
| ① 语言覆盖表每语言 ≥1 surface 且非零候选 | PASS（C+Python+Rust 三语言全覆盖） |
| ② 全部 FFI 边界有 cross_evidence | PASS |
| ③ 六门禁 PASS | PASS |

**Ground truth 结果**：5 个植入漏洞检出 4 个 REACHABLE，1 个（GT-3 指针截断）被正确证伪为 UNREACHABLE —— skill 纠正了植入方自己的错误（CPython 3.14 全指针透传实证）。R3.5-N 复活攻击 4/4 命中（双标纠偏/事实错误/死代码豁免误用/机制误述各一），**防漏放机制首次实战即产出 4 个真实纠偏**。

**关键缺陷发现（key_finding）**：R0 缺 `target_kind`（application/library）判定 → verifier 对库型目标混用应用审计存在性规则，同批裁决矛盾（2/2 证伪 + 4/4 复活全部指向同一根因）。已按 Newtonsoft.Json 库型先例统一裁决，列为 v3.2.1 最高优先项。

### 1.2 真实混合项目 Lersosa（用户提供，Go 374 + Python 176 + Rust 53 + TS 32）— PASS

| 判据 | 结果 |
|---|---|
| ① 语言覆盖表每语言 ≥1 surface 且非零候选 | PASS（Go 20 面 5 候选 / Python 17 面 5 候选 / Rust 13 面 1 候选；TS 为浏览器客户端组件，1 边界面 cross_evidence + Go 侧归因，qualification 记录） |
| ② 全部 FFI 边界有 cross_evidence | PASS（10/10 边界面双侧证据链落盘：6 REACHABLE / 2 UNREACHABLE / 1 conditional / 1 操作者控制面） |
| ③ 六门禁 PASS | PASS（51/51 面追踪，11/11 候选终态，R3.5-N 复活 2/2，H1-H7 全 VERIFIED） |

**R1→R3.5 全链**：51 面（4 域 + 边界域 10 面）→ 10 候选 → R3 7 REACHABLE / 3 UNREACHABLE → R3.5-N 复活 2/2 未复活（死代码判定 AST 级穷举确认）→ R3.5 证伪波 14/14 → **终态 5 REACHABLE / 2 条件候选（NEEDS_REVIEW）/ 4 UNREACHABLE**。

**R3.5 证伪波的裁决产出**：
- CAND-001（gRPC 流式上传 fileSize 预分配 OOM）：存活，**分级升级** edge_proven→empirically_confirmed（证伪者端到端复现 8TB→RSS 9.4GB、16TB→OOM 死亡）；2 项归因纠正（明文 9003 路径不实——Linux 下客户端 TLS 失败是致命 panic；机制数字修正 ~1.2MB/GB 提交比）
- CAND-003（Rust /v1/reload 无鉴权配置篡改）：存活，+2 补强（artifact_dir="/dev/zero" 无文件写入即可永久 DoS；agent 流水线组合权重劫持）；删除 CSRF 子声明
- CAND-004（Python 爬虫 SSRF）+ CAND-009（CSV 注入/训练投毒）：**共享入口边断裂**——顶层 `common`/`infrastructure` 导入失败 → 爬虫控制器零注册 → /crawler/run 404（证伪者实际启动实证 + 主代理 find_spec 复核）。一致性降级 NEEDS_REVIEW（修复即可达条件候选）
- CAND-007（OSS 配置写出站注入）：2/2 证伪降级 UNREACHABLE（Redis 门闩错误分支写反死代码 + JSON 形状不匹配阻断消费端）；**转正 CAND-011**（未认证 GET 明文返回全部 OSS AccessKey/SecretKey，CWE-522，2 独立对抗证伪者确认）
- CAND-008（无鉴权中间件家族）：存活，归因纠正（shipped config 全部 tls_enable: true；击穿机制=证书在仓+Windows 路径 Linux fail-open；38/88 PRIVATE KEY）
- CAND-010（明文凭据）：存活，+2 补强（凭据横向覆盖 4 类生产服务；TLS 客户端私钥=第二条独立认证路径）；死接线计数勘误 3→2

**v3.2 机制首次实战验证**：lang 分组裁决（PREC-MULTI-LANG-001）、复活攻击（R3.5-N）、机械分级重算、R4↔R3 交叉验证（H-7 f1 在 CAND-001 原判定出错处是对的）。

**新发现的 v3.2.1 缺陷**：
1. `target_kind` 缺失二次出现（fixture 同根因）——Lersosa 三处 verifier 部署前提错误均可追溯至此
2. 判据①措辞未区分客户端组件语言（TS 前端）
3. verifier 盲区扩展：**「模块存在≠被导入」**（导入断裂 + DI 扫描器吞错）；缓存层/门闩层漏枚举（CAND-007 Redis 门闩）

## 2. 单语言零回退回归（REQ-V3.2-101）— PASS

akka-http 复跑（_phase313 基线对照）：**结论与 313 验收完全一致**——CAND-004 REACHABLE，9 候选 UNREACHABLE，零回退。

## 3. 发布（REQ-V3.2-102）

合并 main + install 到 skill 目录（运行时权威切换），R6 lessons 回写已生效（Lersosa 36 条机械提取 + 8 条过程观察 → lessons/SKILL_LESSONS_Lersosa.md）。

## 4. 总体结论

**Phase 3.2.3 三判据全部 PASS。** v3.2 在三个维度达成设计目标：
- **P-A 语言维度**：混合项目 4 语言全覆盖，候选级 lang 属性贯穿（C 词族不再误配 Rust surface）
- **P-B FFI 边界**：10 边界面双侧证据链，边界域捕获了单语言审计会漏的跨语言契约分裂（CAND-005/006 proto 契约 + mTLS 分歧）
- **P-C 防漏放**：R3.5-N 复活 + 证伪波在 fixture（4/4 复活命中）与 Lersosa（2 降级 + 1 转正 + 10 项归因纠正）均产出真实纠偏，无一次误杀 REACHABLE 结论（5 个存活结论全部经 2/2 对抗证伪加固）
- **P-D 制度化**：机械分级重算（CAND-001 升级）、裁决纠正落盘（correction_record 36 条）、R6 自动回写全部生效

**v3.2.1 候选清单**（按优先级）：① target_kind R0 判定 + 部署实证前置；② verifier 任务书补「模块可导入性」预检与缓存/门闩层枚举；③ 判据①客户端语言措辞；④ R4 H-7 默认值盘点反哺 R3 gate 证据。
