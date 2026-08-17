# R5 实证抽验执行说明（harness）

## 采样协议（SWR-V3-042/043）
1. 启动目标进程并记录基线 VmRSS/存活状态
2. 发送攻击载荷
3. 每秒读 /proc/<pid>/status VmRSS + kill -0 存活检查，持续 ≥30s 或直至进程退出
4. **投递速率确认**: 先以慢速采样确认服务器实测到达量随发送增长
   （沙箱代理可能限流——以服务器实测到达量为准，不以客户端发送量为准）
5. 记录环境: 工具链版本/依赖/端口/限流备注（harness_runner.py env 可采集）

## harness 模板: {template}（{attack}）
脚本: {script}
判据: {judgement}

## 结果写回
confirmed → evidence_grade=empirically_confirmed；
refuted → correction_record + 候选降级 + superseded_by 标记（REQ-V3-051 闭环）


---

## 输出自查（强制，SWR-V3-085）
提交前必须用 `python3 -c "import json,sys; json.load(sys.stdin)"` 校验你的 JSON 输出；evidence/字符串中禁止出现裸反斜杠（转义为 \\\\）。
