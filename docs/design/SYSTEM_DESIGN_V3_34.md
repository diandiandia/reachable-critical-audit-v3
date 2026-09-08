# SYSTEM_DESIGN_V3_34: 文件分层重构

## 变更动机

v3.1 起 12 个运行时模块 + 5 类资产目录平铺于仓库根 (16 顶层文件 + 7 顶层目录),
版本链 20+ 周期后职责分层不可读: 运行时机制、流程编排、知识资产、测试、文档
混在同层, 新贡献者无法从结构推断依赖方向。用户裁定: 按逻辑分层重组 +
刷新设计文档写清上下层关系。

## 变更边界不变式

**纯移动 + 纯派生修复**: 零运行时语义变化、零机制改动、零门禁判据变化。
550 用例全绿 = 语义等价性证明。资产内容逐字节不变 (git mv 验证)。

## 分层架构 (详见 FILE_LAYOUT_V3_34.md)

```
L0 契约层   SKILL.md / README.md / install.sh
L1 运行时   src/  (12+1 模块: _paths 单一事实源 + 审计引擎)
L2 编排层   tools/ (5 CLI)
L3 资产层   assets/ (resources/task_templates/templates/harness_manuals/lessons)
L4 验证层   tests/ (fixtures 回归锚点)
L5 文档层   docs/ (design/history/legacy)
```

依赖方向铁律: L2→L1 单向 import; L1/L2 只读 L3; L4 是消费者不改运行时;
L0 引用下层相对路径。

**允许的例外 (唯一)**: L1 workflow_export → L2 batch_verify (Mode W 脚本导出
需复用队列编排逻辑, 且其运行上下文由 L2 转调建立)。其余 L1→L2 边一律禁止。

## 模块影响面 (v3.33 → v3.34 diff)

| 文件 | 变更 |
|---|---|
| 顶层 12 .py → src/ | 资源路径派生改经 src/_paths.py (单一事实源) |
| 顶层 5 资产目录 → assets/ | 同上 + deproject 扫描基座改 ASSETS_DIR |
| tools/*.py | sys.path 增 src 层; workflow_export 路径改 src/; 资源路径改 assets/resources |
| tests/*.py | bootstrap 增 src 层; 资产路径引用改 assets/ 前缀 |
| install.sh | 拷贝清单改四目录 (src/tools/assets/tests) 形态 |
| SKILL.md / README.md | 21 处命令引用 / 布局说明同步 |
| 新增 src/_paths.py | 分层路径单一事实源 (代码锚点) |
| 新增 docs/design/FILE_LAYOUT_V3_34.md | 文件层级权威参考 |

## 兼容性

- 安装副本 (skill 目录) 与开发仓库同构 (install.sh 拷贝四层)——
  SKILL.md 内 `<skill_dir>/src/...` 引用在两种上下文一致。
- 旧队列/旧审计产物零影响 (运行时语义不变, servo 旧队列复跑 blocking=0)。
- v2.1 遗产 docs/legacy/ 不动。

## 版本链

TOOLING_VERSION → 3.34; 测试守卫 ×24 → 3.34; SKILL.md v3.34 增量段;
REQUIREMENTS_TRACKING 手工段; gen_tracking VERSIONS 登记; 本设计件 + FILE_LAYOUT。
