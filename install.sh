#!/bin/bash
# 从 v3 开发主仓库安装到 Claude skill 目录
# 用法: ./install.sh [目标目录]   (默认 /root/.claude/skills/reachable-critical-audit)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
ALLOW_DIRTY=0
if [ "${1:-}" = "--allow-dirty" ]; then ALLOW_DIRTY=1; shift; fi
DST="${1:-/root/.claude/skills/reachable-critical-audit}"

# v3.26 (SWR-V3.26-001): dev 仓库未提交改动静默上运行时是漂移温床
# (前周期欠账实录: 未提交矩阵文件已装至运行时; warn 级防线 v3.16→v3.22
# 复发史证明不足)。拒绝安装, --allow-dirty 显式豁免; 非 git 仓库跳过。
check_git_clean() {
  git -C "$SRC" rev-parse --git-dir >/dev/null 2>&1 || return 0
  if [ "$ALLOW_DIRTY" = 1 ]; then return 0; fi
  local dirty
  dirty="$(git -C "$SRC" status --porcelain)"
  if [ -z "$dirty" ]; then return 0; fi
  echo "拒绝安装: dev 仓库工作树有未提交改动 (提交后重装, 或 --allow-dirty 显式豁免):" >&2
  echo "$dirty" >&2
  exit 1
}
check_git_clean

echo "安装 v3 skill: $SRC -> $DST"

mkdir -p "$DST/src" "$DST/tools" "$DST/assets" "$DST/tests" "$DST/docs/legacy"

# v3.34 分层: L1 src/ 运行时核心, L2 tools/ 阶段 CLI, L3 assets/ 知识资产
# (安装目录与开发仓库保持一致; .venv 不随安装管理)
cp "$SRC"/SKILL.md "$DST/"
cp "$SRC"/README.md "$DST/"
cp "$SRC"/docs/legacy/SKILL_V2.1.md "$DST/docs/legacy/"
cp -r "$SRC"/src/. "$DST/src/"
cp -r "$SRC"/tools/. "$DST/tools/"
cp -r "$SRC"/assets/. "$DST/assets/"
cp -r "$SRC"/tests/. "$DST/tests/"

# 清理安装目录中已在开发仓库删除的文件 (保持单一权威)
for d in src tools assets tests docs; do
  find "$DST/$d" -type f | while read -r f; do
    rel="${f#$DST/$d/}"
    [ -e "$SRC/$d/$rel" ] || rm -f "$f"
  done
done
# v3.34 分层迁移清理: 移除 v3.33 及更早平铺形态的残留 (顶层 .py 与
# 旧资产目录已迁入 src//assets/; 遗留文件会造成双副本漂移与 SKILL.md
# 路径歧义——单一权威只认新层位)
find "$DST" -maxdepth 1 -name "*.py" | while read -r f; do
  [ -e "$SRC/src/$(basename "$f")" ] || rm -f "$f"
done
for legacy in harness_manuals lessons resources task_templates templates; do
  if [ ! -e "$SRC/$legacy" ] && [ -d "$DST/$legacy" ]; then
    rm -rf "$DST/$legacy"
  fi
done
# v3.2.3: 顶层 SKILL_V2.1.md 为 v2.1 时代陈旧重复 (权威副本在 docs/legacy/)
[ -e "$DST/SKILL_V2.1.md" ] && rm -f "$DST/SKILL_V2.1.md"

# 清理缓存
find "$DST" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 冒烟验证 (安装后的位置跑测试)
PY="${PYTHON_BIN:-$DST/.venv/bin/python3}"
[ -x "$PY" ] || PY="python3"
"$PY" -m pytest "$DST/tests/" -q --ignore="$DST/tests/legacy_v2" 2>/dev/null \
  && echo "✓ 安装完成, 测试全绿" \
  || echo "✓ 安装完成 (测试未运行/未全绿, 请手动验证: $PY -m pytest $DST/tests/)"
