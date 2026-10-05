"""Level-map scalings past 12 (2026-10-03). Base BG3 and dnd55e level maps stop at 12, so Sneak Attack, Martial Arts,
Rage damage, Bardic Inspiration, cantrip dice, Eldritch Blast beams... never grew past 12. Each series is copied from
its current top layer (base or dnd55e, read from the bg3-data MCP index) with the PHB 2024 steps above 12 added, and
overrides that series by UUID. Levels 1-12 follow dnd55e except where FIX below restores the PHB 2024 schedule (dnd55e/base compress some steps to
fit the 12-level cap: owner decision 2026-10-03, "restore PHB 2024 values").

Owns LevelMapValues.lsx between LEVELMAPS 13-20 markers.
Run: python3 Scripts/gen_levelmaps.py
"""
import json
import os
import sqlite3

from gen_common import Gen

G = Gen("levelmaps", "LEVELMAPS 13-20")
DB = os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite")

ADD = {  # series name -> {level: value} (2024 rules)
    "DragonShapeBreath": {14: "5d6"},                          # Circle of Dragons breath at 14 (Griffon's Saddlebag)
    "SneakAttack": {15: "8d6", 17: "9d6", 19: "10d6"},        # Rogue: (level + 1) / 2 d6
    "MartialArts": {17: "1d12"},                               # Monk die d12 at 17
    "RageDamage": {16: "4"},                                   # Rage damage +4 at 16
    "RageDamageThrown": {16: "8"},                             # the base game's doubled thrown rage damage
    "BardicInspiration": {15: "1d12"},                         # Bardic Inspiration d12 at 15
    "D4Cantrip": {17: "4d4"}, "D6Cantrip": {17: "4d6"}, "D8Cantrip": {17: "4d8"}, "D10Cantrip": {17: "4d10"},
    "D12Cantrip": {17: "4d12"}, "D8CantripCleric": {17: "4d8"},  # cantrip damage: four dice at 17
    "EldritchBlast": {17: "4"},                                # four beams at 17
    "TrueStrike": {17: "3d6"},                                 # True Strike extra Radiant 3d6 at 17
    "BoomingBlade": {17: "3d8"}, "BoomingBlade_Walk": {17: "4d8"},
    "Soulknife": {17: "1d12"}, "PsiWarrior": {17: "1d12"},     # Psionic Energy die d12 at 17
    "ProficiencyBonusD4": {13: "5d4", 17: "6d4"},              # a d4 per point of Proficiency Bonus
    "HaloOfSpores": {14: "1d10"},                              # TCoE: 1d10 at 14
    "BreathWeapon": {17: "4d10"},                              # Dragonborn 2024: 4d10 at 17
}


FIX = {  # PHB 2024 steps that base/dnd55e compress below 13: name -> {level: value, None = drop that level}
    "SneakAttack": {11: "6d6", 13: "7d6"},                     # (level + 1) / 2 d6; dnd55e jumps to 7d6 at 11
    "LandsAid": {5: None, 10: "3d6", 14: "4d6"},                # Circle of the Land: 2d6, 3d6 at 10, 4d6 at 14
}
MOVE_10_TO_11 = ["D4Cantrip", "D6Cantrip", "D8Cantrip", "D10Cantrip", "D12Cantrip", "D8CantripCleric", "EldritchBlast",
                 "TrueStrike", "BoomingBlade", "BoomingBlade_Walk", "BreathWeapon"]  # third tier at 11, not 10


def apply_fix(levels, lvl, val):
    """Set a step (None = drop it). A level without an entry takes the nearest lower one, so steps are all that matter."""
    if val is None:
        levels.pop(lvl, None)
    else:
        levels[lvl] = val


def current(name):
    con = sqlite3.connect(DB)
    row = con.execute("SELECT uuid, attrs FROM staticdata WHERE kind LIKE 'LevelMap%' AND name=? AND layer != 'apotheosis' "
                      "ORDER BY rank DESC LIMIT 1", (name,)).fetchone()
    assert row, f"level map {name} not found"
    a = json.loads(row[1])
    levels = {int(k[5:]): v for k, v in a.items() if k.startswith("Level") and k[5:].isdigit()}
    return row[0], levels, a.get("PreferredClassUUID")


if __name__ == "__main__":
    for name, extra in ADD.items():
        uuid_, levels, cls = current(name)
        if name in MOVE_10_TO_11:
            lower = [k for k in levels if k < 10]
            prev = levels[max(lower)]  # the tier in force before level 10 (a level without an entry takes the nearest lower)
            assert 10 in levels and levels[10] != prev, f"{name}: no tier step at 10 ({levels})"
            step = levels[10]
            if 9 in levels:
                levels[10] = prev  # dense map: level 10 keeps the previous tier
            else:
                del levels[10]  # sparse map: the lower entry carries
            levels[11] = step  # the tier lands at 11; a dense map's 12 already holds it
        for lvl, val in FIX.get(name, {}).items():
            apply_fix(levels, lvl, val)
        assert max(levels) < min(extra), f"{name} already reaches {max(levels)}"
        G.levelmap(name, uuid_, {**levels, **extra}, cls)
    for name in FIX:  # fixed series that get no 13-20 additions
        if name not in ADD:
            uuid_, levels, cls = current(name)
            for lvl, val in FIX[name].items():
                apply_fix(levels, lvl, val)
            G.levelmap(name, uuid_, levels, cls)
    G.patch_files()
    print(f"{len(ADD)} level maps extended past 12; PHB 2024 steps restored for "
          f"{len(set(FIX) | set(MOVE_10_TO_11))} series")
