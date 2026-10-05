"""Generate single PHB 2024 class features that dnd55e and Apotheosis lacked (one issue each):
- #11 Ranger 14 Nature's Veil, Ranger 17 Precise Hunter
- #12 College of Glamour 14 Unbreakable Majesty
- #13 Battle Master 15 Relentless (the +1 Superiority Die moves to the level-15 node)
- #16 Warrior of the Open Hand 17 Quivering Palm (the 2024 two-step feature)

Owns Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_ClassFeatures.txt; patches Progressions (by UUID),
ActionResourceDefinitions and loca. Script Extender half: ScriptExtender/Lua/ClassFeatures.lua (Relentless).

Run: python3 Scripts/gen_class_features.py && python3 Scripts/build_all_class_expectations.py
"""
from gen_common import Gen, drop_entries, patch_progressions, icon_of

G = Gen("classfeatures", "CLASS FEATURES 2024")

# ---------------------------------------------------------------- #11 Ranger
G.resource("NaturesVeil", 7, "Rest", "Nature's Veil", "Become Invisible until the end of your next turn. Uses equal to your Wisdom modifier; returns on a Long Rest.")
WIS_LADDER = ";".join(f"IF(AbilityGreaterThan('Wisdom',{n},context.Source)):ActionResource(NaturesVeil,1,0)" for n in (13, 15, 17, 19, 21, 23))
G.passive("Ranger_14_NaturesVeil", "Nature's Veil",
          "As a Bonus Action, you become Invisible until the end of your next turn. You can do this a number of times equal to your Wisdom modifier (minimum once), regaining all uses on a Long Rest.",
          {"Boosts": "UnlockSpell(Shout_Ranger_NaturesVeil);ActionResource(NaturesVeil,1,0);" + WIS_LADDER},
          icon="Spell_Illusion_GreaterInvisibility", comment="Uses = Wisdom modifier, as dnd55e's WardingFlare ladder.")
G.spell("Shout_Ranger_NaturesVeil", "Nature's Veil", "Become Invisible until the end of your next turn.", {
    "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": "BonusActionPoint:1;NaturesVeil:1",
    "SpellProperties": "ApplyStatus(SELF,RANGER_NATURES_VEIL,100,2)", "SpellFlags": "IgnoreSilence;Invisible"}, icon="Spell_Illusion_GreaterInvisibility")
G.status("RANGER_NATURES_VEIL", "Nature's Veil", "Invisible until the end of your next turn.", {"StackId": "RANGER_NATURES_VEIL"},
         using="GREATER_INVISIBILITY", comment="The 2024 Invisible condition doesn't end when you attack, like Greater Invisibility.")
G.passive("Ranger_17_PreciseHunter", "Precise Hunter",
          "You have Advantage on attack rolls against the creature currently marked by your Hunter's Mark.",
          {"Boosts": "IF(HasStatus('HUNTERS_MARK', context.Target, context.Source)):Advantage(AttackRoll)"}, icon="Spell_Divination_HuntersMark")

# ---------------------------------------------------------------- #12 College of Glamour
G.resource("UnbreakableMajesty", 1, "ShortRest", "Unbreakable Majesty", "Assume a majestic presence. Returns on a Short or Long Rest.")
G.resource("UnbreakableMajestyHit", 1, "Turn", "Unbreakable Majesty (this turn)", "Once per turn, an attacker must save or miss.")
G.passive("Glamour_14_UnbreakableMajesty", "Unbreakable Majesty",
          "As a Bonus Action, assume a majestic presence for 1 minute or until you're Incapacitated. During it, the first time a creature hits you on a turn, it must succeed on a Charisma saving throw against your spell save DC or the attack misses. Once per Short or Long Rest, or by expending a level 5+ spell slot.",
          {"Boosts": "UnlockSpell(Shout_Glamour_UnbreakableMajesty);UnlockSpell(Shout_Glamour_UnbreakableMajesty_Slot);"
                     "UnlockInterrupt(Interrupt_Glamour_UnbreakableMajesty);ActionResource(UnbreakableMajesty,1,0);ActionResource(UnbreakableMajestyHit,1,0)"},
          icon="Spell_Enchantment_CrownOfMadness")
