# Path to Apotheosis: Vision

## Goal

Baldur's Gate 3, even with dnd55e, is designed for levels 1–12. **Path to Apotheosis raises that to the
full level 1–20 D&D experience.** It adds every class and subclass feature for levels 13–20, 7th- to
9th-level spells and slots, and the content needed to support play at those levels.

## Principles

1. **PHB 2024 is the source of truth.** Class and subclass features, spell text and level placement
   follow the 2024 rules. For subclasses outside the PHB, follow the source dnd55e uses for them.
2. **Every feature at its 2024 level.** dnd55e compresses features above level 12 into lower levels to
   fit its cap (for example, Psychic Veil at Soulknife 9 when the rules say 13). Apotheosis moves them
   back: a `PassivesRemoved` node at dnd55e's level and a `PassivesAdded` node at the 2024 level.
3. **Build on dnd55e; don't replace it.** dnd55e is a dependency. Where dnd55e already has a feature,
   use its implementation unless ours is more accurate. Don't override dnd55e entries just to change
   them. The level 1–12 game must play the same as dnd55e alone, apart from moving compressed features
   back to their 2024 levels (principle 2).
4. **Accuracy over homebrew.** Implement the feature as written. Never replace a rule with a different
   mechanic because it's easier.
   - **Stats first.** Use stats, statuses, passives and progressions when they can express the rule
     faithfully. They're the most compatible and stable across saves.
   - **Script Extender when stats can't.** Apotheosis already requires Script Extender and dnd55e
     doesn't use it, so things out of reach for dnd55e are possible for us. Examples: turn and action
     manipulation (Time Stop), changing an existing aura's radius (Aura Expansion), movement or
     targeting rules, and bookkeeping like "once per long rest unless you spend a resource". Scripted
     features must log through `Apotheosis.Log`, get a `FeatureTests.lua` entry, and never change
     dnd55e's level 1–12 behavior.
   - **Document what's left.** Only when neither can do it, use the closest faithful approximation and
     document the gap.
5. **Complete the curve.** Fill gaps at levels 13–20 for every class and subclass dnd55e ships:
   features, 7th- to 9th-level spells, upcasts of existing spells to 9th level, spell slots, XP and the
   level cap.
6. **Stay in sync with dnd55e.** dnd55e changes often. Re-audit against the current upstream
   reference clone (`../dnd55e`): `Scripts/compat_audit*.py`, `Scripts/build_all_class_expectations.py`.
   When dnd55e adds something we also built, compare the two (principles 1–4) and keep the better
   one.

## Check before acting

Before any change, confirm:

- [ ] Does it move the game toward complete 1–20 play (the goal)?
- [ ] Does it match the 2024 rules text and level (principles 1 and 2)?
- [ ] Does dnd55e already have it? If so, whose version is more accurate, and at what level (principle 3)?
- [ ] Does it leave dnd55e's levels 1–12 unchanged, apart from moving compressed features back
      (principle 3)?
- [ ] If stats can't express it faithfully, can a Script Extender script? Only if neither can: is the
      approximation the closest possible, and is the gap documented (principle 4)?

## Approved exceptions

Deliberate additions outside levels 13–20, each approved by the user and to be dropped once dnd55e ships its own.

- **Portal Jumper origin feat** (Arcana Unleashed), approved 2026-10-10. dnd55e doesn't have the feat yet and its author plans
  to add the Arcana Unleashed origin feats. Offered in the Human origin-feat pick through a `MergedInto` passive list (dnd55e's
  list is not overridden), switchable in MCM (`portal_jumper`). Generator `Scripts/gen_portal_jumper.py`, Lua
  `PortalJumper.lua`. Principle served: accuracy (4) — rules text from the shared library, no homebrew.
