# SOFTWARE_DESIGN_V3_37: 函数级设计

## workflow_export (P1)

三处落盘引用字段绝对化 (任务书文件落盘位置不变):

```
:599  c["taskFile"] = os.path.join(_tasks_dir, f"resurrect_{c['id']}.md")
:811  c["taskFile"] = os.path.join(_tasks_dir, f"verify_{c['id']}.md")
:854  tfs.append(os.path.join(_tasks_dir, f"refute_{c['id']}_{i}.md"))
```

(原为 `f".audit_results/_tasks/..."` 相对形态; `_tasks_dir` 已是
`project_root/.audit_results/_tasks` 绝对形态, join 即得。)

## checklist_library (P3)

两条新条目 (去项目化, 五字段同既有条目形态):

- **CK-SLICE-CAPACITY** family=memory-safety, applies_to=["verifier","refuter"]:
  steps: (1) 声称 `s[:N]`/`s[i:j]` 越界 panic 前, 先回答输入切片的 cap 与分配者;
  (2) 2-index 切片边界条件 = `j ≤ cap(s)` (非 len)——len 小 cap 大时恒不越界,
  读到的是 cap 内未初始化尾区; (3) ReadAll/ReadFile/网络缓冲类输入的 cap ≥
  初始缓冲常量, 固定小 N 的前缀切片恒安全——"无长度守卫即 panic" 声称不成立;
  (4) 判据: 声称 panic 必须给出 cap 证据 (分配点/增长策略), 无 cap 证据 →
  降级为"无守卫的代码卫生建议"而非漏洞。
- **CK-MAGNITUDE-OWNERSHIP** family=empirical, applies_to=["verifier","refuter"]:
  steps: (1) 资源类声称 (oom/unbounded/高占用) 先列量级变量: 单请求上界 S 与
  聚合上界 N 各自由谁控制; (2) S 由部署内容尺寸/配置决定且攻击者只控制"请求
  哪个既有资源"+并发数 → 量级驱动权不在攻击者; (3) N 受平台 fd/连接/流上限
  约束 → 无攻击者可控的无界维度; (4) 判据: 两上界均非攻击者输入 → 不得报
  remote oom——按加固缺口口径 (部署前提显式标注) 或降 NEEDS_REVIEW。

## P 分层序列

P1 workflow_export 绝对化 → P3 两条清单条目 → P4 版本链五件。
