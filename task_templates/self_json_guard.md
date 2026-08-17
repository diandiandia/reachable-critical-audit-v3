# 输出 JSON 自查（所有子智能体任务书尾部强制附加）

提交前必须通过本地校验:
```
python3 -c "import json,sys; json.load(sys.stdin)" <<'JSON'
<你的输出>
JSON
```
- evidence/字符串中禁止出现裸反斜杠（转义为 \\）
- 校验失败不得提交，修正后重试
