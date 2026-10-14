"""Class resource curves 1-20 (2026-10-03): sums ActionResource(X,n,0) boosts from class progressions (node Boosts and
their passives' Boosts, last layer wins per node) and prints the levels where the total changes, for the 2024
resources that keep growing past 12. Reads the bg3-data MCP index.
Run: python3 Scripts/resource_audit.py"""
import json
import os
import re
import sqlite3

con = sqlite3.connect(os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite"))
pboost = {}
for name, data in con.execute("SELECT name, data FROM stats WHERE type='PassiveData' ORDER BY rank"):
    b = json.loads(data).get("Boosts")
    if b is not None:
        pboost[name] = b
EXPECT = {  # class: {resource: {level: total}} - 2024 values at 13-20 (and the last value before 13)
    "Monk": {"KiPoint": {12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20}},
    "Sorcerer": {"SorceryPoint": {12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20}},
    "Barbarian": {"Rage": {12: 5, 17: 6}},
    "Druid": {"WildShape": {12: 3, 17: 4}},
    "Cleric": {"ChannelDivinity": {12: 3, 18: 4}},
    "Ranger": {"FavoredEnemy": {12: 4, 13: 5, 16: 5, 17: 6}},
    "Wizard": {"ArcaneRecoveryPoint": {12: 6, 13: 7, 15: 8, 17: 9, 19: 10}},
    # subclass / class / species pools (2026-10-13, gen_class_resources.py; node names, not class names)
    "Celestial": {"HealingLight": {L: L + 1 for L in range(12, 21)}},                       # 1 + Warlock level d6s
    "CircleOfDreams": {"Balm": {L: L for L in range(12, 21)}},                              # d6s = Druid level
    "CircleOfTheLand": {"NaturalRecoveryPoint": {L: -(-L // 2) for L in range(12, 21)}},    # half the Druid level, rounded up
    "ZealotPath": {"WarriorOfTheGods": {12: 6, 16: 6, 17: 7}},
    "Alchemist": {"ExperimentalElixir": {12: 4, 14: 4, 15: 5}},
    "Artificer": {"ReplicateMagicItem": {12: 4, 13: 4, 14: 5, 17: 5, 18: 6}},
    "RuneKnight": {"Rune": {12: 5, 14: 5, 15: 6}, "RunicShield": {12: 4, 13: 5, 16: 5, 17: 6}},
    "PsiWarrior": {"PsiWarrior": {12: 8, 13: 10, 16: 10, 17: 12}},                          # twice the Proficiency Bonus
    "Soulknife": {"Soulknife": {12: 8, 13: 10, 16: 10, 17: 12}},
    "Swarmkeeper": {"WrithingTidePoint": {12: 4, 13: 5, 16: 5, 17: 6}},
    "Dragonborn": {"BreathWeapon": {12: 4, 13: 5, 16: 5, 17: 6}},                           # Proficiency Bonus uses
    "Eladrin": {"Eladrin": {12: 4, 13: 5, 17: 6}}, "Goliath": {"Goliath": {12: 4, 13: 5, 17: 6}},
    "ShadarKai": {"ShadarKai": {12: 4, 13: 5, 17: 6}},
    "Fighter": {"Interrupt_Indomitable": {12: 1, 13: 2, 17: 3}},
    # not counted here: Action Surge (a once-per-Short-Rest cooldown; the second use at 17 is its own spell) and
    # dnd55e's Lay on Hands (its own charge model, not the 5 x level pool)
}

EXPECT_STEP = {   # name: {resource: {level: increase over the level before}} - for tables where base game and dnd55e nodes stack
    "AbjurationSchool": {"ArcaneWard": {L: 2 for L in range(13, 21)}},   # 2 x Wizard level (+ Int modifier)
}


def totals(cls):
    nodes = {}
    for uuid, level, attrs in con.execute("SELECT uuid, level, attrs FROM prog WHERE name=? ORDER BY rank", (cls,)):
        a = json.loads(attrs)
        if str(a.get("IsMulticlass", "")).lower() == "true":
            continue
        nodes[uuid] = (int(level), a)
    run, out = {}, {}
    for L in range(1, 21):
        for lv, a in nodes.values():
            if lv != L:
                continue
            text = a.get("Boosts") or ""
            for p in [x for x in (a.get("PassivesAdded") or "").split(";") if x]:
                text += ";" + pboost.get(p, "")
            for res, n in re.findall(r"ActionResource\((\w+),\s*(\d+),\s*0\)", text):
                run[res] = run.get(res, 0) + int(n)
        out[L] = dict(run)
    return out


bad = 0
# passives whose uses follow the Proficiency Bonus (CharacterLevelGreaterThan(4) / (8) steps) must go on to (12) and (16)
for name, boosts in sorted(pboost.items()):
    if "CharacterLevelGreaterThan(8)" in boosts and "ActionResource" in boosts and "CharacterLevelGreaterThan(12)" not in boosts:
        bad += 1
        print(f"passive {name}: Proficiency Bonus steps stop at +4 (no CharacterLevelGreaterThan(12))")
for cls, resources in EXPECT.items():
    t = totals(cls)
    for res, want in resources.items():
        for L, v in want.items():
            have = t[L].get(res, 0)
            if have != v:
                bad += 1
                print(f"{cls:10s} {res:18s} L{L:2d}: has {have}, want {v}")
for cls, resources in EXPECT_STEP.items():
    t = totals(cls)
    for res, want in resources.items():
        for L, v in want.items():
            have = t[L].get(res, 0) - t[L - 1].get(res, 0)
            if have != v:
                bad += 1
                print(f"{cls:10s} {res:18s} L{L:2d}: grows by {have}, want {v}")
print(f"{bad} mismatches")
