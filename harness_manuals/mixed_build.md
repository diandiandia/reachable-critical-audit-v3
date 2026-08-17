# 混合项目实证工具链手册 (v3.2)

> 适用：language_inventory ≥2 的项目。单语言项目用对应语言的 <lang>.md。

## 1. 组件级构建矩阵（实证前置）
- 每组件一行: {lang, build_cmd, 产物, 测试入口}——先按组件分别验证构建，
  再组装跨语言场景（避免"整仓构建失败不知何组件"）

## 2. 跨语言实证编排
- 宿主进程 + 动态库加载: C 核心编译 .so/.dll → Python ctypes / Rust cdylib 驱动
- 双向探针: 边界两侧各放插桩（RSS/引用计数/析构时序），交叉对表
- 顺序建议: 先单侧机制级（各语言手册阳性模式）→ 再边界级 E2E

## 3. FFI harness 模板
- ctypes 驱动 C 核心: `ctypes.CDLL(path)` + argtypes/restype 显式声明（缺省 c_int
  截断是高频缺陷源）→ 畸形输入矩阵 + 释放责任观测（Valgrind/ASan 两侧）
- cargo cdylib + Python 导入: maturin/pyo3 产物 import 后跑 pytest 探针
- 嵌入场景: CPython 嵌入 C 的引用计数配平探针（借出/归还计数差）

## 4. 常见陷阱
- ctypes 默认 argtypes 未声明 → 64 位指针截断
- 跨语言字符串编码（UTF-8 vs wchar vs 平台默认）
- 释放责任错配（Python 侧 free 了 C 侧 malloc 的内存）
- 两侧编译优化级别不一致导致的 ABI 行为差异
