# SWR_V3_37: Caddy 验收复盘三修复

## SWR-V3.37-001: 任务书落盘路径绝对化 (D-1)

- **裁决**: workflow_export 三处 taskFile/taskFiles 落盘字段由相对路径改
  `os.path.join(project_root, ...)` 绝对形态。任务书文件本身落盘位置不变
  (`.audit_results/_tasks/`), 仅 payload 引用字段绝对化——Workflow agent 的
  cwd 不可假定为项目根。
- **义务三问**: ①触发条件——Mode W 派发的全部任务书引用 (无条件, 数据正确性);
  ②消费者——Workflow 脚本 prompt 内的 Read 指令 (verify/refutation/resurrect
  三形态); ③裁掉丢什么——Caddy 实录: 主代理手工补绝对路径才避免全线伪裁决。
- **测试守卫**: test_v337.py T-1。

## SWR-V3.37-002: CK-SLICE-CAPACITY 清单条目 (D-2)

- **裁决**: 新清单条目 (family=memory-safety, 提示级): 静态切片越界声称的验证
  必须核对输入缓冲容量语义——2-index 切片 `s[:N]` 边界条件为 `N ≤ cap(s)`;
  对 ReadAll/ReadFile/网络缓冲类输入, cap ≥ 初始缓冲常量, `[:N]` 恒不越界,
  "无长度守卫即 panic" 声称不成立。判定点: 声称 panic 前先回答"该输入切片的
  cap 是多少、由谁分配"。
- **义务三问**: ①触发条件——候选声称切片越界 panic/crash 类后果时;
  ②消费者——verifier 任务书清单绑定 (family=memory-safety);
  ③裁掉丢什么——CAND-011 整候选误报实录 (cap-vs-len 语言语义前提错误)。
- **测试守卫**: test_v337.py T-2。

## SWR-V3.37-003: CK-MAGNITUDE-OWNERSHIP 清单条目 (D-3)

- **裁决**: 新清单条目 (family=empirical, 提示级): 资源类声称 (oom/unbounded/
  高占用) 的量级驱动权必须归属攻击者可控输入维度。单请求累积上界由部署内容
  尺寸决定、聚合上界由平台连接/流上限决定的形态, 不得报 remote 级 oom——
  按加固缺口口径申报 (部署前提显式标注), 或降级 NEEDS_REVIEW。
- **义务三问**: ①触发条件——claim_type ∈ {oom,unbounded} 且 attacker_tier=
  remote 的判定与证伪; ②消费者——verifier/证伪者任务书清单绑定
  (family=empirical); ③裁掉丢什么——CAND-002 量级前提幻觉 (证伪 1/2 才拦截,
  主代理裁决降级) 实录。
- **测试守卫**: test_v337.py T-3。

## 兼容性不变式

- 任务书文件落盘路径不变, 仅引用字段绝对化 (旧 payload 的相对路径被脚本
  Read 时由 agent 失败——修复后新导出全部绝对; 历史 payload 不受影响);
- 新清单条目为提示级, 无新义务面/无新门禁 (义务三问已过);
- 旧队列复跑零新增告警 (验收判据)。
