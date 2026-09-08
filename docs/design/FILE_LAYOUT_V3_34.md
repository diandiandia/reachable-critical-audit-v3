# FILE_LAYOUT_V3_34: 仓库文件分层 (权威参考)

> v3.34 (2026-09-08) 分层重构。本文件是文件层级关系的单一权威——
> SKILL.md/README/install.sh/src/_paths.py 均按此布局推导, 改动任何层位必须同步本文。

## 一、五层总览

```
reachable-critical-audit-v3/                    (开发主仓库 = 安装源)
│
├── SKILL.md ......................... L0 契约层: 唯一面向用户/子智能体的规范入口
├── README.md ........................ L0 项目说明 (仓库结构与状态)
├── install.sh ....................... L0 安装器: 开发仓库 → skill 目录的官方通道
│
├── src/ ............................. L1 运行时核心 (审计引擎, 12+1 模块)
│   ├── _paths.py ....................   分层路径单一事实源 (本层位的代码锚点)
│   ├── surface_mapper.py ............   R0 scope / R1 输入面测绘+校验+合并
│   ├── signature_lib.py .............   R0 签名库 (完整性自检+去项目化扫描)
│   ├── signature_matcher.py .........   R2 签名匹配器 (可选佐证器)
│   ├── r2_guard.py ..................   R2 假设 schema 守卫 + 筛选保真校验
│   ├── evidence_ledger.py ...........   分级 + 六门禁断言 (唯一权威)
│   ├── language_issue_matrix.py .....   语言问题矩阵 (R2 提示 + 回填)
│   ├── lessons_recorder.py ..........   R6 lessons 机械提取+落盘
│   ├── harness_runner.py ............   R5 harness 注册表+环境探针
│   ├── checklist_binder.py ..........   清单绑定 (检查清单库消费)
│   ├── precedent_library.py .........   先例裁决库消费
│   ├── generation_registry.py .......   生成层注册表 (DSL/扩展名)
│   └── workflow_export.py ...........   Mode W 编排导出 (→ L2 消费)
│
├── tools/ ........................... L2 阶段驱动 CLI (R0-R6 流程编排)
│   ├── batch_verify.py ..............   队列编排 (collect/波次/门禁/报告)
│   ├── fixminer.py ..................   安全修复挖掘 (v3.32 修复驱动通道)
│   ├── target_kind.py ...............   R0 目标形态判定
│   ├── target_profile.py ............   R0 目标画像判定
│   └── gen_tracking.py ..............   需求追踪矩阵重建 (文档工具)
│
├── assets/ .......................... L3 知识资产 (只读数据/模板/手册/归档)
│   ├── resources/ ...................   单一事实源数据 (7 JSON)
│   │   ├── signature_library.json ...   25 签名 (9 L3 + 16 L2 词族)
│   │   ├── issue_coverage_matrix.json   覆盖账本 (批次选题判据)
│   │   ├── language_issue_matrix.json    语言×族种格 (R2 提示)
│   │   ├── language_issue_inventory.json  K1/K2 目标条目
│   │   ├── checklist_library.json ...   45 检查清单
│   │   ├── precedent_library.json ...   18 裁决先例
│   │   └── generation_registry.json .   生成层注册表
│   ├── task_templates/ ..............   子智能体任务书 (3 md)
│   ├── templates/harness/ ...........   实证模板 (7)
│   ├── harness_manuals/ .............   语言工具链手册 (18)
│   └── lessons/ .....................   战役期历史教训归档 (31, 只读追溯源)
│
├── tests/ ........................... L4 验证层 (550 用例 + fixtures)
│   └── fixtures/ ....................   回归锚点 (known_instances/recall_regression_set)
│
└── docs/ ............................ L5 文档层 (204)
    ├── design/ ......................   版本设计五件套 + 本文件 + tracking
    ├── history/ .....................   历史文档
    └── legacy/SKILL_V2.1.md .........   v2.1 规范备份 (唯一遗产)
```

## 二、依赖方向铁律

```
L2 (tools)  ──import──▶  L1 (src)     单向, 禁止反向
L1/L2       ──read────▶  L3 (assets)  只读, 永不写 (写侧=阶段 6 回填, 经 L1 函数)
L4 (tests)  ──import──▶  L1/L2        测试即消费者, 不改运行时
L0 (SKILL/install) 引用 L1-L5 的相对路径 (安装时整体平移)
```

违反规则的形态 (禁止):
- L1 模块 import L2 模块 (src → tools)
- 任何运行时代码写 assets/ 之外的仓库文件
- 运行时逻辑硬编码层位 (层位一律经 `src/_paths.py` 派生)

## 三、路径派生规范

- **L1 内资源**: 一律 `from _paths import ASSETS_DIR / RESOURCES_DIR / SKILL_ROOT`
  (`src/_paths.py` 由 `__file__` 上溯推导, 开发仓库与安装副本同构, 零硬编码)。
- **L2 内引用 L1**: `sys.path.insert(0, os.path.join(<仓库根>, "src"))`——
  仓库根 = `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (tools/ 一层深, 不变式)。
- **L1 内引用 L2**: workflow_export 需要 batch_verify (编排导出)——
  `sys.path.insert(0, os.path.join(<仓库根>, "tools"))`, 属 L1→L2 的唯一边——
  存在理由: Mode W 脚本导出必须复用队列编排逻辑, 且 workflow_export 运行在
  L2 编排的运行时上下文内 (由 L2 转调)。已在 BIAS_EVAL 中注明为允许例外。
- **测试**: tests/ 同时挂 `仓库根` + `src/` + `tools/` 三层路径。

## 四、v3.34 迁移记录 (自扁平结构)

| 迁移前 | 迁移后 | 层 |
|---|---|---|
| 顶层 12 个 .py | src/ | L1 |
| tools/ (5) | tools/ (不变) | L2 |
| resources/ task_templates/ templates/ harness_manuals/ lessons/ | assets/<同名>/ | L3 |
| tests/ docs/ | 不变 | L4/L5 |
| 顶层 workflow_export.py 等 | src/ | L1 |

同层改名: 无。删除: 无 (纯移动, git mv 保留历史)。

## 五、变更同步义务

- 层位变更 → 本文件 + `src/_paths.py` + SKILL.md 路径引用 + install.sh 拷贝清单
  四处必须同一提交内同步 (v3.34 教训: 四处不同步会产生静默安装漂移)。
- 新资产 (模板/手册/数据) 入库 assets/ 对应子目录, 并同步 SKILL.md 附录计数行。
