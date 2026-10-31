"""Spells learned at levels 13-20 by the classes that learn at level-up: Sorcerer, Warlock, Bard, Occultist Guild (PHB 2024;
2026-10-05).

PHB 2024: whenever a Sorcerer/Warlock gains a level it can add spells up to its Prepared Spells number, of any level it has
spell slots for, and replace one spell on its list. The level-up screen offers the selector's list as the game loaded it:
dnd55e makes its one-level lists cumulative with MergedInto lists ("5.5 Sorcerer SLevel 1 List to 3" -> the level 3 list),
our level 7-9 lists had none, so Sorcerer 13 offered only level 7 spells (seen in game 2026-10-05). Each selector here
points at a list that already holds every spell level the class casts at that level.

  Sorcerer Prepared Spells 12->20: 16 17 17 18 18 19 20 21 22 (+1 at 13, 15, 17, 18, 19, 20)
  Warlock  Prepared Spells 12->20: 11 12 12 13 13 14 14 15 15 (+1 at 13, 15, 17, 19; Pact Magic slots stay level 5)

Lists: dnd55e's per-level learn lists (read from its Progressions, as released) + our overrides + our 7th-9th lists.
"""
import os
import re

from gen_common import DND, PUB, patch_progressions

OUR_LISTS = os.path.join(PUB, "Lists", "SpellLists.lsx")
SORC, WARL = "e2416b02-953a-4ce8-aa8f-eb98d549d86d", "a7a958f1-d858-4021-9fa7-cf87e7d71377"

# new list UUID -> (name, class table, our higher-level lists to add)
LISTS = {
    "00170002-0001-0001-0001-000000000002": ("Sorcerer Learn L1-7", SORC, ["00170001-0001-0001-0001-000000000002"]),
    "00180002-0001-0001-0001-000000000002": ("Sorcerer Learn L1-8", SORC, ["00180001-0001-0001-0001-000000000002"]),
    "00190002-0001-0001-0001-000000000002": ("Sorcerer Learn L1-9", SORC, ["00190001-0001-0001-0001-000000000002"]),
    "00150002-0001-0001-0001-000000000007": ("Warlock Learn L1-5", WARL, []),
}
# node UUID -> (new spells, list, selector id): every level also replaces one spell
SORC_LIST = lambda L: "00170002-0001-0001-0001-000000000002" if L < 15 else "00180002-0001-0001-0001-000000000002" if L < 17 else "00190002-0001-0001-0001-000000000002"
PLAN = {f"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaa9{L - 12:02d}": (n, SORC_LIST(L), "SorcererSpell")
        for L, n in {13: 1, 14: 0, 15: 1, 16: 0, 17: 1, 18: 1, 19: 1, 20: 1}.items()}
PLAN.update({f"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbb9{L - 12:02d}": (n, "00150002-0001-0001-0001-000000000007", "")
             for L, n in {13: 1, 14: 0, 15: 1, 16: 0, 17: 1, 18: 0, 19: 1, 20: 0}.items()})
# Bard: one spell a level from Magical Secrets (dnd55e's design from 10 on: Bard, Cleric, Druid and Wizard spells of every
# level, cumulative in game through MergedInto) - Bard 13-20 also had a Bard-list pick, two spells a level where the PHB
# table adds one (Prepared Spells 16 17 17 18 18 19 20 21 22), and no replacement at 14 and 16.
# Magical Secrets is one list with every level merged in (dnd55e's + our 7th-9th). The level-up screen greys out new picks
# above the bard's slots, but the Replace Spell screen doesn't, and the engine then refuses the swap at Accept (seen in game
# 2026-10-19, #37: Bard 16 swapped to a 9th-level spell, nothing happened). So 13-14 and 15-16 learn from capped copies:
# everything merged into Magical Secrets except our 8th/9th (resp. 9th) list; 17-20 keep the full list. A mod that merges
# its own spells into Magical Secrets only shows up from 17.
MAGICAL_SECRETS = "858d4322-9e9f-4aa4-aada-9c68835dc6fe"
MS8, MS9 = "00180001-0001-0001-0001-000000000006", "00190001-0001-0001-0001-000000000006"
MS_CAPPED = {"00170002-0001-0001-0001-000000000003": ("Bard Magical Secrets to L7", {MS8, MS9}),
             "00180002-0001-0001-0001-000000000003": ("Bard Magical Secrets to L8", {MS9})}
