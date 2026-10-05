# Sources for dnd55e's third-party subclasses (researched 2026-10-03)

`Scripts/subclass_gap_audit.py` lists dnd55e subclasses with no features past level 12. dnd55e's wiki
(`github.com/Yoonmoonsik/bg3dnd/wiki`, cloned from `bg3dnd.wiki.git`) describes what it built but names no sources, so the
sources below were found by web search on feature names (VISION principle 1: follow the source dnd55e uses; principle 4:
no homebrew). dnd55e often rewrites its subclasses for the 2024 rules (features moved, merged or reworked), so a source's
13+ feature is only "missing" if dnd55e didn't already fold it into levels 1-12.

Status: BUILT = in `Scripts/gen_subclass_features.py` and tested in game; TEXT = source text found, not built yet; NO TEXT =
source identified but its rules text isn't reachable (paid book, site blocks automated fetches); UNKNOWN = no source found.

| Class | Subclass | Source (confidence) | Source's 13+ features | Status |
| --- | --- | --- | --- | --- |
| Barbarian | Shadow Gnawer | Book of Ebon Tides, Open Design 2022 (OGL, 5esrd) - certain | 14 Corrosive Haze | BUILT |
| Cleric | Shadow Domain | Book of Ebon Tides, Open Design 2022 (OGL, 5esrd) - certain | 17 Army of Shadow | BUILT |
| Cleric | Mind Domain | Exploring Eberron, Keith Baker (dnd5e.wikidot "Mind Domain (HB)") - certain | 17 Bend Reality | BUILT (interrupt is a manual check) |
| Rogue | Highway Rider | Grim Hollow Player's Guide (Nieb's Critical Collection mirror) - certain | 13 True Grit, 17 Desperado | 13 BUILT (Constitution proficiency only); 17 BUILT (free weapon attack option only) |
| Rogue | Arachnoid Stalker | Valda's Spire of Secrets, Mage Hand Press, 2024 version (magehandpress.com/2024/10/arachnoid-stalker) - certain | 13 Web Walker, 17 Paralytic Venom | 13 BUILT; 17 TEXT (dnd55e already has a Cunning Strike Paralytic Venom at 9) |
| Druid | Circle of Dragons | The Griffon's Saddlebag: Book Two - certain | 14 Heart of a Dragon (breath weapon outside dragon form, AC 16 + Dex max 2, Fly 40, three attacks, Large form) | BUILT, tested in game 2026-10-04 (References/Subclasses/griffons_saddlebag_circle_of_dragons.txt): in dragon shape AC 16 + Wisdom (dnd55e's form uses Wisdom, not Dex; 21 vs the form's 20 on a Wis 20 Druid), ExtraAttack_2, Movement +3 m; no 30-foot cone, Large form or exact 40-foot Fly |
| Druid | Circle of the Unbroken | The Griffon's Saddlebag: Book One (Bell of Lost Souls) - certain | 14: Shillelagh Mastery d12 | NO TEXT |
| Bard | College of Choreography | The Griffon's Saddlebag: Book One (Hit Point Press; D&D Beyond source gsb1) - certain; the PHB 2024 College of Dance pasted 2026-10-04 is a different subclass | 14 Fast Movement +5 ft, Entrancing Movement (Irresistible Dance), Endless Dance (page photographed by the user 2026-10-04, shown in the Griffon's Saddlebag as "College of Dance") | BUILT, tested in game 2026-10-04 |
| Cleric | Astral Domain | The Griffon's Saddlebag: Book One - certain | 17 Supreme Switching (upgrades Spatial Exchange / Misty Step) | NO TEXT |
| Cleric | Dragon Domain | Valda's Spire of Secrets: Player Pack 2 - certain (dnd55e owner, bg3dnd discussion #1568, 2026-10-05) | 17: ? | NO TEXT (17 feature unknown until the Player Pack 2 text is available) |
| Sorcerer | Heroic Sorcery | Valda's Spire of Secrets "Heroic Bloodline" (capstone: Haste without Concentration) - likely; dnd55e's version (Heroic Spells, Martial Sorcery, Extra Attack, War Magic) is a rework | 14 / 18: ? | NO TEXT (Mage Hand Press's 2017 "Reincarnated Hero" is a different, older subclass) |
| Fighter | Viking | Kobold Press, Northlands Worldbook (Seaborne, Savage Charge, Call of the Northlands) - certain | 15 Marauder's Reprisal, 18 Unstoppable Assault (levels per the dnd55e gap) | NO TEXT |
| Rogue | Blade of Radiance | Steinhardt's Guide to the Eldritch Hunt (World Anvil homebrew, masongarth2000) - certain | 13 / 17: ? (Chains of Judgement, Divine Retaliation are 9) | NO TEXT (World Anvil returns 403) |
| Barbarian | Fractured | Grim Hollow, "Barbarian: Path of the Fractured" (grimhollow.fandom.com, Scribd copy) - certain | 14: ? (3 Face of Rage / Mask of Civility, 6 Brains and Brawn, 10 Cunning and Brutal) | NO TEXT (fandom returns 402) |
| Cleric | Apocalypse Domain | Cthulhu by Torchlight - certain (dnd55e owner, bg3dnd discussion #1567, 2026-10-05) | ? | NO TEXT (17 feature unknown until the book's text is available) |
| Sorcerer | Frost Sorcery | dandwiki "Frost Sorcery" is a different design | ? | UNKNOWN |

Built with a known gap:
- **Highway Rider 17 Desperado** ("reduced to 0 HP: use your Reaction for one Hair Trigger action before you fall"): a stand-in
  `DownedStatus` plus a Lua hook fires a free Hair Trigger attack (Advantage) at the nearest hostile, then the character
  falls. Only the attack option of Hair Trigger is offered (no move / Dodge / use object choice).
- **True Grit's Evasion-style half**: the engine's Evasion is Dexterity-only, so only the Constitution proficiency is built.

To finish a NO TEXT row, add the book's text under `References/Subclasses/` (or The Oracle's `owned_books`) and its features to
`Scripts/gen_subclass_features.py`. `Scripts/regen_all.sh` then regenerates everything.

Also open (not sourcing gaps): the half-caster 13/17 spells BG3 doesn't have (`Scripts/gen_subclass_spells.py` MISSING).

Built from `References/Subclasses/missing_subclass_ref.txt` on 2026-10-04, all tested in game the same evening (host mechanism cases + nine builds 2-20, every level check clean): Unbroken 14 Nature Armor, Fractured 14 Better Half, Astral 17 Supreme Switching, Viking 15 Marauder's Reprisal / 18 Unstoppable Assault, Blade of Radiance 13 Saintly Revelations / 17 Final Judgement. Arachnoid 17 Paralytic Venom is skipped: dnd55e's level 9 Paralytic Venom already paralyses on a Constitution save.
