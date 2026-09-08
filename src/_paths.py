"""分层路径单一事实源 (v3.34 文件分层重构)。

层结构:
    L0 SKILL.md / install.sh     契约与安装层
    L1 src/                      运行时核心 (本模块所在层)
    L2 tools/                    阶段驱动 CLI
    L3 assets/                   知识资产 (只读)
    L4 tests/                    验证层
    L5 docs/                     文档层

依赖方向铁律: L2 → L1 单向; assets 只被 L1/L2 读, 永不写。
所有运行时资源路径必须经本模块派生, 禁止模块内硬编码相对层位
(第一原则三禁止③: 相对推导, 零绝对路径)。
"""
import os

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
RESOURCES_DIR = os.path.join(ASSETS_DIR, "resources")