for name, title, cost in (("Shout_Glamour_UnbreakableMajesty", "Unbreakable Majesty", "BonusActionPoint:1;UnbreakableMajesty:1"),
                          ("Shout_Glamour_UnbreakableMajesty_Slot", "Unbreakable Majesty (spell slot)", "BonusActionPoint:1;SpellSlotsGroup:1:1:5")):
    G.spell(name, title, "Assume a majestic presence for 1 minute: the first creature to hit you each turn must save or miss.", {
        "SpellType": "Shout", "Level": "0", "TargetConditions": "Self()", "UseCosts": cost,
        "RequirementConditions": "not HasStatus('GLAMOUR_UNBREAKABLE_MAJESTY')",
        "SpellProperties": "ApplyStatus(SELF,GLAMOUR_UNBREAKABLE_MAJESTY,100,10)", "SpellFlags": "IgnoreSilence"}, icon="Spell_Enchantment_CrownOfMadness")
G.status("GLAMOUR_UNBREAKABLE_MAJESTY", "Unbreakable Majesty", "The first creature to hit you each turn must succeed on a Charisma saving throw or miss.", {
    "RemoveConditions": "HasStatus('SG_Incapacitated')", "RemoveEvents": "OnStatusApplied", "StackId": "GLAMOUR_UNBREAKABLE_MAJESTY"},
    icon="Spell_Enchantment_CrownOfMadness")
G.interrupt("Interrupt_Glamour_UnbreakableMajesty", "Unbreakable Majesty", "The attacker must succeed on a Charisma saving throw or miss.", {
    "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "HasStatus('GLAMOUR_UNBREAKABLE_MAJESTY', context.Observer) and Self(context.Target,context.Observer) and HasInterruptedAttack() and Enemy(context.Source,context.Observer) and not AnyEntityIsItem() and IsFlatValueInterruptInteresting(99, context.Source)",
    "Roll": "not SavingThrow(Ability.Charisma, SourceSpellDC(10, context.Observer, Ability.Charisma), false, false, context.Source)",
    "Success": "AdjustRoll(OBSERVER_OBSERVER,-99)", "Cost": "UnbreakableMajestyHit:1", "InterruptDefaultValue": "Enabled"}, icon="Spell_Enchantment_CrownOfMadness",
    comment="Hits only: IsFlatValueInterruptInteresting(99, source) = a penalty could still turn it into a miss (as base Shield's 5). Once per round: its charge returns on your turn.")

# ---------------------------------------------------------------- #13 Battle Master
G.resource("BattleMasterRelentless", 1, "Turn", "Relentless", "Once per turn, a maneuver costs no Superiority Die.")
G.passive("BattleMaster_Relentless", "Relentless",
          "Once per turn, when you use a maneuver, you can roll a d8 and use it instead of expending a Superiority Die.",
          {"Boosts": "ActionResource(BattleMasterRelentless,1,0)"}, icon="Action_ForcedManeuver",
          comment="ClassFeatures.lua returns the first Superiority Die a maneuver spends each turn.")

# ---------------------------------------------------------------- #16 Warrior of the Open Hand 17: Quivering Palm
MONK_DC = "SourceSpellDC(10, context.Source, Ability.Wisdom)"  # the 2024 Focus save DC: 8 + Wisdom + PB
G.passive("OpenHand_17_QuiveringPalm", "Quivering Palm",
          "When you hit a creature with an Unarmed Strike, you can expend 4 Focus Points to start lethal vibrations in its body. Later, as an action, you end them: it makes a Constitution saving throw, taking 10d12 Force damage on a failure or half on a success. Only one creature at a time; you can also end them harmlessly.",
          {"Boosts": "UnlockInterrupt(Interrupt_QuiveringPalm);UnlockSpell(Target_QuiveringPalm_Trigger);UnlockSpell(Target_QuiveringPalm_Release)"},
          icon="Action_Monk_OpenHandTechnique_Push")
G.interrupt("Interrupt_QuiveringPalm", "Quivering Palm", "Expend 4 Focus Points to start lethal vibrations in the creature you hit.", {
    "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "Self(context.Source,context.Observer) and not Self() and IsUnarmedAttack() and not IsMiss() and Character(context.Target) and not AnyEntityIsItem() and not HasStatus('QUIVERING_PALM',context.Target,context.Source)",
    "Properties": "ApplyStatus(QUIVERING_PALM,100,-1)", "Cost": "KiPoint:4", "InterruptDefaultValue": "Ask;Enabled"},
    icon="Action_Monk_OpenHandTechnique_Push")
