# v3.2.1 验收记录 — Phase 3.2.1.3（四缺陷修复验证）

> 日期：2026-08-17
> 验收依据：REQ-V3.2.1-040（target_kind 判定准确）/ 041（复跑零回退 + R3 前置捕获）/ 042（门禁 + install）
> 前置：v3.2.1 开发完成（20 SWR，90/90 测试绿，commit 11f0c29）

## 1. target_kind 判定准确（REQ-V3.2.1-040）— PASS

| 项目 | 机械判定 | 人工结论 | 结果 |
|---|---|---|---|
| mixed-fixture（C 核心 + Python/Rust 绑定） | **library**（high，无监听器信号 + Cargo 无 [[bin]]） | library/hybrid（Newtonsoft.Json 库型先例统一裁决） | 一致 ✓ |
| Lersosa（Go/Python/Rust/TS 服务栈） | **application**（medium，12 处监听命中 + kratos 启动链） | application | 一致 ✓ |

两项目队列均已主代理签收（verify_queue.target_kind），门禁⑧ PASS。

## 2. R3 前置捕获验证（REQ-V3.2.1-041）— PASS

用 v3.2.1 任务书（含步骤 0.5 模块可导入性预检 / 步骤 5.5 消费端中间层枚举 /
target_kind 存在性规则段）对历史上 R3.5 才纠正的两个候选做单点 R3 重验：

| 候选 | 历史（v3.2 流程） | v3.2.1 任务书单点重验 | 前置捕获 |
|---|---|---|---|
| CAND-004（爬虫 SSRF） | R3 判 REACHABLE → R3.5 证伪波才发现入口 404 | **NEEDS_REVIEW**，blocking_point=required_args_constructor.py:39（真实 import 执行实证 ModuleNotFoundError + 真实 ComponentScanner 执行吞错 → 零注册 → 404） | ✓ 步骤 0.5 子项 2 捕获 |
| CAND-007（OSS 写出站注入） | R3 判 REACHABLE → R3.5 2/2 证伪才发现 Redis 门闩 | **UNREACHABLE**（默认态），11 跳链 + 步骤 5.5 三查与门闩三组件 1:1 对应（错误分支写反/写读形状不匹配/缓存键无写入方），附 `fmt.Errorf("%w", nil)` Go 探针核实条件态 | ✓ 步骤 5.5 捕获 |

**零回退判据**：两候选终态与 v3.2 验收完全一致（CAND-004 → NEEDS_REVIEW；
CAND-007 → UNREACHABLE），且捕获发生在 R3 阶段（不依赖 R3.5 事后证伪）——
**R3.5 证伪波的核心发现被程序化前置到 R3**。

**验收暴露的新缺陷（已即时修复）**：步骤 0.5 子项 1 措辞缺口——`find_spec` 只验证
顶层包存在性、不执行模块体，对传递依赖断裂（断裂在 import 链内一层）空过；
验证者实测 find_spec('app.adapter.web.crawler_controller') 返回 True 而真实
import 抛 ModuleNotFoundError。已修正任务书：存在依赖可疑时必须用实际导入验证
（python3 -c 'import <module>'，stub 仅第三方依赖）。记入 W6 §26.2。

## 3. 历史队列回放（REQ-V3.2.1-032 判据）— PASS

- **r4_feedback 断言**在 Lersosa 现有队列上检出 1 处冲突：
  `CAND-008 tls_enable: candidate_code_lens=false vs H-7 committed=true` ——
  正是 v3.2 验收时 verifier 的"代码零值默认明文"错误（W6 §25.4），warn 级不阻断
  PASS，主代理裁决：CAND-008 的 correction_record 已纠正该错误，冲突为历史证据
  残留（evidence 保留原文以保可追溯性），无新增动作。
- 六门禁 + 门禁⑧：Lersosa PASS（51/51 追踪，11/11 终态）；fixture（legacy 队列 +
  target_kind 签收）PASS。

## 4. 发布（REQ-V3.2.1-042）— PASS

install 到 skill 目录 + 全量回归（90/90）。

## 5. 结论

四缺陷全部修复并验证：
- **P-A target_kind**：机械判定两项目全对，门禁⑧ 制度化（未签收不放行）
- **P-B1 模块可导入性**：步骤 0.5 强制预检（CK-IMPORT-REGISTRATION 绑定），单点验证证明 R3 即捕获 404 断裂
- **P-B2 中间层枚举**：步骤 5.5 write→read 族强制（CK-CACHE-GATE-LAYER 绑定），单点验证证明 R3 即捕获 Redis 门闩
- **P-C 判据措辞**：服务端组件语言判据 + 客户端组件边界面等价判据（组件角色列）
- **P-D H-7 反哺**：shipped-config 前置盘点 + r4_feedback 机械断言（历史回放即检出 CAND-008 tls 冲突）

遗留（记入 W6 §26 候选）：r4_feedback 冲突解决后 evidence 与 correction_record
的"历史残留"如何处理（保留原文 vs 标注已纠正）尚无规范条款；shipped-config 盘点
workflow 尚未在真实项目上端到端跑过（导出/lint 已测试）。
