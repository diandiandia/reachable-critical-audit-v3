#!/usr/bin/env python3
"""W1/W4: Mode W workflow 脚本导出器。

满足: REQ-V3-090 (Mode W), REQ-V3-091 (workflow-script 导出),
      REQ-V3-094 (独立复核 N=2 证伪多数决).
关键约束: workflow 脚本无文件系统——脚本只做验证并返回 verdicts,
主代理用 batch_verify --stage collect 落盘 (队列是唯一事实源)。

用法:
    python3 workflow_export.py <project_root> --mode verify [--batch-size N]
    python3 workflow_export.py <project_root> --mode refutation [--batch-size N]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
import batch_verify as bv

# v3.1: 清单绑定 + 自证伪提示（可失败降级——两库缺失不阻塞导出，只省略增强段）
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import checklist_binder
    import precedent_library
except ImportError:  # pragma: no cover
    checklist_binder = None
    precedent_library = None

VERDICT_SCHEMA = {
    "type": "object",
    "required": ["id", "verdict", "reachability_type", "call_chain",
                 "call_chain_depth", "evidence", "evidence_grade", "blocking_point"],
    "properties": {
        "id": {"type": "string"},
        "verdict": {"enum": ["REACHABLE", "UNREACHABLE", "NEEDS_REVIEW"]},
        "reachability_type": {"enum": ["DIRECT", "ACROSS_BOUNDARY", "INDIRECT"]},
        "call_chain": {"type": "array", "items": {"type": "string"}},
        "call_chain_depth": {"type": "integer", "minimum": 0},
        "evidence": {"type": "string"},
        "evidence_grade": {"enum": ["static_only", "edge_proven", "empirically_confirmed"]},
        "blocking_point": {"type": ["string", "null"]},
        "edge_evidence": {"type": "array", "items": {
            "type": "object", "required": ["edge", "proof"],
            "properties": {"edge": {"type": "string"}, "proof": {"type": "string"}}}},
        "cwe": {"type": "array", "items": {"type": "string"}},
    },
}

REFUTATION_SCHEMA = {
    "type": "object",
    "required": ["id", "refuted", "reason"],
    "properties": {
        "id": {"type": "string"},
        "refuted": {"type": "boolean"},
        "reason": {"type": "string"},
        # v3.1 (W6 §13.6/§12.5): 证伪者不只会证伪——补强向量与归因更正结构化落盘
        "strengthened": {"type": "string"},
        "attribution_correction": {"type": "string"},
        "note": {"type": "string"},
    },
}

# v3.1 (W6 §21.1/§19.4/§16.10): 证伪者实证工具箱——按声称类别附标准实验动作
REFUTER_TOOLBOX = {
    "interval/boundary": "区间/边界类: 小规模参照模型实现 + 百万级随机对拍差分 (W6 §21.1)",
    "parser": "解析类: 真实构件(jar/库)+畸形输入矩阵+触发计数——『sink 分支行为死代码』一击致命 (W6 §19.4)",
    "proxy/divergence": "代理/解析分歧类: 标准基础设施(nginx/HAProxy)配置片段实测标准部署行为 (W6 §16.10)",
}

VERIFY_SCRIPT = r"""export const meta = {
  name: 'v3-verify-wave',
  description: 'R3 批量验证波次: 每候选一个 verifier agent, schema 强校验',
  phases: [{ title: 'Verify', detail: 'schema-validated verdict per candidate' }],
}

// v3.1 (W6 §5): resume 必须携带与首跑一致的 args; 缺失时脚本内防御不崩溃
if (!args || !args.candidates) {
  return { mode: 'verify', error: 'args.candidates 缺失 (resume 必须携带与首跑一致的 args, W6 §5)' }
}

const VERDICT_SCHEMA = __SCHEMA__

const results = await pipeline(
  args.candidates,
  (c) => agent(c.prompt, { label: `verify:${c.id}`, schema: VERDICT_SCHEMA }),
)

const verdicts = results.map((r, i) => r || null)
return {
  mode: 'verify',
  verified: verdicts.filter(Boolean),
  missing: args.candidates.filter((_, i) => !verdicts[i]).map((c) => c.id),
  note: 'missing 保持 PENDING 并 attempt+1; verified 由主代理 --stage collect 落盘',
}
"""

REFUTATION_SCRIPT = r"""export const meta = {
  name: 'v3-refutation-wave',
  description: 'R3 独立复核: REACHABLE 候选经 N 个证伪者多数决',
  phases: [{ title: 'Refute', detail: 'N refuters per candidate' }],
}

// v3.1 (W6 §5): resume args 防御
if (!args || !args.candidates) {
  return { mode: 'refutation', error: 'args.candidates 缺失 (resume 必须携带与首跑一致的 args, W6 §5)' }
}

const REFUTATION_SCHEMA = __SCHEMA__
const N_REFUTERS = 2
const KILL_THRESHOLD = 2

