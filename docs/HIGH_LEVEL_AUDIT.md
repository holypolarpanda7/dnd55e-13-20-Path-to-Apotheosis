# High-level resource audit (2026-10-13)

The Hit Point Dice turned out to stop at level 12 because dnd55e hands out class resources one step per level up to its
12-level cap. This is the sweep for everything else of that kind: class, subclass and species resources, level-scaled dice,
spend variants and summon strength, checked against PHB 2024 / SRD 5.2.1 and the shared library (`D:\Library\DnD`).

How it was done, and how to repeat it:

- `Scripts/resource_audit.py`: per-class and per-subclass resource totals by level against what the rules say (EXPECT tables) and
  every passive with Proficiency Bonus steps (`CharacterLevelGreaterThan(4)` / `(8)`) that stops at +4.
- `bg3_lint_rules` now has a `RES` check: every resource column of the SRD class tables (Rage, Channel Divinity, Wild Shape,
  Second Wind, Ki, Sorcery Points, Favored Enemy, Seals) against the data, and the Weapon Mastery picks each level adds.
- `Scripts/levelmap_audit.py`: level maps that stop below 13 (34 left, each judged below).
- A survey of every `ClassLevelHigherOrEqualThan(N)` / `CharacterLevelGreaterThan(N)` in dnd55e's stats for tiers that end near 12.

## Fixed

| Feature | Was | Now | Source |
| --- | --- | --- | --- |
| Hit Point Dice | stopped at 12 | one per level to 20 | PHB 2024 (earlier commits) |
| Ranger Favored Enemy | 4 | 5 at 13, 6 at 17 | SRD table |
| Wizard Arcane Recovery | 6 | 7, 8, 9, 10 at 13, 15, 17, 19 | PHB 2024 |
| Celestial Healing Light | 13 dice | 1 + Warlock level (to 21) | Warlock.txt |
| Circle of Dreams Balm | 12 dice | Druid level (to 20); spend variants of 7-10 dice at 14/16/18/20 | XGE |
| Abjuration Arcane Ward | 2 x level to 12 | 2 x Wizard level to 20 | Wizard.txt |
| Circle of the Land Natural Recovery | 6 | half the Druid level, rounded up | Druid.txt |
| Zealot Warrior of the Gods | 6 dice | 7 at 17 (+ a 7-dice spend variant) | Barbarian.txt |
| Alchemist Experimental Elixir | 4 | 5 at 15 | Artificer.txt |
| Artificer Magic Items | 4 | 5 at 14, 6 at 18 | SRD table |
| Rune Knight | runes 5, Runic Shield 4 | +1 rune at 15; Runic Shield = Proficiency Bonus | Tasha's |
| Psi Warrior / Soulknife | 8 Psionic Energy Dice | 10 at 13, 12 at 17 | Fighter.txt / Rogue.txt |
| Swarmkeeper Writhing Tide | PB 4 | PB 5 / 6 | Tasha's |
| Dragonborn, Eladrin, Goliath, Shadar-kai | PB 4 uses | PB 5 at 13, 6 at 17 | PHB 2024 / MPMM |
| 13 feats with Proficiency Bonus uses (Lucky, Healer, Poisoner, the Giant feats, Adrenaline Rush, Fey Trickster, Spellfire Spark, Purple Dragon Commandant) | PB 4 | PB 5 / 6 | PHB 2024 |
| Monk Unarmored Movement | +20 ft at 10 | +25 ft at 14, +30 ft at 18 | PHB 2024 |
| Fighter Weapon Mastery | 5 | 6 at 16 | SRD table |
| Cleric Divine Spark dice | 2d8 at 5, 3d8 at 11, 4d8 at 17 (the cantrip tiers) | 1d8, 2d8 at 7, 3d8 at 13, 4d8 at 18 | Cleric.txt |
| Berserker/World Tree Life-Giving Force | 3d6 | 4d6 at 16 (Rage Damage) | Barbarian.txt |
| Venomous Strike (Poison Sneak Attack) | 7d8 at 11 and then flat | as many d8s as Sneak Attack dice: 6d8 at 11 ... 10d8 at 19 | follows Sneak Attack |
| Beast Master companions, Steel Defender | the level 11 template for good (55 / 60 HP, Proficiency Bonus 4) | bands at 13/15/17/19: +10 HP each and the owner's Proficiency Bonus | PHB 2024 (HP 5 + 5 x level) |
| Barbarian and Cleric 12 | missing a Hit Point Die (override dropped it) | restored (earlier commit; progression lint now flags it) | |

All of these are per-level node boosts (or the dnd55e passive extended with itself, re-read at each regen), so they apply at the
level-up and survive dnd55e updates. Generators: `gen_class_resources.py`, `gen_levelmaps.py`, `gen_hit_dice.py`.

## Needs a decision or a source

- **Experimental Elixir potency at 15** (Healing 4d8, Speed +20 ft, Resilience 8 hours, Boldness, Flight 30 ft): the elixirs are items
  summoned into the inventory per tier (`Shout_EE_*`); a 15+ tier needs new item templates.
- **Way of the Four Elements disciplines** (Burning Hands, Fist of Unbroken Air, Shatter, Thunderwave, Water Whip, Ray of Frost,
  Shocking Grasp, Scorching Ray, Hold Person; level maps `*_Monk`, `FistOfUnbrokenAir`, `WaterWhip`): dnd55e steps them at 9; the 2014
  PHB lets monks spend one more ki at 13 and 17 (a die or ray more). Not in the library, so from memory: not changed.
- **Wild Shape**: forms' damage dice (`WildShapeDamageLow/Medium`, 1d8 / 1d10 at 12) and the CR limit (Druid level / 3) are capped at
  12 in dnd55e; unchecked in game.
- **Wizard / Illusion summons** (`Target_SummonBeast_*_Illusion`, `Target_SummonFey_Illusion`) have the same band-to-11 shape as the
  companions; not changed (rules text not checked).
- **Artificer plans**: plans known 7 at 14 and 8 at 18, and the 14+ plan list, aren't modelled (dnd55e unlocks plans by tier up to 10).
- **Lay on Hands** is a charge pool whose heal scales with the Paladin level (not 5 x level Hit Points): kept, as decided 2026-10-03.
- **Star Map / Cosmic Omen** uses are Wisdom-modifier based in the 2024 text; dnd55e steps them by level. Not a cap problem; left.
- **Bladesong** (`Bladesong` level map 2/3/4): the Bladesinger moved to dnd55e.
- dnd55e's own gaps below 13 (not built here: dnd55e adds lower-level content itself): Gunslinger Weapon Mastery picks at 4 and 10;
  Illrigger Seal damage 3d6 at 10 (the table says 11).

## To check in game

- Abjuration Arcane Ward: the base game's and dnd55e's nodes both sit in the table, the audit counts 31 at level 12 (2 x level + 7).
- A feat's Proficiency Bonus uses at the level-up that raises the Proficiency Bonus (the conditional boosts may wait for the next
  load, as the level-conditional passives did): take Lucky at 12, level to 13, read the Luck Points.
- Companion HP and Proficiency Bonus at 13, 15, 17, 19; Balm 7-10 dice; Warrior of the Gods 7 dice; Unarmored Movement at 14/18.
