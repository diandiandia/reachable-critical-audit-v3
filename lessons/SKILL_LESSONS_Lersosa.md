# SKILL Lessons — Lersosa（2026-08-17）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = application

### R3
- [grade_recomputed] CAND-001: 机械分级重算 (main-agent R3.5: edge_proven→empirically_confirmed（证伪者#1 端到端实证：8TB 声明→RSS 980755)
- [grade_recomputed] CAND-003: 机械分级重算 (evidence_ledger v3.2)
- [grade_recomputed] CAND-004: 机械分级重算 (evidence_ledger v3.2)
- [grade_recomputed] CAND-008: 机械分级重算 (evidence_ledger v3.2)
- [grade_recomputed] CAND-009: 机械分级重算 (evidence_ledger v3.2)

### R3.5
- [strengthened] CAND-001: 攻击可零带宽触发：仅一条纯元数据首消息（fileSize=16GB，不发送任何 chunk）即同步完成 make 预分配并 OOM SIGKILL；接收循环 (file_upload_cmd_exe.go:126-141) 无总量上限、无 ; 真实攻击链已实证：单条流首消息（约百字节）声明 fileSize=8TB 即令服务器 RSS 提交 9.4GB，第二条流声明 16TB 即 OOM kill；mTLS 门禁可用仓库内随附的客户端证书+私钥对直接通过。附加面：流无 deadl
- [attribution_correction] CAND-001: 『三层全开 0.0.0.0:9003 明文可达』错误 — shipped config 在 Linux 上因客户端 TLS 配置失败是致命错误（file_provider.go:29→wireApp→main.go:80 panic），9003 未绑定；可达部署形态（Windows 或路径修正后 Linux）服务端 TLS 加载成功并强制 gRPC mTLS。真正可达路径是『mTLS 门禁 + 仓
- [strengthened] CAND-003: artifact_dir 重定向可与同样无鉴权的 agent 流水线组合：agent_task_submit/agent_chat_turn (routes.rs:31-33) 触发训练并把模型写入可预测路径 artifacts/runs/; artifact_dir 重定向不需要任何文件写入能力：(a) 纯网络 DoS：artifact_dir="/dev/zero" → 每次 infer/generate 的 TransformerLmTrainingConfig::load
- [attribution_correction] CAND-003: 『CSRF 可达』子声明不成立，已删除：axum 0.8 Json extractor 对非 application/json 返回 415，跨源 fetch 携带 JSON 必触发 CORS 预检而全仓无 CORS 支持（OPTIONS /v1/reload 405 且无 Access-Control-Allow-*）。可达攻击者仅列：本机进程（127.0.0.1，主路径）+ 容器邻居/远端（仅
- [verdict_correction] CAND-004: 调用边真实性证伪成立（证伪者#0 实证 + 主代理 find_spec 复核：common/infrastructure 顶层包均 None；Dockerfile ENTRYPOINT python src/main.py，sys.path[0]=src/，无 PYTHONPATH 别名机制）
- [verdict_correction] CAND-004: verifier 归因两处精度修正（证伪者#1）：『lifespan include_router』实际路径是 BeanContainerManager._register_controller_routes(bean_container_manager.py:230) 在 BeanLifecycle 启动钩子执行；『SSRF 全维度无阻断』略不精确——默认 robots smart 策略存在 RobotsCheckHandler 但不构成安全阻断（自身即 SSRF、失败即放行、strategy_name=disabled 可绕过）
- [verdict_correction] CAND-004: SSRF 维度比原判定更广（存活面）：响应体经攻击者可控 CSS/XPath 解析落盘、默认跟随重定向、headers 攻击者可控（IMDSv2 token/Host）、SmartRobots 对目标主机先发 robots.txt 探测、元数据服务可直接作 url_template
- [demotion] CAND-004: 
- [strengthened] CAND-004: SSRF 非盲打且维度比原判定更广（响应落盘+重定向跟随+可控 headers+robots 双探测+元数据直连），但入口边断裂使其当前不可达——保留为修复即可达条件候选。
- [attribution_correction] CAND-004: evidence_grade edge_proven 应降级：静态逐行链未覆盖运行时导入解析；真正的阻断点是 required_args_constructor.py:39 顶层 common 导入断裂。
- [verdict_correction] CAND-007: 2/2 证伪：『write→upload→出站连接攻击者 MinIO』在默认/全新部署下不成立（Redis 门闩 + JSON 形状不匹配 + 缓存键无写入方），原 REACHABLE 为过度声称（evidence_grade=static_only 未核验缓存层状态依赖）
- [verdict_correction] CAND-007: 幸存事实（两侧证伪者独立确认）：(1) 未认证 GET /resource/v1/oss-config PageOssConfig 明文返回全部行 SecretKey/AccessKey（→ 新候选 CAND-011）；(2) 未认证 DELETE 可删光配置致上传 DoS；(3) 写端无鉴权+零校验属实，若修复缓存层错误分支则 write→upload 重定向立即成立（修复即可达跟踪项）
- [verdict_correction] CAND-007: 归因修正：verifier 漏掉 gRPC adapter 与 domain 之间的 Redis 缓存层；repo.List 无 Order 时 entities[0] 是旧配置而非攻击者新行
- [demotion] CAND-007: 
- [strengthened] CAND-007: 未认证读路径 GET /resource/v1/oss-config（Page）直接读 DB、不经缓存，convertor.ToOssConfigCo 含全部凭据字段——存量 OSS 密钥静态披露（CWE-522，转 CAND-011）; 未认证 DELETE /resource/v1/oss-config 可删光配置造成上传功能 DoS；写端无鉴权+零校验本身属实，若修复缓存层错误分支则 write→upload 重定向将立即成立（修复即可达）
- [attribution_correction] CAND-007: verifier 承重前提 P4 漏掉同文件 63-73 行的 Redis 前置门闩及 oss_config_redis_impl.go:47-60 条件反转 bug；『凭证渗出』impact 框架有误——攻击者写入的是自己的凭据，真实危害是数据重定向/可用性破坏/Domain URL 投毒，真正的凭据披露是未认证 PageOssConfig 读接口。
- [strengthened] CAND-008: 写路径连业务层校验都没有：oss_config_domain_service.go:92-99 SaveOssConfig/ModifyOssConfig 零检查一行透传到 repo.Save/repo.Modify，攻击者可无约束写入/篡; 凭证泄漏面覆盖全链路：PostgreSQL 客户端证书+私钥在仓且有效（config.yaml sslcert/sslkey）；redis/postgres/elasticsearch 密码 Zcx@223852// 明文在仓，docker
- [attribution_correction] CAND-008: 『tls_enable 零值 false 默认明文』表述不精确：5 个在仓 configs 全部显式 tls_enable: true，零值 plaintext 路径仅适用于遗漏该字段的部署。真正的、也是充分的门禁击穿是证书密钥在仓（已用 openssl 实证链有效）+ Windows 绝对路径在 Linux 加载失败 log-and-continue 明文（grpc.go:40-44/http.
- [verdict_correction] CAND-009: 2/2 证伪：部署布局下整条链每个模块都不可导入（30+ 链上模块裸顶层导入 infrastructure；@RequiredArgsConstructor 装饰器模块裸导入顶层 common），ComponentScanner 吞错 → 0 爬虫 bean/路由注册 → 404（实证启动）
- [verdict_correction] CAND-009: verifier 边证据归因错误：(a) 引用 chain.py:367-369 作为责任链组装证明，但该文件仅 79 行，行号不存在——责任链组装实际在 crawler_gateway_impl.py:_build_pipeline(:343-371)；(b) 鉴权注释行应为 bootstrap.py:72 而非 :78（:78 在 _add_cors_middleware docstring 内），注释禁用实质结论为真；(c) evidence_grade edge_proven 与实际不符：关键边依赖不可导入的模块
- [verdict_correction] CAND-009: 『训练正样本目录同树』错误：OUTPUT_DIR 带 src/ 前缀与训练目录不同树（Docker CWD 下）；全仓库无任何代码读取 crawl_sample.jsonl/csv——训练投毒链路无消费端证据
- [verdict_correction] CAND-009: 修复即可达跟踪：若上游修复 required_args_constructor.py:39 导入（from app.common.utils...），入口恢复，其余链节经 2 独立证伪者逐跳复核全部属实
- [demotion] CAND-009: 
- [strengthened] CAND-009: 无——入口 404 使原链整体不可达。但补充观察：即便不修 import，若该链将来可达，同链还天然构成未认证 SSRF（static_page_strategy.py:139 requests.Session.get 任意 URL + s
- [attribution_correction] CAND-009: 证伪仅限于『当前部署布局下可达』；底层机制真实存在（verbatim 写无公式中和、validate_all_tasks 仅查非空、鉴权注释禁用、CORS *、pages.start/end 无界整数是独立存在的次级向量）。
- [strengthened] CAND-010: 凭据暴露面远大于原判定：同一明文密码 Zcx@223852// 在 git HEAD 覆盖至少 7 个文件（5 份 configs/config.yaml + docker-compose-dev.yml:22/90/116/130 + p; 独立于密码的第二条利用路径：TLS 客户端私钥被提交且未 gitignore（ai/stellar certs + doc/config/ssl/client），服务全部 tls_enable: true / sslmode=verify-
- [attribution_correction] CAND-010: 调用点数量勘误：宣称 3 处实际 2 处可达。app/stellar/interface/.../data.go:44 的 NewCreateClient 未接入任何服务二进制（wire.go 未含 infrastructure provider），为死接线；活调用点为 stellar/service 的 status_data.go:84 与 info_data.go:84，经 wire_gen
- [strengthened] CAND-011: 未认证 DELETE /resource/v1/oss-config 可删光配置造成上传功能 DoS；未认证 POST 写篡改面属实（若未来修复缓存层错误分支，write→upload 出站重定向将立即成立——修复即可达跟踪项）。

### 裁决
- [adjudication_note] Lersosa R3.5 主代理裁定（wf_6944bdcf-0c2，14/14 证伪者，962k tokens）：7 候选经受 N=2 对抗证伪——4 存活（CAND-001 分级升级为 empirically_confirmed、CAND-003、CAND-008、CAND-010）、2 降级 NEEDS_REVIEW（CAND-004/009 共享入口边断裂：顶层 common/infrastructure 导入失败 → crawler 控制器零注册 → 404 实证，主代理 find_spec 复核确认；修复即可达）、1 降级 UNREACHABLE（CAND-007 出站链被 Redis 门闩阻断，2/2 证伪）+ 转正新候选 CAND-011（未认证 OSS 凭据读取，2 独立对抗证伪者确认）。一致性裁决：CAND-004/009 同入口边统一降级（PREC-CONSISTEN

### 验收
- [acceptance] {"project": "Lersosa (github.com/Leyramu/Lersosa) — v3.2 混合项目试审", "target_kind": "application", "language_inventory": {"go": 374, "python": 176, "rust": 53, "typescript": 32}, "surface_map": {"total": 51, "go": 20, "python": 17, "rust": 13, "typescript": 1}, "criteria": {"1_language_coverage": {"result": "PASS", "table": [{"lang": "Go", "surfaces": 20, "candidates": ["CAND-001", "CAND-007", "CAND-

## 主代理过程观察（人工补充）

- R3 verifier 盲区一: 「函数存在≠被调用」扩展为「模块存在≠被导入」— CAND-004/009 的 verifier 逐行核实 9 跳调用链全部为真, 但顶层 common/infrastructure 导入断裂使整个爬虫组件栈在运行时零注册 (POST /crawler/run 404 实证)。静态逐行链必须补『模块可导入性』预检: 顶层包解析 (find_spec) + DI/组件扫描器的吞错路径审查。
- R3 verifier 盲区二: gRPC adapter 与 domain 之间的缓存层被整层漏掉 (CAND-007) — verifier 只核验了路由→controller→repo 直通, 未发现 GetDefaultOssConfig 的 Redis 前置门闩 (且该门闩错误分支写反是死代码)。verifier 任务书应要求对消费端中间件/缓存/门闩层做显式枚举, 不能只沿调用链直查。
- R3 verifier 部署前提错误集中爆发: CAND-001 声称『三层全开明文 0.0.0.0:9003』实际 Linux 下客户端 TLS 失败是致命 panic (进程根本不监听); CAND-008 声称『tls_enable 零值默认明文』实际 5 份 shipped config 全部显式 true。教训: 『默认可达』类 gate 必须核对 shipped 配置文件的实际值而非代码零值; 平台限定路径 (Windows 证书路径) 必须在证据中显式标注。
- R4 与 R3 交叉验证价值: H-7 f1 (tls fail-open 明文) 在 CAND-001 原判定出错处是正确的 — R4 假设层捕获了 R3 verifier 漏掉的部署层真实形态。建议制度化: R4 H-7 默认值盘点结果反向回灌 R3 候选的 gate 证据。
- target_kind 缺失 (R0) 二次出现 (与 fixture 验收同根因): Lersosa 为 application 型, verifier 未经 target_kind 约束的『默认部署』假设在 3 处出错。target_kind 判定 + 部署实证前置是 v3.2.1 最高优先项。
- 判据①措辞缺陷 (v3.2.1 候选): REQ-V3.2-100 判据①『每语言 ≥1 surface 且非零候选』未区分客户端组件语言 — Lersosa TS 前端 (32 文件, 浏览器组件) 零候选但覆盖面经边界面 (SURF-BOUND-LER-009) cross_evidence + Go 侧归因达成。建议判据限定服务端组件语言或接受边界面裁决等价。
- R3.5 证伪者实证纪律红利: CAND-004/009 的 404 实证 (实际启动服务 + 启动日志 + curl) 纠正了 9 跳逐行静态核实为真的 verifier 判定; CAND-001 证伪者的端到端 OOM 复现 (8TB→RSS 9.4GB) 纠正了原探针的错误机制数字 (~1.2MB/GB 提交比而非 4GB 全提交)。证伪者默认立场『有疑问即 refuted』+ 允许实证的机制设计有效。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