MS_LIST = lambda L: "00170002-0001-0001-0001-000000000003" if L < 15 else "00180002-0001-0001-0001-000000000003" if L < 17 else MAGICAL_SECRETS
PLAN.update({f"99999999-9999-9999-9999-9999999999{L - 12:02d}": (n, MS_LIST(L), "BardMagicalSecrets")
             for L, n in {13: 1, 14: 0, 15: 1, 16: 0, 17: 1, 18: 1, 19: 1, 20: 1}.items()})
# Occultist Guild (dnd55e third caster): 3rd-level slots from 13, but learned from the level 1-2 Wizard list; "5.5 Wizard
# SLevel 3" is 1-3 in game (MergedInto). Its picks stay as they were (13, 15, 17, 19, 20).
WIZ3 = "22755771-ca11-49f4-b772-13d8b8fecd93"
PLAN.update({f"a4682900-0000-0000-0000-0000000000{L}": (1, WIZ3, "EldritchKnightAbjEvo") for L in (13, 15, 17, 19, 20)})
# Wizard 13-20: the two free spellbook spells a level learn from capped copies of the Wizard list as loaded - dnd55e's
# "5.5 Wizard SLevel 6" with every list merged into it, minus our 8th/9th (resp. 9th) lists. They were hand-written
# snapshots (2026-09-30) and missed every spell added since: all Arcana Unleashed 7-9 spells, Project Image, Power Word
# Stun and dnd55e's newer Wizard spells (reported 2026-10-31: Detonate / Wail of the Banshee etc. not offered at 17).
# Same UUIDs, so the Wizard progression nodes keep their selectors.
WIZ_MAIN = "bc917f22-7f71-4a25-9a77-7d2f91a96a65"
W8, W9 = "00180001-0001-0001-0001-000000000001", "00190001-0001-0001-0001-000000000001"
WIZ_CAPPED = {"aa384b4e-36b4-5b2d-93b3-c1063ba2ffb2": ("WizardUpToL7", {W8, W9}),
              "f0f0369f-fef5-5399-92c1-0a02c56c93bd": ("WizardUpToL8", {W9}),
              "ae03c25e-d0ac-55a5-899a-ae75a3b20c5a": ("WizardUpToL9", set())}
MARK = "LEARN LISTS 13-20"


def lists(path):
    t = open(path, encoding="utf-8").read()
    out = {}
    for b in re.findall(r'<node id="SpellList">(.*?)</node>', t, re.S):
        u = re.search(r'id="UUID"[^>]*value="([^"]*)"', b)
        s = re.search(r'id="Spells"[^>]*value="([^"]*)"', b)
        if u and s:
            out[u.group(1)] = [x for x in s.group(1).split(";") if x]
    return out


def merged_into(target):
    """UUIDs of the lists merged into `target` at load (MergedInto), dnd55e's and ours (ours override by UUID), in order."""
    found = {}
    for path in (os.path.join(DND, "Lists", "SpellLists.lsx"), OUR_LISTS):
        for b in re.findall(r'<node id="SpellList">(.*?)</node>', open(path, encoding="utf-8").read(), re.S):
            u = re.search(r'id="UUID"[^>]*value="([^"]*)"', b).group(1)
            m = re.search(r'id="MergedInto"[^>]*value="([^"]*)"', b)
            found[u] = m.group(1) if m else None
    return [u for u, t in found.items() if t == target]


def learn_lists(table):
    """dnd55e's leveled-spell learn lists for a class table, in level order (not cantrips, Mystic Arcanum or feature lists)."""
    t = open(os.path.join(DND, "Progressions", "Progressions.lsx"), encoding="utf-8").read()
    found, skip = [], set()  # a list flagged as cantrips/arcanum anywhere is skipped everywhere (Warlock 4 reuses the
    for b in re.findall(r'<node id="Progression">(.*?)</node>', t, re.S):  # cantrip list without flags)
        if f'value="{table}"' not in b:
            continue
        sel = re.search(r'id="Selectors"[^>]*value="([^"]*)"', b)
        for args in re.findall(r"SelectSpells\(([^)]*)\)", sel.group(1) if sel else ""):
            a = [x.strip() for x in args.split(",")]
            if any("Cantrip" in x or "MysticArcanum" in x or x == "AlwaysPrepared" for x in a[3:]):
                skip.add(a[0])
            elif a[0] not in found:
                found.append(a[0])
    return [x for x in found if x not in skip]


