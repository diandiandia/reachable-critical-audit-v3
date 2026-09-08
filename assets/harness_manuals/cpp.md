# C++ 实证工具链手册 (v3.3.1)

> 与 c.md 同族（继承 §1 工具链探测/§2 版本义务/§3 陷阱清单的 C 通用条目），
> 本文档仅列 C++ 特有项。C++ 首审前以 c.md 为主手册、本文件为增量。

## 1. 工具链探测（C++ 特有）
- g++ 与 ASan/UBSan：`g++ -fsanitize=address,undefined -g -O1` 覆盖裸 new/new[]
  越界与容器 OOB；STL 容器 bug 需 `-D_GLIBCXX_ASSERTIONS`（libstdc++ 断言模式）
- 探测命令：`g++ --version && gcc --version && make --version`

## 2. 陷阱清单（C++ 特有）
- **容器无界增长 ≠ 裸分配**：vector push_back/resize 的 RSS 增长走 allocator
  复用路径，峰值提交内存常呈 1.5-2x 阶梯而非线性——实证采样必须记录
  容量/大小双曲线（capacity() vs size()），否则「无界累积」判定证据不足
- **new 失败语义**：默认 `new` 抛 bad_alloc（非返回 NULL）——harness 判
  「干净失败」时应捕获异常而非检查空指针；`new (nothrow)` 形态另当别论
- **虚函数表/OOP 多态路径**：verifier 步骤 2 的多态穿透在 C++ 需展开
  vtable 实现类（.cpp 内 override），grep 调用点只命中基类名会漏掉子类实现
- **RAII 与生命周期**：分配类声称在 C++ 须核查析构路径——std::unique_ptr/
  容器析构自动释放使「泄漏/无界」判定与 C 不同（R3.5 证伪者重点攻击面）

## 3. 阳性模式
- ASan + UBSan 组合实测为 C++ 解析器类声称的标准证据链（同 c.md parser_fuzz
  模板，编译命令换 g++）
- 分配放大类实证优先 strace mmap 捕获 + /proc/self/status VmPeak 采样
  （同 PREC-ALLOC-VIRTUAL-001：提交内存 vs 虚拟分配分离判定）
