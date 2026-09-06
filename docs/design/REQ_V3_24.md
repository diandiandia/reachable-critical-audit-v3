# REQ V3.24 — 三引擎全景召回评估驱动缺陷修复

日期：2026-09-06。驱动：三引擎 2025-2026 全景 recall eval
（`docs/design/recall_eval_2025_2026/recall_eval.md`：2886 CVE 逐条分类，
包络内 80.2%，critical 57% 落 L0b，L2b+c+f 9.0%）+ firefox lessons §三.2
DDL 未消化项 + v3.23 遗留阶段 6 验收审计。

## 能力评估四问（阶段 0 判据，全景 eval 已回答）

1. 能否发现 → 80.2% 包络内（critical 85.1%），无覆盖面级缺口；
2. 暴露问题 → 缺口类型转为「深耕+精度」：site-isolation 检查点缺锚点 /
   JIT 根因归属无通道 / 边界声明缺两族 / 回归集缺三大族样本 /
   equivalent 档强度无提示（DDL）；
3. 修复方案 → 下表五修复，全部提示级/fixture 层，零门禁变更；
4. 四缺陷评估 → BIAS_EVAL_V3_24.md，实现期重跑。

## 缺陷清单（代码核实完成，编辑点行号实测）

| # | 缺陷（代码核实） | 修复 | 编辑点（实测） |
|---|---|---|---|
| D-1 | H4 无 site-isolation/origin-placement 检查点——L0d 412 条为包络内第三大方向，H4 现要点（reply 通道/初始化时序/平台信任模型）无「跨进程资源归因错误 origin」形态 | H4 补提示级检查点子条 | `task_templates/biz_hypothesis.md:40`（平台信任模型条）后、`:41`（H5）前 |
| D-2 | JIT 轴无根因归属条款——classify_chrome 47 条 V8 非 TC 内存缺陷 runtime/JIT 归属未知（[ambig]），v3.23 轴未定义「归属未知」处置 | JIT 轴段补提示级归属条款 | `task_templates/surface_map_domain.md:90`（轴段末条）后 |
| D-3 | 边界声明未含 UI 信任指示层/移动端平台集成层——L2b 82 + L2c 125 为每期固定产出，R2 无排除锚点 | 声明补 (d)(e) 两族 | `SKILL.md:343-344`（(a)(b)(c) 项后） |
| D-4 | 召回率回归集缺 L0b/L0d/L0c 样本——critical 57% 落 L0b、L0d 为最大单方向、L0c 为图形边界族 | fixture 追加 RECALL-002..004 | `tests/fixtures/recall_regression_set.json` entries 数组 |
| D-5 | equivalent 档结论强度未提示 real-target 抽验（firefox lessons §三.2 DDL 未消化：等价实证 1/4 被真实目标推翻） | R5 保真段补提示级句子 | `SKILL.md:281`（mechanism 档句）后 |

案例支撑来源（逐条指向会话内产物）：
- D-1：`classify_firefox.json` L0d 97 条（含 CVE-2026-74934 CanvasWebGL
  site-isolation、CVE-2025-9180 Canvas2D SOP bypass）+ `classify_chrome.json`
  L0d 274 条（Site Isolation 组件族 3066/9903/11174/17779/78903…）+
  `classify_webkit.json` L0d 41 条（沙箱/SOP/CSP 簇 21 条干净条目）；
- D-2：`classify_chrome.json` 47 条 V8 非 TC [ambig]（分类观察 3）+
  `classify_webkit.json` L1a 仅 2 条实证材料稀薄（观察 4）；
- D-3：`recall_eval.md` §2.2/§4（L2b 82 + L2c 125，0/8 critical 形态）；
- D-4：`recall_eval.md` §2.3（critical 188 条中 L0b 107=57%）；
- D-5：`/root/firefox/.audit_results/lessons.md` §三.2（real-target 验证轮，
  H3-F1 等价实证被真实目标反证，四取三）。

## 裁除裁决（义务三问/取证）

| # | 候选 | 理由 |
|---|---|---|
| C-1 | H3 假说义务化深耕 | 无新触发条件（三问①）；H3 要点（回调持引用/池复用）已覆盖 L0b 全部机制形态——Chrome 106 条 critical UAF 的 desc 形态无一超出；critical 占比是选题优先级信号而非假设族缺口 |
| C-2 | L2a 度量改进 | 公告粒度问题（Chrome 351 条粗标签）；修复路径是外部数据工程（bug tracker 明细联动），非 skill 机制 |
| C-3 | 内部组件专项（L2d 263 条） | 攻击面分类非机制缺口——完整代码库审计时 R1 表面测绘天然覆盖 telemetry/devtools/updater 协议端点 |
| C-4 | 移动平台分支/产品线扩展 | 使命外（WKWebView 集成层）；L2c 125 条占比 4.3% 且低危；产品线扩展另议不阻塞主线 |

## DDL 消化状态（2026-09-06，SWR-V3.21-003 条款）

- v8 lessons：全部已消化——§对 skill 1-5→v3.18/3.19 期，实证复活波追记
  1/3/4→v3.19-003/005/006（v3.23 取证复核确认在位），召回复盘 1→v3.23 D-2..D-5 ✓
- WebKit lessons：全部已消化——§一→v3.18 前身，§一补 5/6→v3.20、7/8/9→v3.21 ✓
- firefox lessons：§一/§一补→v3.22（消化状态已在 lessons 文件内标注）✓；
  §三.1→v3.23 D-1 ✓；**§三.2→本轮 D-5 入库** ✓
- v3.23 遗留：阶段 6 验收审计未跑 → 本周期任务 #55 执行（优先 coverage-ledger
  缺口格，REQ-V3.4-008）✓

## 测试守卫约束

- `tests/test_v324.py`：每个 SWR ≥1 用例含反面分支（提示级不自动改写/无约束零输出类）；
- 版本守卫：`workflow_export.py TOOLING_VERSION` 3.23→3.24，14 个测试文件版本断言行同步
  （仅 `TOOLING_VERSION == "3.xx"` 断言行；SWR-V3.23-xxx 历史 ID 字符串不动）；
- 去项目化：新增运行时文本（D-1/D-2/D-3/D-5 插入句）与 fixture 新条目
  （除 case_source 外）零项目 token——test_v324 内新增扫描断言；
- 兼容性：旧队列复跑零新增告警（v8/WebKit/firefox assert_ledger），
  test_v323 九用例全绿（RECALL-001 结构未动）。

## 开发序列

P1 无（本轮无判定函数/守卫条件级机械缺陷——全为内容文本与 fixture）→
P3 内容五处 + fixture 追加 → P4 版本链五件 → 阶段 4 测试验收 → 阶段 5 安装提交 →
阶段 6 验收审计。

## 验证命令

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q                      # 全量回归
python3 tests/test_v324.py                        # 新用例
# 旧队列复跑（零新增告警）:
python3 tools/batch_verify.py /root/v8 --stage assert-ledger 2>&1 | tail -3
# （WebKit/firefox 同形）
bash install.sh                                   # 阶段 5
```
