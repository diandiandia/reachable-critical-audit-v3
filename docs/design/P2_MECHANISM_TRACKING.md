# P2 机制追踪矩阵（补格批次: cpp-httplib / devise / cosign / java-jwt）

> P2 目标：补覆盖格缺口（AUTHN×cpp/ruby、DATA-INTEGRITY×go、CRYPTO×java）+ PREC 精度门回归。
> 判据同 P1：10 项机制在真实波次中至少使用一次；六门禁全 PASS；REACHABLE 结论可追溯。

## 项目进度

| 项目 | 语言 | target_kind | R3 候选 | REACHABLE | 六门禁 | 状态 |
|---|---|---|---|---|---|---|
| java-jwt | java | library | 2 | 1 (oom 实证 9.4-18x) | ✅ PASS 8/8 | 报告+lessons+R6 完成 |
| cosign | go | application | 4 | 3 (env 反射泄露实证 / 无界 blob R5 实证 / symlink 写) | ✅ PASS 39/39 | 报告+lessons+R6 完成 |
| devise | ruby | library | 4 | 2 (sign-in 枚举 + **复活新增 bcrypt cost 炸弹, Medium**) | ✅ PASS 20/20 | 报告+lessons+R6 完成; 复活改判 gate 通过 (证伪 0/2, cost=20 已 41s 强化) |
| cpp-httplib | c | library | 9 | 6 (TOCTOU / 队列无界 R5 实证 / 解码器 / **复活改判 SIGBUS crash / SIZE_MAX 解压 unbounded / state-0 O(N²) protocol_dos**, 4 实证) | ✅ PASS 29/29 | 报告+lessons+R6 完成; 复活改判 gate 通过 (3/3 证伪 0/2) |

## 复活闭环（R3.5-N, P2 最大机制产出）

P2 复活攻击 8 出 5 revived（63%），远超 P1：

| 项目 | 候选 | 复活缺口 | 重验结果 |
|---|---|---|---|
| devise | CAND-002 | bcrypt 存储 hash cost 指数放大（cost=31 ≈23.8h/次登录, 写原语 gate 宿主部署面） | REACHABLE 条件式（stretches=12 事实错误指正, 实证 cost12/14/16 四倍几何）→ 补 R3.5 证伪中 |
| cpp-httplib | CAND-002 | Windows fullwidth (%uFF0E/%EF%BC%8E) 穿越, canonicalize=_fullpath 词法不转换 | **gap 被反驳**: NTFS/Win32 内核对全角按字面名处理（DNN CVE-2025-52488 证明需应用层 NFKC, httplib 无此层）→ UNREACHABLE 维持（12 边更强理由） |
| cpp-httplib | CAND-003 | SSL 构建 SSL_write 用户态 memcpy 读映射 → SIGBUS（EFAULT 仅明文 TCP） | **改判 REACHABLE crash**: TLS1.3 默认配置 exit=135 SIGBUS 实证（TLS1.2/明文优雅, 配置矩阵）→ 补 R3.5 证伪中 |
| cpp-httplib | CAND-004 | SIZE_MAX 分支解压守卫 no-op + 总时限禁用 + redirect 旁路背压 | **改判 REACHABLE unbounded**: 三条 gap 全实证（214:1 解压交付 127MB 冲破 README 100MB 宣称+负对照; 滴流永不终止; 302 旁路 12.4MB 丢弃）→ 补 R3.5 证伪中 |
| cpp-httplib | CAND-007 | state 0 O(N²) 重扫（verifier 自测 2.69e11 ops@1MB 与自身裁决矛盾） | **改判 REACHABLE protocol_dos**: 8MB/4MB 比值 3.99 纯二次方, 100MB 整请求 75.2s 单核, 1B 块变体 8MB>600s → 补 R3.5 证伪中 |
| java-jwt | CAND-001 | 未复活（线性扫描机制证伪确认） | — |
| cosign | CAND-001 | 未复活（verifier 枚举计数 8→12 处被指正, 结论不变） | — |
| devise | CAND-001 | 未复活（DB 内比较+熵屏障确认） | — |

## 10 机制使用记录

