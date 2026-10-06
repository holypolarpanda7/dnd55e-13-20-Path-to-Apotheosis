# Coverage & Gap Audit

Last full audit: 2026-07-14 (`Scripts/completeness_audit.py` + `Scripts/compat_audit.py`
+ TableUUID diff against dnd55e).

## Complete

- All 16 base classes have progression rows for every level 13–20.
- 80 subclasses have 13–20 feature nodes; TableUUID cross-check against dnd55e
  reports **0 missing / 0 unresolved** remaps.
- 157 of 175 passives are REAL (mechanical boosts/functors); the rest are
  classified below.

## Stub passives that are intentional (do not "fix")

- `Barbarian_BrutalStrike_Improved`, `Barbarian_BrutalStrike_17` — markers read
  by `HasPassive()` conditions in `Spell_Target.txt`.
- `Warlock_MysticArcanum_7/8/9` — display markers; the arcanum spells are
  granted via `SelectSpells` in Progressions.lsx.
- `Druid_BeastSpells`, `Diviner_14_GreaterPortent`,
  `NobleGenies_15_ElementalRebuke` — implemented in Lua
  (`BootstrapServer.lua`), the passive is the visible anchor.

## Real gaps — features that do nothing yet

None as of 2026-07-14. The four previously flagged:

| Passive | Resolution |
| --- | --- |
| `Berserker_10_Retaliation` | false positive — implemented in dnd55e (`UnlockInterrupt(Interrupt_Berserker_10_Retaliation)`) |
| `ControlledChaos` | false positive — implemented in base game (`UnlockInterrupt(Interrupt_ControlledChaos)`) |
| `DeadThree_UnholyInfiltration` | implemented 2026-07-14: Advantage on Stealth/Deception + 18m darkvision |
| `WinterWalker_15_FrozenHaunt` | implemented 2026-07-14: Cold resistance + CHILLED (2 turns) on dealing cold damage |

`completeness_audit.py` now reads base-game and dnd55e Passive.txt too, labeling
upstream-implemented passives `REAL-UPSTREAM` instead of `STUB`.

## Missing subclass extensions (exist in dnd55e, no 13–20 rows here)

24 subclasses (by dnd55e progression TableUUID):

- **Cleric domains:** Apocalypse, Astral, Mind, Nature, Shadow, Tempest
- **Druid circles:** Dragons, Dreams, Spores, Unbroken
- **Sorcerer:** Frost Sorcery, Shadow Magic, Storm Sorcery
- **Warlock:** Hexblade, Undead Patron
- **Paladin:** Blade of Radiance, Crown
- **Fighter:** Cavalier
- **Monk:** Kensei
- **Bard:** Spirits College
- **Barbarian:** Fractured, Hollow Warden
- **Rogue/Gunslinger-family:** Highway Rider, Shadow Gnawer

These are the largest outstanding content work. Each needs: 13–20 progression
rows (features typically at 14/15/17/18/20 depending on class), passives with
real boosts, localization handles, and expectations regeneration.

## Subclass features 13-20 for dnd55e's other subclasses (2026-10-03)

`Scripts/subclass_gap_audit.py` lists every subclass whose 13-20 feature levels (2024 class tables) or 13/17 subclass
spells have no Apotheosis node. Built so far (`Scripts/gen_subclass_features.py` + `SubclassFeatures.lua`, tests
`tests/bg3/subclass_features.toml`; source texts `References/Subclasses/Subclasses_13_20_Sources.txt`):
- **Half-caster subclass spells at 13/17** (`gen_subclass_spells.py`): 9 oaths, 5 ranger and 4 artificer subclasses.
  Not in BG3, so skipped: Commune, Compulsion, Legend Lore, Yolande's Regal Presence, Commune with Nature, Tree Stride,
  Contact Other Plane, Mislead, Hallucinatory Terrain, Passwall, Wall of Force. Untested in game (needs a 13+ level-up).
