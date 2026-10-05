#!/usr/bin/env bash
# Regenerate every generated file from the generators (2026-10-03). Run after a dependency update (bg3_deps_update
# runs it via layers.json `regen`) or whenever the generators change. dnd55e is read as released: the dependency pak
# extracted by the bg3-data MCP (see Scripts/gen_common.py DND, bg3deps.lock.json).
set -euo pipefail
cd "$(dirname "$0")/.."
MCP="$(cd .. && pwd)/bg3-data-mcp"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.cache/bg3-data-mcp/venv}"
for g in gen_spells_2024 generate_level79_spells gen_true_polymorph gen_indomitable_might gen_summons \
         gen_class_features gen_subclass_features gen_subclass_spells gen_epic_boons gen_gunslinger gen_illrigger \
         gen_levelmaps; do
  echo "== $g"; python3 "Scripts/$g.py" | tail -2
done
uv run --project "$MCP" bg3-data refresh apotheosis > /dev/null  # gen_upcasts reads the index (incl. the files above)
echo "== gen_upcasts"; python3 Scripts/gen_upcasts.py | grep -v '^WARN' | tail -3
echo "== gen_spell_mastery_containers"; python3 Scripts/gen_spell_mastery_containers.py
echo "== apply_icons"; python3 Scripts/apply_icons.py
