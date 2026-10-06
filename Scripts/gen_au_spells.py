"""Arcana Unleashed level 7-9 spells (2026-10-05). 14 of its 15 are new to BG3, dnd55e and this mod; Hindsight (watch 10 years
of the past) has nothing in BG3 to act on and isn't made.

Each spell builds on a base-game spell with the same shape (`using`), so animations, sounds and targeting come with it; the
mechanics follow the rules text (library: excerpts/subclasses/ArcanaUnleashed.txt). Class lists: Scripts/data/
rules_spell_classes.json via gen_rules_spell_lists.py (rerun Scripts/extract_rules_spells.py after changing names here).

Not modelled (no BG3 equivalent): Deafened (Lightning Ring, Wail of the Banshee); Power Word Pain's Constitution save to cast
a spell; Reweave Fate's 6d10 Temporary Hit Points when the reroll succeeds (the interrupt can't see the new result);
Detonate's Disadvantage when the target dropped to 0 (damage IF() conditions are read at cast start); Illusory Dragon is
the frightening appearance plus a Bonus Action breath from you (no tangible dragon to move; a creature can't study it).
Exhaustion (Vision of Elapsing Eons) is the 2024 rule as statuses APO_EXHAUSTION_1-5, level 6 kills; a Long Rest clears
it all (2024: one level).
Run: python3 Scripts/gen_au_spells.py
"""
from gen_common import Gen

G = Gen("auspells", "ARCANA UNLEASHED SPELLS")
DAMAGE = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic", "Radiant",
          "Slashing", "Thunder"]


def slot(level, action="ActionPoint"):
    return f"{action}:1;SpellSlotsGroup:1:1:{level}"


def spell(name, title, text, using, level, school, fields, icon=None):
    G.spell(name, title, text, {"Level": str(level), "SpellSchool": school, "UseCosts": slot(level), **fields}, using=using, icon=icon)


def repeat_save(ability):
    """The 2024 'repeats the save at the end of each of its turns, ending the spell on a success' (HOLD_PERSON's form)."""
    return {"TickType": "EndTurn", "RemoveConditions": f"SavingThrow(Ability.{ability}, SourceSpellDC())", "RemoveEvents": "OnTurn",
            "StatusPropertyFlags": "OverheadOnTurn"}


# ---------------------------------------------------------------- 7th level
spell("Shout_Apo_AuraOfEvasion", "Aura of Evasion",
      "For 1 minute, you and your allies within 9m have Advantage on Dexterity saving throws and take no damage on a successful "
      "save against an effect that deals half damage on a success (half on a failure). Incapacitated creatures don't benefit.",
      "Shout_SpiritGuardians_Radiant", 7, "Abjuration",
      {"SpellContainerID": "", "AreaRadius": "9", "DamageType": "", "VerbalIntent": "Buff",
       "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsConcentration;IsSpell",
       "SpellProperties": "ApplyStatus(APO_AURA_OF_EVASION_AURA,100,10)"}, icon="Action_Paladin_AuraOfProtection")
G.status("APO_AURA_OF_EVASION_AURA", "Aura of Evasion", "You and allies within 9m have Advantage on Dexterity saves and Evasion.",
         {"StackId": "APO_AURA_OF_EVASION_AURA", "AuraRadius": "9",
          "AuraStatuses": "IF(Ally() and not Dead() and not Tagged('INANIMATE') and not HasStatus('SG_Incapacitated')):ApplyStatus(APO_AURA_OF_EVASION)",
          "StatusGroups": "SG_RemoveOnRespec"}, icon="Action_Paladin_AuraOfProtection")
G.status("APO_AURA_OF_EVASION", "Aura of Evasion", "Advantage on Dexterity saving throws; no damage on a successful save against "
         "an area effect, half on a failure.",
         {"StackId": "APO_AURA_OF_EVASION", "Boosts": "Advantage(SavingThrow,Dexterity);AreaDamageEvade()",
          "RemoveConditions": "HasStatus('SG_Incapacitated')", "RemoveEvents": "OnStatusApplied"}, icon="Action_Paladin_AuraOfProtection")