- **Storm Sorcery** 14 Storm's Fury (the base game's reaction, which dnd55e blanks at 11), 18 Wind Soul.
- **Shadow Sorcery** 14 Shadow Walk, 18 Umbral Form (real Charisma save at 0 HP via Lua; incorporeal movement not
  implemented).
- **Divine Soul** 14 Otherworldly Wings, 18 Unearthly Recovery.
- **Hexblade** 14 Masterful Hex (19-20 crits on the Hex target, Infectious Hex, Resilient Hex).
- **Undead Patron** 14 Superior Dread (fly + Vitality Siphon; Profane Casting's no-components isn't expressible).
- **College of Spirits** 14 Mystical Connection (second roll offered as a free switch).
- **Hollow Warden** 15 Ancient Endurance (Exhaustion immunity; Persistent Hunt spends the lowest level 4+ slot).
- **Conquest** (XGE) 15 Scornful Rebuke, 20 Invincible Conqueror. **Crown** (SCAG) 15 Unyielding Spirit (Paralyzed only:
  the engine has no Stunned-save tag), 20 Exalted Champion. **Watchers** (TCoE) 15 Vigilant Rebuke (Lua, automatic,
  spends your Reaction), 20 Mortal Bulwark (no Truesight; banishes Aberrations/Celestials/Elementals/Fey/Fiends).
  **Oathbreaker** (DMG 2014, as the base game) 15 Supernatural Resistance, 20 Dread Lord.
