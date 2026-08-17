# v3.1 Phase 3.1.3 验收报告（三项目复跑对照）

> **日期**：2026-08-17
> **验收判据**（REQ-V3.1-100）：① R3.5 拦截率较战役基线下降 ② 原 REACHABLE 结论零丢失 ③ 六门禁全 PASS
> **方法**：三项目候选队列重置（保留原假设/锚点/摘要，剥离原裁决）→ v3.1 verifier（步骤 0
> 承重前提 + 家族清单注入 + 自证伪提示）Mode W 复跑 → 机械分级复核 → v3.1 R3.5 证伪波
> （工具箱注入 + strengthened 结构化）→ 主代理裁决 → 六门禁。
> 各项目验收记录：`<project>/.audit_results/_phase313/acceptance.json`

## 结果总表

| 项目 | ① 拦截率 | ② 零丢失 | ③ 六门禁 | 结论 |
|---|---|---|---|---|
| akka-http | **75% → 0%** ✅ | CAND-004 保留 ✅（+2 补强） | PASS | ✅ |
| etcd | **66.7% → 20.0%** ✅ | {002,010} 保留 ✅（+3 升级） | PASS | ✅ |
| actix-web | **66.7% → 0%** ✅ | CAND-006 保留 ✅（+1 恢复） | PASS | ✅ |

**三判据全部满足 → Phase 3.1.3 验收 PASS。**

## 判据 ① 详析：拦截率下降的两条路径

1. **R3 自拦截（akka 型）**：基线被 R3.5 事后证伪的前提类假阳性，被 v3.1 verifier 在 R3 阶段
   自行拦截——akka 3/3（CAND-001 双层守卫 8 维矩阵、CAND-003 WS 流式前提断裂、CAND-008
   Host↔authority 一致性封口）、actix CAND-009（Host 采信族裁决树在 R3 即应用，直接判
   NEEDS_REVIEW——与基线主代理裁定结论一致）。
2. **claim 精化（etcd 型）**：基线降级针对旧 claim 的维度，v3.1 verifier 重新推导出更准确的
   claim 并经证伪者确认——CAND-003（`\x00` 区间字面 vs open-ended 语义分歧，e2e 实机实证）、
   CAND-004（syncWatchers 全量物化 O(R²/1000) + 读写全停）、CAND-005（quota=DoS 转换点）、
   actix CAND-005（WS 输入缓冲无界：检查在整帧缓冲后执行，实测 200MB→RSS+200MB，
   u64::MAX-100 绕过溢出检查）。

## 判据 ② 详析：零丢失 + 净增益

- 三项目基线最终 REACHABLE 共 4 个（akka 1 / etcd 2 / actix 1）——**全部保留**。
- 净增益 4 个 REACHABLE（etcd 3 升级 + actix 1 恢复），全部经 0/2 证伪存活且带证伪者补强。
- 证伪者 correction 修正了 3 处 verifier 归因（actix Dispatcher 死代码路径、etcd 幽灵边、
  行号漂移）——全部不影响结论，归因更正落盘。

## 判据 ③ 详析：六门禁（含验收中修复的 2 个 gate 缺陷）

| 门禁 | 三项目 |
|---|---|
| ① no_pending | 10/10 VERIFIED × 3 |
| ② REACHABLE 无 static_only | 机械分级复核后全过（etcd CAND-005 用证伪者逐边验证转录补边） |
| ③ 实证类 100%（含 R4） | 通过；**验收修复 gate ③b 缺陷 ×2**：source_fact 哨兵/算术类豁免未实现；reviewed_clean 的 Info 正向条目被误伤 |
| ④ H1-H7 全 VERIFIED | 基线 R4 装载 + status 补记后全过 |
| ⑤ 对账零差异 | dispatched 全终态 |
| ⑥ escalated=0 | 0 |
| ⑦ surface 覆盖 100% | 三项目全覆盖 |

## 验收发现并已修复的 v3.1 缺陷（验收的价值证明）

1. **gate ③b source_fact 豁免缺失**：与 §17.7/§21.4 源事实级规则矛盾 → 已修复
2. **gate ③b 作用域错误**：误伤 reviewed_clean 正向确认条目 → 已限定 confirmed 假说
3. **CK-UNBOUNDED-HOPS 绑定关键词缺口**：etcd CAND-004 类"缓冲上限"表述未命中"无上限/无界/累积"
   → 关键词补"上限/缓冲"（etcd 复跑按原绑定完成，缺口记录为迭代项）
4. **verifier 自我分级过低模式**：akka CAND-004 / etcd CAND-002 有完整边证据却自标 static_only
   → 机械分级复核已兜底；verifier 任务书补充"分级是证据的机械函数"说明（待回填 lessons）

## 结论

v3.1 三判据全部满足。合并 main + install 的条件成立（REQ-V3.1-101）。
验收过程中暴露的 4 个缺陷已全部修复或记录迭代项——验收不仅验证了设计主张
（拦截率下降 66.7-75% → 0-20%），还产出了 4 个净增 REACHABLE 发现。
