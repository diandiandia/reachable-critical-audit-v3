#!/usr/bin/env python3
"""R6 lessons_recorder — 审计完成后自动生成代码审计问题文档 (v3.2 新增)。

职责: 从 .audit_results/ 产物中机械提取 skill 流程问题证据, 生成
lessons/SKILL_LESSONS_<project>_<date>.md 骨架; 过程级观察(agent 行为/工具链
陷阱)由主代理补充后提交。索引 lessons/README.md 自动更新。

满足: REQ-V3.2-060 (lessons 回写强制), REQ-V3.2-061 (证据机械提取 + 索引)。

用法:
    python3 lessons_recorder.py <project_root>            # 提取预览 (不落盘)
    python3 lessons_recorder.py <project_root> --write    # 生成 lessons 文档
"""
import json
import os
import sys

SKILL_ROOT = os.path.dirname(os.path.abspath(__file__))
LESSONS_DIR = os.path.join(SKILL_ROOT, "lessons")


def collect(project_root):
    """SWR-V3.2-080: 从审计产物机械提取问题证据。返回 {project, issues[]}。"""
    d = os.path.join(project_root, ".audit_results")
    project = os.path.basename(project_root.rstrip("/"))
    issues = []
    # 1. verify_queue.json: 裁决纠正/复活/裁决注记
    try:
        q = json.load(open(os.path.join(d, "verify_queue.json")))
    except Exception:
        q = {}
    for c in q.get("candidates", []):
        cid = c.get("id")
        for rec in (c.get("correction_record") or []):
            issues.append({
                "stage": "R3.5",
                "kind": "verdict_correction",
                "detail": f"{cid}: {str(rec)[:300]}"})
        adj = c.get("r35_adjudication") or {}
        if adj.get("demote"):
            issues.append({"stage": "R3.5", "kind": "demotion",
                           "detail": f"{cid}: {adj.get('adjudication', '')[:200]}"})
        if adj.get("strengthened"):
            issues.append({"stage": "R3.5", "kind": "strengthened",
                           "detail": f"{cid}: {'; '.join(str(s)[:120] for s in adj['strengthened'][:2])}"})
        if adj.get("attribution_corrections"):
            issues.append({"stage": "R3.5", "kind": "attribution_correction",
                           "detail": f"{cid}: {str(adj['attribution_corrections'][0])[:200]}"})
        # v3.2.2 (REQ-V3.2.2-015): resurrection_review lenient 加载——
        # 契约形态是候选级 dict{revived,outcome}; str/list 落盘曾崩溃 (mbedtls 实测)
        rr = c.get("resurrection_review") or {}
        if isinstance(rr, str):
            rr = {"revived": False, "outcome": rr}
        elif isinstance(rr, list):
            rr = {}
        if isinstance(rr, dict) and rr.get("revived"):
            issues.append({"stage": "R3.5-N", "kind": "resurrection",
                           "detail": f"{cid}: {rr.get('outcome', '')[:200]}"})
        if c.get("grade_recomputed_by"):
            issues.append({"stage": "R3", "kind": "grade_recomputed",
                           "detail": f"{cid}: 机械分级重算 ({c['grade_recomputed_by'][:80]})"})
        if c.get("paraphrased"):
            issues.append({"stage": "R3", "kind": "paraphrased_evidence",
                           "detail": f"{cid}: 证据被标记 paraphrased"})
    if q.get("adjudication_note"):
        issues.append({"stage": "裁决", "kind": "adjudication_note",
                       "detail": q["adjudication_note"][:400]})
    if q.get("target_kind"):
        issues.append({"stage": "R0", "kind": "target_kind",
                       "detail": f"审计目标类型 = {q['target_kind']}"})
    # 2. R1 修复统计 (repair stats 若已落盘)
    try:
        stats = json.load(open(os.path.join(d, "repair_stats.json")))
    except Exception:
        stats = None
    if stats:
        issues.append({"stage": "R1", "kind": "repair_stats",
                       "detail": json.dumps(stats, ensure_ascii=False)})
    # 3. 门禁违规历史
    try:
        gates = json.load(open(os.path.join(d, "_phase313", "acceptance.json")))
    except Exception:
        gates = None
    if gates:
        issues.append({"stage": "验收", "kind": "acceptance",
                       "detail": json.dumps(gates, ensure_ascii=False)[:400]})
    return {"project": project, "issues": issues}


def render(project_root, process_notes=None):
    """SWR-V3.2-081: 生成 lessons 文档。process_notes 由主代理补充
    (agent 行为/工具链/workflow 缺陷——非结构化过程观察)。"""
    from datetime import date
    data = collect(project_root)
    project = data["project"]
    today = date.today().isoformat()
    lines = [f"# SKILL Lessons — {project}（{today}）", "",
             "> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。", "",
             "## 审计统计（自动提取）", ""]
    by_stage = {}
    for i in data["issues"]:
        by_stage.setdefault(i["stage"], []).append(i)
    for stage in sorted(by_stage):
        lines.append(f"### {stage}")
        for i in by_stage[stage]:
            lines.append(f"- [{i['kind']}] {i['detail']}")
        lines.append("")
    if process_notes:
        lines += ["## 主代理过程观察（人工补充）", ""]
        lines += [f"- {n}" for n in process_notes]
        lines.append("")
    lines += ["## 待回填", "",
              "- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；",
              "  低价值条目保留在本文件作为审计轨迹。", ""]
    return "\n".join(lines), data


def write_lesson(project_root, process_notes=None):
    """SWR-V3.2-081: 落盘 lessons 文档 + 索引更新。返回文件路径。"""
    body, data = render(project_root, process_notes)
    project = data["project"]
    os.makedirs(LESSONS_DIR, exist_ok=True)
    out = os.path.join(LESSONS_DIR, f"SKILL_LESSONS_{project}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    # 索引更新
    idx_path = os.path.join(LESSONS_DIR, "README.md")
    from datetime import date
    row = f"| [SKILL_LESSONS_{project}.md](SKILL_LESSONS_{project}.md) | 自动 | {project} | {date.today().isoformat()} | R6 机械生成: {len(data['issues'])} 条问题证据 |"
    if os.path.exists(idx_path):
        content = open(idx_path, encoding="utf-8").read()
        if f"SKILL_LESSONS_{project}.md" not in content:
            content += row + "\n"
            open(idx_path, "w", encoding="utf-8").write(content)
    return out


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    if "--write" in argv:
        notes = None
        out = write_lesson(root, notes)
        print(f"lesson written: {out}")
        _, data = render(root)
        print(f"extracted {len(data['issues'])} issues")
        return 0
    body, data = render(root)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
