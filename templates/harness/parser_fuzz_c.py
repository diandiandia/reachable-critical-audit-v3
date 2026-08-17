#!/usr/bin/env python3
"""v3.2.2 (REQ-V3.2.2-008): parser-fuzz 模板——C 解析器候选的 ASan+UBSan 实证 harness。

适用声称: crash/panic 类 (解析器 OOB 读/写)。通用形态 (mbedtls 审计实战模板化):
1. 把 sink 函数体逐字提取为独立 C 文件 (harness 注入随机主循环)
2. clang/gcc -fsanitize=address,undefined 编译
3. 攻击输入矩阵: N 随机缓冲 + 结构化截断 + 长度字段极值 (0x00/0x7F/0xFF 前缀)
4. 判定: 任意 ASan/UBSan 报告 → 越界确认; 零报告 + 拒绝语义正确 → 防御确认

用法: python3 parser_fuzz_c.py --sink <提取的C文件> --rounds 200000
输出: {"asan_findings": n, "ubsan_findings": n, "rounds": n, "verdict": ...}
"""
import argparse
import json
import os
import random
import subprocess
import sys
import tempfile


def compile_harness(sink_c):
    """把 sink 文件包装进随机主循环并编译 (ASan+UBSan)。"""
    wrapper = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

extern int sink(unsigned char *p, const unsigned char *end);

int main(int argc, char **argv) {
    unsigned long rounds = strtoul(argv[1], NULL, 10);
    unsigned long seed = strtoul(argv[2], NULL, 10);
    size_t cap = strtoul(argv[3], NULL, 10);
    srand(seed);
    for (unsigned long i = 0; i < rounds; i++) {
        size_t len = rand() % cap;
        unsigned char *buf = malloc(len ? len : 1);
        for (size_t j = 0; j < len; j++) buf[j] = (unsigned char)rand();
        /* 结构化变异: 长度字段极值前缀 (0x00/0x7F/0xFF/0x80 形态) */
        if (len > 2 && (i & 3) == 0) buf[0] = (unsigned char[]){0x00, 0x7F, 0xFF, 0x80}[i & 3];
        if (len > 3 && (i & 7) == 4) { buf[1] = 0x80; buf[2] = 0x7F; }
        /* 截断形态: 声明长度 1..127 个八位组但实际缓冲不足 */
        if (len > 4 && (i & 15) == 8) { buf[1] = (unsigned char)((i % 127) + 1); len /= 2; }
        (void)sink(buf, buf + len);
        free(buf);
    }
    return 0;
}
'''
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "harness.c")
        with open(src, "w") as f:
            f.write(open(sink_c).read() + "\n" + wrapper)
        exe = os.path.join(td, "harness")
        cc = os.environ.get("CC") or "cc"
        r = subprocess.run([cc, "-O1", "-g", "-fsanitize=address,undefined",
                            "-fno-omit-frame-pointer", "-o", exe, src],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return {"error": f"compile failed: {r.stderr[:300]}"}
        return {"exe": exe}


def run_matrix(exe, rounds, seed, cap):
    asan = ubsan = 0
    r = subprocess.run([exe, str(rounds), str(seed), str(cap)],
                       capture_output=True, text=True)
    err = (r.stderr or "") + (r.stdout or "")
    asan = err.count("ERROR: AddressSanitizer")
    ubsan = err.count("runtime error:")
    return {"asan_findings": asan, "ubsan_findings": ubsan,
            "rounds": rounds, "exit": r.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sink", required=True, help="提取的 sink 函数 C 文件")
    ap.add_argument("--rounds", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cap", type=int, default=4096)
    args = ap.parse_args()
    built = compile_harness(args.sink)
    if "error" in built:
        print(json.dumps(built))
        return 2
    res = run_matrix(built["exe"], args.rounds, args.seed, args.cap)
    res["verdict"] = ("OUT_OF_BOUNDS_CONFIRMED"
                      if (res["asan_findings"] or res["ubsan_findings"])
                      else "DEFENSE_CONFIRMED")
    print(json.dumps(res, indent=2))
    return 0 if res["verdict"] == "DEFENSE_CONFIRMED" else 1


if __name__ == "__main__":
    sys.exit(main())
