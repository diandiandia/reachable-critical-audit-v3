# SOFTWARE_DESIGN_V3_34: 分层重构机械变更清单

## 迁移 (git mv, 零内容变化)
- 顶层 12 .py → src/; 顶层 5 资产目录 → assets/<同名>/。

## 派生修复
- src/_paths.py 新建 (SKILL_ROOT = 上溯两层; ASSETS_DIR/RESOURCES_DIR)。
- 7 模块资源路径改 _paths 派生 (lessons_recorder/generation_registry/
  checklist_binder/evidence_ledger/precedent_library/language_issue_matrix/
  harness_runner/signature_lib); signature_lib 的 fixtures 路径改 SKILL_ROOT/tests。
- workflow_export: tools 兄弟层 sys.path 修正。
- tools/*: sys.path 增 src 层 (parent/src); batch_verify 资源路径改
  assets/resources (4 处); workflow_export 路径改 src/ (2 处)。
- tests/*: bootstrap 增 src 层 (统一正则补全后单次重插, 防多轮 sed 重复);
  资产路径引用改 assets/ 前缀 (变量形态 ROOT/WORK/WORKSPACE/dirname 全清查);
  test_v326 fixture 布局改四目录形态。
- install.sh: 拷贝清单改 src/tools/assets/tests 四目录 + 清理循环同步。
- SKILL.md: 21 处命令引用重写 (模块 src/ 前缀 + 资产 assets/ 前缀 + R6 段 +
  附录布局段); README.md 同步。

## 版本链
TOOLING 3.34; 守卫 ×24; SKILL.md v3.34 增量段; tracking 手工段;
gen_tracking VERSIONS 登记; FILE_LAYOUT_V3_34 + SYSTEM_DESIGN_V3_34。
