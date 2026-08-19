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
"name":"...","lang":"该面代码语言 (c/cpp/go/rust/java/python/ruby/...; 从架构上下文继承, 必填)",
"entry_points":[{"file":"...","line":N,"function":"...","evidence":{"snippet":"该行代码"}}],
"taint_channels":["..."],"downstream_hints":["..."],
"trust_boundary":{"type":"unauthenticated_remote|authenticated_remote|trusted_channel|host_api|local|environment|unknown","gate":"none|..."},
"confidence":"high|medium|low"}]}

## 非网络/离线项目映射指引（v3.3 强制，REQ-V3.3-009）
本项目若无网络服务面，按以下映射归类，**不得**把宿主 API 输入过度归为 local/environment：
- **库/解析引擎类**：宿主应用通过公共 API 喂入的不可信数据（脚本文本/字节码/二进制块/字符串）
  → **data_input**，trust_boundary 用 **host_api**（宿主 API 即信任边界）
- **数据处理库/协议栈类**：文件/持久化入口 → storage_input；进程控制/命令执行 → process_input
- **无 socket 代码时**：network 域写 `empty_domain_reason` 说明（合法产出，非缺漏）
- host_api 语义：数据经宿主对本库公共 API 的调用进入——跨库边界 ≠ 跨主体边界

## 落盘拦截契约（v3.2.3 强制）
若环境（权限/plan mode）阻止写入 {out}：最终回复**必须**是完整 JSON 且
末尾附一行 `UNWRITTEN: <原因>` 标注；禁止只写"已保存"而实际未落盘。
主代理会从最终回复完整恢复（写 recovered_by 字段）。

---

## 输出自查（强制，SWR-V3-085）
提交前必须用 `python3 -c "import json,sys; json.load(sys.stdin)"` 校验你的 JSON 输出；evidence/字符串中禁止出现裸反斜杠（转义为 \\\\）。
