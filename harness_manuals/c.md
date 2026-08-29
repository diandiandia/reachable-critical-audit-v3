# C 实证工具链手册 (v3.1)

> 适用战役：C 首审（10 候选 2 REACHABLE、2/2 票证伪 2 条，R3.5 拦截 50% 含 2 降级）。
> 事实来源：W6_MORE_LANGS_FINDINGS.md §22（主）；SKILL_LESSONS_C.md（C 实测）。

## 1. 工具链探测
- gcc + make 可用且实机构建成功：./configure && make 全流程通过（W6 §22.5；SKILL_LESSONS_C §0）
- 探测命令：`gcc --version && make --version && which cc`
- gcc -E 预处理是死代码/宏分支判定的实证武器：`gcc -E -P -I src -I src/ls-hpack lshpack.c` 验证 `#if LS_HPACK_USE_LARGE_TABLES` 等宏分支是否编译进产物，把"死代码"判定从猜测升级为实证（SKILL_LESSONS_C §1.5）
- 并发模式：10~20 并发 + 簇级任务书（每 agent 一个 file×CWE 簇）为 Mode A' 官方形态，157 个 collect 批次无丢失（SKILL_LESSONS_C §1.4.7）
- R0.5 差异考古工具纪律：输出必须传 `-o` 落盘（不传不落盘）；grep 词表分级（security 关键词 vs 通用 fix 词）避免 1688 commit 全被标安全相关（SKILL_LESSONS_C §1.4.5）

## 2. 版本记录义务
- 精确版本 + commit 成对记录：C 项目先例（SKILL_LESSONS_C §0）
- 上游负向验证需版本成对记录：1.4.85 vs upstream 1.4.86 逐字节比对（SKILL_LESSONS_C §1.5）
- 构建配置影响功能可达性：configure 参数/module 顺序改变结论（SSI 被 mod_staticfile 抢先 handler_module），构建产物与结论必须绑定配置记录（W6 §22.5）
- 复审计项目先读旧审计终稿（报告/report json）：v2 终稿已把 ssi.exec 降级 Low hardening，不能凭记忆或草稿级 artifact（_r4_merged.json 与终稿不一致时以终稿为准）（W6 §22.2）

## 3. 常见陷阱清单
- 连接洪泛类实证的黄金证据（SWR-V3.4.3-071, P2 cpp-httplib R5 实测）：
  ① 接受率——N/N 裸连接全部被 accept+enqueue（无连接数/队列深度检查）；
  ② fd 计数——flood 期间 `len(os.listdir('/proc/<pid>/fd'))` ≈ 连接数（队列深度 1:1）；
  ③ 合法请求饿死——flood 期间正常 GET 超时（worker 全被钉住），排空只在超时后发生。
  三项同现才是"无界队列"的完整证明，单项（仅接受率高）不构成 DoS 证据。
  注意 pgrep -f 自匹配陷阱与 ss 缺失（见 go.md 同批追加）
- R1 证据质量最差语言：process agent 4 处 paraphrased snippet（行号漂移 ±45 + 细节臆造如 "last_sigterm_info = *si" 非真实行内容）；network 首版产出 30 surfaces 超模板——snippet 必须逐字符复制、禁臆造细节、表面数超模板视为 agent 失控信号（W6 §22.1）
- "configure && make 成功 ≠ 功能可测"：SSI 实测被 mod_staticfile 抢先 handler_module 阻断——harness 失败先怀疑"该功能本就是非默认路径"而非环境问题（W6 §22.5）
- "默认开启"三层语义：ssi_exec=1 是代码层默认值；mod_ssi 加载与 ssi.extension 配置是模块层默认（关）；写入原语是部署层前提（需另一漏洞）——verifier 只看到第一层；三层全开才算默认可达（W6 §22.3）
- env 注入三原语枚举：名消毒（HTTP_[A-Z0-9_]+ 使 PATH/LD_* 不可达）+ HTTP_PROXY 抑制 + CR/LF/NUL 解析层 400 + envp NUL 截断无夹带——"注入"类假设必须逐一枚举注入原语（换行/空字节/名污染）并验证各自阻断（W6 §22.4）
- L0 规则 89% 伪影：CWE-476 `(pointer_expression)` 命中每个指针解引用（7,062 条）、CWE-416 命中每个 free()（373 条）、CWE-908 正则命中注释行（1,551+ 条）——10,097 原始命中 ~9,000 伪影（SKILL_LESSONS_C §1.1）
- 路径过滤漏洞：`src/t/`（目录名 "t" 不匹配 test 词元）、`src/lemon.c`（构建时代码生成器 ~332 候选）、`packdist.sh`（14 候选）、`NEWS`（文档，2 候选）均漏网——路径过滤应 glob 化 + 构建系统感知（区分运行时目标 vs 代码生成器）（SKILL_LESSONS_C §1.2）
- R1.5 wrapper_detection 平台错配：部分 wrapper 形态属特定平台生态，C 服务端项目真实 wrapper 全靠提取器 agent 兜底——wrapper 规则须按平台 profile（服务端/嵌入式/桌面）拆分（SKILL_LESSONS_C §1.3）
- 工具链坑：`--cand-` 解析器强制 CAND- 前缀（R05-* 候选无法 collect，需手工改 JSON）；ast_scanner 重跑整体覆写 verify_queue.json（应 merge 语义）；`| head` SIGPIPE 致 exit 1 误判失败（SKILL_LESSONS_C §1.4）
- assert 阶段 null blocking_point 报错："常规同步 free 无后续使用"没有单点阻断，69 个候选被断言拒绝——允许 "N/A" + evidence 解释的合法组合（SKILL_LESSONS_C §1.4.3）

