# Changelog

## Unreleased

- Built against DnD 5.5e All-in-One BEYOND 4.14.0.2 (was 4.13.10.5). DnD 5.5e reworked Reckless Attack, Brutal Strike, Frenzy and the Rune Knight's runes to follow the rules more closely; PTA's 13-20 features for them are rebuilt on the new versions:
  - Barbarian: Reckless Attack is now the reaction on your first attack, and Brutal Strike effects are hotbar toggles. Improved Brutal Strike (13) adds Staggering Blow and Sundering Blow toggles; at 17 Brutal Strike deals 2d10 and adds a toggle for each pair of two effects. The old Reckless Attack spells are gone (DnD 5.5e removed them).
  - Berserker Frenzy now uses your Rage Damage in d6s, so it reaches 4d6 at Barbarian 16 (#57).
  - Rune Knight: your fifth rune is a rune pick at 15 (runes have their own uses now). Master of Runes (15) now does what the rules say (each rune you know can be invoked twice per rest) instead of a +2 AC / saving throw bonus. Runic Juggernaut (18) makes Giant's Might's extra damage 1d10 instead of adding another 1d10. Giant's Might uses keep growing with your Proficiency Bonus (5 at 13, 6 at 17); Runic Shield now uses your Constitution modifier (DnD 5.5e), so PTA no longer adds uses to it.
- Fixed: Monk Body and Mind (20) raised Dexterity and Wisdom by 6 instead of 4 (a leftover +2 on the level 20 node), and its maximum is 25 as in the rules. Barbarian Primal Champion's maximum is 25 too (was 24). Reported as #58.
- Fixed: Spell Mastery's free spells (Wizard 18) lost their spell properties: Hold Person, Web, Invisibility and others didn't need Concentration, harmful spells weren't marked as attacks, and Magic Missile, Burning Hands and Blindness were wrongly set up as spell menus. They now keep the real spell's properties. Reported as #60.
- Changed: Evoker Overchannel (14) is a hotbar toggle (on by default). Toggle it off to cast normally and avoid the Necrotic damage. Requested in #59.
- Removed eight unused feature entries that had no effect and were never granted (#57).
- Fixed: Holy Aura, Divine Word, Storm of Vengeance, Control Weather, Antimagic Field and Conjure Celestial (and the Boon of Siberys copy of Control Weather) showed as an empty spell menu on the hotbar and couldn't be cast. Same cause as the Spell Mastery bug in #60.

## v1.0.4.0 - 2026-10-23

- Fixed: Evoker Overchannel (level 14) added your Intelligence modifier to damage instead of what the rules say. It now maximizes the damage dice of your 1st- to 5th-level damaging spells. The first use after a Long Rest is free; each further use deals 2d12 Necrotic damage per spell level to you, +1d12 per level for every earlier use since that rest. Reported as #48.
- Fixed: Barbarian Reckless Attack (the normal melee one and its Brutal Strike blows) lost Frenzy's extra damage and its own advantage on the attack after DnD 5.5e started recognising Reckless Attack by spell name; our Brutal Strike versions are now recognised too. The thrown and unarmed versions were not affected. Reported as #55.
- Built against DnD 5.5e All-in-One BEYOND 4.13.10.5 (was 4.13.9.0). Theft of Vitae and Moonlight Step were restructured upstream; their 7th- to 9th-level versions are rebuilt on the new layout, and the Sneak Attack rules fixes and upcast copies follow the other 4.13.10 changes (#50, #51).

## v1.0.3.0 - 2026-10-20

- Fixed: multiclassed spellcasters never got 7th-, 8th- or 9th-level spell slots (e.g. Bard 16 / Fighter 1 stopped at 6th-level slots). The game's multiclass spell slot table stopped at caster level 12; it now continues to 20 like the full casters' (7th at 13, 8th at 15, 9th at 17, then a 5th, 6th and 7th at 18-20). Reported on Nexus, #37.
- Fixed: at Bard 13-16 the Replace Spell screen listed Magical Secrets spells above your highest spell slot (8th and 9th level at 13), and picking one silently did nothing. Bard 13-14 now learns and replaces from Magical Secrets up to 7th level, 15-16 up to 8th, 17-20 the full list. (Spells another mod adds to Magical Secrets show from 17.) #37.
- Fixed: Font of Magic stopped turning spell slots into Sorcery Points at 14 points, so from Sorcerer level 15 you could never convert back up to your maximum. The ceiling is now your Sorcerer level from 15 on (20 at level 20), as the rules say ("You can't have more Sorcery Points than the number shown in the table for your level"). Font of Magic can now also convert 6th- to 9th-level slots (6 to 9 points), which the rules allow. Reported on Nexus.

## v1.0.2.0 - 2026-10-17

- Built against DnD 5.5e All-in-One BEYOND 4.13.9.0 (tested through the Bard 1-20 build; the Bard level 7-12 spell picks that DnD 5.5e moved to the class progression sit under the 13-20 picks as before).
- Sanguine Thief (Grim Hollow rogue, new in DnD 5.5e 4.13.9.0): levels 13-20. Third-caster slots as the Arcane Trickster (3rd-level at 13 and 16, 4th-level at 19) with picks from new Sanguine Thief 3rd and 4th level spell lists (Wizard lists plus Sangromancy), Sangromancy Dice grow with the Sneak Attack dice (7 / 8 / 9 / 10), Bloodstitch at 13 (Magic action, 3 dice, 30 ft emanation, Dexterity save, 3d8 Necrotic; a creature it drops gives a die back) and Bloody Exit at 17 (Reaction, 5 dice: the attack misses, you strike back for +5d8 Necrotic if the attacker is within 3 m, and may teleport 30 ft without an action on your next turn).
- Dark Sacrament and Viscous Sheath (new Sangromancy spells in DnD 5.5e 4.13.8.0) upcast to 7th-9th level with their Hit Point Dice costs, and work with Sanguine Vigor.

## v1.0.1.0 - 2026-10-13

- New spell effects for 7th- to 9th-level spells, built from the base game's own effects (layered, recoloured, enlarged; no other mod's assets). 9th- and 8th-level spells get the largest: e.g. Meteor Swarm's meteors are the Netherbrain's Orb of Obliteration, Wail of the Banshee layers a necrotic destructive wave with a 52 m soul burst, Wish uses Divine Intervention in arcane colours, Gate opens two planar portals.
- Spells that had no effects now have them (Meteor Swarm, Time Stop, Gate, Mass Heal, Foresight, Prismatic Wall, Wish, True Resurrection, Resurrection, Project Image, Feeblemind, Glibness, Power Word Stun) and spells that borrowed a mismatched look get a fitting one (Fire Storm and Earthquake no longer look radiant; the Illusory Dragon's necrotic breath no longer looks like fire).
- Fixed: Meteor Swarm did no damage. It now drops four meteors, each a 12 m (40 ft) blast: Dexterity save, 20d6 Fire + 20d6 Bludgeoning, half on a success.
- Fixed: the Wild Magic Darkness Shroud and Frozen Vortex statuses showed no visual (their effects didn't exist).
- Sangromancer (Grim Hollow wizard, new in DnD 5.5e 4.13.7): levels 13-20 - Red Renewal at 14 (your first Short Rest after a Long Rest restores Hit Point Dice and Full-Blooded dice equal to half your Wizard level), the Full-Blooded pool keeps growing to 1 + Wizard level, and Sangromancy Savant picks at 13, 15 and 17.
- Grim Hollow Sangromancy spells, 7th-9th level: Burst Forth, Sanguine Fusillade, Creeping Death, Red Rain, Steal Immortality - Hit Point Dice cost (a d6/d8/d10/d12 variant each, the d12 spends Full-Blooded) like DnD 5.5e's 1st-4th level ones, on the class lists their book tags give them, and offered by the Sangromancer's Savant picks at 13, 15 and 17. Sanguine Vigor works with them.
- Fixed: Hit Point Dice stopped at 12 for every base class; you now gain one per level through 20 (PHB 2024), which also gives short rests and Hit Point Dice costs their full range.
- Fixed: Barbarians and Clerics reaching level 12 got no Hit Point Die for that level.
- Fixed: Ranger Favored Enemy uses stopped at 4 (now 5 at level 13 and 6 at 17) and Wizard Arcane Recovery stopped at 6 (now 7, 8, 9, 10 at levels 13, 15, 17, 19), as in the PHB 2024.
- Fixed (found by a sweep of class resources against the PHB 2024): pools and uses that dnd55e stops growing at level 12 now keep growing - Celestial Healing Light (1 + level d6s), Circle of Dreams Balm (Druid level, with 7-10 dice spend options), Abjuration Arcane Ward (2 x level), Circle of the Land Natural Recovery (half the level), Zealot Warrior of the Gods (7 dice at 17), Alchemist elixirs (5 at 15), Artificer Magic Items (5 at 14, 6 at 18), Rune Knight runes and Runic Shield, Psi Warrior and Soulknife Psionic Energy Dice (10 at 13, 12 at 17), Swarmkeeper Writhing Tide, and the Proficiency Bonus uses of Dragonborn, Eladrin, Goliath, Shadar-kai and 13 feats (Lucky, Healer, Poisoner, the Giant feats ...).
- Fixed: Monk Unarmored Movement now reaches +25 ft at 14 and +30 ft at 18; Fighters get their sixth Weapon Mastery at 16.
- Fixed: Cleric Divine Spark now follows the PHB 2024 dice (1d8, 2d8 at 7, 3d8 at 13, 4d8 at 18; dnd55e used the cantrip steps); Life-Giving Force rolls 4d6 at 16; Venomous Strike keeps up with Sneak Attack's dice.
- Fixed: Beast Master companions and the Steel Defender grow after level 11 (+10 hit points at 13, 15, 17 and 19, and your Proficiency Bonus) instead of staying at their level 11 strength.
- New: the level 14 Artificer Replicate Magic Item plans - Armor +2 (the +1 armor becomes +2), Flame Tongue (+2d6 Fire), Arrow-Catching Shield and Ring of the Ram (three charges, 2d10 Force and a push each). Sun Soul Monks' Searing Arc Strike reaches spell levels 6-9 at Monk 14-20.
- New: Experimental Elixir at Artificer 15 offers five more in-game potions: Elixir of Cloud Giant Strength, Battlemage's Power, Viciousness, Guileful Movement and Barkskin.
- New: Circle of the Moon Wild Shape forms at the rules' Challenge Rating tiers (Druid level / 3): Elephant at 12 (CR 4), Triceratops at 15 (CR 5), Mammoth at 18 (CR 6), with Gore and Stomp attacks (re-skinned models).
- Fixed: Illusionist Phantasmal Creatures keeps pace with your spell slots - the Illusion Summon Beast and Summon Fey summon level 7, 8 and 9 creatures at Wizard 13, 15 and 17 (dnd55e stopped at level 6).
- Fixed: the Way of the Four Elements disciplines (Burning Hands, Fist of Unbroken Air, Shatter, Thunderwave, Water Whip, Ray of Frost, Shocking Grasp, Scorching Ray, Hold Person) get their ki steps at Monk 13 and 17.
- Requires DnD 5.5e All-in-One BEYOND 4.13.7.2 (was 4.13.7.1). Our upcast copies of smites, Armor of Agathys and Hail of Thorns and the Sneak Attack rules fixes carry its Hex fix: damage riders such as Hex no longer repeat on extra damage.

## v1.0.0 - 2026-10-11

First public release.

- Levels 13-20 for every class and subclass DnD 5.5e All-in-One BEYOND ships (including Artificer, Gunslinger, Illrigger and Monster Hunter), with each feature at its PHB 2024 level.
- 7th- to 9th-level spells and spell slots on each class's rules spell list, and upcasts of existing spells to 9th level.
- Epic Boons at level 19: the 12 PHB 2024 boons plus boons from Heroes of Faerun and Arcana Unleashed.
- Features that DnD 5.5e compresses below level 13 are moved back to their 2024 levels; levels 1-12 otherwise play as DnD 5.5e alone.
- Experience curve to level 20, with an optional multiplier (Mod Configuration Menu).
- Portal Jumper (Arcana Unleashed origin feat) in the Human origin feat pick; can be switched off in Mod Configuration Menu.
- Optional Mod Configuration Menu settings: XP gain multiplier and scope, Epic Boon level gate, Portal Jumper, debug logging.
- Built against DnD 5.5e All-in-One BEYOND 4.13.1.0.
