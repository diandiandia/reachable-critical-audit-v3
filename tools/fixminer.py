#!/usr/bin/env python3
"""fixminer — 安全修复挖掘器 (v3.32, SWR-V3.32-002)。

从目标仓库 git 历史挖掘近期安全修复 commit 并按账本族分类——修复 commit 是
该代码库缺陷形态的 ground truth, 输出供 R2 修复驱动假设步骤消费 (提示级:
只挖不判, 假设由主代理生成)。

用法:
    python3 tools/fixminer.py <project> [--since N]
    N 默认 180 (天)。无 git 历史 → {"status": "NO_GIT"} exit 0。

关键词分级纪律 (同 SKILL_LESSONS_C §1.4.5): security 词净分 = 安全词命中数
- 通用 fix 词命中数; 净分 > 0 才入选 (避免 1688 commit 全被标安全相关的
历史教训)。family 经覆盖账本 cwe 关键词映射 (账本族名, 单一事实源)。
"""
import json
import os
import re
import subprocess
import sys

SECURITY_WORDS = ("security", "cve", "overflow", "out-of-bounds", "out of bounds",
                  "use-after-free", "use after free", "inject", "xss", "escape",
                  "deserialize", "validate", "validation", "bounds", "crash",
                  "dos", "leak", "permission", "auth", "sanitize", "traversal",
                  "double-free", "double free", "oob", "uaf", "underflow",
                  "null-deref", "null deref", "race")
GENERIC_FIX_WORDS = ("typo", "style", "refactor", "doc", "docs", "test", "tests",
                     "ci", "format", "comment", "cleanup", "nit", "chore",
                     "readme", "build", "lint", "cosmetic", "rename", "whitespace")

# 族关键词映射 (账本族名; 与 tools/batch_verify fam_map 同源语义)
_FAMILY_KEYWORDS = {
    "MEMORY-SAFETY": ("overflow", "out-of-bounds", "out of bounds", "oob",
                      "use-after-free", "use after free", "uaf", "double-free",
                      "double free", "null-deref", "null deref", "underflow"),
    "INJECTION": ("inject", "xss", "escape", "deserialize", "traversal",
                  "command", "sql"),
    "RESOURCE-DOS": ("dos", "crash", "leak", "exhaust", "unbounded"),
    "AUTHN": ("permission", "auth", "access-control", "bypass"),
    "RACE": ("race",),
    "DATA-INTEGRITY": ("validate", "validation", "sanitize"),
}

# SWR-V3.33-008 (D-8): 文件路径信号——subject 关键词净分为零但改动落在安全
# 敏感路径的修复 commit (召回上限实录: 无安全关键词的修复漏采)。低权重加分,
# 净分>0 入选门槛与 GENERIC_FIX_WORDS 精度护栏不变。
_PATH_SIGNAL_PATTERNS = ("crypto", "crypt", "tls", "ssl", "auth", "permission",
                         "parser", "decode", "deserialize", "memory", "alloc",
                         "unsafe", "secure", "sanitize", "validate", "bounds",
                         "token", "cookie", "certificate")


def _path_score(files):
    blob = " ".join(files).lower()
    return 1 if any(p in blob for p in _PATH_SIGNAL_PATTERNS) else 0


def _security_score(text):
    t = text.lower()
    sec = sum(1 for w in SECURITY_WORDS if w in t)
    gen = sum(1 for w in GENERIC_FIX_WORDS if w in t)
    return sec - gen


def _family_of(subject, files):
    blob = (subject + " " + " ".join(files)).lower()
    for fam, kws in _FAMILY_KEYWORDS.items():
        if any(k in blob for k in kws):
            return fam
    return "OTHER"


def run(project, since_days=180):
    try:
        r = subprocess.run(["git", "-C", project, "rev-parse", "--git-dir"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {"status": "NO_GIT", "project": project}
        # D-8: --stat 与 log 单次合并——路径信号通道需要文件清单, 逐 commit
        # git show 对 180 天窗口大仓不可行 (数千次子进程); 单次 log --stat
        # 输出中 "\t" 行 = 提交头 (%h\t%s), " | " 行 = 文件统计。
        r = subprocess.run(
            ["git", "-C", project, "log", f"--since={since_days}.days",
             "--stat", "--pretty=format:%h\t%s"],
            capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"status": "NO_COMMITS", "project": project}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"status": "GIT_ERROR", "error": str(e)}

    fixes = []
    fam_counts = {}
    path_signal_count = 0
    cur = None          # (hash, subject)
    cur_files = []
    def _flush():
        nonlocal cur, cur_files, path_signal_count
        if cur is None:
            return
        h, subject = cur
        ps = _path_score(cur_files)
        # D-8: 入选判据 = subject 关键词净分 + 路径信号 (低权重加分), >0 才入选
        if _security_score(subject) + ps <= 0:
            cur, cur_files = None, []
            return
        fam = _family_of(subject, cur_files)
        fam_counts[fam] = fam_counts.get(fam, 0) + 1
        if ps:
            path_signal_count += 1
        fixes.append({"hash": h, "subject": subject[:120],
                      "files": cur_files[:8], "family": fam,
                      "path_signal": bool(ps)})
        cur, cur_files = None, []
    for line in r.stdout.splitlines():
        if "\t" in line:
            _flush()
            h, subject = line.split("\t", 1)
            cur, cur_files = (h, subject), []
        elif "|" in line:
            cur_files.append(line.strip().split()[0])
    _flush()
    return {"status": "OK", "project": project, "since_days": since_days,
            "fix_commits": fixes, "families": fam_counts,
            "path_signal_count": path_signal_count}


def main(argv):
    if not argv:
        print("usage: python3 tools/fixminer.py <project> [--since N]",
              file=sys.stderr)
        return 2
    project = argv[0]
    since = 180
    if len(argv) >= 3 and argv[1] == "--since":
        since = int(argv[2])
    out = run(project, since)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