spell("Target_Apo_FracturedAwareness", "Fractured Awareness",
      "Conflicting visions of possible futures assail a creature (Intelligence save). On a failure it takes 12d10 Psychic damage "
      "and has Disadvantage on D20 Tests, repeating the save at the end of each of its turns. On a success, half damage only.",
      "Target_PhantasmalKiller", 7, "Divination",
      {"TargetRadius": "36", "TargetConditions": "Character() and not Self() and not Dead()", "VerbalIntent": "Damage",
       "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
       "SpellSuccess": "DealDamage(12d10,Psychic,Magical);ApplyStatus(APO_FRACTURED_AWARENESS,100,10)",
       "SpellFail": "DealDamage((12d10)/2,Psychic,Magical);ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)",
       "TooltipDamageList": "DealDamage(12d10,Psychic)"})
G.status("APO_FRACTURED_AWARENESS", "Fractured Awareness", "Disadvantage on D20 Tests. Repeats the Intelligence save at the end of "
         "each of its turns.",
         {"StackId": "APO_FRACTURED_AWARENESS", "Boosts": "Disadvantage(AttackRoll);Disadvantage(AllSavingThrows);Disadvantage(AllAbilities)",
          **repeat_save("Intelligence"), "StatusGroups": "SG_RemoveOnRespec"}, icon="Spell_Illusion_PhantasmalKiller")

spell("Target_Apo_PowerWordPain", "Power Word Pain",
      "A word of power deals 6d8 Force damage. If the creature had 100 Hit Points or fewer, it is also Charmed for 1 minute: "
      "Speed at most 3m and Disadvantage on D20 Tests except Constitution saves. It repeats a Constitution save at the end of "
      "each of its turns.",
      "Target_PowerWordKill", 7, "Enchantment",
      {"TargetRadius": "18", "SpellProperties": "DealDamage(6d8,Force,Magical);IF(HasHPLessThan(101)):ApplyStatus(APO_POWER_WORD_PAIN,100,10)",
       "TooltipDamageList": "DealDamage(6d8,Force)"})
G.status("APO_POWER_WORD_PAIN", "Power Word Pain", "Charmed: Speed at most 3m, Disadvantage on D20 Tests except Constitution saves. "
         "Repeats the Constitution save at the end of each of its turns.",
         {"StackId": "APO_POWER_WORD_PAIN",
          "Boosts": "CannotHarmCauseEntity(CannotHarmCharmer);ActionResourceOverride(Movement,3,0);Disadvantage(AttackRoll);Disadvantage(AllAbilities);"
                    + ";".join(f"Disadvantage(SavingThrow,{a})" for a in ("Strength", "Dexterity", "Intelligence", "Wisdom", "Charisma")),
          **repeat_save("Constitution"), "StatusGroups": "SG_Charmed;SG_Condition"}, icon="Status_Charmed")

G.spell("Shout_Apo_ReweaveFate", "Reweave Fate",
        "Reaction, when an ally within 18m fails an attack roll or saving throw: it rerolls with Advantage and must use the new roll.",
        {"Level": "7", "SpellSchool": "Divination", "UseCosts": slot(7, "ReactionActionPoint"),
         "InterruptPrototype": "Interrupt_Apo_ReweaveFate", "SpellFlags": "HasSomaticComponent;IsSpell;IsLinkedSpellContainer"},
        using="Shout_Shield_Wizard", icon="PassiveFeature_Lucky_RollAdditionalDie")
