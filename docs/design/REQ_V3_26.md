# REQ_V3.26 — P0 交付链与防漂移机制修复（2026-09-07，三轮评估驱动）

> 本周期触发形态：用户以钱学森系统工程视角对 skill 本体做三轮评估
> （设计层/实现层/历史包袱与过设计），取证发现五个缺陷——全部为
> **交付链与文档一致性类**，不涉及审计运行时行为。缺陷清单如下。

## 缺陷清单（代码核实）

| # | 缺陷 | 案例支撑 | 修复 | 编辑点（实测行号） |
|---|---|---|---|---|
| D-1 | install.sh 无 git 状态前置守卫——未提交改动静默上运行时 | 本会话取证：`git status` = `M resources/issue_coverage_matrix.json` 未提交，而 dev/installed `diff -rq` 证明该未提交态已装至运行时目录；漂移类复发史 v3.16 加 warn（43f157a）→ v3.22 仍复发（99eb060），warn 级被实证不足 | 纯 bash `check_git_clean()`：SRC 为 git 仓库且 `status --porcelain` 非空 → 拒绝并输出脏文件清单 + `--allow-dirty` 豁免用法；非 git 仓库跳过（零误伤）。无自动改写（不自动 commit） | install.sh 第 7 行（SRC/DST 探测）后插入 |
| D-2 | doc-lint 网不覆盖散文文件引用——SKILL.md:980 引用 `tools/check_no_cjk.py`，本 skill tools/ 无此文件（实际交付在兄弟 skill cve-ghsa-draft），466 测试全绿未拦截 | 本会话取证：`ls tools/` 仅 4 文件 vs SKILL.md:980 引用；`ls /root/.claude/skills/cve-ghsa-draft/tools/check_no_cjk.py` 存在 | test_doc_lint 新增用例：SKILL.md 全部 `tools/<f>.py` 引用必须（本地 tools/ 存在）或（同行含 `交付至 <skill>` 标注且 `~/.claude/skills/<skill>/tools/<f>` 存在）；SKILL.md:980 补标注 | tests/test_doc_lint.py 追加 + SKILL.md:980 |
| D-3 | SKILL.md↔workflow_export.TOOLING_VERSION 一致性无断言——现查证"TOOLING 3.25"在 SKILL.md 全文不存在（当前版本即已脱节） | SKILL.md:979 实录：TOOLING_VERSION 3.7→3.9 漂移两版才被发现；本会话 grep 复证同形态缺口仍在 | test_doc_lint 断言 ①`f"TOOLING {TOOLING_VERSION}" in SKILL_MD` ②最新 🆕 增量段头版本号 == TOOLING_VERSION | tests/test_doc_lint.py 追加（①依赖 P4 增量段落盘） |
| D-4 | 未提交 `resources/issue_coverage_matrix.json`（python 8→37、shell +1 等覆盖账本回填）已安装未提交 | 本会话取证：git diff 18+/16-，内容为合法覆盖账本数据；dev==installed 已含此态 | 本分支首 commit 提交 | git commit（P1） |
| D-5 | 根目录 REQUIREMENTS_TRACKING.md 为 v3.23 时代孤儿副本，与权威脱节两版 | 本会话取证：权威路径三处证据——README:206、tests/test_v33.py:31、tools/gen_tracking.py:146 全部指向 `docs/design/`；install.sh 复制清单零引用；git log 显示根文件仅 v3.23 P4（0c6620d）触碰一次后废弃 | 删除（`git rm`）。零消费者即裁除 | git rm REQUIREMENTS_TRACKING.md（P1） |

## 召回率回归集评估（v3.23, SWR-V3.23-005 义务）

本周期缺陷全部属**交付链/文档一致性类**，回归集条目（已知真实缺陷语料的
发现力对照）属**发现力方向**——零重叠，本周期不适用；回归集将作为阶段 6
验收审计（用户提供新项目）的发现力对照输入，不裁除不排队迁移。

## DDL 消化核验（v3.21, SWR-V3.21-003 义务）

机械清单四份 lessons.md 全部已在既往周期闭环：v8（含实证复活波/召回复盘
追记）→ v3.18/v3.19/v3.23；WebKit（含一补报漏 8 条）→ v3.20/v3.21；
firefox（含一补报漏）→ v3.22/v3.23；MaintainWise（5 候选 + DDL 注记）→
v3.25（SWR-V3.25-001~006 逐条对应 lessons 第 1-5 条）。本周期无新审计
lessons 输入——消化义务状态：已闭合，零新增。

## 开发序列

1. P1 实例清理：D-4 提交 + D-5 删除
2. P2 机制修复：D-1 install.sh 守卫 + D-2/D-3 doc-lint 测试 + SKILL.md:980 标注
3. P4 版本链：TOOLING 3.26 + 守卫 ×16 同步 + SKILL.md 增量段 + tracking
   手工段 + gen_tracking VERSIONS 登记

## 验证命令

```bash
python3 -m pytest tests/ -q                     # 全量回归（466 基线 + test_v326 新增）
python3 signature_lib.py selfcheck /root/Pillow # 资产通用性不回退（非 fixture 项目）
./install.sh ~/.claude/skills/reachable-critical-audit   # 干净树安装全绿
```

## 验收判据（Phase 3.26）

全量回归全绿（466 基线 + test_v326 新增用例）+
旧队列复跑（v8/firefox/WebKit/MaintainWise）assert_ledger 零新增告警
（运行时零改动，warn 集必须与变更前逐条一致）+
install 双副本同步 + 脏树安装被拒/`--allow-dirty` 放行双分支实测。
阶段 6 验收审计：用户提供未审计新项目后执行，再判定合并主分支。
