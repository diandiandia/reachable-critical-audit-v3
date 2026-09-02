# REQ V3.19 — V8 审计复盘缺陷修复（2026-09-02）

## 上下文

V8 审计（2026-09-01/02，首个运行时/引擎形态验收项目 + 实证复活波）全流程闭合后，
lessons 落盘 `/root/v8/.audit_results/lessons.md`（唯一读入口，已按纪律读取）。
六条 skill 教训候选全部经代码取证核实（编辑点行号为 dev 树实测）；其中 2 条
（L3/L4 方向）与既有机制重叠——按义务棘轮裁除条款只补提示/明示，不重造。
本版不改阶段骨架、六门禁①-⑧判据语义、队列数据模型主体。

## 修复清单（6 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | correction_record 字符串条目使 assert_ledger 崩——`cr.get("demote_to")` 对 str 条目 AttributeError（V8 审计主代理裁决按字符串落盘实录, gate ⑤/③c 检查路径直接崩溃） | assert_ledger 的 adjudication_verification 检查对 str 条目 lenient 跳过（字符串=注记形态, dict=demote 裁决形态——放宽非新义务）+ SKILL.md 数据模型速查补双形态注记 | evidence_ledger.py:436-437、SKILL.md 数据模型速查 |
| D-2 | verifier "sink 可达≠缺陷可达"区分缺失——引擎/库型目标公共 API 恒可达, 24/30 证伪分歧票集中于"无具体缺陷断言"（V8 实录） | _build_prompt 步骤 0 块增提示级一句: 库型目标下 API 可达性只解决"面存在", claim 声明前必须给出具体缺陷机制的静态证据, 否则 claim_type=other 并在 evidence 写明 | tools/batch_verify.py `_build_prompt` 步骤 0 块 |
| D-3 | claim=other 豁免实证成为实质机制候选的庇护——CAND-013/049 静态机制已双证伪确证但 claim=other 无实证义务, 用户挑战后实证升格 empirically_confirmed（V8 实录） | SKILL.md R3.5-N/R5 条款（提示级）: 复活波抽样与实证裁决时, claim=other 但"机制静态确证"信号（0 票证伪+证伪者补强）的候选优先纳入实证池 | SKILL.md R3.5-N/R5 节 |
| D-4 | 实证证伪降级到 UNREACHABLE 后缺 resurrection_review 簿记——六门禁复跑 FAIL（gate ③c）暴露契约, 补记后 PASS（V8 实录） | SKILL.md R5 实证证伪条款 + 数据模型速查明示: 主代理实证降级 UNREACHABLE 必须同步写候选级 resurrection_review {revived:false, outcome}（机制已存在, 只补契约明示） | SKILL.md R5/数据模型速查 |
| D-5 | ASan 变体与 dcheck 构建的实证冲突——dcheck_always_on 的 DEBUG 层不变量前置拦截畸形输入, ASan 精确定位被阻（V8 CAND-049 实录） | ENVIRONMENT_PROBES.md 新增条目: sanitizer 实证需 dcheck 关闭变体（is_asan + dcheck_always_on=false）; DEBUG 不变量是实证输入的前置拦截器 | harness_manuals/ENVIRONMENT_PROBES.md |
| D-6 | 构建配置前提类候选实证前未枚举配置矩阵——CAND-013 的 OOB 写仅在无指针压缩变体物化, 默认构建同输入为 OOM 路径（V8 实录） | resurrect_prompt 复活维度新增第 9 条（提示级）: 构建配置前提（指针压缩/sandbox/特性开关/GC 模式）逐项枚举——默认构建可能把内存破坏路径变成 OOM/拒绝路径, 实证必须按配置矩阵选载体 | workflow_export.py resurrect_prompt（:479 维度 8 之后） |

## 版本链 v3.19

- workflow_export.py:22 TOOLING_VERSION → "3.19"
- SKILL.md v3.19 增量段
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、
  test_v39.py:266、test_v314.py:219、test_v315.py:253、test_v316.py:120、
  test_v317.py:347、test_v318.py:132 → "3.19"（实测行号 P4 逐处核对）
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
  gen_tracking VERSIONS 登记

## 开发序列

- **C0**（本文档集）
- **P1 机械**：D-1（lenient + 测试守卫）
- **P3 内容**：D-2（步骤 0 措辞）+ D-5（ENVIRONMENT_PROBES 条目）+
  D-6（resurrect 第 9 维）
- **P4 文档+版本链**：D-3/D-4（SKILL.md 条款）+ TOOLING/守卫/tracking/test_v319

## 测试守卫约束

- 必须保持绿：全量 400 基线、test_evidence_ledger.py（门禁名不增）、
  test_doc_lint.py（资产计数零变化——本轮不新增计数资产）
- 新增 tests/test_v319.py（约 8 用例）：D-1 str 条目 lenient（混形态队列零崩溃 +
  dict 条目检查保留）/D-2 步骤 0 措辞存在/D-5 探针条目存在/D-6 复活第 9 维存在/
  D-3/D-4 SKILL.md 条款存在/TOOLING 3.19/反面分支（lenient 不改写任何字段）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 signature_lib.py selfcheck /root/v8
bash install.sh
```

## 边界声明

- **不做**：新门禁/新强制义务/新阶段/自动改写；L4 不重造机制（只明示契约）；
  L3 提示级不设强制优先级。
- **案例支撑来源**：/root/v8/.audit_results/lessons.md 六条目（会话内实录,
  编辑点行号取证核实）。审计自身教训（harness 编译链/对照组方法论/checksum
  校准）无明确运行时消费者——按义务三问不入运行时资产, 留项目 lessons。
