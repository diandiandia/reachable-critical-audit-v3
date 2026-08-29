#!/usr/bin/env python3
"""
batch_verify.py — R3 批量验证编排器 (Mode A' for opencode/Claude Code)

设计原则：
  - 只做调度和记账，不做分析
  - 每个候选通过 task 子智能体独立验证（有完整的 grep/read 能力）
  - 每批完成后立即落盘，支持断点续传
  - 最后 assert 无 PENDING 残留

用法 (由 Agent 驱动):
  1. 读取下一批:
     python3 batch_verify.py /path/to/project --stage next
     → 输出 3-4 个候选的任务书 + 批次号

  2. Agent 并发执行 task:
     task(subagent_type="general", description=..., prompt=...)
     ...

  3. 收集结果:
     python3 batch_verify.py /path/to/project --stage collect \\
       --batch <n> --cand-001='{"verdict":"REACHABLE",...}' \\
       --cand-002='{"verdict":"UNREACHABLE",...}'
     → 更新 verify_queue.json, 写回磁盘

  4. 重复 1-3 直到 --stage assert 通过

  5. 最终断言:
     python3 batch_verify.py /path/to/project --stage assert
     → 0 PENDING → exit 0
     → 有 PENDING → exit 2 + 列出未验证候选
"""

import json
import os
import re
import sys
import glob
import hashlib
import datetime

BATCH_SIZE = 4
REQUIRED_VERDICT_KEYS = {"verdict", "reachability_type", "call_chain", "call_chain_depth", "evidence"}
MIN_CALL_CHAIN_DEPTH = 3
VALID_VERDICTS = {"REACHABLE", "UNREACHABLE", "NEEDS_REVIEW"}
VALID_REACHABILITY_TYPES = {"DIRECT", "ACROSS_BOUNDARY", "INDIRECT", None}

# v3.2.2 (REQ-V3.2.2-006): verifier 步骤 0.5 按候选 lang 分派模板——
# 第一原则三禁止②: 运行时机制不得依赖单一语言特征 (Python 思维定式根除)
IMPORTABILITY_STEPS = {
    "python": """### 步骤 0.5（v3.2.1 强制）: 模块可导入性预检
回溯前先回答：**链首模块在部署布局下能否被导入？**（模块存在≠被导入）
1. 顶层包解析：链首模块所属顶层包能否解析（import 语法/包结构）——顶层包不存在则链首模块整体不可导入。
   ⚠️ 包存在性检查不执行模块体：传递依赖断裂（模块体 import 链内一层断裂，
   如模块体顶层裸导入同级模块）会空过——存在依赖可疑时必须用实际导入验证
   （python3 -c 'import <module>'，stub 仅第三方依赖、项目自身 import 图真实执行）
2. DI/组件扫描器吞错路径审查：注册器若含 `except Exception: log/continue` 模式，
   必须验证目标模块实际注册成功（注册表/路由表/扫描日志），不得以框架设计推定
3. import 失败 → 该边记 broken_edge，verdict=NEEDS_REVIEW（修复即可达条件候选，
   blocking_point 写明断裂点）——静态链真实 ≠ 运行时存在""",
    "c": """### 步骤 0.5（v3.2.1 强制）: 模块构建包含性预检
回溯前先回答：**链首源文件在部署布局下是否被构建包含？**（源码存在≠被编译链接）
1. 构建包含：该源文件被构建系统引用（CMake file(GLOB)/显式源列表/Makefile）——
   未列入构建的文件不可达
2. 符号引用：sink 函数是否被链上调用者实际引用（交叉引用/链接符号/调用 grep）——
   被 #if 0 或未链接分支包围的符号不可达
3. 构建失败/符号无引用 → 该边记 broken_edge，verdict=NEEDS_REVIEW
   （修复即可达条件候选，blocking_point 写明断裂点）""",
    "cpp": """### 步骤 0.5（v3.2.1 强制）: 模块构建包含性预检
回溯前先回答：**链首源文件在部署布局下是否被构建包含？**（源码存在≠被编译链接）
1. 构建包含：该源文件被构建系统引用（CMake/显式源列表）——未列入构建的文件不可达
2. 符号引用：sink 函数是否被链上调用者实际引用（链接符号/调用 grep）——
   被 #if 0 或未链接分支包围的符号不可达
3. 构建失败/符号无引用 → 该边记 broken_edge，verdict=NEEDS_REVIEW""",
    "go": """### 步骤 0.5（v3.2.1 强制）: 模块构建包含性预检
回溯前先回答：**链首源文件在部署布局下是否被构建包含？**（源码存在≠被编译链接）
1. 构建包含：该文件所属 package 是否被主模块 import（go.mod module 路径 +
   包 import 图）——未被 import 的包不进入二进制
2. 符号引用：sink 函数是否被实际调用（调用 grep/接口实现注册）
3. 构建失败/符号无引用 → 该边记 broken_edge，verdict=NEEDS_REVIEW""",
    "rust": """### 步骤 0.5（v3.2.1 强制）: 模块构建包含性预检
回溯前先回答：**链首源文件在部署布局下是否被构建包含？**（源码存在≠被编译链接）
1. 构建包含：该文件所属 crate 是否被 workspace/Cargo.toml 包含（mod 声明链）
2. 符号引用：sink 函数是否被实际调用（调用 grep/特征实现注册）
3. 构建失败/符号无引用 → 该边记 broken_edge，verdict=NEEDS_REVIEW""",
    "java": """### 步骤 0.5（v3.2.1 强制）: 模块构建包含性预检
回溯前先回答：**链首源文件在部署布局下是否被构建包含？**（源码存在≠被编译打包）
1. 构建包含：该文件是否在构建系统（Maven module/Gradle sourceSet）内
2. 符号引用：sink 方法是否被实际调用（调用 grep/接口实现/框架反射注册——
   反射调用需查注解与扫描器配置，不得以框架设计推定）
3. 构建失败/符号无引用 → 该边记 broken_edge，verdict=NEEDS_REVIEW""",
    "default": """### 步骤 0.5（v3.2.1 强制）: 模块可导入性/构建包含性预检
回溯前先回答：**链首模块在部署布局下能否被导入/构建？**（模块存在≠被导入）
1. 顶层解析：链首模块所属顶层单元能否解析（包导入/构建系统包含/模块声明链）
2. 依赖断裂审查：模块体内部依赖若断裂（如顶层裸导入缺失模块），存在性检查会
   空过——可疑时必须用实际执行验证（实际 import/实际编译，stub 仅第三方依赖）
3. 导入失败 → 该边记 broken_edge，verdict=NEEDS_REVIEW（修复即可达条件候选，
   blocking_point 写明断裂点）——静态链真实 ≠ 运行时存在""",
    # SWR-V3.3.2-014: 静态编译语言短段——编译期链接下完整预检是仪式
    # (七项目批次 71 候选零 broken_edge 实证)
    "static_short": """### 步骤 0.5（build 列表核对）: 构建包含性一行核对
链首源文件在构建系统源列表内（CMake 源列表/GOPATH/cargo 目标/Makefile）——
不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
}

# SWR-V3.3.2-014: 完整预检语言集合——动态导入风险语言；其余静态编译语言
# (c/cpp/go/rust) 走 static_short（application 目标仍注入完整预检）
IMPORTABILITY_FULL_LANGS = {"python", "javascript", "java"}

# v3.5 (偏见 B2): static_short 按语言家族分派——原措辞纯 C 系词汇
# (CMake/GOPATH/cargo/Makefile), 派发给 kotlin/scala/csharp/php/ruby/swift/
# perl/powershell/shell 的库型候选是语言错配 (脚本语言无构建系统, JVM/.NET
# 无 CMake/GOPATH)。各家族措辞均为同一通用语义: 链首模块在部署布局下能否被
# 构建/加载 (模块存在 ≠ 被包含)。未知语言回退 IMPORTABILITY_STEPS["static_short"]。
STATIC_SHORT_BY_FAMILY = {
    "c": IMPORTABILITY_STEPS["static_short"],
    "cpp": IMPORTABILITY_STEPS["static_short"],
    "go": """### 步骤 0.5（go.mod 核对）: 构建包含性一行核对
链首包在 go.mod 模块依赖树内（或被 main 包引用），且不在测试/示例目录——
不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "rust": """### 步骤 0.5（cargo 核对）: 构建包含性一行核对
链首 crate 在 Cargo.toml 依赖树内（[[bin]] 或 src/ 被 lib 引用），且不在
tests/示例目录——不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "kotlin": """### 步骤 0.5（构建单元核对）: 构建包含性一行核对
链首源文件在 Gradle sourceSet/Maven module 源码集内且被主源码集编译包含——
不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "scala": """### 步骤 0.5（构建单元核对）: 构建包含性一行核对
链首源文件在 Gradle sourceSet/Maven module 源码集内且被主源码集编译包含——
不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "csharp": """### 步骤 0.5（工程核对）: 构建包含性一行核对
链首源文件在 .csproj/.sln 编译包含集内（未被 <Compile Remove> 排除）且被
主程序集引用——不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "swift": """### 步骤 0.5（Package.swift 核对）: 构建包含性一行核对
链首源文件在 Package.swift target 源目录内且未被 exclude 排除——
不在则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "php": """### 步骤 0.5（加载闭包核对）: 模块存在 ≠ 被加载
链首模块是否被实际 require/include（composer autoload/显式 require），且不在
死代码分支/测试目录——未被加载则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "ruby": """### 步骤 0.5（加载闭包核对）: 模块存在 ≠ 被加载
链首模块是否被实际 require（Gemfile bundle 内/显式 require），且不在死代码
分支/测试目录——未被加载则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "perl": """### 步骤 0.5（加载闭包核对）: 模块存在 ≠ 被加载
链首模块是否被实际 use/require（cpanfile/显式 use），且不在死代码分支/测试
目录——未被加载则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "powershell": """### 步骤 0.5（加载闭包核对）: 模块存在 ≠ 被加载
链首脚本/模块是否被实际 Import-Module/dot-source（PSModulePath 内），且不在
死代码分支/测试目录——未被加载则记 broken_edge → verdict=NEEDS_REVIEW。""",
    "shell": """### 步骤 0.5（加载闭包核对）: 脚本存在 ≠ 被执行
链首脚本是否被实际 source/调用（主脚本引用链），且不在测试目录——
未被调用则记 broken_edge → verdict=NEEDS_REVIEW。""",
}

# 扩展名 → 语言 (v3.5.2: ast_scanner 已裁除, 本表为独立归一来源)
_EXT_LANG = {
    ".java": "java", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".py": "python", ".go": "go", ".rs": "rust",
    ".js": "javascript", ".ts": "javascript", ".jsx": "javascript", ".tsx": "javascript",
    ".cs": "csharp", ".php": "php", ".rb": "ruby", ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala", ".sh": "shell",
    ".pl": "perl", ".pm": "perl", ".ps1": "powershell",
    # v3.8 (SWR-V3.8-021/022): .sql 识别层 (BIAS_EVAL F2); .m/.mm 与
    # signature_matcher.EXT_LANG_ALIAS 对齐 (BIAS_EVAL F3, 原识别层内部矛盾)
    ".sql": "sql", ".m": "objc", ".mm": "objc",
}
_R15_IGNORE_DIRS = {"node_modules", ".git", ".audit_results", ".agents", ".codex",
                    ".venv", "__pycache__", "reachable-critical-audit", "build",
                    "target", "dist", "vendor", "third_party", "libs", "test",
                    "tests", "tool", "tools", "script", "scripts", "mock",
                    "mocks", "unittest", "scratch", "demo"}

# 短语言别名 → 规范名 (SWR-V3.4.6-001: _project_dom_lang 与 lang_of 共用)
# v3.5.2 (P3): 补 typescript→javascript——否则 typescript 候选写入账本幻影列
# (账本 langs 无 typescript; 归一输出集才有 javascript)
_LANG_ALIAS = {"py": "python", "pl": "perl", "ts": "javascript", "js": "javascript",
               "rb": "ruby", "kt": "kotlin", "sh": "shell", "ps1": "powershell",
               "cs": "csharp", "rs": "rust", "typescript": "javascript"}


def _norm_lang(lg):
    """归一化语言标识: 去点/短别名/unknown 占位 → 规范名或 None。"""
    lg = (lg or "").strip().lstrip(".")
    if not lg or lg == "unknown":
        return None
    return _LANG_ALIAS.get(lg, lg)


def _project_dom_lang(project_root):
    """SWR-V3.4.6-001: 项目主导语言回退链 (候选空队时从 R1 产物推导)。
    链: input_surface.json surfaces[].lang 多数 → architecture_context.json
    language_inventory 文件数主导 → None (调用方落 "other")。
    语义: R1 任务书 schema 强制 surface.lang 必填, 空队形态下该事实源仍可用
    ——账本不因 R3 空队误记 other 格 (quic-go 全 Go 项目误记实录)。
    返回规范语言名或 None; 只读 R1 产物, 缺文件/损坏静默跳过。"""
    audit = os.path.join(project_root, ".audit_results")

    # 回退 1: input_surface.json surface lang 多数
    isurf = os.path.join(audit, "input_surface.json")
    if os.path.exists(isurf):
        try:
            freq = {}
            for s in json.load(open(isurf)).get("surfaces") or []:
                lg = _norm_lang(s.get("lang"))
                if lg:
                    freq[lg] = freq.get(lg, 0) + 1
            if freq:
                return max(freq, key=freq.get)
        except (OSError, ValueError):
            pass
    # 回退 2: architecture_context.json language_inventory 主导 (文件数加权)
    actx = os.path.join(audit, "architecture_context.json")
    if os.path.exists(actx):
        try:
            inv = json.load(open(actx)).get("language_inventory") or []
            if isinstance(inv, dict):
                inv = inv.values()
            freq = {}
            for it in inv:
                if not isinstance(it, dict):
                    continue
                lg = _norm_lang(it.get("lang"))
                if not lg:
                    continue
                try:
                    n = int(it.get("file_count") or 1)
                except (TypeError, ValueError):
                    n = 1
                freq[lg] = freq.get(lg, 0) + n
            if freq:
                return max(freq, key=freq.get)
        except (OSError, ValueError):
            pass
    return None



def _detect_languages(project_root):
    """统计项目各语言源文件数，返回按文件数降序的语言列表。"""
    counts = {}
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in _R15_IGNORE_DIRS]
        for f in files:
            if ".min." in f:
                continue
            lang = _EXT_LANG.get(os.path.splitext(f)[1].lower())
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
    return sorted(counts.keys(), key=lambda l: -counts[l]), counts


def load_queue(project_root):
    path = os.path.join(project_root, ".audit_results", "verify_queue.json")
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, dict) and "candidates" in raw:
        return raw
    return {"candidates": raw}


