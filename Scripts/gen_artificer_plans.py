"""Artificer: the level 14 Replicate Magic Item plans (2026-10-13).

PHB 2024 / Forge of the Artificer (excerpts/classes/Artificer.txt) lists Magic Item Plans at Artificer levels 2, 6, 10 and 14. dnd55e
models plans as spells in the Replicate Magic Item container (Target_RMI_*) that put the item's effect on a creature as a status, and
stops at the level 10 list: every plan is available as soon as its level is reached (no plans-known choice), so "plans known 7 at
14 and 8 at 18" needs nothing; the 14+ list does:

  Armor, +2            Target_RMI_MagicArmor: the +1 status becomes +2 at 14 (as dnd55e does for the weapon, shield, wand and wraps at 10)
  Flame Tongue         +2d6 Fire on weapon attacks
  Arrow-Catching Shield  +2 AC while a shield is equipped (the book's bonus is against ranged attacks and adds a Reaction to take
                       the hit for a neighbour; the engine has no AC bonus per attack type, so it is a flat +2 here)
  Ring of the Ram      three charges (Long Rest): a ranged attack, 2d10 Force and a 1.5 m push per charge spent (the book recharges
                       1d3 a day; the spectral ram's +7 attack bonus is your spell attack)
Not modelled: "Rare Wondrous Item that isn't cursed" (a learn-it-repeatedly choice of any rare item). Ring of Free Action and Ring of
Protection are on the level 10 list in dnd55e (the 2024 table has them at 14); left as they are.

Experimental Elixir at 15 (user decision 2026-10-13): the book's elixirs get stronger at 15 (Healing 4d8, Speed +20 ft, Resilience 8 hours ...),
but dnd55e's are already the base game's potions (Healing Supreme is far above 4d8), so a stronger tier would only weaken them.
Instead the level 15 Artificer chooses from five more in-game elixirs (Rare, or Uncommon for Barkskin): Cloud Giant Strength,
Battlemage's Power, Viciousness, Guileful Movement, Barkskin. They go in the same Experimental Elixir container as dnd55e's
(Shout_EE_*; potion item icons, as dnd55e does) and cost the same elixir use.

Run: python3 Scripts/gen_artificer_plans.py   (after gen_class_resources.py in regen_all.sh)
"""
import glob
import os
import re

from gen_common import DND, Gen

G = Gen("rmi", "ARTIFICER PLANS 14")
LVL = "ClassLevelHigherOrEqualThan(14,'Artificer',context.Source)"


def dnd_field(entry, field, files="Spell*.txt"):
    for f in glob.glob(os.path.join(DND, "Stats", "Generated", "Data", files)):
        s = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(rf'new entry "{re.escape(entry)}"\r?\n(.*?)(?=\r?\nnew entry |\Z)', s, re.S)
        if m:
            v = re.search(rf'data "{field}" "([^"]*)"', m.group(1))
            if v:
                return v.group(1)
    raise SystemExit(f"{entry}.{field} not found in the dnd55e release (gen_artificer_plans.py)")


def plan(spell, status, title, text, boosts, icon, status_icon=None, extra=None):
    G.status(status, title, text, {"StatusType": "BOOST", "StackId": status, "Boosts": boosts, **(extra or {})},
             using="RMI_MAGICARMOR", icon=status_icon or icon)
    G.spell(spell, title, text, {"SpellType": "Target", "SpellProperties": f"ApplyStatus({status},100,-1);",
                                 "RequirementConditions": LVL + ";", "TooltipStatusApply": f"ApplyStatus({status},100,-1)"},
            using="Target_RMI_MagicArmor", icon=icon)


# Armor +2: dnd55e's Target_RMI_MagicArmor with a level 14 step
G.status("RMI_MAGICARMOR_2", "Armor, +2", "You have a +2 bonus to Armor Class while wearing armor.",
         {"StatusType": "BOOST", "StackId": "RMI_MAGICARMOR_2", "Boosts": "IF(WearingArmor(context.Source)):AC(2);"},
         using="RMI_MAGICARMOR", icon="PassiveFeature_MediumArmorMaster")