G.status("QUIVERING_PALM", "Quivering Palm", "Lethal vibrations: the Monk can end them for 10d12 Force damage (Constitution save for half).", {
    "StackId": "QUIVERING_PALM", "StatusPropertyFlags": "IgnoreResting;DisableOverhead", "StatusGroups": "SG_RemoveOnRespec"},
    icon="Action_Monk_OpenHandTechnique_Push", comment="Lasts until ended (the source: days equal to your Monk level). ClassFeatures.lua keeps it on one creature.")
G.spell("Target_QuiveringPalm_Trigger", "Quivering Palm: End the Vibrations", "The creature makes a Constitution saving throw: 10d12 Force damage, or half on a success.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "60", "UseCosts": "ActionPoint:1",
    "TargetConditions": "HasStatus('QUIVERING_PALM',context.Target,context.Source)",
    "SpellRoll": f"not SavingThrow(Ability.Constitution, {MONK_DC})", "SpellSuccess": "DealDamage(10d12,Force,Magical)",
    "SpellFail": "DealDamage((10d12)/2,Force,Magical)", "SpellProperties": "RemoveStatus(QUIVERING_PALM)",
    "TooltipDamageList": "DealDamage(10d12,Force)", "TooltipAttackSave": "Constitution", "DamageType": "Force",
    "SpellFlags": "IsHarmful;IgnoreSilence"}, icon="Action_Monk_OpenHandTechnique_Push")
G.spell("Target_QuiveringPalm_Release", "Quivering Palm: Release", "End the vibrations harmlessly.", {
    "SpellType": "Target", "Level": "0", "TargetRadius": "60", "UseCosts": "", "AIFlags": "CanNotUse",
    "TargetConditions": "HasStatus('QUIVERING_PALM',context.Target,context.Source)", "SpellProperties": "RemoveStatus(QUIVERING_PALM)",
    "SpellFlags": "IgnoreSilence"}, icon="Action_Monk_OpenHandTechnique_Push")


# ---------------------------------------------------------------- class resources past 12 (resource audit 2026-10-03)
# Monk 15 Perfect Focus (PHB 2024): at Initiative, with 3 or fewer Focus Points, regain them up to 4 (it used to raise
# the maximum by 2). Top-down ladder: each step sees the amount the previous one left.
KI = lambda n: f"HasActionResource('KiPoint',{n},0,false,false,context.Source)"
G.passive("Monk_PerfectFocus", "Perfect Focus",
          "When you roll Initiative and have 3 or fewer Focus Points, you regain expended Focus Points until you have 4.", {
              "StatsFunctorContext": "OnCombatStarted",
              "StatsFunctors": ";".join(f"IF({KI(have)} and not {KI(have + 1)}):RestoreResource(SELF,KiPoint,{4 - have},0)" for have in (3, 2, 1))
                               + f";IF(not {KI(1)}):RestoreResource(SELF,KiPoint,4,0)"},
          icon="PassiveFeature_Generic_Tactical")
# Druid 20 Archdruid (PHB 2024): Evergreen Wild Shape + Nature Magician (it used to restore every use on a Short Rest and
# at combat start, plus +100 uses - the 2014 "unlimited").
G.spell("Shout_ApoNatureMagician", "Nature Magician",
        "Once per Long Rest, convert unexpended uses of Wild Shape into a single spell slot: 2 spell levels per use.", {
            "SpellType": "Shout", "TargetConditions": "Self()", "ContainerSpells": ";".join(f"Shout_ApoNatureMagician_{n}" for n in (1, 2, 3, 4)),
            "SpellFlags": "IsLinkedSpellContainer", "UseCosts": "ApoNatureMagician:1", "VerbalIntent": "Utility"}, icon="Skill_Druid_WildShape")
for n in (1, 2, 3, 4):
    G.spell(f"Shout_ApoNatureMagician_{n}", f"Nature Magician: {n} use{'s' if n > 1 else ''} -> level {2 * n} slot",
            f"Expend {n} use{'s' if n > 1 else ''} of Wild Shape to regain a level {2 * n} spell slot.", {
                "SpellType": "Shout", "TargetConditions": "Self()", "SpellContainerID": "Shout_ApoNatureMagician",
                "SpellProperties": f"RestoreResource(SELF,SpellSlot,1,{2 * n})", "UseCosts": f"WildShape:{n};ApoNatureMagician:1",
                "VerbalIntent": "Utility"}, icon="Skill_Druid_WildShape")
