#!/usr/bin/env python3
"""W1/W4: Mode W workflow 脚本导出器。

满足: REQ-V3-090 (Mode W), REQ-V3-091 (workflow-script 导出),
      REQ-V3-094 (独立复核 N=2 证伪多数决).
关键约束: workflow 脚本无文件系统——脚本只做验证并返回 verdicts,
主代理用 batch_verify --stage collect 落盘 (队列是唯一事实源)。

用法:
    python3 workflow_export.py <project_root> --mode verify [--batch-size N]
    python3 workflow_export.py <project_root> --mode refutation [--batch-size N]
    python3 workflow_export.py <project_root> --mode resurrect [--batch-size N]
"""
import json
import os
import re
import sys

# SWR-V3.4.4-008: tooling 版本一致性守卫——导出脚本内嵌本版本号, collect 侧
# 对比检测导出/收集两端代码版本漂移 (jsrsasign 验收: workspace 导出 +
# installed 旧版收集的实测事故)
TOOLING_VERSION = "3.12"

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

# v3.2: 声称类集合 (与 evidence_ledger.EMPIRICAL_CLAIMS 同源; workflow 脚本
# 模块独立性——不在顶层 import evidence_ledger 以免循环依赖)
EMPIRICAL_CLAIMS = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos")

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
        # v3.2.2 (REQ-V3.2.2-017): claim_type 仅 REACHABLE 有意义——
        # "声称"(漏洞声称)只属于可达裁决; UNREACHABLE 填 claim 会被 collect
        # 机械置 null (claim_nulled_by=collect-claim-null-v3.2.2)
        # v3.2.3 (Lua 审计): 补 rce (env→dlopen/代码执行类, 此前无匹配类别
        # 被迫判 null) 与 other (兜底); null 仅留给 UNREACHABLE 置空语义
        # SWR-V3.4.3-022: 补 leak (信息泄露/env 反射类, cosign 批次实证
        # 此前被迫归 other 失去语义)
        "claim_type": {"enum": ["crash", "panic", "oom", "unbounded", "xss",
                                "protocol_dos", "rce", "leak", "other", "null"]},
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

# v3.2.1 (SWR-V3.2.1-020): shipped-config 盘点——提交值 vs 代码零值对照
SHIPPED_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["component", "items"],
    "properties": {
        "component": {"type": "string"},
        "items": {"type": "array", "items": {
            "type": "object",
            "required": ["file", "key", "committed_value"],
            "properties": {
                "file": {"type": "string"},
                "key": {"type": "string"},
                "committed_value": {"type": "string"},
                "code_default": {"type": "string"},
                "mismatched": {"type": "boolean"},
                "note": {"type": "string"}}}},
    },
}

SHIPPED_CONFIG_SCRIPT = r"""export const meta = {
  name: 'v3-shipped-config',
  description: 'R1.5 子任务: shipped config 实际值盘点 (v3.2.1)',
  phases: [{ title: 'Inventory', detail: 'committed value vs code default per component' }],
}

// SWR-V3.4.5-002: 裸数组形态容忍 (派发侧误传自动包装)
if (Array.isArray(args)) { args = { components: args }; }
else { args = args || {}; }
if (!args.components) {
  return { mode: 'shipped-config', error: 'args.components 缺失 (resume 须携带与首跑一致的 args, W6 §5)' }
}

const SCHEMA = __SCHEMA__

const results = await pipeline(
  args.components,
  (comp) => agent(comp.prompt, { label: `shipped-config:${comp.name}`, schema: SCHEMA }),
)

return {
  mode: 'shipped-config',
  inventories: results.filter(Boolean),
  missing: args.components.filter((_, i) => !results[i]).map((c) => c.name),
}
"""

CONFIG_KEY_HINTS = ("tls", "ssl", "auth", "token", "cert", "listen", "addr",
                    "port", "bind", "password", "secret", "key", "enable",
                    "enabled", "timeout", "limit", "cors")


