#!/usr/bin/env python3
"""M5 harness_runner — R5 实证抽验：触发判定、模板注册、时序采样、结果写回。

满足: SWR-V3-040 (needs_harness), SWR-V3-041 (4 内置模板),
      SWR-V3-042/043 (时序采样 + 投递速率确认协议),
      SWR-V3-044 (apply_result: confirmed/refuted 两路径),
      SWR-V3-045 (环境记录).
用法:
    python3 harness_runner.py templates                 # 列出注册模板
    python3 harness_runner.py check <candidate.json>    # 触发判定
"""
import json
import os
import platform
import re
import subprocess
import sys
import time

EMPIRICAL_CLAIMS = ("crash", "panic", "oom", "unbounded", "xss", "protocol_dos")

TEMPLATES = {
    "ws_frame_alloc": {
        "langs": ["kotlin", "rust"],
        "attack": "发送仅含帧头的 ws 帧（声明大长度、零 payload），观测服务端 RSS 跳变",
        "metrics": ["VmRSS_before", "VmRSS_after", "server_alive"],
        "judgement": "RSS 增量 ≈ 声明长度 → 预分配确认",
        "script": "templates/harness/ws_frame_alloc.py",
    },
    "ws_frame_accum": {
        "langs": ["rust", "kotlin", "scala"],
        "attack": "声明大帧长 + 慢速流式喂数据，逐秒采样 RSS",
        "metrics": ["VmRSS_timeline", "delivery_rate", "server_alive"],
        "judgement": "RSS 随接收字节线性增长 → 累积确认",
        "script": "templates/harness/ws_frame_accum.py",
    },
    "xss_path_sim": {
        "langs": ["perl", "php", "python"],
        "attack": "复刻精确代码路径（解码/清洗/输出）验证载荷存活",
        "metrics": ["payload_survives", "rendered_output"],
        "judgement": "载荷完整存活于输出属性 → XSS 确认",
        "script": "templates/harness/xss_path_sim.pl",
    },
    "multipart_align": {
        "langs": ["python"],
        "attack": "构造对齐模式 multipart body + 解析器节奏插桩",
        "metrics": ["peakRSS_growth", "handler_received", "rhythm_trace"],
        "judgement": "累积发生且 handler 收到 0 字节 → 确认；对齐必然恢复 → 证伪",
        "script": "templates/harness/multipart_align.py",
    },
}

SAMPLING_PROTOCOL = (
    "1. 启动目标进程并记录基线 VmRSS/存活状态;\n"
    "2. 发送攻击载荷;\n"
    "3. 每秒读 /proc/<pid>/status VmRSS + kill -0 存活检查，持续 ≥30s 或直至进程退出;\n"
    "4. 投递速率确认: 先以慢速(如 64KB/s)采样，确认服务器实测到达量随发送增长"
    "（沙箱代理可能限流——以服务器实测到达量为准，不以客户端发送量为准）;\n"
    "5. 记录环境: 工具链版本/依赖/端口/限流备注，保证可复现。"
)


def needs_harness(candidate):
    """SWR-V3-040: claim ∈ EMPIRICAL_CLAIMS 且 grade < empirically_confirmed → 触发。"""
    claim = (candidate.get("claim_type") or "").lower()
    grade = candidate.get("evidence_grade")
    hit = any(k in claim for k in EMPIRICAL_CLAIMS)
    return hit and grade != "empirically_confirmed"


def list_templates():
    return TEMPLATES


def collect_env():
    """SWR-V3-045: 环境记录（工具链版本/依赖/端口）。"""
    env = {"platform": platform.platform(), "python": sys.version.split()[0]}
    for tool in ("swift", "java", "rustc", "perl", "node"):
        p = subprocess.run(["which", tool], capture_output=True, text=True)
        if p.returncode == 0:
            try:
                v = subprocess.run([tool, "--version"], capture_output=True, text=True,
                                   timeout=10).stdout.splitlines()[0][:80]
            except Exception:
                v = "unknown"
            env[tool] = v
    return env


def sample_process(pid, seconds=30, interval=1.0):
    """SWR-V3-042: /proc/<pid>/status VmRSS 时序采样 + 存活检查。"""
    timeline = []
    alive = True
    for _ in range(int(seconds / interval)):
        rss, is_alive = None, False
        try:
            with open(f"/proc/{pid}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        rss = int(line.split()[1])
                        break
        except OSError:
            pass
        try:
            os.kill(pid, 0)
            is_alive = True
        except OSError:
            is_alive = False
            alive = False
        timeline.append({"t": round(time.time(), 2), "rss_kb": rss, "alive": is_alive})
        if not is_alive:
            break
        time.sleep(interval)
    return {"timeline": timeline, "alive": alive}


def parse_empirical_result(raw):
    """从 harness 脚本输出解析结构化结果（脚本约定输出 JSON 段）。"""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"status": "parse_error", "raw": raw[:500]}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"status": "parse_error", "raw": raw[:500]}


