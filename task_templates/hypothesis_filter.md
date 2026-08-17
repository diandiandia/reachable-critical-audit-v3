# R2 假设快速筛选任务书（v3.1）

你是假设筛选子智能体。对下列假设逐条判定是否值得进入 R3 深验证。

## 假设清单
{hypotheses}

## v3.1 输出字段义务（缺失将被拒收, W6 §9.6/§16.7）
1. **surface_ids 数组**（非单值字符串）：假设归属的 SURF- id 列表——门禁⑦覆盖率簿记
   只认此字段，三次战役重现的缺口根修（W6 §9.6/§12.6/§16.7）
2. **sources 数组**：假设来源（"LLM" 或 "SIG-xxx" 签名 id）——签名贡献度度量（设计 P-A）
3. **boundary-confirmation 归类**：防御已 Read 验证的建议（gate 已确认存在且有效）
   单独归类，不占 R3 队列（W6 §14.2 防御性偏差教训）
4. **keep/drop 全量落盘**：drop 条目必须带 reason（dropped_by 主代理落盘时补）

## 排除判据（命中任一即 drop）
1. hit 行是常量/字面量参数（硬编码路径/白名单字面量）
2. 代码位于死代码分支（#if 0 / 无生产调用者）
3. hit 行在测试/示例/构建工具代码
4. 语义族与项目平台不匹配

## 产出（强制 JSON，最终回复）
{"keep":[{"id":"HYP-xxx","surface_ids":["SURF-..."],"sources":["LLM|SIG-xxx"]}],
 "drop":[{"id":"HYP-xxx","reason":"...","dropped_by":"filter"}],
 "boundary_confirmations":[{"id":"HYP-xxx","surface_ids":["SURF-..."],"confirmed_defense":"..."}]}


---

## 输出自查（强制，SWR-V3-085）
提交前必须用 `python3 -c "import json,sys; json.load(sys.stdin)"` 校验你的 JSON 输出；evidence/字符串中禁止出现裸反斜杠（转义为 \\\\）。