def save_queue(project_root, queue):
    path = os.path.join(project_root, ".audit_results", "verify_queue.json")
    # Normalize to dict form if needed
    if isinstance(queue, list):
        queue = {"candidates": queue}
    with open(path, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def _load_lenient_json(text):
    """SWR-V3-056: 容错 JSON 加载——非法反斜杠转义修复后重试。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re as _re
        fixed = _re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 不可恢复: {e}") from e


def _validate_verdict_payload(cand_id, payload):
    if not isinstance(payload, dict):
        return [f"{cand_id}: verdict must be a dict (kept PENDING for retry)"]

    errors = []
    missing = sorted(REQUIRED_VERDICT_KEYS - set(payload.keys()))
    if missing:
        errors.append(f"{cand_id}: missing required verdict keys {missing} (kept PENDING for retry)")

    if payload.get("verdict") not in VALID_VERDICTS:
        errors.append(f"{cand_id}: invalid verdict '{payload.get('verdict')}' (kept PENDING for retry)")

    if payload.get("reachability_type") not in VALID_REACHABILITY_TYPES:
        errors.append(f"{cand_id}: invalid reachability_type '{payload.get('reachability_type')}'")

    if "call_chain" in payload and not isinstance(payload.get("call_chain"), list):
        errors.append(f"{cand_id}: call_chain must be a list")

    if "call_chain_depth" in payload and not isinstance(payload.get("call_chain_depth"), int):
        errors.append(f"{cand_id}: call_chain_depth must be an integer")

    if "evidence" in payload and not isinstance(payload.get("evidence"), str):
        errors.append(f"{cand_id}: evidence must be a string")

    # SWR-V3-052: collect 与 assert 校验统一——UNREACHABLE 需 blocking_point
    # (允许 "N/A" 与 "no production callers"; 缺省时从 call_chain 回填)
    if payload.get("verdict") == "UNREACHABLE":
        bp = payload.get("blocking_point")
        if not bp:
            chain = payload.get("call_chain") or []
            if chain:
                payload["blocking_point"] = chain[1] if len(chain) > 1 else chain[0]
                payload["blocking_point_autofilled"] = True
            else:
                errors.append(f"{cand_id}: UNREACHABLE 缺 blocking_point"
                              f" (允许 'N/A' / 'no production callers')")

    if payload.get("evidence_grade") is not None and \
       payload["evidence_grade"] not in ("static_only", "edge_proven", "empirically_confirmed"):
        errors.append(f"{cand_id}: invalid evidence_grade '{payload.get('evidence_grade')}'")

    return errors


def stage_next(project_root, batch_size=BATCH_SIZE):
    """Find next batch of PENDING candidates and print task prompts."""
    queue = load_queue(project_root)
    candidates = queue["candidates"]

    pending = [c for c in candidates if c.get("status") == "PENDING"]
    if not pending:
        print(json.dumps({"status": "ALL_DONE", "message": "No pending candidates remaining"}))
        return

    # 按优先级排序: P0(最高) → P3(最低), 无优先级的放最后
    priority_key = lambda c: c.get("priority", 99)
    pending.sort(key=priority_key)

    batch = pending[:batch_size]
    batch_info = {
        "status": "BATCH_READY",
        "batch_id": _next_batch_id(project_root),
        "count": len(batch),
        "total_pending": len(pending),
        "total_candidates": len(candidates),
        "tasks": []
    }

    for i, cand in enumerate(batch):
        # Get context for the task prompt
        ctx = _build_context(cand)
        out_rel = f"_verify_{cand['id']}.json"
        task = {
            "out_file": f".audit_results/{out_rel}",

            "index": i,
            "candidate_id": cand["id"],
            "file": cand.get("file_path", "?"),
            "line": cand.get("source_line", cand.get("line_number", "?")),
            "cwe": cand.get("cwe_id", "?"),
            "category": cand.get("category", "?"),
            "type": cand.get("type", "TAINT_ANALYSIS"),
            "language": cand.get("language", "?"),
            "prompt": _build_prompt(cand, ctx, project_root)
            + (
                f"\n\n## 心跳契约（SWR-V3-058）\n"
                f"1. 第一步先写占位文件 {'.audit_results/' + out_rel}.pending"
                f"（内容 {json.dumps({'started_at': 'ISO8601'})}）\n"
                f"2. 完成后把最终 JSON 写入 {'.audit_results/' + out_rel}\n"
                f"3. 若目标文件已存在且非本人 pending，追加 .agent-<你的id> 后缀，禁止覆盖\n"
                f"4. 提交前用 python3 -c 'import json,sys; json.load(sys.stdin)' 校验输出"
            )
        }
        batch_info["tasks"].append(task)

    print(json.dumps(batch_info, indent=2, ensure_ascii=False))


def _detect_journal_anomaly(transcript_dir):
    """SWR-V3.10.2-006: journal 后验信号——同 id 多 result 且内容 hash 各异
    提示幻觉 verdict 风险 (workflow args 失效时 agent 自由发挥的实录形态:
    4 条 result 全部同 id、内容各异)。仅告警, 不阻断。"""
    import hashlib as _hl
    jp = os.path.join(transcript_dir, "journal.jsonl")
    if not os.path.isfile(jp):
        return []
    by_id = {}
    try:
        for line in open(jp):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") != "result":
                continue
            r = d.get("result")
            if not isinstance(r, dict) or not r.get("id"):
                continue
            h = _hl.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:12]
            by_id.setdefault(r["id"], set()).add(h)
    except OSError:
        return []
    return [cid for cid, hashes in by_id.items() if len(hashes) > 1]

def _derive_attacker_tier(v, c):
    """SWR-V3.11-002: attacker_tier 缺省推导——verifier 未显式给出时按
    reachability_type/trust_boundary/evidence 信号推导; 无法判定返回 None
    (主代理裁决, 不机械兜底)。"""
    if v.get("attacker_tier") in ("same_process", "same_device_cross_app",
                                  "system_broker", "remote"):
        return v["attacker_tier"]
    if str(v.get("attacker_tier") or ""):
        print(f"Warning: {c.get('id')} 非法 attacker_tier={v.get('attacker_tier')!r} "
              f"回退推导", file=sys.stderr)
    ev = " ".join(str(v.get(k) or "") for k in ("evidence",)).lower()
    rt = v.get("reachability_type")
    if rt == "DIRECT":
        return "same_process"
    if rt == "ACROSS_BOUNDARY":
        # 平台组件注入信号 > 网络内容信号 (同设备异主体优先于远程)
        if (any(k in ev for k in ("导出组件", "意图", "跨应用", "binder",
                                   "组件注入"))
                or re.search(r"\bintent\b", ev)
                or "intent extra" in ev or "intent 参数" in ev
                or "exported=" in ev or "android:exported" in ev):
            return "same_device_cross_app"
        if any(k in ev for k in ("远程", "网络", "remote", "http", "url", "下载",
                                 "服务器", "字节流", "网络内容")):
            return "remote"
        return None
    return None

def stage_collect(project_root, batch_id, verdicts):
    """Collect verdicts from a batch and update the queue."""
    queue = load_queue(project_root)
    candidates = queue["candidates"]
    cand_map = {c.get("id"): c for c in candidates}

    updated = 0
    errors = []
    for cand_id, v in verdicts.items():
        # 非法条目：单独记入 errors 并跳过该条，但**不影响同批其他合法条目落盘**。
        # 出错的候选保持原有 PENDING 状态，下一轮 --stage next 会再次出队重试，
        # 绝不因批内个别坏 verdict 而丢弃整批已完成的工作。
        if cand_id not in cand_map:
            errors.append(f"Unknown candidate: {cand_id}")
            continue

        validation_errors = _validate_verdict_payload(cand_id, v)
        if validation_errors:
            errors.extend(validation_errors)
            continue
        # v3.11 (SWR-V3.11-001/002): attacker_tier 落盘 (显式或推导)
        tier = _derive_attacker_tier(v, cand_map[cand_id])
        if tier:
            v["attacker_tier"] = tier

        # Validate call chain depth
        call_chain = v.get("call_chain", [])
        depth = v.get("call_chain_depth", len(call_chain))
        # SWR-V3-059: 死代码豁免——无生产调用者是合法阻断，不触发 depth 门禁
        dead_code_exempt = v.get("blocking_point") == "no production callers"
        if v["verdict"] in ("REACHABLE", "UNREACHABLE") and depth < MIN_CALL_CHAIN_DEPTH \
                and not dead_code_exempt:
            # Depth too shallow: upgrade to NEEDS_REVIEW and flag for retry
            v["verdict"] = "NEEDS_REVIEW"
            v["evidence"] = (v.get("evidence", "") +
                f" [AUTO: call_chain_depth={depth} < {MIN_CALL_CHAIN_DEPTH}, requires deeper backtracking]")

        entry = cand_map[cand_id]
        entry["status"] = "VERIFIED"
        entry["verdict"] = v["verdict"]
        entry["reachability_type"] = v.get("reachability_type")
        entry["call_chain"] = call_chain
        entry["call_chain_depth"] = depth
        entry["evidence"] = v.get("evidence", "")
        entry["blocking_point"] = v.get("blocking_point")
        if v.get("blocking_point_autofilled"):
            entry["blocking_point_autofilled"] = True
        # W5 回归发现: v3 字段必须落盘——claim_type (实证门禁 ③ 依赖)
        # 与 edge_evidence (分级证据链); 此前被 v2 字段白名单静默丢弃
        # v3.2.2 (REQ-V3.2.2-016): "声称"只属于 REACHABLE——
        # UNREACHABLE/NEEDS_REVIEW 携带 claim 曾反触发强制实证 (mbedtls 实测)
        if v.get("claim_type") and v["verdict"] == "REACHABLE":
            entry["claim_type"] = v["claim_type"]
        elif v.get("claim_type") and v["verdict"] != "REACHABLE":
            entry["claim_type"] = None
            entry["claim_nulled_by"] = "collect-claim-null-v3.2.2"
        if v.get("edge_evidence"):
            entry["edge_evidence"] = v["edge_evidence"]
        # Preserve CWE from rule if not overridden
        if v.get("cwe"):
            entry["cwe"] = v["cwe"]
        # SWR-V3.7-001: 主代理严重程度覆盖透传——机械分级与真实影响不符时,
        # 覆盖值+理由落盘; 队列 JSON 仍是唯一事实源 (可直接编辑)
        if v.get("severity_override"):
            entry["severity_override"] = v["severity_override"]
            entry["severity_override_reason"] = v.get("severity_override_reason", "")
        # SWR-V3.4.3-004/005: verifier 自报 grade 存 grade_self_reported 仅追溯;
        # evidence_grade 由 grade_verdict 机械重算为唯一权威 (对齐 SKILL.md
        # 原意——P0/P1 共 9+ 候选自报 empirically 而无结构化实证, 机械重算后
        # 主代理按证据文本回填, collect 侧口径漂移是回填频发的根因)
        if v.get("evidence_grade"):
            entry["grade_self_reported"] = v["evidence_grade"]
        try:
            _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if _parent not in sys.path:
                sys.path.insert(0, _parent)
            import evidence_ledger as _el
            _g, _gerrs = _el.grade_verdict(entry)
            entry["evidence_grade"] = _g
            if entry.get("grade_self_reported") and _g != entry["grade_self_reported"]:
                entry["grade_recomputed_by"] = "collect-mechanical-recompute"
                # SWR-V3.10-006: 边缺口显式信号——自报 edge_proven 级被重算
                # static_only 时, 最可能是合并边 (v3.8 契约: 逐跳一条, 总条数
                # >= 跳数-1); 此前只有静默降级, 主代理要等报告阶段才发现
                # (kernel 审计最高价值候选 12 跳 10 边实录)。信号不改降级行为,
                # 只补显式 reason 与补拆指引。
                if (_g == "static_only" and
                        entry.get("grade_self_reported") in
                        ("edge_proven", "empirically_confirmed")):
                    cc_len = len(entry.get("call_chain") or [])
                    ee_len = len(entry.get("edge_evidence") or [])
                    entry["edge_gap"] = (
                        f"call_chain={cc_len} 跳, edge_evidence={ee_len} 条"
                        f" (契约要求 >= {cc_len - 1})——疑似合并边, "
                        "补拆为逐跳一条后重 collect")
        except Exception:
            if entry.get("evidence_grade") is None:
                entry["evidence_grade"] = ("edge_proven" if call_chain and depth >= MIN_CALL_CHAIN_DEPTH
                                           else "static_only")
        # SWR-V3-057: language 缺失时按扩展名推断
        if not entry.get("language"):
            src = entry.get("source_file", "")
            entry["language"] = _EXT_LANG.get(os.path.splitext(src)[1].lower(), "unknown")
        updated += 1

    # 只要有任何合法结果就落盘（部分成功优于整批丢弃）。
    save_queue(project_root, queue)
    remaining = len([c for c in candidates if c.get("status") == "PENDING"])
    result = {
        "status": "BATCH_COLLECTED" if not errors else "BATCH_COLLECTED_WITH_ERRORS",
        "batch_id": batch_id,
        "updated": updated,
        "errors": errors,
        "remaining_pending": remaining,
        "progress_pct": round((1 - remaining / len(candidates)) * 100, 1) if candidates else 0
    }
    print(json.dumps(result, ensure_ascii=False))


def stage_r35n_collect(project_root, transcript_dir, expect_ids=None):
    """SWR-V3.4.3-004: resurrect decisions 机械落盘——候选级
    resurrection_review dict {revived, outcome} (REQ-V3.2.2-015 落盘契约)。
    幂等: 已有 resurrection_review 的候选跳过。--expect 全集对账同 collect。"""
    queue = load_queue(project_root)
    anomalies = _detect_journal_anomaly(transcript_dir)
    if anomalies:
        print(json.dumps({"status": "journal_anomaly",
                          "ids": anomalies,
                          "note": "同 id 多 result 且内容各异——疑似 workflow args "
                                  "失效致 agent 自由发挥; 核实后决定是否采信"},
                         ensure_ascii=False), file=sys.stderr)
    files = []
    for name in ("journal.jsonl",):
        p = os.path.join(transcript_dir, name)
        if os.path.isfile(p):
            files.append(p)
    if not files:
        print("Error: journal.jsonl 不存在 (--from-journal 应为 workflow "
              "transcript 目录)", file=sys.stderr)
        return 1
    decisions = []
    for line in open(files[0]):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("type") != "result":
            continue
        r = rec.get("result") or rec.get("value")
        if isinstance(r, dict) and r.get("id") and "revived" in r:
            decisions.append(r)
    if not decisions:
        print("Error: journal 无 resurrect schema 结果 (id+revived)", file=sys.stderr)
        return 1
    extracted = {d["id"] for d in decisions}
    if expect_ids:
        missing = [e for e in expect_ids if e not in extracted]
        if missing:
            print(f"Error: --expect 全集校验失败: journal 缺失 {missing} "
                  f"(提取到 {sorted(extracted)}), 不落盘", file=sys.stderr)
            return 1
    updated = 0
    skipped = 0
    for d in decisions:
        c = next((x for x in queue["candidates"] if x.get("id") == d["id"]), None)
        if c is None:
            print(f"Warning: {d['id']} 不在队列, 跳过", file=sys.stderr)
            continue
        if c.get("resurrection_review"):
            skipped += 1
            continue
        c["resurrection_review"] = {
            "revived": bool(d.get("revived")),
            "outcome": (d.get("reason") or d.get("gap") or "").strip(),
        }
        updated += 1
    save_queue(project_root, queue)
    tw = _tooling_version_warning(project_root)
    if tw:
        print(f"Warning (SWR-V3.4.4-008): {tw}", file=sys.stderr)
    print(json.dumps({"status": "R35N_COLLECTED",
                      "updated": updated, "skipped_existing": skipped,
                      "candidates": [d["id"] for d in decisions]},
                     ensure_ascii=False))
    return 0


def stage_assert(project_root):
    """Assert no PENDING candidates remain."""
    queue = load_queue(project_root)
    candidates = queue["candidates"]
    pending = [c for c in candidates if c.get("status") == "PENDING"]
    needs_review = [c for c in candidates if c.get("verdict") == "NEEDS_REVIEW"]
    invalid_verified = []
    for c in candidates:
        if c.get("status") != "VERIFIED":
            continue
        verdict = c.get("verdict")
        if verdict not in VALID_VERDICTS:
            invalid_verified.append({"id": c.get("id"), "reason": "invalid verdict"})
            continue
        if verdict in ("REACHABLE", "UNREACHABLE"):
            if not isinstance(c.get("call_chain"), list) or c.get("call_chain_depth", 0) < MIN_CALL_CHAIN_DEPTH:
                invalid_verified.append({"id": c.get("id"), "reason": "insufficient call_chain_depth"})
            if not c.get("evidence"):
                invalid_verified.append({"id": c.get("id"), "reason": "missing evidence"})
        if verdict == "REACHABLE" and not c.get("reachability_type"):
            invalid_verified.append({"id": c.get("id"), "reason": "missing reachability_type"})
        if verdict == "UNREACHABLE" and not c.get("blocking_point"):
            invalid_verified.append({"id": c.get("id"), "reason": "missing blocking_point"})
        # SWR-V3-042: REACHABLE 且 static_only 不得存在（可申报性门禁）
        if verdict == "REACHABLE" and c.get("evidence_grade") == "static_only":
            invalid_verified.append({"id": c.get("id"), "reason": "reachable static_only"})

    if pending:
        print(json.dumps({
            "status": "ASSERT_FAILED",
            "pending_count": len(pending),
            "pending_ids": [c.get("id") for c in pending],
            "needs_review_count": len(needs_review)
        }))
        sys.exit(2)

    if invalid_verified:
        print(json.dumps({
            "status": "ASSERT_FAILED_INVALID_VERIFIED",
            "invalid_count": len(invalid_verified),
            "invalid": invalid_verified[:50],
        }))
        sys.exit(3)

    reachable = [c for c in candidates if c.get("verdict") == "REACHABLE"]
    unreachable = [c for c in candidates if c.get("verdict") == "UNREACHABLE"]

    # Calculate average call chain depth
    depths = [c.get("call_chain_depth", 0) for c in candidates if c.get("call_chain_depth")]
    avg_depth = round(sum(depths) / len(depths), 2) if depths else 0

    print(json.dumps({
        "status": "ASSERT_PASSED",
        "total": len(candidates),
        "reachable": len(reachable),
        "unreachable": len(unreachable),
        "needs_review": len(needs_review),
        "avg_call_chain_depth": avg_depth,
        "min_call_chain_depth": min(depths) if depths else 0,
        "max_call_chain_depth": max(depths) if depths else 0,
        "reachability_rate_pct": round(len(reachable) / len(candidates) * 100, 2) if candidates else 0,
        "noise_reduction_rate_pct": round(len(unreachable) / len(candidates) * 100, 2) if candidates else 0,
        "warning": "call chain depth below threshold" if avg_depth < MIN_CALL_CHAIN_DEPTH else None
    }))


def _extract_journal_verdicts(transcript_dir):
    """v3.2.2 (REQ-V3.2.2-024): 从 workflow transcript 目录的 journal.jsonl
    提取 schema-validated 最终返回 (result/value 双字段兼容, W6 §10.3)。
    返回 {cand_id: verdict_dict}——只采信 schema 校验过的最终返回,
    半程输出作废。"""
    import glob as _glob
    out = {}
    candidates = _glob.glob(os.path.join(transcript_dir, "journal.jsonl"))
    if not candidates:
        return out
    for line in open(candidates[0]):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("type") != "result":
            continue
        r = rec.get("result") or rec.get("value")
        if isinstance(r, dict) and r.get("id") and r.get("verdict"):
            out[r["id"]] = r
    return out


def _refutation_journal_hint(transcript_dir):
    """SWR-V3.4.4-004: 检测 journal 是否含 refutation schema 结果
    (id+refuted), 是则返回 r35-collect 指引。"""
    jp = os.path.join(transcript_dir, "journal.jsonl")
    if not os.path.exists(jp):
        return ""
    try:
        for line in open(jp):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") != "result":
                continue
            r = rec.get("result") or rec.get("value")
            if isinstance(r, dict) and r.get("id") and "refuted" in r:
                return ("——该 journal 为 refutation 结果 (id+refuted 形态), "
                        "请用 --stage r35-collect")
    except OSError:
        return ""
    return ""


def _tooling_version_warning(project_root):
    """SWR-V3.4.4-008: 导出脚本内嵌 TOOLING_VERSION vs 本模块版本比对——
    不一致时返回 warn 文本 (不阻断, 主代理裁决)。导出/收集两端代码版本
    漂移曾致 jsrsasign 验收 collect 误用旧版 (实测事故)。"""
    audit = os.path.join(project_root, ".audit_results")
    if not os.path.isdir(audit):
        return None
    local = None
    try:
        import importlib.util
        parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location(
            "workflow_export", os.path.join(parent, "workflow_export.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        local = getattr(mod, "TOOLING_VERSION", None)
    except Exception:
        pass
    warnings = []
    for name in ("workflow_verify.js", "workflow_refutation.js",
                 "workflow_resurrect.js"):
        p = os.path.join(audit, name)
        if not os.path.exists(p):
            continue
        try:
            m = re.search(r"tooling_version:\s*([\"'])([0-9.]+)\1",
                          open(p).read())
        except OSError:
            continue
        if not m:
            continue
        if local and m.group(2) != local:
            warnings.append(f"{name} 由 v{m.group(2)} 导出, 当前代码 v{local} "
                            f"——collect 结果与导出端版本不一致, 请核对")
    return "; ".join(warnings) if warnings else None


def _norm_hypothesis_id(hid):
    """v3.2.2 (REQ-V3.2.2-014): 假说 id 归一——H1/H7 与 H-1/H-7 双向接受,
    内部统一 H-N 形态 (mbedtls 审计: collect 落 H1 形态、assert 期望 H-1 形态)。"""
    if not isinstance(hid, str):
        return hid
    h = hid.strip()
    if len(h) == 2 and h[0].upper() == "H" and h[1].isdigit():
        return f"H-{h[1]}"
    if re.fullmatch(r"H-\d", h):
        return h
    return h


def _adapt_r4_finding(f):
    """SWR-V3.4.3-001: 单 finding 漂移归一 (evidence 数组/r3_link dict/severity/
    recommendation)。返回 (finding, flags)。"""
    flags = []
    out = dict(f)
    ev = out.get("evidence")
    if isinstance(ev, list):
        out["evidence"] = "; ".join(str(x) for x in ev)
        flags.append("evidence-array")
    r3 = out.get("r3_link")
    if isinstance(r3, dict):
        cand, note = r3.get("candidate"), r3.get("note")
        out["r3_link"] = (f"{cand} ({note[:60]})" if cand and note
                          else (cand or (note[:60] if note else None)))
        flags.append("r3-link-dict")
    sev = out.get("severity")
    if isinstance(sev, str) and sev and sev != sev.capitalize():
        out["severity"] = sev.capitalize()
        flags.append("severity-normalized")
    if "recommendation" in out and not out.get("fix"):
        out["fix"] = out.pop("recommendation")
        flags.append("recommendation->fix")
    # v3.9 (SWR-V3.9-001): 漂移归一扩展——Pillow 审计实测五类形态中四类为
    # 字段级漂移 (cwe 字符串/call_chain 字符串/location 别名/surfaces 别名),
    # 原四类自适应 (evidence 数组/r3_link dict/severity/recommendation) 未覆盖。
    cwe = out.get("cwe")
    if isinstance(cwe, str):
        toks = [t.strip() for t in re.split(r"[/;]", cwe) if t.strip()]
        out["cwe"] = toks or [cwe]
        flags.append("cwe-str")
    cc = out.get("call_chain")
    if isinstance(cc, str):
        out["call_chain"] = [cc] if cc.strip() else []
        flags.append("callchain-str")
    if not out.get("call_chain") and isinstance(out.get("location"), list):
        locs = []
        for d in out["location"]:
            if isinstance(d, dict) and d.get("file"):
                locs.append(f"{d['file']}:{d.get('line', '')}".rstrip(":"))
        if locs:
            out["call_chain"] = locs
            flags.append("location->callchain")
    if not out.get("tracked_surfaces") and isinstance(out.get("surfaces"), list):
        out["tracked_surfaces"] = list(out["surfaces"])
        out.setdefault("mapped_surface_ids", {})["surfaces-alias"] = "tracked_surfaces"
        flags.append("surfaces->tracked")
    return out, flags


def _normalize_r4_payload(raw):
    """SWR-V3.4.3-001: 文件级漂移归一——hypotheses 对象形态 + findings 顶层数组。
    返回 (items, norm_flags)。canonical 输入零变化 (回归锚)。"""
    flags = []
    if isinstance(raw, dict) and isinstance(raw.get("hypotheses"), list):
        return raw["hypotheses"], flags
    if isinstance(raw, dict) and isinstance(raw.get("hypotheses"), dict):
        hyps = raw["hypotheses"]
        items = []
        for k, hbody in hyps.items():
            item = {"hypothesis_id": k, **hbody}
            items.append(item)
        flags.append("hypotheses-dict")
        # findings 顶层数组形态: {id, hypothesis, ...} 按 hypothesis 归位
        top = raw.get("findings")
        if isinstance(top, list) and items:
            by_hyp = {}
            for f in top:
                by_hyp.setdefault(f.get("hypothesis"), []).append(f)
            for item in items:
                adapted = []
                for f in by_hyp.get(item.get("hypothesis_id"), []):
                    nf, ff = _adapt_r4_finding(f)
                    flags.extend(f"finding:{ff}" for ff in ff)
                    adapted.append(nf)
                if adapted:
                    item["findings"] = adapted
                # hypothesis 级 tracked_surfaces 下放 (cpp-httplib H1-H4 形态)
                hts = item.get("tracked_surfaces") or []
                for fi in item.get("findings", []):
                    if not fi.get("tracked_surfaces") and hts:
                        fi["tracked_surfaces"] = list(hts)
                        flags.append("tracked-from-hypothesis")
            flags.append("top-level-findings")
        return items, flags
    if isinstance(raw, list):
        items = []
        for f in raw:
            nf, ff = _adapt_r4_finding(f)
            flags.extend(f"finding:{x}" for x in ff)
            items.append(nf)
        return items, flags
    return [raw], flags


def _map_surface_id(sid, known):
    """SWR-V3.4.3-002: tracked_surfaces 域前缀互转映射 (SURF-DAT-* ↔
    SURF-DATA-* 等; cpp-httplib 批次 R1 混合前缀致 agent 自造 id 高频误配)。
    known 为 norm_surface_id 归一化后集合 (无 SURF- 前缀)。
    返回 (mapped_id, changed)。"""
    m = re.match(r"^SURF-([A-Z]{3,4})-(\d+)$", sid or "")
    if not m:
        return sid, False
    dom, num = m.group(1), m.group(2)
    if f"{dom}-{num}" in known:
        return sid, False
    alt = {"DAT": "DATA", "DATA": "DAT", "PRC": "PROC", "PROC": "PRC",
           "STR": "STOR", "STOR": "STR"}
    cand_dom = alt.get(dom, "")
    if cand_dom and f"{cand_dom}-{num}" in known:
        return f"SURF-{cand_dom}-{num}", True
    return sid, False


# SWR-V3.4.4-002: 主代理裁决字段——r4-collect 重跑时按 finding title 匹配
# 保留旧记录中的裁决痕迹 (agent 新产出显式携带的字段优先)。
_R4_ADJUDICATION_FIELDS = (
    "claim_type", "claim_nulled_by", "empirical_verified_by",
    "correction_record", "mapped_surface_ids",
)


def _preserve_adjudication(old, new):
    """返回被保留字段列表 (供 adjudication_preserved_from 追溯)。

    SWR-V3.4.4-002 语义: 重新 collect 的输入文件是 agent 原始产出 (不含裁决),
    必然携带 claim_type 等原始值——已裁决 finding 的裁决字段须**强制保留**
    (裁决信号 = claim_nulled_by/empirical_verified_by/correction_record);
    未裁决 finding 仅在新值缺失时用旧值兜底。"""
    preserved = []
    # SWR-V3.10.1-002: finding 键规范化——title 缺失形态 (libpng 波用
    # finding_id/summary, 无 title) 下 {title: fi} 全部折叠到 None 键,
    # 末条 finding 的 CONFIRMED empirical_result 被强制保留覆写到所有
    # finding (libpng H-1 四 finding 实测全部变为 f-h1-4 文本)。键序:
    # finding_id > id > title > summary 前缀。
    def _fkey(fi):
        return (fi.get("finding_id") or fi.get("id") or fi.get("title")
                or (fi.get("summary") or "")[:80] or None)
    old_fi = {}
    for of in (old.get("findings") or []):
        old_fi[_fkey(of)] = of
    for fi in (new.get("findings") or []):
        ofi = old_fi.get(_fkey(fi))
        if not ofi:
            continue
        fi_preserved = []
        adjudicated = bool(ofi.get("claim_nulled_by")
                           or ofi.get("empirical_verified_by")
                           or ofi.get("correction_record"))
        if adjudicated:
            for k in _R4_ADJUDICATION_FIELDS:
                if k in ofi:
                    fi[k] = ofi[k]
                    fi_preserved.append(k)
        else:
            for k in _R4_ADJUDICATION_FIELDS:
                if ofi.get(k) and not fi.get(k):
                    fi[k] = ofi[k]
                    fi_preserved.append(k)
        # empirical_result: 旧值带 CONFIRMED/REFUTED 主代理标记且新值不带
        # → 强制保留 (前缀标记即主代理复验信号)。v3.10.1-002 修订: v3.10
        # 任务书四态指引使 agent 原始产出同样携带 CONFIRMED 前缀——
        # "原始输入不可能携带"前提过时, 双向 CONFIRMED 时无条件覆写会
        # 冻结首次测量 (SWR-V3.10.1-002 实录)。新值已带前缀 → 保留新值。
        oer = ofi.get("empirical_result") or ""
        ner = fi.get("empirical_result") or ""
        # 非字符串形态 (list/cli_observation dict 等, libjpeg-turbo 实测形态)
        # 不参与前缀保留判定——字符串比较会抛 AttributeError
        oer_s = oer if isinstance(oer, str) else ""
        ner_s = ner if isinstance(ner, str) else ""
        if not ner and oer:
            fi["empirical_result"] = oer
            fi_preserved.append("empirical_result")
        elif oer_s and oer_s.upper().startswith(("CONFIRMED", "REFUTED")) \
                and not (ner_s and ner_s.upper().startswith(("CONFIRMED", "REFUTED"))):
            fi["empirical_result"] = oer
            fi_preserved.append("empirical_result")
        # evidence: 旧值含主代理裁决段而新值无 → 追加裁决段 (不整段覆写)
        oev = ofi.get("evidence") or ""
        nev = fi.get("evidence") or ""
        idx = oev.find("主代理裁决")
        if idx >= 0 and "主代理裁决" not in nev:
            fi["evidence"] = nev + "\n" + oev[idx:]
            fi_preserved.append("evidence(adjudication-tail)")
        if fi_preserved:
            fi["adjudication_preserved_from"] = list(fi_preserved)
            preserved.extend(fi_preserved)
    return preserved


R4_VERDICTS = ("confirmed", "reviewed_clean", "not_applicable")
R4_SEVERITIES = ("critical", "high", "medium", "low")


def _warn_r4_enums(items):
    """v3.8 (SWR-V3.8-003/004/005): R4 枚举完整性告警 (stderr, 不阻断)。

    tomcat 审计实录: R4 agent 产出非枚举 verdict (PARTIAL/REFUTED/REFUTED_HIGH/
    整句散文) 与非法 severity (informational), 收集层不拦截 → 自证伪条目被当
    确认问题列进清单。逐条 warn + 附原文, 由主代理归一 (任务书契约见
    task_templates/biz_hypothesis.md)。"""
    warnings = []
    for h in items or []:
        hid = h.get("hypothesis_id") or "?"
        hv = (h.get("verdict") or "").strip().lower()
        if hv and hv not in R4_VERDICTS:
            warnings.append({
                "kind": "illegal_hypothesis_verdict", "hypothesis_id": hid,
                "value": h.get("verdict"),
                "hint": f"需归一化为 {R4_VERDICTS} 之一 (部分证伪但仍有 confirmed "
                        f"finding → verdict=confirmed + 该条 title 标 [refuted])"})
        for n, fi in enumerate(h.get("findings", []) or [], 1):
            sev = (fi.get("severity") or "").strip().lower()
            if sev and sev not in R4_SEVERITIES:
                warnings.append({
                    "kind": "illegal_finding_severity", "hypothesis_id": hid,
                    "finding": f"{hid}-F{n}", "value": fi.get("severity"),
                    "hint": f"需归一化为 {R4_SEVERITIES} 之一; 非法值会落到机械映射"
                            f"兜底 (medium) 误导分级"})
            title = (fi.get("title") or "").lower()
            if "[refuted]" in title or "informational" in title:
                warnings.append({
                    "kind": "refuted_finding_in_list", "hypothesis_id": hid,
                    "finding": f"{hid}-F{n}",
                    "hint": "自证伪条目不应以确认问题形态进清单——证伪断言移出 "
                            "findings 数组, 或 severity=Low + title 标 [refuted]"})
    for w in warnings:
        print(json.dumps({"status": "R4_ENUM_WARNING", "warning": w},
                         ensure_ascii=False), file=sys.stderr)
    return len(warnings)


def write_scope_review(project_root, changed_dir, decision, reason, surfaces_reopened=None):
    """SWR-V3.10.2-018: 主代理对物化增量面的裁决落盘 (append scope_review.jsonl)。
    decision ∈ {reopen, keep}。"""
    row = {"changed_dir": changed_dir, "decision": decision,
           "reason": reason, "surfaces_reopened": surfaces_reopened or []}
    p = os.path.join(project_root, ".audit_results", "scope_review.jsonl")
    with open(p, "a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row

def stage_reopen(project_root, cid, reopen_reason=None):
    """SWR-V3.10.2-012: NEEDS_REVIEW 候选重开——环境 blocker 解除后回 PENDING
    (保留 correction_record/needs_review_reason/refutation/resurrection_review);
    reopen_reason 必填 (blocker 解除依据)。"""
    queue = load_queue(project_root)
    target = None
    for c in queue.get("candidates", []):
        if c.get("id") == cid:
            target = c
            break
    if target is None:
        print(json.dumps({"status": "REOPEN_NOT_FOUND", "id": cid},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    if target.get("verdict") != "NEEDS_REVIEW":
        print(json.dumps({"status": "REOPEN_REJECTED", "id": cid,
                          "note": f"仅 NEEDS_REVIEW 候选可重开 (当前 {target.get('verdict')})"},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    reason = reopen_reason or os.environ.get("REOPEN_REASON", "")
    if not reason:
        print(json.dumps({"status": "REOPEN_REJECTED", "id": cid,
                          "note": "reopen_reason 必填 (blocker 解除依据)——"
                                  "--reopen-reason 参数传入 (环境变量 REOPEN_REASON 兼容兜底)"},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    target["status"] = "PENDING"
    target["verdict"] = None
    target["evidence_grade"] = None
    target["claim_type"] = None
    target["reopen_reason"] = reason
    import datetime as _dt
    target.setdefault("reopen_history", []).append({
        "reopened_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "prior": {"verdict": "NEEDS_REVIEW",
                  "needs_review_reason": target.get("needs_review_reason")}})
    save_queue(project_root, queue)
    print(json.dumps({"status": "REOPENED", "id": cid,
                      "reason": reason}, ensure_ascii=False))
    return 0

def stage_r4_collect(project_root, findings_file):
    """SWR-V3-055: R4 findings 写回 (merge 语义)。

    v3.2.3 (Lua 审计): 任务书模板产出 {"hypotheses":[...]} 包裹结构与
    裸列表双形态自适应解包; 输入非空但 0 hypothesis_id 提取时 stderr 告警
    (静默空收曾导致主代理误判 R4 已收集)。
    v3.4.3 (SWR-V3.4.3-001/002): 四类漂移自适应 (hypotheses 对象形态/
    findings 顶层数组/evidence 数组/r3_link dict) + tracked_surfaces 前缀
    映射; canonical 输入零变化。"""
    # v3.4.2: sys.path bootstrap——v3.3.2 为新 stage 统一加 bootstrap 时漏掉
    # r4_collect, 从 workspace 外运行 (cwd=/root) 时 import surface_mapper
    # 失败且被误报为 "tracked_surfaces 未知 id" 告警 (P0 三锚点复跑实测)
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    queue = load_queue(project_root)
    findings = json.load(open(findings_file))
    items, norm_flags = _normalize_r4_payload(findings)
    # v3.8 (SWR-V3.8-003/004/005): 枚举完整性告警——非法 verdict/severity 不得
    # 静默入库或静默兜底误导 (tomcat 审计: PARTIAL/REFUTED_HIGH 散文 verdict 与
    # informational 非法 severity 直接进清单)。warn 不阻断 (C2: 拒收需新重试机制)。
    _warn_r4_enums(items)
    # v3.9 (SWR-V3.9-002): tracked_surfaces 硬失败守卫——静默缺簿记导致门禁⑦
    # 假失败、反向制造手工补救 (Pillow H7 13 面缺失实录)。input_surface.json
    # 存在时校验; 违规 hypothesis 整体不合并 (原子性: 部分合并禁止)。
    isurf_path = os.path.join(project_root, ".audit_results", "input_surface.json")
    missing_ts = []
    if os.path.exists(isurf_path):
        try:
            import surface_mapper as _sm
            _norm = getattr(_sm, "norm_surface_id")
            _isurf = json.load(open(isurf_path))
            _known_samples = sorted({_norm(s.get("id"))
                                     for s in _isurf.get("surfaces", [])})[:8]
            for h in items:
                findings = h.get("findings") or []
                for fi in findings:
                    # SWR-V3.10.2-007: surfaces 别名容错 (canonical hypotheses-list
                    # 形态不经 _adapt_r4_finding——波 1 两项目 R4_TRACKED_MISSING
                    # 实录: agent 产出 surfaces 键被硬失败守卫拦截)
                    if not fi.get("tracked_surfaces") \
                       and isinstance(fi.get("surfaces"), list):
                        fi["tracked_surfaces"] = list(fi["surfaces"])
                        fi.setdefault("mapped_surface_ids", {}) \
                           ["surfaces-alias"] = "tracked_surfaces"
                    if fi.get("tracked_surfaces"):
                        continue
                    missing_ts.append({
                        "hypothesis": h.get("hypothesis_id"),
                        "finding": (fi.get("title") or "")[:60],
                        "hint": ("finding 缺 tracked_surfaces 且无 surfaces 别名可恢复——"
                                 "需原样引用 input_surface.json 的 surface id, "
                                 f"前缀示例: {_known_samples}")})
                # SWR-V3.10.2-008: 空 findings 假说须声明假说级 tracked
                # (全量扫掠面)——完全无 tracked 仍拦截
                if not findings and not (h.get("tracked_surfaces") or []):
                    missing_ts.append({
                        "hypothesis": h.get("hypothesis_id"),
                        "finding": "(空 findings 假说)",
                        "hint": ("空 findings 假说 (reviewed_clean/not_applicable) "
                                 "缺假说级 tracked_surfaces——需声明审查触及的"
                                 "全量扫掠面 (原样引用 input_surface.json id, "
                                 f"前缀示例: {_known_samples})")})
        except ValueError:
            pass
    if missing_ts:
        print(json.dumps({"status": "R4_TRACKED_MISSING",
                          "violations": missing_ts,
                          "note": "未写回队列 (原子性: 部分合并禁止)——修复输入文件后重跑 r4-collect"},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    existing = {f.get("hypothesis_id"): f for f in queue.get("r4_findings", [])}
    collected = 0
    for f in items:
        hid = _norm_hypothesis_id(f.get("hypothesis_id"))
        if hid:
            f["hypothesis_id"] = hid
            f["status"] = "VERIFIED"
            # SWR-V3.4.4-002: 保留既有 finding 的主代理裁决字段——重复 collect
            # 不得抹掉 claim 置空/实证标记/裁决记录 (jsrsasign H7-F5 实测事故)
            old = existing.get(hid)
            if old:
                preserved = _preserve_adjudication(old, f)
                if preserved:
                    f.setdefault("adjudication_preserved_from", []) \
                     .extend(preserved)
            # SWR-V3.10-002/003: 假说级 tracked_surfaces 保存 (reviewed_clean /
            # 无 finding 载体的审查触及面——kernel 审计 H4/H5/H6 审 ~30 面零簿记
            # 实录); 幂等追加去重, 不覆盖 finding 级; 有 finding 载体时不重复
            hts = f.get("tracked_surfaces") or []
            if hts:
                have_finding_ts = bool(
                    (f.get("findings") or []) and
                    all((fi.get("tracked_surfaces") or [])
                        for fi in f["findings"]))
                if not have_finding_ts:
                    merged = set(f.get("hypothesis_tracked_surfaces") or [])
                    merged.update(hts)
                    f["hypothesis_tracked_surfaces"] = sorted(merged)
            existing[hid] = f
            collected += 1
    if not collected and items:
        diag = ""
        if isinstance(findings, dict):
            diag = (f" (顶层 keys={sorted(findings.keys())[:6]}, "
                    f"hypotheses 类型={type(findings.get('hypotheses')).__name__})")
        print(json.dumps(
            {"status": "R4_COLLECT_WARNING",
             "warning": (f"输入含 {len(items)} 条目但 0 条提取到 hypothesis_id——"
                         "文件应为裸列表 [{hypothesis_id,...}] 或 "
                         '{"hypotheses":[...]} 包裹; 未写回任何 finding'),
             "diagnosis": diag,
             "file": findings_file},
            ensure_ascii=False), file=sys.stderr)
    queue["r4_findings"] = list(existing.values())
    save_queue(project_root, queue)
    # SWR-V3.3.2-015: tracked_surfaces id 契约校验——前缀映射后经 norm 对照
    # input_surface 已知集, 仍未知才告警 (不阻断落盘)
    unknown = []
    mapped = []
    isurf_path = os.path.join(project_root, ".audit_results", "input_surface.json")
    if os.path.exists(isurf_path):
        try:
            import surface_mapper as sm
            norm = getattr(sm, "norm_surface_id")
            isurf = json.load(open(isurf_path))
            known = {norm(s.get("id")) for s in isurf.get("surfaces", [])}
            for f in queue["r4_findings"]:
                for fi in f.get("findings", []):
                    ids = fi.get("tracked_surfaces") or []
                    new_ids = []
                    for sid in ids:
                        mapped_sid, changed = _map_surface_id(sid, known)
                        if changed:
                            mapped.append({"hypothesis": f.get("hypothesis_id"),
                                           "finding": (fi.get("title") or "")[:60],
                                           "from": sid, "to": mapped_sid})
                            fi.setdefault("mapped_surface_ids", {})[sid] = mapped_sid
                        new_ids.append(mapped_sid)
                    fi["tracked_surfaces"] = new_ids
                    for sid in new_ids:
                        if norm(sid) not in known:
                            unknown.append({"hypothesis": f.get("hypothesis_id"),
                                            "finding": (fi.get("title") or "")[:60],
                                            "surface_id": sid})
            if mapped:
                save_queue(project_root, queue)
        except ValueError as e:
            unknown.append({"error": f"input_surface.json 校验失败: {e}"})
    result = {"status": "R4_COLLECTED", "hypotheses": sorted(existing.keys())}
    if mapped:
        result["mapped_surface_ids"] = mapped
    if unknown:
        result["unknown_surface_ids"] = unknown
        result["warning"] = ("tracked_surfaces 含 input_surface.json 中不存在的 id "
                             "(前缀映射+归一化后)——任务书要求原样引用 surface id (SWR-V3.3.2-015)")
    print(json.dumps(result, ensure_ascii=False))


def _r4_missing(queue):
    """v3.6 (P1-4): H1-H7 未 VERIFIED 清单——从 stage_r4_assert 提取,
    供账本回填前置复用 (同一判定语义, 单一事实源)。"""
    have = {_norm_hypothesis_id(f.get("hypothesis_id"))
            for f in queue.get("r4_findings", [])
            if f.get("status") == "VERIFIED"}
    return [f"H-{i}" for i in range(1, 8) if f"H-{i}" not in have]


def stage_r4_assert(project_root):
    """SWR-V3-055: H1-H7 全部 VERIFIED 断言。"""
    queue = load_queue(project_root)
    missing = _r4_missing(queue)
    print(json.dumps({"status": "R4_ASSERT_PASSED" if not missing else "R4_ASSERT_FAILED",
                      "missing": missing}, ensure_ascii=False))
    return 0 if not missing else 1


def stage_grade_recheck(project_root):
    """SWR-V3.3.2-013: 批量逐候选机械复核 (v3.2 分级复核条款的 CLI 载体)。
    差异写 grade_recomputed_by, 打印差异清单。"""
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    import evidence_ledger as el
    queue = load_queue(project_root)
    changed = []
    warnings = []
    for c in queue.get("candidates", []):
        grade, errors = el.grade_verdict(c)
        for e in errors:
            warnings.append({"id": c.get("id"), "error": e})
        if c.get("evidence_grade") not in ("static_only", "edge_proven",
                                           "empirically_confirmed"):
            continue
        if grade != c.get("evidence_grade"):
            old_grade = c.get("evidence_grade")
            c["evidence_grade"] = grade
            c["grade_recomputed_by"] = "main-agent-mechanical-recheck"
            changed.append({"id": c.get("id"),
                            "from": old_grade, "to": grade})
    save_queue(project_root, queue)
    print(json.dumps({"status": "GRADE_RECHECKED", "changed": changed,
                      "warnings": warnings}, ensure_ascii=False, indent=2))
    return 0


def stage_r35_collect(project_root, transcript_dir):
    """SWR-V3.3.2-011: refutation decisions 机械落盘——
    correction(demote)/strengthened/attribution_correction/note/PoC 文本
    经 evidence_ledger.commit 落候选 (REQ-V3.1-051 落盘位置收敛:
    候选 refutation 字段为权威, 报告从队列派生)。"""
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    import evidence_ledger as el
    import glob as _glob
    queue = load_queue(project_root)
    anomalies = _detect_journal_anomaly(transcript_dir)
    if anomalies:
        print(json.dumps({"status": "journal_anomaly",
                          "ids": anomalies,
                          "note": "同 id 多 result 且内容各异——疑似 workflow args "
                                  "失效致 agent 自由发挥; 核实后决定是否采信"},
                         ensure_ascii=False), file=sys.stderr)
    files = _glob.glob(os.path.join(transcript_dir, "journal.jsonl"))
    if not files:
        print("Error: journal.jsonl 不存在", file=sys.stderr)
        return 1
    decisions = []
    for line in open(files[0]):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("type") != "result":
            continue
        r = rec.get("result") or rec.get("value")
        if isinstance(r, dict) and r.get("id") and ("refuted" in r):
            decisions.append(r)
    if not decisions:
        print("Error: journal 无 refutation schema 结果 (id+refuted)", file=sys.stderr)
        return 1
    by_id = {}
    for d in decisions:
        by_id.setdefault(d["id"], []).append(d)
    for cid, decs in by_id.items():
        c = next((x for x in queue["candidates"] if x.get("id") == cid), None)
        if c is None:
            print(f"Warning: {cid} 不在队列, 跳过", file=sys.stderr)
            continue
        refutation = {"by": [d.get("agent") or f"refuter-{i}"
                             for i, d in enumerate(decs)]}
        kills = [d for d in decs if d.get("refuted")]
        # v3.8 (SWR-V3.8-031): 契约完备——渲染器 _refutation_line 只读
        # survived/votes/refute_count, 旧版 collect 不落盘致 summary 复核列
        # 恒「未复核」(elasticsearch 8 候选实测, nacos #7 同源闭环)。
        refutation["votes"] = len(decs)
        refutation["refute_count"] = len(kills)
        refutation["survived"] = len(kills) < 2
        poc = "；".join((d.get("note") or "").strip() for d in decs if
                        d.get("note") and any(k in d["note"] for k in
                                              ("PoC", "poc", "实测", "实证", "RSS", "exit")))
        if poc:
            refutation["poc_evidence"] = poc
        if kills and len(kills) >= 2:
            refutation["demote"] = True
            el.commit(queue, {"id": cid,
                              "correction": {
                                  "target": cid, "demote_to": "NEEDS_REVIEW",
                                  "reason": ("R3.5 双证伪者一致 demote (r35-collect 机械落盘): "
                                             + (kills[0].get("reason") or "")[:300]),
                                  "by": "r35-collect"}})
        strengthened = [d.get("strengthened") for d in decs if d.get("strengthened")]
        if strengthened:
            refutation["strengthened"] = strengthened
        ac = [d.get("attribution_correction") for d in decs if d.get("attribution_correction")]
        if ac:
            refutation["attribution_correction"] = ac
        el.commit(queue, {"id": cid, "refutation": refutation})
    save_queue(project_root, queue)
    tw = _tooling_version_warning(project_root)
    if tw:
        print(f"Warning (SWR-V3.4.4-008): {tw}", file=sys.stderr)
    print(json.dumps({"status": "R35_COLLECTED", "candidates": sorted(by_id)},
                     ensure_ascii=False))
    return 0


SATURATED_CELL_THRESHOLD = 15   # v3.5 B5: 单格候选数 >= 15 视为饱和, 不建议再选题


def _ledger_pressure(ledger):
    """v3.5 B5: 账本格压力统计 (无新门禁/无新持久字段, 触发=ledger 读取/选题时,
    消费者=主代理; 背景: 波次式同格灌水无提示, RESOURCE-DOS x go 单格 55)。
    - pressure_cells: 非零格按 count 降序, >= SATURATED_CELL_THRESHOLD 标 saturated
    - family_skew: 每族最大格占比 (族内集中度信号)"""
    fams = {r["family"]: (r.get("langs") or {}) for r in ledger.get("rows", [])}
    cells, skew = [], []
    for fam, ls in fams.items():
        tot = sum(ls.values())
        if tot == 0:
            continue
        for lg, n in ls.items():
            if n > 0:
                cells.append({"cell": f"{fam} x {lg}", "count": n,
                              "saturated": n >= SATURATED_CELL_THRESHOLD})
        top_lg, top_n = max(ls.items(), key=lambda kv: kv[1])
        skew.append({"family": fam, "top_cell": f"{fam} x {top_lg}",
                     "top_count": top_n, "family_total": tot,
                     "top_share": round(top_n / tot, 3)})
    cells.sort(key=lambda c: -c["count"])
    skew.sort(key=lambda s: -s["top_share"])
    return {"pressure_cells": cells, "family_skew": skew}


def _ledger_source_key(project_root):
    """v3.5.1: 账本 sources 幂等身份 = 项目路径 sha256 前 16 hex (去项目化)。
    第一原则三禁止③: 运行时资产不落历史项目绝对路径——sources 仅作幂等
    比对身份, 路径内容无用, 追溯由 docs/design/ACCEPTANCE_* 承担。"""
    return hashlib.sha256(os.path.abspath(project_root).encode("utf-8")).hexdigest()[:16]


def _aggregate_counts(queue, project_root):
    """v3.6 (P1-4): 从队列聚合 cwe x lang 计数 (候选 + R4 findings 按主导语言
    近似计入)——从 stage_coverage_ledger 提取, 行为零变化; 供 --write 与
    IDEMPOTENT_SKIP 的 would_be_new_counts 共用 (只算不写)。"""
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ledger = json.load(open(os.path.join(_parent, "resources",
                                         "issue_coverage_matrix.json")))
    fam_map = {}
    for fam, spec in (ledger.get("families") or {}).items():
        for code in (spec.get("cwe") or []):
            fam_map[int(code)] = fam

    def fam_of(code):
        return fam_map.get(int(code), "OTHER")

    def codes_of(entry):
        codes = set()
        cw = entry.get("cwe")
        if isinstance(cw, list):
            for x in cw:
                m = re.search(r"CWE-(\d+)", str(x))
                if m:
                    codes.add(int(m.group(1)))
        elif isinstance(cw, str):
            m = re.search(r"CWE-(\d+)", cw)
            if m:
                codes.add(int(m.group(1)))
        if not codes:
            for m in re.finditer(r"CWE-(\d+)", str(entry.get("sink_type") or "")):
                codes.add(int(m.group(1)))
        return codes

    def lang_of(c):
        lg = (c.get("language") or c.get("lang") or "").strip()
        if lg:
            # 归一化: 旧队列存在 ".go" 扩展名形态 / 短扩展名形态 (py/pl) /
            # "unknown" 占位 (v3.2 前数据)
            lg = lg.lstrip(".")
            if lg and lg != "unknown":
                return _LANG_ALIAS.get(lg, lg)
        ext = os.path.splitext(str(c.get("source_file") or ""))[1].lower()
        return _EXT_LANG.get(ext, "other")

    counts = {}
    lang_freq = {}
    for c in queue.get("candidates", []):
        lg = lang_of(c)
        lang_freq[lg] = lang_freq.get(lg, 0) + 1
        for code in codes_of(c):
            counts[(fam_of(code), lg)] = counts.get((fam_of(code), lg), 0) + 1
    if lang_freq:
        dom = max(lang_freq, key=lang_freq.get)
    else:
        # SWR-V3.4.6-001: 候选空 (R3 空队, R2 keep 0 合法终态) 时主导语言
        # 回退 R1 产物——否则纯语言项目误记 other 格 (quic-go 验收实录:
        # 全 Go 项目 R4 findings 记入 *xother 格, 账本失真人工修正)
        dom = _project_dom_lang(project_root) or "other"
    for f in queue.get("r4_findings", []):
        for fi in f.get("findings", []):
            for code in codes_of(fi):
                counts[(fam_of(code), dom)] = counts.get((fam_of(code), dom), 0) + 1
    return counts


def stage_coverage_ledger(project_root, write=False):
    """SWR-V3.4-001/002/003: 覆盖账本——CWE 族 x 语言审计覆盖追踪 (范围守护)。
    --write: 从 verify_queue 聚合候选级 cwe x lang (+ R4 findings 按项目主导语言
    近似计入), 项目级幂等 (sources 去重), merge 累加写账本。
    前置 (v3.6 P1-4): r4-assert 语义 (H1-H7 全 VERIFIED) + r4_feedback 无未决冲突,
    不满足输出 LEDGER_WRITE_BLOCKED_* 且不烧 sources key。
    无参: 打印缺口格 (0 覆盖 + 单项目低深度) 与全矩阵计数表。"""
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    ledger_path = os.path.join(_parent, "resources", "issue_coverage_matrix.json")
    if not os.path.exists(ledger_path):
        print("Error: resources/issue_coverage_matrix.json 缺失", file=sys.stderr)
        return 1
    ledger = json.load(open(ledger_path))

    if not write:
        gaps, low = [], []
        langs = ledger.get("langs") or []
        for row in ledger.get("rows", []):
            fam = row["family"]
            for lg in langs:
                n = (row.get("langs") or {}).get(lg, 0)
                if n == 0:
                    gaps.append((fam, lg))
                elif n == 1:
                    low.append((fam, lg))
        pressure = _ledger_pressure(ledger)
        print(json.dumps({
            "status": "LEDGER_GAPS",
            "gap_cells": [f"{f} x {l}" for f, l in gaps],
            "low_depth_cells": [f"{f} x {l}" for f, l in low],
            "pressure_cells": pressure["pressure_cells"],
            "family_skew": pressure["family_skew"],
            "note": ("缺口格 = 该 CWE 族 x 该语言从未审计 (0 覆盖)。"
                     "批次选题优先缺口格 (REQ-V3.4-006); "
                     "saturated 格 (count>=15) 不建议再选题 (v3.5 B5)。"),
        }, ensure_ascii=False, indent=2))
        return 0

    key = _ledger_source_key(project_root)
    queue = load_queue(project_root)
    if key in (ledger.get("sources") or []):
        # v3.6 (P1-4): skip 分支附打印 would_be_new_counts (只算不写)——sources 幂等
        # 身份是机制语义 (每项目只回填一次, 防重复记账); 附当前队列将产生的新计数
        # 供主代理核对 (先回填后补标 cwe 的缺口格不回写, 由下批选题闭合)。
        would_be = _aggregate_counts(queue, project_root)
        print(json.dumps({"status": "LEDGER_IDEMPOTENT_SKIP",
                          "project": project_root,
                          "would_be_new_counts": {f"{f}x{l}": n for (f, l), n in
                                                  sorted(would_be.items())},
                          "note": "sources 已含本项目 hash, 不重复记账 (v3.6)"},
                         ensure_ascii=False, indent=2))
        return 0
    # v3.6 (P1-4): 回填前置 (a) r4-assert 语义 (H1-H7 全 VERIFIED)
    missing = _r4_missing(queue)
    if missing:
        print(json.dumps({"status": "LEDGER_WRITE_BLOCKED_R4", "missing": missing,
                          "note": "回填时序: 全部 cwe 修正(含 r4_feedback 裁决)"
                                  " → r4-assert PASS → 六门禁 → --write (v3.6)"},
                         ensure_ascii=False, indent=2))
        return 1
    # 前置 (b) r4_feedback 无未决冲突 (evidence_ledger 已内置 resolved 过滤)
    import evidence_ledger as el
    conflicts = el.r4_feedback(queue)
    if conflicts:
        print(json.dumps({"status": "LEDGER_WRITE_BLOCKED_FEEDBACK",
                          "conflicts": conflicts,
                          "note": "先裁决 r4_feedback 冲突并落盘 r4_feedback_resolved"
                                  " 后再回填 (v3.6)"},
                         ensure_ascii=False, indent=2))
        return 1
    counts = _aggregate_counts(queue, project_root)
    rows = {r["family"]: (r.get("langs") or {}) for r in ledger.get("rows", [])}
    for (fam, lg), n in counts.items():
        if fam not in rows:
            rows[fam] = {}
        rows[fam][lg] = rows[fam].get(lg, 0) + n
    ledger["rows"] = [{"family": f, "langs": ls} for f, ls in sorted(rows.items())]
    ledger.setdefault("sources", []).append(_ledger_source_key(project_root))
    ledger["updated_at"] = datetime.date.today().isoformat()
    json.dump(ledger, open(ledger_path, "w"), ensure_ascii=False, indent=2)
    print(json.dumps({"status": "LEDGER_WRITTEN", "project": project_root,
                      "new_counts": {f"{f}x{l}": n for (f, l), n in
                                     sorted(counts.items())}},
                     ensure_ascii=False, indent=2))
    return 0


# ---- v3.7 (SWR-V3.7-001): 报告严重程度机械映射 ----
# 判据: CWE 族映射 (按 resources/issue_coverage_matrix.json 的账本族归并) +
# claim_type 回退。分级只服务报告呈现; 六门禁判据不依赖本表 (无新门禁)。
# 义务入库三问: 触发=主代理认为机械分级与真实影响不符时用 severity_override;
# 消费者=render_report_md 的分组与排序; 悔例=override 无 reason/非法值 → 渲染告警行。
SEVERITY_ORDER = {"critical": 3, "high": 2, "medium": 1}
SEVERITY_LABELS = {"critical": "严重", "high": "高", "medium": "中"}
SEVERITY_BY_CWE = {
    # 命令/代码注入 + 反序列化 + MEMORY-SAFETY 全族 + NUMERIC 整数下溢 (191, 与 190 对称)
    "critical": {78, 94, 77, 502, 787, 125, 416, 415, 476, 190, 129, 191},
    # SQLi/路径穿越/SSRF + AUTHN 主体 + RESOURCE-DOS 全族 + RACE 全族 +
    # STATE 序对/协议类 (841/696) + NUMERIC 除零 (369, crash 类) +
    # ERROR-HANDLING 未初始化 (457, 实证 SIGABRT 档) + WEB 请求走私 (444) +
    # RESOURCE-DOS ReDoS (1333, 全族 high 先例)
    "high": {89, 74, 22, 918, 862, 863, 639, 306,
             400, 770, 789, 409, 833, 834, 362, 366, 367,
             841, 696, 369, 457, 444, 1333},
    # XSS/开放重定向/CSRF + 鉴权弱项 + CRYPTO 全族 + DATA-INTEGRITY 全族 +
    # STATE 恒错控制流 (670) + NUMERIC 截断/不一致比较 (681/697, 逻辑缺陷默认档) +
    # ERROR-HANDLING 初始化不完整 (665) + WEB 双解析器前提 (436)
    "medium": {79, 601, 352, 285, 287, 926,
               327, 326, 338, 347, 330, 310, 311, 295, 345, 351, 829,
               670, 681, 697, 665, 436},
}
CLAIM_TYPE_SEVERITY = {  # 回退: cwe 无命中时 (REQ-V3.4.3-006: leak 已同步)
    "rce": "critical", "leak": "critical",
    "crash": "high", "panic": "high", "oom": "high",
    "unbounded": "high", "protocol_dos": "high",
    "xss": "medium",
}


def _parse_cwes(entry):
    """提取候选的 CWE 编号集合: cwe 字段 (list 或 str) + sink_type 全量扫描。"""
    blob = " ".join([
        str(entry.get("cwe") or ""),
        str(entry.get("sink_type") or ""),
    ])
    return {int(m) for m in re.findall(r"CWE-(\d+)", blob)}


def severity_for(candidate):
    """SWR-V3.7-001: 返回 (severity, source)。
    优先级: severity_override (合法值, 附 reason) > cwe 映射 (全部 cwe 取 max)
    > claim_type 回退 > medium (default)。override 非法值 → (机械值, invalid_override),
    调用方渲染告警行。"""
    ov = (candidate.get("severity_override") or "").strip().lower()
    if ov in SEVERITY_ORDER:
        return ov, "override"
    if ov:
        mech, src = _mechanical_severity(candidate)
        return mech, "invalid_override"
    return _mechanical_severity(candidate)


def _mechanical_severity(candidate):
    cwes = _parse_cwes(candidate)
    hits = sorted(n for n in cwes
                  if any(n in ids for ids in SEVERITY_BY_CWE.values()))
    if hits:
        by_cwe = {sev for sev, ids in SEVERITY_BY_CWE.items() for n in hits if n in ids}
        top = max(by_cwe, key=lambda s: SEVERITY_ORDER[s])
        return top, "cwe:" + ",".join(f"CWE-{n}" for n in hits)
    ct = (candidate.get("claim_type") or "").strip().lower()
    if ct in CLAIM_TYPE_SEVERITY:
        return CLAIM_TYPE_SEVERITY[ct], f"claim_type({ct})"
    return "medium", "default"


def stage_report(project_root, force=False):
    """SWR-V3-055: 基础量化报告 (过程问责指标)。
    v3.10.2 (SWR-V3.10.2-009): 报告防覆盖——主代理段落已存在时拒绝重跑,
    --force 显式重生成 (批次收尾后重跑机械渲染会覆盖主代理修复建议/结论/
    severity 裁决)。"""
    ar = os.path.join(project_root, ".audit_results")
    rep_path = os.path.join(ar, "reachable_vulnerabilities_report.md")
    if os.path.exists(rep_path) and not force:
        try:
            body = open(rep_path).read()
            # 主代理段落判定: 第三节标题存在且内容非占位符模板
            m = "## 三、修复建议与结论（主代理补充）"
            idx = body.find(m)
            if idx >= 0:
                tail = body[idx + len(m):]
                if "（主代理补充）" not in tail[:400]:
                    print(json.dumps({
                        "status": "REPORT_REFUSED_OVERWRITE",
                        "note": "报告已含主代理段落; 重跑机械渲染将覆盖修复建议/结论/severity 裁决——如确需重生成请 --force"}, ensure_ascii=False), file=sys.stderr)
                    return 1
        except OSError:
            pass
    queue = load_queue(project_root)
    cands = queue["candidates"]
    total = len(cands)
    verified = [c for c in cands if c.get("status") == "VERIFIED"]
    pending = [c for c in cands if c.get("status") == "PENDING"]
    grades = {}
    for c in verified:
        g = c.get("evidence_grade", "unknown")
        grades[g] = grades.get(g, 0) + 1
    reachable = [c for c in verified if c.get("verdict") == "REACHABLE"]
    static_only_reachable = [c for c in reachable if c.get("evidence_grade") == "static_only"]
    r4 = queue.get("r4_findings", [])
    # SWR-V3.4-004: 覆盖账本缺口段 (报告尾注, 范围守护)
    coverage_ledger = None
    try:
        _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _lp = os.path.join(_parent, "resources", "issue_coverage_matrix.json")
        if os.path.exists(_lp):
            ledger = json.load(open(_lp))
            langs = ledger.get("langs") or []
            gap = []
            for row in ledger.get("rows", []):
                for lg in langs:
                    if (row.get("langs") or {}).get(lg, 0) == 0:
                        gap.append(f"{row['family']} x {lg}")
            pressure = _ledger_pressure(ledger)
            coverage_ledger = {"status": "LEDGER_GAP_SUMMARY",
                               "gap_cell_count": len(gap),
                               "gap_cells": gap[:30],
                               "pressure_cells": pressure["pressure_cells"][:30],
                               "saturated_cell_count": sum(
                                   1 for c in pressure["pressure_cells"] if c["saturated"]),
                               "note": ("批次选题优先缺口格 (REQ-V3.4-006); "
                                        "saturated 格 (count>=15) 不建议再选题 (v3.5 B5)")}
    except (OSError, ValueError):
        coverage_ledger = {"status": "LEDGER_UNAVAILABLE"}
    report = {
        "total_candidates": total,
        "verified": len(verified),
        "pending": len(pending),
        "evidence_grade_distribution": grades,
        "reachable": len(reachable),
        "reachable_static_only_violations": [c["id"] for c in static_only_reachable],
        "correction_records": sum(len(c.get("correction_record", [])) for c in verified),
        "coverage_ledger": coverage_ledger,
        "r4_hypotheses_verified": len([f for f in r4 if f.get("status") == "VERIFIED"]),
        "input_surface_note": "input_surface.json 追踪见 surface_mapper; 覆盖门禁由编排器断言",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # v3.7 (SWR-V3.7-002): 机械渲染完整报告 md (队列派生, REQ-V3.3.2-007)。
    # 写入状态走 stderr——stdout 保持纯 JSON 契约 (test_report_outputs 整段 json.loads)。
    try:
        path = render_report_md(project_root, report)
        print(json.dumps({"status": "REPORT_MD_WRITTEN", "path": path},
                         ensure_ascii=False), file=sys.stderr)
    except Exception as e:  # 渲染失败不阻断 JSON 报告 (报告仍可读)
        print(json.dumps({"status": "REPORT_MD_ERROR", "error": str(e)},
                         ensure_ascii=False), file=sys.stderr)


def _problem_summary(c):
    """问题摘要 = claim_type 前缀 + evidence 首 120 字符 (summary 字段 collect 不落盘)。"""
    ct = (c.get("claim_type") or "").strip()
    ev = " ".join(str(c.get("evidence") or "").split())
    head = ev[:120] + ("…" if len(ev) > 120 else "")
    return (f"[{ct}] {head}" if ct else head) or "(无 evidence)"
# v3.11 (SWR-V3.11-003): tier 标注附加在清单摘要尾部
def _tier_suffix(c):
    t = c.get("attacker_tier")
    if c.get("verdict") == "REACHABLE" and t in (
            "same_device_cross_app", "system_broker", "remote"):
        return f" [tier: {t}]"
    return ""


def _needs_review_cause(cand):
    """REQ-V3.3-011: NEEDS_REVIEW 成因双分——显式字段优先, 关键词启发式兜底
    (机械侧近似, 未注明则主代理确认)。"""
    explicit = (cand.get("needs_review_cause") or "").strip()
    if explicit:
        return explicit
    blob = " ".join([
        str(cand.get("evidence") or ""),
        " ".join(str(r) for r in cand.get("correction_record", []) or []),
    ])
    if any(k in blob for k in ("保守", "防御充分", "门禁压力", "防御证据充分")):
        return "保守裁决"
    # v3.10.2 (SWR-V3.10.2-013): 成因三分——环境受限 (无目标平台运行面) 单列
    if any(k in blob for k in ("环境限制", "环境无", "无设备", "无运行面",
                               "不可实证", "无法运行时实证", "环境受限")):
        return "环境受限"
    if any(k in blob for k in ("证据不足", "无法取证", "无法验证", "前提无法",
                               "调用边无法", "不可验证")):
        return "证据不足"
    return "未注明（主代理确认）"


def _refutation_line(c):
    """R3.5 复核列: refutation.survived → 证伪者结果, else 未复核。"""
    rf = c.get("refutation")
    if isinstance(rf, dict) and rf.get("survived") is not None:
        return f"{rf.get('refute_count', '?')}/{rf.get('votes', '?')} 证伪 survived"
    return "未复核"


def _tracked_ids(project_root, queue, surfaces):
    """机械 tracked 集 (B.3/B.5 六门禁⑦用)。
    v3.9 (SWR-V3.9-006): 优先 r2_filter_result.json 三组 surface_ids
    (keep/drop/boundary_confirmations——SWR-V3.4.6-002 保真契约: drop/bc 条目
    的 surface_ids 同样计入覆盖), hypotheses.json 仅无 filter 结果时兜底;
    ∪ r4 findings[].tracked_surfaces ∪ queue.coverage_bridge[].surface。
    v3.10 (SWR-V3.10-001): 多波批次形态——①r2_filter_result*.json 全波次文件
    glob 合并 (主文件与分波文件同权) ②logic_hypotheses[].surface_ids 恒并入
    (门禁⑦语义: "R2 假设 surface_ids" 含 logic 组——防御裁决面的覆盖簿记,
    kernel 审计 27/152 假失败实录) ③假说级 hypothesis_tracked_surfaces
    (reviewed_clean 假说的审查触及面, SWR-V3.10-002/003)。"""
    ids = set()
    ar = os.path.join(project_root, ".audit_results")
    filt_used = False
    for fp in sorted(glob.glob(os.path.join(ar, "r2_filter_result*.json"))):
        try:
            fr = json.load(open(fp))
            for k in ("keep", "drop", "boundary_confirmations"):
                for e in fr.get(k, []) or []:
                    ids.update(e.get("surface_ids", []) or [])
            filt_used = True
        except (OSError, ValueError):
            pass
    hyp_path = os.path.join(ar, "hypotheses.json")
    if os.path.exists(hyp_path):
        try:
            hp = json.load(open(hyp_path))
            if not filt_used:
                for h in hp.get("hypotheses", []):
                    ids.update(h.get("surface_ids", []) or [])
            # logic 组恒并入 (与 filter 结果存在与否无关)
            for lh in hp.get("logic_hypotheses", []) or []:
                ids.update(lh.get("surface_ids", []) or [])
        except (OSError, ValueError):
            pass
    for f in queue.get("r4_findings", []) or []:
        ids.update(f.get("hypothesis_tracked_surfaces", []) or [])
        for fi in f.get("findings", []) or []:
            ids.update(fi.get("tracked_surfaces", []) or [])
    for e in queue.get("coverage_bridge", []) or []:
        if isinstance(e, dict) and e.get("surface"):
            ids.add(e["surface"])
    return sorted(ids)


def stage_tracked_ids(project_root):
    """SWR-V3.9-006: tracked 集机械化 CLI——门禁⑦ 准备免手写 union 脚本;
    落盘 _tracked_ids.json (直接可喂 assert_ledger surface_data);
    覆盖率 <100% 时 exit 1 (供脚本链使用, 主代理可决定继续)。"""
    queue = load_queue(project_root)
    sf_path = os.path.join(project_root, ".audit_results", "input_surface.json")
    surfaces = None
    if os.path.exists(sf_path):
        try:
            surfaces = json.load(open(sf_path))
        except (OSError, ValueError):
            pass
    total = len(surfaces.get("surfaces", [])) if surfaces else 0
    tracked = _tracked_ids(project_root, queue, surfaces)
    all_ids = {s.get("id") for s in surfaces.get("surfaces", [])} if surfaces else set()
    missing = sorted(all_ids - set(tracked))
    out = {"status": "TRACKED_IDS", "total": total,
           "tracked": len(tracked), "missing": missing}
    ad = os.path.join(project_root, ".audit_results")
    if os.path.isdir(ad):
        with open(os.path.join(ad, "_tracked_ids.json"), "w", encoding="utf-8") as f:
            json.dump(sorted(tracked), f, ensure_ascii=False, indent=1)
        out["written"] = ".audit_results/_tracked_ids.json"
    print(json.dumps(out, ensure_ascii=False))
    return 0 if not missing else 1


def _gates_for_report(project_root, queue, surfaces):
    """机械调用六门禁 (evidence_ledger.assert_ledger)——渲染 ①-⑧ 行, 不新增判据。"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import evidence_ledger as _el
    except ImportError:
        return [], "evidence_ledger 不可导入"
    dispatched = [c["id"] for c in queue.get("candidates", []) if c.get("id")]
    surface_data = None
    if surfaces is not None:
        surface_data = {
            "total": len(surfaces),
            "tracked_ids": _tracked_ids(project_root, queue, surfaces),
            "mirror_pairs": surfaces.get("mirror_pairs") or [],
        }
    try:
        ok, violations = _el.assert_ledger(queue, dispatched=dispatched,
                                           surface_data=surface_data)
    except Exception as e:  # 六门禁渲染兜底: 断言失败不阻断报告生成
        return [], f"assert_ledger 不可用: {e}"
    return violations, None


def _r4_severity(fi):
    """SWR-V3.7-010: R4 finding 分级 = 申报值归一化 (High→high, Medium→medium,
    Low→low)。申报值缺失/非法 → 回退机械映射 (severity_for 兜底 medium)。
    用户裁决: R4 agent 按实际影响裁定比机械 cwe 映射准 (CWE-476 族 Low 影响
    的 NoMethodError 走机械映射会误判为严重)。"""
    sev = (fi.get("severity") or "").strip().lower()
    # v3.8 (SWR-V3.8-012, zookeeper 审计修正回填): critical 必须入白名单——
    # 旧 ("high","medium","low") 使申报 Critical 的 R4 finding 落到机械映射兜底。
    if sev in ("critical", "high", "medium", "low"):
        return sev, f"r4:{sev}"
    return severity_for(fi)


def _r4_location(fi):
    """SWR-V3.9-005: R4 finding 位置列来源——call_chain[0] (r4-collect 归一化保证
    file:line 形态) → location 字段 → 降级 '-' (渲染铁律: 缺失降级占位不抛异常)。"""
    cc = fi.get("call_chain") or []
    if cc and isinstance(cc[0], str) and cc[0].strip():
        return cc[0].strip()
    loc = fi.get("location")
    if isinstance(loc, list) and loc:
        d = loc[0]
        if isinstance(d, dict) and d.get("file"):
            return f"{d['file']}:{d.get('line', '')}".rstrip(":")
        if isinstance(d, str) and d.strip():
            return d.strip()
    return "-"


def _confirmed_issues(queue, cands):
    """SWR-V3.7-009: 确认问题全集 = R3 REACHABLE 候选 ∪ R4 confirmed findings
    (High/Medium)。R4 分级口径=申报值归一化; r3_link 指向候选 (CAND-) 的
    同事实条目不重复列 (SWR-V3.4.3-060), 记入 dupes 供清单尾部说明。"""
    issues, dupes = [], []
    for c in cands:
        if c.get("verdict") == "REACHABLE":
            sev, src = severity_for(c)
            issues.append({"kind": "r3", "obj": c, "severity": sev,
                           "source": src, "key": c.get("id")})
    for f in queue.get("r4_findings", []) or []:
        # SWR-V3.10.1-001: 只并入 confirmed 假说的 findings——spec 口径
        # "R4 confirmed findings"; reviewed_clean/not_applicable 假说的
        # 复核记录 (severity null/Low 正向确认) 被 _r4_severity 机械兜底
        # medium 后误入问题清单 (libjpeg-turbo 审计实录: 9 条复核 clean
        # 记录渲染为"中"级问题)。verdict 非 confirmed 的假说跳过。
        if (f.get("verdict") or "").strip().lower() != "confirmed":
            continue
        hid = f.get("hypothesis_id") or "?"
        for n, fi in enumerate(f.get("findings", []) or [], 1):
            sev, src = _r4_severity(fi)
            # critical 必须并入: _render_problem_list 的 grouped 有 critical 桶,
            # 旧过滤 ("high","medium") 使该桶对 R4 条目永不可达 —— 申报为
            # Critical 的 R4 finding 被静默丢弃 (zookeeper 审计实录: C 客户端
            # jute vector calloc 无判空, 实测 SIGSEGV/OOM-kill, 未进问题清单)。
            if sev not in ("critical", "high", "medium"):  # Low 留附录 B (含「正向确认」类)
                continue
            fid = f"{hid}-F{n}"
            link = fi.get("r3_link")
            if isinstance(link, str) and link.startswith("CAND-"):
                # r3_link 常带裁决注释 (如 "CAND-001 (R3 裁决 VERIFIED...)"), 去重行只显示候选 id
                dupes.append((fid, link.split()[0], sev))
                continue
            issues.append({"kind": "r4", "obj": fi, "hyp": hid, "fid": fid,
                           "severity": sev, "source": f"r4:{hid}", "key": fid})
    return issues, dupes


def _r4_grade_col(fi):
    """R4 条目证据等级列: 实证确认 → empirically_confirmed, else R4 申报。"""
    emp = fi.get("empirical_result")
    if isinstance(emp, dict) and str(emp.get("outcome", "")).upper() == "CONFIRMED":
        return "empirically_confirmed"
    if isinstance(emp, str) and emp.strip():
        return "r4 实证申报"
    return "r4 申报"


def _render_problem_list(cands, queue):
    """一、问题清单: 确认问题全集 (R3 REACHABLE ∪ R4 High/Medium),
    按 严重→高→中 三节, 每节表行 (SWR-V3.7-009)。"""
    issues, dupes = _confirmed_issues(queue, cands)
    if not issues:
        return "无确认问题（R3 空队且 R4 无 High/Medium 确认 findings 为合法终态）。"
    grouped = {"critical": [], "high": [], "medium": []}
    for it in issues:
        grouped.setdefault(it["severity"] if it["severity"] in grouped else "medium",
                           []).append(it)
    out = []
    for sev in ("critical", "high", "medium"):
        rows = grouped.get(sev, [])
        if not rows:
            continue
        out.append(f"### {SEVERITY_LABELS[sev]}（{len(rows)}）")
        out.append("| ID | 问题摘要 | 位置 | CWE | 证据等级 | 复核 |")
        out.append("|---|---|---|---|---|---|")
        for it in sorted(rows, key=lambda x: x["key"]):
            if it["kind"] == "r3":
                c = it["obj"]
                cwes = [f"CWE-{n}" for n in sorted(_parse_cwes(c))]
                sev_note = " ⚠override非法" if it["source"] == "invalid_override" else ""
                out.append(f"| {c.get('id')} | {_problem_summary(c)}{_tier_suffix(c)} | "
                           f"`{c.get('source_file')}:{c.get('source_line')}` | "
                           f"{', '.join(cwes) or '-'} | {c.get('evidence_grade', '-')} | "
                           f"{_refutation_line(c)}{sev_note} |")
            else:
                fi = it["obj"]
                cwes = [f"CWE-{n}" for n in sorted(_parse_cwes(fi))]
                out.append(f"| {it['fid']} | {_problem_summary(fi)} | {_r4_location(fi)} | "
                           f"{', '.join(cwes) or '-'} | {_r4_grade_col(fi)} | "
                           f"R4 确认（无 R3.5 复核） |")
    if dupes:
        out.append("")
        out.append("**同事实去重（SWR-V3.4.3-060）**: "
                   + "；".join(f"{fid} ↔ {link}（{SEVERITY_LABELS[sev]}）"
                               for fid, link, sev in dupes)
                   + " — R4 与 R3 候选同事实共享实证，不重复列。")
    return "\n".join(out)


def _render_problem_details(cands, queue):
    """二、问题详情: 确认问题全集每条一节 (SWR-V3.7-009)。
    R3: 位置/证据/前提/复核/实证/修复建议; R4: 申报证据/实证结果/fix。"""
    issues, _dupes = _confirmed_issues(queue, cands)
    if not issues:
        return "（无）"
    r4_fix = {}
    r4_links = {}
    for f in queue.get("r4_findings", []) or []:
        hid = f.get("hypothesis_id")
        if not hid:
            continue
        for fi in f.get("findings", []) or []:
            if fi.get("fix"):
                r4_fix.setdefault(hid, fi["fix"])
            if isinstance(fi.get("r3_link"), str) and fi["r3_link"]:
                r4_links[hid] = fi["r3_link"]
    # 同事实去重 (SWR-V3.4.3-060): r3_link 指向主申报方, 无独立 fix 时共享其 fix
    for hid, link in r4_links.items():
        r4_fix.setdefault(hid, r4_fix.get(link, ""))
    out = []
    for it in sorted(issues, key=lambda x: x["key"]):
        if it["kind"] == "r3":
            c = it["obj"]
            out.append(f"### {c.get('id')} — {_problem_summary(c)}"
                       f"（{SEVERITY_LABELS[it['severity']]}, 来源: {it['source']}）")
            out.append(f"- 位置/语言: `{c.get('source_file')}:{c.get('source_line')}`"
                       f"（{c.get('language') or c.get('lang') or '-'}）")
            cwes = [f"CWE-{n}" for n in sorted(_parse_cwes(c))]
            out.append(f"- CWE / claim_type: {', '.join(cwes) or '-'} / "
                       f"{c.get('claim_type') or '-'}")
            grade = c.get("evidence_grade", "-")
            if c.get("grade_recomputed_by"):
                grade += f"（{c['grade_recomputed_by']}）"
            out.append(f"- verdict + 证据分级: {c.get('verdict')} / {grade}")
            cc = c.get("call_chain") or []
            if cc:
                out.append(f"- 调用链（{c.get('call_chain_depth', len(cc))} 跳, "
                           f"{c.get('reachability_type', '-')}）: `{' -> '.join(cc)}`")
            if c.get("evidence"):
                out.append(f"- 证据: {c.get('evidence')}")
            bp = c.get("blocking_point")
            if bp:
                out.append(f"- 前提（PREC-CONDITIONAL-REACHABLE-001）: {bp}")
            rf = c.get("refutation")
            if isinstance(rf, dict) and rf:
                # SWR-V3.10.2-011: 补强/归因修正未签收 → （未复核）标记
                has_str = bool(rf.get("strengthened") or rf.get("attribution_correction")
                               or rf.get("attribution_corrections"))
                signed = bool(rf.get("strengthened_verified_by")
                              or rf.get("attribution_correction_verified_by"))
                str_mark = "" if (signed or not has_str) else "（未复核）"
                out.append(f"- 独立复核（R3.5）: {_refutation_line(c)}; "
                           f"votes={rf.get('votes')}, refute_count={rf.get('refute_count')}, "
                           f"survived={rf.get('survived')}"
                           + (f"; strengthened={rf.get('strengthened')}{str_mark}"
                              if rf.get("strengthened") else "")
                           + (f"; attribution_corrections={rf.get('attribution_corrections')}{str_mark}"
                              if rf.get("attribution_corrections") else ""))
            emp = c.get("empirical")
            if isinstance(emp, dict) and emp:
                # SWR-V3.10-005: 键名容错双形态——保留键 (outcome/evidence_numbers)
                # 优先; 缺失时回退标准键 (verdict/result/input/harness); 双形态
                # 都缺时占位 (绝不抛异常)。kernel 审计实录: 回填 dict 用标准键
                # 致实测数据在报告里全部渲染为 None。
                outcome = emp.get("outcome") or emp.get("verdict")
                nums = emp.get("evidence_numbers") or emp.get("result")
                extra = emp.get("input")
                harness = emp.get("harness")
                # SWR-V3.10.2-002: 实证保真度前缀 (equivalent/mechanism 标注)
                fid = emp.get("fidelity") or "real_target"
                fid_prefix = {"equivalent": "等价复现: ", "mechanism": "机制级: "}.get(fid, "")
                # SWR-V3.10.2-010: 实证产物目录守卫 warn (R0 前缀规则机械检查)
                path_warn = ""
                if harness and not _under_audit_results(harness):
                    path_warn = " [产物目录违规 warn]"
                out.append(f"- 实证记录（R5）: {fid_prefix}outcome={outcome}, "
                           f"evidence_numbers={nums}"
                           + (f", input={extra}" if extra else "")
                           + (f", harness={harness}{path_warn}" if harness else "")
                           + (f", report={emp.get('report')}" if emp.get("report") else ""))
            hyp_id = None
            if c.get("members"):
                hyp_id = (c.get("members") or [{}])[0].get("id")
            fix = r4_fix.get(hyp_id or "", "") if hyp_id else ""
            out.append(f"- 修复建议: {fix or '（主代理补充）'}")
        else:
            fi = it["obj"]
            out.append(f"### {it['fid']} — {_problem_summary(fi)}"
                       f"（{SEVERITY_LABELS[it['severity']]}, 来源: {it['source']}）")
            out.append(f"- 来源: R4 业务假说确认（{it['hyp']}）——"
                       f"R4 申报值分级，无 R3.5 独立复核")
            cwes = [f"CWE-{n}" for n in sorted(_parse_cwes(fi))]
            out.append(f"- CWE / claim_type: {', '.join(cwes) or '-'} / "
                       f"{fi.get('claim_type') or '-'}")
            out.append(f"- 位置: {_r4_location(fi)}")
            ir = fi.get("independent_review")
            if isinstance(ir, dict) and any(ir.get(k) for k in ("by", "method", "artifacts")):
                out.append(f"- 独立复核（③d）: {ir.get('by') or '?'} — "
                           f"{ir.get('method') or '-'}"
                           f"（artifacts: {ir.get('artifacts') or '-'}）")
            if fi.get("title"):
                out.append(f"- 要点: {fi.get('title')}")
            if fi.get("evidence"):
                out.append(f"- 证据: {fi.get('evidence')}")
            emp = fi.get("empirical_result")
            if emp:
                out.append(f"- 实证结果: {emp}")
            ts = fi.get("tracked_surfaces") or []
            if ts:
                out.append(f"- 追踪 surface: {', '.join(ts)}")
            out.append(f"- 修复建议: {fi.get('fix') or '（主代理补充）'}")
    return "\n".join(out)


def _render_appendix_a_needs_review(queue):
    """附录 A: NEEDS_REVIEW 清单 + 成因双分 + 同事实映射 (REQ-V3.1-092)。
    v3.9 (SWR-V3.9-003): collect 终态写 status=VERIFIED + verdict=NEEDS_REVIEW,
    旧过滤只认 status==NEEDS_REVIEW 致终态候选不渲染 (Pillow CAND-001 实录)——
    双语义容忍 (同 load_lenient 先例)。"""
    nr = [c for c in queue.get("candidates", [])
          if (c.get("status") == "VERIFIED" and c.get("verdict") == "NEEDS_REVIEW")
          or c.get("status") == "NEEDS_REVIEW"]
    if not nr:
        return "无 NEEDS_REVIEW 候选。"
    hyp_by_id = {f.get("hypothesis_id"): f for f in queue.get("r4_findings", []) or []}
    out = ["| ID | 成因 | correction_record 理由 | 位置 | 佐证注记 |", "|---|---|---|---|---|"]
    for c in sorted(nr, key=lambda x: x.get("id", "")):
        cr = c.get("correction_record") or []
        cr_txt = "; ".join(str(r) for r in cr) or "-"
        # SWR-V3.10.2-013: 环境受限 + 上游公开佐证 → 佐证注记列
        corroboration = ""
        if _needs_review_cause(c) == "环境受限":
            blob2 = " ".join(str(r) for r in cr)
            for kw in ("官方自认", "官方 issue", "上游", "先例", "佐证"):
                if kw in blob2:
                    corroboration = "上游佐证 (见 correction_record)"
                    break
        out.append(f"| {c.get('id')} | {_needs_review_cause(c)} | {cr_txt} | "
                   f"`{c.get('source_file')}:{c.get('source_line')}` | "
                   f"{corroboration or '-'} |")
    out.append("")
    out.append("**同事实映射（REQ-V3.1-092）**: NEEDS_REVIEW ↔ R4 hypothesis/finding")
    out.append("| NEEDS_REVIEW | 映射的 R4 假说 | 依据 |")
    out.append("|---|---|---|")
    for c in sorted(nr, key=lambda x: x.get("id", "")):
        mem = (c.get("members") or [{}])[0].get("id") if c.get("members") else None
        if mem and mem in hyp_by_id:
            out.append(f"| {c.get('id')} | {mem} | members[].id 命中 |")
        else:
            out.append(f"| {c.get('id')} | - | 主代理补充 |")
    return "\n".join(out)


def _render_appendix_b_process(project_root, queue, report_json):
    """附录 B: 规模对照/语言覆盖/FFI/R4 verdict/六门禁/覆盖账本——全部机械源。"""
    cands = queue.get("candidates", [])
    out = []
    # B.1 规模对照
    total = len(cands)
    terminal = sum(1 for c in cands if c.get("status") in
                   ("VERIFIED", "ESCALATED", "NEEDS_REVIEW"))
    out.append("### B.1 规模对照")
    out.append(f"- 候选: {total}（闭合率 {terminal}/{total} = "
               f"{round(terminal / total * 100) if total else 0}% 终态）")
    hyp_path = os.path.join(project_root, ".audit_results", "hypotheses.json")
    if os.path.exists(hyp_path):
        try:
            out.append(f"- 假设: {len(json.load(open(hyp_path)).get('hypotheses', []))}")
        except (OSError, ValueError):
            out.append("- 假设: （hypotheses.json 损坏）")
    else:
        out.append("- 假设: （hypotheses.json 未落盘）")
    sf_path = os.path.join(project_root, ".audit_results", "input_surface.json")
    surfaces = None
    if os.path.exists(sf_path):
        try:
            surfaces = json.load(open(sf_path))
            out.append(f"- surface: {len(surfaces.get('surfaces', []))}"
                       f"（含 conflicts {len(surfaces.get('conflicts', []))}）")
        except (OSError, ValueError):
            out.append("- surface: （input_surface.json 损坏）")
    else:
        out.append("- surface: （input_surface.json 未落盘）")
    # B.2 语言覆盖表 (组件角色现场重算)
    # v3.9 (SWR-V3.9-004): 双侧 lang 词汇归一后 join——surface.lang 为规范名
    # (python/c), language_inventory 行为扩展名形态 (.py/.c), 原直接字符串键
    # 比对致计数恒 0 (Pillow 实录)。归一失败归 unknown 桶。
    out.append("### B.2 语言覆盖表")
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import surface_mapper as _sm
        inv = _sm.language_inventory(project_root)
        surf_langs = {}
        if surfaces:
            for s in surfaces.get("surfaces", []):
                lg = _norm_lang(s.get("lang"))
                if lg:
                    surf_langs[lg] = surf_langs.get(lg, 0) + 1
        cand_langs = {}
        for c in cands:
            lg = _norm_lang(c.get("language") or c.get("lang"))
            if lg:
                cand_langs[lg] = cand_langs.get(lg, 0) + 1
        inv_rows = {}
        for r in inv:
            lg = _norm_lang(r.get("lang")) or "unknown"
            agg = inv_rows.setdefault(lg, {"count": 0, "roles": set()})
            agg["count"] += int(r.get("file_count", 0) or 0)
            if r.get("component_role"):
                agg["roles"].add(r["component_role"])
        out.append("| 语言 | 文件数 | 组件角色 | surfaces | 候选 | 判据① |")
        out.append("|---|---|---|---|---|---|")
        for lg in sorted(inv_rows):
            agg = inv_rows[lg]
            has_sf = surf_langs.get(lg, 0) >= 1
            has_cand = cand_langs.get(lg, 0) >= 1
            judge = "✓" if (has_sf and has_cand) else "-"
            role = "/".join(sorted(agg["roles"])) or "-"
            out.append(f"| {lg} | {agg['count']} | {role} | "
                       f"{surf_langs.get(lg, 0)} | {cand_langs.get(lg, 0)} | {judge} |")
    except Exception:
        out.append("（language_inventory 现场重算失败, 角色列由主代理补充）")
    # B.3 FFI 边界表
    out.append("### B.3 FFI 边界表")
    bnd = []
    if surfaces:
        bnd = [s for s in surfaces.get("surfaces", [])
               if s.get("boundary_kind") or s.get("lang_pair")]
    if not bnd:
        out.append("无 FFI 边界面（boundary_kind/lang_pair 未标记）。")
    else:
        out.append("| surface | lang_pair | boundary_kind | 追踪 | 裁决 |")
        out.append("|---|---|---|---|---|")
        tracked = set(_tracked_ids(project_root, queue, surfaces))
        for s in bnd:
            t = "✓" if s.get("id") in tracked else "-"
            out.append(f"| {s.get('id')} | {s.get('lang_pair', '-')} | "
                       f"{s.get('boundary_kind', '-')} | {t} | 主代理补充 |")
    # B.4 R4 verdict 表
    out.append("### B.4 R4 假说 verdict 表")
    r4 = queue.get("r4_findings", []) or []
    if not r4:
        out.append("R4 未运行/未收集。")
    else:
        out.append("| 假说 | verdict | findings |")
        out.append("|---|---|---|")
        for f in r4:
            out.append(f"| {f.get('hypothesis_id')} | {f.get('verdict', '-')} | "
                       f"{len(f.get('findings', []) or [])} |")
    # B.5 六门禁断言
    out.append("### B.5 六门禁断言")
    violations, err = _gates_for_report(project_root, queue, surfaces)
    if err:
        out.append(f"（{err}）")
    else:
        gate_names = {v.get("gate") for v in violations}
        gate_rows = [("no_pending", "① no_pending"),
                     ("no_static_only_reachable", "② REACHABLE 无 static_only"),
                     ("empirical_required", "③ 实证类 100% confirmed"),
                     ("r4_all_verified", "④ H1-H7 全 VERIFIED"),
                     ("dispatched_reconcile", "⑤ 对账零差异"),
                     ("escalated", "⑥ escalated=0 或签收"),
                     ("coverage", "⑦ surface 覆盖率 100%"),
                     ("target_kind", "⑧ target_kind_required"),
                     ("resurrection", "③c 复活攻击完成度"),
                     ("r4_independent_review", "③d R4 confirmed 独立复核")]
        out.append("| 门禁 | 结果 | 详情 |")
        out.append("|---|---|---|")
        for key, name in gate_rows:
            hits = [v for v in violations if v.get("gate") == key]
            if hits:
                out.append(f"| {name} | FAIL | {hits[0]} |")
            else:
                out.append(f"| {name} | PASS | - |")
        r4f = [v for v in violations if v.get("gate") == "r4_feedback"]
        if r4f:
            out.append(f"- r4_feedback 告警（warn 级）: {r4f[0]}")
    # B.6 覆盖账本
    out.append("### B.6 覆盖账本（REQ-V3.4-007）")
    cl = (report_json or {}).get("coverage_ledger")
    if not cl or cl.get("status") == "LEDGER_UNAVAILABLE":
        out.append("账本缺失（resources/issue_coverage_matrix.json 不可读）。")
    else:
        out.append(f"- 缺口格 {cl.get('gap_cell_count')}: "
                   f"{'、'.join(cl.get('gap_cells', [])) or '无'}")
        out.append(f"- 饱和格 {cl.get('saturated_cell_count')}（count≥15 不建议再选题）")
    # B.7 v3.11 (SWR-V3.11-010): 审计树与部署物差异声明
    out.append("### B.7 审计树与部署物差异（SWR-V3.11-009/010）")
    snap_path = os.path.join(project_root, ".audit_results", "scope_snapshot.json")
    div = None
    if os.path.exists(snap_path):
        try:
            div = json.load(open(snap_path)).get("build_divergence")
        except (OSError, ValueError):
            pass
    if div is None:
        out.append("（scope snapshot 无构建差异段——旧快照兼容跳过）")
    elif not div:
        out.append("无构建清单声明的依赖差异（审计树与部署物一致声明）。")
    else:
        for d in div:
            out.append(f"- `{d.get('manifest')}` ({d.get('kind')}): "
                       f"缺失/空目录 {d.get('missing_or_empty') or '无'}"
                       f"（声明样例 {d.get('declared_dirs_sample') or '无'}）")
    return "\n".join(out)


def _under_audit_results(path):
    """SWR-V3.10.2-010: 实证产物目录守卫——harness 路径须落在项目
    .audit_results/ 下 (R0 前缀规则); 相对路径默认视为合规 (无法判定时
    不误报)。"""
    if not isinstance(path, str) or not path:
        return True
    return ".audit_results" in path

def render_report_md(project_root, report_json=None):
    """SWR-V3.7-002: 机械渲染完整报告 md → .audit_results/reachable_vulnerabilities_report.md。
    铁律: 所有可选输入缺失时降级渲染占位, 绝不抛异常 (test_end_to_end 最小队列形态)。
    去项目化: 模板文本零项目名零绝对路径, 内容全部来自队列/R1 产物。"""
    queue = load_queue(project_root)
    cands = queue.get("candidates", [])
    sf_path = os.path.join(project_root, ".audit_results", "input_surface.json")
    surfaces = None
    if os.path.exists(sf_path):
        try:
            surfaces = json.load(open(sf_path))
        except (OSError, ValueError):
            surfaces = None
    parts = [
        "# 可达性严重漏洞审计报告（reachable-critical-audit v3）",
        f"- 生成方式: `--stage report` 机械生成（队列派生, REQ-V3.3.2-007）；"
        f"主代理仅补充 修复建议/结论/审计基线",
        f"- 日期: {datetime.date.today().isoformat()}",
        "- 项目/审计基线: （主代理补充）",
        "",
        "## 一、问题清单（按严重程度排序）",
        _render_problem_list(cands, queue),
        "",
        "## 二、问题详情",
        _render_problem_details(cands, queue),
        "",
        "## 三、修复建议与结论（主代理补充）",
        "> 本段由主代理补充；补充后**不得重跑 `--stage report`**（机械渲染会覆盖本段）。",
        "",
        "## 附录 A：NEEDS_REVIEW 清单与同事实映射",
        _render_appendix_a_needs_review(queue),
        "",
        "## 附录 B：审计过程信息",
        _render_appendix_b_process(project_root, queue, report_json),
        "",
    ]
    md = "\n".join(parts)
    out_dir = os.path.join(project_root, ".audit_results")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "reachable_vulnerabilities_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    return path


MAX_ATTEMPTS = 3


def stage_bump_attempt(project_root, candidate_id):
    """REQ-V3-092: 候选 attempt+1; >=MAX_ATTEMPTS 转 escalated 显式终态。"""
    queue = load_queue(project_root)
    for c in queue["candidates"]:
        if c.get("id") == candidate_id:
            if c.get("status") == "ESCALATED":
                break  # 已升级主代理, 不再累加 (幂等保护)
            c["attempt"] = c.get("attempt", 0) + 1
            if c["attempt"] >= MAX_ATTEMPTS:
                c["status"] = "ESCALATED"
                c["escalated_reason"] = f"attempt >= {MAX_ATTEMPTS} (验证失败/失联)"
            break
    save_queue(project_root, queue)
    print(json.dumps({"status": "ATTEMPT_BUMPED", "id": candidate_id}))


def stage_workflow_script(project_root, mode="verify", batch_size=4):
    """REQ-V3-091: 从当前队列导出 Mode W workflow 脚本 (转调 workflow_export.py,
    避免循环 import)。workflow 脚本只验证并返回 verdicts; 主代理用
    --stage collect / --stage bump-attempt 落盘, 队列是唯一事实源。
    v3.4.3 (SWR-V3.4.3-003): mode=resurrect 转调 export_script_resurrect
    (此前无 CLI 入口, 需 workflow_export 直调 + 主代理手工落盘)。"""
    export_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "workflow_export.py")
    if not os.path.exists(export_py):
        print(json.dumps({"status": "ERROR", "msg": f"workflow_export.py 缺失: {export_py}"}))
        return 1
    # 直接 import 执行 (同目录树, 无循环: workflow_export 的 import batch_verify 命中已加载模块)
    import importlib.util
    spec = importlib.util.spec_from_file_location("workflow_export", export_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mode == "resurrect":
        result = mod.export_script_resurrect(project_root, batch_size=batch_size)
    else:
        result = mod.export_script(project_root, mode=mode, batch_size=batch_size)
    # v3.2.2 (REQ-V3.2.2-018/019): 入队前 scope diff——R0 快照 vs 现状,
    # 子模块物化/目录变化时附 scope_changed 提示 (mbedtls 审计: R4 智能体
    # submodule update 使 R2 drop 理由作废, 需复活重验)
    ar_dir = os.path.join(project_root, ".audit_results")
    snap_path = os.path.join(ar_dir, "scope_snapshot.json")
    if os.path.exists(snap_path):
        try:
            import surface_mapper as _sm
            snap = json.load(open(snap_path))
            diff = _sm.scope_diff(project_root, snap)
            result["scope_changed"] = diff
            if diff.get("changed"):
                result["scope_advice"] = (
                    "scope 已变更: R2 的 scope_dependent drop (树外不可验证类) "
                    "理由可能失效——按 R3.5-N 复活流程重开受影响候选")
                # SWR-V3.10.2-018: 物化增量面重开建议——物化目录与 R1 面
                # entry_points 路径交叉 (建议级, 主代理裁决后落盘 scope_review)
                try:
                    changed_dirs = [str(x.get("path") or x.get("dir") or "")
                                    for x in (diff.get("changes") or [])]
                    changed_dirs = [d for d in changed_dirs if d]
                    isurf_path = os.path.join(ar_dir, "input_surface.json")
                    reopen_candidates = []
                    if changed_dirs and os.path.exists(isurf_path):
                        isurf = json.load(open(isurf_path))
                        for s in isurf.get("surfaces", []) or []:
                            for ep in s.get("entry_points", []) or []:
                                f = ep.get("file") or ""
                                for d in changed_dirs:
                                    if d in f:
                                        reopen_candidates.append({
                                            "surface_id": s.get("id"),
                                            "file": f,
                                            "materialized_dir": d})
                                        break
                    if reopen_candidates:
                        result["scope_reopen_advice"] = {
                            "note": "物化目录相关面建议重开测绘 (R1 面 entry_points "
                                    "落于新物化目录内——物化前标树外不可验证的裁决 "
                                    "前提可能已失效); 主代理裁决后以 write_scope_review "
                                    "落盘 scope_review.jsonl",
                            "candidates": reopen_candidates[:10],
                            "total": len(reopen_candidates)}
                except (OSError, ValueError):
                    pass
        except (ImportError, ValueError):
            pass
    # v3.9 (SWR-V3.9-007): payload 落盘——next_step 的"整读整传"条款需要一个
    # 真实存在的文件 (旧实现只把 payload 打在 stdout, 主代理手工重提取, Pillow 实录)
    pl = result.get("payload")
    if pl is not None:
        pl_rel = f".audit_results/{mode}_payload.json"
        pl_path = os.path.join(project_root, ".audit_results", f"{mode}_payload.json")
        try:
            os.makedirs(os.path.dirname(pl_path), exist_ok=True)
            with open(pl_path, "w", encoding="utf-8") as f:
                json.dump(pl, f, ensure_ascii=False, indent=1)
            result["payload_file"] = pl_rel
            if isinstance(result.get("next_step"), str):
                result["next_step"] += (f"\n  - payload 已落盘 {pl_rel}: args 从该文件 "
                                        f"整读整传 (W6 §10.3)")
            print(f"payload written: {pl_path}", file=sys.stderr)
        except OSError as e:
            print(f"payload write failed: {e}", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def stage_status(project_root):
    """Print queue status summary."""
    queue = load_queue(project_root)
    candidates = queue["candidates"]
    statuses = {}
    verdicts = {}
    cwes = {}
    for c in candidates:
        s = c.get("status", "UNSET")
        statuses[s] = statuses.get(s, 0) + 1
        v = c.get("verdict", "UNSET")
        verdicts[v] = verdicts.get(v, 0) + 1
        cwe = c.get("cwe_id", "?")
        cwes[cwe] = cwes.get(cwe, 0) + 1

    priorities = {}
    for c in candidates:
        p = c.get("priority", 99)
        priorities[p] = priorities.get(p, 0) + 1

    print(json.dumps({
        "status": "QUEUE_STATUS",
        "total": len(candidates),
        "by_status": statuses,
        "by_verdict": verdicts,
        "by_priority": dict(sorted(priorities.items())),
        "by_cwe": dict(sorted(cwes.items(), key=lambda x: -x[1])[:15])
    }))





def _next_batch_id(project_root):
    """Find the next batch number for continuation."""
    existing = glob.glob(os.path.join(project_root, ".audit_results", "batch_*.json"))
    nums = []
    for p in existing:
        try:
            nums.append(int(os.path.basename(p).split("_")[1].split(".")[0]))
        except (ValueError, IndexError):
            pass
    return max(nums) + 1 if nums else 1


def _build_context(cand, project_root=None):
    """Build a concise context summary for the task prompt.
    W5 回归发现: v3 候选用 source_file/sink_type 字段, v2 风格用 file_path/
    cwe_id——两套字段名兼容映射, 否则 prompt 里全是 '?'。
    W6/Pester 发现: v3 候选无 sink_content/language 字段, prompt 里
    "Sink 代码: `CWE-94`" / "语言: ?" 误导 verifier——sink 缺失时读源文件
    行内容兜底, language 按扩展名映射。"""
    src = cand.get("file_path", cand.get("source_file", "?"))
    line = cand.get("source_line", cand.get("line_number", "?"))
    sink = (cand.get("sink_content") or cand.get("source_pattern") or "")[:200]
    if not sink and isinstance(line, int) and src and src != "?":
        try:
            resolved = src
            if project_root and not os.path.isabs(src):
                resolved = os.path.join(project_root, src)
            lines = open(resolved, errors="ignore").read().splitlines()
            if 1 <= line <= len(lines):
                sink = lines[line - 1].strip()[:200]
        except OSError:
            pass
    if not sink:
        sink = cand.get("sink_type") or ""
    # SWR-V3.4.3-021: 优先候选级 lang 字段 (v3.2 数据模型), language 为旧形态
    # 兼容; 均缺才按扩展名推断 (cpp-httplib 批次实证: .h/.cpp 扩展名映射
    # 缺失致 C++ 项目被推断 unknown, 任务书语言分片失效)
    language = cand.get("lang") or cand.get("language")
    if not language:
        language = _EXT_LANG.get(os.path.splitext(str(src))[1].lower(), "unknown")
    ctx = {
        "file": src,
        "line": line,
        "sink": sink,
        "language": language,
        "cwe": cand.get("cwe_id", cand.get("sink_type", "?")),
        "category": cand.get("category", "?"),
        "type": cand.get("type", "?"),
        "sources_regex": cand.get("sources_regex", []),
        "verification_logic": cand.get("verification_logic", ""),
        "reachability_constraints": cand.get("reachability_constraints", ""),
    }
    return ctx


def _load_target_kind(project_root):
    """SWR-V3.2.1-012: verify_queue.target_kind 优先, 回退 target_kind.json;
    均缺 → None (不注入, 兼容旧队列)。"""
    try:
        q = json.load(open(os.path.join(project_root, ".audit_results",
                                        "verify_queue.json")))
        tk = q.get("target_kind")
        if tk:
            return tk
    except Exception:
        pass
    try:
        d = json.load(open(os.path.join(project_root, ".audit_results",
                                        "target_kind.json")))
        return d.get("recommendation")
    except Exception:
        return None


def _is_write_read_family(cand):
    """SWR-V3.2.1-011 触发条件: write→read 注入族候选 (写入端→消费端出站/重定向)。"""
    text = " ".join(str(cand.get(k) or "") for k in
                    ("claim_type", "sink_type", "summary", "cwe")).lower()
    return any(k in text for k in ("write", "写入", "注入", "redirect", "重定向",
                                   "出站", "outbound", "config", "配置"))


def _build_prompt(cand, ctx, project_root):
    """Build the task prompt for a vulnerability-verifier subagent.

    The subagent has full access to read, grep, and explore tools.
    This prompt only provides context — it does NOT constrain how
    the subagent verifies the finding.
    """
    is_property_check = cand.get("type") == "PROPERTY_CHECK"

    # v3.2.3 (Lua 审计): category 为 "?" (未分类) 时不再渲染 "(?)"——
    # 曾误导 verifier 把类别占位符当作 CWE 注释
    cat = ctx["category"]
    cwe_line = (f"- **CWE**: {ctx['cwe']}"
                + (f" (类别: {cat})" if cat and cat != "?" else ""))

    prompt = f"""你是一个 vulnerability-verifier 子智能体。你有完整的代码阅读和分析工具（read、grep 等）。

## 任务上下文
- **候选 ID**: {cand["id"]}
- **文件**: {ctx["file"]}:{ctx["line"]}
- **语言**: {ctx["language"]}
{cwe_line}
- **Sink 代码**: `{ctx["sink"]}`
"""
    if ctx["sources_regex"]:
        prompt += f"- **Source 正则**: {ctx['sources_regex']}\n"
    prompt += f"- **项目路径**: {project_root}\n"

    # v3.2.1 (SWR-V3.2.1-010/011/012): target_kind 存在性规则 + 两盲区预检
    target_kind = _load_target_kind(project_root)
    if target_kind == "library":
        prompt += """
## 目标类型存在性规则（v3.2.1, target_kind=library）
- 公共 API 即信任边界（库型先例）：API 静态存在即攻击面
- 仓内调用者缺失**不是**阻断；死代码豁免规则不适用（库的调用者在仓外）
- 部署前提不适用；平台限定路径仅记录型
"""
    elif target_kind == "hybrid":
        prompt += """
## 目标类型存在性规则（v3.2.1, target_kind=hybrid）
- 按候选所属组件装载规则：库型组件=公共 API 即边界；应用型组件=应用规则（下表）
- 无法确定组件归属时按 application 规则（保守）
"""
    elif target_kind == "application":
        prompt += """
## 目标类型存在性规则（v3.2.1, target_kind=application）
- 默认可达三层检查的第三层**必须**核对 shipped 配置文件的提交实际值（不是代码零值）
- 运行时注册必须核实（路由/DI 注册真实发生），不得以框架设计推定
- platform_precondition（平台限定路径，如 Windows 证书路径）必须显式标注
"""

    # SWR-V3.3.2-014: 步骤 0.5 按型门控——动态导入风险语言或 application 目标
    # 注入完整预检；静态编译语言降为一行 build 列表核对（71 候选 boilerplate 削减）
    step05 = (IMPORTABILITY_STEPS.get(ctx["language"], IMPORTABILITY_STEPS["default"])
              if ctx["language"] in IMPORTABILITY_FULL_LANGS or target_kind == "application"
              else STATIC_SHORT_BY_FAMILY.get(ctx["language"],
                                              IMPORTABILITY_STEPS["static_short"]))

    prompt += f"""
## 强制分析步骤（语言无关）

### 步骤 0（v3.1 强制，W6 §17.10）: 承重前提验证
回溯开始前，先 grep 一句话能证实/证伪的**假设承重前提**（严格相等门控/默认参数/
调用存在性/常量值）。前提断裂 → 立即终止回溯，verdict 按断裂方向判定。
verifier 最常犯的错误是"沿假设惯性向前推，未回头验证承重前提"（W6 §17.10/§19.5）。

{step05}
- 模板产物存在性（v3.11, SWR-V3.11-008）: sink 所在模板/生成器文件不随源码
  构建但随产物生成进入部署——存在性按「模板 → 实例化产物」链判定（产物生成
  链存在即存在性成立）; 阻断论证引用「零导出组件」类清单事实时必须核对模板
  产物形态（源码树清单 ≠ 部署物清单）
### 步骤 1: 逆向调用链回溯（最小深度 3 层）
1. 读取 {ctx['file']} L{ctx['line']} 周围代码，确认 sink 点
2. 使用 grep 反向查找直接调用者（Caller_L1），记录调用处 file:line:function
3. 追踪 Caller_L1 的每个参数来源，找到 Caller_L2
4. 重复直到追溯到外部输入源（请求参数/文件/Binder IPC/蓝牙 HCI 事件等）
5. **质量门禁**: call_chain 必须 >= 3 层（Sink ← L1 ← L2），不足则继续向上搜索
6. **混合语言项目（v3.8, SWR-V3.8-006）**: 调用点搜索必须覆盖跨语言调用形态——
   语言别名/桥接层/绑定层（如 JVM 系互调别名、FFI 绑定、解释器嵌入）。只 grep
   同语言标识符会漏掉跨语言调用点导致 UNREACHABLE 误判（函数存在≠被调用，
   反之亦然：调用存在≠按同语言形态书写）
7. **edge_evidence 契约（v3.8, SWR-V3.8-006）**: edge_evidence 逐跳一条——
   call_chain 相邻两跳之间一条 {{edge, proof}}，总条数 ≥ call_chain 长度 - 1。
   **禁止合并多跳为一条**（合并边会被机械分级降级 static_only 并触发补边波次）；
   每跳的 proof 必须指名调用处 file:line 与调用形态（直接/别名/桥接）
8. **路径格式（v3.10, SWR-V3.10-011）**: call_chain / edge_evidence 的 file
   一律用**相对项目根**路径（不带项目根前缀）——混用会原样进入报告

### 步骤 1.5: upstream 修复搜索（v3.10, SWR-V3.10-011）
对 sink 搜索 upstream 修复/已知缺陷报告作为外部佐证：
- `git log --all --oneline -S <sink 关键标识>` 与公开 CVE/补丁列表检索
- 命中时：引用 commit hash 并核对**本树是否已含该修复**——"快照落于修复
  前/后窗口"是候选可信度与报告语境的关键事实，写入 evidence
- **首发归属（v3.10 增补）**：命中"公开补丁但未合并"或"已有 CVE/公开
  报告"时，标注发现链（发现者/补丁作者/时间戳/列表链接）与补丁状态
  （未合并/已合并未回移），evidence 写明"非首发发现"——主代理收尾按
  "推补丁合并 + 佐证材料"路径，申报不得以首发口径
- **可选步·构建依赖 CVE 对账注记（v3.10.2, SWR-V3.10.2-017）**: 仅当 R1
  context 输出含 pinned 第三方依赖清单时执行——对关键依赖（解码器/解析器
  执行主体等直接决定攻击面的依赖）查询 OSV/官方 advisory 的已知 CVE 状态,
  产出 dependency_cve_notes 写入 evidence 尾段（注记级: 不改变 verdict,
  供报告附录 B 与申报语境引用）。无依赖清单或非关键依赖 → 跳过

### 步骤 2: 多态穿透
遇接口/抽象类/虚函数/特征(trait)，搜索所有具体实现类继续回溯

### 步骤 3: 跨边界判定
调用链到达任何进程/IPC/跨模块边界时，边界即 sink：
- 自由文本参数来自外部输入拼接 → REACHABLE_ACROSS_BOUNDARY
- 强制参数化/类型安全/白名单 → UNREACHABLE
- v3.3 (REQ-V3.3-008): 库组件的宿主 API 边界（trust_boundary=host_api）——
  数据经宿主对本库公共 API 的调用进入时，「跨库边界」≠「跨主体边界」：
  env/调用参数控制者=启动者本人（同主体）时 reachability_type 用 DIRECT 并
  在 evidence 注明信任边界几何，不得默认升级 ACROSS_BOUNDARY（惯例假设幻觉，
  R3.5 证伪者将拦截）
- v3.10.2 (SWR-V3.10.2-016): 平台信任模型对照——「同主体」判定前必须过目标
  平台的信任模型清单（下方注入）: 同设备其他应用经导出组件/意图参数注入、
  平台鉴权中介、网络策略门、沙箱语义等平台机制可能使「库外调用者」≠「同主体」
- v3.11 (SWR-V3.11-001): 攻击者主体层级判定——evidence 必须注明 attacker_tier
  四层之一: same_process (攻击者与目标同进程) / same_device_cross_app (同设备
  其他应用经导出组件/意图参数/跨应用调用注入) / system_broker (经系统中介:
  服务绑定/用户授权中介/系统回调) / remote (网络可达内容)。DIRECT+host_api
  通常推导 same_process, 但平台组件注入面会使其升为 same_device_cross_app——
  该层级决定申报口径与 CVSS 基线 (AV:L 同设备 vs AV:N 远程), 不得含糊

### 步骤 4: 阻断检测
- 强类型转换、掩码（`& 0xFF`）、参数化绑定（`?` 占位符）、边界检查（`offset+len <= total`）
- 阻断必须覆盖所有攻击者可控制维度——多维度中只要有一维无阻断，仍为 REACHABLE
- 运行时版本条件（v3.11, SWR-V3.11-011）: 版本 API 级判断（版本宏/运行时能力
  检测）与构建变体差异（调试/发布配置）影响攻击面维度——同一代码路径在不同
  平台版本有不同攻击面（低版本无限制/高版本有门）; 阻断论证必须按**受影响
  版本区间**陈述; 注入参数/调试面被发布构建过滤的差异作为前提维度写进 evidence

### 步骤 5: 路径覆盖
- 列出所有到达该 Sink 点的调用路径
- 多条路径中只要有一条无阻断 → 该点 REACHABLE
"""

    if _is_write_read_family(cand):
        prompt += """### 步骤 5.5（v3.2.1，write→read 注入族强制，W6 §25.3）: 消费端中间层枚举
本候选为写入端→消费端复合链。对消费端执行：
1. 中间层横向枚举：adapter 与 domain 之间逐层列出缓存/门闩/降级/拦截器——
   不能只沿调用链直查（既有先例: 缓存前置门闩被整层漏掉的前车之鉴）
2. 缓存层三查：
   - 错误分支方向：错误处理落在成功分支 = 写反死代码（Go 习语示例:
     `if err == nil` 块内处理错误分支）；缓存未命中返回什么（空实体 +
     无错误返回会短路 DB 回源）
   - 写读形状一致：缓存写入方与读取方序列化形状是否匹配
     （writer 单对象 vs reader 切片 → 往返必然失败）
   - 缓存键写路径：Save/Modify 是否失效/回填缓存键——不写则新写入的 DB 行
     永远进不了读路径
3. 状态依赖（缓存命中的条件态 vs 默认态）写入 evidence；默认态不可达时
   blocking_point 写明门闩层
"""

    prompt += """
### 步骤 6: 结论
无法明确判定 → NEEDS_REVIEW（不允许默认判定或静默丢弃）
NEEDS_REVIEW 成因三选一并在 evidence 注明 (v3.10.2, SWR-V3.10.2-013):
  保守裁决 (防御证据充分但门禁压力下保守) / 证据不足 (前提或调用边无法取证)
  / 环境受限 (无目标平台运行面——无设备/无运行库/依赖未物化)
"""
    prompt += """## 输出格式（强制 JSON，不要其他文字）
{
  "verdict": "REACHABLE | UNREACHABLE | NEEDS_REVIEW",
  "reachability_type": "DIRECT | ACROSS_BOUNDARY | INDIRECT",
  "call_chain": ["file:line:function", "file:line:function", "file:line:function", ...],
  "call_chain_depth": <int>,
  "blocking_point": "file:line / no production callers / N/A",
  "evidence": "包含调用链和每层数据流路径分析的说明",
  "cwe": ["CWE-xxx"],
  "evidence_grade": "static_only | edge_proven",
  "edge_evidence": [{"edge": "f1->f2", "proof": "grep 命中: file:line"}],
  "claim_type": "crash|panic|oom|unbounded|xss|protocol_dos|rce|other"
}
## v3 强制规则（REQ-V3-040/042/046）
1. call_chain 每相邻两跳必须附 edge_evidence（grep 调用方的命中行）; 缺证据 → evidence_grade=static_only
2. REACHABLE 且无逐跳边证据 → static_only（不得申报）
3. 死代码豁免: 无生产调用者 → blocking_point="no production callers", verdict=UNREACHABLE, 不强制凑 3 层链
4. 前提维度: platform_precondition 无 platform_evidence → NEEDS_REVIEW
5. claim 与实证自洽 (SWR-V3.3.2-033): 实证结果与 claim_type 矛盾时，必须按实证方向
   修正 claim 并在 evidence 说明（如实证 exit 0 且确定性崩溃不可达，则不得声明 crash，
   改 other 并记录实测结果）
6. 计数类观测不做可复现证据 (SWR-V3.4.4-007): 素性试除次数、重试次数等
   几何随机变量单次观测波动大（同输入两次运行方向可翻转）——只标注
   "单次观测, 数量级参考", 不得作为可复现证据引用（jsrsasign CAND-010
   MR 计数 79/48 vs 55/69 实测翻转）
"""
    return prompt


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 batch_verify.py <project_root> --stage next")
        print("  python3 batch_verify.py <project_root> --stage collect --batch <n> --cand-001='{...}' --cand-002='{...}'")
        print("  python3 batch_verify.py <project_root> --stage assert")
        print("  python3 batch_verify.py <project_root> --stage status")
        print("  python3 batch_verify.py <project_root> --stage workflow-script [--mode verify|refutation] [--batch-size N]")
        print("  python3 batch_verify.py <project_root> --stage bump-attempt --file <candidate_id>")
        sys.exit(1)

    project_root = sys.argv[1]
    stage = None
    batch_id = None
    batch_size = None
    findings_file = None
    from_journal = None
    verdicts = {}
    sinks_file = None
    sinks_inline = None
    mode = "verify"
    expect_ids = []
    force = False
    reopen_id = None
    reopen_reason = None

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--stage" and i + 1 < len(args):
            stage = args[i + 1]
        elif arg.startswith("--stage="):
            stage = arg.split("=", 1)[1]
        elif arg.startswith("--from-journal="):
            from_journal = arg.split("=", 1)[1]
        elif arg == "--from-journal" and i + 1 < len(args):
            from_journal = args[i + 1]
        elif arg.startswith("--expect="):
            expect_ids = arg.split("=", 1)[1].split(",")
        elif arg == "--expect" and i + 1 < len(args):
            expect_ids = args[i + 1].split(",")
        elif arg.startswith("--batch="):
            batch_id = int(arg.split("=", 1)[1])
        elif arg == "--batch" and i + 1 < len(args):
            batch_id = int(args[i + 1])
        elif arg.startswith("--sinks-file="):
            sinks_file = arg.split("=", 1)[1]
        elif arg == "--sinks-file" and i + 1 < len(args):
            sinks_file = args[i + 1]
        elif arg.startswith("--sinks="):
            sinks_inline = arg.split("=", 1)[1]
        elif arg.startswith("--batch-size="):
            batch_size = int(arg.split("=", 1)[1])
        elif arg == "--batch-size" and i + 1 < len(args):
            batch_size = int(args[i + 1])
        elif arg == "--force":
            force = True
        elif arg.startswith("--reopen-id="):
            reopen_id = arg.split("=", 1)[1]
        elif arg == "--reopen-id" and i + 1 < len(args):
            reopen_id = args[i + 1]
        elif arg.startswith("--reopen-reason="):
            reopen_reason = arg.split("=", 1)[1]
        elif arg == "--reopen-reason" and i + 1 < len(args):
            reopen_reason = args[i + 1]
        elif arg.startswith("--mode="):
            mode = arg.split("=", 1)[1]
        elif arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
        elif arg.startswith("--file="):
            findings_file = arg.split("=", 1)[1]
        elif arg == "--file" and i + 1 < len(args):
            findings_file = args[i + 1]
        elif arg.startswith("--cand-"):
            parts = arg.split("=", 1)
            if len(parts) == 2:
                # SWR-V3-050: 按字面 id 匹配，接受任意前缀
                # --cand-011=... → CAND-011; --cand-R05-001=... → R05-001;
                # --cand-CAND-011=... 也接受（向后兼容）
                num = parts[0].replace("--cand-", "")
                cand_id = num if num.startswith("CAND-") else f"CAND-{num}"
                try:
                    verdicts[cand_id] = _load_lenient_json(parts[1])
                except ValueError as e:
                    print(f"Error parsing {parts[0]}: {e}", file=sys.stderr)
                    sys.exit(1)

    if not stage:
        print("Error: --stage is required", file=sys.stderr)
        sys.exit(1)

    if stage == "next":
        # SWR-V3-054: --batch-size 生效于逐候选出队
        if batch_size and batch_size != BATCH_SIZE:
            stage_next(project_root, batch_size=batch_size)
        else:
            stage_next(project_root)
    elif stage == "r4-collect":
        if not findings_file:
            print("Error: r4-collect requires --file findings.json", file=sys.stderr)
            sys.exit(1)
        stage_r4_collect(project_root, findings_file)
    elif stage == "r4-assert":
        sys.exit(stage_r4_assert(project_root))
    elif stage == "tracked-ids":
        sys.exit(stage_tracked_ids(project_root))
    elif stage == "bump-attempt":
        stage_bump_attempt(project_root, findings_file or "")
    elif stage == "workflow-script":
        sys.exit(stage_workflow_script(project_root, mode=mode, batch_size=batch_size or 4))
    elif stage == "report":
        stage_report(project_root, force=force)
    elif stage == "reopen":
        if not reopen_id:
            print("Error: reopen requires --reopen-id <id>", file=sys.stderr)
            sys.exit(1)
        sys.exit(stage_reopen(project_root, reopen_id, reopen_reason))
    elif stage == "scope-review":
        # SWR-V3.11-018 补充: write_scope_review 的 CLI 入口 (此前仅 API 形态,
        # 无调用点——过设计/死代码评估发现)
        _dir = None
        _decision = None
        _reason = ""
        for j, arg in enumerate(args):
            if arg.startswith("--dir="):
                _dir = arg.split("=", 1)[1]
            elif arg == "--dir" and j + 1 < len(args):
                _dir = args[j + 1]
            elif arg.startswith("--decision="):
                _decision = arg.split("=", 1)[1]
            elif arg == "--decision" and j + 1 < len(args):
                _decision = args[j + 1]
            elif arg.startswith("--reason="):
                _reason = arg.split("=", 1)[1]
            elif arg == "--reason" and j + 1 < len(args):
                _reason = args[j + 1]
        if not _dir or _decision not in ("reopen", "keep"):
            print("Error: scope-review requires --dir <d> --decision reopen|keep "
                  "[--reason <r>]", file=sys.stderr)
            sys.exit(1)
        row = write_scope_review(project_root, _dir, _decision, _reason)
        print(json.dumps({"status": "SCOPE_REVIEW_WRITTEN", **row},
                         ensure_ascii=False))
        sys.exit(0)
    elif stage == "collect":
        # v3.2.2 (REQ-V3.2.2-024): --from-journal 桥接——从 workflow transcript
        # 目录的 journal.jsonl 提取 schema-validated 结果 (result/value 双字段,
        # W6 §10.3), 免手工拼 --cand-XXX 参数 (mbedtls 审计手工步骤机械化)
        if from_journal:
            # v3.2.3 (Lua 审计): 区分「目录不存在/传了文件」与「有 journal
            # 但无 schema 结果」——旧报错把两种形态混为一谈, 误导定位
            if not os.path.isdir(from_journal):
                print(f"Error: --from-journal 应为 workflow transcript 目录 "
                      f"(内含 journal.jsonl), 不是文件/不存在路径: {from_journal}",
                      file=sys.stderr)
                sys.exit(1)
            extracted = _extract_journal_verdicts(from_journal)
            if not extracted:
                # SWR-V3.4.4-004: journal 为 refutation 结果时指引正确入口
                # (jsrsasign R3.5 收集时对反证 journal 误跑 collect 实测绕路)
                hint = _refutation_journal_hint(from_journal)
                print(f"Error: 目录存在但 journal.jsonl 无 schema-validated 结果: "
                      f"{from_journal} (检查 journal 行 type=result 且含 id+verdict)"
                      f"{hint}",
                      file=sys.stderr)
                sys.exit(1)
            # SWR-V3.3.2-010: --expect 全集校验——journal 提取结果必须覆盖
            # 派发全集 (防子集误匹配/部分落盘, 七项目批次 journal 张冠李戴教训)
            tw = _tooling_version_warning(project_root)
            if tw:
                print(f"Warning (SWR-V3.4.4-008): {tw}", file=sys.stderr)
            if expect_ids:
                missing = [e for e in expect_ids if e not in extracted]
                if missing:
                    print(f"Error: --expect 全集校验失败: journal 缺失 {missing} "
                          f"(提取到 {sorted(extracted)}), 不落盘",
                          file=sys.stderr)
                    sys.exit(1)
            verdicts.update(extracted)
        if not verdicts:
            print("Error: --cand-XXX JSON arguments or --from-journal required for collect",
                  file=sys.stderr)
            sys.exit(1)
        stage_collect(project_root, batch_id or 0, verdicts)
    elif stage == "assert":
        stage_assert(project_root)
    elif stage == "grade-recheck":
        sys.exit(stage_grade_recheck(project_root))
    elif stage == "coverage-ledger":
        sys.exit(stage_coverage_ledger(project_root, write="--write" in args))
    elif stage == "r35-collect":
        if not from_journal:
            print("Error: r35-collect requires --from-journal <transcript_dir>",
                  file=sys.stderr)
            sys.exit(1)
        sys.exit(stage_r35_collect(project_root, from_journal))
    elif stage == "r35n-collect":
        if not from_journal:
            print("Error: r35n-collect requires --from-journal <transcript_dir>",
                  file=sys.stderr)
            sys.exit(1)
        sys.exit(stage_r35n_collect(project_root, from_journal,
                                    expect_ids=expect_ids))
    elif stage == "status":
        stage_status(project_root)
    else:
        print(f"Error: unknown stage '{stage}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
