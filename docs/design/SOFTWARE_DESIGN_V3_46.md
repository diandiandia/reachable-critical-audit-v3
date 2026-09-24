# SOFTWARE_DESIGN_V3_46 — 函数级设计 + P 分层序列

## P1 机械小修（D-1）

**位置**：tools/batch_verify.py `_derive_attacker_tier`（关键词匹配段，实测
457-459 行附近）。

**设计**：
```
def _derive_attacker_tier(evidence_text):
    sentences = _split_sentences(evidence_text)   # 按 。.!?; 换行 切分
    hits = 0
    for s in sentences:
        if _is_disclaimer_sentence(s):            # 免责句式集匹配
            continue
        if any(k in s for k in REMOTE_KEYWORDS):  # 现有关键词表不变
            hits += 1
    if hits > 0:
        return "remote"
    if _any_disclaimer_present(sentences):
        return None                               # 全免责 → 交主代理
    return "non_remote"
```
- `_is_disclaimer_sentence`：匹配"非 remote / 不是 remote / 不构成 remote /
  无 remote / not remote / no remote / never remote / 非网络 / 不经网络 /
  不涉及网络"等形态（含英文小写化后匹配）。
- 返回 None 时调用处输出 warn：`attacker_tier 全免责句未推导，主代理裁决`。
- 调用处（tier 预填路径）对 None 的 fallback：**不写字段**（保持与"未推导"
  同态，让下游按缺省处理），warn 提示主代理。

**测试**：tests/test_v346.py 三形态 + K6/K7 fixture（免责句样本取自 lessons
条目原文，去项目化改写）。

## P2 结构修复（D-2、D-3）

**D-2 归一器扩展**（tools/batch_verify.py `_normalize_r4_payload`，实测 ~970）：
```
ALIASES = {
  "id": "hypothesis_id",
  "tracked_surfaces": "hypothesis_tracked_surfaces",
}
# 对象内键遍历时命中别名 → 键改名 + norm_flags.append(f"alias:{k}->{v}")
```
- 仅当目标键不存在时应用别名（canonical 键优先，防覆盖）。
- 前缀形态"hypothesis_tracked_surfaces"若以变体出现（如
  "hypothesis_tracked-surface"）不在本轮范围（K9 实测形态只含前两种别名；
  更宽泛前缀模糊匹配是过设计，留到出现再扩）。
- norm_flags 汇总在 r4-collect 输出一行 warn：`schema 归一 N 处（明细: ...）`。
- biz_hypothesis.md canonical 示例键名下加注："键名必须与示例逐字一致；
  仅 hypothesis_id / hypothesis_tracked_surfaces 为合法拼写"。

**D-3a workflow JS 预检**（src/workflow_export.py verify/refutation 导出段，
实测 225-232 / 269-272）：
- 生成 JS 头部加：
```
const taskFiles = (args.candidates||[]).flatMap(c => [c.taskFile,
  ...(c.refuters||[]).map(r=>r.taskFile)]).filter(Boolean);
const missing = [...new Set(taskFiles)].filter(f => !require('fs').existsSync(f));
if (missing.length) throw new Error('taskFile 不存在: ' + missing.join(', '));
```
- 内嵌任务书回退形态（payload 无 taskFile 字段）跳过预检。

**D-3b r4-collect 多文件报错**（tools/batch_verify.py 参数解析，实测 3396-3398）：
- 重复 `--file` 时：`Error: --file 重复指定（r4-collect 只接受一个合并
  findings 文件）: a.json, b.json` exit 1。

## P3 内容（D-4、D-5、D-6、D-7）

- **D-4**：surface_map_domain.md 在 trust_boundary 枚举说明后插入
  「config 门核条款」段落（原文 5-8 行）。
- **D-5**：新文件 assets/harness_manuals/kernel_zero_hardware_channels.md
  （四条通道 + 陷阱注记 + 来源 lessons 条目号）。
- **D-6**：`_tooling_version_warning`（实测 864-905）告警 append 处追加
  一句解释文本（见 SWR-V3.46-006）。
- **D-7**：workflow_export.py eligible 挑选处（实测 528-536 附近）加注释块
  （见 SWR-V3.46-007）。

## P4 版本链五件

1. workflow_export.py:22 TOOLING_VERSION "3.45"→"3.46"；
2. 版本守卫测试行：test_v310.py:115、test_v313.py:193、test_v332.py:92、
   test_v324.py:120、test_v312.py:181、test_v317.py:346（另 grep 遗漏者）——
   逐处 sed "3.45"→"3.46" 并核对上下文；
3. SKILL.md 增量段（SWR-V3.46-001..007 + 验收判据）；
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking VERSIONS 登记；
5. 资产计数守卫同步（若本周期增改资产条数，SKILL.md 附录与正文计数处同步）。
