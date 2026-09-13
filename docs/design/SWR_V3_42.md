# SWR_V3_42 — 六缺陷 SWR 条目

每条含裁决理由 + 测试守卫。全部修法形态纪律：提示级/判定健壮化优先，禁止自动改写，已存在机制不重造。

## SWR-V3.42-001（D-1 refutation 资格判定健壮化）

- 裁决：`workflow_export.py` refutation 资格判定从「`"refutation" not in c`」改为
  「`not _has_refutation_result(c)`」——`_has_refutation_result` 判定
  `refutation` 为 dict 且含 `votes` 或 `summary` 键。空 dict / 仅签收字段
  （strengthened_verified_by/attribution_correction_verified_by）视为未复核。
- 理由：主代理签收脚本对全队列 `setdefault('refutation',{})` 是常见操作形态
  （本次审计实录），键存在语义使资格判定把未复核候选静默排除，且空转输出
  只报 qualified_total=0 无诊断——两次导出空转 + 手工清理 12 个空 dict 的
  修复成本远大于判定健壮化。
- 附带：空转（qualified 为空且存在带 refutation 键但无票数的候选）时
  advisory 追加 `empty_refutation_keys: [id...]` 提示。
- 测试守卫：tests/test_v342.py::test_refutation_empty_dict_eligible /
  ::test_refutation_sigonly_eligible / ::test_refutation_with_votes_excluded /
  ::test_refutation_advisory_lists_empty_keys。

## SWR-V3.42-002（D-2 r4-collect 近似键诊断）

- 裁决：R4_COLLECT_WARNING 的 diagnosis 追加近似键扫描——顶层条目含
  `hypothesis`/`hypothesisId`/`hypID` 等键但无 `hypothesis_id` 时，输出
  `字段名提示: 检测到近似键 X，预期 hypothesis_id`。仅提示不改写。
- 理由：本次 H1/H2 两文件两次 collect 零提取，diagnosis 只报键清单，
  主代理需手工读文件定位字段名差异；映射提示一步到位且零风险（提示级）。
- 测试守卫：tests/test_v342.py::test_r4_collect_fieldname_hint。

## SWR-V3.42-003（D-3 verifier 分支级声称提示）

- 裁决：verifier 任务书「步骤 0 承重前提验证」段追加提示级义务：
  「证据中的分支级声称（isAbsolute/fallback/else-branch/条件分支行为）须
  标注为待实证子断言，不得作为结论性证据——门禁与复核均基于同一源码，
  只有部署布局实证能拦截此类误差（Keycloak CAND-010 isAbsolute 子断言被
  real-target 证伪实录）」。
- 理由：edge_proven 判定的子断言级误差在本次审计被 real-target 实证
  暴露（verifier 声称绝对路径旁路，实测校验期 containment 拦截，真实缺口
  在 CWD 回退分支）。提示级不加重义务，但让 verifier 与主代理对分支级
  断言保留实证意识。
- 测试守卫：tests/test_v342.py::test_verifier_prompt_branch_claim_hint。

## SWR-V3.42-004（D-4 upstream 已修声称树内核实）

- 裁决：SKILL.md「公开面关联检索（v3.38 SWR-V3.38-003）」段追加：
  「upstream『已修复/已包含』结论必须附树内 commit 佐证（git log -S /
  merge-base --is-ancestor），无法佐证时按未修复处理——版本号声称与树内
  事实不符是时间差发现的直接来源（CVE-2026-1180 公开声称已修而 nightly
  main 无修复痕迹实录）」。
- 理由：本次 H-4-F1 High 发现完全依赖该对账（若按公开信息「已修」处理
  则整条漏报）。
- 测试守卫：tests/test_v342.py::test_skillmd_upstream_verify_hint。

## SWR-V3.42-005（D-5 filter drop 判据补维度）

- 裁决：hypothesis_filter.md 排除判据段追加提示：「『无权限提升』方向的
  drop 前，必须核对信息暴露（枚举 oracle/存在性判定）与跨信任域完整性
  （第三方信任域消费合成事件/数据）两个维度——R2 filter 与 R4 假说的
  判据差集是真实发现空间（emitEvent 弱门被 filter drop 后 R4 从用户
  oracle 维度重发现为 High 实录）」。
- 理由：filter 判据侧重权限提升，R4 判据覆盖信息暴露——两个维度差集
  使同一事实在 R2 被 drop、在 R4 成为 High finding。R4 通道补盲是兜底，
  但 filter 侧补维度可减少依赖兜底。
- 测试守卫：tests/test_v342.py::test_filter_template_drop_dimension_hint。

## SWR-V3.42-006（D-6 前缀级联提示）

- 裁决：SKILL.md「实证回填规范」段追加：「回填前缀语义：CONFIRMED 前缀
  触发 ③d independent_review 要求（无 independent_review/r3_link 即
  违规）；机制级静态确证写 SOURCE_FACT 前缀（has_confirmed 判定包含
  source_fact 关键词）。回填前预判 gate 链级联——本次审计 CONFIRMED
  回填后 ③d 违规、补 independent_review 才过门禁的实录」。
- 理由：gate ③b/③d 的级联触发关系散落在两处条款，主代理回填时需
  试错才能掌握；一条提示即可消除。
- 测试守卫：tests/test_v342.py::test_skillmd_prefix_cascade_hint。

## 裁除记录（本次评估已裁，不做）

- SAML broker 实证链设计（SAML 协议特定，泛化性弱，留项目轨迹）
- pkill 自匹配陷阱（执行层通用陷阱，非 skill 义务）
- 矩阵补种 10 格（v3.42 内容工作队列，独立于缺陷修复）
