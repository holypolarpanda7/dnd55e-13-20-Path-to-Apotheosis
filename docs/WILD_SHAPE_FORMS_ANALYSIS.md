# Wild Shape forms at 13-20: analysis (2026-10-13)

Question: the PHB 2024 Circle of the Moon allows forms up to CR = Druid level / 3 (CR 4 at 12, 5 at 15, 6 at 18). What would new
forms take, and is "new forms" even the right fix? Findings first, then the options and a recommendation. Nothing is built.

## What the rules ask for

- Beast Shapes table (every Druid): known forms 4 / 6 / 8, max CR 1/4 / 1/2 / 1 and a Fly Speed, all reached at Druid 8; nothing
  after 8. Temporary Hit Points on shape-shift = Druid level (done: `WILDSHAPE_TEMPHP_DRUIDLEVEL`).
- Circle of the Moon: max CR = Druid level / 3, AC 13 + Wisdom if higher, Temporary Hit Points = 3 x Druid level (per level, done).
  Improved Circle Forms (6) and the 10 and 14 features are present.

## What the game has

Forms are spells (`Shout_WildShape_Combat_*`, bonus action, one Wild Shape use) that apply a polymorph status. dnd55e's lists:

| Druid level | Forms |
| --- | --- |
| 2 | Badger, Polar Bear, Cat, Spider, Dire Wolf |
| 4 | Deep Rothe, Raven |
| 6 | Panther, Owlbear |
| 8 | Saber-toothed Tiger |
| 10 | Dilophosaurus; Moon only (base game): the four Myrmidons (Air, Earth, Fire, Water: the base list "Druid Elemental Wild Shape") |

Not on any list but present as player-form templates: Displacer Beast (`Displacer_Beast_PlayerWildshape`), Intellect Devourer.
Other creature models in the base game that are not wild shape forms yet: Bulette, Hook Horror, Ankheg, Giant Crab, Worg and
others (no elephant, mammoth, ape, crocodile or tyrannosaur).

## The bigger problem: forms stop scaling at 12

The base game does not use the stat blocks; every form comes in a template per band of two levels (`Bear_Polar_PlayerWildshape`,
`_4`, `_6`, `_8`, `_10`, `_12`) with growing hit points. The top band is 12:

| Form | Vitality by band (base, 4, 6, 8, 10, 12) |
| --- | --- |
| Polar Bear | 30, 39, 51, 66, 86, **111** |
| Dire Wolf | 18, 25, 35, 49, 69, **97** |
| Panther | 45, -, -, 54, 60, **68** |
| Owlbear / Dilophosaurus | 112 / 96 at band 12 |

A Druid 20 turns into the level 12 form: the same hole as the Hit Point Dice and the Beast Master companions (which were fixed with a
status applied on summoning). The missing CR 4-6 forms are therefore the smaller half of the gap: every existing form is also
under-strength for 13-20, and the Moon's Myrmidons (CR 7 in the Monster Manual) already exceed the CR 6 the rules allow at 18.

## Options

**A. Scale the existing forms at 13, 15, 17, 19 (recommended first).** Like the companion bands: the form spell applies an extra status
on shape-shifting (`APO_WILDSHAPE_HIGH_n`): +hit points per band (the base game adds about +25 per two levels at the top: polar bear
86 to 111), your Proficiency Bonus, and the Moon's attack and damage steps. Covers all 18 forms and both subclass kinds with one
generator; no models, templates or new spells. Work: find how the base game picks the band (a status per band chosen in the form
spell's `SpellProperties`, or in the status's template choice), then extend each form spell the way `summon_bands()` does in
`gen_class_resources.py`. About a day with tests (the polymorph status chain is the risk: statuses that end with the form).

**B. Unlock more of the forms that exist.** Add the Displacer Beast (a CR 3 beast with a player template) to the Moon at 12, and
move or duplicate the Myrmidons to the Moon's 15 / 18 (they are CR 7; accept the overshoot or keep them at 10 and add forms only).
Each new form needs its band chain (the Displacer Beast has a single template), a spell, an icon and loca. Small, but it gives one to
four forms, not a CR curve.

**C. New CR 4-6 forms from base-game models.** Candidate stat blocks from the Monster Manual that have a usable base model: Giant
Boar / Worg variants (CR 2-3, too low), Ankheg (CR 2), Hook Horror (CR 3, not a beast), Bulette (CR 5, a Monstrosity: not a legal Wild
Shape form in the 2024 rules, which allow Beasts only). The beasts the rules want at CR 4-6 (elephant CR 4, giant crocodile CR 5,
triceratops CR 5, mammoth CR 6, giant ape CR 7) have no model in the game, so a new form would reuse a mismatched model (a bear or
the Dilophosaurus scaled up) with new stats: it plays right and looks wrong.

**D. New creature models.** A real elephant / mammoth needs new meshes, skeletons and animations (GR2 export through the planned
Blender pipeline, see the assets roadmap): the cleanest result and by far the largest job. Not feasible in the near term.

## Recommendation

1. Do **A** (the existing forms keep up with the Druid's level): it fixes every Druid 13-20, not just Moons, and uses machinery we
   already have. Test with Moon and Land builds at 13 / 15 / 17 / 19.
2. Then **B** for variety (Displacer Beast at 12, Myrmidons for the Moon's higher steps), each with a new icon.
3. Hold **C** and **D**. If a CR 4-6 Moon form is wanted, take the beasts the rules list, build them as scaled re-skins (C) and flag
   them as such in the description, or wait for models (D).

Open questions for you: is A's "forms keep scaling" in scope for this release? Should the Moon's higher forms be gated on the
Druid level at 12 / 15 / 18 (the CR / 3 steps) or follow dnd55e's own (tier at 10)? Is a stand-in model acceptable for C?