G.interrupt("Interrupt_Apo_ReweaveFate", "Reweave Fate", "An ally failed a roll: reroll it with Advantage.",
            {"InterruptContext": "OnPostRoll", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
             "Conditions": "IsAbleToReact(context.Observer) and not AnyEntityIsItem() and not HasVerbalComponentBlocked(context.Observer) and "
                           "((HasInterruptedAttack() and Ally(context.Source,context.Observer) and IsRerollInterruptInteresting(context.Source)) or "
                           "(HasInterruptedSavingThrow() and Ally(context.Target,context.Observer) and IsRerollInterruptInteresting()))",
             "Properties": "SetAdvantage()", "Cost": slot(7, "ReactionActionPoint"), "InterruptDefaultValue": "Ask;Enabled"},
            icon="PassiveFeature_Lucky_RollAdditionalDie",
            comment="SetAdvantage() rerolls with Advantage, as Interrupt_ApoMasterDuelist / dnd55e Seeking Spell")

TRANSFIX = "An alluring otherworldly aura: a creature within 18m makes a Charisma save or is Charmed and Incapacitated, moving toward you, and takes {d} Psychic damage whenever it ends its turn within 1.5m of you. While you concentrate you can use an action to target another creature (not one that saved)."
for lv, d in ((7, "4d8"), (8, "5d8"), (9, "6d8")):
    sfx = "" if lv == 7 else f"_{lv}"
    up = {} if lv == 7 else {"RootSpellID": "Target_Apo_Transfix", "PowerLevel": str(lv)}
    common = {"TargetRadius": "18", "VerbalIntent": "Control",
              "TargetConditions": "Character() and not Self() and not Dead() and not HasStatus('APO_TRANSFIX_RESISTED')",
              "SpellRoll": "not SavingThrow(Ability.Charisma, SourceSpellDC())",
              "SpellSuccess": f"ApplyStatus(APO_TRANSFIXED{sfx},100,10)",
              "SpellFail": "ApplyStatus(APO_TRANSFIX_RESISTED,100,10);ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)"}
    if lv == 7:
        spell("Target_Apo_Transfix", "Transfix", TRANSFIX.format(d=d), "Target_HoldMonster", 7, "Enchantment",
              {**common, "SpellProperties": "ApplyStatus(SELF,APO_TRANSFIX_CASTER,100,10)"})
    else:
        G.spell(f"Target_Apo_Transfix{sfx}", "Transfix", TRANSFIX.format(d=d),
                {**common, "SpellProperties": f"ApplyStatus(SELF,APO_TRANSFIX_CASTER{sfx},100,10)", "UseCosts": slot(lv), **up},
                using="Target_Apo_Transfix")
    G.spell(f"Target_Apo_Transfix_Retarget{sfx}", "Transfix: New Target", "Transfix another creature (not one that saved).",
            {**common, "SpellProperties": "", "UseCosts": "ActionPoint:1", "Level": "0",
             "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;IsHarmful;Temporary"}, using="Target_Apo_Transfix")
    G.status(f"APO_TRANSFIX_CASTER{sfx}", "Transfix", "You can Transfix another creature with an action.",
             {"StackId": "APO_TRANSFIX_CASTER", "Boosts": f"UnlockSpell(Target_Apo_Transfix_Retarget{sfx})",
              "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"}, icon="Spell_Enchantment_CommandApproach")
    G.status(f"APO_TRANSFIXED{sfx}", "Transfixed", f"Charmed and Incapacitated; moves toward the caster and takes {d} Psychic "
             "damage when it ends its turn within 1.5m of them.",
             {"StackId": "APO_TRANSFIXED", "TickType": "EndTurn",
              "TickFunctors": f"IF(DistanceToTargetLessThan(1.6)):DealDamage({d},Psychic,Magical)",
              "RemoveConditions": "not HasStatus('APO_TRANSFIX_CASTER',context.Source)", "RemoveEvents": "OnTurn",
              "StatusGroups": "SG_Approaching;SG_Charmed;SG_Incapacitated;SG_Condition"},
             using="COMMAND_APPROACH", icon="Spell_Enchantment_CommandApproach")
G.status("APO_TRANSFIX_RESISTED", "Resisted Transfix", "Can't be targeted by this Transfix again.",
         {"StackId": "APO_TRANSFIX_RESISTED", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})

