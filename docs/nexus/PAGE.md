# Nexus Mods page (draft 2026-10-06)

Fields for creating the page at nexusmods.com/baldursgate3 (Upload a mod). The description below is BBCode, ready to paste.
Items marked **DECIDE** are the author's call.

| Field | Value |
| --- | --- |
| Name | Path to Apotheosis - Levels 13-20 for DnD 5.5e All-in-One |
| Category | Classes (or Gameplay) - **DECIDE** |
| Version | from the release (`python -m bg3data.release package apotheosis` prints it) |
| Summary (350 chars max) | Raises the level cap from 12 to 20 on top of DnD 5.5e All-in-One BEYOND: every class and subclass feature for levels 13-20 at its 2024 level, 7th- to 9th-level spells and slots, upcasts to 9th level and the Epic Boons at 19. PHB 2024 is the source of truth. |
| Requirements | DnD 5.5e All-in-One BEYOND (Nexus mod 12727); Norbyte's BG3 Script Extender |
| Adult content | No |
| Permissions | **DECIDE** (see note at the end) |
| File | the zip from `release package` (pak + info.json + README + CHANGELOG): main file, "Path to Apotheosis vX" |
| Images | **TODO** - level-up screens at 13-20, a 9th-level spell, the Epic Boon picker (bg3_screenshot) |

## Description (BBCode)

```
[size=5][b]Path to Apotheosis[/b][/size]
[i]Levels 13-20 for DnD 5.5e All-in-One BEYOND[/i]

Baldur's Gate 3 stops at level 12, and so does DnD 5.5e. [b]Path to Apotheosis[/b] takes every class to [b]level 20[/b]: the full D&D curve, following the [b]2024 Player's Handbook[/b] and built on top of DnD 5.5e rather than replacing it.

[size=4][b]What it adds[/b][/size]
[list]
[*][b]Levels 13-20 for every class[/b] DnD 5.5e ships, including its Artificer, Gunslinger, Illrigger and Monster Hunter.
[*][b]Subclass features 13-20[/b], each at its 2024 level.
[*][b]7th-, 8th- and 9th-level spells and spell slots[/b], on each class's rules spell list, learned through the normal level-up screen.
[*][b]Upcasting to 9th level[/b] for existing spells.
[*][b]Epic Boons at level 19[/b]: all 12 from the 2024 PHB, plus boons from Heroes of Faerûn and Arcana Unleashed.
[*][b]Features back at their real levels[/b]: DnD 5.5e squeezes some level 13+ features into lower levels to fit the cap. Apotheosis moves them back to their 2024 levels. Apart from that, levels 1-12 play exactly as DnD 5.5e alone.
[/list]

[size=4][b]How it's tested[/b][/size]
Every class/subclass build is levelled 1 to 20 in the running game by an automated test harness. Each level-up screen is checked against the rules (features, choices and counts), and the new features are cast and checked in staged encounters. Rules accuracy beats homebrew: if a feature can't be done faithfully with stats, it uses Script Extender; if neither can, the gap is documented.

[size=4][b]Requirements[/b][/size]
[list]
[*][url=https://www.nexusmods.com/baldursgate3/mods/12727]DnD 5.5e All-in-One BEYOND[/url] (load it [b]before[/b] Path to Apotheosis)
[*][url=https://github.com/Norbyte/bg3se]BG3 Script Extender[/url]
[/list]

[size=4][b]Installation[/b][/size]
[list=1]
[*]Install the requirements.
[*]Install this mod with Vortex or BG3 Mod Manager (the zip includes info.json), or put the .pak in your Mods folder and enable it.
[*]Load order: DnD 5.5e All-in-One BEYOND, then Path to Apotheosis.
[/list]

[size=4][b]Compatibility[/b][/size]
[list]
[*]Made for the current DnD 5.5e release; when DnD 5.5e updates, check here for a matching update.
[*]Other mods that change the level cap, XP table or class progressions above 12 will conflict.
[*]Existing saves: [b]DECIDE / test[/b] (new game recommended until verified).
[/list]

[size=4][b]Known gaps[/b][/size]
A few subclasses have no published level 13+ text yet. They are listed with their sources in the project's [url=https://github.com/holypolarpanda7/dnd55e-13-20-Path-to-Apotheosis/blob/main/docs/COVERAGE.md]coverage notes[/url].

[size=4][b]Credits[/b][/size]
[list]
[*]Yoonmoonsik and contributors for DnD 5.5e All-in-One, which this builds on.
[*]Norbyte for the Script Extender and LSLib.
[/list]

Source, issues and changelog: [url=https://github.com/holypolarpanda7/dnd55e-13-20-Path-to-Apotheosis]GitHub[/url]
```

## Before publishing

- **Permissions check against DnD 5.5e:** the generators read DnD 5.5e's released pak, and some of our files override its
  entries (progression nodes, lists). Check DnD 5.5e's Nexus permissions tab for "modify / use assets" terms, and credit or ask
  the author as those terms say. Its author rejected automated reports on 2026-10-05, so any contact should come from you.
- **Script Extender link:** use its Nexus page if you prefer a Nexus requirement (adds the "required" banner) - pick it in the
  requirements picker rather than trusting an ID from memory.
- **Coverage notes are stale:** docs/COVERAGE.md "Missing subclass extensions" predates the 2026-10-03/04 work; refresh it
  before the page links to it.
