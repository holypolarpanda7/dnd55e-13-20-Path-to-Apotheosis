"""Hit Point Dice at levels 13-20 (2026-10-12). PHB 2024: you have one Hit Point Die per character level. dnd55e grants them per
class level as action resources (HitPointDice06/08/10/12) up to 12 for the twelve base classes (its own Artificer, Gunslinger,
Illrigger and Monster Hunter tables already go to 20); without these a level-20 character had 12 dice - short rests, and
everything that spends Hit Point Dice (Sangromancy spells, Sangromancer's Red Renewal), came up short.

One hidden passive per class, added at its level-13 node, grants one die of the class's size for each class level from 13 on:
IF(ClassLevelHigherOrEqualThan(N,'Class')):ActionResource(HitPointDiceXX,1,0) - the conditional-boost form dnd55e's own
ShortResting passive uses. The level-13 nodes are rewritten in full by other generators, so this one appends
(gen_common.append_progressions) and runs after them in regen_all.sh.

Owns Stats/Generated/Data/Passive_HitDice.txt and its loca.
Run: python3 Scripts/gen_hit_dice.py
"""
from gen_common import Gen, append_progressions

G = Gen("hitdice", "HIT DICE 13-20")
CLASSES = {  # class: (hit die, its level-13 node in Progressions.lsx)
    "Barbarian": (12, "11111111-1111-1111-1111-111111111101"), "Bard": (8, "99999999-9999-9999-9999-999999999901"),
    "Cleric": (8, "77777777-7777-7777-7777-777777777701"), "Druid": (8, "88888888-8888-8888-8888-888888888801"),
    "Fighter": (10, "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"), "Monk": (8, "22222222-2222-2222-2222-222222222201"),
    "Paladin": (10, "44444444-4444-4444-4444-444444444401"), "Ranger": (10, "55555555-5555-5555-5555-555555555501"),
    "Rogue": (8, "33333333-3333-3333-3333-333333333301"), "Sorcerer": (6, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaa901"),
    "Warlock": (8, "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbb901"), "Wizard": (6, "66666666-6666-6666-6666-666666666601"),
}
ADDS = {}
for cls, (die, node) in CLASSES.items():
    name = f"Apo_HitPointDice_{cls}"
    res = f"HitPointDice{die:02d}"
    G.passive(name, "Hit Point Dice", f"One d{die} Hit Point Die for each {cls} level from 13 on.",
              {"Boosts": ";".join(f"IF(ClassLevelHigherOrEqualThan({n},'{cls}')):ActionResource({res},1,0)" for n in range(13, 21))},
              icon=f"HitPointDice{die:02d}", hidden=True)
    ADDS[node] = {"PassivesAdded": name}


if __name__ == "__main__":
    G.write_stats("HitDice", "gen_hit_dice.py", "Hit Point Dice 13-20")
    G.patch_loca()
    append_progressions(ADDS)
    print(f"{len(G.P)} passives, {len(ADDS)} level-13 nodes")
