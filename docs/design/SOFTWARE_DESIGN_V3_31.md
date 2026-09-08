# SOFTWARE_DESIGN_V3.31
P1 机械：D-1 assert_ledger 增参 r2_filter（dict: keep/bc/total/spot_checked）——条件成立且
len(spot_checked)<3 → violations 增 {"gate":"keep0_spotcheck"}；SKILL.md 门禁代码块读
r2_filter_result.json 传参。D-5 batch_verify collect 循环：fidelity==equivalent 且
empirical 无 ownership_model → warnings.append（SWR-V3.31-005 同款句式）。
P2 结构：D-2 hints 命令（cells_for+inventory_for 合并 json）；D-3 write_lesson 目标改
project_root/.audit_results/lessons.md（os.makedirs 前置；机械段+过程段全量重渲染幂等）。
P3 内容：D-4 SKILL.md 两处触发条款；D-6 四轴职责表+通道边界条款；R2 条款改引 hints。
P4 版本链：TOOLING 3.31+守卫×21+增量段+tracking+gen_tracking。
test_v331：6 SWR 各 ≥1 用例含反面分支。
