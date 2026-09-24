# REQ_V3_46 — v3.46 周期需求 (K6-K9 四批 lessons 复盘)

> 触发: 用户指令 "开始优化 /root/reachable-critical-audit" (2026-09-24)。
> 输入: batch_K6/K7/K8/K9 lessons.md「对 skill 的教训」共 12 条 → 聚类 7 缺陷。
> DDL 消化: K6-K9 全部教训条目在本清单出现或显式裁除 (裁除项见 §5)。

## 1. 缺陷清单 (编号/缺陷(代码核实)/修复/编辑点)

| # | 缺陷 (取证核实) | 修复 | 编辑点 (实测) |
|---|---|---|---|
| D-1 | `_derive_attacker_tier` 裸子串匹配把免责句 "非 remote" 误标 remote (K6 批次级 4 候选 + K7 第 4 次触发 8 候选手工修正) | 句级清洗: 免责句式不参与关键词计数; 全免责时返回 None + warn 交主代理 | tools/batch_verify.py:457-459 |
| D-2 | r4-collect schema 漂移持续扩散: K9 三形态——(a) "id" 替代 hypothesis_id (b) "hypothesis" 描述键干扰 (c) "hypothesis_tracked_surfaces" 前缀键不被识别 (K8 三种形态 + K9 三种新变体) | 归一器扩展三形态 + 每次命中记 norm_flags (collect warn); **裸 id 形态不归一** (v3.42 近似键诊断契约, 不自动改写); 模板 canonical 示例钉死键名并禁别名 | tools/batch_verify.py:970(_normalize_r4_payload), 新 _norm_hypothesis_keys; assets/task_templates/biz_hypothesis.md |
| D-3 | workflow taskFile 路径手工重打漂移无预检 (K9 refutation 一票拒绝 + token 浪费); r4-collect 多文件静默只取首个 (K8) | 生成 JS 加 Node fs.existsSync 预检快速失败; r4-collect --file 多文件显式报错 | src/workflow_export.py:225-232, 269-272; tools/batch_verify.py r4-collect 入口 |
| D-4 | R1 trust_boundary 判定缺编译面前置 (K6 HID 35/40 面前提被 R3 推翻; K8 计划前提被 R1 实测证伪) | surface_map 任务书加 config 门核条款: 未核对编译面不得写 local | assets/task_templates/surface_map_domain.md |
| D-5 | 零硬件实证通道四条未入库 (K6 dummy_hcd/usb-storage, K7 nciemp, K8 RPC responder) — SWR-V3.38-005 回收条款欠账 | 新手册条目 kernel_zero_hardware_channels.md (去项目化, 来源注记 lessons 条目) | assets/harness_manuals/ (新文件) |
| D-6 | workflow 版本滞后告警语义不清 (只告警不阻断, 未注明重导出后可安全运行) (K6 #11) | 告警文案补一句 | 告警文案处 (实现期定位) |
| D-7 | resurrect 导出器 eligible 只挑 UNREACHABLE, REQ-V3.2-021 的 20% 抽样规则与工具能力不一致 (K7 #9) | 文档/注释澄清: NEEDS_REVIEW 抽样需主代理手工 payload | src/workflow_export.py:536 附近注释 |

## 2. 测试守卫约束

- D-1: 免责句/混合句/纯正向句三形态断言 + K6/K7 样本 fixture
- D-2: K8/K9 漂移形态 fixture 输入 → 键名规范 + alias 计数 warn
- D-3: 缺文件 payload → 导出 JS 含预检 + 单测快速失败路径
- 全量回归 + 旧队列复跑零新增告警 (gpac/freetype/av 队列)

## 3. 开发序列

P1 (D-1) → P2 (D-2, D-3) → P3 (D-4, D-5, D-6, D-7) → P4 版本链五件 → 测试验收 → 安装提交。

## 4. 验证命令

```bash
bash install.sh                       # 自带全量测试
python3 tests/test_v346.py            # 新周期守卫
# 旧队列: assert_ledger 复跑, violations blocking=0 / warn 与变更前一致
```

## 5. DDL 裁除项 (显式)

- K6 #11 与 K7 #9 已并 D-6/D-7; K7 #10 (finit_module ENOEXEC) 并入 D-5 手册陷阱注记;
- K8 #8 (heredoc \x00 双转义) 为环境级一次教训, 裁除 (无技能侧机制承载, 记录保留于 lessons)。