## 4. 阳性模式（战役验证过的做法）
- gcc -E 预处理验证宏分支死代码（SKILL_LESSONS_C §1.5）
- 上游逐字节比对 diff 确认"无修复缺口"，对开源项目是低成本负向验证（SKILL_LESSONS_C §1.5）
- "注释掉的守卫"是 grep 可见的最强证据形态：h2 rwin 记账三处注释 + WINDOW_UPDATE 无条件回发 + SETTINGS 16MB-1，纯源事实即构成完整论证——verifier 应主动 grep 被注释的安全相关行（W6 §22.6）
- 真实 wrapper 生态识别（R1.5 提取器）：buffer_append_* 家族、gw_backend 协议编码器、fdevent_fork_execve、ck_* 分配器、SQL 拼接（mod_vhostdb_mysql_query）——L0 零覆盖，全在 L1（SKILL_LESSONS_C §1.3）
- L1 提取器 prompt 注入项目背景：34 个 L1 候选全部依赖主代理在 prompt 补充 buffer/协议/spawn 生态——框架感知扩展的质量由主代理领域知识决定（SKILL_LESSONS_C §1.5）
- 三层 gate 拆分裁决：代码默认值/模块默认加载/部署前提三层全开才算默认可达（W6 §22.3）
- R0.5 变体复核模式：对 HEAD 审计的"疑似未修复"判定改为"修复变体复核"（兄弟路径是否残留同类缺陷），7 个高价值近期修复全部确认完整（SKILL_LESSONS_C §1.4.5）
- R3 质量门禁的调用链质量是可信度支柱：867 个 UNREACHABLE 平均深度 4.18（最深 7），"分配与长度同源/引用计数配对/关闭置 NULL"等防御定位精确到行（SKILL_LESSONS_C §2）

## 5. 网络依赖
- 本批实证零网络依赖：configure && make 全本地完成（W6 §22.5）
- 上游比对需 github.com（可达，W6 §21.4）
- 依赖库源码同仓库内（mod_staticfile 等）

## 6. 实证范围建议
- E2E 级可行（configure && make 实机构建，W6 §22.5）——但必须核对模块接管顺序后再测目标功能（W6 §22.5）
- 机制级：gcc -E 死代码验证 + 注释守卫 grep（SKILL_LESSONS_C §1.5；W6 §22.6）
- 源事实级可定谳："默认开启"三层语义与注入原语枚举均为纯源论证（W6 §22.3/22.4）
- 工具链级：簇级批量 10-20 并发，每 agent 候选数 ≤6，输出先过 json.load 自检（SKILL_LESSONS_C §1.4.7/1.4.6）

## 7. 有状态 sink 的最小 stub 复刻法（v3.10, SWR-V3.10-012）
parser_fuzz 的随机主循环适配无状态解析器；sink 依赖解析上下文/内核结构体时
（长度字段无符号下溢、边界指针回退、分配布局比例参与越界判定），按以下纪律
手工构造最小 stub 后接入模板编译：
- **无符号下溢语义保留**：长度/指针字段用目标同宽类型（u16/u32/size_t），
  自减/pull 步进逐字复刻，不得改有符号或加断言（断言会掩盖目标缺陷）——
  攻击链的核心机制往往就是下溢本身
- **边界指针语义**：head/data/tail 三指针以独立字段复刻，pull/trim 的相对
  移动与真实语义一致；分配起点与指针偏移的布局比例按真实结构模拟（乱改
  比例会使越界不可观测）
- **分配布局模拟**：用 malloc 模拟目标分配单元，数据起点放在真实 headroom/
  头结构偏移处——越界判定依赖布局比例
- **逐字提取纪律**：提取函数体保持逐字（含来源行注释），stub 单独标注
  "stub（语义复刻）"与目标语义行号来源；混写/改写破坏证据链
- **消费侧复刻**：sink 下游按长度拷贝的循环同样复刻——长度传播到消费点
  才是完整攻击链的实证（仅 sink 级越界读数 vs 消费级大范围越界读，严重度
  证据完全不同）
- 实测形态（来源：2026-08 内核级目标两次 ASAN 实证，见 lessons/SKILL_LESSONS_common.md
  过程观察）：确定性输入求解（穷举长度/校验字段使门禁通过）+ 1M 轮随机矩阵
  双模式，ASAN 报 redzone 越界即 CONFIRMED

## 8. 资源防护样板（v3.10.2, SWR-V3.10.2-019）

实证 harness 可能触发 GB/TB 级分配——无防护环境复跑极值预设会 OOM-kill 整机。
运行前二选一：

```bash
# 方式 A: shell 级限额 (最简)
ulimit -v 8388608    # 8GB 虚拟内存上限; 分配超限时 malloc 失败而非杀主机
```

```c
/* 方式 B: harness 内显式防护 (可复现性更强, 推荐写入 harness 头部) */
#include <sys/resource.h>
static void limit_vmem_kb(long kb) {
    struct rlimit rl = { (rlim_t)kb * 1024, (rlim_t)kb * 1024 };
    if (setrlimit(RLIMIT_AS, &rl) != 0) { perror("setrlimit"); exit(2); }
}
/* main 开头: limit_vmem_kb(8 * 1024 * 1024);  // 8GB */
```

纪律：
- 极值预设（0xFFFFFFFF 类长度/计数）仅在限额环境运行；甜点区间（GB 级成功
  分配）与极值（bad_alloc）分两次运行分别取证。
- 对照复现（RSS 测量）用 `-O1` 无 sanitizer，与 ASan/UBSan 运行分离
  （ASan 约 2x 内存开销会干扰 RSS 读数；报告注明工具链差异）。
- 实证产物全部落盘 `.audit_results/empirical/<name>/`（R0 目录守卫）——
  含源码、输入、EMPRICAL_REPORT（工具链版本/输入/输出/判定）。