# ---------------------------------------------------------------- 8th level
spell("Target_Apo_EntrancingMirrors", "Entrancing Mirrors",
      "Illusory mirrors confound up to three creatures within 27m (Intelligence save). On a failure, 7d6 Psychic damage and "
      "Stunned with halved Speed, repeating the save at the end of each of its turns. On a success, half damage only.",
      "Target_PhantasmalKiller", 8, "Illusion",
      {"TargetRadius": "27", "AmountOfTargets": "3", "TargetConditions": "Character() and not Self() and not Dead()",
       "VerbalIntent": "Damage", "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
       "SpellSuccess": "DealDamage(7d6,Psychic,Magical);ApplyStatus(APO_ENTRANCED,100,10)",
       "SpellFail": "DealDamage((7d6)/2,Psychic,Magical);ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)",
       "TooltipDamageList": "DealDamage(7d6,Psychic)",
       "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsConcentration;IsSpell;IsHarmful;IgnorePreviouslyPickedEntities"})
G.status("APO_ENTRANCED", "Entranced", "Stunned, Speed halved. Repeats the Intelligence save at the end of each of its turns.",
         {"StackId": "APO_ENTRANCED", "Boosts": "AbilityFailedSavingThrow(Strength);AbilityFailedSavingThrow(Dexterity);Advantage(AttackTarget);"
                                                 "DetectDisturbancesBlock(true);ActionResourceMultiplier(Movement,50,0)",
          **repeat_save("Intelligence")}, using="STUNNED", icon="Status_Stunned")

BREATH = {"Acid": "Zone_DragonsBreath_Acid", "Cold": "Zone_DragonsBreath_Cold", "Fire": "Zone_DragonsBreath_Fire",
          "Lightning": "Zone_DragonsBreath_Lightning", "Necrotic": "Zone_DragonsBreath_Fire", "Poison": "Zone_DragonsBreath_Poison"}
DRAGON = ("A Huge shadowy dragon appears. Enemies within 18m make a Wisdom save or drop their weapon and are Frightened. "
          "While you concentrate (1 minute), as a Bonus Action the dragon exhales an 18m cone: Intelligence save, 6d6 {t} damage, "
          "half on a success.")
G.spell("Shout_Apo_IllusoryDragon", "Illusory Dragon", DRAGON.format(t="Acid, Cold, Fire, Lightning, Necrotic or Poison (your choice)"),
        {"SpellType": "Shout", "Level": "8", "SpellSchool": "Illusion", "UseCosts": slot(8),
         "ContainerSpells": ";".join(f"Shout_Apo_IllusoryDragon_{t}" for t in BREATH), "TargetConditions": "Self()",
         "SpellFlags": "HasSomaticComponent;IsConcentration;IsSpell;IsHarmful;IsLinkedSpellContainer", "VerbalIntent": "Control"},
        icon="Spell_Illusion_Fear")
