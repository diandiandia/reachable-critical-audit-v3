# v3.6 系统设计：评估驱动机制修复 + 内容补全（无设计膨胀）

> 日期：2026-08-23。评估报告：`docs/history/AUDIT_EVAL_V3_5_2.md`（puma v8.0.1 在线项目实战验收）。
> 范围（用户三约束）：**保持通用性 / 不携带审计历史信息（项目名）/ 不出现无用设计**。
> 用户两项裁决：① 8 语言 harness 模板 → **裁减 + 提炼 1 个通用协议级模板**；
> ② REQUIREMENTS_TRACKING 只回填新近 6 条（REQ-V3.1-100/101 + SWR-V3.4.6-001~004，
> 历史 119 条不动）。
> 基线：HEAD `5aad6b6`（v3.5.2），193 测试全绿。

## 1. 背景与动机

puma v8.0.1 实战验收暴露两处机制缺口 + 一处对称性不一致 + 一处账本时序缺口；
v3.5.2 确认「留 v3.6」的内容补全类 5 项中 1 项（锚点 swift）已被 v3.5 覆盖
（SWR-V3.5-011）。本版本以「评估驱动修复 + 用户裁决补全」双轨推进，全程受
第一原则三约束约束。

## 2. P1 机制修复（评估驱动）

### 2.1 B9 清单注入时点错位（puma §2.1 实录）

**现象**：R3.5 证伪者任务书从未收到家族检查清单段（CK-EMPIRICAL-SCOPE 等），
预分配类候选在无清单语境下被证伪者以「对齐必然恢复」类论据误杀。

**根因**（三路探查确认）：
- verify 导出时候选全部 PENDING，cwe/claim_type 由 collect 阶段才落盘
  （batch_verify.py:423-433）→ `_in_r5_semantic_space` 恒 False → 清单绑定恒空；
- refutation 分支被 `if mode == "verify"` 守卫排除，从不注入清单。

**修法（方案 a，与 AUDIT_EVAL_V3_5_2.md 建议一致）**：refutation payload 组装时
对每候选两个证伪者 prompt 追加 `_checklist_section(c)`——该时点 cwe/claim_type
已落盘，r5-semantic 判定可用。小助手 `_refutation_checklist_section` 包装，
不改 `refute_prompt` 本体（直调它的单测不受影响）。

**不修（裁决记录 R1）**：
- **resurrect 分支不加代码**：复活者语境是找 UNREACHABLE 缺口，非实证范围分级
  消费语境——注入清单是设计错位，无消费者。
- **Mode A' 不加代码**：手工循环下主代理直接编排，注入点在主代理侧语境中，成本
  大于收益。

### 2.2 R2「防御已到位」drop 缺默认权限上下文核查（puma HYP-005/006 误 drop 实录）

**现象**：R2 筛选将「防御已到位」类假设 drop——但 puma 实录中默认 token 随机
+ 文件权限上下文使防御实际失效，R4 实证推翻 R2 误 drop。gate 存在 ≠ 防御有效。

**修法**：`task_templates/hypothesis_filter.md` 两处——bc 归类条款句末追加
默认权限上下文核查义务（文件/目录/umask/监听 socket 权限、环境变量默认值、
启动命令注入点）+ 引用源码证据行（file:line）；排除判据补第 5 条，未引用
证据行的 bc/drop 条目主代理拒收补查。SKILL.md:132 R2 筛选句措辞对齐。

**不修（裁决记录 R2）**：不做 r2_guard 机械 warn——「防御已到位」判定依赖
语义理解，机械检测误报率高于收益；义务走任务书契约（主代理拒收）而非新机制。

### 2.3 EMPIRICAL_CLAIMS 对称缺口

**现象**：`harness_runner.py:20` 与 `evidence_ledger.py:20` 的 6 类旧集
（crash/panic/oom/unbounded/xss/protocol_dos）缺 rce/leak——这两类声称能绑定
家族清单（binder R5_CLAIM_TYPES 8 类）却不触发强制实证（needs_harness False、
gate ③ 不拦）——绑定与实证不对称。

**修法**：两处 6 类 → 8 类（补 rce/leak），对齐 SKILL.md:217 的 claim_type 枚举。
needs_harness 与 gate ③/③b/③c 语义自然延伸，零新机制。

