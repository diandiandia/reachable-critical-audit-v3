# BIAS_EVAL_V3_11 — v3.10.2 + v3.11 过设计 / 设计偏见 / 死代码评估（2026-08-29）

> 评估对象：v3.10.2（13 项 Q-A~Q-M）+ v3.11（7 项 R-A~R-G）全部新增机制。
> 评估维度：过设计（机制超出需求/义务棘轮）、设计偏见（形态偏置/案例过拟合）、
> 死代码（定义无调用点/不可达分支）。修复随 P13 提交。

## 1. 过设计评估

| # | 发现 | 判定 | 处置 |
|---|---|---|---|
| O-1 | `_BUILD_MANIFESTS` 列 8 种生态清单但目录提取逻辑仅对 DEPS/.gclient 的「树内目录声明」形态有效——pom/gradle/cargo/go.mod/npm/pyproject 的依赖解析形态各异，统一提取是**伪能力** | 过设计 | ✅ 已修：三档裁剪（DEPS/.gclient 有效提取；其余清单降为存在性注记「未做目录级提取」） |
| O-2 | `stage_reopen` 用 `REOPEN_REASON` 环境变量传参——CLI 命令用环境变量传业务参数是接口形态瑕疵（手写 CLI 解析器的惯性） | 设计瑕疵 | ✅ 已修：`--reopen-reason` CLI 参数（env 兼容兜底） |
| O-3 | mirror_candidates 的语义域词集为**封闭双域**（image/message，从多媒体系批次提炼）——非图像/消息形态项目静默失效 | 过设计（封闭形态） | ✅ 已修：开放扩展注记（词集按需扩展，勿视为封闭全集） |
| O-4 | 渲染四标记/fidelity 前缀/journal anomaly——纯标注或 warn 级，判据不变 | 克制（不构成过设计） | 不改 |

## 2. 设计偏见评估

| # | 发现 | 判定 | 处置 |
|---|---|---|---|
| B-1 | PTM 4/7 + PAC 4/4 条目全部 mobile 系——触发案例全来自 Android 系审计，desktop/web/embedded_kernel 各仅 1 条 PTM | 平台偏见（案例过拟合的必然） | 记录待回填：设计文档已声明「首版条目来源」；desktop/web 契约条目待后续审计回填 |
| B-2 | attacker_tier 推导信号词「intent」为英文通用词**子串匹配**——`"intentional"` 被误判为 `same_device_cross_app`（实测复现） | 误匹配缺陷（非偏见） | ✅ 已修：`\bintent\b` 词边界 + 「intent extra/intent 参数/exported=/android:exported」具体形态 |
| B-3 | 推导信号词偏 Android 习语（导出组件/binder）——非 Android 项目零信号 → 返回 None 交主代理不机械兜底 | 反偏见设计正确 | 不改（None 交主代理是有意设计） |
| B-4 | `_under_audit_results` 子串匹配实现弱（任何含 `.audit_results` 子串的路径放行） | 弱实现（warn 级可接受） | 注记不改（warn 级提示不承载裁决） |
| B-5 | 契约库 PTM/PAC 条目中文书写、平台机制级描述、零项目 API 名 | 去项目化达标 | 不改（0 命中扫描通过） |

## 3. 死代码评估

| # | 发现 | 判定 | 处置 |
|---|---|---|---|
| D-1 | `write_scope_review` 定义后无任何调用点（唯一「引用」是提示文本）——CLI 不可达，主代理无法通过命令行触发 | 死代码 | ✅ 已修：新增 `--stage scope-review --dir <d> --decision reopen|keep [--reason <r>]` CLI 入口 |
| D-2 | 其余 9 个新符号（_tier_suffix/_derive_attacker_tier/_detect_journal_anomaly/stage_reopen/_under_audit_results/platform_api_contracts/_build_divergence/_BUILD_MANIFESTS）定义/引用计数 1:≥1 | 无死代码 | 不改 |
| D-3 | v3.11 mirror_candidates 第一版插在 `return merged` 之后成死代码（开发过程发现并修正） | 过程教训 | 已修（记录：多 return 函数插入新段必须先确认插入点在目标 return 之前） |
| D-4 | 新增测试 28 条（test_v3102 15 + test_v311 13）全部执行且全绿 | 无死测试 | 不改 |

## 4. 其他小瑕疵

| # | 发现 | 处置 |
|---|---|---|
| F-1 | `reopen_history[].reopened_at` 空字符串占位 | ✅ 已修：`datetime.now().isoformat()` 实际时间 |

## 5. 评估结论

- 过设计 3 处（全修）、设计瑕疵 1 处（全修）、误匹配缺陷 1 处（全修）、死代码 1 处（全修）；
- 偏见类 2 项记录待回填（mobile 平台偏重 + 域词集开放扩展——均为「案例过拟合的必然」，
  以声明+开放形态处理，不做过度修正）；
- 克制项 2 处（渲染标记/judgment 交主代理）确认不改——评估本身也遵守义务棘轮。
- 回归：修复后全量 301 passed（含 test_v3102/v311 全部断言）。
