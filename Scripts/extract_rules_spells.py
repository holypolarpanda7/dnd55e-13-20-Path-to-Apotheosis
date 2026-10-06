"""Which classes get each level 7-9 spell, by the rules texts (2026-10-05) -> Scripts/data/rules_spell_classes.json.

Reads the "Level N School (Class, Class)" line under each spell name in the library (DND_LIBRARY): SRD 5.2.1, PHB 2024,
Arcana Unleashed. Only names, levels, schools and class tags are written (no book text), plus the mod's spell entries with
that display name, resolved through the bg3-data index. gen_rules_spell_lists.py puts each entry on its classes' lists.

Run (needs the bg3-data venv): UV_PROJECT_ENVIRONMENT=~/.cache/bg3-data-mcp/venv uv run --project ../bg3-data-mcp \
    python Scripts/extract_rules_spells.py
Rerun after a new level 7-9 spell is implemented (so its entry is picked up) or a new source is added.
"""
import collections
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("DND_LIBRARY", "/mnt/d/Library/DnD")
OUT = os.path.join(REPO, "Scripts", "data", "rules_spell_classes.json")
# first source wins for a spell in several (the SRD is the 2024 text too)
SOURCES = [("SRD 5.2.1", "text/srd-cc-v5-2-1.txt"), ("PHB 2024", "text/d-d-5e-players-handbook-2024.txt"),
           ("Arcana Unleashed", "excerpts/subclasses/ArcanaUnleashed.txt")]
SCHOOL = "Abjuration|Conjuration|Divination|Enchantment|Evocation|Illusion|Necromancy|Transmutation"
# rules name -> the mod's display name, where they differ
ALIASES = {"Arcane Sword": "Mordenkainen's Sword", "Magnificent Mansion": "Mordenkainen's Magnificent Mansion"}
# NPC, story and scroll copies that share a spell's display name
NOT_PLAYER = re.compile(r"Apostle|Scroll|_LOW_|DarkUrge|_NPC|_Monster", re.I)


def norm(x):
    return re.sub(r"[^a-z0-9]", "", x.lower().replace("’", "'"))


def rules_spells():
    out = {}
    for src, rel in SOURCES:
        lines = [l.strip() for l in open(os.path.join(LIBRARY, rel), encoding="utf-8", errors="replace")]
        for i, l in enumerate(lines):
            m = re.match(rf"Level ([7-9]) ({SCHOOL}) \(([^)]+)\)$", l)
            if not m:
                continue
            k = next((k for k in range(i - 1, max(0, i - 3), -1) if lines[k]), i)
            # Arcana Unleashed puts an art credit and caption between some names and their level line ("Illusory Dragon /
            # Julie Dillon / blank / Illusory dragons look terrifyingly real. / Level 8 ..."): the name is above the credit
            if src == "Arcana Unleashed" and lines[k].endswith("."):
                k = next((j for j in range(k - 1, max(0, k - 3), -1) if lines[j]), k) - 1
            name = lines[k] if k < i else ""
            name = re.sub(r"\s+", " ", name).strip().replace("’", "'")
            if name.isupper():  # some PHB headings are in capitals
                name = name.title().replace("'S ", "'s ")
            # the SRD's "Arcane Sword" is the PHB's "Mordenkainen's Sword": one spell
            if 2 < len(name) < 40 and norm(name) not in (norm(ALIASES.get(n, n)) for n in out):
                out[name] = {"level": int(m.group(1)), "school": m.group(2), "source": src,
                             "classes": [c.strip() for c in m.group(3).split(",")]}
    return out


def mod_entries(names):
    sys.path.insert(0, os.path.join(os.path.dirname(REPO), "bg3-data-mcp"))
    from bg3data import query
    s = query.Store(refresh=False)
    act = s.active(None)
    w, p = s._where(act)
    by_name = collections.defaultdict(list)
    for (n,) in s.db.execute(f"SELECT DISTINCT name FROM stats WHERE type='SpellData' AND {w}", p):
        r = s.resolve(n, act)
        if not r:
            continue
        f = {k: v for k, (v, _) in r["fields"].items()}
        if str(f.get("Level", "")) not in ("7", "8", "9") or f.get("SpellContainerID") or f.get("RootSpellID", n) not in ("", n):
            continue
        if NOT_PLAYER.search(n) or "IsSpell" not in (f.get("SpellFlags") or ""):
            continue
        by_name[norm(s.display_name(r["fields"], act))].append(n)
    return {nm: sorted(by_name.get(norm(ALIASES.get(nm, nm)), [])) for nm in names}


def main():
    rules = rules_spells()
    ent = mod_entries(rules)
    for nm, r in rules.items():
        r["entries"] = ent[nm]
    json.dump({"generated": "Scripts/extract_rules_spells.py", "spells": dict(sorted(rules.items()))},
              open(OUT, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    miss = [f"L{r['level']} {n} ({r['source']})" for n, r in sorted(rules.items(), key=lambda t: (t[1]["level"], t[0])) if not r["entries"]]
    multi = {n: r["entries"] for n, r in rules.items() if len(r["entries"]) > 1}
    print(f"{len(rules)} rules spells, {len(rules) - len(miss)} implemented; not implemented: {len(miss)}")
    print("  " + "\n  ".join(miss))
    if multi:
        print("several entries:", multi)


if __name__ == "__main__":
    main()
