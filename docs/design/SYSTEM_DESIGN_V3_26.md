# SYSTEM_DESIGN_V3.26 — P0 交付链与防漂移机制修复

## 变更边界不变式（与既往周期一致）

- **不改阶段骨架**（R0-R5 + 六门禁结构零改动）
- **不改六门禁 ①-⑧ 判据语义**（零改动）
- **不改队列数据模型主体**（verify_queue/hypotheses/input_surface 字段零改动）
- **不改运行时模块**（surface_mapper/signature_lib/signature_matcher/
  evidence_ledger/harness_runner/workflow_export/checklist_binder/
  precedent_library/r2_guard/lessons_recorder/generation_registry/
  language_issue_matrix + tools/batch_verify + tools/target_kind +
  tools/target_profile 共 15 个运行时文件的业务逻辑零改动；
  workflow_export 仅 TOOLING_VERSION 常量前进，属版本链）

## 模块影响面

| 文件 | 改动 | 性质 |
|---|---|---|
| install.sh | 新增 `check_git_clean()` + `--allow-dirty` 参数解析 | 交付链守卫 |
| tests/test_doc_lint.py | 追加 2 用例（SWR-002/003） | 防漂移网补孔 |
| tests/test_v326.py | 新建（SWR-001 三用例 + TOOLING 守卫登记） | 回归守卫 |
| SKILL.md | :980 引用标注（SWR-002）+ v3.26 增量段（版本链） | 规格注记 |
| workflow_export.py | :22 TOOLING_VERSION 3.25→3.26 | 版本链 |
| tests/test_v310/312/313/314/315/316/317/318/319/320/3210/322/323/324/325/39.py | `we.TOOLING_VERSION == "3.25"` → `"3.26"` ×16 处 | 版本链守卫同步 |
| tools/gen_tracking.py | VERSIONS 登记 ("V3.26", REQ_V3_26, SWR_V3_26) | 版本链 |
| docs/design/REQUIREMENTS_TRACKING.md | V3.26 手工段追加（禁 gen_tracking 再生成） | 版本链 |
| resources/issue_coverage_matrix.json | 提交入库（前周期欠账数据） | 实例清理 |
| REQUIREMENTS_TRACKING.md（根） | 删除 | 实例清理 |

## 兼容性

- 运行时行为零变更 → 旧队列复跑（v8/firefox/WebKit/MaintainWise）
  assert_ledger 输出必须与变更前逐条一致（零新增 warn/blocking）
- 资产计数零变更（无新签名/先例/清单/模板/手册）→ test_asset_counts_current
  不变
- 去项目化零变更（无项目名入运行时正文；SKILL.md 标注仅提兄弟 skill 名）
  → test_deproject_assets.py 不变
- Mode W / Mode A' 双通道零影响

## 回退路径

- SWR-001 守卫异常阻塞时：`--allow-dirty` 或删除 install.sh 中
  `check_git_clean` 调用段即恢复 v3.25 行为（单点可逆）
- SWR-002/003 测试守卫误报时：对应 test_doc_lint 用例单点移除即回退
  （零运行时耦合）
