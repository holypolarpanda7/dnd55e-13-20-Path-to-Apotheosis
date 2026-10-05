"""Own icons for entries owned by many generators and hand-written files (2026-10-05). Icons/icon_map.json maps
stats entry -> icon name (an Icons/src/<name>.png built by the bg3-data icon pipeline). Sets or replaces the entry's
`data "Icon"` in whichever Stats/Generated/Data file defines it. Runs last in regen_all.sh, so regenerating any
generator keeps the icons.
Run: python3 Scripts/apply_icons.py"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = glob.glob(os.path.join(ROOT, "Public", "*", "Stats", "Generated", "Data"))[0]


def main():
    imap = json.load(open(os.path.join(ROOT, "Icons", "icon_map.json"), encoding="utf-8"))
    left = dict(imap)
    for path in sorted(glob.glob(os.path.join(DATA, "*.txt"))):
        text = open(path, encoding="utf-8").read()
        changed = False
        for name in [n for n in left if f'new entry "{n}"' in text]:
            m = re.search(r'new entry "%s"\n.*?(?=\n\nnew entry |\nnew entry |\Z)' % re.escape(name), text, re.S)
            blk = m.group(0)
            icon = left.pop(name)
            if re.search(r'^data "Icon" "[^"]*"$', blk, re.M):
                nb = re.sub(r'^data "Icon" "[^"]*"$', f'data "Icon" "{icon}"', blk, count=1, flags=re.M)
            else:
                nb = blk.rstrip("\n") + f'\ndata "Icon" "{icon}"'
            if nb != blk:
                text = text[:m.start()] + nb + text[m.end():]
                changed = True
        if changed:
            open(path, "w", encoding="utf-8").write(text)
    print(f"{len(imap) - len(left)} icons applied" + (f"; not found: {', '.join(sorted(left))}" if left else ""))


if __name__ == "__main__":
    main()
