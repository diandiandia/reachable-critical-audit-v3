# 2025-2026 三引擎 CVE 全景召回评估

reachable-critical-audit 发现包络对照（WebKit / Firefox / Chrome，medium 及以上）。
评估日期 2026-09-06。分类契约见同目录 `taxonomy.md`。

## 0. 结论速览

1. **包络内召回上限 80.2%**（1948/2430，剔除 456 条无信息 rollup/粗标签后）——
   skill 现状机制可生成约 4/5 真实 CVE 的族级假设；critical 级 85.1%（160/188）。
2. **不需要浏览器分支**：UI 信任指示层 + 移动平台集成层 + 安全 UX 合计仅 9.0%，
   且全部为固定低危产出——主线吸收 + 边界声明补两族即可。
3. **需要优化，但缺口类型已变**：v3.23 前的"JIT 层未覆盖"已修；本轮证据指向
   "深耕 + 精度"——site-isolation 检查点、JIT 根因归属判据、边界声明补族、
   回归集扩三类（详见 `v324_requirements.md`：四修复三裁除）。
4. **v3.23 JIT 轴验证自洽**：L1 全引擎仅 68 条（2.8%），65 条 L1a 除 1 条外全为
   high/medium——v3.23 假设族规模与真实分布匹配，无欠账；但 WebKit 侧实证
   材料稀薄（1.0%），JIT 轴价值验证需代码级样本而非公告计数。

## 1. 方法与数据

| 引擎 | 数据源 | 公告期次 | 唯一 CVE（medium+） | 覆盖 |
|---|---|---|---|---|
| Firefox | MFSA 官方公告索引 | 186 期（2025-01..98 / 2026-01..88） | 530（C8/H262/M260） | 100%，0 失败 |
| Chrome | Chrome Releases Stable 系 | 170 期（2025-01-07..2026-09-03） | 2164（C173/H987/M1004） | 100%（92 期含 CVE，78 期原文无） |
| WebKit | WSA + Apple Safari 公告 + NVD 核验 | WSA 15 期 + Safari 13 期 | 192（C7/H75/M107/L3） | WSA/Safari 100%；OS 级公告抽样核实 |

判定口径：**族覆盖**（defect_class × surface 能否由 R1→R2/H1-H7 生成假设），
非点命中。无机制关键词不猜（→L2a）。逐条 rationale 引用原文机制词。
逐引擎强校验：len(in)==len(out)、CVE 集合相等、layer 枚举合法。189 条标 `[ambig]`。

## 2. 全景统计

### 2.1 每引擎包络占比

| 引擎 | 总数 | L0+L1 | 包络内 | L1 | L1% | L2a | L2b+c+f | L2c+L2d |
|---|---|---|---|---|---|---|---|---|
| Firefox | 530 | 313 | 73.6%（313/425） | 27 | 6.4% | 105 | 60（14.1%） | 74（17.4%） |
| Chrome | 2164 | 1460 | 80.5%（1460/1813） | 39 | 2.2% | 351 | 142（6.6%） | 313（17.3%） |
| WebKit | 192 | 175 | 91.1%（175/192） | 2 | 1.0% | 0 | 16（8.3%） | 1（0.5%） |
| **合计** | **2886** | **1948** | **80.2%（1948/2430）** | **68** | **2.8%** | **456** | **218（9.0%）** | **388（16.0%）** |

### 2.2 层级分布（severity 交叉）

| layer | 总数 | critical | high | medium |
|---|---|---|---|---|
| L0a 数据面内存 | 732 | 40 | 414 | 278 |
| L0b 生命周期内存 | 670 | **107** | 379 | 182 |
| L0c 图形/GPU 边界 | 63 | 6 | 40 | 17 |
| L0d 信任边界逻辑 | 412 | 6 | 98 | 307 |
| L0e 资源耗尽 | 3 | 0 | 0 | 3 |
| L1a JIT 编译正确性 | 65 | 1 | 53 | 11 |
| L1b 引擎 GC 屏障 | 3 | 0 | 0 | 3 |
| L2a 无信息 | 456 | 5 | 191 | 260 |
| L2b UI 信任指示 | 82 | 0 | 11 | 71 |
| L2c 移动平台集成 | 125 | 8 | 37 | 80 |
| L2d 内部组件 | 263 | 15 | 98 | 150 |
| L2e 闭源第三方 | 1 | 0 | 1 | 0 |
| L2f 安全 UX | 11 | 0 | 2 | 9 |

### 2.3 critical 188 条分布

L0b **107（57%）** > L0a 40（21%）> L2d 15（8%）> L2c 8（4%）>
L0c 6 + L0d 6（各 3%）> L2a 5（3%）> L1a 1（1%）。

- **critical 的 85.1% 在包络内**（L0 四族 + L1a = 160/188）；
- **L0b 是 critical 回收主力**：Chrome 173 个 critical 中 106 个是浏览器组件
  UAF（Ozone/Aura/Views/Bluetooth/Chromoting/Passwords/Downloads 等桌面壳组件）——
  H3 异步生命周期假说族覆盖；
- **L1a 对 critical 贡献仅 1 条**：JIT 类真实分布以 high 为主（53/65），
  CVE-2026-85046（CVSS 8.8 high）落在该形态内，与 v3.23 轴族设定一致。

## 3. 四问回答

