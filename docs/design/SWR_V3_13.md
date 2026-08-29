# SWR_V3_13 — 软件需求（v3.13 错误路径处理族 + 数值语义族 + 账本锚点一致性修复）

> 对应文档：REQ_V3_13.md（需求语义）/ SOFTWARE_DESIGN_V3_13.md（改动点）。
> SWR 为可测契约：每条含断言式描述，测试实现见 test_v313.py。
> 原则：旧队列零行为变化；新增行为全部有触发条件（cwe/关键词命中）。

## 1. 覆盖账本（REQ-V3.13-001）

- **SWR-V3.13-001**：`families` 含 NUMERIC(191/369/681/697) 与
  ERROR-HANDLING(457/665)；WEB cwe 含 436/444；RESOURCE-DOS cwe 含 1333；
  两族 rows 均含 `langs == {}` 空行；`_aggregate_counts` 将 436/444→WEB、
  1333→RESOURCE-DOS、191→NUMERIC、457→ERROR-HANDLING（均非 OTHER）；
  缺口扫描输出 NUMERIC/ERROR-HANDLING 缺口格。

## 2. 严重程度映射（REQ-V3.13-002）

- **SWR-V3.13-002**：`severity_for` 191→critical、369→high、457→high、
  444→high、1333→high、681→medium、697→medium、665→medium、436→medium；
  override 优先级与 claim_type 回退语义不变（以 test_v37_report 既有锁为回归锚）。

## 3. 数值语义族清单（REQ-V3.13-003）

- **SWR-V3.13-003**：CK-NUMERIC-TRUNCATION 与 CK-NUMERIC-SEMANTICS 经既有
  binder 绑定（零代码改动）：
  - cwe 路径：191/681 → TRUNCATION；369/697 → SEMANTICS（唯一锚定，精确断言）；
  - 关键词路径：CJK（截断/回绕/除零/不一致比较）与 ASCII 多词（"integer
    overflow"/"wraparound"/"divide by zero"/"inconsistent comparison"）双路径命中；
  - 负例限定形态（非全量零误绑声称——「算术」等宽词共绑合法）：`error_handler`
    形态不绑数值族条目。

## 4. 错误路径族清单（REQ-V3.13-004）

- **SWR-V3.13-004**：CK-ERROR-BRANCH 与 CK-ERROR-CLEANUP 绑定契约：
  - 错误分支/失败分支/条件反转/异常路径/error path/failure path 任一命中 →
    CK-ERROR-BRANCH（无 CWE 锚定，关键词绑定为主）；
  - 负例：summary 含「异常处理 catch 分支」→ 绑 CK-SIBLING-LISTENERS 而
    **不绑**新条目（新关键词无裸「异常」的验证）；
  - cwe 路径：457/665 → CK-ERROR-CLEANUP；关键词路径：未初始化/uninitialized 命中；
  - 负例限定形态：`error_handler`（下划线）/`cleanup()`/裸 error 不绑新条目
    （无裸 error/cleanup 关键词）。

## 5. 去项目化与版本链（REQ-V3.13-005）

- **SWR-V3.13-005**：4 条新清单去项目化扫描 0 命中（DEPROJECT_BLACKLIST 全量
  含 lersosa、无 /root/ 路径、无 applications 死字段）。
- **SWR-V3.13-006**：TOOLING_VERSION == "3.13"；SKILL.md 含「🆕 v3.13 增量」段
  且资产地图计数为 38 条检查清单/17 条裁决先例；严重度表含 9 码注记；test_v313
  全绿且既有全量回归全绿（315 基线）；源仓库同步分 commit + install +
  安装版测试全绿。

## 6. 兼容与明确不建（回归护栏）

- 旧队列复跑零新增 blocking（数据/映射层追加；无队列 schema 变更、无门禁语义
  变更；既有 CWE 归属锁 770/400→RESOURCE-DOS、327→CRYPTO、345→DATA-INTEGRITY、
  190/129→MEMORY-SAFETY 零碰撞）。
- 不建 H8/H9、不重归 190/129、不动 CK-SENTINEL-SEMANTICS/CK-SIBLING-LISTENERS
  存量、无新 PREC、无新 harness、时间/Unicode/侧信道暂缓。
- ⚠️ 禁止运行 `tools/gen_tracking.py` 再生成 REQUIREMENTS_TRACKING.md
  （V3.4.4-V3.7 手工维护段不在 VERSIONS——再生成会删除）。V3.13 段手工追加。
