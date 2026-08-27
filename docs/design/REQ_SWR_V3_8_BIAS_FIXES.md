# v3.8 偏向性修复 — 系统方案 / 系统需求 / 软件方案 / 软件需求

> 输入: [BIAS_EVAL_V3_8.md](BIAS_EVAL_V3_8.md)（Top15 语言 × 10 维度偏向性评估）。
> 本文件只收评估收敛出的 **5 个修复项（F1-F5）**；不修项 N1-N5 及理由见评估报告，
> 不重复。

## 一、系统方案

**目标**: 消除语言偏向缺口与识别层内部一致性矛盾，不新增任何语言专属逻辑。

**设计纪律（评估同款四条）**:
- C1 通用性: 修复全部是语言中立机制（扩展名集合/文件名清单/token 库）——不写
  任何语言的专属 API 逻辑，不带入审计史项目名。
- C2 最小性: 5 文件、11 行级改动、零删除、零新机制；SQL 只补识别层不虚构
  深度资产（词族/手册/验证段按需增长，硬凑即「无用逻辑」）。
- C3 可落地: 每 SWR = 代码 + 回归测试。
- C4 无死代码: C1 顺带消除 size_tier 与 CODE_EXTENSIONS 的重复集合（单事实源）。

**已裁决接受的设计副作用**（记录在案）: .sql 进入识别层后，含 SQL 文件的混合仓库
会被语言清单计为第二语言 → R1 可能多派一个 boundary 域任务。这是识别层支持的
诚实代价（SQL 文件确是 storage_input 面），空 boundary 域是合法签收产出；
不为压制该信号做 SQL 专属目录排除（违反 C1）。

## 二、系统需求 (REQ)

| id | 需求 | 来源 |
|---|---|---|
| REQ-V3.8-C1 | size_tier 与 CODE_EXTENSIONS 单事实源——C++/objc 源码计入规模档位 | BIAS_EVAL F1（C++ top-2 被低估） |
| REQ-V3.8-C2 | .sql 进入语言识别层（CODE_EXTENSIONS + _EXT_LANG）——SQL 脱离 top-15 全盲 | BIAS_EVAL F2 |
| REQ-V3.8-C3 | _EXT_LANG 与 EXT_LANG_ALIAS 对齐（.m/.mm→objc）——消除识别层内部矛盾 | BIAS_EVAL F3 |
| REQ-V3.8-C4 | 构建清单补 5 名：.csproj/.sln/build.sbt/build.gradle.kts/tsconfig.json | BIAS_EVAL F4 |
| REQ-V3.8-C5 | LISTEN_PATTERN 补 3 个框架通用 token：ServerBootstrap/embeddedServer/bindAndHandle | BIAS_EVAL F5 |

## 三、软件方案

| REQ | 文件 → 函数 | 改动 |
|---|---|---|
| C1 | surface_mapper.py → size_tier | 内联扩展名集合 → `from signature_matcher import CODE_EXTENSIONS`（language_inventory 同款写法） |
| C2 | signature_matcher.py → CODE_EXTENSIONS；tools/batch_verify.py → _EXT_LANG | 各补 `.sql`（仅识别层，不加 L2/手册/验证段） |
| C3 | tools/batch_verify.py → _EXT_LANG | 补 `.m`/`.mm` → objc（与 signature_matcher.EXT_LANG_ALIAS 一致） |
| C4 | surface_mapper.py → BUILD_FILES | 补 5 个文件名（沿用既有根目录精确名 + 小写变体匹配语义） |
| C5 | tools/target_kind.py → LISTEN_PATTERN | 补 3 token（与既有 axum::serve/hyper::Server 同类：框架服务器构建 API） |

## 四、软件需求 (SWR)

| id | 可测断言 | 测试落点 |
|---|---|---|
| SWR-V3.8-020 | 150 个 .cpp 文件的仓库 → tier=medium（修复前 0 文件计入 → small） | tests/test_v38.py |
| SWR-V3.8-021 | `.sql` ∈ CODE_EXTENSIONS；language_inventory 识别 .sql 文件 | tests/test_v38.py |
| SWR-V3.8-022 | _EXT_LANG[".sql"]=="sql"、[".m"]=="objc"、[".mm"]=="objc" | tests/test_v38.py |
| SWR-V3.8-023 | 5 个新构建文件名各被 build_architecture_context 检出 | tests/test_v38.py |
| SWR-V3.8-024 | LISTEN_PATTERN 命中 3 个新 token 形态 | tests/test_v38.py |

## 五、验收

- `pytest tests/` 全绿（基线 233 + 5 组新用例）。
- 既有 fixture 行为零变化（无删除、无既有条目修改）。