def main():
    have = lists(os.path.join(DND, "Lists", "SpellLists.lsx"))
    have.update(lists(OUR_LISTS))  # our overrides of dnd55e lists win
    rows = []
    for u, (name, table, extra) in LISTS.items():
        spells = []
        for lu in learn_lists(table) + extra:
            assert lu in have, f"{name}: list {lu} not found"
            spells += [x for x in have[lu] if x not in spells]
        rows.append((u, name, spells))
        print(f"{name}: {len(spells)} spells")
    sources = merged_into(MAGICAL_SECRETS)
    assert MS8 in sources and MS9 in sources, "our Magical Secrets 8th/9th lists no longer merge into Magical Secrets"
    for u, (name, drop) in MS_CAPPED.items():
        spells = list(have.get(MAGICAL_SECRETS, []))
        for lu in sources:
            if lu not in drop:
                spells += [x for x in have[lu] if x not in spells]
        rows.append((u, name, spells))
        print(f"{name}: {len(spells)} spells from {len(sources) - len(drop)} lists")
    sources = merged_into(WIZ_MAIN)
    assert W8 in sources and W9 in sources, "our Wizard 8th/9th lists no longer merge into the Wizard list"
    for u, (name, drop) in WIZ_CAPPED.items():
        spells = list(have.get(WIZ_MAIN, []))
        for lu in sources:
            if lu not in drop:
                spells += [x for x in have[lu] if x not in spells]
        rows.append((u, name, spells))
        print(f"{name}: {len(spells)} spells from {len(sources) - len(drop)} lists")
    body = "".join(
        f'                <node id="SpellList">\n'
        f'                    <attribute id="Comment" type="LSString" value="generated by Scripts/gen_learn_lists.py"/>\n'
        f'                    <attribute id="Name" type="FixedString" value="{n}"/>\n'
        f'                    <attribute id="Spells" type="LSString" value="{";".join(s)}"/>\n'
        f'                    <attribute id="UUID" type="guid" value="{u}"/>\n'
        f'                </node>\n' for u, n, s in rows)
    block = f"                <!-- {MARK} BEGIN (generated) -->\n{body}                <!-- {MARK} END -->\n"
    t = open(OUR_LISTS, encoding="utf-8").read()
    start, end = f"                <!-- {MARK} BEGIN", f"<!-- {MARK} END -->\n"
    if start in t:
        t = t[:t.index(start)] + block + t[t.index(end) + len(end):]
    else:
        i = t.rindex("            </children>")
        t = t[:i] + block + t[i:]
    open(OUR_LISTS, "w", encoding="utf-8", newline="").write(t)

    # the class nodes: keep every other attribute and selector, replace the class's own learn selector
    prog = open(os.path.join(PUB, "Progressions", "Progressions.lsx"), encoding="utf-8").read()
    nodes = {}
    for b in re.findall(r'<node id="Progression">.*?</node>', prog, re.S):
        u = re.search(r'id="UUID" type="guid" value="([^"]*)"', b).group(1)
        if u not in PLAN:
            continue
        attrs = {k: v for k, v in re.findall(r'id="(PassivesAdded|PassivesRemoved|Boosts|Selectors)" type="LSString" value="([^"]*)"', b)}
        n, lst, sid = PLAN[u]
        keep = [s for s in re.findall(r"\w+\([^)]*\)", attrs.get("Selectors", ""))
                if not (s.startswith("SelectSpells(") and "MysticArcanum" not in s)]
        attrs["Selectors"] = ";".join([f"SelectSpells({lst},{n},1{',' + sid if sid else ''})"] + keep)
        nodes[u] = attrs
    assert len(nodes) == len(PLAN), f"class nodes not found: {set(PLAN) - set(nodes)}"
    patch_progressions(nodes, [], "UNUSED")
    print(f"{len(nodes)} Sorcerer/Warlock/Bard/Occultist Guild nodes 13-20 set")


if __name__ == "__main__":
    main()