G.SP.append(G.entry("Target_RMI_MagicArmor", "SpellData", {
    "SpellProperties": "IF(not ClassLevelHigherOrEqualThan(14,'Artificer')):ApplyStatus(RMI_MAGICARMOR,100,-1);"
                       "IF(ClassLevelHigherOrEqualThan(14,'Artificer')):ApplyStatus(RMI_MAGICARMOR_2,100,-1);",
    "TooltipStatusApply": "ApplyStatus(RMI_MAGICARMOR,100,-1);ApplyStatus(RMI_MAGICARMOR_2,100,-1)"},
    using="Target_RMI_MagicArmor", comment="Armor +1 becomes +2 at Artificer 14 (gen_artificer_plans.py)"))

plan("Target_RMI_FlameTongue", "RMI_FLAMETONGUE", "Flame Tongue",
     "Your weapon attacks deal an extra 2d6 Fire damage while the item lasts.",
     "IF(IsWeaponAttack()):DamageBonus(2d6, Fire, false);", "Apo_Spell_FlameTongue", "Apo_Spell_FlameTongue")
plan("Target_RMI_ArrowCatchingShield", "RMI_ARROWCATCHING", "Arrow-Catching Shield",
     "You have a +2 bonus to Armor Class while you hold a shield.",
     "IF(HasShieldEquipped(context.Source)):AC(2);", "Apo_Spell_ArrowCatchingShield", "Apo_Spell_ArrowCatchingShield")

# Ring of the Ram: three charges per Long Rest, 2d10 Force and a push per charge spent
G.resource("ApoRamRing", 3, "Rest", "Ring of the Ram charges", "Charges of the Ring of the Ram you made with Replicate Magic Item.")
for n in (1, 2, 3):
    G.SP.append(G.entry(f"Projectile_Apo_RingOfTheRam_{n}", "SpellData", {
        "SpellProperties": "", "SpellSuccess": f"DealDamage({2 * n}d10,Force,Magical);Force({1.5 * n:g})",
        "SpellFail": "", "TooltipDamageList": f"DealDamage({2 * n}d10,Force)", "UseCosts": f"ActionPoint:1;ApoRamRing:{n}",
        "DisplayName": G.h(f"ram{n}:n", f"Ring of the Ram ({n} charge{'s' if n > 1 else ''})"),
        "Description": G.h(f"ram{n}:d", f"Spend {n} charge{'s' if n > 1 else ''} of the Ring of the Ram: a spectral ram's head makes a ranged attack against a creature "
                                       f"you can see; on a hit the target takes {2 * n}d10 Force damage and is pushed {5 * n} feet."),
        "Icon": "Apo_Spell_RingOfTheRam", "PowerLevel": str(n)}, using="Projectile_FireBolt"))
G.SP.append(G.entry("Projectile_Apo_RingOfTheRam", "SpellData", {
    "ContainerSpells": "Projectile_Apo_RingOfTheRam_1;Projectile_Apo_RingOfTheRam_2;Projectile_Apo_RingOfTheRam_3", "SpellFlags": "IsLinkedSpellContainer",
    "SpellSuccess": "", "SpellRoll": "", "TooltipDamageList": "", "UseCosts": "ActionPoint:1;ApoRamRing:1",
    "DisplayName": G.h("ram:n", "Ring of the Ram"),
    "Description": G.h("ram:d", "Spend 1 to 3 charges of the Ring of the Ram: a spectral ram's head makes a ranged attack; on a hit the target takes 2d10 Force damage and is pushed 5 feet for each charge spent."),
    "Icon": "Apo_Spell_RingOfTheRam"}, using="Projectile_FireBolt"))
