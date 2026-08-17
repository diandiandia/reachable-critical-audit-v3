# Python 实证工具链手册 (v3.1)

> 来源：W6_MORE_LANGS_FINDINGS.md（Django 批次，§14）。实证工件：`/root/django/.audit_results/empirical_harness_t1.py`、`empirical_harness_t2.py`。

## 1. 工具链探测
- **纯 Python 项目实证环境成本最低**：`venv` + `sys.path.insert(0, '<audit-src>')` 直接导入审计源码即可跑全链路；Django 批次实测 `settings.configure(...)` + `django.setup()` 最小运行时启动真实 ASGIHandler（W6 §14.8 + t1 harness 工件）——无需安装目标包。
- 依赖补齐：纯 Python 依赖（如 asgiref）用 **skill 自带的 venv** 补齐（W6 §14.8）；探测 = `python3 --version` + `python3 -m venv` + 检查 skill venv 路径。
- 协议面实证：`subprocess` 起 `runserver` 可测协议层行为（W6 §14.8）；但 runserver 是开发专用面（默认回环绑定 + 启动 WARNING，W6 §14.4），仅用于机制验证不作为可达性证据。
- 环境事实：审计批次环境 Python 3.14.4（t1/t2 harness 运行事实）——跨环境行为差异（如 zip 实现、regex 优化）须记录。

## 2. 版本记录义务
- 记录 python3 精确版本 + 审计目标版本（Django 6.2.0）+ 依赖版本（asgiref 等按 venv 实际版本）。
- **框架 gate 版本化**：ALLOWED_HOSTS 行为矩阵（默认全锁=退化阻断 vs `'*'`=零阻断）随版本与文档演进，裁决记录必须注明依据版本（W6 §14.7）。
- 运行时版本影响利用性维度（§13.4 通用）：Python 的 regex 优化/stdlib 行为随小版本变化，ReDoS 类实证先做 pattern 搜索（自动原子化假阴性，§13.4）再做版本矩阵。
- 声称类先定类：protocol_dos 类声称（如 ASGI 无界落盘）按攻击影响定类，实证成本不得改判（§13.9 通用）。

## 3. 常见陷阱清单
- **通用 regex 签名零区分度**：11 条 Python 规则 1784 命中 → 81 假设 0 keep——命中全是防御性转义（escape/re.escape/base64）、框架自配置、有界结构；Django 真实 sink（asgi read_body 无界循环、RequestSite.get_host、pickle.loads 三后端族、safe_join）零签名覆盖——通用规则（append/encode）应降权或退役，补框架语义族（asgi receive 循环落盘 / get_host+validate_host / pickle.loads+cache、session 后端矩阵 / tag_re 正则 / import_string 配置族）（W6 §14.1）。
- **LLM 假设生成器的防御性偏差**：23 假设中 13 条是"防御验证签收"（gate 已 Read 验证后建议不投入）——假设必须指向残余面，签收类假设不占 R3 队列，且防诱导 verifier 复读（W6 §14.2）。
- **"检查点晚于累积点"**（H1 清单第一条）：ASGI read_body 全量落盘后 `_check_data_too_big` 才可触发 + body_receive_timeout 死代码——T1 实证 10,000× 超额；写循环内无预算检查是该族红旗（W6 §14.3，三次复现模式）。
- **开发专用面 ≠ 可攻击面**：runserver 默认回环绑定 + 模块自述非生产 + 启动 WARNING + 414/close 全有界 → 降级 NEEDS_REVIEW；证伪者论点需要实证闭环——协议走私声称必须实测跨请求边界（T2 证明残留字节仅同连接自混淆）（W6 §14.4）。
- **gate 翻转语义区分**：ALLOWED_HOSTS 属"必然翻转的配置 gate"（任何可用部署必须设 `'*'` 或清单）→ 保留 REACHABLE + 记录矩阵；runserver 属"被警告的非默认操作"→ 降级——区分标准 = 是否存在任何可用部署必须翻转该 gate（W6 §14.7）。
- **agent 行号漂移**：46 surface 中 3 处行号漂移被 suggested_line 捕获（W6 §14.6）——逐行证据校验是有效防线。
- **成熟框架的假设产出天花板**：Django 批次 10 候选 → 2 REACHABLE + 1 降级，R3.5 拦截（runserver 开发面、ALLOWED_HOSTS 矩阵裁决）——成熟框架的 R3 假设应预设"机制真 ≠ 危害真"，verifier 对默认值类声称系统偏乐观（§20.1/§21.5 通用先验）。

## 4. 阳性模式（战役验证过的做法）
- **最小真实运行时模板**（可复制）：`sys.path.insert(0, audit_src)` + `settings.configure(DEBUG=False, ALLOWED_HOSTS=[...], DATA_UPLOAD_MAX_MEMORY_SIZE=<缩小限额>)` + `django.setup()` → 直接实例化真实 handler 类跑攻击载荷（t1 harness 工件）——**跑真实框架代码而非复刻逻辑**（§18.5 精神）。
- **声称类一律实证**：纯 Python 实证成本接近零（venv + sys.path）——Python 项目的所有声称类都应按此执行（W6 §14.8）。
- **verifier/R4 自发小实证被鼓励**：verifier 跑真实 Django checkout 验证 stdlib policy fail-closed（CAND-010 邮件头 CRLF）；R4 agent 实证 O(n²)（模板 tag_re 60KB>60s）——实证结果落 verdict.empirical 字段，即使结论是 UNREACHABLE（W6 §14.5）。
- **subprocess 起真实服务测协议面**：runserver 的 414/close 行为、跨请求边界残留验证（T2 对照）用真实进程（W6 §14.4）。
- **全链路导入验证**：`django.setup()` 触发所有信号/过滤链注册（§17.4-17.5 的动态注册教训在 Python 侧对应 setup 后状态）——harness 必须走完整 setup 而非 import 局部模块。

## 5. 网络依赖
- **核心实证零网络**：venv + sys.path 导入审计源码离线可跑；asgiref 等纯 Python 依赖从 skill venv 补齐（W6 §14.8）——无 pip 环境时手下载纯 Python 依赖即可（§14.8 记录）。
- runserver 协议实证本地回环完成，无外部网络。
- lessons 未记录 Python 批次的网络阻断；网络不可达时按 §21.4 降源事实级 + 记录 blocker，但 Python 场景应极少触发。

## 6. 实证范围建议
- **E2E 全覆盖**（Python 专属档）：实证成本接近零（W6 §14.8）——所有声称类一律 E2E；ASGI 无界落盘（T1 10,000× 超额）与 Host 投毒密码重置两个 REACHABLE 均以 E2E/机制实证收束。
- **机制级**：仅当需要真实服务进程（runserver 协议面）时叠加；机制级实证只支撑 edge_proven（§17.7 规则）。
- **对照矩阵必带**：默认配置拒绝 vs 弱化配置接受（如 DATA_UPLOAD_MAX_MEMORY_SIZE 缩小限额 + 默认限额两组测量）——§24.4 模式在 Django harness 直接可用。
- 分层：函数体级（tag_re O(n²)）→ 机制级（handler 单例注入）→ E2E（真实 Django checkout + runserver）按声称强度选档，报告标注 scope（§15.6 规则）。
