# SWR_V3_39: haproxy 验收复盘四修复

## SWR-V3.39-001: normalize 关键词词边界匹配 (D-1)

- **裁决**: normalize_surfaces 两分支的 ASCII 关键词匹配改词边界语义
  (正则 `\b` 词边界; CJK 关键词保持子串——无词边界概念, 同 binder
  _kw_match 判据 SWR-V3.4.4-001)。两分支共用同一辅助函数, 消双实现漂移。
- **义务三问**: ①触发条件——自由文本 trust_boundary 归一化 (无条件, 数据正确性);
  ②消费者——merge 全链 + R2/R3 边界语义; ③裁掉丢什么——haproxy 40/82 面
  误映射实录 (wire 字节判 local)。
- **测试守卫**: test_v339.py T-1。

## SWR-V3.39-002: seed 双写覆盖全部种格条目 (D-2)

- **裁决**: seed_entries 双写循环扩展为覆盖全部成功种格条目 (external_seeded
  与 battle_verified/source_seeded 统一处理, origin 字符串按 tier 区分);
  矩阵格缺失时自动创建 (seeded 形态, 五字段初始化)。
- **义务三问**: ①触发条件——seed 命令种格 (无条件, 双写一致性契约);
  ②消费者——test_v329 双写一致性守卫 + hints 格提示; ③裁掉丢什么——R6
  手动双写 + 缺格手动建的两轮失同步实录。
- **测试守卫**: test_v339.py T-2。

## SWR-V3.39-003: 资产计数守卫集中化 (D-3)

- **裁决**: 新建 tests/asset_guards.py 承载全部资产计数常量
  (清单/先例/签名/inventory 条目/battle_confirmed/矩阵格数), 既有守卫
  测试 import 之。合法回填后的守卫更新 = 单点编辑; 硬编码计数作为漂移
  守卫的语义不变 (不变弱, 只集中)。
- **义务三问**: ①触发条件——资产回填提交前 (无条件); ②消费者——既有守卫
  测试 ×N; ③裁掉丢什么——R6 守卫失同步两次复发实录。
- **测试守卫**: test_v339.py T-3。

## SWR-V3.39-004: severity_override 形态契约 (D-4)

- **裁决**: (a) SKILL.md 严重程度段补契约一句——severity_override 为字符串
  {critical,high,medium}, 理由写 severity_override_reason 独立字段;
  (b) batch_verify 消费点加形态容忍: dict {value, reason} 机械归一化为
  字符串+reason 字段并输出 warn (数据形态归一化, 不动语义——同 evidence
  归一化先例; 不自动改写纪律不适用于形态归一化)。
- **义务三问**: ①触发条件——r4-collect/grade 读 severity_override 时;
  ②消费者——报告渲染/分级; ③裁掉丢什么——dict 形态 AttributeError 实录。
- **测试守卫**: test_v339.py T-4。

## 兼容性不变式

- 六门禁判据/队列模型/N=2/铁律零触碰; 全提示级/机械级;
- 旧队列复跑零新增告警 (servo/haproxy 双队列验收判据);
- 本轮手动补的双写数据保持幂等 (seed 重跑零重复)。
