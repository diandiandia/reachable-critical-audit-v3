# SKILL Lessons — quarkus（2026-08-27）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

### R0
- [target_kind] 审计目标类型 = hybrid

## 主代理过程观察（人工补充）

- 【v3.8 验证审计】quarkus 为第二批验证项目 (先 elasticsearch 后 quarkus)。R2 keep=0 → 抽样复核条款触发, 3/3 bc 防御点源码核实属实 (checkSession 先于 readObject / Host 头语义 / management 默认关)。
- 【机制价值】R4 深度验证产出核心新发现: FileSystemStaticHandler decode-after-normalize (%2e%2e 复活 → 任意文件读取, H-7-F1 高)。该发现由 v3.8-009 路径白名单 checklist 驱动的组件级核查链引出——R1 data 域对静态资源面做了 knownPaths 精确匹配核实, R4 H-7 沿『路径语义越界』假说找到 webjar 分支的解码顺序缺陷。任务书 checklist 的正向价值实证。
- 【机制价值】Host 头谓词缺陷 (H-5-F1/H-7-F3): LocalHostOnlyFilter 检查 absoluteURI().getHost() 而非 remoteAddress——『本地过滤器』语义陷阱的通用形态: Host 头是攻击者可控输入, 本地性判定必须基于 socket 对端地址。可提炼为通用 checklist (CK 候选: 本地性判定谓词的输入源)。
- 【裁决实录】quarkus R3 空队 + R4 22 findings 形态: keep=0 时 R4 是唯一深度验证层, 抽样复核条款 (SWR-V3.4.6-004) 是防『过度防御性 drop』的必要制衡——本役 bc 残留 (Host 伪冒/静态密码无限速/opt-in 管理接口) 全部经 R4 H-5/H-7 升格为 confirmed findings, 证明 bc 机制只放行默认上下文防御而不吞掉残留。
- 【编排】两项目连续审计共用同一套薄封装 (verify/refutation/resurrect thin wrapper), ES 侧修复的 const const bug 未复发; quarkus 侧锚点裁决器引入『同分取离声称行最近』修正 (ES 侧裁决器缺陷)。
- 【skill 缺陷·复核确认】ES 侧 3 项新发现 (target_kind _scan_files 400 上限 / r35-collect 缺 survived/votes/refute_count / BOUNDARY_KINDS 无 panama) 在 quarkus 侧未出现新形态, 维持待修清单。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
