# SKILL Lessons — Pillow（2026-08-28）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

## 主代理过程观察（人工补充）

- Pillow 是 skill 首个带官方 STRIDE 威胁模型的目标。上游文档直接提供信任边界声明与既知风险清单(E-1~E-4/D-1~D-3/S-1/I-2/T-1~T-3), 使 R2 大量假设可直接映射为『已文档化』——正确姿态是把审计火力集中到『绕过其声称缓解的新路径』上(本次产出: DCX/MPO 绕过 D-1; EPS-symlink 绕过 E-2 的文件读写类)
- R1 测绘 agent 两次误报同一模式: 只看局部函数(ImagingNewPrologueSubtype 仅有上界检查)漏掉调用者前置的守卫(ImagingNewInternal/ImagingNewBlock 的 xsize<0||ysize<0); TgaRleDecode 漏看 literal 分支在裁剪前的完整 n 校验。经验: C 解码器的边界判断必须沿调用链双向核查(守卫在调用者 vs 被调者)。R2 filter 两次都正确拦截, 主代理抽查 3 条 drop 均属实
- ASAN 双构建是本次审计的决胜基础设施: 普通构建下『越界但没崩→结论不确定』的泥潭被 ASAN 直接判定(12k+8k 变异零报告、187 个结构化样本全 REFUTED、SGI 11 组样本确认 64 位兜底成立)。经验: 内存安全类审计应尽早并行建 ASAN 构建(复制源码树+CFLAGS=-fsanitize=address), 它同时喂饱 R3/R4/R5 三级验证
- 实证 harness 纪律: 主代理对两个头部 finding(DCX bypass、EPS symlink bypass)均做了『从零构造+对照实验』的独立复核, 不复用子智能体 harness——DCX 用单帧 PCX 同尺寸对照证明『门禁存在但被绕过』而非『门禁不存在』; EPS 用 /tmp 内 vs /tmp 外 symlink 对照厘清 gs -dSAFER 的目录白名单语义, 归因得以精确
- H1 的 DCX/MPO 是同一缺陷家族(多帧 seek 逐帧改 _size 无逐帧 bomb 检查)的两个实例。发现方式: 不是新 sink 而是『门禁时序 vs 状态机重入』——open 时一次性检查覆盖不到 per-frame _open 重跑。多帧容器类目标值得用『逐帧状态机 vs 逐帧门禁』的对账清单

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。

## Skill 缺陷清单（主代理复盘，2026-08-28 运行实证）

### P0 — 真缺陷
1. **R4 schema 漂移超出 r4-collect 自适应范围**：6 agent 中 4 个产出非 canonical 形态
   （cwe 字符串、call_chain 字符串、location/surfaces 别名、H7 tracked_surfaces 整体缺失）。
   文档宣称的四类自适应漂移不覆盖上述任何一类。主代理被迫手写 normalizer；
   未修复则门禁⑦ 假失败（H7 13 面）。修法: r4 前置 schema 校验器（仿 r2_guard fidelity）。
2. **--stage report 三处渲染缺陷**：①附录 A 无视队列 NEEDS_REVIEW 候选（CAND-001 存在
   却输出"无"）；②B.2 语言覆盖表 surfaces/候选恒 0（未现场重算 input_surface.json）；
   ③R4 finding 位置列恒 "-"（不消费 call_chain[0]/location）。均靠主代理手工编辑补救。
3. **SKILL.md 文档漂移**：v3.1 增量段仍记载已裁除的 `surface_mapper.py repair`
   （v3.5.2 删除后 changelog 段无注记）——误调用一次。

### P1 — 机制缺口
4. **R1 任务书缺"边界检查双向核实"条款**：两次误报同模式（B-001 只看 Prologue 漏调用者
   守卫；S-CDEC-008 漏 :71 前置检查），均被 R2 filter 拦截但各浪费一轮。
5. **门禁⑦ tracked_ids 无机械支持**：union 脚本手写；73 个无 finding 面被迫以
   H-COV [covered] finding 承载。建议一等 surface 裁决记录结构。
6. **assert_ledger 失败输出只报覆盖差异一行**，不枚举各门状态。
7. **--stage workflow-script payload 不落盘**：next_step 说"从落盘文件整读整传"，
   实际只打在 stdout——主代理手工重提取。

### P2 — 经验固化建议
8. **"check-after-op + 循环不变量"是安全形态**：BcnDecode put_block 后检查 y 被两 agent
   误判为缺陷；判缺陷前须证明不变量破坏。建议入 checklist_library。
9. **R4 confirmed finding 无内建独立复核**：本次靠主代理自发从零复现兜底，且抓到了
   H4-1 的假阴性陷阱（symlink 必须在 /tmp 内 gs 才放行）。
10. **cve-ghsa-draft 零中文自检无脚本**，靠主代理手写正则。

## v3.9 修复回执（2026-08-28）

缺陷清单（上节 10 条）已按 SYSTEM_DESIGN_V3_9/REQ_V3_9/SWR_V3_9 全量处置：
- 修复：P0-1/2/3、P1-4/5/7、P2-8/9/10（r4 守卫、报告三修、tracked-ids stage、
  payload 落盘、任务书双向核实条款、CK-POSTOP-INVARIANT、门禁 ③d、
  check_no_cjk 脚本、TOOLING_VERSION 3.7→3.9、SKILL.md repair 注记）
- 撤销：P1-6（代码复查确认 assert_ledger 现有契约已完备，防义务棘轮）
- 验证：255 passed/2 skipped（243 基线 + 14 新增 - 2 旧测试预期更新）；
  signature_lib selfcheck 去项目化扫描绿；Pillow 真实队列复跑：tracked-ids
  120/120、六门禁含 ③d 全 PASS、报告三处渲染缺陷消失且主代理零手工编辑
  （仅恢复契约允许的三、修复建议与结论段）
- 旧测试预期更新 2 处：test_gate3b_* 按 ③d 豁免先例改 require_r4_independent=False；
  test_language_coverage_table_roles 锁定的 ".js" 原始形态与新归一化行为冲突
