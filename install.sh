#!/bin/bash
# 从 v3 开发主仓库安装到 Claude skill 目录
# 用法: ./install.sh [目标目录]   (默认 /root/.claude/skills/reachable-critical-audit)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DST="${1:-/root/.claude/skills/reachable-critical-audit}"

echo "安装 v3 skill: $SRC -> $DST"

mkdir -p "$DST/tools" "$DST/resources" "$DST/task_templates" "$DST/templates" "$DST/tests" "$DST/lessons" "$DST/harness_manuals" "$DST/docs/legacy"

# 运行时 + 规范 (安装目录与开发仓库保持一致; .venv 不随安装管理)
cp "$SRC"/SKILL.md "$DST/"
cp "$SRC"/README.md "$DST/"
cp "$SRC"/docs/legacy/SKILL_V2.1.md "$DST/docs/legacy/"
cp "$SRC"/surface_mapper.py "$SRC"/signature_lib.py "$SRC"/signature_matcher.py \
   "$SRC"/evidence_ledger.py "$SRC"/harness_runner.py "$SRC"/workflow_export.py \
   "$SRC"/checklist_binder.py "$SRC"/precedent_library.py "$SRC"/r2_guard.py \
   "$SRC"/lessons_recorder.py "$DST/"
cp -r "$SRC"/tools/. "$DST/tools/"
cp -r "$SRC"/resources/. "$DST/resources/"
cp -r "$SRC"/task_templates/. "$DST/task_templates/"
cp -r "$SRC"/templates/. "$DST/templates/"
cp -r "$SRC"/tests/. "$DST/tests/"
cp -r "$SRC"/lessons/. "$DST/lessons/"
cp -r "$SRC"/harness_manuals/. "$DST/harness_manuals/"

# 清理安装目录中已在开发仓库删除的文件 (保持单一权威)
for d in tools resources task_templates templates tests lessons harness_manuals docs; do
  find "$DST/$d" -type f | while read -r f; do
    rel="${f#$DST/$d/}"
    [ -e "$SRC/$d/$rel" ] || rm -f "$f"
  done
done
find "$DST" -maxdepth 1 -name "*.py" | while read -r f; do
  [ -e "$SRC/$(basename "$f")" ] || rm -f "$f"
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
