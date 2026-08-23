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

# 扩展名 → 语言 (与 ast_scanner.ASTCoarseScanner.EXTENSION_MAP 保持一致的子集)
_EXT_LANG = {
    ".java": "java", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".py": "python", ".go": "go", ".rs": "rust",
    ".js": "javascript", ".ts": "javascript", ".jsx": "javascript", ".tsx": "javascript",
    ".cs": "csharp", ".php": "php", ".rb": "ruby", ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala", ".sh": "shell",
    ".pl": "perl", ".pm": "perl", ".ps1": "powershell",
}
_R15_IGNORE_DIRS = {"node_modules", ".git", ".audit_results", ".agents", ".codex",
                    ".venv", "__pycache__", "reachable-critical-audit", "build",
                    "target", "dist", "vendor", "third_party", "libs", "test",
                    "tests", "tool", "tools", "script", "scripts", "mock",
                    "mocks", "unittest", "scratch", "demo"}

# 短语言别名 → 规范名 (SWR-V3.4.6-001: _project_dom_lang 与 lang_of 共用)
_LANG_ALIAS = {"py": "python", "pl": "perl", "ts": "javascript", "js": "javascript",
               "rb": "ruby", "kt": "kotlin", "sh": "shell", "ps1": "powershell",
               "cs": "csharp", "rs": "rust"}


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
    old_fi = {fi.get("title"): fi for fi in (old.get("findings") or [])}
    for fi in (new.get("findings") or []):
        ofi = old_fi.get(fi.get("title"))
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
        # empirical_result: 旧值带 CONFIRMED/REFUTED 主代理标记 → 强制保留
        # (前缀标记即主代理复验信号, 原始输入不可能携带)
        oer = ofi.get("empirical_result") or ""
        ner = fi.get("empirical_result") or ""
        if oer and (oer.upper().startswith(("CONFIRMED", "REFUTED"))
                    or (not ner)):
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


def stage_r4_assert(project_root):
    """SWR-V3-055: H1-H7 全部 VERIFIED 断言。"""
    queue = load_queue(project_root)
    have = {_norm_hypothesis_id(f.get("hypothesis_id"))
            for f in queue.get("r4_findings", [])
            if f.get("status") == "VERIFIED"}
    missing = [f"H-{i}" for i in range(1, 8) if f"H-{i}" not in have]
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


def stage_coverage_ledger(project_root, write=False):
    """SWR-V3.4-001/002/003: 覆盖账本——CWE 族 x 语言审计覆盖追踪 (范围守护)。
    --write: 从 verify_queue 聚合候选级 cwe x lang (+ R4 findings 按项目主导语言
    近似计入), 项目级幂等 (sources 去重), merge 累加写账本。
    无参: 打印缺口格 (0 覆盖 + 单项目低深度) 与全矩阵计数表。"""
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    ledger_path = os.path.join(_parent, "resources", "issue_coverage_matrix.json")
    if not os.path.exists(ledger_path):
        print("Error: resources/issue_coverage_matrix.json 缺失", file=sys.stderr)
        return 1
    ledger = json.load(open(ledger_path))
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

    if project_root in (ledger.get("sources") or []):
        print(json.dumps({"status": "LEDGER_IDEMPOTENT_SKIP",
                          "project": project_root}, ensure_ascii=False))
        return 0
    queue = load_queue(project_root)
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
    rows = {r["family"]: (r.get("langs") or {}) for r in ledger.get("rows", [])}
    for (fam, lg), n in counts.items():
        if fam not in rows:
            rows[fam] = {}
        rows[fam][lg] = rows[fam].get(lg, 0) + n
    ledger["rows"] = [{"family": f, "langs": ls} for f, ls in sorted(rows.items())]
    ledger.setdefault("sources", []).append(project_root)
    ledger["updated_at"] = "2026-08-19"
    json.dump(ledger, open(ledger_path, "w"), ensure_ascii=False, indent=2)
    print(json.dumps({"status": "LEDGER_WRITTEN", "project": project_root,
                      "new_counts": {f"{f}x{l}": n for (f, l), n in
                                     sorted(counts.items())}},
                     ensure_ascii=False, indent=2))
    return 0


def stage_report(project_root):
    """SWR-V3-055: 基础量化报告 (过程问责指标)。"""
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
    snap_path = os.path.join(project_root, ".audit_results", "scope_snapshot.json")
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
        except (ImportError, ValueError):
            pass
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

### 步骤 1: 逆向调用链回溯（最小深度 3 层）
1. 读取 {ctx['file']} L{ctx['line']} 周围代码，确认 sink 点
2. 使用 grep 反向查找直接调用者（Caller_L1），记录调用处 file:line:function
3. 追踪 Caller_L1 的每个参数来源，找到 Caller_L2
4. 重复直到追溯到外部输入源（请求参数/文件/Binder IPC/蓝牙 HCI 事件等）
5. **质量门禁**: call_chain 必须 >= 3 层（Sink ← L1 ← L2），不足则继续向上搜索

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

### 步骤 4: 阻断检测
- 强类型转换、掩码（`& 0xFF`）、参数化绑定（`?` 占位符）、边界检查（`offset+len <= total`）
- 阻断必须覆盖所有攻击者可控制维度——多维度中只要有一维无阻断，仍为 REACHABLE

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
   - 错误分支方向：`if err == nil` 块内处理错误分支 = 写反死代码；
     缓存未命中返回什么（空实体+nil error 会短路 DB 回源）
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
    elif stage == "bump-attempt":
        stage_bump_attempt(project_root, findings_file or "")
    elif stage == "workflow-script":
        sys.exit(stage_workflow_script(project_root, mode=mode, batch_size=batch_size or 4))
    elif stage == "report":
        stage_report(project_root)
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
