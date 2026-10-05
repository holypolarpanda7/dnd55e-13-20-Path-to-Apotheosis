"""Spell Mastery free casts of spells with variants (2026-10-04). A `<Spell>_SM` copy of a container spell (Chromatic
Orb, Disguise Self, Enlarge/Reduce, Find Familiar) inherited the base picker, and every base variant costs a spell
slot, so the "free" cast spent a slot after the pick (found by the bg3-data lint PICKER rule). This generator gives
each such `_SM` container its own free children: `<Child>_SM` using the child with UseCosts ActionPoint:1 and
SpellContainerID = the `_SM` container, and points the container's ContainerSpells at them.

Owns the section between the SPELL MASTERY CONTAINERS markers in Spell_SpellMastery.txt.
Run: python3 Scripts/gen_spell_mastery_containers.py   (reads the bg3-data MCP index; refresh it first)
"""
import json
import os
import re
import sqlite3
from pathlib import Path

GUID = "dnd55e_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
FILE = Path(__file__).resolve().parent.parent / f"Public/{GUID}/Stats/Generated/Data/Spell_SpellMastery.txt"
DB = os.path.expanduser("~/.cache/bg3-data-mcp/cache/index.sqlite")
BEGIN, END = "// SPELL MASTERY CONTAINERS BEGIN (Scripts/gen_spell_mastery_containers.py)", "// SPELL MASTERY CONTAINERS END"
LAYERS = ("base", "dnd55e", "apotheosis")


def main():
    db = sqlite3.connect(DB)

    def rows(name):
        q = f"SELECT layer, type, using_, data FROM stats WHERE name=? AND layer IN ({','.join('?' * len(LAYERS))}) ORDER BY rank"
        return db.execute(q, (name, *LAYERS)).fetchall()

    def field(name, key, seen=None):
        """Resolved field through `using` (last layer wins, then the parent)."""
        seen = seen or set()
        if name in seen:
            return None
        seen.add(name)
        rs = rows(name)
        for layer, typ, using, data in reversed(rs):
            d = json.loads(data)
            if key in d:
                return d[key]
            if using and using != name:
                return field(using, key, seen)
        return None

    text = FILE.read_text(encoding="utf-8")
    body = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", text, flags=re.S)
    sm = re.findall(r'new entry "([A-Za-z0-9_]+_SM)"\ntype "SpellData"\ndata "SpellType" "([A-Za-z]+)"\nusing "([A-Za-z0-9_]+)"\n', body)
    out = [BEGIN, "// free variants for the Spell Mastery copies of spells with variants; regenerated - don't edit"]
    n = 0
    for name, stype, parent in sm:
        kids = [k for k in (field(parent, "ContainerSpells") or "").split(";") if k.strip()]
        if not kids or name.endswith("_SM_SM"):
            continue
        sm_kids = []
        for k in kids:
            kt = field(k, "SpellType") or stype
            sm_kids.append(f"{k}_SM")
            out += [f'new entry "{k}_SM"', 'type "SpellData"', f'data "SpellType" "{kt}"', f'using "{k}"',
                    'data "UseCosts" "ActionPoint:1"', f'data "SpellContainerID" "{name}"', 'data "RootSpellID" ""',
                    'data "PowerLevel" ""', ""]
        # the hand-written container entry gets (or refreshes) its ContainerSpells line
        head = re.compile(r'(new entry "%s"\ntype "SpellData"\ndata "SpellType" "[A-Za-z]+"\nusing "[A-Za-z0-9_]+"\n)(data "ContainerSpells" "[^"]*"\n)?' % re.escape(name))
        body = head.sub(lambda m: m.group(1) + f'data "ContainerSpells" "{";".join(sm_kids)}"\n', body, count=1)
        n += 1
    out.append(END)
    FILE.write_text(body.rstrip("\n") + "\n\n" + "\n".join(out) + "\n", encoding="utf-8")
    print(f"{n} Spell Mastery containers given free variants")


if __name__ == "__main__":
    main()
