#!/usr/bin/env python3
"""从 REQ_V3(.1).md / SWR_V3(.1).md 自动提取需求编号，重新生成 REQUIREMENTS_TRACKING.md。
注意: 状态变更在 REQUIREMENTS_TRACKING.md 手工维护；本脚本用于需求文档增删后重建骨架
(会保留既有状态，仅按当前需求文档补齐/移除条目)。v3.1 需求同样纳入重建。"""
import re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCS = {
    "REQ-V3": "docs/design/REQ_V3.md",
    "SWR-V3": "docs/design/SWR_V3.md",
    "REQ-V3.1": "docs/design/REQ_V3_1.md",
    "SWR-V3.1": "docs/design/SWR_V3_1.md",
}

# v3.1 REQ 文档无逐条状态列——状态以 SWR 完成度为代理 + 验收项显式标注
REQ_V31_OVERRIDE = {
    # Phase 3.1.3 验收未开始
    "REQ-V3.1-100": "未开发", "REQ-V3.1-101": "未开发",
}

def extract(path):
    reqs = []
    for line in open(os.path.join(ROOT, path), encoding="utf-8"):
        m = re.match(r'\| (REQ-V3-\d{3}|SWR-V3-\d{3}|REQ-V3\.1-\d{3}|SWR-V3\.1-\d{3}) \| (.+?) \|', line)
        if m:
            reqs.append((m.group(1), m.group(2).strip()))
    return reqs

def load_status():
    """从既有 tracking 行加载状态 (v3 与 v3.1 都认)。"""
    status = {}
    p = os.path.join(ROOT, 'docs/design/REQUIREMENTS_TRACKING.md')
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            m = re.match(r'\| (REQ-V3-\d{3}|SWR-V3-\d{3}|REQ-V3\.1-\d{3}|SWR-V3\.1-\d{3}) \| .+? \| (未开发|开发中|已完成) \|', line)
            if m:
                status[m.group(1)] = m.group(2)
    # SWR_V3_1.md 自带状态列, 作为 SWR-V3.1 的第二状态源
    for line in open(os.path.join(ROOT, DOCS["SWR-V3.1"]), encoding="utf-8"):
        m = re.match(r'\| (SWR-V3\.1-\d{3}) \| .+? \| .+? \| (未开发|开发中|已完成) \|', line)
        if m:
            status.setdefault(m.group(1), m.group(2))
    return status

def emit_section(out, title, reqs, status, override=None):
    override = override or {}
    out.append(f'\n## {title}（共 {len(reqs)} 条）\n')
    out.append('| 编号 | 需求 | 状态 | 备注 |\n|---|---|---|---|')
    for rid, text in reqs:
        st = override.get(rid) or status.get(rid, '未开发')
        out.append(f'| {rid} | {text} | {st} |  |')

sys_v3 = extract(DOCS["REQ-V3"])
swr_v3 = extract(DOCS["SWR-V3"])
sys_v31 = extract(DOCS["REQ-V3.1"])
swr_v31 = extract(DOCS["SWR-V3.1"])
status = load_status()
# v3.1 REQ 默认态: SWR 全完成 → 已完成 (验收项除外)
v31_done = all(status.get(rid) == '已完成' for rid, _ in swr_v31)
for rid, _ in sys_v31:
    if rid not in status and rid not in REQ_V31_OVERRIDE:
        status[rid] = '已完成' if v31_done else '开发中'

out = ['# Reachable Critical Audit v3 — 需求追踪矩阵（Requirements Tracking）\n',
       '> 状态枚举：`未开发` / `开发中` / `已完成`；完成判据 = 对应测试通过。\n',
       '> 本文件由 tools/gen_tracking.py 生成（保留既有状态）。\n']
emit_section(out, '系统需求（REQ-V3）', sys_v3, status)
emit_section(out, '软件需求（SWR-V3）', swr_v3, status)
emit_section(out, '系统需求（REQ-V3.1）', sys_v31, status, REQ_V31_OVERRIDE)
emit_section(out, '软件需求（SWR-V3.1）', swr_v31, status)
open(os.path.join(ROOT, 'docs/design/REQUIREMENTS_TRACKING.md'), 'w').write('\n'.join(out) + '\n')
print(f'{len(sys_v3)} REQ-V3 + {len(swr_v3)} SWR-V3 + {len(sys_v31)} REQ-V3.1 + {len(swr_v31)} SWR-V3.1 regenerated')
