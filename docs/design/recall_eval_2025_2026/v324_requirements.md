# v3.24 优化需求清单

输入来源：`recall_eval.md`（2026-09-06 三引擎 2886 CVE 全景分类）。
本文件是 skill-optimizer v3.24 周期**阶段 0 的输入**，未做实现。

## 证据基线

- 2886 条 medium+ CVE 逐条分类（Firefox 530 / Chrome 2164 / WebKit 192），
  逐引擎 len/集合强校验，189 条 [ambig]；
- 包络内召回上限 **80.2%**（1948/2430）；critical 85.1% 包络内；
- L1 = 68（2.8%）；L2b+c+f = 218（9.0%）；L2c+L2d = 388（16.0%）；
- critical 188 条中 L0b 107（57%）、L0a 40（21%）。

## 修复候选（进入 v3.24 设计五件套）

### V324-R-1（P3 内容层）H4 信任边界检查点补 site-isolation/origin-placement 形态

- **证据**：三引擎 L0d 412 条为包络内第三大方向；Firefox 2025H2 起每期固定产出
  SOP/site-isolation/mitigation-bypass 条目，含 **Graphics 组件里的 site-isolation**
  （CVE-2026-74934 CanvasWebGL、CVE-2025-9180 Canvas2D SOP bypass、16358/16399
  WebRender/Navigation）；Chrome Site Isolation 组件族（3066/9903/11174/17779/
  78903/78953/79002/79191/79228）；WebKit 沙箱逃逸/SOP/CSP 簇 21 条干净条目。
- **修法**：`task_templates/biz_hypothesis.md` H4 检测要点补一行提示级检查点：
  "跨进程资源归因（site isolation/origin placement）：纹理/缓存/下载/导航目标/
  worker 等资源被绑定到错误 origin 即信任边界破坏——检查资源创建与归因的
  origin 上下文是否一致"。禁止新增门禁/强制义务。
- **义务三问**：① 触发条件：多进程 origin 隔离形态目标（application 型，
  H4 本就运行）；② 消费者：R4 H4 假说子智能体；③ 裁掉丢什么：site-isolation
  类是 2026 三引擎固定产出，无该锚点假设生成对该方向系统性盲（Firefox 97 条
  L0d 实录）。

### V324-R-2（P3 内容层）JIT 轴补根因归属判定条款

- **证据**：Chrome 47 条 V8 非 TC 内存缺陷（OOB/整数溢出）从公告无法区分
  runtime/JIT 根因，全部标 [ambig]；WebKit L1a 实证材料仅 2 条。v3.23 轴族
  未定义"归属未知"的处置，验证期有默认归编译器的误判风险（85046 与
  runtime 类缺陷的族边界被稀释）。
- **修法**：`task_templates/surface_map_domain.md` JIT 优化正确性层轴测绘段
  （v3.23 段内）补一句提示级条款："缺陷根因无法在 runtime 实现与编译器
  正确性之间归属时，标注归属未知并保持 [ambig]——不得默认归编译器正确性"。
- **义务三问**：① 触发条件：generation_layers 含 jit 的目标；② 消费者：
  R2 假设生成 + R3 验证判定 + 六门禁证据分级（claim 归属影响 CWE 映射）；
  ③ 裁掉丢什么：L0/L1 族边界失真，回归集对照失效（Chrome 47 条实录）。

### V324-R-3（P3 内容层）发现包络边界声明补两族

- **证据**：L2b UI 信任指示 82 条（地址栏欺骗/UI spoofing，0 critical 11 high）
  + L2c 移动平台集成 125 条（iOS WKWebView 集成/Android 组件层）为每期固定
  产出，且 v3.23 边界声明（JIT/闭源/非目标平台）未覆盖——假设生成对这两族
  无排除锚点。
- **修法**：SKILL.md 发现包络边界声明段补 "UI 信任指示层（地址栏/界面欺骗类）"
  与 "移动端平台集成层"；warn 注记不阻断（同 v3.23 形态）。severity 映射与
  门禁不动。
- **义务三问**：① 触发条件：无条件（声明性文档，R2 提示级）；② 消费者：
  R2 假设生成边界提示 + 报告边界段；③ 裁掉丢什么：两族 218 条（9.0%）无
  显式排除，R2 对 UI 层无效投入（三引擎实测每期 1-3 条固定低危产出）。

