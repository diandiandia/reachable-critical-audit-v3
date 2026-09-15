# REQ V3.45 — K1-K5 linux kernel 五批次复盘缺陷修复需求

> 输入: /root/linux/.audit_results/batch_K1..K5/lessons.md「对 skill 的教训」节
> (K1 7 条已由 v3.44 消化, 本周期 K2-K5 28 条 → 16 缺陷组 20 修复 1 裁除)。
> 取证: 全部编辑点已实测 (2026-09-15, dev 树 ffcbff0)。
> 版本: v3.45 (TOOLING 3.44 → 3.45)。

## 缺陷清单表

| # | 缺陷 (代码核实) | 修复 | 编辑点 (实测) |
|---|---|---|---|
| D-1 | domain_unmapped 计数按 surface.type 全等匹配, validate 无 type 枚举归一 — 全名 type ("network_endpoint") 漏计致 warn 恒触发 (K2-9) | merge 计数改前缀匹配; validate_surfaces 对非枚举 type 输出 warn | src/surface_mapper.py:931-936, validate_surfaces:629 |
| D-2 | r4-collect 对 hypothesis_id 缺失的 item 静默跳过 (docstring 声称告警无实现); item 级 `hypothesis` 键别名未处理 (K3-7) | 缺 id 输出 R4_ENUM_WARNING; `hypothesis` 键别名归一为 hypothesis_id | tools/batch_verify.py stage_r4_collect ~:1270 |
| D-3 | r35n-collect 对已有 resurrection_review 无条件跳过 — auto_bookkept 占位挡住 revived 真决策 (K5-11) | 占位标记 auto_bookkept; journal 真决策可覆写占位 | tools/batch_verify.py stage_r35n_collect ~:50, ~:88 |
| D-4 | hypotheses.json 裸数组形态致渲染器 .get() AttributeError → REPORT_MD_ERROR (K5-8) | 渲染器容错双形态 (dict/list); R2 落盘约定 dict | tools/batch_verify.py _render_appendix_b_process:2592 |
| D-5 | refuted-in-list 告警对已合规形态 (Low+[refuted]) 仍触发, 判据与合规形态不一致 (K4-13) | 合规 (severity=Low 且 title 标 [refuted]) 不告警 | tools/batch_verify.py _warn_r4_enums:1160-1164 |
| D-6 | target_profile empirical_modes 恒空 — static-only 判定不看交付物引导面 (K2-7) | 新增引导面探针 (树内 Image/vmlinuz/bzImage + 宿主 qemu/交叉编译器) → empirical_modes=["real-target"] | tools/target_profile.py:205 |
| D-7 | collect 对非 REACHABLE 的 claim_type 直接置 None, 声称分类丢失 (K2-8) | 归档 claim_self_reported (verifier 原值); claim_type 语义保持 SWR-V3.3.2-001 | tools/batch_verify.py:505-512 |
| D-8 | containment profile 派生缺省无一致性核查 — 内核上下文证据与 process_sandbox 矛盾静默入库 (K1-4, v3.44 漏网) | 派生值 × 证据内核上下文信号 (softirq/kthread/workqueue/中断) → warn | tools/batch_verify.py _derive_containment:403 |
| D-9 | biz_hypothesis.md 枚举明示未生效: claim_type 自造枚举两批再现 (K3-8/K4-12)、verdict 散文意图无映射 (K4-11)、新面桥接无指引 (K4-14) | 三条款: claim_type 非法值反例+映射表; verdict 常见散文意图→枚举映射; 清单外面发现先声明后由主代理桥接 | assets/task_templates/biz_hypothesis.md |
| D-10 | verifier 任务书缺三维度: 同一字段快照/活体读 (K2-4)、生命周期/提交期 GC 枚举 (K2-5, 服务 RECALL-002)、交付二进制证据面 (K3-10) | 步骤 0 增补三条 | tools/batch_verify.py 步骤 0 段 ~:3081 |
| D-11 | resurrect_prompt 无实证通道信号 (K2-10) 无 gap 行号容差明示 (K3-9) | 两条增补 | src/workflow_export.py resurrect_prompt:494 |
| D-12 | hypothesis_filter.md 无进度摘要指令 (K4-10: 7/7 停滞 vs 加指令零停滞对照) | 模板首部加进度摘要条款 | assets/task_templates/hypothesis_filter.md |
| D-13 | R2 假设生成派发无分片落盘条款 — 96KB 回复 API 断连一死一活对照 (K5-7) | SKILL.md R2 节派发条款 (提示级) | SKILL.md R2 假设生成段 |
| D-14 | 开题四步无工作区卫生检查 — 跨批次插桩遗留 (K4-15) | 四步 ① 前置卫生检查条目 | SKILL.md:238-244 |
| D-15 | 对抗枚举缺"新机制×旧机制组合窗口"维度 (K5-3: failfs 2026×LOOKUP_MOUNTPOINT 2020 = 唯一 REACHABLE) | 对抗枚举段增补一条 | SKILL.md:173-180 |
| D-16 | severity_override 通道存在但主代理未用, 裁决与机械渲染脱节 (K5-6) | R4/R6 节提示级条款 (severity 裁决走 override 通道) | SKILL.md R4/R6 段 |

## 裁除

| 项 | 理由 (取证) |
|---|---|
| K2-11 taskFile 相对路径 | workflow_export.py:603 `_tasks_dir = os.path.join(project_root, ...)` 已绝对路径 (K5 波次 payload 实测为绝对路径) — 已修 |
| K4-1 上游 master 比对 / K4-2 树内自证 / K5-1 R4 兜底 / K5-4 配置形态 / K5-10 抽核度量 / K5-12 实证分工 / K5-9 resume SOP / K2-12 journal label / K4-16 WebSearch 降级 | 已有机制/可推导/观察项 (阶段 0 评估已裁, 详见本周期复盘记录) |
| RECALL-001/003/004 | 目标形态不匹配 (JIT/浏览器/GPU 类, 非 kernel 周期缺口) |

## 测试守卫约束

- 每条 SWR 至少一测试用例 (含反面分支)
- 全量回归 (611 基线 + 新增) 全绿
- 旧队列复跑 (quickjs/servo/haproxy/gpac 代表队列) blocking=0, warn 与变更前一致
- signature_lib.py selfcheck 不回退

## 开发序列 (P 分层)

P1 (机械): D-1..D-8 → P3 (内容): D-9..D-16 → P2 结构并入 P1/P3 编辑点 → P4 版本链

## 验证命令

```bash
cd /root/reachable-critical-audit-v3
python3 -m pytest tests/ -x -q          # 全量
python3 -m pytest tests/test_v3_45.py -v  # 新守卫
bash install.sh                          # 安装 + 自带全量测试
```