def shipped_config_prompt(component):
    """SWR-V3.2.1-020: 每组件一个盘点 agent 的任务书。"""
    return f"""你是一个 shipped-config 盘点子智能体 (R1.5 子任务, v3.2.1)。

## 任务上下文
- **组件**: {component['name']} (语言 {component.get('lang', '?')})
- **项目路径**: {component['project_root']}
- **候选目录**: {component.get('dirs', '全仓 config 目录')}

## 任务 (只读盘点, 不修改任何文件)
1. 找出该组件**随仓库提交的配置文件**（configs/*.yaml|toml|json、.env*、docker-compose*.yml、nginx.conf 等）
2. 对每个安全敏感键（tls/ssl/auth/token/cert/监听地址/端口绑定/密码/密钥/开关/超时/上限/cors）：
   - `committed_value` = 配置文件中的提交实际值
   - `code_default` = 代码中该键的零值/默认值（从结构体定义/默认构造 grep）
   - `mismatched` = 两者不一致时为 true（这正是"代码零值默认明文"类误判的根源, W6 §25.4）
3. **编译开关/特性键（v3.10, SWR-V3.10-009）**：若组件形态为构建开关配置（如 Kconfig 风格的 config 开关、Cargo features、CMake 选项等），键语义同样适用——committed_value 含"显式关闭"（如 `# ... is not set`）亦为提交值；code_default 从开关定义处（Kconfig default/features 声明/选项默认）grep；安全相关开关（鉴权默认、沙箱、加固、调试面暴露类）逐项入表。此形态与上款键清单并列，按组件实际形态分派
4. 输出 items 数组, 每个 item: file/key/committed_value/code_default/mismatched/note(平台限定路径如 Windows 证书路径须注明)

## 输出格式
结构化输出工具按 schema 强制校验。最终回复直接作为结果返回, 不要写文件。"""


def export_script_shipped_config(project_root, components):
    """SWR-V3.2.1-020: 导出 shipped-config 盘点 workflow 脚本。
    components: [{name, lang, dirs}]。"""
    if not components:
        return {"status": "WORKFLOW_NOTHING_TO_DO", "mode": "shipped-config"}
    payload = [{"name": c["name"],
                "prompt": shipped_config_prompt({**c, "project_root": project_root})}
               for c in components]
    js = SHIPPED_CONFIG_SCRIPT.replace("__SCHEMA__",
                                       json.dumps(SHIPPED_CONFIG_SCHEMA,
                                                  ensure_ascii=False))
    out_rel = "workflow_shipped_config.js"
    script_path = os.path.join(project_root, ".audit_results", out_rel)
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    with open(script_path, "w") as f:
        f.write(js)
    return {
        "status": "WORKFLOW_SCRIPT_READY",
        "mode": "shipped-config",
        "count": len(payload),
        "script_path": f".audit_results/{out_rel}",
        "payload_key": "components",
        "payload": payload,
        "schema": SHIPPED_CONFIG_SCHEMA,
        "next_step": (
            f"Workflow 工具运行: scriptPath={script_path}, "
            f"args={{\"components\": <payload>}};\n"
            f"收集 inventories 落盘 .audit_results/shipped_config.json "
            f"(主代理汇总: {{component, items[]}})。"),
    }


# v3.1 (W6 §21.1/§19.4/§16.10): 证伪者实证工具箱——按声称类别附标准实验动作
REFUTER_TOOLBOX = {
    "interval/boundary": "区间/边界类: 小规模参照模型实现 + 百万级随机对拍差分 (W6 §21.1)",
    "parser": "解析类: 真实构件(jar/库)+畸形输入矩阵+触发计数——『sink 分支行为死代码』一击致命 (W6 §19.4)",
    "proxy/divergence": "代理/解析分歧类: 标准基础设施(nginx/HAProxy)配置片段实测标准部署行为 (W6 §16.10)",
    "leak/disclosure": "信息泄露类: 逐通道枚举泄露出口 (stderr/日志/错误串/网络侧流量/缓存头), 验证掩码/截断/白名单是否存在; 信任边界几何 (输入控制者 vs 环境控制者 vs 输出读者) 三方核对 (cosign env 反射实证形态)",
}