| # | 机制 | 证据 |
|---|---|---|
| 1 | wave registry 簿记 | 4 项目各 verify/refutation/resurrect/re-verify 波全登记（含 supplementary 波注记） |
| 2 | collect --expect 对账 | 每波均带 --expect, 零张冠李戴 |
| 3 | gap 渲染 (SWR-020) | 5 候选 re_verify_gap 渲染实测（cpp-httplib ×4 + devise ×1, prompt 含「复活复核 gap」段） |
| 4 | r35-collect 落盘 | java-jwt/cosign/cpp-httplib/devise 全部候选 refutation 字段落盘（含 strengthened/attribution_corrections） |
| 5 | 复活改判 gate (SWR-005) | devise CAND-002 真实触发: revived→重验 REACHABLE→无 refutation→补 R3.5 证伪（流程进行中） |
| 6 | coverage CLI surface_data | 4 项目 assert_ledger surface_data 计算实测 |
| 7 | coverage-ledger 回填 | java-jwt (AUTHN×java 2, RESOURCE-DOS×java 6), cosign (RESOURCE-DOS×go 3, WEB×go 1) --write 完成 |
| 8 | 0.5 门控双形态 | java 完整段 / go 完整段（go.mod import 图）/ c 短段「构建包含性一行核对」/ ruby 短段（gemspec 打包核对）四形态对照成立 |
| 9 | PREC 精度门 | 复活重验轮 PREC-DEFAULT-3LAYER-001/PREC-CONFIG-FLIP-001/PREC-CAPABILITY-001 注入并实际用于裁决（devise CAND-002 条件式 REACHABLE 形态）; CAND-001 机制级证伪拦截（java-jwt/cpp-httplib CAND-005 同款） |
| 10 | 清单绑定 | CK-PATH-GUARD (CWE-22)/CK-CRYPTO-MISUSE (CWE-347)/CK-AUTHN-BYPASS/CK-SENTINEL-SEMANTICS 绑定实证; CK-WS-MATERIALIZE 误绑缺陷在 P2 项目继续出现（CWE-400 通用码, verifier 普遍自行判 N/A——W6 §32 缺陷#1 佐证） |

## P2 过程中新发现的 skill 缺陷（→ W6 §33 / v3.4.3 候选追加）

1. **R4 任务书 schema 漂移**：cpp-httplib H1-H4 agent 产出 hypotheses 对象键 + findings 顶层数组 + evidence 数组 + r3_link 嵌套 dict 的非 canonical 形态——r4-collect 0 提取告警后主代理手工转换。候选修复：r4-collect 增加 schema 自适应（hypotheses 对象形态/evidence 数组 join/r3_link dict 展平），或 R4 任务书加输出自查段。
2. **R4 agent tracked_surfaces 自造 id**：cpp-httplib H1-H4 agent 用 SURF-DATA-00X 前缀（R1 测绘自身是 SURF-DAT-00X 混合前缀）——SWR-V3.3.2-015 再次被违反。候选修复：R4 任务书附实际 surface id 清单（而非"原样引用"指令），或 r4-collect 归一化时做前缀模糊映射。
3. **resurrect 模式无 CLI**（W6 §32 #8 再现）：batch_verify --mode resurrect 报错, export_script_resurrect 需 workflow_export 直调 + 主代理手工落盘 resurrection_review。
4. **resurrect/refute prompt 截断**（W6 §32 #5 再现）：resurrect_prompt 1200 字符静默截断（无标记, 比 refute_prompt 的 800 有标记版更糟）——P2 全部复活/证伪波由主代理重建完整证据版 args。
5. **R1 surface id 前缀不一致**：cpp-httplib SURF-DATA-001 + SURF-DAT-002..008 混合——R1 测绘/合并层未统一前缀, 下游 tracked_surfaces 对照频繁误配。候选修复：surface_mapper merge 时前缀归一化。

## PREC 精度门回归判断（P2 专项）

java-jwt CAND-001 注入 PREC-STREAM-MATERIALIZE-001/ENGINE-MATRIX-001（均不适用标注）+ verifier 以机制级"线性≠超线性"裁决 UNREACHABLE——精度门在库型线性扫描类上表现正确。P1 记录的"无适用性过滤"缺陷（PREC-STREAM-MATERIALIZE 注入非 WS 候选）在 P2 未造成误判（verifier 普遍自行判 N/A 并记录），但缺陷本身未修复——仍为 v3.4.3 候选。

## 覆盖格判定（P2 选题判据）

- AUTHN×cpp: cpp-httplib CAND-002 (CWE-22)/R4 H5 (CWE-285 遮蔽型鉴权绕过 Medium, 实证 route_calls=0)——AUTHN 家族在 cpp 有产出 ✓
- AUTHN×ruby: devise CAND-001/004 (CWE-203/204) + R4 H6 (CWE-307)——✓
- DATA-INTEGRITY×go: cosign R4 H1/H2 (bundle 无界读取/证书链 panic)——数据完整性验证面（sigstore）产出 ✓
- CRYPTO×java: java-jwt R4 H7 密码学默认审查（HMAC isEqual 常数时间/PSS 参数固定）+ CAND-002 验签路径——✓
- 最终以 coverage-ledger --write 聚合为准
