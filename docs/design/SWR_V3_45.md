# SWR V3.45 — 逐条修复裁决与测试守卫

> 义务入库四问 (①触发条件 ②消费者 ③裁掉丢什么 ④可推导性) 逐条已过;
> 全部为 修/提示级, 零自动改写, 零新门禁名, 零新强制义务。

## SWR-V3.45-001 (D-1): domain_unmapped 前缀匹配 + type 枚举 warn
- **裁决**: merge 的 per_domain 计数改前缀匹配 (`t == d or t.startswith(d+"_")`);
  validate_surfaces 对 type 不在 {network,data,process,storage,boundary} 的条目输出
  warn (建议归一到枚举值)。不自动改写 (误猜风险>收益, v3.14 D-4 先例)。
- **测试守卫**: test_v3_45: 造含 "network_endpoint" type 的面 → merge 后
  domain_unmapped 不含 network; validate 对全名 type 输出 warn 且不报错。
- **消费者**: merge 门禁⑦前置化 + 主代理空域签收裁决。

## SWR-V3.45-002 (D-2): r4-collect 键漂移告警 + hypothesis 别名
- **裁决**: item 缺 hypothesis_id 且无 `hypothesis` 别名 → R4_ENUM_WARNING
  (kind=missing_hypothesis_id, 不阻断); `hypothesis` 键值归一为 hypothesis_id
  (与 hypotheses-dict 形态同权)。docstring 已有承诺, 实现缺失 = P1 缺陷。
- **测试守卫**: 输入 [{"hypothesis":"H3",...}] → collect 提取 hypothesis_id=H-3;
  输入 [{"findings":[...]}] (无 id) → stderr 告警含 missing_hypothesis_id。

## SWR-V3.45-003 (D-3): auto_bookkept 占位可被 journal 真决策覆写
- **裁决**: 自动簿记记录加 `"auto_bookkept": true` 标记; collect 的 skip 条件改为
  `if c.get("resurrection_review") and not c["resurrection_review"].get("auto_bookkept")`。
  兼容: 旧队列无标记记录保持跳过 (幂等语义不变)。
- **测试守卫**: 先 auto_bookkept 再喂 revived=true decision → resurrection_review
  翻转为 revived=true 且 auto_bookkept 标记移除; 真实决策两次 collect → 第二次 skip。

## SWR-V3.45-004 (D-4): hypotheses.json 渲染双形态容错
- **裁决**: _render_appendix_b_process 读 hypotheses.json 时 list 形态直接取 len,
  dict 形态取 .get("hypotheses", [])。R2 落盘约定维持 dict (K4 形态), 容错为
  渲染侧防御 (零改写)。
- **测试守卫**: 裸数组 hypotheses.json → render 不抛异常且计数正确。

## SWR-V3.45-005 (D-5): refuted-in-list 合规形态不告警
- **裁决**: 告警条件收窄为 `标记命中且不(severity==Low 且 title 含 [refuted])`。
  hint 文本同步更新为"非合规形态才告警"。合规形态 = 既有 hint 的第二选项。
- **测试守卫**: Low+[refuted] → 0 warn; Medium+[refuted] → warn; Low+informational
  无 [refuted] → warn。

