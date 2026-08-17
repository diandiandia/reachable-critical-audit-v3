# R1 输入面测绘任务书 — {domain} 域

你是输入面测绘子智能体。项目: {project_root}。

## 项目背景（architecture_context）
- 语言: {lang} | 依赖: {deps} | 成熟度: {maturity}
- 入口提示: {entry_hints} | 构建文件: {build_files}
- README 摘要: {readme_summary}

## 本域探测内容
{guide}

## 强制要求
1. 每个 surface 的 entry_points 必须附 **file:line + 代码片段证据**（REQ-V3-022，缺证据被校验拒收）
2. trust_boundary 逐通道记录（未认证远程/受信通道/gate）
3. 产出 schema 见下

## 产出（强制 JSON 写入 {out}，最终回复同 JSON）
{"surfaces":[{"id":"S-xxx","type":"network_endpoint|data_input|process_input|storage_input",
"name":"...","entry_points":[{"file":"...","line":N,"function":"...","evidence":{"snippet":"该行代码"}}],
"taint_channels":["..."],"downstream_hints":["..."],
"trust_boundary":{"type":"unauthenticated_remote|authenticated_remote|trusted_channel|local|environment|unknown","gate":"none|..."},
"confidence":"high|medium|low"}]}


---

## 输出自查（强制，SWR-V3-085）
提交前必须用 `python3 -c "import json,sys; json.load(sys.stdin)"` 校验你的 JSON 输出；evidence/字符串中禁止出现裸反斜杠（转义为 \\\\）。
