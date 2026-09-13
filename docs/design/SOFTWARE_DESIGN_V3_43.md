# SOFTWARE_DESIGN_V3_43

函数级/内容级设计。机制冻结——本周期无函数改动（版本链机械步除外）。

## K-1 c 矩阵 PAGE-CACHE-OWNERSHIP 族（seed_entries）

```json
{"entries": [{
  "lang": "c", "family": "TRUST-BOUNDARY",
  "title": "零拷贝/in-place 优化所有权: 外部支撑页被协议栈 in-place 写",
  "cwe": ["CWE-787", "CWE-290"],
  "patterns": [
    "splice/vmsplice 植入的只读页被当作自有缓冲做 in-place 加密/解密写",
    "skb fragment 槽接收外部支撑页后协议栈直接改写",
    "零拷贝优化路径跳过页所有权/可写性检查"
  ],
  "sinks": [
    "splice/vmsplice 页植入点 (pipe_buffer ops)",
    "skb frag 槽填充点 (skb_fill_page_desc/vmsplice_to_user 反向)",
    "scatterlist 外部页绑定点",
    "in-place 加密/解密路径 (AEAD authencesn/ESP/RxRPC 族)"
  ],
  "pitfalls": [
    "外部支撑页 in-place 写 = 越权写 (CWE-787 页缓存形态) 判据: 页 owner 与写入者非同一主体",
    "同族防御对比矩阵: splice 路径族的页所有权检查 (page_is_accessed/anon_pipe_buf_ops) 逐点对照——任一兄弟有防御而本面没有即假设 (SWR-V3.38-001 形态)",
    "优化路径清单枚举: 零拷贝/in-place 优化是独立假设空间 (修复变体族: Dirty Pipe 2022-0847 ground truth, 变体间隔可跨多年)",
    "确定性逻辑缺陷 (无竞态) 形态——不依赖时序, 实证成本低 (单发 PoC)"
  ],
  "source": {"tier": "external_seeded",
             "origin": "2026 Linux kernel LPE CVE 公开披露族分析 (Copy Fail CVE-2026-31431 / Dirty Frag CVE-2026-43284+43500 / Fragnesia CVE-2026-46300 / Dirty Decrypt CVE-2026-31635 / PinTheft CVE-2026-43494 / DirtyClone CVE-2026-43503 / pedit COW CVE-2026-46331; Dirty Pipe CVE-2022-0847 家族)",
             "date": "2026-09-13"}
}]}
```

## K-2 java 矩阵 10 格补种（seed_entries，battle_verified）

族归并条目（source=Keycloak lessons 2026-09-13, tier=battle_verified）：
- INJECTION 族追加 pattern「日志注入: 用户可控值进日志记录（控制字符/伪造记录行/敏感头日志）」cwe 117+532
- AUTHN 族追加条目「信任代理判定 fail-open: 未配置可信地址时恒真 + 客户端自置信任头被采信（证书身份冒充面）」cwe 290+287
- RACE 族追加条目「时序窗口: TOCTOU 检查与消费跨事务分离 / 并发窗口 (竞态窗口+会话过期+重放归一族)」cwe 367+362+613+294
- ERROR-HANDLING 族追加「空引用解引用: 解析结果零长度元素未防御 (Java 形态 AIOOBE/NPE)」cwe 476
- NUMERIC 族追加「类型混淆: 不可信 claim 强转 (JSON 类型攻击者可控)」cwe 704
- RESOURCE-DOS 族追加「无界集合累积: 分页参数直通 skip/limit 无钳制 (java 形态)」cwe 789
- AUTHN 族追加「撤销策略未生效: 多层 notBefore 校验维度缺失 (realm/client/user 三级检查不完整)」cwe 303

## K-3/K-4/S-3 SKILL.md 文本（提示级）

K-3 H7 段 ③ 替换为：
```
③ 鉴权谓词弱化或逻辑错误（前缀/子串/hash 替代全名；条件写错/比较对象
错位——谓词本身错误而非被弱化，潜伏长周期形态, SWR-V3.43-003）
```
K-4 fixminer 段补句：
```
同形态修复族间隔 >1 年时（如 page cache 写越权族 2022→2026 变体潮），
--since 默认窗口挖不到 ground truth——族信号驱动需长窗口或手工指定修复
commit（SWR-V3.43-004）。
```
S-3 R6 段补句：
```
条款消费度量（v3.43, SWR-V3.43-008, 提示级无门禁）：审计收官时在
lessons.md 记录本轮实际被装载/消费的 SKILL.md 条款清单——两周期后按
消费记录批量裁除死条款（条款密度与遵守率负相关，无消费即裁除）。
```

## K-5 biz_hypothesis.md H3 段补句

```
（v3.43, SWR-V3.43-005, 提示级）kernel 形态锚点: 任务退出竞态（退出路径
与回调并发）、timer/延迟回调持引用、调度器状态复用（RBTree 双插入形态）、
异步子系统对象生命周期（io_uring 形态）——2025 年 UAF 族六大 CVE 与
H3 检测要点的对应形态。
```

## S-1/S-2 skill-optimizer SKILL.md

S-1 义务三问段扩为四问，追加 ④；S-2 新增「架构重设计触发判据」段（五信号）。

## P4 版本链

1. TOOLING_VERSION "3.42"→"3.43"
2. 版本守卫测试行同步（grep "3.42" 的断言）
3. SKILL.md 版本历史表 + TOOLING 锚点行
4. REQUIREMENTS_TRACKING 手工追加段 + gen_tracking VERSIONS 登记