- **Cavalier** (UA 2025) 15 Ferocious Charger (Prone on a failed save; the push option isn't offered), 18 Vigilant
  Defender (special Reaction for Opportunity Attacks, refilled by Lua). **Arcane Archer** (XGE) 15 Ever-Ready Shot,
  18 Improved Shots.
- **Kensei** 17 Unerring Accuracy, **Sun Soul** 17 Sun Shield, **Drunken Master** 17 Intoxicated Frenzy (Lua),
  **Swashbuckler** 13 Elegant Maneuver / 17 Master Duelist (XGE).
- **Forge** 17 (XGE), **Twilight** 17 Twilight Shroud (TCoE), **Tempest** 17 Stormborn (always on: BG3 has no
  outdoors test). **Spores** 14 Fungal Body (no Deafened condition in BG3), **Dreams** 14 Walker in Dreams (Scrying
  only; Dream and the special Teleportation Circle aren't in BG3), **Swarmkeeper** 15 Swarming Dispersal.
- In-game tested: 24 cases in `tests/bg3/subclass_features.toml`. Not tested in game yet: Supernatural Resistance,
  Mortal Bulwark's banishment, Vigilant Defender, Arcane Archer, Unerring Accuracy, Master Duelist, Stormborn,
  Walker in Dreams, Unyielding Spirit.
- Still missing: Nature 17 Master of Nature (commanding charmed beasts/plants), and the subclasses whose 13-20 texts
  aren't available here (third-party or unknown sources): see `docs/SUBCLASS_SOURCING.md`.

## Upcasting to 7th-9th level (2026-10-03)

Base BG3 and dnd55e stop every spell's `_N` upcast variants at 6th level, so a 7th-9th level slot couldn't upcast
Bless, Hex, Ice Knife, Counterspell, Chromatic Orb... `Scripts/gen_upcasts.py` adds `_7`..`_9` for all 333 families
that stop at 6 (~1100 spells, ~190 statuses, 15 interrupts, 12 passives, 51 creatures and 15 trap items in `*_Upcast79.txt`). Each variant uses `X_6` and
extends the 5th->6th level step linearly (PHB 2024 upcasting is linear per slot level), generating any referenced
status / interrupt / container child at the new level the same way. Verified in game: the engine offers the `_9`
variants once a 9th level slot exists; `tests/bg3/upcasts.toml` (6 cases) passes.

Per-level creatures and traps (generated like everything else, tests in `tests/bg3/upcasts.toml`):
- **Summons**: dnd55e's per-level summons (Summon Beast, Aberration, Celestial, Dragon, Fey, Undead) get generated 7th-9th
  level creatures (`RootTemplates/Upcast79.lsf` + `Character_Upcast79.txt`: stepped HP/AC/damage, attacks = half the
  spell level), whether their levels chain (wolf, beholder) or are siblings (Red Cap, Summon Undead).
- **Glyph of Warding** (Acid, Cold, Fire, Lightning, Thunder): a trap item per level that names its own stepped trap
  projectile (11d8 at 9th). Sleep and Detonation have no dice and keep the 6th level trap.
- **Summon Elemental** is dnd55e's own (deferred 2026-10-03); Apotheosis's `Target_ApoSummonElemental` was retired.

Known limits (7th-9th inherit the 6th level behaviour):
- **Cloudkill** scales through a per-level surface (`Cloudkill6Cloud`); 7th-9th deal 6th level damage (needs per-level
  surface definitions).
- **Conjure Elemental**'s Myrmidon forms (their 6th level entry isn't named `_6`) and **Seeming**'s AI helper spell aren't
  extended.
- **Danse Macabre** can't resolve at any level (dnd55e bug, filed as bg3dnd #1539).
- Families already reaching 9th level (hand-written in `Spell_HighLevel.txt`, the Apotheosis summons) are untouched.

## Level maps (2026-10-03)

`Scripts/gen_levelmaps.py` extends 20 series past 12 and, by owner decision, restores the PHB 2024 steps base/dnd55e
compress to fit the 12-level cap (Sneak Attack, cantrip dice, Eldritch Blast, True Strike, Booming Blade, Breath
Weapon, Land's Aid). The overrides apply to every user of those series, monsters included. Verified in game by reading
the series back (Ext.StaticData LevelMap).

## Regenerating this audit

```bash
python Scripts/completeness_audit.py
python Scripts/compat_audit.py
python Scripts/build_all_class_expectations.py
python3 Scripts/subclass_gap_audit.py   # subclass 13-20 features / 13-17 spells (bg3-data MCP index)
python3 Scripts/slot_audit.py           # spell-slot curves vs the 2024 tables, levels 1-20
```

Slot curves (2026-10-03): all full, half and third casters match the 2024 tables through 20 after adding the Eldritch
Knight / Arcane Trickster / Mystic Arts 13-20 rows; Warlock gets its fourth Pact Magic slot at 17.

## Epic Boons

Approximations and gaps (2026-10-02):
- **Communication:** only the ability increase. Telepathy and the language features have no BG3 equivalent.
- **Iron Mind:** stops damage from breaking Concentration. Other things that break Concentration (incapacitation,
  casting another Concentration spell) still do.
- **Magic School Mastery:** spells with variant menus (container spells) aren't offered. The Spellcasting/Pact Magic
  prerequisite isn't enforced (true of every boon that has it).
- **Bright Sun:** Daylight Presence lights the area but doesn't dispel magical Darkness.
- **Eternal Rest** (Soul Drinker) isn't implemented.
- **Siberys** (Eberron: Forge of the Artificer, added 2026-10-05): the casting ability is the boon's choice (three
  variants, `EpicBoon_Siberys_Cast<Int|Wis|Cha>`); the +1 is the ordinary ability pick. The pool is the Sorcerer level 1-8
  list plus the Siberys Dragonmark Spells table (Scripts/data/siberys_spells.json, Scripts/export_siberys_spells.py).
  Container spells aren't offered, as for Magic School Mastery. The Eberron-campaign prerequisite isn't enforced.


## Gunslinger 13-20

Rebuilt 2026-10-02 (issue #6) from the Risk-dice Gunslinger dnd55e implements (`References/Classes/Gunslinger.txt`);
generated by `Scripts/gen_gunslinger.py`, scripted parts in `ScriptExtender/Lua/Gunslinger.lua`, tests in
`tests/bg3/gunslinger.toml`. Approximations:
- **Deft Maneuver (18):** dnd55e's maneuvers cost a Risk Die and no Bonus Action, so the extra maneuver-only Bonus
  Action has nothing to pay for. The passive is there; the Risk Die becoming a d12 at 18 is real.
- **Headshot (20):** the extra 10d10 is doubled by the Critical Hit, like every damage die on a crit.
- **Double or Nothing (High Roller 14):** a toggle, so you decide before attacking rather than after the crit. It
  doubles or halves the crit's total damage, which matches the rule exactly when the damage has no flat bonus
  (firearms) and is close otherwise.
- **Magic Bullet (Spellslinger 14):** adds the Risk Die to your spell attack roll rather than switching to your
  weapon's attack bonus; costs only a Risk Die, like dnd55e's other maneuvers.
- **Gold Star Hero (White Hat 14):** Stunned Surrender's DC uses `ManeuverSaveDC()` (8 + PB + the higher of Str
  and Dex) where the Gunslinger's is 8 + PB + Dex. The 30-foot aura gives allies Advantage against Frightened;
  you keep dnd55e's own Steely-Eyed immunity.

## Illrigger 13-20

Rebuilt 2026-10-02 (issue #7) from the MCDM Illrigger dnd55e implements (`References/Classes/Illrigger.txt`);
generated by `Scripts/gen_illrigger.py`, scripted parts in `ScriptExtender/Lua/Illrigger.lua`, tests in
`tests/bg3/illrigger.toml`. Built on dnd55e's model: a creature carries one INTERDICTED status (not a seal count),
burning removes it, and Infernal Conduit is a once-per-rest spell whose dice come from a level map (extended here,
in dnd55e's d12s, to 7/8/9/10 at 13/15/17/19). Moved back to their source levels (VISION principle 2): Hell's
Assassin (dnd55e 7, source 13), Dispater's Supremacy and Blood for Blood (dnd55e 7, source 18), Incontrovertible
(dnd55e 11, source 18). Approximations:
- **Infernal Majesty (17):** the Blood Price rider and reforming in Hell after death aren't implemented.
- **Master of Hell (20):** Darkness's Blindness lasts the minute rather than ending when a creature leaves the area.
- **Moving seals** isn't in dnd55e's model, so boons that trigger "when you place or move a seal" trigger on
  placing one: Flash of Brimstone on any seal, the Bonus Action ones (Dis's Onslaught, Soul's Doom, By the Throat)
  on dnd55e's Bonus Action seal.
- **Superior Interdict:** ignoring resistance is untested in game: seal damage scales with Illrigger level, so it
  needs a real Illrigger character.
- **Hellish Frenzy:** activated with a free action on your turn (not only at its start); its extra attack is a free
  weapon attack rather than an extra attack inside the Attack action.
- **Iron Gaol:** "native to Hell" isn't checked; creatures of level 4 or lower stay imprisoned.
- **Last Word:** spends up to three seals automatically, and the healing is its own roll of the same dice rather
  than the explosion's total; it heals even if the explosion hits no one.
- **Spellbreaker:** dnd55e's 2024 Counterspell (a Constitution save) rather than a leveled Counterspell.
- **Quid Pro Quo:** BG3 has no horned devil or devil jurist; a Merregon (devil soldier) stands in, as your follower.
- **Sanguine Gift:** a toggle (spends a seal on each heal within 30 feet while on).
- **Haemal Exchange:** the d8 goes to the nearest ally within 30 feet.
- **Dark Malediction:** uses the Darkness spell's cloud, which (unlike the source) darkvision can't see through.
- **By the Throat:** the "no more than one size larger" limit isn't checked.

## Spells added for issue #10

From the PHB 2024 text (Skill Empowerment: Xanathar's), `References/Spells/Issue10_Spells.txt`;
`Scripts/gen_spells_2024.py`; tests `tests/bg3/spells_2024.toml`. Approximations:
- **Aura of Life:** "Hit Point maximums can't be reduced" isn't implemented (no boost for it).
- **Aura of Purity:** Advantage on saves against Charmed, Frightened, Paralyzed and Poisoned (the engine's
  *_ADV tags); Blinded, Deafened and Stunned have no such tag.
- **Geas:** a 30-day Charmed (cast out of combat); the 5d10 Psychic for acting against the command isn't implemented.
- **Raise Dead:** out of combat, playable characters only; the material diamond isn't consumed. Untested in game
  (needs a dead party member).
- **Skill Empowerment:** doesn't check that the target is proficient in the chosen skill.
Summons are new creatures (`Scripts/gen_summons.py`, tests `tests/bg3/summons.toml`): each form has its own root
template (`RootTemplates/Apotheosis_Summons.lsf`) and Character stats, and the slot level arrives as a level status
(your PB, spell attack modifier and save DC; the stat block's "+ spell level" AC/HP; Multiattack via Extra Attack;
the level's Slam variant). Models are base-game placeholders, swappable per form in `MODELS`.
- **Summon Elemental** (Air/Earth/Fire/Water, levels 4-9) and **Summon Construct** (Clay/Metal/Stone, 4-9): built and
  tested 2026-10-03. Approximations: no Burrow/Swim/Amorphous Form; Opportunity Attacks use the unarmed attack, not
  the Slam; Stony Lethargy blocks all reactions (as dnd55e's Shocking Grasp) and ignores "if it can see it"; Heated
  Body ignores grapples; Berserk Lashing doesn't move toward a creature out of reach.
- **Mordenkainen's Faithful Hound** (4), **Bigby's Hand** (5-9) and **Animate Objects** (5-9): built and tested
  2026-10-03, with `Summons.lua`. The hound is invulnerable, skips its own turns and bites an enemy within 5 ft at
  the start of yours (Dex save vs your DC, 4d8 Force); a Magic action moves it 30 ft; it ends beyond 300 ft. The
  hand has AC 20 and your Hit Point maximum; Forceful Hand's push is done in Lua (Force() takes no formula). Animate
  Objects hides each targeted object and summons a Medium/Large/Huge Animated Object in its place within your
  spellcasting modifier's budget; the object returns when the creature ends or your Concentration does.
  Approximations: the hand **acts on its own turn** (one effect, 60 ft move) instead of on your Bonus Action, as BG3
  does with summons such as Spiritual Weapon; Interposing Hand gives an ally +2 AC/Dex saves instead of
  space-based cover and no Difficult Terrain; Grappled is Speed 0 + Disadvantage on attacks with an Athletics
  check at the end of its turns to escape; the hound is visible to everyone and has no alarm bark or Truesight;
  animated objects don't carry excess damage over to the object, and "nonmagical / not fixed" isn't checked. Exploration-only spells BG3 can't express: Locate Creature, Commune with Nature, Tree Stride,
Fabricate, Creation, Stone Shape, Transmute Rock, Leomund's Secret Chest, Mordenkainen's Private Sanctum.

## Quivering Palm (Open Hand 17, issue #16)

The 2024 two-step feature (`Scripts/gen_class_features.py`): an Unarmed Strike hit can start the vibrations for
4 Focus Points (an interrupt), and an action ends them for a Constitution save against 8 + Wisdom + PB (10d12
Force, half on a success); a free spell ends them harmlessly. Approximations: the vibrations last until ended
(not "days equal to your Monk level"), and ending them costs an action rather than replacing one attack of the
Attack action.

## True Polymorph follow-ups (issue #23)

`Scripts/gen_true_polymorph.py` + `ScriptExtender/Lua/TruePolymorph.lua`; tests `tests/bg3/true_polymorph.toml`.
- CR 7 forms for targets of level 7+: Earth/Fire/Air/Water Myrmidon and Mind Flayer (the base game's player
  shapeshift templates), temporary HP = the BG3 form's HP (103 / 90 / 90 / 90 / 150), as the #20 forms.
- Object into creature: a nonmagical object becomes a Minotaur, Dire Wolf, Phase Spider or Shadow Mastiff that
  follows you; it reverts if Concentration ends early, stays after the full hour. BG3 has no full-statblock
  forms between CR 7 and CR 9 to offer for objects, so the choice stops at CR 3 there.

## Hotbar: 9th-level spell slots (fixed 2026-10-04)
The hotbar's action resource bar (HotBar.xaml `ActionResourcesList`, bound to the engine's
`CurrentPlayer.UIData.ActionResourcesCostPreview`) lists spell slot levels 1 to MaxLevel - 1 of the `SpellSlot` resource
definition. The base game's MaxLevel is 9, so a level 17+ caster's 9th-level slots existed (and could be spent) but never
showed: the bar ended at VIII. Apotheosis overrides the base `SpellSlot` definition (same UUID) with MaxLevel 10 in
ActionResourceDefinitions.lsx; checked in game: the engine list then holds levels 1-9 and the bar shows IX. No UI file is
replaced, so it can't conflict with UI mods.


## Duplicate spell definitions removed (2026-10-05)
Two implementations of Prismatic Spray and of Dominate Monster were both on the class lists (players saw each twice),
Foresight was defined twice in Spell_HighLevel.txt (the later, less accurate copy won), and Feeblemind sat on the Bard
lists next to its PHB 2024 replacement Befuddlement. Kept the more accurate version (VISION: accuracy over homebrew):
- Prismatic Spray: Spell_Zone.txt `Zone_PrismaticSpray` (12d6 per ray, as the rule) - the generated one dealt 2d6 of five
  types. Reworked the same day to the full PHB 2024 rule (user decision): one cast, a d8 per creature (8 = two rays),
  indigo (Restrained, Con save at each turn end until three of a kind; three failures = Petrified) and violet (Blinded,
  Wis save at the start of the caster's next turn; failure = APO_PRISMATIC_BANISHED, our stand-in for "another plane").
  The d8s and follow-up saves are ScriptExtender/Lua/PrismaticSpray.lua; damage stays in the spell (Evasion, combat
  log, spell DC). No higher-level casting (the 14d6/16d6 upcasts were homebrew). Back in Magic School Mastery.
- Dominate Monster: Spell_Target.txt `Target_DominateMonster` (Wisdom save, advantage when fighting, its own status, 9th
  level upcast) - the generated one was a Dominate Person reskin.
- Foresight: the 8-hour, touch version, limited to willing creatures.
- Feeblemind: off every list; kept only as Befuddlement's chassis.
generate_level79_spells.py REMOVE_FROM_LISTS strips the dropped ones on every regen.

## Level 7-9 spells on their rules classes' lists (2026-10-05)
Scripts/extract_rules_spells.py reads each level 7-9 spell's class tags from the rules texts (SRD 5.2.1, PHB 2024, Arcana
Unleashed) into Scripts/data/rules_spell_classes.json (names and tags only) with the mod entries of that name;
Scripts/gen_rules_spell_lists.py puts every entry on those classes' lists and on Bard Magical Secrets. It added the spells
other generators, dnd55e or the base game provide: Project Image (Wizard, Bard), Power Word Stun (Sorcerer, Wizard, Warlock,
Bard), Glibness (Warlock, Bard), Resurrection (Cleric, Bard), Incendiary Cloud (Druid), Antipathy/Sympathy and Prismatic
Wall (Bard). Rerun the extractor after implementing a level 7-9 spell.

## Arcana Unleashed level 7-9 spells (2026-10-05)
Scripts/gen_au_spells.py: Aura of Evasion, Fractured Awareness, Power Word Pain, Reweave Fate, Transfix (7); Entrancing Mirrors,
Illusory Dragon, Iron Body, Lightning Ring, Moment of Prescience (8); Detonate, Invulnerability, Vision of Elapsing Eons, Wail
of the Banshee (9). Not made: Hindsight (watching the past 10 years has nothing in BG3 to act on). Approximations:
- No Deafened in BG3 (Lightning Ring, Wail of the Banshee); Wail skips Silenced creatures (can't hear).
- Power Word Pain: the Constitution save to cast a spell while Charmed isn't modelled.
- Reweave Fate: rerolls with Advantage and always grants half the Temporary Hit Points, 3d10 (the rule gives 6d10 only if the
  reroll succeeds, which the interrupt can't see; user decision 2026-10-05). Offered for allies' attack rolls and saves.
- Detonate: the explosion's Disadvantage when the target dropped to 0 isn't modelled.
- Illusory Dragon: implemented but kept off every list (gen_rules_spell_lists.HOLD) until the dragon itself can be modelled
  (user decision 2026-10-05). As built: no tangible dragon. Enemies within 18m of you save when it appears; the Bonus Action breath comes from
  you; the Frightened creature repeats its save each turn (FRIGHTENED's own) instead of only when out of the dragon's sight.
- Vision of Elapsing Eons: Exhaustion is the 2024 rule (D20 Tests -2 per level, Speed -1.5m per level, death at 6) as new
  statuses APO_EXHAUSTION_1-5, which a Long Rest clears entirely (2024: one level). Help shakes the target free.
- Iron Body's "Exhaustion can't increase" blocks those statuses.

## Spells learned at level-up, 13-20 (2026-10-05)
The level-up screen offers a selector's list as the game loads it: dnd55e's one-level lists are cumulative in game through
`MergedInto` lists, ours had none, so Sorcerer 13 offered only level 7 spells (seen in game). Fixed by
Scripts/gen_learn_lists.py, against the PHB 2024 tables (tests/bg3/class_tables.toml):
- Sorcerer: cumulative lists (1-7 / 1-8 / 1-9), +1 spell at 13, 15, 17, 18, 19, 20 (was 13, 14, 15, 17), replace one every level.
- Warlock: a regular pact spell (levels 1-5) at 13, 15, 17, 19 - there was none - and a replacement every level.
- Bard: one Magical Secrets spell a level (was two: Magical Secrets + a Bard-list pick), replacement at 14 and 16 too.
- Occultist Guild: learns from the level 1-3 Wizard list (was 1-2, with 3rd-level slots).
Caught from now on by bg3_lint_progressions (NARROW SPELL CHOICES, SPELLS PER LEVEL) and by every test build, which fails a
level whose level-up screen offers spell levels with gaps.

## Level 13-20 features aligned with the rules texts (2026-10-05)
Found by bg3_lint_rules, approved by the user, built by Scripts/gen_rules_fixes.py (texts in D:\Library\DnD):
- Paladin 14 Restoring Touch (PHB 2024) replaces our Cleansing Touch: Lay on Hands gains Restore options for Blinded, Charmed,
  Frightened, Paralyzed, Stunned (one use each; BG3 has no Deafened).
- Rogue 13 Subtle Strikes (+2 attack, not a rules feature) removed; Rogue 14 Devious Strikes: Daze, Knock Out, Obscure Cunning
  Strike toggles, wired into dnd55e's 12 Sneak Attack entries like its Terrify option (dice costs not modelled, as in dnd55e).
- Assassin 13 Envenom Weapons replaces our Infiltration Expertise: the Poison Cunning Strike deals 2d6 Poison on the failed
  save and at each failed repeat save; the Assassin's Poison damage ignores Resistance.
- Artificer 14 Advanced Artifice (Eberron: Forge of the Artificer): Refreshed Genius + the 4th cantrip; our "+1 to saves"
  Magic Item Savant stand-in removed (BG3 has no attunement).
- Banneret 18 Inspiring Commander (Heroes of Faerun) replaces Inspiring Surge (Improved): Group Recovery / Rallying Surge reach
  doubled to 60 ft, Immunity to Charmed and Frightened.
- Scion of the Three 13 Aura of Malevolence (Lua: SubclassFeatures.lua, after a Bloodthirst teleport) and 17 Dread Incarnate
  (Cutthroat + Murderous Intent as written) replace our Unholy Infiltration and homebrew Murderous Intent.
Static checks only (stats, progression and rules lints clean); not yet run in game.
