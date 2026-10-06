"""Every implemented level 7-9 spell on the lists of the classes the rules give it to (2026-10-05).

generate_level79_spells.py lists only the spells it writes; spells from other generators, dnd55e or the base game (Project
Image, Power Word Stun, Resurrection, Glibness, Incendiary Cloud) were missing from some classes. The class tags come from
Scripts/data/rules_spell_classes.json (Scripts/extract_rules_spells.py: SRD 5.2.1, PHB 2024, Arcana Unleashed); the
target lists are generate_level79_spells.L, including Bard Magical Secrets ("all"). Additive and idempotent.

Run from the repo root before gen_learn_lists.py (which builds the cumulative learn lists from these): python3 Scripts/gen_rules_spell_lists.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_level79_spells import L, SPELL_LISTS  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rules_spell_classes.json")
# implemented but kept off every list (taken off on each run): Illusory Dragon until the dragon itself can be modelled
# (user decision 2026-10-05)
HOLD = {"Shout_Apo_IllusoryDragon"}
CLASS = {"Bard": "brd", "Cleric": "clr", "Druid": "dru", "Sorcerer": "sor", "Warlock": "wlk", "Wizard": "wiz"}


def additions():
    out = {}
    for name, r in json.load(open(DATA, encoding="utf-8"))["spells"].items():
        for e in [e for e in r["entries"] if e not in HOLD]:
            targets = {u for c in r["classes"] if c in CLASS for u in L.get((CLASS[c], r["level"]), [])}
            targets |= set(L[("all", r["level"])])
            for u in targets:
                out.setdefault(u, []).append(e)
    return out


def main():
    text = SPELL_LISTS.read_text(encoding="utf-8")
    text = re.sub(r'(id="Spells"[^/]*?value=")([^"]*)(")',
                  lambda m: m.group(1) + ";".join(x for x in m.group(2).split(";") if x and x not in HOLD) + m.group(3), text)
    added = 0
    for uuid, spells in additions().items():
        node = re.search(r'<node id="SpellList">(?:(?!</node>).)*?value="' + re.escape(uuid) + r'"(?:(?!</node>).)*?</node>', text, re.S)
        if not node:
            print(f"WARNING: spell list {uuid} not found")
            continue
        block = node.group(0)
        m = re.search(r'(id="Spells"[^/]*?value=")([^"]*)(")', block)
        have = [x for x in m.group(2).split(";") if x]
        new = [s for s in spells if s not in have]
        if not new:
            continue
        added += len(new)
        print(f"  {uuid}: + {', '.join(new)}")
        block = block[:m.start(2)] + ";".join(have + new) + block[m.end(2):]
        text = text[:node.start()] + block + text[node.end():]
    SPELL_LISTS.write_text(text, encoding="utf-8")
    print(f"{added} list entries added")


if __name__ == "__main__":
    main()
