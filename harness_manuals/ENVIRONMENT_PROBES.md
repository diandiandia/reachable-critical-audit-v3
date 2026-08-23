# 环境能力探针清单（SWR-V3.3.2-060）

> R5 实证前必检。用途：实证前确认"机制所需能力"在本环境真实可用——七项目批次教训：
> io_uring_setup 被容器 seccomp 阻断（liburing 可装、编译通过、实测 -1），CAND-008
> e2e 白跑一轮后才走 R5 可选路径；lsquic 子模块为空致 QUIC 无法构建。
> 探针失败不阻断审计，但必须显式记录 blocker 并触发 R5 可选路径裁决（降级 NEEDS_REVIEW）。

## 1. 机制所需 syscall 探针

| 机制 | 探针 | 失败含义 |
|---|---|---|
| io_uring | `gcc -o /tmp/t_uring -luring` + `io_uring_queue_init(8,&ring,0)` 返回值 | seccomp/内核阻断 → io_uring 后端 e2e 不可行 |
| 原始 socket | `socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)` | 需要 raw socket 的实证不可行 |
| prctl/seccomp 自身 | `prctl(PR_GET_SECCOMP)` | 容器 seccomp 策略面 |
| 大页/锁页 | `mlock`/`memlock` rlimit | 需要驻留内存测量的实证受扰动 |

通用 C 探针片段（io_uring 例）：
```c
#include <liburing.h>
#include <stdio.h>
int main(){ struct io_uring ring; int r = io_uring_queue_init(8, &ring, 0);
printf("queue_init=%d\n", r); if(!r) io_uring_queue_exit(&ring); return 0; }
```

## 2. 依赖存在性探针（构建类）

- 头文件/库：`ls /usr/include/<lib>.h` / `ldconfig -p | grep <lib>`——可 apt 安装 ≠ 可链接（liburing-dev 案例）
- 子模块物化：`git submodule status` + 目录非空检查（lsquic 空目录案例：目录存在 ≠ 源码在场）
- 语言工具链：cargo/rustc 常不在 PATH（$HOME/.cargo/bin），go/gcc 版本义务见各语言手册

## 3. 工具存在性及替代

| 缺失工具 | 替代 |
|---|---|
| `ss` | `/proc/net/tcp` inode 反查 pid（/proc/*/fd 扫描） |
| `/usr/bin/time -v` | python `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss` |
| `fuser`/`lsof` | /proc 扫描（同上） |
| `pkill -f <pattern>` | **禁止用**——pattern 会匹配自身命令行导致自杀；用 /proc 扫描 + os.kill |

## 4. Shell 陷阱

- zsh `echo ===`（等号展开）中止复合命令——分隔符用引号包裹或改用 printf
- zsh `echo =======` 同理；`echo ----` 安全
- 后台进程管理：`cmd &` + `wait $PID` 遇阻塞子进程会挂死整个复合命令——用 python subprocess 管理生命周期

## 5. 探测时机与记录

R5 步骤 0（harness 选择前）：按声称机制跑第 1 节探针；构建类实证跑第 2 节。
探针结果写入 EMPIRICAL_REPORT.md「环境探针」段：{probe, result, blocker?}。
blocker 存在 → R5 可选路径裁决（主代理降级 NEEDS_REVIEW + correction_record），
不实证不申报。
