#!/usr/bin/env python3
r"""从全部版本 REQ/SWR 文档自动提取需求编号，重新生成 REQUIREMENTS_TRACKING.md。
注意: 状态变更在 REQUIREMENTS_TRACKING.md 手工维护；本脚本用于需求文档增删后重建骨架
(会保留既有状态，仅按当前需求文档补齐/移除条目)。
v3.3 (SWR-V3.3-060/061): DOCS 覆盖全部版本段, 提取正则泛化
`(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}`——v3.2 起追踪矩阵漂移的根修。"""
import re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 版本段有序: (标签, REQ 文档路径, SWR 文档路径)
VERSIONS = [
    ("V3",     "docs/design/REQ_V3.md",     "docs/design/SWR_V3.md"),
    ("V3.1",   "docs/design/REQ_V3_1.md",   "docs/design/SWR_V3_1.md"),
    ("V3.2",   "docs/design/REQ_V3_2.md",   "docs/design/SWR_V3_2.md"),
    ("V3.2.1", "docs/design/REQ_V3_2_1.md", "docs/design/SWR_V3_2_1.md"),
    ("V3.2.2", "docs/design/REQ_V3_2_2.md", "docs/design/SWR_V3_2_2.md"),
    ("V3.3",   "docs/design/REQ_V3_3.md",   "docs/design/SWR_V3_3.md"),
    ("V3.3.2", "docs/design/REQ_V3_3_2.md", "docs/design/SWR_V3_3_2.md"),
    ("V3.4",   "docs/design/REQ_V3_4.md",   "docs/design/SWR_V3_4.md"),
    # v3.12 登记 (2026-08-29, REQ_V3_12/SWR_V3_12 为标题形态零提取——登记仅未来-proof；
    # REQUIREMENTS_TRACKING.md 的 V3.12 段为手工追加，禁止运行本脚本再生成)
    ("V3.12",  "docs/design/REQ_V3_12.md",  "docs/design/SWR_V3_12.md"),
    # v3.13 登记 (同 v3.12 语义: 标题形态零提取, 手工段维护, 禁止再生成)
    ("V3.13",  "docs/design/REQ_V3_13.md",  "docs/design/SWR_V3_13.md"),
    # v3.14 登记 (同 v3.13 语义)
    ("V3.14",  "docs/design/REQ_V3_14.md",  "docs/design/SWR_V3_14.md"),
    # v3.15 登记 (同 v3.14 语义: 手工段维护, 禁止再生成)
    ("V3.15",  "docs/design/REQ_V3_15.md",  "docs/design/SWR_V3_15.md"),
    # v3.16 登记 (同 v3.15 语义)
    ("V3.16",  "docs/design/REQ_V3_16.md",  "docs/design/SWR_V3_16.md"),
    # v3.17 登记 (同 v3.16 语义: 手工段维护, 禁止再生成)
    ("V3.17",  "docs/design/REQ_V3_17.md",  "docs/design/SWR_V3_17.md"),
    # v3.18 登记 (同 v3.17 语义)
    ("V3.18",  "docs/design/REQ_V3_18.md",  "docs/design/SWR_V3_18.md"),
    # v3.19 登记 (同 v3.18 语义)
    ("V3.19",  "docs/design/REQ_V3_19.md",  "docs/design/SWR_V3_19.md"),
]
DOCS = {f"{k}-{label}": p for label, rp, sp in VERSIONS
        for k, p in (("REQ", rp), ("SWR", sp))}

# v3.1 REQ 文档无逐条状态列——状态以 SWR 完成度为代理 + 验收项显式标注
REQ_V31_OVERRIDE = {
    # Phase 3.1.3 验收未开始
    "REQ-V3.1-100": "未开发", "REQ-V3.1-101": "未开发",
}

ID_RE = r'(REQ|SWR)-V3(?:\.[0-9.]+)?-\d{3}'

# v3.3: 历史版本 SWR 文档状态措辞归一化 (v3.2.2 用「已经完成开发」)
STATUS_RE = r'(未开发|开发中|已完成|已经完成开发)'
STATUS_NORM = {"已经完成开发": "已完成"}


