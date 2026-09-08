# SWR_V3.30

| 编号 | 需求 | 裁决理由 | 测试守卫 |
|---|---|---|---|
| SWR-V3.30-001 | paired_control_probe 模板:TEMPLATES 注册(langs:["any"])+argv 契约(双命令+timeout/interval/threshold)+进程树峰值采样(shell+后代)+三态判定(PAIRED_CONFIRMED/NO_SIGNIFICANT_DIFF/CONTROL_FAILED) | D-1;采样进程树是 shell=True 形态的必要修正(子进程漏采样实测) | test_v330 8 用例(注册/argv/去项目化/双态判定/对照失败/枚举) |