## SWR-V3.45-006 (D-6): empirical_modes 交付物引导面探针
- **裁决**: target_profile 新增 S7 探针: 树内可引导产物 (arch/*/boot/Image|vmlinuz|
  vmlinux|bzImage|zImage) + 宿主仿真器 (qemu-system-* 可执行) + 交叉编译器
  (*-linux-gnu-gcc) 三信号 → empirical_modes=["real-target"] (提示级建议, 主代理
  签收后生效)。零信号 → 现状 [] (零行为变化)。
- **测试守卫**: fixture 树 (Image 文件 + fake qemu) → 推荐 real-target; 空树 → []。

## SWR-V3.45-007 (D-7): claim_self_reported 归档
- **裁决**: collect 对非 REACHABLE 且 verifier 给出 claim_type 的候选, 写
  `claim_self_reported` 字段保留原值, claim_type 维持 None (SWR-V3.3.2-001 声称
  只属 REACHABLE 语义不变); R3.5-N 抽样消费侧 (is_claim_like) 已有单真相
  (v3.44-001), 本字段为追溯归档。verifier 任务书步骤 4 增一行: "UNREACHABLE 时
  claim_type 按声称分析填写, collect 归档 claim_self_reported"。
- **测试守卫**: verifier 返回 {verdict:UNREACHABLE, claim_type:crash} → collect 后
  claim_type=None 且 claim_self_reported="crash"。

## SWR-V3.45-008 (D-8): containment 派生一致性 warn
- **裁决**: _derive_containment 走 profile 派生分支且证据文本含内核上下文信号
  (softirq|kthread|workqueue|中断上下文|kernel thread|软中断) 且派生值 ∈
  {process_sandbox} 时输出 warn (提示级, 不自动改值)。verifier 显式给出值时不告警。
- **测试守卫**: 派生 process_sandbox + 证据含 "softirq 上下文" → stderr warn;
  证据无信号 → 无 warn; verifier 显式 containment → 无 warn。

## SWR-V3.45-009 (D-9): biz_hypothesis 任务书三条款
- **裁决**: (a) claim_type 反例表: static_verified/self_refuted/sibling_differential
  等描述词 → 映射 other/null (v3.41-003 实录); (b) verdict 意图映射: "部分证伪但
  无 confirmed finding → reviewed_clean (证伪断言入 findings 须标 [refuted]+Low)";
  (c) 面桥接条款: finding 落在清单外新面 → tracked_surfaces 不填该面, coverage_note
  声明新面 file:line 证据, 由主代理回填 input_surface.json 后再重跑 collect。
- **测试守卫**: test_doc_lint 资产计数同步 (先例/清单条数在正文节多处出现)。

## SWR-V3.45-010 (D-10): verifier 任务书三维度
- **裁决**: 步骤 0 增补: (a) 同一字段多处读取须区分快照读/活体读, 守卫与消费
  读取序不一致时枚举 [快照,活体) 窗口; (b) UNREACHABLE 阻断论证须枚举生命周期/
  提交期 GC 维度 (写点时刻对象仍在世); (c) 可选维度: 交付二进制核查 (extract-ikconfig/
  nm/objdump) — 配置与修复进入交付物的更强证据层。
- **测试守卫**: 任务书文本 grep 三维度关键词 (test_doc_lint 或 test_v3_45 字符串断言)。

## SWR-V3.45-011 (D-11): resurrect_prompt 两增补
- **裁决**: (a) 实证通道信号: "本目标实证通道已开 (qemu 真实内核引导形态) 时可
  自建 harness 补测, 优先补测 verifier 未实测维度"; (b) gap 行号容差明示: "gap
  引用行号 ±5 容差, 以定义形态为准, 消费侧重验者逐字核对"。
- **测试守卫**: resurrect_prompt 输出含两关键词 (字符串断言)。

## SWR-V3.45-012 (D-12): hypothesis_filter 进度摘要条款
- **裁决**: 模板首部: "每完成 4-5 条输出一行进度摘要 (filtered N/M: k=x d=y bc=z),
  严禁长时间静默 — K4 批次 7/7 筛选 agent 因静默被 watchdog 停滞的实录"。
- **测试守卫**: 模板文本断言。

## SWR-V3.45-013 (D-13): R2 假设生成派发条款 (SKILL.md)
- **裁决**: R2 假设生成段增补 (提示级): 派发假设生成 agent 时任务书必须含
  分片落盘条款 (每 ~15 条写 _hypo_<GROUP>_partN.json 或等价增量文件, 完成后合并)
  与"最终回复只给统计, 严禁粘贴完整 JSON" — 96KB 回复 API 断连一死一活实录。
- **测试守卫**: SKILL.md 文本断言。

## SWR-V3.45-014 (D-14): 开题四步卫生检查
- **裁决**: 开题四步 ① 前增加: 工作区卫生检查 (git status --short 必须为空;
  前批次 harness 插桩遗留先还原 — K4 act_skbmod.c 实录)。
- **测试守卫**: SKILL.md 文本断言。

## SWR-V3.45-015 (D-15): 对抗枚举增"新机制×旧机制组合窗口"维度
- **裁决**: 对抗枚举段增补: 目标近期引入新机制时, 枚举新机制与树内历史机制
  (查找模式/状态位/旧回调契约) 的组合窗口 — K5 failfs(2026)×LOOKUP_MOUNTPOINT
  (2020) 实录 = 该批次唯一 REACHABLE。
- **测试守卫**: SKILL.md 文本断言。

## SWR-V3.45-016 (D-16): severity 裁决走 override 通道提示
- **裁决**: R4/R6 段增补 (提示级): 主代理 severity 裁决与机械映射不一致时, 用
  severity_override + severity_override_reason 落盘 (通道已存在, K5-6 实录主代理
  未用 → 提示条款; 不改动 render 优先级)。
- **测试守卫**: SKILL.md 文本断言。

## 不修/裁除 (附理由, DDL 消化记录)
- K2-11 taskFile: 已修 (取证: workflow_export.py:603 绝对路径) → 裁除
- K2-12 journal label / K4-16 WebSearch 降级 / K5-9 resume SOP / K5-10 抽核度量 /
  K5-12 实证分工: 观察项 → 留档 lessons, 不入库
- K4-1 上游比对 / K4-2 树内自证 / K5-1 R4 兜底 / K5-4 配置形态: 可推导 (四问④)
  → 裁除
- RECALL-001/003/004: 目标形态不匹配 → 裁除; RECALL-002 由 D-10(b) 服务
