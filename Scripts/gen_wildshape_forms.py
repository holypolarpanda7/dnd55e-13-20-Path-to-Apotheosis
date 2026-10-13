"""Circle of the Moon: Wild Shape forms at the rules' CR tiers (2026-10-13; user decision: follow the true tiers, re-skins are fine).

PHB 2024: a Moon Druid's Wild Shape form may have a Challenge Rating up to Druid level / 3 - CR 4 at 12, 5 at 15, 6 at 18 (the other
Druids stay on the Beast Shapes table, which ends at 8). dnd55e's Moon list ends at its level 10 forms and the game has no CR 4-6
beast models, so each tier gets one new form on a re-skinned model (the parent template supplies the look):

  Moon 12  Elephant     CR 4   76 HP  AC 12  Str 22   Gore 3d8+6 Piercing, Stomp 3d10+6 Bludgeoning (a Prone target)   model: Polar Bear
  Moon 15  Triceratops  CR 5  114 HP  AC 13  Str 22   Gore 4d8+6 Piercing, Stomp 3d10+6 Bludgeoning (a Prone target)   model: Dilophosaurus
  Moon 18  Mammoth      CR 6  126 HP  AC 13  Str 24   Gore 4d8+7 Piercing, Stomp 4d10+7 Bludgeoning (a Prone target)   model: Owlbear

Stat blocks from the Monster Manual 2024 (Beasts); Trampling Charge is not modelled. Built the way the base game's forms are: a character
root template (with its attack spells as the template's skills) + a Character stats entry + a POLYMORPHED status + the form spell
(a child of the Moon's Shout_WildShape_Combat container, one Wild Shape use and a bonus action), the form spell unlocked by a Moon node at
12 / 15 / 18. The damage is the stat block's, not dnd55e's WildShapeDamage level maps (those stay for the existing forms).

Run: python3 Scripts/gen_wildshape_forms.py
"""
from gen_common import Gen, patch_progressions

G = Gen("wsforms", "WILD SHAPE FORMS")
MOON = "ede8583c-434b-4fb2-87a8-af8e0e239d62"
SPELL_LEVEL = {"Elephant": 12, "Triceratops": 15, "Mammoth": 18}

FORMS = {  # name: dict(cr, parent template, parent Character stats, stats, ...)
    "Elephant": dict(cr=4, parent="960a6318-3fc0-4b85-8b70-887e99ff248f", base="Bear_Polar_Wildshape", hp=76, ac=12, move=12,
                     abil=(22, 9, 17, 3, 11, 6), gore="3d8", stomp="3d10", icon="Apo_Spell_WildShapeElephant"),
    "Triceratops": dict(cr=5, parent="fca74933-fb42-45c0-af31-c9f806368453", base="Dilophosaurus_Wildshape", hp=114, ac=13, move=15,
                        abil=(22, 9, 17, 2, 11, 5), gore="4d8", stomp="3d10", icon="Apo_Spell_WildShapeTriceratops"),
    "Mammoth": dict(cr=6, parent="92467fe9-2452-47f4-8c19-59883cca6dc5", base="Wildshape_Owlbear", hp=126, ac=13, move=12,
                    abil=(24, 9, 21, 3, 11, 6), gore="4d8", stomp="4d10", icon="Apo_Spell_WildShapeMammoth"),
}
NODES = []

for name, f in FORMS.items():
    mod = (f["abil"][0] - 10) // 2
    low = name.lower()
    gore, stomp = f"Target_Apo_WildShape_{name}_Gore", f"Target_Apo_WildShape_{name}_Stomp"
    for spell, dice, kind, title, text, extra in [
        (gore, f["gore"], "Piercing", "Gore", "Gore with your horns or tusks: a melee attack for {d} + your Strength modifier Piercing damage.", {}),
        (stomp, f["stomp"], "Bludgeoning", "Stomp", "Stomp a Prone creature: a melee attack for {d} + your Strength modifier Bludgeoning damage.",
         {"TargetConditions": "not Self() and not Dead() and HasStatus('PRONE',context.Target)"}),
    ]:
        dmg = f"max(1,{dice}+UnarmedMeleeAbilityModifier)"
        G.spell(spell, f"{title} ({name})", text.format(d=dice), {
            "SpellSuccess": (f"IF(not HasPassive('LunarRadiance',context.Source)):DealDamage({dmg},{kind},Magical);"
                             f"IF(HasPassive('LunarRadiance',context.Source)):DealDamage({dmg},Radiant,Magical);"),
            "TooltipDamageList": f"DealDamage({dice}+UnarmedMeleeAbilityModifier,{kind})", "DamageType": kind, **extra},
            using="Target_Claws_Owlbear_WildShape", icon="Apo_Action_Gore" if spell == gore else "Apo_Action_Stomp")
    G.character(f"Wildshape_Apo_{name}", {
        "Strength": f["abil"][0], "Dexterity": f["abil"][1], "Constitution": f["abil"][2], "Intelligence": f["abil"][3],
        "Wisdom": f["abil"][4], "Charisma": f["abil"][5], "Armor": f["ac"], "Vitality": f["hp"],
        "ActionResources": f"ActionPoint:1;BonusActionPoint:1;Movement:{f['move']};ReactionActionPoint:1",
        "Passives": "AttackOfOpportunity;DarknessRules", "UnarmedAttackAbility": "Strength", "UnarmedRangedAttackAbility": "Strength"},
        using=f["base"], comment=f"Monster Manual 2024 {name} (CR {f['cr']}), a Beast")
    tpl = G.template(f"form{name}", f"Apo_{name}_PlayerWildshape", f["parent"], f"Wildshape_Apo_{name}", f"{name} (Wild Shape)",
                     skills=[gore, stomp], spellset="CommonSummonActions")
    status = f"WILDSHAPE_APO_{name.upper()}_PLAYER"
    G.status(status, f"{name} Form", f"You have taken the form of a {low}.", {"TemplateID": tpl}, using="WILDSHAPE_OWLBEAR_PLAYER", icon=f["icon"])
    form = f"Shout_WildShape_Combat_Apo_{name}"
    G.spell(form, name, f"Assume the form of a {low} (Challenge Rating {f['cr']}): {f['hp']} Hit Points, AC {f['ac']}, Strength {f['abil'][0]}; "
                        f"Gore and Stomp attacks. Circle of the Moon, Druid level {SPELL_LEVEL[name]}.",
            {"SpellProperties": f"ApplyStatus({status},100,-1);", "ExtraDescriptionParams": f"RegainHitPoints({f['hp']})"},
            using="Shout_WildShape_Combat_Owlbear", icon=f["icon"])
    NODES.append((MOON, "CircleOfTheMoon", 1, SPELL_LEVEL[name], {"Boosts": f"UnlockSpell({form})"}))


def write():
    G.write_stats("WildShapeForms", "gen_wildshape_forms.py", "Moon forms at CR 4-6")
    G.write_templates("Apotheosis_WildShape")
    G.patch_files()
    patch_progressions({}, [(G.gid(f"node:{t}:{lv}"), n, lv, pt, t, a) for t, n, pt, lv, a in NODES], G.marker)
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(FORMS)} forms: {len(G.SP)} spells, {len(G.S)} statuses, {len(G.C)} characters, {len(G.T)} templates")
