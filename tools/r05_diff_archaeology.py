#!/usr/bin/env python3
"""
R0.5 安全修复差异考古工具 (REQ-25 / SYSTEM_DESIGN.md §4.6)

利用目标 repo 的 git 历史, 将"安全修复 commit 的 diff"转化为漏洞特征,
定位规则库无法表达的语义逻辑缺陷 (如 fastjson2 checkAutoType hash 白名单绕过)。

用法:
    python3 r05_diff_archaeology.py <repo> [--tag <tag-or-commit>] [--grep <kw>]
    python3 r05_diff_archaeology.py <repo> --tag 2.0.62 --grep "autotype|rce|security"

输出:
    JSON 到 stdout 或 --output 文件; 含每个安全 commit 的 {sha, subject, files,
    added_guards(新增校验特征), removed_paths(被删/弱化路径)}。
    疑似未修复特征由主 Agent 依据 commit message + diff 判定后, origin=R05 入 R3。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_GREP = "security|autotype|rce|bypass|cve|deny|fix|safe|exploit|gadget|hardening|sanitize"

# 特征关键词: diff 中出现的校验/授权/边界相关线索
GUARD_HINTS = [
    "validate", "check", "guard", "deny", "whitelist", "blacklist", "allow",
    "limit", "cap", "bound", "length", "max", "sanitize", "reject",
    "authoriz", "permission", "illegal", "forbid", "size_t", "overflow",
]
REMOVAL_HINTS = ["remove", "delete", "drop", "weaken", "bypass", "allow"]


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def _is_ancestor(repo, commit, tag):
    p = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                        commit, tag], capture_output=True)
    return p.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="R0.5 security-fix-diff archaeology")
    ap.add_argument("repo", help="目标 git 仓库路径")
    ap.add_argument("--tag", default=None, help="限定到该 tag/commit 之前的历史")
    ap.add_argument("--grep", default=DEFAULT_GREP, help="commit message 关键词正则")
    ap.add_argument("--grep-tier", choices=["security", "fix", "all"], default="all",
                    help="SWR-V3-064: security=严格安全词 / fix=通用修复词 / all=全部")
    ap.add_argument("--output", "-o", default=None,
                    help="输出 JSON 文件路径 (默认 .audit_results/r05_diff_archaeology.json)")
    ap.add_argument("--cross-tags", default=None,
                    help="SWR-V3-060: 逗号分隔 tag 列表, 输出修复 commit 是否在各 tag 的矩阵")
    ap.add_argument("--head-mode", action="store_true",
                    help="SWR-V3-062: HEAD 审计变体复核模式 (全部修复为 HEAD 祖先时标注)")
    args = ap.parse_args()

    repo = Path(args.repo)
    if not (repo / ".git").exists():
        # SWR-V3-061: 无 git 历史输出 NO_GIT 状态 (而非误导性文本)
        out = {"status": "NO_GIT", "stage": "R0.5", "repo": str(repo),
               "skipped_reason": "no git history available"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    log_range = [args.tag] if args.tag else []
    tier_grep = args.grep
    if args.grep_tier == "security":
        tier_grep = r"secur|CVE-|RCE|bypass|injection|travers|overflow|out-of-bounds|use-after-free"
    elif args.grep_tier == "fix":
        tier_grep = args.grep or r"fix|bug"
    log = git(repo, "log", "--oneline", "--grep", tier_grep, "--regexp-ignore-case",
              "--extended-regexp",
              *(log_range + ["--"] if log_range else ["--"]))
    if not log:
        print('[R0.5] 无匹配安全关键词的 commit (或 tag 不存在)', file=sys.stderr)
        return 0

    results = []
    for line in log.splitlines():
        parts = line.split(" ", 1)
        sha = parts[0]
        subject = parts[1] if len(parts) > 1 else ""
        # 定位 parent (可能为空 = 根提交)
        parents = git(repo, "rev-parse", f"{sha}^").splitlines()
        parent = parents[0] if parents else ""
        diff_stat = git(repo, "diff", parent, sha, "--stat") if parent else ""
        diff_text = git(repo, "diff", parent, sha, "--", "*.php", "*.java", "*.go", "*.c", "*.cc", "*.h", "*.py", "*.js", "*.swift")
        added_guards = []
        removed_paths = []
        if diff_text:
            for line in diff_text.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    if any(h in line.lower() for h in GUARD_HINTS):
                        added_guards.append(line[1:].strip()[:160])
                if line.startswith("-") and not line.startswith("---"):
                    if any(h in line.lower() for h in REMOVAL_HINTS):
                        removed_paths.append(line[1:].strip()[:160])
        results.append({
            "sha": sha,
            "subject": subject,
            "parent": parent or None,
            "files_changed": len(diff_stat.splitlines()) - 1 if diff_stat else 0,
            "diff_stat": diff_stat[:800],
            "added_guards": added_guards[:20],
            "removed_paths": removed_paths[:20],
            "hint": subject,
        })
        print(f"[R0.5] {sha[:8]} {subject}  (+{len(added_guards)} guards)", file=sys.stderr)

    out = {
        "stage": "R0.5",
        "repo": str(repo),
        "tag": args.tag,
        "grep": args.grep,
        "grep_tier": args.grep_tier,
        "commit_count": len(results),
        "results": results,
        "note": "疑似未修复特征: 主 Agent 依据 added_guards/removed_paths 判定目标版本是否含该漏洞特征, origin=R05 入 R3。",
    }
    if args.cross_tags:
        tags = [t.strip() for t in args.cross_tags.split(",") if t.strip()]
        matrix = []
        for r in results:
            row = {"sha": r["sha"], "subject": r["subject"][:70]}
            for t in tags:
                # git merge-base --is-ancestor <commit> <tag> → 0=在 tag 内
                row[f"in_{t}"] = _is_ancestor(repo, r["sha"], t)
            matrix.append(row)
        out["cross_tags"] = {"tags": tags, "matrix": matrix,
                             "note": "SWR-V3-060: in_<tag>=true 表示修复 commit 在该 tag 内; "
                                     "发行版未含修复时 in_<tag>=false"}
    if args.head_mode:
        out["head_mode"] = {
            "mode": "variant_recheck",
            "note": "SWR-V3-062: 全部匹配 commit 为 HEAD 祖先; 价值在兄弟路径残留同类缺陷的变体复核",
        }
    if not args.output:
        default_dir = repo / ".audit_results"
        default_dir.mkdir(exist_ok=True)
        args.output = str(default_dir / "r05_diff_archaeology.json")
    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[+] Wrote {args.output}", file=sys.stderr)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
