# SWR_V3_33: Servo 验收复盘修复条款

每条 SWR 含裁决理由 + 测试守卫 + 义务三问结论。案例支撑 = /root/servo/.audit_results/lessons.md (N-1..N-5)。

## D-1 merge 同 id 碰撞标注

**SWR-V3.33-001**: surface_mapper merge 检测跨文件同 surface id 碰撞, 碰撞对落
`conflicts` 列表 (条目含 surfaces 双 id + 各自首个锚点 + resolution="kept-first-same-id"),
去重行为 (first-wins) 保持不变。

- 裁决理由: 静默覆盖曾致 18 面丢失 (servo N-1); 标注不阻断——主代理收口对账
  (Σ域文件面数 == merged 面数) 才有机械依据; 与现有 kept-first-multi-domain
  (同锚不同 id) 冲突标注对齐。
- 义务三问: 触发=merge 运行 (无条件, 机制自身形态); 消费者=主代理 R1 收口 +
  conflicts 渲染; 裁掉丢什么=18 面静默丢失实录。
- 测试: 合成双文件同 id 输入 → merge 输出 conflicts 含同 id 对; 无碰撞 → conflicts 无该形态条目。

## D-2 R1 域覆盖收口 warn

**SWR-V3.33-002**: merge 收口时对 DOMAINS 四类各计数; 某域无文件且无
(reviewed_by+empty_domain_reason) 签收 → 输出 warn 级 `domain_unmapped`
violations (提示级不阻断, 主代理裁决重派或补签收)。

- 裁决理由: servo process/storage 零派发零记录, layout 组件零面 (fixminer 显示
  layout 崩溃修复史, 漏测成本真实); 空域合法结论已有 empty_domain_reason 契约,
  本条款只补"没派发也没签收"的机械可见性。
- 义务三问: 触发=merge (R1 收口必达点); 消费者=主代理; 裁掉丢什么=servo 零面实录。
- 测试: 四域文件齐 → 零 warn; 缺 process+storage 且无签收 → warn 2 条; 缺域带
  empty_domain_reason 签收 → 零 warn。

## D-3 filter focus_sink 路径存在性校验

**SWR-V3.33-003**: r2_guard fidelity 对 keep 条目 focus_sink 做路径存在性校验
(相对路径按 project_root 解析), 缺失 → error (主代理拒收补查, 附 filter 任务书
「路径存在性自检」义务已有, 本条为机械面)。

- 裁决理由: HYP-043 路径段漂移直到主代理抽查才发现 (servo N-4)。
- 义务三问: 触发=fidelity 运行; 消费者=入队前主代理; 裁掉丢什么=路径漂移实录。
- 测试: keep 含不存在路径 → error; 合规路径 → 零 error。

## D-4 fidelity surface_ids 一致性校验

**SWR-V3.33-004**: r2_guard fidelity 校验 keep/drop/bc 三组条目 surface_ids 与
hypotheses.json 原样一致 (元素级), 不一致 → error (verbatim 继承规则的机械面;
restore 通道保留供旧形态缺省)。

- 裁决理由: B 批 15 处重写、4 处编造不存在 id (servo N-4)——门禁⑦计数失真面。
- 义务三问: 触发=fidelity; 消费者=门禁⑦ tracked 计数; 裁掉丢什么=计数失真实录。
- 测试: 重写条目 → error; 原样继承 → 零 error。

## D-5 reviewed_clean Medium+ findings 归位提示

**SWR-V3.33-005**: r4-collect 对 verdict=reviewed_clean 假说中 severity∈{Medium,
High, Critical} 的 findings 输出 warn `reviewed_clean_medium_plus` (主代理裁决:
升 confirmed 承载 / 主代理段补报 / 明确留档三选一); SKILL.md R4 段补同文条款。

- 裁决理由: servo:config 点击劫持 (CWE-926/1021 M) 与 TrustedPromise 滞留
  (CWE-401 M) 是真实确认问题, 被 reviewed_clean 语义留在 B.4 计数 (servo 复盘判型)。
  不自动改写 verdict (修法形态纪律)。
