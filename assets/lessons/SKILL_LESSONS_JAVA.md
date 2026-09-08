# Reachable Critical Audit Skill — Java 审计暴露的缺陷与改进建议

> **文档性质**：基于 fastjson2（2.0.62/2.0.63/2.0.65-dev 三版本交叉复核）实测审计对
> `reachable-critical-audit` skill 的回顾性缺陷分析。驱动 skill v2.1 规则库改进，非项目审计报告。
>
> **审计日期**：2026-08-13
> **测试目标**：fastjson2 2.0.62（AutoType hash 白名单绕过，2.0.63 修复）与当前 head af56f06ee（2.0.65-dev）

---

## 0. 摘要

Java 是 skill 规则库覆盖最广的语言之一（21 条规则），但 fastjson2 实测暴露 3 类缺陷：

1. **语义逻辑缺陷不可表达**（最重要）：`checkAutoType` 的 **hash-only 白名单**绕过不是
   "脏数据到 sink" 的污点问题，而是"授权谓词被弱化"的逻辑问题——sink+taint 模型抓不到，
   只有 `git diff` 2.0.63 修复 commit 才能确认。→ 催生 LOGIC_PATTERN 规则类型 + R0.5 考古阶段。
2. **CWE-78 伪通用噪音**：`exec`/`execute` 命中 ASM `Frame.execute`、javac `JCTree.exec`，
   140 条候选全为框架内部方法。→ 需要接收者限定（REQ-28）。
3. **"修复-再暴露"循环**：同一 autoType 修复在 git 历史出现 7 次，2.0.65 又发现 2.0.63
   修复可被 hash-cache 命中绕过——需用版本考古而非单点扫描发现。

---

## 1. 关键缺陷

### 1.1 CWE-502 AutoType hash 白名单绕过（语义逻辑缺陷，规则库无法表达）

**现象（fastjson2 2.0.62，`ObjectReaderProvider.checkAutoType`）**：
```java
if (Arrays.binarySearch(acceptHashCodes, hash) >= 0) {   // 只比 64 位滚动 hash
    clazz = loadClass(typeName);                          // 加载"攻击者类名"而非白名单类
    if (clazz != null) { ... return clazz; }              // 无完整类名文本校验
}
```
- 硬编码 hash `-6293031534589903644L`（`com.alibaba.fastjson.util.AntiCollisionHashMap` 的
  FNV 前像）常驻 acceptHashCodes → 任意与该 hash 前缀碰撞的类名都被放行。
- 非 SupportAutoType 分支缺 ClassLoader/DataSource/RowSet 黑名单（黑白名单不对称）。
- 修复 commit（2.0.63 `ec47e24c4`）才补上 `acceptNameSet.contains(完整类名)` 文本校验。

**skill 缺陷**：L0 扫描 12341 候选、CWE-502 1616 条，但**全部命中 `JSON.java` 的
`readObject` 入口**（如 CAND-3264），`checkAutoType`/`loadClass`/`newInstance` 零命中。
CWE-78 140 条全是噪音。**该漏洞 100% 靠 git diff 定位，非规则库定位。**

**根因**：Java 反序列化授权逻辑（`@type` → 白名单 → `loadClass` → `newInstance`）是
"危险谓词"，不是"危险函数"。CodeQL 的 `UnsafeDeserialization` 能表达 class-path 层，
但"hash-only 校验"这类语义需要专门 pattern。

### 1.2 "修复-再暴露"循环（版本考古才能发现）

- 2.0.63 修复（`ec47e24c4`）→ 2.0.65 又加 `e2bde524c` "unify AutoType authorization to
  type name and **reject hash-cache hit**"——2.0.63 的文本校验仍可被 hash-cache 命中绕过，
  即一次"修复后被绕、再修"。
- 同标题修复在 git 历史出现 **7 次**（3 轮 review 跟进 + android 分支 backport）。

**skill 缺陷**：单点扫描（无论 L0/R3/R4）无法发现"修复是否被后续绕过"；只有 R0.5 阶段
（`git log --grep=autotype` + `diff parent..commit` 提取守卫特征）能定位。

### 1.3 CWE-78 伪通用噪音（语言适配缺失）

**现象（fastjson2 全库）**：
- `Frame.execute`（ASM 字节码解释器）、`JCTree.exec`（javac AST 构建）——140 条 CWE-78
  候选全部为框架内部方法名。
- Java `exec`/`execute` 是高频方法名，与 C 的 `exec*` 裸系统调用语义完全不同。

**根因**：Java 规则 CWE-78 的 regex `exec\s*\(`/`execute\s*\(` 无接收者限定。必须限定
`Runtime.exec` / `ProcessBuilder`，并排除 `Frame`/`JCTree`/`ASM` 等内部类。

---

## 2. 当前版本（2.0.65-dev）残余风险面（供 R4 假说参考）

| 残留点 | 位置 | 状态 |
|---|---|---|
| `autoTypeSupport=true` + `expectClass==null` 时最终 `loadClass` 路径仅靠 denyList | `ObjectReaderProvider.java:958-976` | `isAutoTypeDenyClass` 仅含 ClassLoader 子类 + SQL DataSource/RowSet（`JDKUtils.java:468`）；TemplatesImpl/c3p0/spring/HikariCP 等 gadget 不在 deny 内 |
| `TypeUtils.getMapping` 路径无 deny 检查 | `ObjectReaderProvider.java:938-945` | 仅 expectClass 校验 |
| `GenericFastJsonRedisSerializer()` 无参构造仍默认 `SupportAutoType` | `extension-spring6/.../GenericFastJsonRedisSerializer.java:25` | 默认 Spring 配置无白名单 + autoType 开 |

**结论**：2.0.63/2.0.65 修掉 hash 伪造/前缀碰撞/hash-cache 三个具体绕过，但 deny-list
模型非封闭白名单——Redis 投毒 + 非 deny 的 classpath gadget → RCE 面仍在。

---

## 3. 建议改进（已进入 v2.1）

- **P0**：Java 规则库新增 `LOGIC_PATTERN` 危险谓词规则：
  `binarySearch(hashCodes, hash) >= 0` → `loadClass`（hash-only 白名单）; `expectClass==null`
  分支跳过黑名单; `getMapping` 路径缺 deny 检查。
- **P1**：CWE-78 接收者限定 `Runtime.exec`/`ProcessBuilder`，排除 ASM/javac 内部类（REQ-28）。
- **P1**：新增 Java 锚点：`checkAutoType` hash 白名单（fastjson2）、`Class.forName(n).newInstance()`
  （Drupalgeddon2）、`Runtime.getRuntime().exec`（CVE-2016-5734）——已入 `anchor_registry.json`。
- **P1**：R0.5 考古对"迭代修 N 轮"的库（AutoType/RCE 类）优先执行，产出高于静态规则阶段。

---

## 4. 建议后续验证目标

| 项目 | 版本 | Ground truth CVE | 规则面 |
|---|---|---|---|
| fastjson2 | 2.0.62 | AutoType hash 白名单绕过（checkAutoType:834） | CWE-502 LOGIC_PATTERN |
| fastjson1 | 1.2.84 | AutoType 多轮绕过（CVE-2022-25845） | CWE-502 |
| Drupal 8.3.x | <8.3.9 | CVE-2018-7600（unserialize gadget RCE） | CWE-502 |
| phpMyAdmin | 4.8.5 | CVE-2018-12613（LFI→RCE，PHP 侧） | CWE-98 |