**已核查不扩（裁决记录 R3）**：`workflow_export.py:38` 的 6 类集仅服务 resurrect
抽样池语义（声称类 UNREACHABLE 复活抽样），**有意保留**——扩为 8 类会改变复活
抽样率，无评估驱动。记入 SWR_V3_6 防下轮误判。

### 2.4 账本回填机械前置（puma 实录：先回填后补标 cwe 致缺口不可回写）

**现象**：puma 审计在 r4-assert PASS 前执行 `--stage coverage-ledger --write`
回填账本——sources key 被烧，后续 cwe 修正（含 r4_feedback 裁决）无法再写入，
INJECTION×ruby 缺口格错过闭合。

**修法**（`tools/batch_verify.py` stage_coverage_ledger write 分支重排）：
1. 幂等检查（key 在 sources → `LEDGER_IDEMPOTENT_SKIP` + 附打印
   `would_be_new_counts`——聚合只算不写）；
2. 前置 (a)：r4_findings 全 VERIFIED（提取 `_r4_missing`，与 stage_r4_assert
   共用同一判定，:933-942 改调用）——缺 → `LEDGER_WRITE_BLOCKED_R4` + 缺什么，
   exit 1，**不烧 key**；
3. 前置 (b)：`evidence_ledger.r4_feedback` 无未决冲突（conflicts 非空）→
   `LEDGER_WRITE_BLOCKED_FEEDBACK`，exit 1，不烧 key；
4. 全过 → 提取 `_aggregate_counts`（:1154-1174 原聚合逻辑零行为变化）写账本。

SKILL.md R6 节追加回填时序条款：cwe 修正（含 r4_feedback 裁决）→ r4-assert
PASS → 六门禁 → `--write`；:151 句尾交叉引用（v3.6 起强制）。

**不修（裁决记录 R4）**：不做 `--force`、不改数据模型——幂等 sources 防重复
记账是有意设计；时序前置使 force 无必要；历史缺口由下批选题（账本缺口格优先）
自然闭合。

## 3. P2 内容补全（v3.5.2 遗留 + 用户裁决）

### 3.1 L2 词族 5 语言（signature_library 20→25）

SIG-RB-EVAL-001（ruby，CWE-78）/ SIG-PHP-EVAL-001（php，CWE-78/95）/
SIG-PERL-EXEC-001（perl，CWE-78）/ SIG-SCALA-UNSAFE-001（scala，CWE-78）/
SIG-SWIFT-UNSAFE-001（swift，CWE-78）——纯通用语言 API grep 词，lang/cwe 必填，
`_deproject_scan` 零命中。新签名无真实审计锚点 → tests/fixtures/known_instances.json
补 5 条 `confirmed:false` 占位（project:"(pending)"，诚实簿记——不伪造 confirmed，
不参与 anchor recall 回放池）。测试：`test_all_signatures_have_confirmed_fixture`
改双向严格覆盖（每签名有代表 + 无孤儿 + 占位显式标注）；新增
`test_v36_new_l2_families_valid` id 级形状锁。

### 3.2 env 陷阱 9 语言（harness_runner PER_LANG_ENV_TRAPS 7→16）

per_lang 提为模块级 `PER_LANG_ENV_TRAPS`，补 cpp/cs/typescript/kotlin/scala/
perl/php/powershell/shell 至 16 语言（对齐 harness_manuals/ 文件名；js 归属
typescript 手册）。条目为通用环境陷阱形态（工具链版本互斥/网络依赖/运行时
语义），每条源自对应语言手册陷阱节提炼，零项目名。测试：
`test_env_traps_covers_16_langs`（双向对齐手册清单）+ `test_env_traps_each_lang_has_items`
（非空 + 去项目化）。

### 3.3 L3 语义族脚本 token 补全

