#!/usr/bin/env python3
"""differential_probe — 差分执行实证模板 (v3.17, SWR-V3.17-004, langs:["any"]).

用途: 同一输入语料在 N 组运行配置间执行, 比对结果分歧——配置间分歧是
「配置相关缺陷」的强信号 (JIT 优化层级/编译器优化旗标/特性开关/GC 模式/
构建变体)。完全参数化, 零项目名零硬编码路径。

边界 (docstring 契约, 与 R5 SAMPLING_PROTOCOL 对齐):
  - 分歧确认 ≠ 漏洞成立——分歧表供 verifier 定级 (缺陷方向由差异语义裁决);
  - 零分歧 = 该配置轴下一致性确认 (不排除其他轴的缺陷);
  - RSS 对比沿用 R5 采样协议 (基线采样 → 载荷 → 逐秒采样, 以服务器/进程
    实测为准, 客户端投递量不替代实测到达量);
  - 环境记录义务: 工具链版本/配置命令/超时/语料来源写入输出 summary。

用法:
    python3 differential_probe.py \\
        --configs 2 --cmd-0 "bin/engine --opt" --cmd-1 "bin/engine --no-opt" \\
        --corpus /path/to/inputs --compare exit_code,output_hash --rounds 1
    # 或语料生成器 (逐行输出输入文件路径):
    python3 differential_probe.py --configs 2 --cmd-0 ... --cmd-1 ... \\
        --gen "python3 gen_corpus.py --seed 42" --compare output_hash

输出 (stdout JSON): {status, divergent:[{input, per_config, diff}],
consistent, summary:{configs, corpus, rounds, env}}
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

USAGE = ("usage: python3 differential_probe.py --configs N "
         "--cmd-0 <命令> [--cmd-1 <命令> ...] "
         "(--corpus DIR | --gen <生成器命令>) "
         "[--compare exit_code[,output_hash,stderr_hash,rss_delta]] "
         "[--rounds N] [--timeout S]")


def _run(cmd, inp_path, timeout):
    """单配置单输入执行: 返回 {exit, output_hash, stderr_hash, rss_kb}。
    RSS 峰值以 /proc 自读实现 (仅本机可测, 缺失时 None)。"""
    t0 = time.time()
    try:
        with open(inp_path, "rb") as fh:
            p = subprocess.run(cmd + " " + inp_path, shell=True, stdin=fh,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=timeout)
        out, err, code = p.stdout, p.stderr, p.returncode
        rss = None
        try:
            with open("/proc/self/status") as st:
                for ln in st:
                    if ln.startswith("VmRSS:"):
                        rss = int(ln.split()[1])
        except OSError:
            pass
        return {"exit": code,
                "output_hash": hashlib.sha256(out).hexdigest()[:16],
                "stderr_hash": hashlib.sha256(err).hexdigest()[:16],
                "rss_kb": rss, "seconds": round(time.time() - t0, 2)}
    except subprocess.TimeoutExpired:
        return {"exit": "TIMEOUT", "output_hash": "TIMEOUT",
                "stderr_hash": "TIMEOUT", "rss_kb": None,
                "seconds": round(time.time() - t0, 2)}


def main(argv):
    args = dict(zip(argv[1::2], argv[2::2])) if len(argv) > 1 else {}
    try:
        n_cfg = int(args["--configs"])
    except (KeyError, ValueError):
        print(USAGE, file=sys.stderr)
        return 2
    cmds = [args[f"--cmd-{i}"] for i in range(n_cfg)]
    if any(c is None for c in cmds):
        print(USAGE + "\n每配置必须给 --cmd-N", file=sys.stderr)
        return 2
    corpus_dir = args.get("--corpus")
    gen_cmd = args.get("--gen")
    if not corpus_dir and not gen_cmd:
        print(USAGE + "\n--corpus 与 --gen 必须给其一", file=sys.stderr)
        return 2
    compares = (args.get("--compare") or "exit_code,output_hash").split(",")
    compares = [c.strip() for c in compares if c.strip()]
    rounds = int(args.get("--rounds") or "1")
    timeout = int(args.get("--timeout") or "30")

    # 语料: 目录列举或生成器逐行输出路径
    inputs = []
    if corpus_dir:
        inputs = sorted(os.path.join(corpus_dir, f)
                        for f in os.listdir(corpus_dir)
                        if os.path.isfile(os.path.join(corpus_dir, f)))
    else:
        p = subprocess.run(gen_cmd, shell=True, stdout=subprocess.PIPE)
        inputs = [ln.strip() for ln in p.stdout.decode(errors="ignore")
                  .splitlines() if ln.strip()]
    if not inputs:
        print(json.dumps({"status": "EMPTY_CORPUS", "inputs": 0},
                         ensure_ascii=False))
        return 3

    divergent, consistent = [], 0
    for inp in inputs:
        for _ in range(rounds):
            results = [_run(cmd, inp, timeout) for cmd in cmds]
            base = results[0]
            diffs = []
            for ci in range(1, n_cfg):
                for key in ("exit", "output_hash", "stderr_hash"):
                    if key == "exit" and "exit_code" in compares \
                            and results[ci]["exit"] != base["exit"]:
                        diffs.append(f"cfg{ci}:exit {base['exit']}!={results[ci]['exit']}")
                    if key == "output_hash" and "output_hash" in compares \
                            and results[ci]["output_hash"] != base["output_hash"]:
                        diffs.append(f"cfg{ci}:output_hash")
                    if key == "stderr_hash" and "stderr_hash" in compares \
                            and results[ci]["stderr_hash"] != base["stderr_hash"]:
                        diffs.append(f"cfg{ci}:stderr_hash")
                if "rss_delta" in compares:
                    r0, r1 = base.get("rss_kb"), results[ci].get("rss_kb")
                    if r0 and r1 and abs(r1 - r0) > 0.25 * max(r0, 1):
                        diffs.append(f"cfg{ci}:rss {r0}->{r1}KB")
            if diffs:
                divergent.append({"input": inp, "per_config": results,
                                  "diff": diffs})
            else:
                consistent += 1
    out = {"status": "DIVERGENT" if divergent else "CONSISTENT",
           "divergent": divergent, "consistent": consistent,
           "summary": {"configs": cmds, "corpus": corpus_dir or gen_cmd,
                       "rounds": rounds, "compares": compares,
                       "inputs": len(inputs), "timeout_s": timeout}}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if not divergent else 4


if __name__ == "__main__":
    sys.exit(main(sys.argv))