def extract(path):
    reqs = []
    for line in open(os.path.join(ROOT, path), encoding="utf-8"):
        # group(1)=完整 ID, group(2)=REQ|SWR 内层交替, group(3)=需求文本
        m = re.match(rf'\| ({ID_RE}) \| (.+?) \|', line)
        if m:
            reqs.append((m.group(1), m.group(3).strip()))
    return reqs


def load_status():
    """状态源优先级 (v3.3 修正):
    - v3/v3.1 段: tracking 手工维护为权威 (SWR_V3_1 文档状态列仅填充缺项)
    - v3.2+ 段: SWR 文档自带状态列为权威, 覆盖 tracking (tracking 的旧默认
      未开发 曾阻断 SWR 文档已完成 状态——重建错标根修)。"""
    status = {}
    p = os.path.join(ROOT, 'docs/design/REQUIREMENTS_TRACKING.md')
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            # group(1)=完整 ID, group(2)=REQ|SWR 内层交替, group(3)=状态
            m = re.match(rf'\| ({ID_RE}) \| .+? \| (未开发|开发中|已完成) \|', line)
            if m:
                rid = m.group(1)
                if rid.startswith(("REQ-V3.", "SWR-V3.")) and \
                        not rid.startswith(("REQ-V3.1-", "SWR-V3.1-")):
                    continue  # v3.2+ 段不从旧 tracking 继承 (SWR 文档权威)
                status[rid] = m.group(3)
    for label, _, swr_path in VERSIONS:
        swr_file = os.path.join(ROOT, swr_path)
        if not os.path.exists(swr_file):
            continue
        for line in open(swr_file, encoding="utf-8"):
            # SWR 文档三列形态: | 编号 | 需求 | 状态 | (状态措辞归一化)
            m = re.match(rf'\| ({ID_RE}) \| .+? \| {STATUS_RE} \|', line)
            if m:
                rid = m.group(1)
                st = STATUS_NORM.get(m.group(3), m.group(3))
                if label in ("V3", "V3.1"):
                    status.setdefault(rid, st)
                else:
                    status[rid] = st  # v3.2+: SWR 文档权威覆盖
    return status


def emit_section(out, title, reqs, status, override=None):
    override = override or {}
    out.append(f'\n## {title}（共 {len(reqs)} 条）\n')
    out.append('| 编号 | 需求 | 状态 | 备注 |\n|---|---|---|---|')
    for rid, text in reqs:
        st = override.get(rid) or status.get(rid, '未开发')
        out.append(f'| {rid} | {text} | {st} |  |')


def main():
    """v3.3: 执行体收敛进 main + __main__ 守卫——旧版模块级执行使
    `import gen_tracking` 在无 docs/design 的环境 (安装目录冒烟测试)
    于导入时即炸 (FileNotFoundError 实测)。"""
    status = load_status()
    out = ['# Reachable Critical Audit v3 — 需求追踪矩阵（Requirements Tracking）\n',
           '> 状态枚举：`未开发` / `开发中` / `已完成`；完成判据 = 对应测试通过。\n',
           '> 本文件由 tools/gen_tracking.py 生成（保留既有状态）。\n']

    counts = []
    for label, req_path, swr_path in VERSIONS:
        sys_reqs = extract(req_path)
        swr_reqs = extract(swr_path)
        if not sys_reqs and not swr_reqs:
            continue
        counts.extend([f'{len(sys_reqs)} REQ-{label}',
                       f'{len(swr_reqs)} SWR-{label}'])
        # v3.3 泛化: 各版本 REQ 默认态以同版本 SWR 完成度为代理 (v3.1 逻辑推广)
        swr_done = all(status.get(rid) == '已完成' for rid, _ in swr_reqs)
        for rid, _ in sys_reqs:
            if rid not in status and rid not in REQ_V31_OVERRIDE:
                status[rid] = '已完成' if swr_done else '开发中'
        emit_section(out, f'系统需求（REQ-{label}）', sys_reqs, status,
                     REQ_V31_OVERRIDE)
        emit_section(out, f'软件需求（SWR-{label}）', swr_reqs, status)

    out_path = os.path.join(ROOT, 'docs/design/REQUIREMENTS_TRACKING.md')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'w').write('\n'.join(out) + '\n')
    print(' + '.join(counts) + ' regenerated')


if __name__ == "__main__":
    main()
