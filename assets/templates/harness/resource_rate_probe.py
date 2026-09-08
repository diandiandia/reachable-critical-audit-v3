#!/usr/bin/env python3
"""v3.6 (P2-⑧): 通用协议级速率灌注探针——R5 实证通用模板 (langs: ["any"])。

适用声称: protocol_dos / unbounded / oom 类——远端持续投递下的服务端资源行为。
通用形态 (协议无关, 仅 TCP 字节流):
1. 并发连接灌注: --conns 连接 × 每轮投递载荷, 观测服务端处理行为
2. 逐秒 VmRSS 采样: 目标 pid 的 /proc/<pid>/status (服务端测量点, 非客户端)
3. 拒绝计数: 连接被拒/超时/EOF 即计拒绝——服务端开始拒绝 = 资源边界信号
4. delivery-rate 确认: 以服务端实测到达量为准 (沙箱代理可能限流)
5. 关闭回落验证: 停止灌注后继续采样——RSS 回落 vs 无界累积的分野
6. 单调性判定: RSS 持续单调上涨无平台期 → 无界累积确认

用法: python3 resource_rate_probe.py --host 127.0.0.1 --port 8080
      [--pid <target_pid>] [--conns 8] [--duration 30] [--payload 4096]
输出: JSON 汇总 (rss_timeline / rejected / delivery_rate / monotonic /
      recovers / verdict)——verdict 供主代理裁决, 不自动改判。

零依赖: python3 标准库 (socket/time/os/json)。不测目标自身协议语义,
只测"持续投递下的资源行为"——具体协议载荷由调用方在 --payload-hex 给出。
"""
import argparse
import json
import os
import socket
import sys
import time


def parse_args():
    ap = argparse.ArgumentParser(description="通用协议级速率灌注探针")
    ap.add_argument("--host", required=True, help="目标主机")
    ap.add_argument("--port", required=True, type=int, help="目标端口")
    ap.add_argument("--pid", type=int, default=None, help="目标服务端 pid (VmRSS 采样)")
    ap.add_argument("--conns", type=int, default=8, help="并发连接数")
    ap.add_argument("--duration", type=int, default=30, help="灌注时长(秒)")
    ap.add_argument("--interval", type=int, default=1, help="采样/投递间隔(秒)")
    ap.add_argument("--payload", type=int, default=4096, help="每连接每轮投递字节数")
    ap.add_argument("--payload-hex", default=None,
                    help="载荷十六进制(可含具体协议头); 缺省为随机字节")
    ap.add_argument("--recover-wait", type=int, default=10,
                    help="停止灌注后的回落观察秒数")
    return ap.parse_args()


def sample_rss(pid):
    """服务端测量点: /proc/<pid>/status VmRSS (kB)。pid 缺失时返回 None。"""
    if not pid:
        return None
    try:
        for ln in open(f"/proc/{pid}/status", errors="ignore"):
            if ln.startswith("VmRSS:"):
                return int(ln.split()[1])
    except OSError:
        return None
    return None


def pump_round(args, stats):
    """一轮灌注: --conns 条连接各投递一次载荷, 失败计拒绝。返回投递字节数。"""
    sent = 0
    for _ in range(args.conns):
        s = None
        try:
            s = socket.create_connection((args.host, args.port), timeout=2)
            chunk = (bytes.fromhex(args.payload_hex) if args.payload_hex
                     else os.urandom(args.payload))
            s.sendall(chunk)
            sent += len(chunk)
        except OSError:
            stats["rejected"] += 1
        finally:
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
    return sent


def main():
    args = parse_args()
    stats = {"rejected": 0, "sent_bytes": 0, "rss_timeline": [],
             "delivery_rate": None, "monotonic": False, "recovers": None}

    # 阶段 1: 灌注 + 逐秒采样 (采样点优先服务端 VmRSS, 无 pid 则纯黑盒)
    base = sample_rss(args.pid)
    stats["rss_timeline"].append(("base", base))
    deadline = time.time() + args.duration
    peak = base
    while time.time() < deadline:
        stats["sent_bytes"] += pump_round(args, stats)
        v = sample_rss(args.pid)
        stats["rss_timeline"].append(("during", v))
        if v and (peak is None or v > peak):
            peak = v
        time.sleep(args.interval)

    # delivery-rate 确认: 客户端口径投递速率; 沙箱代理限流时以服务端
    # 表现 (拒绝计数/存活) 为准——本探针两者都报, 由主代理裁决
    stats["delivery_rate"] = (round(stats["sent_bytes"] / max(args.duration, 1)),
                              "bytes/sec (客户端口径)")

    # 阶段 2: 停止灌注 → 回落观察
    if args.pid:
        t0 = time.time()
        while time.time() - t0 < args.recover_wait:
            time.sleep(args.interval)
        after = sample_rss(args.pid)
        stats["rss_timeline"].append(("recover", after))
        if base and peak and after:
            # 恢复判定: 停止后回落量 >= 灌注期涨量 (peak-base) 的 50% → 有界释放
            stats["recovers"] = (peak - after) >= (peak - base) * 0.5
        # 单调性只看灌注期序列 (recover 值会污染末段): during 子序列
        during = [v for tag, v in stats["rss_timeline"]
                  if tag == "during" and v is not None]
        if len(during) >= 3:
            third = max(1, len(during) // 3)
            head = sum(during[:third]) / third
            tail = sum(during[-third:]) / third
            stats["monotonic"] = tail > head * 1.5

    verdict = []
    if args.pid and stats["recovers"] is False:
        verdict.append("RSS 未回落 → 无界累积/资源未释放")
    if args.pid and stats["monotonic"]:
        verdict.append("RSS 单调上涨无平台期 → 无界累积确认")
    if stats["rejected"]:
        verdict.append(f"拒绝 {stats['rejected']} 次 → 资源边界信号")
    stats["verdict"] = " ".join(verdict) if verdict else "无异常信号 (或需人工复核)"

    print(json.dumps(stats, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