G.status("RMI_RINGOFRAM", "Ring of the Ram", "A ring with three charges: spend them to ram a creature with spectral force (see the spell).",
         {"StatusType": "BOOST", "StackId": "RMI_RINGOFRAM",
          "Boosts": "ActionResource(ApoRamRing,3,0);UnlockSpell(Projectile_Apo_RingOfTheRam)"},
         using="RMI_MAGICARMOR", icon="Apo_Spell_RingOfTheRam")
G.spell("Target_RMI_RingOfTheRam", "Ring of the Ram", "A ring with three charges that fires a spectral ram's head (2d10 Force and a push per charge).",
        {"SpellType": "Target", "SpellProperties": "ApplyStatus(RMI_RINGOFRAM,100,-1);", "RequirementConditions": LVL + ";",
         "TooltipStatusApply": "ApplyStatus(RMI_RINGOFRAM,100,-1)"}, using="Target_RMI_MagicArmor", icon="Apo_Spell_RingOfTheRam")


ELIXIRS_15 = [  # spell, in-game potion template, item icon, name
    ("Shout_EE_CloudGiantStrength", "e6490cc8-7f81-4aac-95e8-a58ce5e88a31", "Item_CONS_Potion_Attack_Buff_A", "Elixir of Cloud Giant Strength"),
    ("Shout_EE_BattlemagesPower", "7d1699d9-c3fa-4761-9718-28230f78420b", "Item_ALCH_Solution_Elixir_ArcaneAcuity", "Elixir of Battlemage's Power"),
    ("Shout_EE_Viciousness", "44cd95a7-4791-4ace-bea0-a5ca4421171b", "Item_ALCH_Solution_Elixir_Criticals", "Elixir of Viciousness"),
    ("Shout_EE_GuilefulMovement", "b8a2f9e4-3b5e-4418-af05-5ca3cd40dd71", "Item_CONS_Potion_Gaseous_Form_A", "Elixir of Guileful Movement"),
    ("Shout_EE_Barkskin", "cc1a8802-675a-426b-a791-ec1d5a5b6328", "Item_CONS_Potion_Barkskin_A", "Elixir of Barkskin"),
]
for spell, tpl, icon, title in ELIXIRS_15:
    G.spell(spell, title, f"You create an {title}." if title[0] in "AEIOU" else f"You create a {title}.",
            {"SpellProperties": f"SummonInInventory({tpl},-1,1);", "RequirementConditions": LVL + ";"},
            using="Shout_EE_Bloodlust", icon=icon, comment="Experimental Elixir option at Artificer 15 (an in-game potion)")


def write():
    ee = dnd_field("Shout_ExperimentalElixir", "ContainerSpells").rstrip(";")
    G.SP.append(G.entry("Shout_ExperimentalElixir", "SpellData", {"ContainerSpells": ee.replace("Shout_EE_Resource_1", ";".join(x[0] for x in ELIXIRS_15 if x[0] not in ee) + ";Shout_EE_Resource_1", 1) + ";"},
                        using="Shout_ExperimentalElixir", comment="the level 15 elixirs (re-read from dnd55e at each regen)"))
    cont = dnd_field("Target_ReplicateMagicItem", "ContainerSpells").rstrip(";")
    new = ["Target_RMI_FlameTongue", "Target_RMI_ArrowCatchingShield", "Target_RMI_RingOfTheRam"]
    G.SP.append(G.entry("Target_ReplicateMagicItem", "SpellData", {"ContainerSpells": cont + ";" + ";".join(x for x in new if x not in cont) + ";"},
                        using="Target_ReplicateMagicItem", comment="the level 14 plans (re-read from dnd55e at each regen)"))
    G.write_stats("ArtificerPlans", "gen_artificer_plans.py", "Artificer plans 14")
    G.patch_files()
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(G.SP)} spells, {len(G.S)} statuses, {len(G.resources)} resource")
