# SOFTWARE_DESIGN_V3_40 — 函数级设计 + P 分层序列

## P1 机械（D-1: evidence_ledger.grade_verdict fidelity 分支）

编辑点: src/evidence_ledger.py:146-148（empirical 判级三元）

```python
# 现状 (146-148):
if empirical and isinstance(empirical, dict) and \
   (status in CONFIRMED_EMPIRICAL_STATUSES or scope_infer or canonical_infer):
    grade = "empirically_confirmed"
```

目标形态:

```python
empirically_ok = (empirical and isinstance(empirical, dict)
                  and (status in CONFIRMED_EMPIRICAL_STATUSES
                       or scope_infer or canonical_infer))
fidelity = (str(empirical.get("fidelity", "real_target")).lower()
            if isinstance(empirical, dict) else "real_target")
if empirically_ok and fidelity != "mechanism":
    grade = "empirically_confirmed"
elif empirically_ok:  # mechanism 档: 范围纪律 (SKILL.md R5)
    grade = "edge_proven"  # 走 else 分支逻辑前先定初始值, 由下方 edge/static 复算
    errors.append("empirical fidelity=mechanism: 判级维持 edge_proven "
                  "(范围纪律——mechanism 档不得升 empirically_confirmed, "
                  "回填脚本可先跑 harness_runner.check_scope 复核)")
else:
    <现有 edge/static 判定体不变>
```

设计要点:
- fidelity 缺省 real_target（SKILL.md: fidelity 缺省 real_target）
- errors 注记形态对齐 scope_infer/canonical_infer 先例（提示性, 非阻断）
- 控制流重构以 `empirically_ok` 布尔提取, else 体零改动

## P2 结构（D-7: r35-collect 实证回填候选扫描）

编辑点: tools/batch_verify.py r35-collect 段 strengthened 收集块后（~1575-1595）

```python
# 在 result 组装前:
EMP_BACKFILL_MARKERS = ("rrsets", "exit code", "OOM", "OutOfMemory",
                        "VmRSS", "ms 内", "ms内", "/", "试验", "trials",
                        "NOERROR", "NXDOMAIN", "200", "403", "SIGSEGV",
                        "heap-buffer-overflow", "AIOOBE", "ArrayIndexOutOfBounds")
backfill_candidates = []
for cid in sorted(by_id):
    blob = "；".join(
        [str(x) for d in by_id[cid] for k in ("strengthened", "reason", "note")
         for x in (d.get(k) or []) if x])
    if blob and any(mk in blob for mk in EMP_BACKFILL_MARKERS):
        backfill_candidates.append(cid)
if backfill_candidates:
    result["empirical_backfill_candidates"] = {
        "ids": backfill_candidates,
        "advice": ("证伪者证据文本命中实测数字形态——主代理按 R5 实证回填规范裁决 "
                   "(带 backfilled_by + 实测数字依据; fidelity 按 harness 形态标注; "
                   "mechanism 档不得升 empirically_confirmed)。不自动改写。"}
```

设计要点: 纯提示级, 不写队列不写 empirical（纪律 #4）; 标记集取保守值（宁可
多提示不漏提示——主代理裁决成本低, 漏判成本=实测白丢）; 反面分支（无实测数字）
零输出, 测试守卫覆盖。

## P3 内容（D-2/3/4/5/6）

### D-2: verifier 任务书步骤 3.5（tools/batch_verify.py 步骤 3 段后插入）

```
### 步骤 3.5（v3.40, SWR-V3.40-002）: 攻击者字节承载判定
claim_type ∈ {rce, leak, crash, oom, protocol_dos, unbounded} 时:
- 在 call_chain 中标注**至少一跳**的字节承载证据（哪个跳上哪个字段携带
  攻击者字节——如「RPC 载荷字段 X」「argv 参数」「文件内容」），写入 evidence；
- 全链任一跳都不承载攻击者字节 → 链是触发器链而非数据流链:
  verdict 不得判 REACHABLE（改 NEEDS_REVIEW），claim_type 改 other 并注明
  「结构性可达, 字节承载未证」;
- 触发器链 vs 数据流链的区分证据必须落在 edge_evidence 的 proof 文本内
  （CAND-024 形态: 四边全真仍被 2/2 证伪, 根因即该义务缺失）。
```

### D-3: checklist_library.json +1（尾部, 48→49）

