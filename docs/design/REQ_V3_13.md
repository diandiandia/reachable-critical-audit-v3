# REQ_V3_13 — 系统需求（v3.13 错误路径处理族 + 数值语义族 + 账本锚点一致性修复）

> 对应设计文档：SYSTEM_DESIGN_V3_13.md。需求编号 REQ-V3.13-xxx。
> 每条含：语义 / 触发条件 / 消费者 / 案例支撑（三问已过，见设计文档 §3）。
> 本版不改变阶段骨架、六门禁判据语义、队列数据模型。
> 评估：BIAS_EVAL_V3_13.md（含 H-0 自纠条目）。

## 1. 覆盖账本层

### REQ-V3.13-001 覆盖账本族扩展与锚定修正
- **语义**：issue_coverage_matrix `families` 新增两族——`NUMERIC`
  {191 整数下溢, 369 除零, 681 转换精度, 697 不一致比较} 与 `ERROR-HANDLING`
  {457 未初始化, 665 初始化不完整}，`rows` 各加空行。**锚定修正**：WEB cwe 补
  436/444（清单 CK-DUAL-PARSER/CK-HOST-AUTH-CONSISTENCY 与 PREC host-family 族
  已锚定，账本未锚的漂移）；RESOURCE-DOS cwe 补 1333（CK-RUNTIME-RE 与
  PREC-RUNTIME-VERSION-001 已锚定）。190/129 不重归（MEMORY-SAFETY 既有锁）。
  CWE→族映射数据驱动（fam_map），零代码改动。
- **触发条件**：聚合/缺口读取时（恒）。
- **消费者**：批次选题缺口格、报告 B.6 覆盖账本、`_ledger_pressure` 压力提示。
- **案例支撑**：191/369/681/697/457/665 全库零族锚点（前瞻性缺口）；436/444/1333
  的清单/PREC 层已锚而账本未锚是实测漂移——aiohttp CAND-002（CWE-436）
  NEEDS_REVIEW 为真实受影响案例。

## 2. 分级层

### REQ-V3.13-002 严重程度映射扩展
- **语义**：SEVERITY_BY_CWE 补 9 码——191→严重（与 190 整数溢出对称）、
  369→高（除零 crash 类）、457→高（未初始化流入 free 致 SIGABRT 实证档）、
  444→高（请求走私）、1333→高（RESOURCE-DOS 全族 high 先例）、
  681/697/665/436→中（转换截断/不一致比较/初始化不完整/双解析器前提=逻辑缺陷
  默认档）。override 优先级与 claim_type 回退链语义不变。SKILL.md 严重度表同步。
- **触发条件**：`severity_for` cwe 命中（恒按表）。
- **消费者**：报告问题清单分组排序、R4 申报归一化参照。
- **案例支撑**：191↔190 对称（RFCOMM 下溢实证档）；369 除零 media3 实证 CONFIRMED；
  457 未初始化→free(garbage) SIGABRT zookeeper 实证 CONFIRMED；1333 ReDoS 族先例；
  436 双解析器前提依赖外部组件（aiohttp CAND-002 blocking_point 实证）。

## 3. 知识资产层

### REQ-V3.13-003 数值语义族检查清单（2 条）
- **语义**：checklist_library 新增 numeric-semantics 族：
  - **CK-NUMERIC-TRUNCATION**（CWE-191/681 锚定）：截断/窄化先于范围检查（检查
    死代码形态）、长度/计数算术回绕落入检查通过区间（len+4 类）、上游哨兵值
    参与算术的取值域（MaxUint32/-1/0）。
  - **CK-NUMERIC-SEMANTICS**（CWE-369/697 锚定）：除零路径（零宽字段/零尺寸
    输入驱动除数）、比较方向/类型不一致（有符号 vs 无符号、截断后比较）、计数与
    偏移算术的取模边界。
