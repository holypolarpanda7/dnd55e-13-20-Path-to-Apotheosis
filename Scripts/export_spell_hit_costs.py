"""Add each pooled spell's HitCosts to the Epic Boon spell pools (2026-11-19, #82).

Smites (Searing, Thunderous, Branding, Ensnaring Strike...) pay their spell slot in HitCosts, on the hit, not in UseCosts.
gen_epic_boons.py free_copy strips slots from both, so the pools carry "hit_costs" next to "costs". Rerun after
export_siberys_spells.py or a magic_school_spells.json re-export:
    bg3-data refresh apotheosis; UV_PROJECT_ENVIRONMENT=~/.cache/bg3-data-mcp/venv uv run --project ../bg3-data-mcp \
        python Scripts/export_spell_hit_costs.py
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "bg3-data-mcp"))
from bg3data import query  # noqa: E402

POOLS = {"magic_school_spells.json": (2, False), "siberys_spells.json": (1, True)}   # file -> its JSON (indent, ensure_ascii)


def main():
    s = query.Store(refresh=False)
    act = s.active(None)
    for pool, (indent, ascii_) in POOLS.items():
        path = os.path.join(REPO, "Scripts", "data", pool)
        d = json.load(open(path, encoding="utf-8"))
        n = 0
        for name, info in d["spells"].items():
            r = s.resolve(name, act)
            assert r, name
            hc = r["fields"].get("HitCosts", ("", None))[0] or ""
            if hc:   # only the spells that have them (keeps the pools' diffs small)
                info["hit_costs"] = hc
                n += 1
            else:
                info.pop("hit_costs", None)
        json.dump(d, open(path, "w", encoding="utf-8", newline="\n"), indent=indent, ensure_ascii=ascii_)
        print(f"{pool}: {len(d['spells'])} spells, {n} with HitCosts")


if __name__ == "__main__":
    main()