```json
{
 "id": "CK-SIBLING-FIX-AUDIT",
 "family": "sibling-fix-audit",
 "applies_to": ["verifier", "main-agent"],
 "binding": {"keywords": ["fixminer", "修复", "CVE-", "patch", "加固", "validat"],
             "note": "修复触发型: fixminer 命中/公开补丁在证据文本出现时绑定"},
 "steps": [
   "命中修复提交/公开补丁对某函数/类/模块的加固后, 枚举同族实例 (同接口实现/同解析族/同 handler 注册点/同序列化入口) 的加固状态",
   "对每个同族实例按加固维度 (类校验/长度上限/白名单/权限收敛) 建差分矩阵",
   "任一兄弟已加固而本实例未加固 → 修复残留假设 (Hadoop 实录: ZK 已 ValidatingObjectInputStream 白名单而 LevelDB 兄弟裸 OIS; 内层类名已校验而外层仍 initialize=true)",
   "判据: 修复提交的 diff 范围之外的同族实例未同步加固即成立"
 ],
 "source_lessons": ["hadoop 验收 lessons 第 3 条 (ZK vs LevelDB 裸 OIS, HADOOP-19930 内层修/外层漏, 2026-09-10)"],
 "name": "修复残留同族枚举检查"
}
```

### D-4: hypothesis_filter.md 排除判据 4 后插入

```
4.5 **位域/ordinal 越界判据的证据义务（v3.40, SWR-V3.40-004）**:
   判「位域 ordinal 直索引定长枚举数组越界」前必须 Read 枚举常量声明行
   核对 (a) bit 长度 (如 `TYPE(PERMISSION.BITS, 2)`) 与 (b) 枚举值数——
   声明行 file:line 写入 note。bit 范围 ⊆ 枚举值数时该判据不成立
   (实录: 「3bit 索引 4 值枚举」声称与源码 2bit 声明不符, 真实溢出在
   同族另一格式类的 nid 组合域)。
```

### D-5: ENVIRONMENT_PROBES.md 尾部增段

```
## setuid 辅助二进制部署拓扑（v3.40, SWR-V3.40-005）

setuid-root 辅助二进制 (容器执行器/特权 helper 形态) 的 real_target 实证
必须先复刻部署拓扑, 五要素:

1. 配置链: cfg 文件与**全部祖先目录** root 属主且非组/全局可写 (二进制
   启动检查), cfg 路径常为编译期常量——先查编译变量再放 cfg
2. 二进制权限: root 属主 + 属组=cfg 声明组 + 无 other 写/执行位 + setuid
   位 (6750 形态); 检查链逐项失败的日志即修复映射
3. 调用者身份: setuid 下 nm_uid=调用者**真实 uid**——须以专用服务账户
   运行 (root 直跑会被「Running as root is not allowed」拒绝)
4. 数据目录族: local/log dirs 属主=服务账户; tmp/private_slash_tmp/
   private_var_slash_tmp 须容器用户属主 (chmod 由降权后的进程执行);
   usercache 父目录须预置
5. 工作目录: 脚本复制目标 (launch_container.sh) 落在 work_dir——须容器
   用户可写目录 (非 root-only 目录)

实证实录参考: hadoop container-executor 注入实证 12 轮失败日志收敛
(cfg 祖先/二进制位/nm_uid/tmp 族/脚本复制逐项修复)。
```

### D-6: hypothesis_filter.md 排除判据 5 段内增句

```
（v3.40, SWR-V3.40-006）核查默认开关时先判定**开关方向**:
- feature 默认关 (服务/运行时默认不启用) → 可达性降低, drop 前提成立方向;
- 鉴权/校验 gate 默认关 (authorization=false 使 ACL 恒真、token 校验被
  if 短路) → 可达性**升高**, 「防御已到位」drop 前提不成立方向;
两方向裁决不可互套 (实录: 同批次 13 条鉴权 gate 默认关假设全 keep)。
```

## P4 版本链五件

1. workflow_export.py TOOLING_VERSION → "3.40"
2. 版本守卫测试行更新 (tests 中含 "3.39"/TOOLING 断言处逐处核对)
3. SKILL.md 增量段追加 v3.40 行 + 版本历史表 + 附录资产计数 48→49
4. REQUIREMENTS_TRACKING.md 手工追加段 + gen_tracking VERSIONS 登记
5. 计数守卫同步: SKILL.md 附录行 + 正文 checklist 计数处 + tests/asset_guards.py