### V324-R-4（fixture 层）召回率回归集扩充三类样本

- **证据**：现有 RECALL-001 仅覆盖 L1a（85046 形态）；critical 主导族 L0b
  （57%）与最大单方向 L0d 无代表样本，阶段 6 验收对照力不足。
- **修法**：`tests/fixtures/recall_regression_set.json` 追加（去项目化形态，
  归属仅进 case_source 追溯字段）：
  - RECALL-002 L0b 生命周期 UAF：defect_class "异步对象生命周期竞态——回调
    持引用跨任务/跨进程释放"，cwe ["CWE-416"]，expected_hypothesis "H3 异步
    生命周期竞态 → 回调持引用释放竞态"；
  - RECALL-003 L0d site-isolation：defect_class "跨进程资源 origin 归因错误
    （纹理/缓存/下载/导航目标绑定错误 origin）"，cwe ["CWE-863"]，
    expected_hypothesis "H4 跨进程信任边界 → 资源归因错误 origin"；
  - RECALL-004 L0c 图形边界：defect_class "GPU 命令缓冲/着色器校验整数溢出
    导致越界写"，cwe ["CWE-787","CWE-190"]，expected_hypothesis "H2 远端控制
    解引用长度 + H4 跨进程信任边界 → GPU 命令缓冲越界"。
- **义务三问**：① 触发条件：仅测试/评估引用（fixture 不进运行时——与
  RECALL-001 同契约）；② 消费者：test_v323 形态守卫 + 阶段 0/6 对照；
  ③ 裁掉丢什么：L0b/L0d/L0c 三族验收无对照样本。

## 裁除候选（阶段 0 需显式裁决，附预裁决理由）

### V324-C-1 H3 生命周期假说义务化深耕
**预裁决：裁除。** critical 57% 落 L0b 是**选题优先级**信号而非假设族缺口——
H3 检测要点（回调持引用/池复用状态残留）已覆盖 L0b 全部机制形态（Chrome 106
条 critical UAF 的 desc 形态无一超出）。义务三问第一问：无新触发条件可区分。

### V324-C-2 L2a 度量改进（Chrome 粗标签）
**预裁决：裁除。** 351 条 "Inappropriate implementation" 无机制词是公告粒度
问题，修复路径是接 Chromium bug tracker 明细数据源（外部数据工程），不是
skill 机制修改。契约禁猜条款保留。

### V324-C-3 内部组件 escape 专项（L2d 263 条）
**预裁决：裁除。** L2d 是"非 web 可达面"的攻击面分类：对完整浏览器代码库
审计时 R1 表面测绘本就覆盖 telemetry/devtools/updater 端点（它们有协议
输入面）。Firefox 2026 成体系打 escape 标签是 Mozilla 侧披露风格变化，不
构成机制缺口。记入 recall_eval §4 实践注记，不进 skill。

### V324-C-4 移动平台分支/产品线扩展
**预裁决：裁除（本次）。** L2c 125 条为使命外（WKWebView 集成层），量化
占比 4.3% 且 severity 低。若未来产品线扩展另议，不阻塞主线。

## 阶段 0 启动清单（skill-optimizer v3.24）

1. **必读**：本文件 + `recall_eval.md` + taxonomy.md + 三份 classify 文件；
   缺陷清单每条案例支撑必须指向 classify 文件的具体条目（CVE 号）或
   recall_eval 数字——禁止凭本清单转述。
2. **DDL 消化条款**：v3.23 遗留事项（阶段 6 验收审计未跑，新项目优先补
   coverage-ledger 缺口格）+ 本清单四修复四裁除，须在缺陷清单中显式标注
   消化状态。
3. **设计约束**：修法形态纪律（全部提示级/warn 注记，禁止自动改写）；
   fixture 去项目化（机器守卫 test_deproject_assets 若涉 fixture 正文需同步扩）；
   义务三问已逐项预答，阶段 2 复核。
4. **验收对照**：阶段 6 验收审计可用回归集新样本（RECALL-002..004）作为
   发现力对照输入；首轮验收建议以三引擎之一的历史缺陷形态出题（对照口径：
   族覆盖非点命中）。