for t, parent in BREATH.items():
    G.spell(f"Shout_Apo_IllusoryDragon_{t}", f"Illusory Dragon ({t})", DRAGON.format(t=t),
            {"SpellContainerID": "Shout_Apo_IllusoryDragon", "Level": "8", "SpellSchool": "Illusion", "UseCosts": slot(8),
             "AreaRadius": "18", "DamageType": t, "VerbalIntent": "Control", "SpellProperties": "",
             "TargetConditions": "Self() or (Enemy() and not Dead())",
             "SpellRoll": "Self() or not SavingThrow(Ability.Wisdom, SourceSpellDC(), AdvantageOnFrightened(), DisadvantageOnFrightened())",
             "SpellSuccess": f"IF(Self()):ApplyStatus(APO_ILLUSORY_DRAGON_{t.upper()},100,10);IF(not Self()):ApplyStatus(APO_ILLUSORY_DRAGON_FEAR,100,10);"
                             "IF(not Self() and HasWeaponInMainHand()):ApplyStatus(DISARM,100,1)",
             "SpellFail": "ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)",
             "SpellFlags": "HasSomaticComponent;IsConcentration;IsSpell;IsHarmful"}, using="Shout_SpiritGuardians_Radiant", icon="Spell_Illusion_Fear")
    G.status(f"APO_ILLUSORY_DRAGON_{t.upper()}", "Illusory Dragon", f"Your shadowy dragon can exhale {t} as a Bonus Action.",
             {"StackId": "APO_ILLUSORY_DRAGON", "Boosts": f"UnlockSpell(Zone_Apo_IllusoryDragonBreath_{t})", "StatusGroups": "SG_RemoveOnRespec"},
             icon="Spell_Illusion_Fear")
    G.spell(f"Zone_Apo_IllusoryDragonBreath_{t}", f"Illusory Dragon: Exhale ({t})",
            f"The shadowy dragon exhales an 18m cone: Intelligence save, 6d6 {t} damage, half on a success.",
            {"Level": "8", "SpellSchool": "Illusion", "Range": "18", "Angle": "60", "UseCosts": "BonusActionPoint:1",
             "SpellProperties": "", "DamageType": t, "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
             "SpellSuccess": f"DealDamage(6d6,{t},Magical)", "SpellFail": f"DealDamage((6d6)/2,{t},Magical)",
             "TooltipDamageList": f"DealDamage(6d6,{t})", "TargetConditions": "not Dead() and not Self()",
             "SpellFlags": "IsSpell;IsHarmful;Temporary"}, using=parent)
G.status("APO_ILLUSORY_DRAGON_FEAR", "Frightened by the Illusory Dragon", "Frightened of a shadowy dragon.",
         {"StackId": "APO_ILLUSORY_DRAGON_FEAR"}, using="FRIGHTENED", icon="Status_Frightened",
         comment="FRIGHTENED's own per-turn save stands in for 'out of sight of the dragon' (there is no dragon to lose sight of)")

spell("Target_Apo_IronBody", "Iron Body",
      "A willing creature you touch becomes living metal: Resistance to Bludgeoning, Fire, Piercing and Slashing damage, Immunity "
      "to Poison damage and the Paralyzed, Petrified and Poisoned conditions (ending them), and its Exhaustion can't increase.",
      "Target_Stoneskin", 8, "Transmutation",
      {"SpellProperties": "RemoveStatus(SG_Paralyzed);RemoveStatus(SG_Petrified);RemoveStatus(SG_Poisoned);ApplyStatus(APO_IRON_BODY,100,-1)"})
G.status("APO_IRON_BODY", "Iron Body", "Resistance to Bludgeoning, Fire, Piercing and Slashing; Immunity to Poison damage, "
         "Paralyzed, Petrified and Poisoned; Exhaustion can't increase.",
         {"StackId": "APO_IRON_BODY",
          "Boosts": "".join(f"Resistance({t},Resistant);" for t in ("Bludgeoning", "Fire", "Piercing", "Slashing"))
                    + "Resistance(Poison,Immune);StatusImmunity(SG_Paralyzed);StatusImmunity(SG_Petrified);StatusImmunity(SG_Poisoned);StatusImmunity(SG_Exhausted)",
          "StatusGroups": "SG_RemoveOnRespec"}, icon="Spell_Abjuration_Stoneskin")

spell("Shout_Apo_LightningRing", "Lightning Ring",
      "Bonus Action. For 10 minutes a 3m ring of electricity surrounds you: an enemy it reaches, or that ends its turn in it, makes "
      "a Constitution save, taking 3d6 Lightning and 3d6 Thunder damage (half on a success). As an action you can loose an 18m "
      "line: Dexterity save, 6d6 Lightning damage, half on a success.",
      "Shout_SpiritGuardians_Radiant", 8, "Evocation",
      {"SpellContainerID": "", "AreaRadius": "3", "DamageType": "Lightning", "UseCosts": slot(8, "BonusActionPoint"),
       "SpellProperties": "ApplyStatus(APO_LIGHTNING_RING_AURA,100,100)"}, icon="Spell_Evocation_LightningBolt")