G.resource("ApoNatureMagician", 1, "Rest", "Nature Magician", "Convert Wild Shape uses into a spell slot.")
G.passive("Druid_Archdruid", "Archdruid",
          "Evergreen Wild Shape: when you roll Initiative with no uses of Wild Shape left, you regain one. Nature Magician: once per Long Rest, convert unexpended Wild Shape uses into a spell slot (2 spell levels per use).", {
              "StatsFunctorContext": "OnCombatStarted",
              "Conditions": "not HasActionResource('WildShape',1,0,false,false,context.Source)",
              "StatsFunctors": "RestoreResource(SELF,WildShape,1,0)",
              "Boosts": "UnlockSpell(Shout_ApoNatureMagician);ActionResource(ApoNatureMagician,1,0)"}, icon="Skill_Druid_WildShape")
# Fighter 17 Action Surge (PHB 2024): two uses before a rest, only once per turn. The base Action Surge is a
# once-per-Short-Rest cooldown, so the second use is its own spell with its own cooldown.
G.spell("Shout_ApoActionSurge_Second", "Action Surge (second use)", "Use Action Surge a second time before a rest (not on a turn you already did).", {
    "RequirementConditions": "not HasStatus('ACTION_SURGE',context.Source)"}, using="Shout_ActionSurge")
G.passive("Fighter_17_ActionSurgeTwice", "Action Surge (two uses)",
          "You can use Action Surge twice before a rest, but only once on a turn.", {"Boosts": "UnlockSpell(Shout_ApoActionSurge_Second)"},
          icon=icon_of("Shout_ActionSurge"))

# ---------------------------------------------------------------- progression
NODES = {
    # resource audit fixes (2026-10-03): real resource names, 2024 levels
    "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6": {"PassivesAdded": "Fighter_StudiedAttacks", "Boosts": "ActionResource(Interrupt_Indomitable,1,0)"},
    "e5f6a7b8-c9d0-41e2-f3a4-b5c6d7e8f9a0": {"PassivesAdded": "Fighter_17_ActionSurgeTwice", "Boosts": "ActionResource(Interrupt_Indomitable,1,0)"},
    "11111111-1111-1111-1111-111111111101": {"PassivesAdded": "Barbarian_BrutalStrike_Improved"},
    "11111111-1111-1111-1111-111111111105": {"PassivesAdded": "Barbarian_BrutalStrike_17", "Boosts": "ActionResource(Rage,1,0)"},
    "11111111-1111-1111-1111-111111111106": {"PassivesAdded": "Barbarian_IndomitableMight"},
    "88888888-8888-8888-8888-888888888805": {"PassivesAdded": "UnlockedSpellSlotLevel9", "Boosts": "ActionResource(SpellSlot,1,9);ActionResource(WildShape,1,0)",
                                             "Selectors": "AddSpells(00190001-0001-0001-0001-000000000004)"},  # Druid 9th-level list (9127692, 2026-10-04)
    "88888888-8888-8888-8888-888888888808": {"PassivesAdded": "Druid_Archdruid", "Boosts": "ActionResource(SpellSlot,1,7)"},
    "55555555-5555-5555-5555-555555555502": {"PassivesAdded": "Ranger_14_NaturesVeil"},
    "55555555-5555-5555-5555-555555555505": {"PassivesAdded": "Ranger_17_PreciseHunter", "Boosts": "ActionResource(SpellSlot,1,4);ActionResource(SpellSlot,1,5)",
                                             "Selectors": "AddSpells(6b625ece-306d-576a-9fa2-896d884e4e05)"},
    "17171717-1717-1717-1717-171717171702": {"PassivesAdded": "Glamour_14_UnbreakableMajesty"},
    "aa111111-1111-1111-1111-111111111101": {"PassivesAdded": "BattleMaster_Relentless", "Boosts": "ActionResource(SuperiorityDie,1,0)",
                                             "Selectors": "SelectPassives(e51a2ef5-3663-43f9-8e74-5e28520323f1,2,Maneuvers)"},
}

if __name__ == "__main__":
    drop_entries("Passive.txt", ["BattleMaster_Relentless", "OpenHand_17_QuiveringPalm", "Monk_PerfectFocus", "Druid_Archdruid"])
    drop_entries("Spell_Target.txt", ["Target_Apotheosis_QuiveringPalm"])
    G.write_stats("ClassFeatures", "gen_class_features.py", "issues #11 #12 #13")
    G.patch_files()
    patch_progressions(NODES, [], "CLASS FEATURES 2024")
    G.patch_loca()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.I)} interrupts, {len(G.loca)} strings")
