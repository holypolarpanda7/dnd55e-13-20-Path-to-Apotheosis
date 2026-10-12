"""Spell visual effects for entries owned by many generators and hand-written files (2026-10-12). Scripts/data/spell_vfx.toml
maps stats entry -> {effect field: effect name}; names resolve through Scripts/data/vfx_generated.json (written by the
bg3-data MCP's bg3_fx_build from Scripts/data/vfx.toml). Sets or replaces each field in whichever Stats/Generated/Data file
defines the entry; "" clears a field the entry would inherit. Runs last in regen_all.sh, like apply_icons.py, so
regenerating any generator keeps the effects.
Run: python3 Scripts/apply_spell_vfx.py"""
import glob
import json
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = glob.glob(os.path.join(ROOT, "Public", "*", "Stats", "Generated", "Data"))[0]


def main():
    spec = tomllib.load(open(os.path.join(ROOT, "Scripts", "data", "spell_vfx.toml"), "rb"))
    gen = json.load(open(os.path.join(ROOT, "Scripts", "data", "vfx_generated.json"), encoding="utf-8"))
    missing = sorted({v for f in spec.values() for v in f.values() if v and v not in gen})
    if missing:
        sys.exit(f"effects not built (rebuild with bg3_fx_build): {', '.join(missing)}")
    left, fields = dict(spec), 0
    for path in sorted(glob.glob(os.path.join(DATA, "*.txt"))):
        text = open(path, encoding="utf-8").read()
        changed = False
        for name in [n for n in left if f'new entry "{n}"\n' in text]:
            m = re.search(r'new entry "%s"\n.*?(?=\n\nnew entry |\nnew entry |\n\n//|\Z)' % re.escape(name), text, re.S)
            blk = m.group(0)
            nb = blk
            for field, effect in left.pop(name).items():
                value = gen[effect]["uuid"] if effect else ""
                line = f'data "{field}" "{value}"'
                if re.search(r'^data "%s" "[^"]*"$' % field, nb, re.M):
                    nb = re.sub(r'^data "%s" "[^"]*"$' % field, line, nb, count=1, flags=re.M)
                else:
                    nb = nb.rstrip("\n") + "\n" + line
                fields += 1
            if nb != blk:
                text = text[:m.start()] + nb + text[m.end():]
                changed = True
        if changed:
            open(path, "w", encoding="utf-8").write(text)
    print(f"{fields} effect fields on {len(spec) - len(left)} spells" + (f"; not found: {', '.join(sorted(left))}" if left else ""))
    if left:
        sys.exit(1)


if __name__ == "__main__":
    main()