def apply_result(candidate, result):
    """SWR-V3-044: confirmed → empirically_confirmed; refuted → correction_record + 降级。"""
    if result.get("status") == "confirmed":
        candidate["evidence_grade"] = "empirically_confirmed"
        candidate["empirical"] = result
    elif result.get("status") == "refuted":
        candidate["empirical"] = result
        candidate.setdefault("correction_record", []).append({
            "target": candidate.get("id"),
            "reason": result.get("reason", "R5 实证证伪"),
            "demote_to": result.get("demote_to", "UNREACHABLE"),
        })
        candidate["verdict"] = result.get("demote_to", "UNREACHABLE")
        candidate["evidence_grade"] = "static_only"
    else:
        candidate["empirical"] = result   # parse_error/unknown: 保留记录不升降级
    return candidate




# ---------------- v3.1 增量 (SWR-V3.1-060~064) ----------------

EMPIRICAL_SCOPES = ("mechanism", "function_body", "full_chain", "e2e")
MANUAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness_manuals")
_SENTINEL_MARKERS = ("max_value", "-1", "哨兵", "sentinel", "usize::max", "long.max",
                     "int64.max", "uint32.max")


def load_manual(lang, max_items=8):
    """SWR-V3.1-060: 装载 harness_manuals/<lang>.md 要点（陷阱清单 + 阳性模式
    各前 max_items/2 条），注入实证任务书。"""
    path = os.path.join(MANUAL_DIR, f"{lang}.md")
    if not os.path.exists(path):
        return ""
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    traps, positives, section = [], [], None
    for ln in lines:
        if ln.startswith("## 3. 常见陷阱清单"):
            section = "trap"
            continue
        if ln.startswith("## 4. 阳性模式"):
            section = "pos"
            continue
        if ln.startswith("## ") and section:
            section = None
        if section == "trap" and ln.startswith("- ") and len(traps) < max_items // 2:
            traps.append(ln[2:])
        elif section == "pos" and ln.startswith("- ") and len(positives) < max_items // 2:
            positives.append(ln[2:])
    if not traps and not positives:
        return ""
    out = ["## 语言实证手册要点 (harness_manuals/%s.md)" % lang]
    if traps:
        out.append("常见陷阱:")
        out.extend(f"- {t}" for t in traps)
    if positives:
        out.append("阳性模式:")
        out.extend(f"- {p}" for p in positives)
    return "\n".join(out)


def check_scope(candidate):
    """SWR-V3.1-061: 实证范围分级强制。
    - empirical 存在时 scope 必填且 ∈ EMPIRICAL_SCOPES, scope_note 必填
    - scope=mechanism/function_body 且 grade=empirically_confirmed → 违规
      (机制级只能支撑 edge_proven, W6 §17.7/§15.6)
    返回违规列表。"""
    violations = []
    emp = candidate.get("empirical")
    if not isinstance(emp, dict):
        return violations
    scope = emp.get("scope")
    if scope not in EMPIRICAL_SCOPES:
        violations.append(f"scope 缺失/非法: {scope} (需 {EMPIRICAL_SCOPES})")
        return violations
    if not emp.get("scope_note"):
        violations.append("scope_note 缺失 (SWR-V3.1-061)")
    if scope in ("mechanism", "function_body") and \
       candidate.get("evidence_grade") == "empirically_confirmed":
        violations.append(
            f"scope={scope} 不得升 empirically_confirmed (W6 §17.7 范围纪律)")
    return violations


def env_trap_checklist(lang):
    """SWR-V3.1-062: 环境陷阱自检清单（harness 启动前必跑, W6 §16.5/§16.6/§16.3/§23.3）。"""
    common = [
        "stale 进程清理: 目标端口 pkill -9 + 诊断路由(/diag)自检配置态后才测量",
        "采样线程必须 daemon + try/finally (异常时不得卡死解释器 shutdown)",
        "env 传播验证: 先查进程 comm 确认 PID 身份再查 environ",
        "PATH 检查: 工具链二进制可能不在后台 shell PATH",
        "测量点放服务端 (CPU tick/VmHWM), 不要用客户端完成信号",
    ]
    per_lang = {
        "swift": ["SIGTERM/SIGINT 会被 runtime 转 SIGTRAP; LD_LIBRARY_PATH 必须含 swift runtime 目录"],
        "rust": ["cargo test 用全路径或显式 PATH; transitive dev-dep 不可见 → 字节内嵌; 不要盲从编译器 help 文本"],
        "java": ["JDK 版本影响标准库语义 (Inflater gzip 行为 JDK22+ 变更); 记录 java -version"],
        "go": ["proxy.golang.org 不可达环境 → 源事实级 + blocker 记录"],
        "ruby": ["ruby -Ilib + Rack::MockRequest 零依赖可跑; 记录 ruby -v"],
        "c": ["./configure && make 可行; harness 失败先怀疑模块接管顺序而非环境"],
        "python": ["venv + sys.path 导入源码即可; 无 pip 用 skill venv"],
    }
    return common + per_lang.get(lang, [])


