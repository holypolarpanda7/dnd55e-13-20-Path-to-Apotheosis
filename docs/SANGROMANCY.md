# Sangromancer and Sangromancy spells 7-9 — plan (2026-10-12)

The Sangromancer (Grim Hollow Player's Guide, Ghostfire Gaming) is a Wizard subclass dnd55e added in 4.13.7 (table
`bd5f7880-233d-4ce5-8833-636988444183`, features at 3/6/10). VISION #5: PTA completes it to 20; VISION #1: it follows
dnd55e's source, the Grim Hollow Player's Guide. Library: `excerpts/subclasses/grim-hollow_sangromancy.md` (subclass text),
`excerpts/spells/grim-hollow_sangromancy-spells.txt` (spell list, stat lines, summaries).

## Done (branch feat/sangromancer-13-20)

| Level | What | Where |
| --- | --- | --- |
| 13-20 | +1 Full-Blooded d12 (`HitPointDice12`) every level: the pool is 1 + Wizard level (dnd55e: 4 at 3, +1 a level) | `gen_subclass_features.py` |
| 13, 15, 17 | Sangromancy Savant pick from dnd55e's Sangromancy list `398d9fdb` (its pick at each new spell-slot level: 3, 5, 7, 9, 11) | `gen_subclass_features.py` |
| 14 | **Red Renewal**: first Short Rest after a Long Rest restores Wizard d6 Hit Point Dice and Full-Blooded d12s, half the Wizard level each | `gen_subclass_features.py` |
| 13-20 | Hit Point Dice for every base class (dnd55e stops at 12; PHB 2024 has one per level) - Red Renewal and every Hit Point Dice cost need them | `gen_hit_dice.py` |

Sanguine Vigor (6) already scales to 20 (`IncreaseMaxHP(ClassLevel(Wizard))`); Blood for Blood (10) has no level scaling.

Not yet: a test case for Red Renewal - the test framework has no rest step (bg3-data MCP follow-up: a `rest = "short"` case
step). The `wiz-sangromancer` build (3-20) is in `tests/bg3/wizard.toml`.

## The five 7th-9th level spells - blocked on the book text

| Spell | Lvl | School | Grim Hollow class tags | Summary (not book text) |
| --- | --- | --- | --- | --- |
| Burst Forth | 7 | Conjuration | Bard, Warlock, Wizard | teleport inside a creature, burst out; Con save, Necrotic, half on success |
| Sanguine Fusillade | 7 | Evocation | Sorcerer, Warlock, Wizard | a creature's blood becomes darts (Piercing) that strike creatures within 60 ft of it |
| Creeping Death | 8 | Necromancy | Warlock, Wizard | Concentration: a death threshold; Bonus Action Con saves raise it; 3 successes end it |
| Red Rain | 8 | Conjuration | Cleric, Warlock | 10-minute cast, blood rain for miles: Frightened beasts/plants, Exhaustion + Necrotic |
| Steal Immortality | 9 | Transmutation | Warlock | Reaction: Temporary HP + the target's creature type (resistances by type) |

Needed from the book before building (accuracy over homebrew): damage dice and their scaling, save DCs/abilities, ranges,
the exact Hit Point Dice cost (summaries say 7/8/9 = the spell level), Creeping Death's threshold formula, Red Rain's
Exhaustion/damage cadence, Steal Immortality's per-type benefits.

### How they'll be built (dnd55e's pattern, verified 2026-10-12)

- **Die-size variants**: each Sangromancy spell is a container with one variant per Hit Point Die size - e.g.
  `Target_CircleOfScarlet6/8/10/12`, `UseCosts` `...;HitPointDice06:4` .. `HitPointDice12:4` (cost = spell level), damage dice
  = that die size (`4d12+SpellCastingAbilityModifier` for the d12 variant). The d12 variant spends the Full-Blooded pool.
- **"Is a Sangromancy spell"**: dnd55e decides with a hard-coded whitelist, `IsSangromancySpell()` in
  `Scripts/thoth/helpers/Wizard.khn` (every variant id). Sanguine Vigor (regain HP = spell level) and Blood for Blood check
  it, so PTA's spells must be on it. Options: (a) ship a PTA helper file redefining `IsSangromancySpell()` as dnd55e's list +
  ours (later definition wins in Lua; fragile - `bg3_deps_diff` must watch dnd55e's Wizard.khn); (b) ask dnd55e's author to
  add a status/flag-based check; (c) override Sanguine Vigor's `Conditions` in PTA with `IsSangromancySpell() or
  IsApoSangromancySpell()` (a full copy of dnd55e's passive - also fragile). Decide with the user.
- **Lists**: dnd55e puts Sangromancy spells on class lists by their Grim Hollow tags (Circle of Scarlet: Sorcerer and Warlock
  4) and on the Savant list `398d9fdb` for Sangromancers; PTA adds the new ones with a `MergedInto` list (see memory
  spell-list-mergedinto) and to `Scripts/data/rules_spell_classes.json` via `extract_rules_spells.py` (re-export Siberys).
  Whether a "Wizard" tag also lands on dnd55e's general Wizard list is to be checked against dnd55e's 1st-4th spells first.
- **Savant picks at 13/15/17** then offer the 7th/8th/9th-level ones automatically (same list).
- **Effects**: `Scripts/data/vfx.toml` has the `blood` palette; candidates from the base game: the Slayer's Living Sacrifice
  (52 m), Cazador's blood stream beam, Bhaal-temple/Orin effects, Concentrated Blast, Wounding Ray (`bg3_search_effects` with
  `color="red"`).

## Upstream (dnd55e's to add, not PTA)

4th-6th level Sangromancy spells missing from dnd55e 4.13.7.1: Dark Sacrament, Viscous Sheath, Mortality, Splattering Smite,
Blood Tide, Heartseeker (memory: dnd55e-lower-level-content).
