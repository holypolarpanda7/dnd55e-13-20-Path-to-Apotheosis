"""Magic School Mastery: spells with variant menus join the pool (2026-11-19, for #82).

magic_school_spells.json listed container spells (Chromatic Orb, Glyph of Warding, Daylight...) under
"skipped_containers"; the 2024 boon takes any spell of the school. This moves each one into "spells" (with its
"children": the menu's variants, their costs/hit costs/flags) and into its school/level list, as
gen_spell_mastery_containers.py does for Spell Mastery. A former container whose menu was since cleared (e.g.
Divine Word, 2026-10-04) joins as a plain spell. Rerunnable: it re-reads every container already moved.
    bg3-data refresh apotheosis; UV_PROJECT_ENVIRONMENT=~/.cache/bg3-data-mcp/venv uv run --project ../bg3-data-mcp \
        python Scripts/export_msm_containers.py
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "bg3-data-mcp"))
from bg3data import query  # noqa: E402

PATH = os.path.join(REPO, "Scripts", "data", "magic_school_spells.json")


def main():
    s = query.Store(refresh=False)
    act = s.active(None)
    d = json.load(open(PATH, encoding="utf-8"))

    def fields(n):
        r = s.resolve(n, act)
        assert r, n
        return r, {k: v for k, (v, _) in r["fields"].items()}

    todo = list(d.get("skipped_containers", [])) + [n for n, v in d["spells"].items() if "children" in v]
    skipped, moved, plain = [], 0, 0
    for n in todo:
        r, f = fields(n)
        school, level = f.get("SpellSchool", ""), int(f.get("Level", 0) or 0)
        if not school or school == "None" or not 1 <= level <= 7:
            skipped.append(n)
            continue
        info = {"costs": f.get("UseCosts", ""), "flags": f.get("SpellFlags", ""), "level": level,
                "name": s.display_name(r["fields"], act), "school": school}
        if f.get("HitCosts"):
            info["hit_costs"] = f["HitCosts"]
        kids = [k for k in (f.get("ContainerSpells") or "").split(";") if k.strip()]
        if kids:
            info["children"] = []
            for k in kids:
                kr, kf = fields(k)
                if kf.get("ContainerSpells"):   # a nested menu: not offered
                    continue
                c = {"id": k, "type": kf.get("SpellType", ""), "costs": kf.get("UseCosts", ""), "flags": kf.get("SpellFlags", "")}
                if kf.get("HitCosts"):
                    c["hit_costs"] = kf["HitCosts"]
                info["children"].append(c)
            if not info["children"]:   # every variant is itself a menu (Enlarge/Reduce): not offered
                skipped.append(n)
                d["spells"].pop(n, None)
                for lst in d["schools"].get(school, {}).values():
                    if n in lst:
                        lst.remove(n)
                continue
            moved += 1
        else:
            plain += 1
        d["spells"][n] = dict(sorted(info.items()))
        lst = d["schools"].setdefault(school, {}).setdefault(str(level), [])
        if n not in lst:
            lst.append(n)
            lst.sort()
    d["skipped_containers"] = sorted(skipped)
    d["spells"] = dict(sorted(d["spells"].items()))
    json.dump(d, open(PATH, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False)
    print(f"{moved} containers with variants, {plain} former containers as plain spells, {len(skipped)} still skipped: {skipped}")


if __name__ == "__main__":
    main()