def mixed_build_hint(candidate):
    """SWR-V3.2-061: 混合项目多组件构建提示——按候选.lang 组装构建矩阵,
    引用 harness_manuals/mixed_build.md 总纲。"""
    langs = {candidate.get("lang")} if candidate.get("lang") else set()
    lp = str(candidate.get("lang_pair") or "")
    for side in lp.replace("->", " ").split():
        if side in ("c", "py", "rust", "js", "ts"):
            langs.add(side)
    if len(langs) < 2:
        return ""
    return (
        "## 混合项目实证提示 (harness_manuals/mixed_build.md)\n"
        "1. 组件级构建矩阵: 每组件 {lang, build_cmd, 产物, 测试入口} 先分别验证构建\n"
        "2. 宿主进程 + 动态库加载编排 (C .so + ctypes/cdylib 驱动)\n"
        "3. 边界两侧各放插桩, 交叉对表; 顺序: 单侧机制级 → 边界级 E2E\n"
        "4. 陷阱: ctypes argtypes 未声明截断/编码不一致/释放责任错配"
    )


def contrast_matrix_prompt(target):
    """SWR-V3.1-063: 对照矩阵实证模式（默认配置拒绝 + 弱化配置接受, W6 §24.4）。"""
    return (
        "## 对照矩阵实证（W6 §24.4 黄金证据形态）\n"
        "设计两组实验:\n"
        "  A. 默认配置: 发送 crafted 载荷 → 预期被拒绝 (记录拒绝机制)\n"
        "  B. 弱化配置: 同一载荷在 gate 弱化后 → 预期被接受 (记录接受路径)\n"
        "同一 payload 的接受/拒绝对照比单侧攻击演示强一个量级;\n"
        "两组结果与 gate 关联关系写入 empirical.contrast_matrix。"
    )


def source_fact_rule(candidate, blocker=None):
    """SWR-V3.1-064: 源事实级降级规则 (W6 §21.4/§17.7)。
    返回 (level, note): 网络阻断 → source_fact + blocker 记录;
    哨兵值/算术类主张接受 source_fact; 其他不得降级。"""
    text = " ".join(str(candidate.get(k) or "")
                    for k in ("summary", "claim_type", "evidence")).lower()
    is_sentinel = any(m in text for m in _SENTINEL_MARKERS) or \
        candidate.get("claim_type") in ("sentinel", "arithmetic")
    if blocker:
        return "source_fact", f"阻断记录: {blocker}"
    if is_sentinel:
        return "source_fact", ("哨兵值/算术类主张 (§17.7/§21.3 先例): "
                               "源事实级可接受, 无需运行时实证")
    return "empirical_required", "非哨兵/算术类且无阻断 → 实证义务不可豁免 (§13.9)"


def _main_additions(argv):
    if argv[1] == "manual":
        print(load_manual(argv[2] if len(argv) > 2 else "rust"))
        return 0
    if argv[1] == "check-scope":
        c = json.load(open(argv[2]))
        for v in check_scope(c):
            print(" -", v)
        return 1 if check_scope(c) else 0
    if argv[1] == "traps":
        print("\n".join(f"- {t}" for t in env_trap_checklist(argv[2] if len(argv) > 2 else "rust")))
        return 0
    return None


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "templates":
        for name, spec in TEMPLATES.items():
            print(f"{name}: {spec['attack'][:60]}...")
        print("\nSAMPLING_PROTOCOL:")
        print(SAMPLING_PROTOCOL)
        return 0
    r = _main_additions(argv)
    if r is not None:
        return r
    if cmd == "check":
        cand = json.load(open(argv[2]))
        print(json.dumps({"needs_harness": needs_harness(cand)}, ensure_ascii=False))
        return 0
    if cmd == "env":
        print(json.dumps(collect_env(), ensure_ascii=False, indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