### Q1 skill 能发现这些问题吗？
**能发现约 80% 的族**。L0 内格局：L0a（732）> L0b（670）> L0d（412）——
数据面内存安全、生命周期竞态、信任边界逻辑三大方向全部由现有机制覆盖
（R1 输入面测绘 + R2 CWE 族假设 + H3/H4/H7 假说）。Firefox 侧 L0d 已反超
经典内存类成为最大单方向（97 条，2025H2 起每期固定产出 SOP/site-isolation/
mitigation-bypass 句式），H4/H7 是当前最高收益方向。

### Q2 需要优化吗？
**需要，但缺口类型从"覆盖面"转为"深耕 + 精度"**：
1. **site-isolation/origin-placement 检查点缺失**（→ V324-R-1）：三引擎 L0d 412
   条中含"Graphics 组件里的 site-isolation"（Firefox 74934 CanvasWebGL 等）、
   Chrome Site Isolation 组件族——现有 H4 检查点未显式含"跨进程资源归因错误
   origin"形态，假设生成缺锚点；
2. **JIT 根因归属判据缺失**（→ V324-R-3）：Chrome 47 条 V8 非 TC 内存缺陷无法
   从公告区分 runtime/JIT 根因，全部 [ambig]——v3.23 轴缺"归属未知"标注条款；
3. **边界声明未含两大实测族**（→ V324-R-4）：L2b（82）+ L2c（125）是每期固定
   产出，声明补族后假设生成可显式排除，避免无效投入；
4. **回归集只有 L1 样本**（→ V324-R-5）：critical 主导族（L0b）与最大单方向
   （L0d）无代表样本，阶段 6 验收对照力不足。
裁除候选（L2a 度量改进 / H3 义务化 / 内部组件专项 / 移动平台分支）理由见
`v324_requirements.md`。

### Q3 需要浏览器分支吗？
**不需要**。量化判据：
- UI 信任指示 + 移动平台集成 + 安全 UX 合计 **9.0%**，且 severity 结构
  全为 low-medium 形态（L2b 82 条中 0 critical / 11 high）；
- 平台面 L2c+L2d（16.0%）本质是"非 web 可达面"的攻击面分类，不是机制缺口——
  对完整浏览器代码库审计时 R1 表面测绘本就覆盖 telemetry/devtools 等端点；
- 引擎间一致性：Firefox 14.1% / Chrome 6.6% / WebKit 8.3%，无一超过
  "主线吸收 + 边界声明"可承受的范围。
若未来做产品线扩展，移动平台集成面（L2c 125）是最大候选，但属使命外。

### Q4 v3.23 JIT 修复验证结果
自洽：L1 真实占比 2.8%，且 severity 结构（high 53/65）与 85046 形态一致，
v3.23 轴族规模未过设计也未欠账。局限：WebKit 侧公告粒度无法提供 JIT 实证
材料（仅 2 条明确 JIT 修复），JIT 轴的价值验证应改走代码级样本（如 85046
形态的审计对照），公告计数不是该轴的验证手段。

## 4. 边界声明 vs 实测

| 已声明边界 | 实测对应 | 判定 |
|---|---|---|
| JIT/编译器优化正确性层 | L1 = 68（2.8%） | 自洽，无需扩缩 |
| 闭源依赖内部 | L2e = 1 | 自洽（vendored 开源库如 libvpx/PDF.js 不属此类，归 L0） |
| 非目标平台变体 | 无直接对应（L2c 是产品线集成层而非平台变体） | 保留 |
| **未声明：UI 信任指示层** | L2b = 82 | **建议补声明**（V324-R-4） |
| **未声明：移动平台集成层** | L2c = 125 | **建议补声明**（V324-R-4） |
| 未声明但非缺口：内部组件 escape | L2d = 263（Firefox 2026 起成体系打标签） | 攻击面分类，R1 天然覆盖，不建机制 |

## 5. 数据质量与局限

- **L2a = 456（15.8%）**：Firefox 105 条 rollup（"Memory safety bugs fixed in X"
  无逐 bug 信息）+ Chrome 351 条粗标签（"Inappropriate implementation" 约 250 条
  无机制词）。契约禁猜——包络内占比 80.2% 因之是**保守下界**；
  提升度量需接 bug 明细数据源（Chromium bug tracker 联动），非 skill 修改
  （裁除 V324-C-2）。
- **WebKit [ambig] 110/192（57%）**：Apple 样板句（"improved memory handling" /
  "improved state management"）无子类机制词；L0 归属可靠（修复动词映射），
  子类分布（L0a 81 vs L0b 48）不可全信——WebKit 的 L0a/L0b 拆分仅为参考。
- Firefox 2025-09 起标题化 desc（"机制词 in the X component"）机器可判，
  此前 prose 期逐条人工判——双轨形态已在 classify 文件 rationale 中溯源。
- WebKit 表含 6 条 2023/2024 编号 CVE（窗口期被 WSA/Apple 收录）与 3 条
  第三方组件条目（PDF.js/ANGLE，开源 vendored 归 L0）。
- 聚合时 Firefox 的 sev="moderate" 已归一化为 medium。

## 6. 文件清单（本目录）

- `taxonomy.md` — 判定契约（分类子代理唯一依据）
- `firefox_cves.json` / `chrome_cves.json` / `webkit_cves.json` — 原始数据
- `classify_firefox.json` / `classify_chrome.json` / `classify_webkit.json` — 逐条分类+rationale
- `v324_requirements.md` — v3.24 优化需求清单（本报告的下一步输入）
