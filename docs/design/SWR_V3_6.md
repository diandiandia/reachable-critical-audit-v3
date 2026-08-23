# SWR-V3.6 修复记录（评估驱动机制修复 + 内容补全，无设计膨胀）

> 设计: SYSTEM_DESIGN_V3_6.md。来源: AUDIT_EVAL_V3_5_2.md（puma 实战验收）+ v3.5.2 遗留内容补全。
> 版本链: 本文件 + SKILL.md「🆕 v3.6 增量」段 + TOOLING_VERSION "3.6"。
> 基线: `5aad6b6`（v3.5.2），193 测试 → 204（+11）。

---

## 一、P1 机制修复

### 1.1 B9 清单注入时点修复（workflow_export.py refutation 分支）

- `export_script` refutation payload 组装新增小助手 `_refutation_checklist_section(c)`：
  非空清单段以 `"\n\n"` 前缀追加到两个证伪者 prompt（复用 `_checklist_section`，
  refutation 时点 cwe/claim_type 已由 collect 落盘 → `_in_r5_semantic_space`
  可判定 → CK-EMPIRICAL-SCOPE 以 r5-semantic 绑定）
- `refute_prompt` 本体不动（test_refutation_prompt_truncation_marker 直调它）
- 测试: `test_refutation_payload_includes_checklist_section`（双 prompts 含
  「家族检查清单」+「CK-EMPIRICAL-SCOPE」）、`test_resurrect_prompt_no_checklist`
  （负向防回退: resurrect 分支不注入）

### 1.2 R2「防御已到位」默认权限上下文核查义务（hypothesis_filter.md）

- bc 归类条款句末追加: 「**bc/『防御已到位』类裁决必须核查默认权限上下文**
  （文件/目录/umask/监听 socket 权限、环境变量默认值、启动命令注入点）并引用
  源码证据行（file:line）——只看 gate 存在性不算核查（v3.6 实录: 默认 token
  随机 + 权限上下文使防御失效, R4 实证推翻 R2 误 drop）」
- 排除判据补第 5 条: 「**『防御已到位』**（gate 默认开启/默认 token 随机/默认
  白名单等）——drop 前必须完成上款默认权限上下文核查并引用源码证据行；未引用
  证据行的 bc/drop 条目主代理拒收补查」
- SKILL.md:132 R2 筛选句追加权限上下文核查义务（措辞对齐）
- 测试: test_doc_lint 既有 bc 措辞防回退断言覆盖（模板文本变化经 task_templates
  全扫路径）；无新增机械 warn（裁决记录 R2）

### 1.3 EMPIRICAL_CLAIMS 8 类对称（harness_runner.py + evidence_ledger.py）

- 两处 `EMPIRICAL_CLAIMS` 6 类 → 8 类（补 rce/leak），对齐 binder R5_CLAIM_TYPES
  与 SKILL.md claim_type 枚举（crash/panic/oom/unbounded/xss/protocol_dos/rce/leak）
- 测试: `test_needs_harness_rce_leak_trigger`（rce/leak edge_proven/static_only →
  True；empirically_confirmed → False）、`test_gate3_rce_leak_claims_enforced`
  （rce/leak 声称 REACHABLE 无实证 → violations 含 empirical_required）

### 1.4 账本回填机械前置（tools/batch_verify.py coverage-ledger）

- 提取 `_r4_missing(queue)`（= stage_r4_assert :936-941 判定，:933-942 改调用）
  与 `_aggregate_counts(queue, project_root)`（模块级，原 :1154-1174 聚合逻辑
  零行为变化）
- write 分支重排: 幂等检查（key 在 sources → `LEDGER_IDEMPOTENT_SKIP` +
  `would_be_new_counts` 只算不写）→ 前置 (a) `_r4_missing` 非空 →
  `LEDGER_WRITE_BLOCKED_R4` exit 1 不烧 key → 前置 (b)
  `evidence_ledger.r4_feedback(queue)` 冲突非空 → `LEDGER_WRITE_BLOCKED_FEEDBACK`
  exit 1 不烧 key → 聚合写账本
