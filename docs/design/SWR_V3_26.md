# SWR_V3.26 — P0 交付链与防漂移机制修复

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.26-001 | install.sh 安装前置：SRC 为 git 仓库且工作树脏（`git status --porcelain` 非空）时**拒绝安装**，输出脏文件清单与 `--allow-dirty` 豁免用法；`--allow-dirty` 显式放行；非 git 仓库跳过检查 | D-1。拒绝级（非 warn）依据：v3.16 账本漂移 warn（43f157a）后 v3.22 仍复发（99eb060），warn 级对漂移无效的复发史实证；豁免通道防误伤开发期快速安装；无自动改写 | test_v326 三用例：脏树拒绝（exit≠0 + 清单输出）/ `--allow-dirty` 放行（exit 0 + 文件落盘）/ 干净树放行 |
| SWR-V3.26-002 | doc-lint 覆盖散文文件引用：SKILL.md 全部 `tools/<f>.py` 引用必须本地 tools/ 存在，或同行含 `交付至 <skill>` 标注且 `~/.claude/skills/<skill>/tools/<f>` 存在 | D-2。check_no_cjk 引用歧义漏网实录；标注格式机器可核验（防装饰性标注） | test_doc_lint 新用例：本仓库全部引用解析 + check_no_cjk 标注目标文件存在性 |
| SWR-V3.26-003 | SKILL.md↔TOOLING_VERSION 一致性断言：①`"TOOLING <版本>"` 串必须出现在 SKILL.md ②最新 🆕 增量段头版本号 == TOOLING_VERSION | D-3。3.7→3.9 漂移两版实录；现查证同形态缺口仍存在（"TOOLING 3.25" 全文缺失） | test_doc_lint 新用例双断言（未来版本链若只动代码不动文档即红） |
| SWR-V3.26-004 | 未提交覆盖账本数据入库（resources/issue_coverage_matrix.json） | D-4。实例清理——合法数据（python 8→37、shell +1、other 12→13 等），缺失追踪归属 | git 历史可追溯（独立 commit，message 注明欠账来源） |
| SWR-V3.26-005 | 根目录 REQUIREMENTS_TRACKING.md 删除，权威唯一化至 docs/design/ | D-5。零消费者裁除：README:206/test_v33.py:31/gen_tracking.py:146 三处权威指向 + install.sh 零引用；遗留即漂移温床（本会话实证：脱节两版） | git rm 落盘；test_doc_lint 既有计数断言不涉及该文件 |

## 义务入库三问（逐项）

- SWR-001：①触发=运行 install.sh 且 SRC 是 git 仓库；②消费者=install 执行者；③裁掉丢什么=脏树静默上运行时（本会话实证）。
- SWR-002/003：①触发=pytest 全量回归；②消费者=doc-lint 测试族；③裁掉丢什么=散文引用/版本一致性漂移静默（本会话双实例实证）。
- SWR-004/005：实例清理，无新义务。

## 修法形态纪律核对

- 无自动改写：D-1 拒绝+显式豁免，不自动 commit/不自动 stash ✓
- 已有机制不重造：D-2/D-3 落在既有 doc-lint 测试族上扩展，不建新 lint 体系 ✓
- 无新门禁名/新阶段/新审计义务：全部为 dev 侧交付守卫与测试 ✓