VERIFY_SCRIPT = r"""export const meta = {
  name: 'v3-verify-wave',
  description: 'R3 批量验证波次: 每候选一个 verifier agent, schema 强校验',
  phases: [{ title: 'Verify', detail: 'schema-validated verdict per candidate' }],
}

// v3.1 (W6 §5): resume 必须携带与首跑一致的 args; 缺失时脚本内防御不崩溃
// SWR-V3.4.5-002: 裸数组形态容忍 (派发侧误传自动包装, gRPC 复活波失败实录)
if (Array.isArray(args)) { args = { candidates: args }; }
else { args = args || {}; }
if (!args.candidates) {
  return { mode: 'verify', error: 'args.candidates 缺失 (resume 必须携带与首跑一致的 args, W6 §5)' }
}

const VERDICT_SCHEMA = __SCHEMA__

// v3.10.2 (SWR-V3.10.2-005): 输入 fail-fast——默认契约 (c.prompt) 与薄封装
// 契约 (c.taskFile) 至少其一非空; 缺失时不派发 agent (undefined prompt 会让
// agent 自由发挥产出幻觉 verdict, 批次实录: 4 条 result 同 id 内容各异)
const results = await pipeline(
  args.candidates,
  (c) => {
    if (!c.prompt && !c.taskFile) {
      return { id: c.id, verdict: 'NEEDS_REVIEW',
               reachability_type: 'INDIRECT', call_chain: [], call_chain_depth: 0,
               evidence: 'workflow input missing: candidate has neither prompt nor taskFile (args contract violation)',
               evidence_grade: 'static_only', blocking_point: 'workflow-input-missing' }
    }
    const prompt = c.taskFile
      ? `你是 reachable-critical-audit 的 R3 候选验证器。第一步: 用 Read 工具读取 \`${c.taskFile}\` 文件全文并严格执行其中任务书。你此前没有见过该任务书内容, 一切以文件内容为准。若该文件读取失败, 返回 verdict=NEEDS_REVIEW 并在 evidence 说明读取失败。`
      : c.prompt
    return agent(prompt, { label: `verify:${c.id}`, schema: VERDICT_SCHEMA })
  },
)

const verdicts = results.map((r, i) => r || null)
return {
  mode: 'verify',
  tooling_version: __TOOLING_VERSION__,
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
// SWR-V3.4.5-002: 裸数组形态容忍 (派发侧误传自动包装)
if (Array.isArray(args)) { args = { candidates: args }; }
else { args = args || {}; }
if (!args.candidates) {
  return { mode: 'refutation', error: 'args.candidates 缺失 (resume 必须携带与首跑一致的 args, W6 §5)' }
}

const REFUTATION_SCHEMA = __SCHEMA__
const N_REFUTERS = 2
const KILL_THRESHOLD = 2

const perCand = args.candidates.map((c) => async () => {
  const votes = await parallel(
    Array.from({ length: N_REFUTERS }, (_, i) => () => {
      // v3.10.2 (SWR-V3.10.2-005): fail-fast——prompts[i] 或 taskFiles[i] 缺失
      // 时不派发 agent
      const prompt = (c.taskFiles && c.taskFiles[i])
        ? `你是 reachable-critical-audit 的 R3.5 证伪者 #${i}。第一步: 用 Read 工具读取 \`${c.taskFiles[i]}\` 文件全文并严格执行其中任务书。你此前没有见过该任务书内容, 一切以文件内容为准。若该文件读取失败, 返回 {"id": "${c.id}", "refuted": false, "reason": "taskFile 读取失败"}`
        : (c.prompts && c.prompts[i])
      if (!prompt) {
        return { id: c.id, refuted: false,
                 reason: 'workflow input missing: refuter prompt unavailable (args contract violation)' }
      }
      return agent(prompt, { label: `refute:${c.id}:${i}`, schema: REFUTATION_SCHEMA })
    }),
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
  tooling_version: __TOOLING_VERSION__,
  decisions,
  note: 'demote=true 的候选由主代理降级并写 correction_record (evidence_ledger.commit); strengthened/attribution_corrections 写入报告 (W6 §13.6/§12.5)',
}
"""


# SWR-V3.4.3-020: 截断协议统一——关键段(承重前提/实证/阻断/结论)必保留,
# 次要段截断且必带标记。旧版 resurrect_prompt 1200 字符静默截断 (无标记)
# 曾致复活者误读证据中段 (P0-P2 全部波次由主代理重建完整证据 args 规避)。
# 锚定段首 (防止粘连段中后段关键词泄漏到次要段分类)
_TRUNC_KEY_HEAD = re.compile(
    r"^【?(?:步骤 ?0|承重前提|实证|阻断|结论|claim 与实证|gap 核实|核对)")


