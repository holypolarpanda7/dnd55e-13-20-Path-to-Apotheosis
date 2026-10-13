# Wild Shape forms at 13-20 (2026-10-13)

Started as an analysis, now also the record of what was built (`Scripts/gen_wildshape_forms.py`). Decision (user, 2026-10-13): scaling
is in scope, it follows the rules' tiers, and re-skinned models are fine.

## What the rules ask for

- Beast Shapes table (every Druid): known forms 4 / 6 / 8, max CR 1/4 / 1/2 / 1 and a Fly Speed, all reached at Druid 8; nothing after 8.
  Temporary Hit Points on shape-shift = Druid level (done: `WILDSHAPE_TEMPHP_DRUIDLEVEL`).
- Circle of the Moon: max CR = Druid level / 3 (CR 4 at 12, 5 at 15, 6 at 18), Temporary Hit Points = 3 x Druid level, AC 13 + Wisdom if
  higher (both per level already).

## What the game has (corrected)

Forms are spells (`Shout_WildShape_Combat_*`, bonus action, one Wild Shape use) that apply a POLYMORPHED status; the status names a
character root template (model, Character stats, the attack spells as the template's skill list). dnd55e's combat forms each use one
template at the base stats (Polar Bear 30 HP, Owlbear 65, Dilophosaurus 74) plus the Temporary Hit Points; the damage of their attacks is
`LevelMapValue(WildShapeDamageLow/Medium)` (1d8 / 1d10 by 12, capped there). (My first draft of this doc said the forms stop scaling at a
"band 12" template: that is the base game's own non-combat path and the Myrmidons' `_12` status; dnd55e's combat forms don't use the bands.)

dnd55e's lists: Druid 2 Badger, Polar Bear, Cat, Spider, Dire Wolf; 4 Deep Rothe, Raven; 6 Panther, Owlbear; 8 Saber-toothed Tiger;
10 Dilophosaurus; the Moon also gets the four Myrmidons at 10 (the base game's "Druid Elemental Wild Shape" list).

## Built: one new Moon form per CR tier

| Moon level | Form | CR | HP | AC | Str | Attacks | Re-skinned from |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | Elephant | 4 | 76 | 12 | 22 | Gore 3d8+6 Piercing; Stomp 3d10+6 Bludgeoning (a Prone target) | Polar Bear |
| 15 | Triceratops | 5 | 114 | 13 | 22 | Gore 4d8+6; Stomp 3d10+6 (a Prone target) | Dilophosaurus |
| 18 | Mammoth | 6 | 126 | 13 | 24 | Gore 4d8+7; Stomp 4d10+7 (a Prone target) | Owlbear |

Monster Manual 2024 Beasts; Trampling Charge is not modelled. Each form is a child of the Moon's `Shout_WildShape_Combat` container (one
Wild Shape use, a bonus action) unlocked by a Moon progression node at 12 / 15 / 18; Primal Strike's Radiant swap (`LunarRadiance`) works
as on the existing forms. New icons: the three forms, Gore and Stomp. Not done: other Druids stay on the Beast Shapes table (as the rules
say), the existing forms keep dnd55e's lists and damage maps (dnd55e gives the Moon the Owlbear at 6 and the Myrmidons at 10, ahead of the
CR / 3 rule: its design, left alone).

## Still open

- Visual fit of the re-skins (a bear for an elephant, an owlbear for a mammoth) is to be judged in game; the template's `Scale` or a
  different parent can change it without touching anything else.
- To verify in game: a Moon 12 / 15 / 18 build gets the spell in the Wild Shape container, the form's HP / attacks / Stomp condition and
  the Primal Strike Radiant swap, and the form ends cleanly (the status chain is the Owlbear's: `WILDSHAPE_OWLBEAR_PLAYER`).
- The existing forms' attack dice stop at 12 (`WildShapeDamageLow/Medium`); the rules give forms their stat-block damage and no growth, so
  nothing is added.
