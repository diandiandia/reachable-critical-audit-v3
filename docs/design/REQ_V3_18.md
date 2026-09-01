# REQ V3.18 — 语言问题矩阵：per-language 知识基座（2026-09-01）

## 上下文

2026-09-01 会话战略评估（用户裁定方案 C）：原目标"Top15 语言 × 每语言
Top10 安全问题"的**知识资产维度 0% 建成**——resources/ 无 per-language
知识库（grep top10/owasp 零命中）；12 CWE 族 × 16 语言覆盖账本 111/192
（58%），ERROR-HANDLING/NUMERIC 两族全语言零覆盖（空壳族）。普适性维度
已超额（16 语言零覆盖语言 = 0），偏离集中在知识深度不可积累、不可问责。

本版修复方向（用户裁定）：**流程机器不动，补数据驱动的内容基座**——
`resources/language_issue_matrix.json`：16 语言 × 12 族的 per-language
条目（典型漏洞形态/关键 sink 词/判定要点/追溯），作为 R2 假设生成注入文本。
零新机制（无新门禁/无新阶段/无新强制义务/零 binder 改动），纯数据 +
一个加载器模块 + SKILL.md 条款。种格纪律：**只种有仓内案例支撑的格**
（L2 签名语义 / 清单与先例 source_lessons / SKILL.md 机制形态实录），
其余格 status=pending 诚实占位（v3.6 confirmed:false 先例）——
验收判据新增「每版本把验收项目的语言×族格回填进矩阵」（知识开始积累，
两段式入库）。

## 修复清单（3 项）

| # | 缺陷（代码核实） | 修复 | 编辑点 |
|---|---|---|---|
| D-1 | per-language 知识资产零存在——resources/ 5 文件无语言×问题映射；R2 假设生成对"该语言主要问题"的提示全部依赖 LLM 裸知识，不可问责不可积累 | 新 `resources/language_issue_matrix.json`：{langs(16, 与账本逐位一致), families(12, 与账本逐位一致), cells[]}；每条 {lang, family, status:seeded|pending, cwes[], patterns[], sinks[], pitfalls[], source_lessons[]}；首版诚实验种 ~28 格（每格 source_lessons 指向仓内证据），其余 pending | resources/language_issue_matrix.json（新） |
| D-2 | 无消费端——矩阵不接线 = 死资产 | 新 `language_issue_matrix.py` 加载器（cells/stats CLI + normalize lang 别名 cs↔csharp/ts↔javascript 与 _LANG_ALIAS 对齐）；SKILL.md R2 条款：主代理生成假设前读该语言已种格作为假设空间提示；pending 格零注入 | language_issue_matrix.py（新）、SKILL.md R2 节 |
| D-3 | 知识无积累纪律——账本记"审过"不记"懂多少"，教训只留 lessons 文本 | SKILL.md 验收判据条款：每版本把验收项目的语言×族格回填进矩阵（审计教训两段式入库，来源写 source_lessons）；R6 教训高价值条目与矩阵回填并行 | SKILL.md 验收判据/R6 节 |

## 版本链 v3.18

- workflow_export.py:22 TOOLING_VERSION → "3.18"（内容版沿惯例前进，v3.13 先例）
- SKILL.md v3.18 增量段
- 版本守卫更新：tests/test_v310.py:276、test_v312.py:180、test_v313.py:191、
  test_v39.py:266、test_v314.py:219、test_v315.py:253、test_v316.py:120 → "3.18"
- REQUIREMENTS_TRACKING.md 手工追加段（禁 gen_tracking 再生成）+
  gen_tracking VERSIONS 登记
- install.sh 模块清单补 language_issue_matrix.py

## 开发序列

- **C0**（本文档集）
- **P1 数据+加载器**：language_issue_matrix.json（种格 ~28）+ language_issue_matrix.py
- **P2 接线+版本链**：SKILL.md R2/验收判据条款 + install.sh + TOOLING/守卫/tracking
- **P3 测试+安装**：test_v318.py + 全量回归 + install.sh + 双副本 diff

## 测试守卫约束

- 必须保持绿：全量 392 基线、test_deproject_assets.py（新资产正文去项目化
  扫描由 test_v318 内 DEPROJECT_BLACKLIST 断言承载）、test_doc_lint.py
  （资产计数零变化——新资产不在计数断言集内，若守卫断言扩展则同步）
- 新增 tests/test_v318.py（约 10 用例，见 SWR 各条）

## 验证

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -q
python3 language_issue_matrix.py stats
bash install.sh
```

## 边界声明

- **不做**：新门禁/新强制义务/新阶段/binder 改动/自动绑定/把 pending 格当
  义务（pending = 零注入零提示，仅 stats 可见）；
- **案例支撑**：本会话战略评估（知识资产 0%、账本 58%、空壳族两族全零）
  + 仓内 L2 签名 16 语言语义 + 清单 source_lessons + SKILL.md 机制形态实录；
- **种格诚实纪律**：无仓内证据的格一律 pending——禁止凭 LLM 通用知识臆造
  种格（矩阵的问责性来自每格可追溯）。
