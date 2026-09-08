# SOFTWARE_DESIGN_V3.32
P1:
- tools/fixminer.py: `python3 tools/fixminer.py <project> [--since N]`
  ①git rev-parse 失败 → {"status":"NO_GIT"} exit 0
  ②git log --since=N 安全关键词(security|CVE|overflow|out-of-bounds|use-after-free|
  inject|XSS|escape|deserialize|validate|bounds|crash|DoS|leak|permission|auth|
  sanitize|traversal) vs 通用 fix 词(typo|style|refactor|doc|test|ci|format|comment|
  cleanup|nit)分级——security 词净分>0 才入选(同 §1.4.5 分级纪律)
  ③输出 {"fix_commits":[{"hash","subject","files","family"}...], "families":{族:计数}}
  family 由 subject+files 命中 _CWE_FAMILY 关键词映射(账本族名)
- language_issue_matrix.py hints: 增 --kind application|library|hybrid 可选参;
  library/hybrid → MEMORY-SAFETY/RESOURCE-DOS/STATE/RACE/NUMERIC 档+1;
  application → INJECTION/WEB/AUTHN/DATA-INTEGRITY 档+1(重排只影响 inventory 序);
  输出增 lessons_refs: lessons/*.md 文件名含 lang 或首 60 行含族名 → 文件路径列表
- batch_verify r35-collect: 结果 dict 增 strengthened_notes(cand_id→strengthened 列表)
  + sibling_advisory 文本(机制静态确证者主代理裁决立候选, SWR-V3.19-003)
P3: SKILL.md R2 段增对抗枚举条款 + 修复驱动条款(提示级, 引用 fixminer)
P4: TOOLING 3.32 + 守卫 ×22 + 增量段 + tracking + gen_tracking
test_v332: 每 SWR ≥1 用例含反面分支。
