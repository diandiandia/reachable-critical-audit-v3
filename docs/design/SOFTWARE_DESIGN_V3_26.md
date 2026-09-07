# SOFTWARE_DESIGN_V3.26 — P0 交付链与防漂移机制修复

## P 分层序列

```
P1 实例清理：D-4 覆盖账本提交 + D-5 根 tracking 删除（独立 commit）
P2 机制修复：D-1 install.sh 守卫 + D-2/D-3 doc-lint 测试 + SKILL.md:980 标注
P4 版本链：TOOLING 3.26 + 守卫 ×16 + SKILL.md 增量段 + tracking 手工段
          + gen_tracking 登记
```

## 函数级设计

### P2-1：install.sh — check_git_clean()（SWR-V3.26-001）

```
install.sh 第 7 行（SRC/DST 探测）后插入：

ALLOW_DIRTY=0
case "${1:-}" in --allow-dirty) ALLOW_DIRTY=1; shift;; esac
DST="${1:-$HOME/.claude/skills/reachable-critical-audit}"   # 既有默认不硬编码改写

check_git_clean() {
  git -C "$SRC" rev-parse --git-dir >/dev/null 2>&1 || return 0   # 非 git 仓库跳过
  [ "$ALLOW_DIRTY" = 1 ] && return 0
  local dirty
  dirty="$(git -C "$SRC" status --porcelain)"
  [ -z "$dirty" ] && return 0
  echo "拒绝安装: dev 仓库工作树有未提交改动 (git 提交或 --allow-dirty 显式豁免):" >&2
  echo "$dirty" >&2
  exit 1
}
check_git_clean
```

设计要点：
- `set -euo pipefail` 兼容（`$(...)` 空输出不触发 -e，`local` 捕获安全）
- 非 git 仓库零误伤（install.sh 复制到无 git 环境仍可用）
- 拒绝信息带脏文件清单与豁免用法——v3.4.4-004 同款"报错指引"形态

### P2-2：test_doc_lint.py — 追加 2 用例

```python
def test_tools_file_references_resolve():
    """SWR-V3.26-002: SKILL.md 散文 tools/ 引用必须本地存在或标注兄弟 skill 交付。
    根因: check_no_cjk.py 引用歧义漏网 (SKILL.md:980, 466 测试全绿未拦截)。"""
    text = open(SKILL_MD).read()
    refs = re.findall(r"tools/([A-Za-z0-9_]+\.py)", text)
    assert refs, "SKILL.md 无 tools/ 引用"
    home = os.path.expanduser("~")
    for fname in sorted(set(refs)):
        local = os.path.join(WORKSPACE, "tools", fname)
        if os.path.exists(local):
            continue
        # 跨 skill 交付必须同行标注: 交付至 <skill-name>
        lines = [ln for ln in text.splitlines() if fname in ln]
        for ln in lines:
            m = re.search(r"交付至 ([a-z0-9-]+)", ln)
            assert m, f"tools/{fname} 不存在且行内无「交付至 <skill>」标注: {ln[:80]}"
            sibling = os.path.join(home, ".claude", "skills", m.group(1),
                                   "tools", fname)
            assert os.path.exists(sibling), f"标注目标不存在: {sibling}"

def test_tooling_version_consistent_with_skmd():
    """SWR-V3.26-003: SKILL.md 声明的 TOOLING 版本与 workflow_export 一致。
    根因: 3.7→3.9 漂移两版才被发现 (SKILL.md:979); 现查证同形态缺口仍在。"""
    import workflow_export as we
    text = open(SKILL_MD).read()
    assert f"TOOLING {we.TOOLING_VERSION}" in text, \
        f"SKILL.md 缺 TOOLING {we.TOOLING_VERSION} 声明 (版本链漂移)"
    segs = re.findall(r"^## 🆕 v([\d.]+) 增量", text, re.M)
    assert segs, "SKILL.md 无增量段"
    assert segs[-1] == we.TOOLING_VERSION, \
        f"最新增量段 {segs[-1]} ≠ TOOLING {we.TOOLING_VERSION}"
```

设计要点：
- SWR-002 标注格式机器可核验（防装饰性标注）——标注名对应
  `~/.claude/skills/<name>/tools/<f>` 真实存在才放行
- SWR-003 双断言覆盖漂移两方向：代码前进文档未动 / 增量段头未前进
- 环境纪律 #8：兄弟 skill 路径以 `~` 展开，零硬编码绝对路径

### P2-3：SKILL.md:980 标注（SWR-V3.26-002）

```
- **cve-ghsa-draft**（REQ-V3.9-012）：新 `tools/check_no_cjk.py` 零中文检查
  脚本（交付至 cve-ghsa-draft skill 目录）
```

### P3：无（本周期无任务书/清单内容义务）

### P4：版本链五件

1. workflow_export.py:22 `TOOLING_VERSION = "3.26"`
2. ×16 守卫行 `we.TOOLING_VERSION == "3.25"` → `"3.26"`
   （test_v310/312/313/314/315/316/317/318/319/320/3210/322/323/324/325/39）
   ——test_v326 新用例自带 `"3.26"` 断言，守卫数 16→17
3. SKILL.md 追加 `## 🆕 v3.26 增量` 段（列 SWR 号 + 验收判据 + "TOOLING 3.26"）
4. docs/design/REQUIREMENTS_TRACKING.md 手工追加 V3.26 段
   （禁止运行 gen_tracking 再生成）
5. tools/gen_tracking.py VERSIONS 登记
   `("V3.26", "docs/design/REQ_V3_26.md", "docs/design/SWR_V3_26.md")`

### 测试设计：test_v326.py（新文件，SWR-V3.26-001）

```python
"""SWR-V3.26: P0 交付链防漂移修复测试。
install.sh git 前置守卫三用例 (脏树拒绝/--allow-dirty 放行/干净树放行)。"""
```

- fixture：临时目录 git init → 最小 skill 布局（SKILL.md/README.md/
  13 个模块占位/docs/legacy/SKILL_V2.1.md/tools/ resources/ task_templates/
  templates/ tests/ lessons/ harness_manuals/ 空目录）→ 拷贝 install.sh 入内
- 用例 1：追加未提交文件 → `install.sh <tmpdst>` exit≠0 且 stderr 含
  "未提交改动" 与脏文件路径
- 用例 2：同状态 `install.sh --allow-dirty <tmpdst>` exit 0 且 SKILL.md 落盘
- 用例 3：全部 commit 后 `install.sh <tmpdst2>` exit 0
- 冒烟段：fixture 无 tests → install.sh 尾部 `|| echo` 分支保证 exit 0
  （既有行为，不修改）
- 版本链登记：`assert we.TOOLING_VERSION == "3.26"`
