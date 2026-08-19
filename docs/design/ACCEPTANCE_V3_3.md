# Reachable Critical Audit v3.3 — 验收记录（Acceptance）

> 日期：2026-08-19。验收判据来源：`REQ_V3_3.md`（14 条）与 v3 验收惯例
> （三判据：无回退 + 新能力实证 + 新项目验收）。

## 判据 1: 全量测试无回退

- `pytest tests/`：**113 passed**（v3.2.3 基线 103 + v3.3 新增 10）
- R0 selfcheck 非 fixture 仓库：yyjson → `integrity OK: 19 signatures
  (lang/cwe/deproject/manual 对齐完备)`，exit 0
- 旧行为回归：Lua 审计队列/六门禁复跑不受影响（分类器/枚举均为加性变更；
  trust_boundary 旧文件照常 validate）

## 判据 2: 新能力实证（对应 REQ 逐条）

| REQ | 实证 |
|---|---|
| REQ-V3.3-001/002（L2 +4 族 / L3 +2 族） | 签名库 13→19；validate PASS；test_v33_c_l2_hits_only_c_surface：C 词族只命中 .c surface 不污染 .rs ✓ |
| REQ-V3.3-004（harness_manuals 对齐） | 对齐检查实现当天即抓出存量缺陷 cs↔csharp 命名不一致（load_manual("cs") 装载失败）——修复后 integrity 全绿 |
| REQ-V3.3-005（四值分类） | 纯库 Cargo.toml fixture → library；main+监听 → app；CMakeLists → infra；无信号 → app（保守）✓ |
| REQ-V3.3-006（maturity 解耦） | Lua → mature（git_tag:v5.5.1）；无标签+README 安全流程 → developing；无信号 → unknown ✓ |
| REQ-V3.3-008（host_api） | 关键词映射（"宿主公共 API 调用方传入"→host_api）+ validate 通过 ✓ |
| REQ-V3.3-012（先例 +2） | 先例库 22→24，两条均带 applications/source_lessons 追溯 ✓ |
| REQ-V3.3-013（追踪泛化） | tracking 重建 440 条含 v3~v3.3 全段；v3.2.2「已经完成开发」措辞归一化；状态源优先级修正（SWR 文档权威）✓ |

## 判据 3: 非 Web 新项目验收（REQ-V3.3-014）

**锚点项目: yyjson**（C JSON 库，未审计过，非 Web 形态）：

| 检查 | 结果 |
|---|---|
| R0 selfcheck（非 fixture 完整性） | PASS（19 签名 + manual 对齐） |
| context 四值分类 | `library`（signals: build_fw:package.swift + build_infra:cmakelists.txt + api_ratio:0.50）——分类器首轮实测暴露两处信号污染（misc/ 工具目录的 main、doxygen 产物 resize.js 的 bind( 误报）并当场修复：skip_dirs 扩 misc/example/bench/fuzz/doc 族 + 小库 1h+1c/header-only 形态纳入 api_ratio |
| 佐证器非空转 | C L2 词族（SIG-C-ALLOC-001）对 C surface 产生命中——v3.2.3 批次识别的"系统语言 0 hits 结构性空白"闭环 |

## 附带修复（验收过程中发现）

1. `_sample_source_files` skip_dirs 扩 misc/example/bench/fuzz/doc 族
   （yyjson 实测：misc/make_tables.c 与 doc/doxygen 产物污染 exec 信号）
2. `_public_api_ratio` 支持小库形态（1h+1c 与 header-only）
3. gen_tracking 状态源优先级修正（v3.2+ 段 SWR 文档权威覆盖 tracking 旧默认）
4. surface_mapper validate 存量 UnboundLocalError 根修（entry 文件不存在时
   suggested_all 未初始化）

## 结论

**三判据 PASS**：113 测试全绿 + 14 REQ 逐条实证 + yyjson 非 Web 新项目验收通过。

---

## v3.3.1 复评修正（2026-08-19，二轮偏见评估取证后）

二轮评估复核触发三项端到端修复——**L2 佐证器空转的另一半根因**：

1. **R1 产出无 lang 字段**：canonical schema（任务书 + SKILL.md）补 lang 必填——
   Lua 审计实测 31 surfaces lang 全部缺失（schema 从未要求）
2. **lang 形态无归一化**：真实流程 lang 是带点扩展名（".c"）或别名（ts/kt/sh），
   签名词表是裸名（c/typescript/kotlin/shell）——旧版直接字符串比较，
   L2 过滤静默全不命中。新增 signature_matcher.norm_lang + EXT_LANG_ALIAS
   （对齐 VALID_LANGS 词汇；与 batch_verify._EXT_LANG 的 csharp/javascript 词汇差异已注明），
   surface_mapper normalize 同步归一化
3. **C++ 词族补齐**：SIG-CPP-ALLOC-001（裸 new/new[]/容器无界增长，lang=cpp）
   + harness_manuals/cpp.md（对齐检查抓出）

验证：端到端实测安装版——`lang=".c"` surface → SIG-C-ALLOC-001 + SIG-PREALLOC-LEN-003
双命中（旧版静默 0 hits）。116 测试全绿（安装版 114+2 skip）。
