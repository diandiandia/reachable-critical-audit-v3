# REQ_V3_43 — 机制冻结实验 + 知识补种 + 架构体检

版本: v3.43 | 来源: 用户架构评估裁定（2026-09-13）——「加功能边际收益递减，正确动作不是重设计而是把节奏从每项目一版本降为知识驱动、机制冻结」

## 周期定位（特殊性）

本周期**零审计骨架机制改动**（R0-R6 阶段/六门禁判据/队列数据模型冻结）——
这是冻结实验的主体约束。允许改动：知识资产（矩阵/清单/先例数据）、
任务书文本（提示级内容条款）、skill-optimizer 侧纪律与文档。
验证假设：知识补种能带来发现力提升（kernel 类目标 hitrate 改善）即证明
「机制稳定、知识驱动」分层正确。

## 需求清单

| # | 需求 | 归属 | 层级 | 案例支撑 |
|---|---|---|---|---|
| K-1 | c 语言矩阵补种 TRUST-BOUNDARY 族（PAGE-CACHE-OWNERSHIP 形态：零拷贝/in-place 优化对 splice 植入页/skb fragment/scatterlist 外部支撑内存的写——锚点原语 splice/vmsplice/pipe_buffer/skb frag/page ownership；判定要点：外部支撑页 in-place 写 = 越权写） | reachable-critical-audit 矩阵资产 | 知识（external_seeded） | 2026 年 9+ CVE 共性根因（Copy Fail 31431/Dirty Frag 43284+43500/Fragnesia 46300/Dirty Decrypt 31635/PinTheft 43494/DirtyClone 43503/pedit COW 46331），Dirty Pipe 2022-0847 家族三代 |
| K-2 | java 矩阵补种 Keycloak hitrate 未种格条目（CWE-117 日志注入 / CWE-290 认证欺骗 / CWE-367 TOCTOU / CWE-362 竞态窗口 / CWE-613 会话过期 / CWE-294 重放 / CWE-476 空指针 / CWE-704 类型混淆 / CWE-789 无界分配 / CWE-303 撤销策略未生效） | 矩阵资产 | 知识（battle_verified） | Keycloak 审计 hitrate 7/18，10 格未种（过程观察 7） |
| K-3 | SKILL.md H7 检测要点补「鉴权谓词逻辑错误」形态（谓词条件写错/比较对象错位——非弱化，ptrace_may_access 潜伏 10 年形态） | SKILL.md H7 段 | 内容提示级 | CVE-2026-46333（2016 引入，Qualys 4 条利用链） |
| K-4 | SKILL.md fixminer 条款补跨多年窗口提示（同形态 CVE 间隔 >1 年：Dirty Pipe 2022 → Copy Fail 2026，默认 --since 12 天窗口挖不到 ground truth；族信号驱动需长窗口或手工指定） | SKILL.md R2 修复驱动段 | 内容提示级 | 2026 页缓存族 9 CVE 与 2022 Dirty Pipe 的修复族关系 |
| K-5 | biz_hypothesis.md H3 段补 kernel 锚点示例（任务退出竞态/timer 回调/调度器状态复用——提示级，降低检测要点与目标形态的翻译损耗） | R4 任务书模板 | 内容提示级 | 2025 年 6 个 UAF（Chronomaly 38352/io_uring 40047/HFSC 38001/vkms 22097/CBS 38350/AF_UNIX 13350）与 H3 检测要点的对应验证 |
| S-1 | skill-optimizer 义务三问补第四问：「该知识是否已在主代理可推导的范围内」——可推导知识默认不入库（入库是为了节省推导成本，需权衡而非默认） | skill-optimizer SKILL.md 纪律段 | 纪律 | v3.42 D-6 前缀级联类知识的入库成本反思 |
| S-2 | skill-optimizer 补「架构重设计触发判据」段：五信号（修复互相冲突/特例化/门禁失效/知识复用归零/兼容债务）任一出现才启动重设计 | skill-optimizer SKILL.md 新段 | 文档 | 用户架构评估裁定 |
| S-3 | reachable-critical-audit R6 lessons 补提示级义务：每轮审计收官记录「本轮实际被装载/消费的 SKILL.md 条款清单」（无门禁承载，提示级——为条款消费度量积累数据，两周期后批量裁除死条款） | SKILL.md R6 段 | 内容提示级 | SKILL.md 条款密度与遵守率负相关矛盾（用户关切） |

## 测试守卫约束

- K-1/K-2: 矩阵 cells/inventory 断言（新族/条目在位 + hitrate 改善可断言——用公开 CVE 的 CWE 查询做发现力对照）
- K-3/K-4: SKILL.md 文本守卫（关键句在位）
- K-5: biz_hypothesis.md 文本守卫
- S-1/S-2: skill-optimizer SKILL.md 文本守卫
- S-3: SKILL.md R6 段文本守卫
- 机制冻结守卫：本周期无 src/tools 判定逻辑改动（除版本链机械步）——tests/test_v343.py 断言 diff 范围

## 开发序列

1. K-1/K-2: 矩阵 seed（seed_entries 双通道）
2. K-3/K-4/K-5/S-3: SKILL.md + 任务书模板文本
3. S-1/S-2: skill-optimizer SKILL.md
4. P4: 版本链五件（TOOLING 3.43）
5. 测试: tests/test_v343.py + 全量回归 + 旧队列复跑

## 验证命令

```bash
cd /root/reachable-critical-audit-v3 && python3 -m pytest tests/test_v343.py -x -q
python3 -m pytest tests/ -x -q
python3 tools/batch_verify.py /root/haproxy --stage assert --require_target_kind=False --require_resurrection=False
# 发现力对照（机制冻结实验判据）:
python3 src/language_issue_matrix.py hitrate c CWE-787,CWE-290  # 页缓存族 CWE 查询应命中新族
```
