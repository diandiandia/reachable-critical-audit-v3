# SOFTWARE_DESIGN_V3.27 — 引擎形态知识基座补种

## P 分层序列

```
P3 内容：矩阵两格三条目 + 清单 CK-LIMIT-BYPASS-ENUM + 模板惯例段
P4 版本链：TOOLING 3.27 + 守卫 ×17 + SKILL.md 增量段/计数 + tracking + gen_tracking
```

## P3-1：矩阵补种（SWR-V3.27-001/002/003）

`resources/language_issue_matrix.json`：

- C×RESOURCE-DOS 格 patterns 追加：
  `"资源门禁强制点=计数分配器包装层: 裸 malloc/mmap/第三方分配器站点逐一枚举——限额类缺陷的旁路族"`
- C×RESOURCE-DOS 格 pitfalls 追加：
  `"子执行上下文 (worker/线程/子 rt) 的资源参数继承矩阵逐项核对; 哨兵值 (0/-1/非法) 语义 fail-open 还是 fail-closed"`
- C×MEMORY-SAFETY 格 pitfalls 追加：
  `"序列化/反序列化读取器的尺寸计算必须 size_t 且逐项溢出检查; 计数 ≤ 剩余输入/单元素最小占用——int 算术回绕 = 小分配大写入"`
- 两格 source_lessons 各追加 `"quickjs lessons 2026-09-07"`（追溯字段）

## P3-2：清单新条目（SWR-V3.27-004）

```json
{
 "id": "CK-LIMIT-BYPASS-ENUM",
 "name": "限额/配额旁路枚举",
 "family": "resource-dos",
 "binding": {
  "cwe": ["CWE-770", "CWE-789"],
  "keywords": ["限额", "memory limit", "配额", "quota", "malloc_limit",
               "memory_limit", "计数分配", "unaccounted"],
  "note": "结构化绑定规则 (v3.1): cwe 并集匹配 或 keywords 任一命中候选文本"
 },
 "applies_to": ["verifier", "refuter"],
 "steps": [
  "目标资源的门禁/限额机制（内存/线程/连接）的强制点在哪里——是否经统一计数包装层？",
  "全树裸分配站点逐一枚举（malloc/calloc/realloc/mmap/第三方分配器）——每个站点是否记账、是否查限？",
  "子执行上下文（worker/线程/子进程/子 runtime）的资源参数是否继承父上下文限额？",
  "限额的哨兵值语义（0/-1/非法值）是 fail-open 还是 fail-closed？",
  "累积型资源（队列/缓存）的入队点是否有总量检查——检查点与累积点的先后？"
 ],
 "source_lessons": ["quickjs lessons 2026-09-07 (worker 子 rt/SAB backing/消息队列三站点 + 哨兵 fail-open 实录)"]
}
```

关键词纪律（v3.12/v3.13 延续）：CJK 词（限额/配额/计数分配）子串语义；
ASCII 全部多词短语或标识符形态（memory limit/quota/malloc_limit/memory_limit/
unaccounted），禁裸词（如 "limit" 单独成词会误配大量候选）。

## P3-3：任务书惯例段（SWR-V3.27-005）

`task_templates/biz_hypothesis.md` 输出形态节后追加：

```
## 正向确认条目惯例（v3.27, SWR-V3.27-005）
防御核实类/检测点复核 clean 类条目按此书写：severity 一律 low、
claim_type 仅枚举值（crash|panic|oom|unbounded|xss|protocol_dos|rce|leak|
other|null——缺枚举值置 null，禁止自造如 default_reachability 形态）、
evidence 注明"核实结论：<防御机制 file:line>"。该类条目由主代理标
positive_confirmation 后不进问题清单（v3.7 正向确认自动排除）。
```

## P4：版本链六件

1. workflow_export.py:22 TOOLING_VERSION "3.26"→"3.27"
2. 守卫 ×17 同步（test_v310/312/313/314/315/316/317/318/319/320/3210/322/
   323/324/325/326/39 + test_v327 自带 "3.27" → 守卫数 18）
3. SKILL.md 追加 `## 🆕 v3.27 增量` 段（列 SWR + 验收判据 + "TOOLING 3.27"）
4. SKILL.md 资产地图清单计数 44→45（附录行 + 正文节 v3.12/v3.13 提及处同步）
5. docs/design/REQUIREMENTS_TRACKING.md 手工追加 V3.27 段（禁 gen_tracking 再生成）
6. tools/gen_tracking.py VERSIONS 登记 ("V3.27", REQ_V3_27, SWR_V3_27)

## 测试设计：test_v327.py（新文件）

- test_matrix_seeded_patterns（SWR-001/002/003）：`language_issue_matrix.cells c`
  输出含三条新串；反面分支=其他语言格不含（零注入语义保持）
- test_ck_limit_bypass_enum（SWR-004）：条目结构完整（id/name/family/binding/
  applies_to/steps/source_lessons）+ id 唯一 + steps≥4 + 零项目名断言
- test_asset_count_45（SWR-004 计数联动）：清单库 45 + SKILL.md 正文节计数同步
- test_biz_template_convention（SWR-005）：模板含惯例段文本 + claim_type 枚举串
- test_tooling_version_guard：TOOLING_VERSION == "3.27"
