"""Multiclass spell slots for caster levels 13-20 (PHB 2024 Multiclass Spellcaster table = the full-caster table).

A character with more than one class gets its spell slots from the base game's MulticlassSpellSlots progression (table
a6f80028, keyed by the combined caster level from each class's MulticlassSpellcasterModifier), not from the class
progressions. That table stops at 12, so a multiclassed caster never got 7th-9th level slots (PTA #37, 2026-10-19:
Bard 16 / Fighter 1 stuck at 6th-level slots while a single-class Bard worked). These nodes continue it to 20 with the
same increments as the full casters' class progressions (13: 7th, 15: 8th, 17: 9th, 18: 5th, 19: 6th, 20: 7th).
14 and 16 add nothing and are empty nodes, like the base game's level 12.

Owns Progressions.lsx between MULTICLASS SPELL SLOTS 13-20 markers.
Run: python3 Scripts/gen_multiclass_slots.py
"""
from gen_common import Gen, patch_progressions

G = Gen("multiclassslots", "MULTICLASS SPELL SLOTS 13-20")
TABLE = "a6f80028-fee2-41e0-bd24-d2f0758d936f"   # base game MulticlassSpellSlots
SLOTS = {13: 7, 15: 8, 17: 9, 18: 5, 19: 6, 20: 7}

NODES = []
for lvl in range(13, 21):
    attrs = {"Boosts": f"ActionResource(SpellSlot,1,{SLOTS[lvl]})"} if lvl in SLOTS else {}
    NODES.append((G.gid(f"node:MulticlassSpellSlots:{lvl}"), "MulticlassSpellSlots", lvl, 0, TABLE, attrs))


def write():
    patch_progressions({}, NODES, G.marker)


if __name__ == "__main__":
    write()
    print(f"{len(NODES)} MulticlassSpellSlots nodes (levels 13-20)")