const perCand = args.candidates.map((c) => async () => {
  const votes = await parallel(
    Array.from({ length: N_REFUTERS }, (_, i) => () =>
      agent(c.prompts[i], { label: `refute:${c.id}:${i}`, schema: REFUTATION_SCHEMA })),
  )
  const valid = votes.filter(Boolean)
  const refuted = valid.filter((v) => v.refuted)
  return {
    id: c.id,
    votes: valid.length,
    refute_count: refuted.length,
    survived: refuted.length < KILL_THRESHOLD,
    demote: refuted.length >= KILL_THRESHOLD,
    reasons: refuted.map((v) => v.reason),
    strengthened: valid.map((v) => v.strengthened).filter(Boolean),
    attribution_corrections: valid.map((v) => v.attribution_correction).filter(Boolean),
    notes: valid.map((v) => v.note).filter(Boolean),
  }
})
const decisions = await parallel(perCand)
return {
  mode: 'refutation',
  decisions,
  note: 'demote=true 的候选由主代理降级并写 correction_record (evidence_ledger.commit); strengthened/attribution_corrections 写入报告 (W6 §13.6/§12.5)',
}
"""


def refute_prompt(c, idx):
    """N 证伪者差异化视角 (同 prompt 会导致缓存复用=伪独立; perspective-diverse verify)。
    v3.1: 按声称类别注入证伪者实证工具箱 (W6 §21.1/§19.4/§16.10)。"""
    lens = {
        0: "调用边真实性: 逐条 grep 验证 call_chain 相邻边的调用点存在性（函数存在≠被调用）；"
           "边证据的 proof 是否与实际边对应；阻断/守卫函数是否死代码（无生产调用点）。",
        1: "前提维度与阻断幻觉: platform_precondition 是否被忽略（平台限定路径被判通用可达）；"
           "trust_boundary 是否惯例假设；gate 是否被当默认开；阻断是否覆盖攻击者可控的全部维度。",
    }
    angle = lens.get(idx, lens[0])
    toolbox = ""
    claim = (c.get("claim_type") or "").lower()
    summary = (c.get("summary") or "").lower()
    if any(k in summary for k in ("区间", "range", "边界", "索引")):
        toolbox = f"\n证伪工具箱建议: {REFUTER_TOOLBOX['interval/boundary']}"
    elif any(k in summary for k in ("解析", "parser", "解码", "decoder", "头")):
        toolbox = f"\n证伪工具箱建议: {REFUTER_TOOLBOX['parser']}"
    elif any(k in summary for k in ("代理", "proxy", "分歧", "走私")):
        toolbox = f"\n证伪工具箱建议: {REFUTER_TOOLBOX['proxy/divergence']}"
    return (
        f"你是独立证伪者 #{idx}（对抗性复核）。候选 {c['id']} 被判 REACHABLE。\n"
        f"任务: 尽力证伪该结论。默认立场: 有疑问即 refuted=true。\n"
        f"你的证伪视角: {angle}{toolbox}\n\n"
        f"原判定证据: {c.get('evidence', '')[:800]}\n"
        f"调用链: {c.get('call_chain', [])[:8]}\n"
        f"证据分级: {c.get('evidence_grade')}\n\n"
        f"输出 refuted=true/false + reason（证伪依据或确认理由，附 file:line）。"
        f"发现更强的攻击向量或 verifier 归因错误时分别写入 strengthened / "
        f"attribution_correction 字段。"
    )


def _checklist_section(c):
    """SWR-V3.1-044: 绑定家族清单并渲染为 prompt 段。"""
    if checklist_binder is None:
        return ""
    bound = checklist_binder.bind(c)
    if not bound:
        return ""
    lib = checklist_binder.load_library()
    by_id = {ck["id"]: ck for ck in lib.get("checklists", [])}
    lines = ["## 家族检查清单（v3.1 强制，逐条执行并写入证据「清单执行记录」段）"]
    for cid, why in bound:
        ck = by_id.get(cid)
        if not ck:
            continue
        lines.append(f"- {cid} {ck['name']} (匹配: {', '.join(why[:2])}):")
        for step in ck.get("steps", []):
            lines.append(f"  - {step}")
    return "\n".join(lines)


def _self_refutation_section(c):
    """SWR-V3.1-045: 自证伪提示（先例匹配 → ≤2 条证伪论据）。"""
    if precedent_library is None:
        return ""
    hints = precedent_library.self_refutation_hints(c)
    if not hints:
        return ""
    lines = ["## 自证伪提示（v3.1: 先用这些论据攻击自己的结论，"
             "自查结论写入证据「自证伪自查」段，不改变裁决结论）"]
    lines.extend(f"- {h}" for h in hints)
    return "\n".join(lines)


def export_script(project_root, mode="verify", batch_size=4):
    queue = bv.load_queue(project_root)
    candidates = queue["candidates"]
    if mode == "verify":
        pool = [c for c in candidates if c.get("status") == "PENDING"][:batch_size]
    elif mode == "refutation":
        # W6/ohmyzsh 发现: 多波复核时已复核候选 (落盘了 refutation 字段) 须排除,
        # 否则每波重复出队前 4 个
        pool = [c for c in candidates
                if c.get("status") == "VERIFIED" and c.get("verdict") == "REACHABLE"
                and c.get("evidence_grade") in ("edge_proven", "empirically_confirmed")
                and "refutation" not in c][:batch_size]
    else:
        raise ValueError(f"unknown mode {mode}")
    if not pool:
        return {"status": "WORKFLOW_NOTHING_TO_DO", "mode": mode}

    payload = []
    for c in pool:
        ctx = bv._build_context(c, project_root)
        prompt = bv._build_prompt(c, ctx, project_root)
        if mode == "verify":
            # v3.1 (SWR-V3.1-044/045): 注入家族清单步骤 + 自证伪提示
            checklist_section = _checklist_section(c)
            hints = _self_refutation_section(c)
            if checklist_section:
                prompt += "\n\n" + checklist_section
            if hints:
                prompt += "\n\n" + hints
            # Mode W: workflow agent 无文件系统, 心跳契约是 Mode A' 机制;
            # 结构化输出由 schema 强制 (StructuredOutput 自动重试), 收集由主代理落盘
            prompt += (
                "\n\n## Mode W 输出契约\n"
                "你的最终回复由结构化输出工具按 schema 强制校验（不匹配自动重试）。\n"
                "不要写任何文件——验证结论直接作为最终回复返回。"
            )
        payload.append({"id": c["id"], "file": c.get("source_file", "?"),
                        "line": c.get("source_line", "?"),
                        "sink_type": c.get("sink_type", "?"),
                        "attempt": c.get("attempt", 0),
                        "prompt": prompt})

    schema = VERDICT_SCHEMA if mode == "verify" else REFUTATION_SCHEMA
    template = VERIFY_SCRIPT if mode == "verify" else REFUTATION_SCRIPT
    js = template.replace("__SCHEMA__", json.dumps(schema, ensure_ascii=False))
    out_rel = f"workflow_{mode}.js"
    script_path = os.path.join(project_root, ".audit_results", out_rel)
    with open(script_path, "w") as f:
        f.write(js)

    if mode == "refutation":
        payload = [{"id": c["id"], "file": c.get("source_file", "?"),
                    "evidence": c.get("evidence", ""),
                    "call_chain": c.get("call_chain", []),
                    "evidence_grade": c["evidence_grade"],
                    "prompts": [refute_prompt(c, i) for i in range(2)]}
                   for c in pool]

    return {
        "status": "WORKFLOW_SCRIPT_READY",
        "mode": mode,
        "count": len(payload),
        "script_path": f".audit_results/{out_rel}",
        "payload_key": "candidates",
        "payload": payload,
        "schema": schema,
        "next_step": (
            f"Workflow 工具运行: scriptPath={script_path}, "
            f"args={{\"candidates\": <payload>}};\n"
            f"v3.1 规范条款 (W6 §10.3/§10.4/§5):\n"
            f"  - args 必须从落盘 payload 文件整读整传, 禁止复制预览截断;\n"
            f"  - resume 必须携带与首跑一致的 args;\n"
            f"  - journal 提取兼容 result/value 双字段;\n"
            f"  - 只采信 schema-validated 最终返回, 半程输出作废。\n"
            f"verify 模式: 返回的 verified 逐条 --stage collect 落盘; "
            f"missing 中的 id 执行 --stage bump-attempt (≥{3} 次转 escalated)。\n"
            f"refutation 模式: demote=true 的候选用 evidence_ledger.commit 写 correction_record 降级;"
            f"strengthened/attribution_corrections 写入报告 (W6 §13.6/§12.5)。"
        ),
    }


def lint_script(js):
    """SWR-V3.1-030 (W6 §17.2): workflow 脚本规范条款检查。
    顶层 const 模板字面量禁 `${}` 插值——模块加载时求值会 ReferenceError。
    返回违规行列表。"""
    violations = []
    import re as _re
    # 粗查: 所有 `const X = \`...\`` 定义块中的 ${ 且不以 args. 开头且不在
    # 函数体/回调内。简化实现: 检查顶层 const 定义 (行首无缩进) 的模板串。
    in_const = False
    for i, line in enumerate(js.splitlines(), 1):
        stripped = line.strip()
        if _re.match(r"^const \w+ = `", stripped):
            in_const = True
        if in_const:
            if "${" in line:
                violations.append(f"line {i}: 顶层 const 模板含 ${{}} 插值 (W6 §17.2)")
            if "`" in line[1:] or stripped.endswith("`"):
                in_const = False
    return violations


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    project_root = argv[1]
    mode = "verify"
    batch_size = 4
    if "--mode" in argv:
        mode = argv[argv.index("--mode") + 1]
    if "--batch-size" in argv:
        batch_size = int(argv[argv.index("--batch-size") + 1])
    print(json.dumps(export_script(project_root, mode=mode, batch_size=batch_size),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
