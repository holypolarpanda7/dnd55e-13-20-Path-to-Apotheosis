# dnd55e findings (candidates for upstream reports) - 2026-10-03

Found by `bg3_lint_progressions` on the dnd55e layer (dnd55e 2026-10-02 14:08 CDT). Not verified in game yet; each
needs a character of that subclass levelled through the listed level before reporting (dnd55e-fork workflow).

- **Stacked subclass choice nodes.** For these tables a base-game node and a dnd55e node with *different* UUIDs sit
  at the same level and both carry Selectors, so both load: the choices (e.g. Nature Domain's skill pick, the domain
  spell lists) may be offered/granted twice. NatureDomain L3/5/7/9, TempestDomain L3/5/7/9, EnchantmentSchool L3/5
  (UUIDs swapped between base and dnd55e), BattleMaster L3 (two dnd55e nodes).
- **Lay on Hands** is a charge pool (3 at 1, +1 at 4 and 10) rather than the 2024 5 x Paladin level Hit Points; not
  extended past 12 here because it's dnd55e's own model.
- **Compressed level maps** (decided 2026-10-03: Apotheosis restores the PHB 2024 steps, see `gen_levelmaps.py` FIX /
  MOVE_10_TO_11; verified in game): Sneak Attack 7d6 at 11 (2024: 6d6; 7d6 at 13), cantrip dice / Eldritch Blast /
  True Strike / Booming Blade / Breath Weapon third tier at 10 (2024: 11), Land's Aid 3d6 at 5 / 4d6 at 10 (2024: 10 / 14).
  Worth reporting upstream if dnd55e wants the same: base BG3 compresses the cantrip tiers (5/10) for its 12-level cap.

## Filed upstream (2026-10-03, against 4.12.18.1; repo is Yoonmoonsik/bg3dnd)

- [#1539](https://github.com/Yoonmoonsik/bg3dnd/issues/1539) Danse Macabre can't be cast: it inherits from the emptied
  `Target_AnimateDead_Ghoul*` entries (no SpellAnimation). Repro: `tests/bg3/upstream_bugs.toml` (the Danse Macabre case
  fails, its control `Target_SummonUndead_6` passes).
- [#1540](https://github.com/Yoonmoonsik/bg3dnd/issues/1540) `Target_Awaken_6` has no UseCosts and spends a 5th level slot.

- [#1556](https://github.com/Yoonmoonsik/bg3dnd/issues/1556) War Domain Cleric never gets Guided Strike: it's on the War
  Domain's level 2 node (2014 layout) while the Cleric now picks its subclass at 3, so the node is never applied (seen in game
  2026-10-04, found by the class test builds + the progression lint's "subclass nodes below the subclass level" rule).
Not filed: the stacked Nature / Tempest / Enchantment / Battle Master choice nodes. Verified at data level only (the base
game's Nature Domain level 3 node and dnd55e's both load); whether the level-up UI offers the choices twice needs a
level-up in game, and the project only takes confirmed bugs from a fresh campaign. The issues above state plainly that the
template's fresh-campaign / no-other-mods checks were not done (the findings are in the release data files).