def _truncate_evidence(evidence, budget=None):
    """关键段保留的分级截断。budget=None 时不截关键段 (复活者要全文关键段),
    只丢弃次要段并附标记; budget 给定且结果仍超预算时硬截并附标记。"""
    if not evidence or (budget and len(evidence) <= budget):
        return evidence
    segments = re.split(r"(?<=\n)(?=【|\[)", evidence)
    if len(segments) <= 1:
        out = evidence
        if budget:
            half = max(budget // 2, 200)
            out = evidence[:half] + evidence[-half:]
        return out + (f" ...[截断: 全文 {len(evidence)} 字符, 见 verify_queue.json]"
                      if len(evidence) > len(out) else "")
    key, minor = [], []
    for seg in segments:
        (key if _TRUNC_KEY_HEAD.match(seg) else minor).append(seg)
    out = "".join(key)
    if minor:
        out += (f" ...[截断: 次要段 {sum(len(s) for s in minor)} 字符, "
                f"全文 {len(evidence)} 字符, 见 verify_queue.json]")
    if budget and len(out) > budget:
        out = out[:budget] + f" ...[截断: 全文 {len(evidence)} 字符, 见 verify_queue.json]"
    return out


def refute_prompt(c, idx):
    """N 证伪者差异化视角 (同 prompt 会导致缓存复用=伪独立; perspective-diverse verify)。
    v3.1: 按声称类别注入证伪者实证工具箱 (W6 §21.1/§19.4/§16.10)。"""
    lens = {
        0: "调用边真实性: 逐条 grep 验证 call_chain 相邻边的调用点存在性（函数存在≠被调用）；"
           "边证据的 proof 是否与实际边对应；阻断/守卫函数是否死代码（无生产调用点）。"
           "混合语言项目必须搜索跨语言调用形态（别名/桥接/绑定层），不得只 grep "
           "同语言标识符（v3.8, SWR-V3.8-006）",
        1: "前提维度与阻断幻觉: platform_precondition 是否被忽略（平台限定路径被判通用可达）；"
           "trust_boundary 是否惯例假设——特别注意平台信任模型 (v3.10.2, SWR-V3.10.2-016): "
           "同设备其他应用经导出组件/意图参数注入是异主体, 不得以『单信任域设计』泛化同主体; "
           "gate 是否被当默认开；阻断是否覆盖攻击者可控的全部维度。"
           "平台 API 行为契约 (v3.11, SWR-V3.11-004~006): 已实证的平台固有处理语义"
           "（归档条目查找封顶/系统绑定中介/版本级前置限制/直缓冲约定）是判定依据——"
           "契约成立时不得以『库侧无校验』忽略, 契约不适用时注明理由。",
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
    # SWR-V3.4.3-020: 截断协议统一——关键段(承重前提/实证/阻断/结论)必保留,
    # 次要段截断且必带标记 (旧版静默 [:800] 曾让证伪者误读上下文)
    evidence = _truncate_evidence(c.get('evidence', ''), budget=800)
    chain = c.get('call_chain', [])
    chain_note = ""
    if len(chain) > 8:
        chain_note = f" ...[截断: 全链 {len(chain)} 跳, 见 verify_queue.json]"
        chain = chain[:8]
    return (
        f"你是独立证伪者 #{idx}（对抗性复核）。候选 {c['id']} 被判 REACHABLE。\n"
        f"任务: 尽力证伪该结论。默认立场: 有疑问即 refuted=true。\n"
        f"你的证伪视角: {angle}{toolbox}\n\n"
        f"原判定证据: {evidence}\n"
        f"调用链: {chain}{chain_note}\n"
        f"证据分级: {c.get('evidence_grade')}\n\n"
        f"佐证检索（v3.10, SWR-V3.10-011）: 搜索 sink 的 upstream 修复/已知"
        f"缺陷报告（git log --all -S 关键标识、公开 CVE/补丁）——命中时核对"
        f"本树是否已含并标注首发归属（发现者/补丁作者/时间, 公开补丁未合并"
        f"或已有 CVE 时写明『非首发发现』）, 写入 reason 或 note。"
        f"file 引用一律相对项目根路径。\n\n"
        f"输出 refuted=true/false + reason（证伪依据或确认理由，附 file:line）。"
        f"发现更强的攻击向量或 verifier 归因错误时分别写入 strengthened / "
        f"attribution_correction 字段。补强/归因修正是第三方断言——主代理将逐条"
        f"复核签收后才进入报告与申报材料 (v3.10.2, SWR-V3.10.2-011), 请确保每条"
        f"可回源码核实 (附 file:line)。"
    )



RESURRECT_SCHEMA = {
    "type": "object",
    "required": ["id", "revived", "reason"],
    "properties": {
        "id": {"type": "string"},
        "revived": {"type": "boolean"},
        "reason": {"type": "string"},
        "gap": {"type": "string"},
    },
}

RESURRECT_SCRIPT = r"""export const meta = {
  name: 'v3.2-resurrect-wave',
  description: 'R3.5-N 复活攻击: UNREACHABLE 候选 N=1 尽力复活复核',
  phases: [{ title: 'Resurrect', detail: 'one revival attacker per candidate' }],
}

// SWR-V3.4.5-002: 裸数组形态容忍 (派发侧误传自动包装)
if (Array.isArray(args)) { args = { candidates: args }; }
else { args = args || {}; }
if (!args.candidates) {
  return { mode: 'resurrect', error: 'args.candidates 缺失 (W6 §5)' }
}

const RESURRECT_SCHEMA = __SCHEMA__

const results = await pipeline(
  args.candidates,
  (c) => {
    // v3.10.2 (SWR-V3.10.2-005): fail-fast——prompt/taskFile 缺失不派发 agent
    if (!c.prompt && !c.taskFile) {
      return { id: c.id, revived: false,
               outcome: 'workflow input missing: candidate has neither prompt nor taskFile (args contract violation)' }
    }
    const prompt = c.taskFile
      ? `你是 reachable-critical-audit 的复活攻击者。第一步: 用 Read 工具读取 \`${c.taskFile}\` 文件全文并严格执行其中任务书。你此前没有见过该任务书内容, 一切以文件内容为准。若该文件读取失败, 返回 {"id": "${c.id}", "revived": false, "outcome": "taskFile 读取失败"}`
      : c.prompt
    return agent(prompt, { label: `resurrect:${c.id}`, schema: RESURRECT_SCHEMA })
  },
)

const decisions = results.map((r, i) => r || null)
return {
  mode: 'resurrect',
  project: __PROJECT__,
  tooling_version: __TOOLING_VERSION__,
  dispatched_ids: args.candidates.map((c) => c.id),
  decisions: decisions.filter(Boolean),
  missing: args.candidates.filter((_, i) => !decisions[i]).map((c) => c.id),
  note: 'revived=true 由主代理回 R3 重验 (附复活者 gap), 不直接改 verdict (REQ-V3.2-021)',
}
"""


def resurrect_pool(candidates, batch_size=8):
    """SWR-V3.2-040: UNREACHABLE 复活攻击抽样。
    (1) 声称类 UNREACHABLE (claim_type 命中 EMPIRICAL_CLAIMS 或 evidence 含
        unbounded/oom/xss/crash 等) → 全量;
    (2) 其他类 → 20% 抽样, 最少 2, 上限 batch_size;
    已有 resurrection_review 的候选排除 (多波不重复, W6 §12.3 同构)。"""
    pool = [c for c in candidates
            if c.get("status") == "VERIFIED" and c.get("verdict") == "UNREACHABLE"
            and not c.get("resurrection_review")]
    claimed, other = [], []
    for c in pool:
        text = " ".join(str(c.get(k) or "")
                        for k in ("claim_type", "evidence", "summary", "sink_type")).lower()
        if any(k in text for k in EMPIRICAL_CLAIMS):
            claimed.append(c)
        else:
            other.append(c)
    sample_n = max(2, min(batch_size, len(other) // 5)) if other else 0
    # 确定性抽样: 按 id 排序取前 N (无随机数依赖, workflow 可重放)
    sampled = sorted(other, key=lambda c: c.get("id", ""))[:sample_n]
    return claimed + sampled


def resurrect_prompt(c):
    """SWR-V3.2-041: 尽力复活任务书——默认立场 = 找到一条 verifier 未枚举的
    阻断缺口或错误前提即 revived=true (防漏放, 313 验收 etcd 三连救回的制度化)。"""
    return (
        f"你是复活攻击者（对抗性复核，N=1）。候选 {c['id']} 被判 UNREACHABLE。\n"
        f"任务: **尽力复活**该候选——枚举 verifier 可能遗漏的阻断缺口或错误前提。\n"
        f"默认立场: 找到一条 verifier 未枚举的维度即 revived=true。\n"
        f"复活维度:\n"
        f"  1. 阻断是否覆盖攻击者可控的**全部**维度（任一维度未覆盖即复活）\n"
        f"  2. 承重前提是否真伪（严格相等门控/默认参数/常量值逐一核实）\n"
        f"  3. 三层默认语义是否误用（部署层前提被当默认关）\n"
        f"  4. 死代码豁免是否误用（'无生产调用者'是否漏了动态/反射调用）\n"
        f"  5. 平台前提是否有实证（platform_excluded 是否凭惯例假设）\n\n"
        f"原判定证据: {_truncate_evidence(c.get('evidence', ''))}\n"
        f"调用链: {c.get('call_chain', [])[:8]}\n\n"
        f"输出 revived=true/false + reason（附 file:line）；revived=true 时 "
        f"gap 字段写 verifier 的具体缺口。"
    )


def export_script_resurrect(project_root, batch_size=8):
    """SWR-V3.2-042: 导出复活攻击 workflow (复用 export_script 的载荷模式)。"""
    queue = bv.load_queue(project_root)
    pool = resurrect_pool(queue["candidates"], batch_size)
    if not pool:
        return {"status": "WORKFLOW_NOTHING_TO_DO", "mode": "resurrect"}
    # SWR-V3.3.2-021: 抽样决策落盘 (记录型义务, 消费者=事后问责/报告追溯)
    selected = [c["id"] for c in pool]
    unselected = [c["id"] for c in queue["candidates"]
                  if c.get("status") == "VERIFIED" and c.get("verdict") == "UNREACHABLE"
                  and not c.get("resurrection_review") and c["id"] not in selected]
    with open(os.path.join(project_root, ".audit_results",
                           "_resurrect_sample.json"), "w") as f:
        json.dump({
            "rule": "声称类 (crash/panic/oom/unbounded/xss/protocol_dos) UNREACHABLE 全量 + "
                    "其他类 20% 抽样 (最少 2, 上限 batch_size), 已有 resurrection_review 排除",
            "selected": selected, "unselected": unselected,
            "unselected_note": "未入池候选无复活复核义务 (REQ-V3.2-023 只查声称类)",
        }, f, ensure_ascii=False, indent=2)
    payload = []
    # v3.10.2 收尾补丁 (P8 遗漏): 平台信任模型清单注入——三层对抗复核
    # (verifier/证伪者/复活者) 知识注入对称; 复活者是放行方向最后防线,
    # 其平台知识基线不得弱于前两层 (026/027 复活成功恰依赖复活者自带
    # 平台知识而证伪者缺失——靠自带知识是运气性因素, 必须机制化注入)
    try:
        import checklist_binder as _cb
        isurf_path = os.path.join(project_root, ".audit_results",
                                  "input_surface.json")
        _surfs = json.load(open(isurf_path)).get("surfaces", []) \
            if os.path.exists(isurf_path) else []
        _plats = _cb.detect_platforms(_surfs)
        _models = _cb.platform_models(_plats)
        _contracts = _cb.platform_api_contracts(_plats)
    except (ImportError, OSError, ValueError):
        _models, _contracts = [], []
    for c in pool:
        prompt = resurrect_prompt(c)
        if _models:
            prompt += ("\n\n## 平台信任模型对照清单 (v3.10.2, SWR-V3.10.2-016)\n"
                       "目标平台信号: " + ", ".join(_plats) + "。复活维度 5"
                       " (平台前提是否有实证) 必须逐条对照: \n")
            for _m in _models:
                prompt += (f"### {_m.get('id')}\n{_m.get('mechanism')}\n"
                           + "".join(f"- {q}\n" for q in _m.get("probe_questions") or []))
            prompt += ("\n『同主体/单信任域』类阻断论证必须对照上表核实——"
                       "同设备其他应用经导出组件/意图参数注入是异主体。\n")
        if _contracts:
            prompt += ("\n\n## 平台 API 行为契约清单 (v3.11, SWR-V3.11-004~006)\n"
                       "已实证的平台 API 固有处理语义, 复活论证必须对照:\n")
            for _ct in _contracts:
                prompt += (f"### {_ct.get('id')}\n{_ct.get('api_pattern')}: "
                           f"{_ct.get('behavior')} (security_effect="
                           f"{_ct.get('security_effect')})\n")
        payload.append({"id": c["id"], "prompt": prompt})
    js = _inject_project_marker(
        RESURRECT_SCRIPT.replace("__SCHEMA__", json.dumps(RESURRECT_SCHEMA, ensure_ascii=False)),
        project_root)
    script_path = os.path.join(project_root, ".audit_results", "workflow_resurrect.js")
    with open(script_path, "w") as f:
        f.write(js)
    return {
        "status": "WORKFLOW_SCRIPT_READY", "mode": "resurrect",
        "count": len(payload), "script_path": ".audit_results/workflow_resurrect.js",
        "payload_key": "candidates", "payload": payload, "schema": RESURRECT_SCHEMA,
        "next_step": ("Workflow 工具运行: scriptPath=workflow_resurrect.js, "
                      "args={\"candidates\": <payload>};\n"
                      "revived=true 候选回 R3 重验 (附 gap), 不直接改 verdict;\n"
                      "全部候选落盘 resurrection_review (REQ-V3.2-023)"),
    }



def _inject_project_marker(js, project_root):
    """SWR-V3.3.2-022: 返回段 project 字段注入 (静态替换, 非模板插值——
    遵守 W6 §17.2 顶层 const 禁 ${} 插值条款)。
    SWR-V3.4.4-008: 同时注入 tooling 版本——collect 侧对比本模块版本,
    不一致告警 (导出/收集两端代码版本漂移守卫, jsrsasign 验收实测事故)。"""
    return (js.replace("__PROJECT__", json.dumps(project_root, ensure_ascii=False))
              .replace("__TOOLING_VERSION__",
                       json.dumps(TOOLING_VERSION, ensure_ascii=False)))

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
    # SWR-V3.4.4-003: 截断前记录资格全集——batch_size 静默截断曾致主代理
    # 误判"仅 N 个合格" (jsrsasign R3.5 波次实测); 结果附 qualified_total +
    # truncated 标记 (verify 波次截断为设计行为, 计数同样有用)
    qualified_total = 0
    if mode == "verify":
        qualified = [c for c in candidates if c.get("status") == "PENDING"]
        qualified_total = len(qualified)
        pool = qualified[:batch_size]
    elif mode == "refutation":
        # W6/ohmyzsh 发现: 多波复核时已复核候选 (落盘了 refutation 字段) 须排除,
        # 否则每波重复出队前 4 个
        qualified = [c for c in candidates
                     if c.get("status") == "VERIFIED" and c.get("verdict") == "REACHABLE"
                     and c.get("evidence_grade") in ("edge_proven", "empirically_confirmed")
                     and "refutation" not in c]
        qualified_total = len(qualified)
        pool = qualified[:batch_size]
    else:
        raise ValueError(f"unknown mode {mode}")
    if not pool:
        return {"status": "WORKFLOW_NOTHING_TO_DO", "mode": mode,
                "qualified_total": qualified_total}

    payload = []
    for c in pool:
        ctx = bv._build_context(c, project_root)
        prompt = bv._build_prompt(c, ctx, project_root)
        if mode == "verify":
            # v3.10.2 (SWR-V3.10.2-016): 平台信任模型清单注入——按 R1 surface
            # 集判定平台键, 注入对应清单条目 (零平台信号 → 零注入)
            try:
                import checklist_binder as _cb
                isurf_path = os.path.join(project_root, ".audit_results",
                                          "input_surface.json")
                _surfs = json.load(open(isurf_path)).get("surfaces", []) \
                    if os.path.exists(isurf_path) else []
                _plats = _cb.detect_platforms(_surfs)
                _models = _cb.platform_models(_plats)
                if _models:
                    prompt += ("\n\n## 平台信任模型对照清单 (v3.10.2, SWR-V3.10.2-016)\n"
                               "目标平台信号: " + ", ".join(_plats) + "。\n")
                    for _m in _models:
                        prompt += (f"### {_m.get('id')}\n{_m.get('mechanism')}\n"
                                   + "".join(f"- {q}\n" for q in _m.get("probe_questions") or []))
                    prompt += ("\n步骤 3 的『同主体/DIRECT』判定必须逐条对照上表："
                               "任一平台机制使『调用者≠启动者本人』(异主体) 时按 ACROSS_BOUNDARY 处理。\n")
                # v3.11 (SWR-V3.11-006): 平台 API 契约注入 (阻断/放行判定的知识基线)
                _contracts = _cb.platform_api_contracts(_plats)
                if _contracts:
                    prompt += ("\n\n## 平台 API 行为契约清单 (v3.11, SWR-V3.11-004~006)\n"
                               "以下平台 API 的固有处理语义是已实证的判定依据, "
                               "阻断/放行论证必须对照 (契约成立时不得忽略, 契约不适用时注明):\n")
                    for _ct in _contracts:
                        prompt += (f"### {_ct.get('id')}\n{_ct.get('api_pattern')}: "
                                   f"{_ct.get('behavior')}\n"
                                   f"security_effect={_ct.get('security_effect')}\n"
                                   + "".join(f"- {q}\n" for q in _ct.get("probe") or []))
            except (ImportError, OSError, ValueError):
                pass
            # v3.1 (SWR-V3.1-044/045): 注入家族清单步骤 + 自证伪提示
            checklist_section = _checklist_section(c)
            hints = _self_refutation_section(c)
            if checklist_section:
                prompt += "\n\n" + checklist_section
            if hints:
                prompt += "\n\n" + hints
            # SWR-V3.3.2-020: 复活复核 gap 渲染 (REQ-V3.2-021「附复活者证据」的
            # 机械载体——七项目批次 6 波手工后处理 hack 的制度化)
            gap = c.get("re_verify_gap")
            if gap:
                prompt += (
                    "\n\n## 复活复核 gap（主代理注入, REQ-V3.2-021）\n"
                    "这是 R3.5-N 复活攻击后的重验轮次。上一轮 verifier 判定 UNREACHABLE，"
                    "复活攻击者发现以下阻断缺口。请先在步骤 0 中逐条核实 gap 的 "
                    "file:line 与机制真伪；gap 成立则必须按其方向重做阻断分析并给出"
                    "新裁决；gap 不成立则在新 evidence 中明确反驳理由：\n" + gap)
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
    js = _inject_project_marker(
        template.replace("__SCHEMA__", json.dumps(schema, ensure_ascii=False)),
        project_root)
    out_rel = f"workflow_{mode}.js"
    script_path = os.path.join(project_root, ".audit_results", out_rel)
    with open(script_path, "w") as f:
        f.write(js)

    if mode == "refutation":
        # v3.6 (P1-1, B9 注入时点修复): refutation 时点 cwe/claim_type 已由
        # collect 落盘, _in_r5_semantic_space 可判定 → 复用 _checklist_section
        # 注入家族清单段 (CK-EMPIRICAL-SCOPE 以 r5-semantic 绑定)。puma 审计
        # 实测: verify 导出时 PENDING 无信号恒空, refutation 分支原不注入 →
        # 清单零到达。resurrect 分支与 Mode A' 不加代码 (语境/成本裁决, SWR_V3_6)。
        def _refutation_checklist_section(c):
            section = _checklist_section(c)
            return ("\n\n" + section) if section else ""

        payload = [{"id": c["id"], "file": c.get("source_file", "?"),
                    "evidence": c.get("evidence", ""),
                    "call_chain": c.get("call_chain", []),
                    "evidence_grade": c["evidence_grade"],
                    "prompts": [refute_prompt(c, i) + _refutation_checklist_section(c)
                                for i in range(2)]}
                   for c in pool]

    result = {
        "status": "WORKFLOW_SCRIPT_READY",
        "mode": mode,
        "count": len(payload),
        "qualified_total": qualified_total,
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
    # SWR-V3.4.4-003: 截断告警 (资格全集 > 本波导出数)
    if len(payload) < qualified_total:
        result["truncated"] = True
        result["exported"] = len(payload)
        result["advice"] = (f"资格候选 {qualified_total} 个, 本波仅导出 {len(payload)} 个 "
                            f"(batch_size={batch_size})——若需全集请 --batch-size {qualified_total}")
    return result


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
    # SWR-V3.4.4-010: resurrect 路由——原仅 batch_verify 入口可导出复活波,
    # 直接 CLI 调用抛 unknown mode (两入口不一致实测)
    if mode == "resurrect":
        print(json.dumps(export_script_resurrect(project_root,
                                                 batch_size=batch_size),
                         indent=2, ensure_ascii=False))
        return 0
    print(json.dumps(export_script(project_root, mode=mode, batch_size=batch_size),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