- 义务三问: 触发=r4-collect 且存在该类 findings; 消费者=报告问题清单; 裁掉丢什么=两 M 实录。
- 测试: reviewed_clean+Medium finding → warn; Low 或 confirmed → 零 warn。

## D-6 报告去重检查承载候选终态

**SWR-V3.33-006**: 报告渲染器同事实去重条件改为: r3_link 承载候选 verdict==REACHABLE
时去重; 否则 finding 自列 (行尾注「同事实候选已非 REACHABLE, 见附录 A」)。

- 裁决理由: H-1 四条 High/Medium finding 整体消失, 主代理手工 r3_link 置空修复
  (servo 收官实录); 修复后无需手工干预。
- 义务三问: 触发=报告渲染且 r3_link 存在; 消费者=问题清单; 裁掉丢什么=High finding 消失实录。
- 测试: 合成队列 r3_link 候选 NEEDS_REVIEW → finding 自列; REACHABLE → 去重行。

## D-7 hints lessons_refs 补种格通道

**SWR-V3.33-007**: language_issue_matrix.hints 的 lessons_refs 检索增加该语言
seeded 格的 source_lessons 条目 (前缀 "matrix/"), 与既有 lessons/ 文件名检索合并;
去重保序。

- 裁决理由: rust lessons_refs=0 (D-4 杠杆证伪, v3.32 判据实录); 矩阵 source_lessons
  是两段式回填的知识基座 (servo 收官已回填 5 格), 且不读任何项目路径
  (第一原则三禁止③合规)。
- 义务三问: 触发=hints 调用; 消费者=R2 假设生成提示 (D-4 杠杆); 裁掉丢什么=rust 检索失效实录。
- 测试: rust refs 含 matrix/ 条目; 未种格语言零注入。

## D-8 fixminer 文件路径信号通道

**SWR-V3.33-008**: fixminer 评分在 subject 关键词净分基础上加文件路径信号
(安全敏感路径模式: 密码学/解析器/内存管理/安全/权限目录, 低权重)——
净分>0 入选门槛与 GENERIC_FIX_WORDS 精度护栏不变; 输出附 path_signal 计数。

- 裁决理由: 召回上限 (关键词漏采) 为 v3.32 判据实录的已知边界; 扩展不牺牲精度护栏。
- 义务三问: 触发=fixminer 运行; 消费者=R2 修复驱动假设; 裁掉丢什么=召回上限实录。
- 测试: 无关键词但路径命中的 commit 入选; 纯通用 fix 词+路径命中的边界用例按净分门槛判定。

## D-9 生成码包络条款 (P3)

**SWR-V3.33-009**: SKILL.md 报告段「发现包络边界声明」增 (f) 构建期生成物类:
「(f) 构建期生成代码 (codegen/DSL 编译产物、宏展开产物等磁盘无源物)——审计
生成器源码与调用契约, 生成物按依赖边界处理; 构建环境可行时应物化 (build 后
读 OUT_DIR/生成目录) 纳入面图」。案例: servo WebIDL codegen 层 (CAND-020 锚点断裂)。

## D-10 行号漂移裁决条款 (P3)

**SWR-V3.33-010**: SKILL.md R1 段漂移裁决条款补: 「裁决依据固定为 snippet 首行
实际锚点 (定义形态), suggested_line 仅作候选——其语义是距声称行最近的全文命中,
多语句 snippet 会错锚 (命中 snippet 中段/函数内他处同名调用)」。案例: servo
13 处漂移中 3 处定义形态裁决 (NET-003/006/004, N-2)。

## D-11 harness 依赖钉死条款 (P3)

**SWR-V3.33-011**: SKILL.md R5 落盘规范补 harness 条款: 「(a) 独立 harness crate
的依赖解析不与 workspace Cargo.lock 共享——版本敏感依赖必须对照目标仓
Cargo.lock 钉死 (=x.y.z); (b) lib 名≠包名 ([lib] name 段) 是常见形态, import 按
lib 名; (c) --offline 可行性探测含 git 依赖面 (workspace 根清单的 git 源会阻断
离线解析)」。案例: servo N-5 (CSP Destination E0004 / net_traits、pixels lib 名 /
stylo git 阻断)。