- **绑定规则**：cwe 并集 OR keywords 任一命中；keywords CJK 主导 + 多词 ASCII
  短语（integer overflow/wraparound/truncation/divide by zero/inconsistent
  comparison）；无裸 ASCII 单词。
- **触发条件**：候选 cwe 命中 191/681/369/697 或 keywords 命中。
- **消费者**：verifier/refuter 任务书 `_checklist_section`（既有管线零代码改动）。
- **案例支撑**：libvpx CAND-001 CWE-681 REACHABLE（截断死代码，实证队列记录）、
  RFCOMM CWE-191 下溢 empirically_confirmed（SKILL_LESSONS_common.md）、
  mixed-fixture GT-2 len+4 回绕（SKILL_LESSONS_mixed-fixture.md）、media3 H-2
  除零 CONFIRMED（实证队列记录）、W6 §19.7（MAX_VALUE/-1/0 三值红旗）与
  §21.3（哨兵值语义）。

### REQ-V3.13-004 错误路径处理族检查清单（2 条）
- **语义**：checklist_library 新增 error-handling 族：
  - **CK-ERROR-BRANCH**（无 CWE 锚定——跨族语义，关键词绑定为主）：错误分支
    条件反转（if err==nil 内处理错误分支=死代码形态）、错误分支被静默阻断、
    异常吞没后转正常路径继续。
  - **CK-ERROR-CLEANUP**（CWE-457/665 锚定）：失败/截断路径残留未初始化状态被
    下游消费、错误路径清理完整性（free 后未置 NULL/部分初始化/提前返回跳过清理）、
    宿主复用后状态残留。
- **关键词纪律**：禁裸「异常」（CJK 子串 ⊂ 异常处理 → 与 CK-SIBLING-LISTENERS
  机械共绑膨胀），用「异常路径」；禁裸 error/cleanup（词边界不拦下划线 →
  error_handler 误配），用 error path/failure path 多词短语。
- **触发条件**：候选 cwe 命中 457/665 或 keywords 命中。
- **消费者**：verifier/refuter 任务书 `_checklist_section`。
- **案例支撑**：zookeeper 截断帧→未初始化栈结构→free(garbage) SIGABRT CONFIRMED
  （实证队列记录 CWE-125/457/787）；W6 §25.3 明示「缓存层条件反转写反=死代码
  列为 CK 检查项」从未制度化——本版落实；W6 §13.5 异常路径描述必须实证抽验；
  Pillow H3 错误路径族候选（维度浮现候选、实证证伪后如实归档——诚实框架）。

### REQ-V3.13-005 版本链
- **语义**：TOOLING_VERSION → "3.13"；SKILL.md v3.13 增量段 + 资产地图计数
  （38 清单）+ 严重度表 9 码；gen_tracking VERSIONS 登记 + REQUIREMENTS_TRACKING
  手工追加段（禁止 gen_tracking 再生成）；既有守卫 6 处更新；新增 tests/test_v313.py。
- **触发条件**：版本发布时（恒）。
- **消费者**：版本漂移守卫（SWR-V3.4.4-008）、test_doc_lint 资产计数守卫。
- **案例支撑**：v3.12 同款先例（TOOLING 漂移收口 + 手工段维护）。

## 4. 明确不做（义务棘轮防护）

- 不建 H8/H9 假说（错误路径保持清单级——v3.12「不建 H8」先例；gate ④ H1-H7
  语义不变）。
- 不重归 190/129（MEMORY-SAFETY 既有锁）；不动 CK-SENTINEL-SEMANTICS 与
  CK-SIBLING-LISTENERS 存量（共绑合法，不触碰）。
- 无新 PREC（436/444/1333 先例 map 已可达——CWE_FAMILY_MAP L19-25）；无新
  harness 模板；不加新门禁、不加新绑定维度、不注入 R4/Mode A'。
- 时间/Unicode/侧信道维度无漏报支撑暂缓（义务三问③不成立）。
- 不修复 README.md 清单计数存量漂移（v3.12 口径一致性，记入评估注记）。
