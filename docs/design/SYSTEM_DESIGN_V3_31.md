# SYSTEM_DESIGN_V3.31
边界不变式：阶段骨架/六门禁①-⑧判据语义不变（①b 为 ① 的条件子检查，同 ③c/③d 形态）；
队列数据模型主体不变；裁决层零改动。
影响面：evidence_ledger.py（①b 检查+参数）、language_issue_matrix.py（hints 命令）、
lessons_recorder.py（落盘路径）、tools/batch_verify.py（equivalent warn）、SKILL.md
（门禁代码块/R4 触发/R2 条款/四轴表）、版本链六件。
兼容性：旧队列复跑 assert_ledger 不传 r2_filter → ①b skip_note，零新增告警；
collect 新 warn 仅对 equivalent 档 REACHABLE 触发（QuickJS 队列无此形态）。
