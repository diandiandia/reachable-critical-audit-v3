# SWR_V3_46 — v3.46 规格（每条修复一条 SWR，含裁决理由 + 测试守卫）

## SWR-V3.46-001 (D-1) attacker_tier 句级否定清洗

- **修复**：`_derive_attacker_tier` 关键词匹配前先按句切分；含免责标记
  （"非/不是/不构成/无/untrusted 前缀否定/not/never/no …remote 形态"）的句子
  不参与关键词计数。全部证据句均为免责句式时返回 `None` + warn 文本
  （主代理裁决 tier，不自动落默认值）。
- **裁决理由**：不自动改写（纪律 #4）——免责句可能是"澄清后仍 remote"（如
  "非本地，而是远程"），自动剔除会产生另一方向误标；None 显式化比静默
  fallback 可审计。
- **测试守卫**：免责句 / 混合句（正向+免责）/ 纯正向句三形态 + K6/K7 样本
  fixture 断言；None 路径断言 warn 输出。

## SWR-V3.46-002 (D-2) r4 schema 归一扩展 + 模板钉死 canonical 键

- **修复**：`_normalize_r4_payload` 扩展三形态——`id`→`hypothesis_id`、
  前缀键 `hypothesis_tracked_surfaces`→`tracked_surfaces`、`hypothesis`
  描述文本键（含内嵌 H-N 提取）→`hypothesis_id`+`hypothesis_note`；每次命中
  记 `norm_flags`（collect 时输出 warn 计数）。**裸 id 形态
  （`{"hypothesis": "H1"}` 且无 hypothesis_id）不归一**——该形态由既有
  v3.42 近似键诊断契约拥有（R4_COLLECT_WARNING, 不自动改写），v3.46 只处理
  描述文本干扰。`biz_hypothesis.md` 的 canonical 示例键名加粗标注
  "键名必须逐字一致（id/hypothesis_tracked_surfaces 等别名不接受）"。
- **裁决理由**：归一器是防线（schema 漂移已连续 2 批扩散）；模板钉死是从源头
  降漂移率。别名映射是建议映射级——改键不丢字段、附 warn 可追责，不违反
  不自动改写（键名归一 ≠ 内容改写）；裸 id 形态让位既有诊断契约（实现期
  全量回归实测：v3.42/v3.45 两测试捕获该冲突后收紧）。
- **测试守卫**：K8/K9 漂移形态 fixture → 输出键名全 canonical + norm_flags
  计数正确；裸 id 形态零改动反面分支；模板文本断言含 canonical 键说明。

## SWR-V3.46-003 (D-3) workflow 导出 taskFile 预检 + r4-collect 多文件显式报错

- **修复**：`workflow_export.py` 生成的 JS 在启动时对 payload 每个
  `taskFile` 路径做 `fs.existsSync` 预检，缺失即立即失败并列出全部缺失路径
  （不等 agent 入场）；`batch_verify.py` 参数解析检测重复 `--file`（覆盖形态）
  显式报错并列出两个路径。
- **裁决理由**：JS 侧预检是机械事实（存在性），非语义裁决——不属于自动改写
  范畴；快速失败省一整波 token（K9 refutation 一票拒绝实录）。
- **测试守卫**：缺文件 payload → 导出 JS 文本含 existsSync 预检段；解析器
  重复 --file 报错分支测试。

## SWR-V3.46-004 (D-4) surface_map 任务书 config 门核条款

- **修复**：`surface_map_domain.md` 新增条款：写 `trust_boundary: local` 前必须
  核对 config 编译面（Kconfig/feature 开关/构建清单默认值）——被 config 门控
  或默认关闭的通道不得写 local，应写 `gated` 或 `unknown` 并附 config 证据行。
- **裁决理由**：提示级条款（任务书义务），无新门禁；案例：K6 HID 35/40 面
  前提被 R3 推翻、K8 计划前提被 R1 实测证伪——两面均为 config 面前提失实。
- **测试守卫**：模板文本含条款断言（doc lint 风格）。

## SWR-V3.46-005 (D-5) 零硬件实证通道手册入库

- **修复**：新文件 `assets/harness_manuals/kernel_zero_hardware_channels.md`，
  收录四条通道的通用化描述：纯软件 USB 控制器通道（dummy 类驱动 + 存储
  栈挂载链）、远程协议模拟控制器（内核侧模拟 driver 绑定真实协议栈）、
  RPC responder（服务端实现嵌入用户态探针，客户端栈真实）、共享内存/字符
  设备环回通道。每条含适用面、观测方法（RSS/存活/exit code/dmesg）、陷阱
  注记（finit_module ENOEXEC → 需与内核同工具链编译；版本对账）。
- **裁决理由**：回收 SWR-V3.38-005 条款欠账；去项目化（零项目名），来源
  注记到 lessons 条目。
- **测试守卫**：deproject 扫描零命中；文件存在 + 四条通道标题断言。

## SWR-V3.46-006 (D-6) 版本滞后告警文案补全

- **修复**：`_tooling_version_warning` 告警文案追加一句："仅提示不阻断——
  重跑 `--stage workflow-script` 重新导出后可安全运行（旧 JS 判据可能落后
  当前版本）"。
- **裁决理由**：文案级，消除"告警=必须处理"的歧义（K6 #11）。
- **测试守卫**：单测断言告警文本含新句子。

## SWR-V3.46-007 (D-7) resurrect 导出器抽样规则注释澄清

- **修复**：`workflow_export.py` eligible 挑选处（UNREACHABLE-only）加注释：
  REQ-V3.2-021 的 20% NEEDS_REVIEW 抽样不在导出器自动范围内，由主代理
  手工 payload 完成；抽样决策落盘 `_resurrect_sample.json`。
- **裁决理由**：工具能力与需求文档一致性澄清，零行为变更（需求原文是
  抽样决策由主代理落盘——导出器无此职责）。
- **测试守卫**：无行为变更，仅注释；随行断言可省（注释非可测行为，
  REQ 表已记录）。
