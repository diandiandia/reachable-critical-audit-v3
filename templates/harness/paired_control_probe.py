#!/usr/bin/env python3
"""通用双测对照探针 (v3.30, SWR-V3.30-001) — 资源类声称的配对测量骨架。

形态: 对照组命令 vs 攻击组命令——同入口/同旗标, 只差被试点; 各跑至完成
或超时, 期间循环采样目标进程的 VmHWM (单调峰值, 不惧短生命周期) 与 VmRSS,
输出差分与判定。argv 驱动, 语言无关, 零项目语义。

采样时序纪律 (内嵌, 源自短生命周期进程峰值漏采样与惰性页伪影的实测教训):
- VmHWM 是单调峰值, 进程存续期轮询取最大值即可靠;
- "RSS 平 = 无分配"不可信: mmap/惰性提交不触写不占 RSS——触写义务在
  命令脚本侧 (攻击/对照脚本必须触写分配页), 本探针只保证峰值采样可靠。

用法:
    python3 paired_control_probe.py <control-cmd> <attack-cmd>
        [--timeout S] [--interval S] [--threshold R]
示例:
    python3 paired_control_probe.py \
        "qjs --memory-limit 16m --std ctrl.mjs" \
        "qjs --memory-limit 16m --std attack.mjs" --threshold 2.0
判定: attack_peak >= control_peak * threshold → PAIRED_CONFIRMED (对照放大成立);
否则 NO_SIGNIFICANT_DIFF; 对照组退出码非 0 → CONTROL_FAILED (对照失效,
攻击组读数不可比——先修对照再跑)。
"""
import json
import os
import subprocess
import sys
import time


def _parse_args(argv):
    timeout = 60
    interval = 0.2
    threshold = 2.0
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--timeout" and i + 1 < len(argv):
            timeout = float(argv[i + 1]); i += 2
        elif a == "--interval" and i + 1 < len(argv):
            interval = float(argv[i + 1]); i += 2
        elif a == "--threshold" and i + 1 < len(argv):
            threshold = float(argv[i + 1]); i += 2
        else:
            rest.append(a); i += 1
    if len(rest) < 2:
        print("usage: paired_control_probe.py <control-cmd> <attack-cmd> "
              "[--timeout S] [--interval S] [--threshold R]", file=sys.stderr)
        return None
    return {"control": rest[0], "attack": rest[1],
            "timeout": timeout, "interval": interval, "threshold": threshold}


def _descendants(root_pid):
    """沿 /proc 进程树取 root_pid 的全部后代 pid (shell=True 时工作负载
    在子进程, 只读 shell 自身会漏采样)。"""
    ppid_map = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                content = f.read()
            rest = content.split(")")[1].split()
            ppid_map[int(d)] = int(rest[1])
        except (OSError, ValueError, IndexError):
            continue
    out, frontier = set(), {root_pid}
    while frontier:
        nxt = {p for p, pp in ppid_map.items() if pp in frontier and p not in out}
        out |= nxt
        frontier = nxt
    return out


def _sample_peak(cmd, timeout, interval):
    """运行 cmd 并循环采样进程树 (shell+后代) VmHWM/VmRSS 峰值。
    返回 {exit, peak_hwm_kb, peak_rss_kb}。"""
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    peak_hwm = 0
    peak_rss = 0
    deadline = time.time() + timeout
    while proc.poll() is None and time.time() < deadline:
        for pid in _descendants(proc.pid):
            try:
                with open(f"/proc/{pid}/status") as f:
                    for line in f:
                        if line.startswith("VmHWM:"):
                            peak_hwm = max(peak_hwm, int(line.split()[1]))
                        elif line.startswith("VmRSS:"):
                            peak_rss = max(peak_rss, int(line.split()[1]))
            except OSError:
                pass
        time.sleep(interval)
    if proc.poll() is None:
        proc.kill()
        proc.wait()
    return {"exit": proc.returncode, "peak_hwm_kb": peak_hwm,
            "peak_rss_kb": peak_rss}


def main(argv):
    args = _parse_args(argv)
    if not args:
        return 2
    ctrl = _sample_peak(args["control"], args["timeout"], args["interval"])
    result = {"control": ctrl,
              "threshold_ratio": args["threshold"],
              "verdict": None}
    if ctrl["exit"] != 0:
        result["verdict"] = "CONTROL_FAILED"
        result["note"] = ("对照组退出码非 0, 攻击组读数不可比——先修对照再跑")
    else:
        atk = _sample_peak(args["attack"], args["timeout"], args["interval"])
        result["attack"] = atk
        ratio = (atk["peak_hwm_kb"] / ctrl["peak_hwm_kb"]
                 if ctrl["peak_hwm_kb"] else float("inf"))
        result["ratio"] = round(ratio, 2)
        result["verdict"] = ("PAIRED_CONFIRMED" if ratio >= args["threshold"]
                             else "NO_SIGNIFICANT_DIFF")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
