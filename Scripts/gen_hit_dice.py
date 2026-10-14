"""Hit Point Dice at levels 13-20 (2026-10-12; reworked 2026-10-13). PHB 2024: you have one Hit Point Die per character level.
dnd55e grants them per class level as action resources (HitPointDice06/08/10/12) up to 12 for the twelve base classes (its own
Artificer, Gunslinger, Illrigger and Monster Hunter tables already go to 20); without these a level-20 character had 12 dice -
short rests, and everything that spends Hit Point Dice (Sangromancy spells, Sangromancer's Red Renewal), came up short.

Each class's level 13-20 progression nodes get one ActionResource(HitPointDiceXX,1,0) boost, applied at that level-up - and so
does every lower-level dnd55e node PTA overrides (an override replaces the node, dnd55e's die with it). The first
version was one passive with IF(ClassLevelHigherOrEqualThan(N,...)) boosts: the game evaluates those conditions when the passive
is applied (and on a save load), not on level-up, so a Wizard 14 had 13 d6 until the next load (2026-10-13; the level check now
tests the rule). The nodes are rewritten in full by other generators, so this appends (gen_common.append_progressions) and runs
after them in regen_all.sh.

The same per-node way carries the other class resources dnd55e stopped growing at 12 (found by Scripts/resource_audit.py
2026-10-13): Ranger Favored Enemy (5 at 13, 6 at 17) and Wizard Arcane Recovery (half the level, rounded up: 7/8/9/10 at 13/15/17/19).

Run: python3 Scripts/gen_hit_dice.py
"""
import os
import re

from gen_common import Gen, PUB, append_progressions

G = Gen("hitdice", "HIT DICE 13-20")   # no stats of its own any more: write_stats removes the old Passive_HitDice.txt
CLASSES = {  # class: (hit die, its level-13 node in Progressions.lsx - the class's table is read from it)
    "Barbarian": (12, "11111111-1111-1111-1111-111111111101"), "Bard": (8, "99999999-9999-9999-9999-999999999901"),
    "Cleric": (8, "77777777-7777-7777-7777-777777777701"), "Druid": (8, "88888888-8888-8888-8888-888888888801"),
    "Fighter": (10, "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"), "Monk": (8, "22222222-2222-2222-2222-222222222201"),
    "Paladin": (10, "44444444-4444-4444-4444-444444444401"), "Ranger": (10, "55555555-5555-5555-5555-555555555501"),
    "Rogue": (8, "33333333-3333-3333-3333-333333333301"), "Sorcerer": (6, "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaa901"),
    "Warlock": (8, "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbb901"), "Wizard": (6, "66666666-6666-6666-6666-666666666601"),
}
RESOURCES = {  # (class, level): extra boost on that level's node (PHB 2024 tables)
    ("Ranger", 13): "ActionResource(FavoredEnemy,1,0)", ("Ranger", 17): "ActionResource(FavoredEnemy,1,0)",
    **{("Wizard", L): "ActionResource(ArcaneRecoveryPoint,1,0)" for L in (13, 15, 17, 19)},
}
ATTR = lambda k, b: (re.search(rf'id="{k}" type="[^"]*" value="([^"]*)"', b) or [None, None])[1]


def class_nodes():
    """{node uuid: (class, level)} for each class's nodes in PTA's Progressions.lsx (same table as its level-13 node): levels
    13-20 and every dnd55e node PTA overrides."""
    s = open(os.path.join(PUB, "Progressions", "Progressions.lsx"), encoding="utf-8").read()
    # nodes other generators add on top of a class (gen_class_resources.py: Monk 14 / 18 Unarmored Movement ...) are not level nodes of
    # their own: they would get a second Hit Point Die
    s = re.sub(r"[ \t]*<!-- (CLASS RESOURCES 13-20|ARTIFICER PLANS 14|WILD SHAPE FORMS) BEGIN.*?<!-- \1 END -->\n", "", s, flags=re.S)
    nodes = re.findall(r'<node id="Progression">.*?</node>', s, re.S)
    by_uuid = {ATTR("UUID", b): b for b in nodes}
    out = {}
    for cls, (_die, l13) in CLASSES.items():
        table = ATTR("TableUUID", by_uuid[l13])
        # 13-20 are PTA's own nodes; below 13 PTA's file only holds nodes it overrides from dnd55e - and an override replaces
        # dnd55e's whole node, Hit Point Die included (Barbarian and Cleric 12 had 11 dice, 2026-10-13), so those get it back too
        mine = [(int(ATTR("Level", b) or 0), ATTR("UUID", b), ATTR("IsMulticlass", b) or "False") for b in nodes
                if ATTR("TableUUID", b) == table and ATTR("Name", b) == cls and 1 <= int(ATTR("Level", b) or 0) <= 20]
        missing = sorted(set(range(13, 21)) - {n for n, _u, mc in mine if mc != "True"})
        assert not missing, f"{cls}: no progression node for levels {missing}"
        out.update({u: (cls, n) for n, u, _mc in mine})
    return out


def drop_old_passive():
    """The first version's Apo_HitPointDice_<class> passives: out of PassivesAdded (nodes no other generator rewrites kept them)
    and out of the loca."""
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()

    def clean(m):
        keep = [x for x in m.group(2).split(";") if x and not x.startswith("Apo_HitPointDice_")]
        return f'{m.group(1)}{";".join(keep)}"/>' if keep else ""
    s = re.sub(r'(<attribute id="PassivesAdded" type="LSString" value=")([^"]*Apo_HitPointDice_[^"]*)"/>', clean, s)
    s = re.sub(r'\n[ \t]*(?=\n)', "", s)    # the line an emptied attribute left
    open(path, "w", encoding="utf-8", newline="").write(s)
    import glob
    for loca in glob.glob(os.path.join(os.path.dirname(PUB), "..", "Mods", "*", "Localization", "English", "*.xml")):
        t = open(loca, encoding="utf-8").read()
        t2 = re.sub(r'[ \t]*<content contentuid="[^"]*" version="\d+">(Hit Point Dice|One d\d+ Hit Point Die for each \w+ level from 13 on\.)</content>\r?\n', "", t)
        if t2 != t:
            open(loca, "w", encoding="utf-8", newline="").write(t2)


if __name__ == "__main__":
    G.write_stats("HitDice", "gen_hit_dice.py", "Hit Point Dice 13-20")
    drop_old_passive()
    nodes = class_nodes()
    append_progressions({u: {"Boosts": ";".join([f"ActionResource(HitPointDice{CLASSES[c][0]:02d},1,0)"] + ([RESOURCES[c, n]] if (c, n) in RESOURCES else []))}
         for u, (c, n) in nodes.items()})
    print(f"{len(nodes)} class level nodes get a Hit Point Die (13-20 + overridden ones)")
