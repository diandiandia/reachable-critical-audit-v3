# SKILL Lessons — grpc（2026-08-22）

> 本文件由 R6 lessons_recorder 机械生成 + 主代理过程观察补充。

## 审计统计（自动提取）

## 主代理过程观察（人工补充）

- gRPC 审计过程观察（2026-08-22）: 1. workflow 脚本 args 契约差异: verify 波次期望 {"candidates": [...]} 数组形态，resurrect 脚本首次以裸数组传入被拒（args.candidates 缺失 W6 §5），修正后成功——两脚本契约一致，是派发侧误传。
- 2. signature_matcher gen 直接覆盖 hypotheses.json: 佐证器 gen 输出 59 条假设覆盖了主代理先写的 28 条 LLM 假设（同文件名），合并需手工重建 LLM 清单——建议 gen 落盘独立文件名（如 hypotheses_gen.json）避免覆盖。
- 3. R1 boundary 域 agent 编号跳号（001,002,004..013 无 003）: merge 后 12/13 条在册，校验器未报缺号——建议校验器提示 id 序列空洞（非阻断）。
- 4. mature 库 R4 与 R3 并行效果: R4 H1-H7 的防御确认与 R2 filter 的 boundary_confirmations 高度一致（HPACK skip-before-allocate、frame_data 检查先行、zlib max_output_size），双通道交叉验证了 C++ core 解码面的防御完整性。
- 5. R3 verifier 对 BoringSSL 钉住 commit 的实证方式（bazel/grpc_deps.bzl 解析 + 下载源码核对 ssl_max_handshake_message_len）是跨仓库依赖审计的有效模式，复活复核同样独立实证了 BIO pair.cc:54 的 17KiB 默认。
- 6. 无 REACHABLE 审计形态: 候选 1 条 UNREACHABLE（声称类）→ 复活攻击全量（N=1）→ revived=false；R5 无实证触发；六门禁全 PASS 含 r4_feedback 无冲突。

## 待回填

- 本文件的价值判定由主代理完成：高价值条目应并入 W6_MORE_LANGS_FINDINGS.md 或对应语言 lessons；
  低价值条目保留在本文件作为审计轨迹。