G.status("APO_LIGHTNING_RING_AURA", "Lightning Ring", "A 3m ring of electricity surrounds you.",
         {"StackId": "APO_LIGHTNING_RING_AURA", "AuraRadius": "3",
          "AuraStatuses": "TARGET:IF(Enemy() and not Dead()):ApplyStatus(APO_LIGHTNING_RING,100,-1)", "AuraFlags": "ShouldCheckLOS",
          "Boosts": "UnlockSpell(Zone_Apo_LightningRing_Line)", "StatusPropertyFlags": "InitiateCombat;BringIntoCombat",
          "StatusGroups": "SG_RemoveOnRespec"}, icon="Spell_Evocation_LightningBolt")
RING_HIT = ("IF(not HasStatus('APO_LIGHTNING_RING_HIT') or StatusDurationLessThan(context.Source, 'APO_LIGHTNING_RING_HIT', 0.1)):DealDamage({l},Lightning,Magical);"
            "IF(not HasStatus('APO_LIGHTNING_RING_HIT') or StatusDurationLessThan(context.Source, 'APO_LIGHTNING_RING_HIT', 0.1)):DealDamage({l},Thunder,Magical);"
            "ApplyStatus(APO_LIGHTNING_RING_HIT,100,1)")
G.status("APO_LIGHTNING_RING", "Lightning Ring", "In the ring: a Constitution save when it reaches you and when you end your turn here.",
         {"TickType": "EndTurn", "OnApplyRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
          "OnApplySuccess": RING_HIT.format(l="3d6"), "OnApplyFail": RING_HIT.format(l="(3d6)/2"),
          "OnTickRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
          "OnTickSuccess": RING_HIT.format(l="3d6"), "OnTickFail": RING_HIT.format(l="(3d6)/2"),
          "StatusGroups": "SG_RemoveOnRespec"}, icon="Spell_Evocation_LightningBolt",
         comment="SPIRIT_GUARDIANS_RADIANT's form, ticking on the creature's own turn end; the _HIT guard is once per turn")
