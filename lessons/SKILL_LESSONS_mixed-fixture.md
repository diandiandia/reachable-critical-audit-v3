# SKILL Lessons — mixed-fixture（2026-08-17）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = library

### R3
- [grade_recomputed] CAND-002: 机械分级重算 (main-agent adjudication (resurrection-verified edges))
- [grade_recomputed] CAND-004: 机械分级重算 (main-agent adjudication (resurrection-verified edges))
- [grade_recomputed] CAND-005: 机械分级重算 (main-agent adjudication (resurrection-verified edges))
- [grade_recomputed] CAND-006: 机械分级重算 (main-agent adjudication (resurrection-verified edges))

### R3.5
- [strengthened] CAND-001: len+4 无符号回绕: len=0xFFFFFFFF → len+4=3 通过一致性检查, memcpy 近 4GiB; line 21 tmp[len]=0 是第二处越界写
- [attribution_correction] CAND-001: source_line=22 指向 -3 哨兵行, 实际 sink 在 line 20/21

### R3.5-N
- [resurrection] CAND-002: REACHABLE (库型边界先例统一)
- [resurrection] CAND-003: UNREACHABLE 维持 (机制证伪独立于可达性)
- [resurrection] CAND-004: REACHABLE (s 维度 CStr 越界扫描 + idx 维度宿主 abort DoS)
- [resurrection] CAND-005: REACHABLE (空输入 dangling 0x1 → free 无效, 机制与分配器无关)

### 裁决
- [adjudication_note] 库型边界先例统一适用 (主代理, PREC-CONSISTENCY-001): fixture 为库交付物 (零 main/网络入口, R1 network 空域), 公共 API 即信任边界——所有同形包装(parse_message/build_index/lookup/dup_alloc/CDLL import) 按同一标准裁决。v3.2 缺陷记录: R0 需 target_kind 判定 (application/library), 见验收报告。

### 验收
- [acceptance] {"project": "mixed-fixture (ground-truth 对照)", "ground_truth": {"GT-1 栈溢出": "REACHABLE ✓ (e2e stack-smashing exit=134 + 2 补强)", "GT-2 无界分配": "REACHABLE ✓ (复活攻击: 同批双标纠偏)", "GT-3 指针截断": "UNREACHABLE ✓✓ (机制实测证伪: CPython 3.14 全指针透传——skill 正确纠正了植入错误)", "GT-4 Rust 越界": "REACHABLE ✓ (复活攻击纠正 verifier 事实错误; 真实面 = CStr 越界扫描 + 宿主 abort, 植入注释的 UB 声称被证伪)", "GT-5 释放错配": "REACHABLE ✓ (复活攻击: 空输入 dangling 0x1 机制与分

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
