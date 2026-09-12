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

## 6. sanitizer 构建变体与 dcheck 交互（v3.19, SWR-V3.19-005）
- **ASan 实证必须用 dcheck 关闭的变体**（is_asan + dcheck_always_on=false）：
  dcheck 开启时 DEBUG 层不变量（DCHECK/DEBUG-only 校验）会在畸形输入到达目标
  sink 之前前置拦截——ASan 精确定位被阻（快照 blob 注入被 DEBUG 层容器校验
  拦截的实录形态）
- 若环境只有 dcheck 开启的 sanitizer 变体：实证结论必须注明前置拦截点
  （哪个 DEBUG 检查拦的）与"输入未到达目标 sink"的事实——不得以 DEBUG 崩溃
  冒充目标机制实证，也不得以 DEBUG 拦截冒充防御存在（release 语义另证）
- 对照实验义务：同输入跑 release 变体 + sanitizer 变体 + 未补丁基线三组,
  因果性由差异建立（单组崩溃不足归因）

## setuid 辅助二进制部署拓扑（v3.40, SWR-V3.40-005）

setuid-root 辅助二进制（容器执行器/特权 helper 形态）的 real_target 实证
必须先复刻部署拓扑。五要素（逐项失败日志即修复映射，按失败顺序排）:

1. **配置链**: cfg 文件与全部祖先目录须 root 属主且非组/全局可写（启动
   自检拒绝）；cfg 路径常为编译期常量——先查构建变量（如 CMake 传入的
   CONF_DIR）再放 cfg，运行时环境变量覆盖通常无效
2. **二进制权限**: root 属主 + 属组等于 cfg 声明组 + 无 other 写/执行位
   + setuid 位（6750 形态）；检查链逐项报错文本对应逐项修复
3. **调用者身份**: setuid 下 nm_uid = 调用者**真实 uid**——须以专用服务
   账户运行（root 直跑会被 "Running as root is not allowed" 拒绝）；
   本地/日志目录属主 = 该服务账户
4. **数据目录族**: usercache 等父目录须预置（mkdir 无 -p 语义时父目录
   缺失即失败）；tmp/private_slash_tmp/private_var_slash_tmp 类目录须
   **运行用户**属主（chmod 由降权后的进程执行, 属主不符即 EPERM）
5. **工作目录**: 脚本复制目标（launch_container 类文件）落在 work_dir
   ——须容器用户可写目录（root-only 目录会在复制步失败）

实操注记: 该拓扑的收敛轮数通常远大于缺陷触发本身（10+ 轮失败日志驱动的
逐项修复是常态, 非异常）；注入类实证的目标是"euid=0 下注入命令执行"的
proof 文件（root 属主落盘即成立, 无需真实被调二进制存在——shell 先报
command not found 再执行注入命令的形态属设计内行为）。