- SKILL.md R6 节（:464-481）追加回填时序条款（cwe 修正 → r4-assert PASS →
  六门禁 → --write）+ puma 实录；:151 句尾交叉引用（v3.6 起强制）
- 测试: 3 既有账本测试 fixture 补 H1-H7 VERIFIED（`_run_ledger_tests` /
  empty_queue_lang_from_surface / derivation_chain）+ 新增
  `test_coverage_ledger_write_blocked_r4`（缺 H-7 → returncode 1 + 缺什么 +
  账本字节级不变）、`test_coverage_ledger_write_blocked_feedback`（H-7
  default_value_table true vs REACHABLE evidence 声称默认明文 → conflicts 非空
  阻断 + 账本不变）、幂等分支 would_be_new_counts 断言并入 `_run_ledger_tests`

## 二、P2 内容补全

### 2.1 L2 词族 5 语言（signature_library 20→25）

- 新增: SIG-RB-EVAL-001（ruby, CWE-78, eval/system/Open3/%x）/ SIG-PHP-EVAL-001
  （php, CWE-78/95, eval/shell_exec/passthru/call_user_func/assert/unserialize）/
  SIG-PERL-EXEC-001（perl, CWE-78, eval 字符串/system/qx/管道 open/IPC::Open3）/
  SIG-SCALA-UNSAFE-001（scala, CWE-78, Runtime.exec/ProcessBuilder/sys.process/.!!）/
  SIG-SWIFT-UNSAFE-001（swift, CWE-78, Process/NSTask/posix_spawn/system/execve）
- fixtures 补 5 条 `confirmed:false` 占位（project:"(pending)"）——不参与 anchor
  recall 回放池（回放循环 `continue`），只作诚实簿记
- 测试: `test_all_signatures_have_confirmed_fixture` 改双向严格覆盖（每签名有
  代表 + 无孤儿 + 占位显式 `(pending)` 标注）；新增 `test_v36_new_l2_families_valid`
  （id 级形状锁: lang/cwe/去项目化零命中/grep 可编译/占位形态）

### 2.2 env 陷阱 9 语言（harness_runner PER_LANG_ENV_TRAPS 7→16）

- per_lang 提为模块级 `PER_LANG_ENV_TRAPS`，补 cpp/cs/typescript/kotlin/scala/
  perl/php/powershell/shell（js 归属 typescript 手册；键名 = harness_manuals/
  文件名 = load_manual 解析契约）
- 条目通用形态（工具链版本互斥/网络依赖/运行时语义），源自各语言手册陷阱节
- 测试: `test_env_traps_covers_16_langs`（双向对齐，排除 mixed_build/
  ENVIRONMENT_PROBES）、`test_env_traps_each_lang_has_items`（非空 + 零项目名）

### 2.3 L3 语义族脚本 token（5 个 L3 签名 grep 追加）

- BUFFER-ACCUM: `.=`/`push(`/`concat(`/`$[A-Za-z_]+[]`/`<<`/`>>`
- PREALLOC-LEN: `bytearray(`/`array_fill(`/`str_repeat(`
- TRUNC-CAST: `intval(`/`|\s*0\b`/`ord(`
- STATE-RACE: `file_exists(`/`File.exist?`/`fs.existsSync`/`test -e`
- CRYPTO-WEAK: `mt_rand(`/`Digest::MD5`/`Math.random`/`$RANDOM`/`md5(`/`sha1(`
- 注: 粗粒度 hint 属佐证器设计（非判定器）——误报代价低于漏报；L3 grep 继续
  演化，测试只锁 v3.6 新增 token（`test_v36_l3_script_tokens_present`）

### 2.4 通用实证模板 resource_rate_probe（用户裁决: 裁减 + 提炼 1 个通用模板）

- `templates/harness/resource_rate_probe.py`（python3 标准库零依赖）:
  并发连接灌注 + 逐秒 VmRSS（/proc/<pid>/status 服务端测量点）+ 拒绝计数 +
  delivery-rate 确认（客户端口径 + 拒绝信号双报，主代理裁决）+ 停止后回落
  验证（回落 ≥ 灌注期涨量 50% → 有界释放）+ 单调性判定（只看灌注期子序列）+
  JSON 汇总（verdict 供主代理裁决，不自动改判）
