# SKILL_LESSONS_nacos（2026-08-25，批次 #4）

Nacos 3.2.x @2979345f2 审计实战教训（R0→R6 全流程，六门禁零违规）。

## 1. R1 域 agent 自定 schema 需要主代理机械归一化（非缺陷但需工时）
process/storage 域 agent 产出顶层 `entry_points` 数组（`code`/`kind`/trust_boundary 为 channel 数组），
boundary 域产出 `boundary_surfaces` + B-* ID——三种形态全被 surface_mapper 拒绝。
主代理机械归一化（ID 重映射 + evidence.snippet 包裹 + trust_boundary 摘要）耗时约 4 轮。
**教训**：surface_map_domain 任务书应明确「五域一律输出 canonical `{"surfaces": [...]}` 包裹形态」，
并对 process/storage/boundary 域给出该形态示例（当前任务书只有 4 域示例且允许自由结构）。

## 2. R1 测绘盲区：storage agent 声称「穿越被阻止」但未查白名单含 '.'
storage 域 S5 判定「Path traversal blocked by charset whitelist (no '/' '\\')」——
但 `ParamUtils.validChars=['_','-','.',':']` 含 '.'，`..` 合法。D01 filter 用「反诱导条款」
反向核实才翻出穿越写链（tenant 维度被 param-check 拦、group 维度 1 层逃逸成立，CAND-012 Medium）。
**教训**：测绘 agent 的防御声称必须查白名单字符集的实际内容（'.' 在白名单 = 路径穿越原语），
不能只 grep '/'。建议 surface_map_domain 任务书对路径类面加一条显式 checklist：
「白名单是否含 '.'/'..' 序列？逐字符集核实」。

## 3. R4 agent 与主代理的结论冲突必须主代理亲自裁决（CAND-012 冲突标注生效）
H4 agent 在 reviewed_clean 段声称「ParamUtils 拒绝 '..'」——与主代理直接验证矛盾。
主代理在 R3 任务书中标注冲突让 verifier 独立裁决，verifier r1 实证 groupPattern 放行 '..'。
**教训**：R4 与 R2 结论冲突时，冲突标注 + 独立 verifier 是低成本高价值的裁决链。

## 4. 复活波价值再现：2/2 证伪基于共同时间序事实错误
CAND-006 首轮 2/2 证伪（「latch(≤3s) 先于 leader 选举(≥5s)，写路径无窗口」）被复活 agent 以
jraft 1.4.0 NodeImpl 源码推翻：单节点稳定组 init() 内同步 electSelf→becomeLeader，5s
选举超时只作用于定时器——bean 构造期 raft 组创建即当选，先于 context refresh 后首个
@Scheduled doCheck tick。**时间序论证必须核实底层库的当选捷径**，不能套用文档化超时参数。
（批次累计：复活波成功 4 例——kafka 3/3 + nacos 1/2。）

## 5. 复活论证也会选择性使用 shipped 值（CAND-014 复活后 2/2 驳回）
复活 agent 用「空 identity 锁 admin 路径」论证但无视「同为空值的 token.secret.key 使 JWT
签发 fail-closed」——复活链的 JWT 段在 shipped 默认断裂。**教训**：复活后证伪（gate
post_resurrect_refutation）是必须的，复活 agent 与前 verifier 有相反的偏差方向
（复活=选择性放行，首验=选择性阻断）。

## 6. R5 实证收获：真实实例 e2e 一石三鸟
构建真实实例（mvn release-nacos install 9.7min + 发行包）后：
- 3 条 unbounded 声称全部 e2e 实证（磁盘 3× 放大/实例 17MB 每千/连接 200KB 每条，均线性无上限）；
- HTTP extractor 1024 字符 metadata 限制被实证（400 拒绝 128KB metadata）——修正了
  「HTTP 路径 metadata 无界」的错误外推，确认 gRPC 才是主放大面；
- 附赠 H5-F1 e2e（匿名创建管理员 200 + 明文密码回显 + login JWT）。
**教训**：JDK25 可构建 Spring Boot 3.x 项目；RAT 检查会因审计产物文件失败（-Drat.skip=true）；
v3 注册 API 用 form 参数非 JSON body（错误消息即文档）。

## 7. 机械报告复核列契约：refutation 字段须归一化为 {by,survived,votes,refute_count}
主代理手工记录的 refutation 数组不被渲染器识别（显示「未复核」）；归一化为机械契约
（survived/demote/strengthened[]）后正常渲染。**教训**：R3.5 收集应直接走
`--stage collect-refutation` 机械落盘，或主代理按契约字段归一（本次手工归一）。

## 8. shipped 事实（对下游审计的通用提示）
- 「总开关 auth.enabled=false 使整体失效」是错误表述——三 scope 独立开关
  （auth/admin/console 各自生效），多个 agent 反复踩坑（H5-F5 才纠正）。
- bootstrap jar 内默认与 distribution conf 默认相反（auth.enabled jar 内 true）——
  部署形态分叉必须分别判定，不能只读一个配置文件。
- 注释中的示例密钥若是公开 known 值，属「诱导性配置弱点」（claim=other 类），
  不是默认可达——判定模板：active 值/注释值/代码零值三态取证。
