# BIAS_EVAL_V3_33: 四缺陷评估 (设计期)

实现期 (阶段 3 完成后) 必须重跑一遍并核对实现是否引入违规。

## ① 盲目带入历史审计信息

- 检查点: 11 条缺陷的案例支撑全部指向本会话产物 (servo lessons N-1..N-5 +
  收官实录), 零凭记忆转述——设计件写完后已对照 lessons.md 原文核对
  (N-1 18 面数字 / N-4 15 处重写 4 处编造 / N-5 CSP E0004)。
- 去项目化: 新条款文本 (D-9/D-10/D-11) 与代码注释**零项目名**——servo 只出现在
  source 追溯字段 (REQ 表案例支撑列/SWR 裁决理由的 lessons 引用), 运行时正文
  (SKILL.md 条款/代码注释) 用形态描述 ("构建期生成物"/"多语句 snippet")。
- 机器守卫: test_deproject_assets 的 PROJECT_TOKENS 扫描零新增命中
  (新增资产正文若带项目名必须同步扩守卫——本周期无新项目 token)。

## ② 设计偏见

- 是否把自身编排便利当 skill 义务: D-1/D-2 均为主代理收口所需的对账/可见性
  (非编排便利); 均为标注/warn 级不强制。
- 是否自动改写: 零自动改写——D-5 归位三选一交主代理裁决; D-2 重派交主代理;
  D-6 渲染修正为机械确定性规则 (承载终态是客观事实), 非猜测性改写。
- 修法层级: D-1/D-2 主代理执行偏差的机械防复发 (守卫), D-5/D-6 机制缺口
  (warn/修正), D-9/D-10/D-11 条款 (提示级)——全部落在正确层级, 无 agent
  行为偏差上升为硬义务。

## ③ 死代码

- D-2 的 signed_empty 读取依赖 validate 落盘形态 (reviewed_by+empty_domain_reason
  契约)——已有消费者 (validate 放行逻辑), 非新字段。
- D-7 matrix/ 前缀条目消费者 = hints 输出 → R2 假设生成装载 (v3.32 条款既有
  消费者)。
- D-8 path_signal 消费者 = fixminer 输出 → R2 修复驱动假设; per-commit 字段
  仅观测用, 若渲染器不消费则裁剪 (实现期核对)。
- D-1 conflicts 新 resolution 形态无既有渲染消费者——与 kept-first-multi-domain
  同容器, 主代理收口人工读 conflicts; 不为它建新渲染段 (无消费者不建)。

## ④ 过设计

- 无新门禁名: D-2/D-5 为 warn, D-3/D-4 为 r2_guard 工具面 error, D-1 为标注——
  六门禁 ①-⑧+③c/③d 判据零变化。
- 无新强制义务: D-9/D-10/D-11 为提示级条款; D-7/D-8 为提示通道增强。
- 义务三问逐项过 (见 SWR 各条)。
- 取证裁除已存在机制: 本周期零裁除案例——11 条全部取证确认缺口真实
  (与 v3.16 D-6 裁除形态对照)。

## 实现期重跑 (阶段 3 完成后填写)

- [ ] 代码注释/条款文本去项目化扫描 (test_deproject_assets 通过)
- [ ] 每个新函数消费者列明 (D-2 _domain_coverage_warn / D-3 _check_focus_sinks /
  D-4 mismatch / D-5 warn / D-6 终态检查 / D-7 refs / D-8 _path_score)
- [ ] 旧队列复跑 blocking=0 且 warn 增量有说明
- [ ] 版本守卫 ×22 全 3.33