- argv 必传 host/port（零项目名零 /root/）；`--payload-hex` 承载具体协议载荷
- 注册 TEMPLATES `langs:["any"]`（已核实该字段无机械消费者，主代理选型用）
- SKILL.md:223/:288/:289 与 README 资产计数同步（4→5 模板、20→25 签名、
  task_templates ×7→×3 漂移修复）
- 测试: `test_sk_resource_rate_probe_listed`（TEMPLATES 注册 + langs:["any"] +
  SKILL.md 枚举 + 无参 usage exit≠0 + 零项目名/零 /root/ 断言）

## 三、P3 文档 + tracking + 版本

- REQUIREMENTS_TRACKING 回填 6 条（REQ-V3.1-100/101 + SWR-V3.4.6-001~004）:
  已完成 + 备注列证据引用（ACCEPTANCE_V3_1.md:62 / batch_verify.py:184 /
  r2_guard.py:13 / surface_mapper.py:796 / SKILL.md:134-137）
- SKILL.md: 新增「🆕 v3.6 增量」段（机制修复 + 内容补全 + 验收判据）；「留 v3.6」
  行更新为已处理（锚点 swift 标 v3.5 已覆盖 SWR-V3.5-011）
- workflow_export.py:22 TOOLING_VERSION "3.5.2" → "3.6"（test_v344 动态引用，安全）
- HEALTHCHECK_EVAL_V3_5.md 未修清单 5 条逐条标 v3.6 处理结果
- README 漂移修复: resources（20→25 签名）/ task_templates（×7→×3）/
  templates（×3→×5 补 parser_fuzz + resource_rate_probe）

## 四、裁决记录（义务入库三问执行证据）

| # | 裁决 | 理由 |
|---|---|---|
| R1 | resurrect 分支与 Mode A' 不加清单注入 | 复活者语境是找 UNREACHABLE 缺口，非实证范围分级消费语境；Mode A' 手工循环注入点在主代理侧，成本 > 收益 |
| R2 | 不做 r2_guard 机械 warn | 「防御已到位」判定依赖语义理解，机械检测误报率 > 收益；义务走任务书契约（主代理拒收）而非新机制 |
| R3 | workflow_export.py:38 六类集有意保留 | 仅服务 resurrect 抽样池语义（声称类 UNREACHABLE 复活抽样率）；扩为 8 类改变抽样率，无评估驱动 |
| R4 | 不做 --force、不改数据模型 | 幂等 sources 防重复记账是有意设计；时序前置使 force 无必要；历史缺口由下批选题自然闭合 |
| R5 | 8 语言模板 → 1 个通用协议级模板（用户裁决） | 触发条件=protocol_dos/unbounded/oom 声称（跨语言共性最强）；消费者=R5 主代理选型 + TEMPLATES；裁掉丢=语言专属仪式，保留协议级通用语义 |
| R6 | 账本先回填后补标缺口不修 | 幂等 key 语义是有意设计；INJECTION×ruby 类缺口由下批选题（缺口格优先）闭合 |
| R7 | HEALTHCHECK :174 括号词族勘误 | 写「swift/ps/objc/lua/cs」与实际矩阵缺口（ruby/php/perl/scala/swift）不符 → 以矩阵实况为准 |
| R8（观察不修） | cs.md/cpp.md 手册陷阱节头与 load_manual 解析头不一致 | v3.5.2 已观察；零行为影响（load_manual 容错），下轮候选 |

## 五、验收

204 测试全绿（193 基线 + 11 新增: workflow_export ×2 / harness_runner ×3 /
evidence_ledger ×1 / batch_verify_v3 ×2 / signature_lib ×2 / doc_lint ×1）+
`signature_lib.py selfcheck /root/phpseclib` exit 0 + install 后 DST pytest 全绿。
新在线项目实战验收（覆盖账本缺口格选题 INJECTION/RACE × ruby 或按 REQ-V3.4-006）
本版本止于 install 回归，另行启动。
