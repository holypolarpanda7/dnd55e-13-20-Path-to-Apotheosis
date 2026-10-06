"""Boon of Siberys spell pool (Eberron: Forge of the Artificer; 2026-10-05) -> Scripts/data/siberys_spells.json.

Aberrant Magic offers a level 1-8 Sorcerer spell or a Siberys Dragonmark Spells table spell. Pool: the cumulative Sorcerer
level 1-8 learn list as the game loads it (gen_learn_lists.py, MergedInto included) plus the table's twelve spells. Container
spells are left out, as for Boon of Magic School Mastery (a no-slot copy of a container's children isn't possible).
gen_epic_boons.py reads the JSON; rerun this after the Sorcerer lists change:
    bg3-data refresh apotheosis; UV_PROJECT_ENVIRONMENT=~/.cache/bg3-data-mcp/venv uv run --project ../bg3-data-mcp \
        python Scripts/export_siberys_spells.py
"""
import datetime
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "bg3-data-mcp"))
from bg3data import query  # noqa: E402

SORCERER_1_8 = "00180002-0001-0001-0001-000000000002"
# the Siberys Dragonmark Spells table (suggested mark in the comment)
TABLE = ["Shout_Apo_AnimalShapes",    # Handling
         "Shout_Apo_ControlWeather",  # Storm
         "Target_Apo_Demiplane",      # Making
         "Shout_HeroesFeast",         # Hospitality
         "Target_Apo_Maze",           # Warding
         "Target_Apo_MindBlank",      # Sentinel
         "Target_Apo_PlaneShift",     # Passage
         "Target_ProjectImage",       # Shadow
         "Target_Regenerate",         # Healing
         "Target_Apo_Symbol",         # Scribing
         "Target_Apo_Teleport",       # Finding
         "Target_TrueSeeing"]         # Detection


def main():
    s = query.Store(refresh=False)
    act = s.active(None)
    pool = s.runtime_list_spells(SORCERER_1_8, act)
    spells, skipped = {}, []
    for n in pool + [t for t in TABLE if t not in pool]:
        r = s.resolve(n, act)
        assert r, n
        f = {k: v for k, (v, _) in r["fields"].items()}
        if f.get("ContainerSpells"):
            skipped.append(n)
            continue
        spells[n] = {"name": s.display_name(r["fields"], act), "level": int(f["Level"]), "costs": f.get("UseCosts", ""),
                     "flags": f.get("SpellFlags", ""), "table": n in TABLE}
    json.dump({"generated": f"{datetime.date.today()} from the Sorcerer L1-8 learn list + the Siberys Dragonmark Spells table (bg3-data-mcp)",
               "skipped_containers": sorted(skipped), "spells": dict(sorted(spells.items()))},
              open(os.path.join(REPO, "Scripts", "data", "siberys_spells.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"{len(spells)} spells ({sum(v['table'] for v in spells.values())} from the table), {len(skipped)} containers skipped")


if __name__ == "__main__":
    main()
