# SOFTWARE_DESIGN_V3_38: 编辑点级设计

## checklist_library.json (D-0 + D-1)

```
CK-SLICE-CAPACITY     + "binding": {"cwe": ["CWE-125", "CWE-787"],
                                    "keywords": ["切片", "slice", "越界", "out of range"]}
CK-MAGNITUDE-OWNERSHIP + "binding": {"cwe": [], "keywords": [],
                                     "applies_to_phase": "R5"}   # 实证语义空间挂载
CK-SIBLING-CONSISTENCY (新) family=sibling-consistency
  binding: {"cwe": [770,789,400,409,834,833,1333, 284,285,287,306,639,862,863,926,
                    22,79,352,918], "keywords": ["端点", "endpoint"]}
  steps: (1) 枚举同功能族兄弟实例 (同路由表其余端点/同模块接口其余实现/同解析族其余路径)
         (2) 防御维度对比矩阵 (体量封顶/鉴权门/超时/输入校验)
         (3) 任一兄弟有防御而本 sink 无 → 缺陷假设 (修复残留/防御不一致)
         (4) 判据: 不一致须有文档化解释, 否则成立
```

## workflow_export.py (D-2 + D-4)

1. VERDICT_SCHEMA properties 增:
   `"self_refutations": {"type": "array", "items": {"type": "string"}}`
2. verify prompt 组装段 (containment 之后, Mode W 输出契约之前) 增两段:
   - 自证伪轮条款 (D-2): ≥2 条翻转点, REACHABLE 攻量级/主体/前提,
     UNREACHABLE 攻防御前提 (默认生效? 覆盖攻击者全部维度?), 空数组须
     evidence 说明理由;
   - 实证机会条款 (D-4): 可构建 + 实证类声称 → 低成本实测建议附数字,
     无环境记录 blocker; 实测数字是分级升档与证伪攻击面。
3. refute_prompt (toolbox 之后) 增注入:
   `c.get("self_refutations")` 非空 → "证伪攻击面 (verifier 自证伪清单):
   优先逐条验证以下翻转点的前提是否成立: ..." (截前 6 条)。

## SKILL.md (D-1 + D-3 + D-5)

- R2 段 (对抗枚举条款之后): 「同族不一致防御枚举 (提示级): hints 装载后对
  目标中同族多实例功能面做防御维度对比矩阵——不一致即假设 (修复残留形态)」;
- R2 段: 「公开面关联检索 (提示级): 网络可用时假设生成前做 CVE/GHSA 关联 +
  上游 master 对账, 落盘 .audit_results/upstream_recon.json; 已修形态降级或
  改口径, 未修附佐证; 上游后修=快照缺陷候选 (时间差假设); 不可用零阻塞」;
- R5 段 (harness 模板枚举之后): 「harness 回收条款 (提示级): 收官复盘对现场
  构造实证程序做通用化评审, 跨项目可复用则去项目化入库 templates/harness/」。

## P 分层序列

P1: D-0 binding + D-2 schema 字段 → P2: D-2 prompt 两条款 + refute 注入 →
P3: D-1 新条目 + SKILL.md 三条款 → P4 版本链五件。
