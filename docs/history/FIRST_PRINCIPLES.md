# 第一原则案例溯源（SKILL.md 规则的历史档案）

> 2026-09-08 自 SKILL.md 迁出（SKILL.md 只保留操作性规则；规则的案例支撑在此追溯）。

## 三禁止的来源（2026-08-17 mbedtls 审计复盘）

签名库携带 Django/NestJS/Ktor/lighttpd/WordPress 专属 API 名（get_host/read_body/
multer/maxDecodedContentLength/good_origin/CleanXSS）、verifier 任务书是 Python
思维定式（find_spec）、harness 按历史战役配置（4 模板 6/15 语言）、R0 冒烟仅对
历史 fixture 有意义（非 fixture 项目恒放行）。修复方案见 v3.2.2 设计
（P-A 资产去项目化问题域）。

## v3 取代 v2.1 的验证档案（2026-08-16 三锚点回归）

v3 由三锚点回归测试（sinatra/lighttpd/actix-web 对照归档基线）实战验证：
候选规模下降 98~99.98%、闭合率 100%、独立复核机制三次实战拦截
"代码路径可达≠攻击相关"误判、产出 2 个实证确认的 REACHABLE。
v2.1 唯一遗产为 `docs/legacy/SKILL_V2.1.md`（规范备份，供对照历史）。
