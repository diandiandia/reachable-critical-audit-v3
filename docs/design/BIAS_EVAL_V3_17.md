# BIAS EVAL V3.17 — 四缺陷评估（2026-09-01）

## ① 盲目带入历史审计信息

- **案例支撑来源**：本版案例 = 2026-09-01 会话 V8 评估实录（六缺陷 + 取证
  行号：surface_mapper.py:224/735、signature_matcher.py:42-44/51、
  batch_verify.py:390/418/1653/1687/1701/1953、harness_runner.py:25、
  checklist_library 零 GC 命中 grep）。本环境各项目无 .audit_results/
  lessons.md、记忆索引为空——设计件已如实声明，不伪造条目指向。
- **去项目化**：运行时资产零项目名零框架名——generation_registry 只含通用
  DSL 族（proto/yacc/lex/fbs/ragel/asn1/idl），**.tq 明确不入库**（两段式：
  机制入库、项目局部署名）；differential_probe 零项目名；清单族用机制形态
  多词短语；target_profile 信号全部机制形态（目录名 gc 为机制词, 非项目词）。
- **机器守卫**：tests/test_deproject_assets.py PROJECT_TOKENS 扫描扩展
  覆盖新资产（differential_probe.py / generation_registry.json /
  target_profile.py / 新清单条目正文）——违规即拦截。

## ② 设计偏见

- **编排便利 ≠ skill 义务**：target_profile --write 与签收是主代理 R0 动作
  （同 target_kind 先例），未签收 = 全默认，**零强制义务**；不新增"必须签收"
  检查项（门禁⑧ target_kind_required 先例不复制——profile 无门禁承载）。
- **不自动改写**：containment 仅缺省推导（none，零告警），severity 调整是
  机械映射的确定性步（非猜测性改写），override 绝对优先；语义轴不做自动
  聚类（v3.11 先例）。
- **修法层级**：D-6 清单族走 applicability_signals 词边界门控（v3.12/v3.13
  先例），不做裸词绑定；agent 行为偏差（verifier 对引擎深度不足）以清单/
  模板提示级承载，不升级为硬义务。

## ③ 死代码

- **消费者清单**：target_profile 每字段 → surface_model（R1 派发/R2 采样/
  门禁⑦ tracked-ids）、generation_layers（三消费端合并视图）、scale_class
  （size_tier 输入）、containment_default（workflow_export 注入 + collect）、
  empirical_modes（R5 主代理选型）——逐字段一消费者, 无消费者不建。
- **scaled_caps**：消费者 = build_project_index/expand_window（佐证器链路）；
  缺省路径零变化, 无新死参数。
- **differential_probe**：TEMPLATES 注册（harness_runner.list_templates
  消费）+ R5 SKILL.md 枚举, 消费者在注册时即存在。
- **新清单 5 条**：checklist_binder 按 binding/applicability_signals 自动
  触达（数据驱动消费者恒在, v3.12 先例）。

## ④ 过设计

- **无新门禁名、无新阶段、无新强制义务**：六门禁①-⑧判据语义零改动；
  profile 未签收 = 现状；旧队列复跑零新增告警为验收硬判据。
- **义务入库三问逐项**：
  - 注册表默认视图（触发=存在 registry 文件, 内容=现状集合→零行为变化；
    消费者=三消费端；裁掉丢 D-1 修复载体）；
  - containment 字段（触发=候选级字段, 缺省 none；消费者=严重度呈现；
    裁掉丢 V8 sandbox 口径错配）；
  - super-large 档（触发=file_count>2000；消费者=SKILL.md R1 派发与模板；
    裁掉丢 D-2 载体, W6 §17.1 失控实录为既有案例）；
  - 语义轴（触发=profile 签收 semantic；消费者=R1/R2/⑦；裁掉丢 D-5 载体）；
  - 差分模板（触发=主代理选型, langs any 无机械消费者——v3.6
    resource_rate_probe 同款形态先例；裁掉丢 D-4 载体）。
- **明确不做**：H8/JIT 假说（v3.12 先例）、语义轴自动组族（v3.11 先例）、
  containment 自动检测（提示级）、.tq 运行时入库（三禁止①）、README 存量
  计数漂移（v3.12 先例不修）。

## 实现期复查计划

实现完成后重跑本评估：新资产正文扫描（PROJECT_TOKENS）、每新函数消费者
核对、门禁名 grep（`gate`/`门禁` 新增处必须为既有 8 项）、旧队列复跑 warn
diff 逐条比对。
