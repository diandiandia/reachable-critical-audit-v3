# R2 假设快速筛选任务书（v3.1）

你是假设筛选子智能体。对下列假设逐条判定是否值得进入 R3 深验证。

## 假设清单
{hypotheses}

## v3.1 输出字段义务（缺失将被拒收, W6 §9.6/§16.7）
1. **surface_ids 数组**（非单值字符串）：假设归属的 SURF- id 列表——门禁⑦覆盖率簿记
   只认此字段，三次战役重现的缺口根修（W6 §9.6/§12.6/§16.7）
2. **sources 数组**：假设来源（"LLM" 或 "SIG-xxx" 签名 id）——签名贡献度度量（设计 P-A）
3. **boundary-confirmation 归类**：防御已 Read 验证的建议（gate 已确认存在且有效）
   单独归类，不占 R3 队列（W6 §14.2 防御性偏差教训）。**bc/『防御已到位』类裁决
   必须核查默认权限上下文**（文件/目录/umask/监听 socket 权限、环境变量默认值、
   启动命令注入点）并引用源码证据行（file:line）——只看 gate 存在性不算核查
   （v3.6 实录: 默认 token 随机 + 权限上下文使防御失效, R4 实证推翻 R2 误 drop）
4. **keep/drop 全量落盘**：drop 条目必须带 reason（dropped_by 主代理落盘时补）

## 排除判据（命中任一即 drop）
1. hit 行是常量/字面量参数（硬编码路径/白名单字面量）
2. 代码位于死代码分支（#if 0 / 无生产调用者）
3. hit 行在测试/示例/构建工具代码
4. 语义族与项目平台不匹配
5. **『防御已到位』**（gate 默认开启/默认 token 随机/默认白名单等）——drop 前必须
   完成上款默认权限上下文核查（文件/目录/umask/监听 socket 权限、环境变量默认值、
   启动命令注入点）并引用源码证据行；未引用证据行的 bc/drop 条目主代理拒收补查

## 平台信任模型对照（v3.10.2, SWR-V3.10.2-016）
「语义族与项目平台不匹配」与「防御已到位」裁决前，若目标含平台组件（移动/桌面/
web/嵌入内核），须对照 checklist_library 的 platform_trust_models 清单中对应平台
条目——同设备其他应用经导出组件/意图参数注入是异主体（不得以『单信任域』泛化
同主体 drop）；平台鉴权中介（系统服务绑定+用户授权）存在时『未认证通道』判据
不成立。主代理在任务书注入实际平台信号与清单条目；未注入时按通用判据执行。

## scope_dependent 标记（v3.2.2, REQ-V3.2.2-019）
drop 理由属于"目标代码在审计范围内不可见"类（子模块未物化/树外实现/依赖缺失）时
必须 `scope_dependent: true`——该 drop 是 scope 快照的函数; scope 变更时（入队前
scope diff）这类 drop 自动提示复活重验（C 库审计实战形态: 子模块中途物化
使"树外不可验证"drop 作废）。其余 drop 为 false。

## focus_sink 格式契约（v3.10, SWR-V3.10-010）
keep 条目的 focus_sink 必须是**纯 `path:line`**（相对项目根路径）——如
`fs/namei.c:4404`。说明性文字一律放 note 字段。**反例**（禁止）：
`fs/namei.c:4404 (lookup_open)`。主代理簇化入队直接按 `path:line` 解析，
带后缀格式会导致入队失败。

## 产出（强制 JSON，最终回复）
{"keep":[{"id":"HYP-xxx","surface_ids":["SURF-..."],"sources":["LLM|SIG-xxx"],"focus_sink":"path:line","note":"核实结论"}],
 "drop":[{"id":"HYP-xxx","surface_ids":["SURF-..."],"reason":"...","dropped_by":"filter",
          "scope_dependent":false|true}],
 "boundary_confirmations":[{"id":"HYP-xxx","surface_ids":["SURF-..."],"confirmed_defense":"..."}]}

## surface_ids 保真义务（v3.4.6, SWR-V3.4.6-002, 缺失即拒收）
**keep / drop / boundary_confirmations 三组条目的 `surface_ids` 均必填数组**
（从假设清单继承, 原样保留, 不得省略）。门禁⑦ tracked 覆盖簿记只认
surface_ids; drop/boundary_confirmations 省略该字段 → 覆盖计数虚低 →
假缺口阻断收尾（成熟网络库 41→31 实录）。

## 落盘拦截契约（v3.2.3 强制）
若环境（权限/plan mode）阻止写入指定的落盘路径：最终回复**必须**是完整
JSON 且末尾附一行 `UNWRITTEN: <原因>` 标注；禁止只写"已保存"而实际未落盘。
主代理会从最终回复完整恢复（写 recovered_by 字段）。


---

## 输出自查（强制，SWR-V3-085）
提交前必须用 `python3 -c "import json,sys; json.load(sys.stdin)"` 校验你的 JSON 输出；evidence/字符串中禁止出现裸反斜杠（转义为 \\\\）。