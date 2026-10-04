"""Generate bg3-data-mcp test cases (tests/bg3/generated.toml) from the SE Lua test registries.

- SpellTests.lua ASSIGN: each 7th-9th level spell -> an automated case in its assigned subclass's build.
- FeatureTests.lua mode="auto" entries -> console cases (`!apofeature <Passive>`) at the level where the
  progression grants the passive.

Run from the repo root (needs the bg3-data-mcp index for spell types and progression levels):
  UV_PROJECT_ENVIRONMENT=~/.cache/bg3-data-mcp/venv uv run --directory ../bg3-data-mcp python \
      ../dnd55e-13-20-Path-to-Apotheosis/Scripts/gen_bg3_tests.py
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(REPO), "bg3-data-mcp"))
from bg3data import query  # noqa: E402

LUA = glob.glob(os.path.join(REPO, "Mods", "*", "ScriptExtender", "Lua"))[0]
OUT = os.path.join(REPO, "tests", "bg3", "generated.toml")


def q(s):
    return json.dumps(s, ensure_ascii=False)


def toml_list(xs):
    return "[" + ", ".join(q(x) for x in xs) + "]"


def spell_cases(store, active):
    src = open(os.path.join(LUA, "SpellTests.lua"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r'\{\s*sub = "(\w+)",\s*cls = "(\w+)",\s*spell = "(\w+)",\s*name = "([^"]+)",\s*lvl = (\d+),\s*verify = (\{.*?\})\s*(?:,\s*extra = "([^"]*)")?\s*\},?\s*$',
                         src, re.M):
        sub, cls, spell, name, lvl, verify, extra = m.groups()
        r = store.resolve(spell, active)
        if not r:
            print(f"skip {spell}: not in index")
            continue
        stype = r["fields"].get("SpellType", ("Target",))[0]
        slot_lvl = r["fields"].get("Level", ("0",))[0]
        statuses = re.findall(r'"(\w+)"', verify)
        area = stype in ("Shout",)
        lines = [f"[[case]]", f"id = {q('spell-' + sub + '-' + spell)}", f"class = {q(cls)}", f"subclass = {q(sub)}",
                 f"level = {lvl}", f"spell = {q(spell)}"]
        expect = []
        cost = "WarlockSpellSlot" if cls == "Warlock" else "SpellSlot"
        if "manual" in verify:
            text = re.search(r'manual = "([^"]*)"', verify).group(1)
            lines += [f"title = {q(name + ': manual check')}", 'mode = "player"', f"instructions = {q(text)}"]
            lines += ['target = "A"', 'spawn = [{ as = "A", template = "wolf", faction = "hostile", hp = 300, distance = 6 }]']
            expect.append("{ cast = true }")
        elif "damage" in verify:
            lines += [f"title = {q(name + ' damages a hostile wolf')}", 'target = "host"' if area else 'target = "A"', "retries = 1",
                      f'spawn = [{{ as = "A", template = "wolf", faction = "hostile", hp = 300, distance = {3 if area else 6} }}]']
            expect.append('{ target = "A", hp_change = [-999, -1] }')
        elif "enemy" in verify:
            # HP-threshold spells (Divine Word: IF(HasHPLessThan(X) and not HasHPLessThan(Y)):ApplyStatus(S,...)) only work below a
            # threshold: spawn the wolf just under the highest threshold of an expected status (a 300 HP wolf can never be hit)
            hp = 300
            succ = r["fields"].get("SpellSuccess", ("",))[0] or ""
            for x, st in re.findall(r"IF\(HasHPLessThan\((\d+)\)[^)]*\)?\)?:ApplyStatus\((\w+)", succ):
                if st in statuses:
                    hp = min(hp, int(x) - 1) if hp != 300 else int(x) - 1
            lines += [f"title = {q(name + ' applies ' + ' or '.join(statuses) + ' to a hostile wolf')}", 'target = "host"' if area else 'target = "A"',
                      "retries = 2", f'spawn = [{{ as = "A", template = "wolf", faction = "hostile", hp = {hp}, distance = {3 if area else 6} }}]',
                      f"notes = {q('the wolf can pass a save: the case retries up to twice')}"]
            expect.append(f'{{ target = "A", status_applied_any = {toml_list(statuses)} }}')
        elif "ally" in verify:
            lines += [f"title = {q(name + ' applies ' + ', '.join(statuses) + ' to an ally')}", 'target = "B"',
                      'spawn = [{ as = "B", template = "wolf", faction = "friendly", distance = 3 }]']
            expect.append(f'{{ target = "B", status_applied = {toml_list(statuses)} }}')
        elif "self" in verify:
            lines += [f"title = {q(name + ' applies ' + ', '.join(statuses) + ' to you')}", 'target = "host"']
            expect.append(f'{{ target = "host", status_applied = {toml_list(statuses)} }}')
        else:
            print(f"skip {spell}: unknown verify {verify}")
            continue
        if extra:
            lines.append(f"prep = {q('also check by eye: ' + extra)}" if "manual" not in verify else f"notes = {q(extra)}")
        if cls == "Warlock" and int(slot_lvl or 0) > 5:
            # 6th-9th level Warlock spells come through Mystic Arcanum: once per rest, no slot (Warlock slots stop at 5th)
            expect += ["{ cast = true }"]
        else:
            expect += ["{ cast = true }", f'{{ resource = "{cost}", level = {slot_lvl}, change = -1 }}']
        lines.append("expect = [\n  " + ",\n  ".join(dict.fromkeys(expect)) + ",\n]")
        out.append("\n".join(lines))
    return out


def feature_cases(store, active):
    src = open(os.path.join(LUA, "FeatureTests.lua"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r'FT\.Register\("(\w+)",\s*\{\s*mode = "(\w+)"(.*?)\n\}\)', src, re.S):
        passive, mode, body = m.groups()
        if mode != "auto":
            continue
        note = re.search(r'note = "([^"]*)"', body)
        w, p = store._where(active)
        rows = store.db.execute(f"SELECT name, level, attrs FROM prog WHERE attrs LIKE ? AND {w} ORDER BY rank DESC",
                                [f"%{passive}%"] + p).fetchall()
        hit = next(((n, l, json.loads(a)) for n, l, a in rows
                    if passive in (json.loads(a).get("PassivesAdded") or "").split(";")), None)
        if not hit:
            print(f"skip feature {passive}: no progression grants it")
            continue
        name, level, attrs = hit
        is_sub = str(attrs.get("ProgressionType", "0")) != "0"
        lines = ["[[case]]", f"id = {q('feature-' + passive)}", (f"subclass = {q(name)}" if is_sub else f"class = {q(name)}"),
                 f"level = {level}", f"title = {q(passive + ': ' + (note.group(1) if note else 'feature test'))}",
                 f'console = "!apofeature {passive}"', f'expect_log = "FeatureTest {passive}: PASS"',
                 f'fail_log = "FeatureTest {passive}: FAILED"', "wait = 12",
                 "retries = 2"]                # a scripted attack can miss (Frozen Haunt's Ray of Frost)
        out.append("\n".join(lines))
    return out


def main():
    store = query.Store(refresh=False)
    active = store.active(None)
    spells, feats = spell_cases(store, active), feature_cases(store, active)
    head = ("# GENERATED by Scripts/gen_bg3_tests.py from SpellTests.lua (ASSIGN) and FeatureTests.lua (auto).\n"
            "# Don't edit by hand: change the Lua registries and re-run. Spec: bg3-data-mcp/docs/TESTING.md.\n\n"
            '[suite]\nname = "Apotheosis spells 7-9 and features"\n')
    open(OUT, "w", encoding="utf-8").write(head + "\n\n" + "\n\n".join(spells + feats) + "\n")
    print(f"wrote {OUT}: {len(spells)} spell cases, {len(feats)} feature cases")


if __name__ == "__main__":
    main()