G.status("APO_LIGHTNING_RING_HIT", "Lightning Ring", None, {"StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.spell("Zone_Apo_LightningRing_Line", "Lightning Ring: Line", "An 18m line of lightning: Dexterity save, 6d6 Lightning damage, half on a success.",
        {"Level": "8", "SpellSchool": "Evocation", "UseCosts": "ActionPoint:1", "Range": "18", "Base": "1.5",
         "SpellSuccess": "DealDamage(6d6,Lightning,Magical)", "SpellFail": "DealDamage((6d6)/2,Lightning,Magical)",
         "TooltipDamageList": "DealDamage(6d6,Lightning)",
         "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;IsHarmful;CanAreaDamageEvade;Temporary"}, using="Zone_LightningBolt")

G.spell("Shout_Apo_MomentOfPrescience", "Moment of Prescience",
        "Reaction, when you fail an attack roll or saving throw: the roll becomes a 20. Or when a creature hits you with an attack "
        "roll: its roll becomes a 1.",
        {"Level": "8", "SpellSchool": "Divination", "UseCosts": slot(8, "ReactionActionPoint"),
         "InterruptPrototype": "Interrupt_Apo_MomentOfPrescience"}, using="Shout_Shield_Wizard", icon="PassiveFeature_Portent_20")
SELF_ROLL = ("((HasInterruptedAttack() and Self(context.Observer,context.Source) and IsSetInterruptInteresting(20, context.Source)) or "
             "(HasInterruptedSavingThrow() and Self(context.Observer,context.Target) and IsSetInterruptInteresting(20)))")
HIT_ME = "(HasInterruptedAttack() and Self(context.Target,context.Observer) and IsSetInterruptInteresting(1, context.Source))"
G.interrupt("Interrupt_Apo_MomentOfPrescience", "Moment of Prescience", "Turn your failed roll into a 20, or an attack that hits you into a 1.",
            {"InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
             "Conditions": f"IsAbleToReact(context.Observer) and not AnyEntityIsItem() and not HasSpellCastBlocked(context.Observer) and ({SELF_ROLL} or {HIT_ME})",
             "Properties": f"IF({HIT_ME}):SetRoll(1);IF(not {HIT_ME}):SetRoll(20)",
             "Cost": slot(8, "ReactionActionPoint"), "InterruptDefaultValue": "Ask;Enabled"},
            icon="PassiveFeature_Portent_20", comment="SetRoll as Portent (20) and Illusory Self (an attack that hits you, 1)")

# ---------------------------------------------------------------- 9th level
spell("Projectile_Apo_Detonate", "Detonate",
      "An explosive seed inside a creature within 150m: Constitution save, 10d10 Fire damage, half on a success. Then each other "
      "creature within 18m of it makes a Dexterity save, taking 10d10 Fire damage, half on a success.",
      "Projectile_Fireball", 9, "Evocation",
      {"TargetRadius": "150", "ExplodeRadius": "0", "TargetConditions": "Character() and not Self() and not Dead()",
       "SpellRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
       "SpellSuccess": "DealDamage(10d10,Fire,Magical)", "SpellFail": "DealDamage((10d10)/2,Fire,Magical)",
       "SpellProperties": "TARGET:ApplyStatus(APO_DETONATE_SEED,100,1);CreateExplosion(Projectile_Apo_Detonate_Explosion)",
       "TooltipDamageList": "DealDamage(10d10,Fire);DealDamage(10d10,Fire)",
       "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold;IsHarmful"})
G.spell("Projectile_Apo_Detonate_Explosion", "Detonate (Explosion)", "Dexterity save, 10d10 Fire damage, half on a success.",
        {"UseCosts": "", "ExplodeRadius": "18", "TargetConditions": "not HasStatus('APO_DETONATE_SEED') and not Dead()",
         "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())",
         "SpellSuccess": "DealDamage(10d10,Fire,Magical)", "SpellFail": "DealDamage((10d10)/2,Fire,Magical)",
         "SpellProperties": "GROUND:SurfaceChange(Ignite);GROUND:SurfaceChange(Melt)",
         "SpellFlags": "IsHarmful;CanAreaDamageEvade"}, using="Projectile_Fireball")
G.status("APO_DETONATE_SEED", "Detonated", None, {"StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
         comment="marks Detonate's target so its own explosion leaves it out")

spell("Shout_Apo_Invulnerability", "Invulnerability", "For up to 10 minutes (Concentration) you have Immunity to all damage.",
      "Shout_SpiritGuardians_Radiant", 9, "Abjuration",
      {"SpellContainerID": "", "AreaRadius": "", "DamageType": "", "VerbalIntent": "Buff", "TargetConditions": "Self()",
       "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsConcentration;IsSpell",
       "SpellProperties": "ApplyStatus(APO_INVULNERABILITY,100,100)"}, icon="Spell_Abjuration_GlobeOfInvulnerability")
G.status("APO_INVULNERABILITY", "Invulnerability", "Immunity to all damage.",
         {"StackId": "APO_INVULNERABILITY", "Boosts": ";".join(f"Resistance({t},Immune)" for t in DAMAGE),
          "StatusGroups": "SG_RemoveOnRespec"}, icon="Spell_Abjuration_GlobeOfInvulnerability")

spell("Target_Apo_VisionOfElapsingEons", "Vision of Elapsing Eons",
      "A creature within 36m sees eons pass in moments (Intelligence save): on a failure, 10d12 Psychic damage and Paralyzed for "
      "1 minute. At the end of each of its turns it repeats the save, gaining a level of Exhaustion on a failure and ending the "
      "spell on a success. An ally can shake it free with the Help action.",
      "Target_HoldMonster", 9, "Illusion",
      {"TargetRadius": "36", "TargetConditions": "Character() and not Self() and not Dead()", "VerbalIntent": "Damage",
       "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
       "SpellSuccess": "DealDamage(10d12,Psychic,Magical);ApplyStatus(APO_ELAPSING_EONS,100,10)",
       "SpellFail": "ApplyStatus(SAVED_AGAINST_HOSTILE_SPELL,100,0)", "TooltipDamageList": "DealDamage(10d12,Psychic)",
       "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful"})
EXHAUST_UP = ";".join([f"IF(HasStatus('APO_EXHAUSTION_5')):Kill()"]
                      + [f"IF(HasStatus('APO_EXHAUSTION_{n}')):ApplyStatus(APO_EXHAUSTION_{n + 1},100,-1)" for n in range(4, 0, -1)]
                      + ["IF(not HasStatus('SG_Exhausted')):ApplyStatus(APO_EXHAUSTION_1,100,-1)"])
G.status("APO_ELAPSING_EONS", "Vision of Elapsing Eons", "Paralyzed. At the end of each of its turns: Intelligence save; a failure "
         "adds a level of Exhaustion, a success ends this. The Help action ends it.",
         {"StackId": "APO_ELAPSING_EONS", "TickType": "EndTurn", "OnTickRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
          "OnTickSuccess": EXHAUST_UP, "OnTickFail": "RemoveStatus(APO_ELAPSING_EONS)",
          "StatusGroups": "SG_Incapacitated;SG_Condition;SG_Paralyzed;SG_Helpable_Condition"}, using="PARALYZED", icon="Status_Paralyzed",
         comment="highest level first, so one failure raises Exhaustion by exactly one")
for n in range(1, 6):
    G.status(f"APO_EXHAUSTION_{n}", f"Exhaustion {n}", f"D20 Tests -{2 * n}, Speed -{1.5 * n:g}m. A sixth level is death. A Long Rest ends it.",
             {"StackId": "APO_EXHAUSTION",
              "Boosts": f"RollBonus(Attack,-{2 * n});RollBonus(SavingThrow,-{2 * n});RollBonus(SkillCheck,-{2 * n});RollBonus(RawAbility,-{2 * n});"
                        f"ActionResource(Movement,-{1.5 * n:g},0)",
              "StatusGroups": "SG_Exhausted;SG_Condition"}, icon="Status_Exhaustion",
             comment="2024 Exhaustion (no BG3 or dnd55e equivalent)" if n == 1 else None)

spell("Target_Apo_WailOfTheBanshee", "Wail of the Banshee",
      "A terrible scream reaches up to ten creatures within 18m. Each with 50 Hit Points or fewer dies. The others make a "
      "Constitution save: 12d10 Psychic damage on a failure, half on a success. A creature that can't hear you is unaffected.",
      "Target_PowerWordKill", 9, "Necromancy",
      {"TargetRadius": "18", "AmountOfTargets": "10", "VerbalIntent": "Damage",
       "TargetConditions": "Character() and not Self() and not Dead() and not HasStatus('SILENCED')",
       "SpellProperties": "IF(HasHPLessThan(51)):Kill()",
       "SpellRoll": "not HasHPLessThan(51) and not SavingThrow(Ability.Constitution, SourceSpellDC())",
       "SpellSuccess": "DealDamage(12d10,Psychic,Magical)",
       "SpellFail": "IF(not HasHPLessThan(51)):DealDamage((12d10)/2,Psychic,Magical)",
       "TooltipDamageList": "DealDamage(12d10,Psychic)",
       "SpellFlags": "HasVerbalComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful;IgnorePreviouslyPickedEntities"})


if __name__ == "__main__":
    G.write_stats("AUSpells", "gen_au_spells.py", "Arcana Unleashed level 7-9 spells, 2026-10-05")
    G.patch_loca()
    print(f"{len(G.SP)} spells, {len(G.S)} statuses, {len(G.I)} interrupts")