5 个 L3 签名 grep 追加脚本语言形态：BUFFER-ACCUM 补 `.=`/push(/concat(/
`$arr[]`/`<<`/`>>`；PREALLOC-LEN 补 bytearray(/array_fill(/str_repeat(；
TRUNC-CAST 补 intval(/`|0`/ord(；STATE-RACE 补 file_exists(/File.exist?/
fs.existsSync/test -e；CRYPTO-WEAK 补 mt_rand(/Digest::MD5/Math.random/`$RANDOM`。
JSON 正则串形态落盘（测试断言可直接 re.compile）。粗粒度 hint 属佐证器设计
（非判定器）——误报代价低于漏报，SWR_V3_6 注明。测试：`test_v36_l3_script_tokens_present`
（只锁 v3.6 新增 token，不锁全表）。

### 3.4 通用实证模板 resource_rate_probe（用户裁决 ①）

**裁决背景**：8 语言专属模板（原计划逐语言定制）→ 用户选择「裁减 + 提炼 1 个
通用协议级模板」。设计依据（义务入库三问）：触发条件——protocol_dos/unbounded/
oom 声称实证（跨语言共性最强的一类）；消费者——R5 阶段主代理按声称类选型 +
TEMPLATES 注册表；裁掉丢什么——丢失语言专属仪式（各语言手动翻版），保留协议
级通用语义（灌注 + 采样 + 拒绝计数 + delivery-rate + 回落 + 单调性）。

**实现**：`templates/harness/resource_rate_probe.py`——python3 标准库零依赖，
argv 必传 host/port（零项目名零 /root/）；并发连接灌注 + 逐秒 VmRSS 采样 +
拒绝计数 + delivery-rate 确认（客户端口径 + 拒绝信号双报，主代理裁决）+
停止后回落验证（回落量 ≥ 灌注期涨量 50% → 有界释放）+ 单调性判定（只看
灌注期子序列）+ JSON 汇总（verdict 供主代理裁决，不自动改判）。注册
TEMPLATES `langs:["any"]`（已核实无机械消费者，主代理选型用）。

## 4. P3 文档 + tracking + 版本

- REQUIREMENTS_TRACKING 回填 6 条（:212-213、:715-718）→ 已完成，备注列引用
  实现/测试证据（ACCEPTANCE_V3_1.md:62 / batch_verify.py:184 / r2_guard.py:13 /
  surface_mapper.py:796 / SKILL.md:134-137）。
- 版本链：本文件 + SWR_V3_6.md 双件套；SKILL.md 新增 v3.6 增量段；「留 v3.6」
  行更新为已处理（锚点 swift 标 v3.5 已覆盖）；TOOLING_VERSION "3.5.2" → "3.6"
  （test_v344 动态引用，安全）；README 漂移修复（task_templates ×7→×3、
  templates ×3→×5 补 parser_fuzz/resource_rate_probe、签名 20→25）。
- HEALTHCHECK_EVAL_V3_5.md 未修清单 5 条逐条标 v3.6 处理结果。

## 5. P4 验收

1. pytest 全绿（193 基线 + ~11 新增 = 204）
2. `signature_lib.py selfcheck /root/phpseclib` exit 0（25 签名 validate +
   L2↔手册对齐 + 去项目化 0 命中 + grep 全编译）
3. `./install.sh` → DST pytest 全绿
4. 按 P1→P2→P3→P4 分阶段 commit（每组全绿）
5. 新在线项目实战验收（覆盖账本缺口格选题）本版本止于 install 回归，另行启动

## 6. 关键风险

- **R1**：3 个既有账本测试 fixture 缺 r4_findings → 前置 (a) 阻断 --write →
  同 commit 补 H1-H7 VERIFIED（已做）。
- **R2**：test_all_signatures_have_confirmed_fixture 对 5 新签名必红 → 改双向
  严格覆盖（已做）。
- **R3**：test_asset_counts_current 从磁盘实算 → P2 增资产同 commit 同步
  SKILL.md/README（已做）。
- **R4**：去项目化三道闸——新签名 grep/semantic 过 `_deproject_scan`（零命中，
  已验证）；resource_rate_probe.py 过 templates/ 全扫（零项目名零 /root/，
  测试断言）；bc 措辞过 task_templates 扫描（puma 出处仅存在于追溯字段）。
- **R5**：幂等检查先于前置（旧项目重跑安全）；前置只拦新回填。
- **R6（观察不修）**：cs.md/cpp.md 手册陷阱节头与 load_manual 解析头不一致，
  记 SWR_V3_6 下轮候选。
