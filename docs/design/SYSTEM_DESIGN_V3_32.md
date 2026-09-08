# SYSTEM_DESIGN_V3.32
边界不变式：流水线/六门禁判据/队列数据模型/裁决层零改动。
影响面：新工具 tools/fixminer.py；language_issue_matrix.py hints 扩展(可选参数向后兼容)；
tools/batch_verify.py r35-collect 结果回显；SKILL.md R2 条款+增量段；版本链。
兼容性：hints 无参行为不变；r35-collect 结果增字段不影响既有消费(JSON 增键)。
