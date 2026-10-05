"""Subclass features at levels 13-20 that dnd55e's subclasses never reach (Scripts/subclass_gap_audit.py lists them).

Each feature follows the source dnd55e uses for the subclass (texts: References/Subclasses/Subclasses_13_20_Sources.txt):
  UA 2025 Horror Subclasses: College of Spirits 14, Hollow Warden 15, Shadow Sorcery 14/18, Hexblade 14, Undead 14
  XGE: Storm Sorcery 14/18, Divine Soul 14/18, Conquest 15/20, Arcane Archer 15/18, Kensei/Sun Soul/Drunken Master 17,
       Swashbuckler 13/17, Forge 17, Circle of Dreams 14
  UA 2025 Subclasses Update: Cavalier 15/18   DMG 2014 (as the base game): Oathbreaker 15/20
  SCAG: Crown 15/20   TCoE: Watchers 15/20, Twilight 17, Spores 14, Swarmkeeper 15   PHB 2014: Tempest 17
Lua for what stats can't do: SubclassFeatures.lua.

Owns Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_SubclassFeatures.txt, the resources/progression nodes
between SUBCLASS FEATURES 13-20 markers, and their loca.
Run: python3 Scripts/gen_subclass_features.py
"""
from gen_common import Gen, patch_progressions, SHOUT_ANIM, icon_of

G = Gen("subclassfeat", "SUBCLASS FEATURES 13-20")
NODES = []  # (table, name, level, passives)
ALL_BUT_FORCE_RADIANT = ["Acid", "Bludgeoning", "Cold", "Fire", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic",
                         "Slashing", "Thunder"]


def node(table, name, level, *passives, boosts=None, selectors=None):
    NODES.append((table, name, level, list(passives), boosts, selectors))


def limited(res, title, text, replenish, mx=1):
    """A once-per-rest feature's resource and the passive boost that grants it."""
    G.resource(res, mx, replenish, title, text)
    return f"ActionResource({res},{mx},0)"


# ================================================================ Sorcerer: Storm Sorcery (XGE)
STORM = "fac6ea25-a7f8-4793-b331-d884041e5adb"
G.passive("StormSorcery_14_StormsFury", "Storm's Fury",
          "When you are hit by a melee attack, you can use your Reaction to deal Lightning damage equal to your Sorcerer level to the attacker; it makes a Strength saving throw or is pushed up to 20 feet away.",
          {"Boosts": "UnlockInterrupt(Interrupt_StormsFury)"}, icon="PassiveFeature_HeartOfTheStorm_Lightning",
          comment="The base game's Storm's Fury (dnd55e blanks it at 11; XGE has it at 14).")
G.passive("StormSorcery_18_WindSoul", "Wind Soul",
          "You have Immunity to Lightning and Thunder damage and a magical Fly Speed. As an action you can give up to 3 + your Charisma modifier creatures within 30 feet a Fly Speed for 1 hour (once per Short or Long Rest).", {
              "Boosts": "Resistance(Lightning,Immune);Resistance(Thunder,Immune);UnlockSpell(Projectile_Fly_Spell);UnlockSpell(Shout_ApoWindSoul);"
                        + limited("ApoWindSoul", "Wind Soul", "Share your flight.", "ShortRest")},
          icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoWindSoul", "Wind Soul: Share Flight",
        "Up to 3 + your Charisma modifier creatures within 30 feet gain a Fly Speed for 1 hour.", {
            "SpellType": "Shout", "AreaRadius": "9", "TargetConditions": "Ally() and not Dead()",
            "SpellProperties": "ApplyStatus(FLY,100,600)", "TooltipStatusApply": "ApplyStatus(FLY,100,600)",
            "UseCosts": "ActionPoint:1;ApoWindSoul:1", "VerbalIntent": "Buff", "SpellAnimation": SHOUT_ANIM},
        icon="Spell_Transmutation_Fly")
node(STORM, "StormSorcery", 14, "StormSorcery_14_StormsFury")
node(STORM, "StormSorcery", 18, "StormSorcery_18_WindSoul")

# ================================================================ Sorcerer: Shadow Sorcery (UA 2025 Horror)
SHADOW = "02d68ea9-5b8d-4f3f-a37a-96ae78d233cd"
G.spell("Target_ApoShadowWalk", "Shadow Walk",
        "While you are in Dim Light or Darkness, teleport up to 120 feet to an unoccupied space you can see that is also in Dim Light or Darkness.",
        {"TargetRadius": "36", "RechargeValues": "", "UseCosts": "BonusActionPoint:1"}, using="Target_ShadowStep",
        icon="Action_ShadowWalk")
G.passive("ShadowMagic_14_ShadowWalk", "Shadow Walk",
          "As a Bonus Action while in Dim Light or Darkness, teleport up to 120 feet to a space in Dim Light or Darkness.",
          {"Boosts": "UnlockSpell(Target_ApoShadowWalk)"}, icon="Action_ShadowWalk")
UMBRAL = ("For 1 minute: Resistance to all damage except Force and Radiant, and if you would drop to 0 Hit Points you make a "
          "Charisma saving throw (DC 5 + half the damage taken); on a success your Hit Points instead become three times "
          "your Sorcerer level.")
G.status("APO_UMBRAL_FORM", "Umbral Form", UMBRAL, {
    "Boosts": ";".join(f"Resistance({t},Resistant)" for t in ALL_BUT_FORCE_RADIANT) + ";DownedStatus(APO_UMBRAL_GRAVE_DOWNED,7)",
    "StackId": "APO_UMBRAL_FORM", "RemoveEvents": "OnStatusApplied",
    # not on its own 0 HP stand-in (an incapacitating DOWNED-type status): a successful save keeps the form (2026-10-03)
    "RemoveConditions": "HasAnyStatus({'SG_Incapacitated'}) and not HasStatus('APO_UMBRAL_GRAVE_DOWNED')"},
    icon="Action_UmbralCloak", comment="SubclassFeatures.lua: the Strength of the Grave save at 0 HP.")
# the Last Stand pattern (gen_epic_boons.py): a downed replacement holds you at 1 HP, then Lua rolls the save
G.status("APO_UMBRAL_GRAVE_DOWNED", "Strength of the Grave", None, {"OnApplyFunctors": "RegainHitPoints(1,Guaranteed)"},
         using="RELENTLESS_ENDURANCE_DOWNED")
G.spell("Shout_ApoUmbralForm", "Umbral Form", "Adopt a shadowy form. " + UMBRAL, {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_UMBRAL_FORM,100,10)",
    "TooltipStatusApply": "ApplyStatus(APO_UMBRAL_FORM,100,10)", "UseCosts": "BonusActionPoint:1;ApoUmbralForm:1",
    "VerbalIntent": "Buff"}, icon="Action_UmbralCloak")
G.spell("Shout_ApoUmbralForm_SorceryPoints", "Umbral Form (6 Sorcery Points)", "Adopt a shadowy form again by spending 6 Sorcery Points. " + UMBRAL,
        {"UseCosts": "BonusActionPoint:1;SorceryPoint:6",
         "RequirementConditions": "not HasActionResource('ApoUmbralForm',1,0,false,false,context.Source)"},
        using="Shout_ApoUmbralForm", icon="Action_UmbralCloak")
G.passive("ShadowMagic_18_UmbralForm", "Umbral Form", "As a Bonus Action, once per Long Rest (or for 6 Sorcery Points): " + UMBRAL, {
    "Boosts": "UnlockSpell(Shout_ApoUmbralForm);UnlockSpell(Shout_ApoUmbralForm_SorceryPoints);"
              + limited("ApoUmbralForm", "Umbral Form", "Adopt your shadowy form.", "Rest")},
    icon="Action_UmbralCloak")
node(SHADOW, "ShadowMagic", 14, "ShadowMagic_14_ShadowWalk")
node(SHADOW, "ShadowMagic", 18, "ShadowMagic_18_UmbralForm")

# ================================================================ Sorcerer: Divine Soul (XGE)
DIVINE = "f98f8748-4842-4441-a3c0-1c2785333e02"
G.status("APO_OTHERWORLDLY_WINGS", "Otherworldly Wings", "Spectral wings: you have a Fly Speed.", {
    "Boosts": "UnlockSpell(Projectile_Fly_Spell)", "StackId": "APO_OTHERWORLDLY_WINGS",
    "RemoveEvents": "OnStatusApplied", "RemoveConditions": "HasAnyStatus({'SG_Incapacitated'})"}, icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoOtherworldlyWings", "Otherworldly Wings", "Manifest spectral wings: you have a Fly Speed until you're Incapacitated.", {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_OTHERWORLDLY_WINGS,100,-1)",
    "TooltipStatusApply": "ApplyStatus(APO_OTHERWORLDLY_WINGS,100,-1)", "UseCosts": "BonusActionPoint:1", "VerbalIntent": "Buff"},
    icon="Spell_Transmutation_Fly")
G.passive("DivineSoul_14_OtherworldlyWings", "Otherworldly Wings", "As a Bonus Action, manifest spectral wings and gain a Fly Speed.",
          {"Boosts": "UnlockSpell(Shout_ApoOtherworldlyWings)"}, icon="Spell_Transmutation_Fly")
G.spell("Shout_ApoUnearthlyRecovery", "Unearthly Recovery",
        "While you have fewer than half your Hit Points, regain Hit Points equal to half your Hit Point maximum.", {
            "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "RegainHitPoints(MaxHP/2)",
            "TooltipDamageList": "RegainHitPoints(MaxHP/2)",
            "RequirementConditions": "HasHPPercentageWithoutTemporaryHPLessThan(50, context.Source)",
            "UseCosts": "BonusActionPoint:1;ApoUnearthlyRecovery:1", "VerbalIntent": "Healing"}, icon="Spell_Evocation_CureWounds")
G.passive("DivineSoul_18_UnearthlyRecovery", "Unearthly Recovery",
          "Once per Long Rest, as a Bonus Action while below half your Hit Points, regain half your Hit Point maximum.", {
              "Boosts": "UnlockSpell(Shout_ApoUnearthlyRecovery);"
                        + limited("ApoUnearthlyRecovery", "Unearthly Recovery", "Recover from grievous injuries.", "Rest")},
          icon="Spell_Evocation_CureWounds")
node(DIVINE, "DivineSoul", 14, "DivineSoul_14_OtherworldlyWings")
node(DIVINE, "DivineSoul", 18, "DivineSoul_18_UnearthlyRecovery")

# ================================================================ Warlock: Hexblade (UA 2025 Horror)
HEXBLADE = "2b9b50de-48e2-4b1c-b40d-6050aa85009a"
G.status("APO_INFECTIOUS_HEX", "Infectious Hex", None, {
    "StackId": "APO_INFECTIOUS_HEX", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Marker on the hexed target: SubclassFeatures.lua deals 1d6 Necrotic to another creature within 30 feet of it.")
G.status("APO_INFECTIOUS_HEX_DAMAGE", "Infectious Hex", None, {
    "OnApplyFunctors": "DealDamage(1d6,Necrotic,Magical)", "StackId": "APO_INFECTIOUS_HEX_DAMAGE",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.status("APO_RESILIENT_HEX", "Resilient Hex", "Taking damage can't break your Concentration on Hex.", {
    "Boosts": "ConcentrationIgnoreDamage(Enchantment)", "StackId": "APO_RESILIENT_HEX",
    "StatusPropertyFlags": "DisableCombatlog"}, icon="Spell_Enchantment_Hex",
    comment="SubclassFeatures.lua keeps it on only while you concentrate on Hex.")
G.passive("Hexblade_14_MasterfulHex", "Masterful Hex",
          "Your attacks against the target of your Hex score a Critical Hit on a 19 or 20. When you use a Hexblade's Maneuver, one other creature within 30 feet of the cursed target takes 1d6 Necrotic damage. Taking damage can't break your Concentration on Hex.", {
              "Boosts": "IF(HasHexStatus()):ReduceCriticalAttackThreshold(1)",
              "StatsFunctorContext": "OnDamage", "Conditions": "HasHexStatus() and IsAttack()",
              "StatsFunctors": "ApplyStatus(APO_INFECTIOUS_HEX,100,0)"}, icon="Spell_Enchantment_Hex")
node(HEXBLADE, "Hexblade", 14, "Hexblade_14_MasterfulHex")

# ================================================================ Warlock: Undead Patron (UA 2025 Horror)
UNDEAD = "35c30532-8f59-4980-b21b-4f729d2cd786"
G.status("APO_VITALITY_SIPHON", "Vitality Siphon", None, {
    "OnApplyFunctors": "RegainHitPoints(max(1,CharismaModifier))", "StackId": "APO_VITALITY_SIPHON",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.passive("UndeadPatron_14_SuperiorDread", "Superior Dread",
          "While in your Form of Dread you have a Fly Speed, and once per turn when you deal Necrotic damage you regain Hit Points equal to your Charisma modifier (minimum 1).", {
              "BoostContext": "OnStatusApplied;OnStatusRemoved",
              "Boosts": "IF(HasStatus('FORM_OF_DREAD',context.Source)):UnlockSpell(Projectile_Fly_Spell)",
              "StatsFunctorContext": "OnDamage",
              "Conditions": "HasStatus('FORM_OF_DREAD',context.Source) and HasDamageDoneForType(DamageType.Necrotic)",
              "StatsFunctors": "ApplyStatus(SELF,APO_VITALITY_SIPHON,100,0)", "Properties": "Highlighted;OncePerTurn"},
          icon="Spell_Necromancy_VampiricTouch")
node(UNDEAD, "UndeadPatron", 14, "UndeadPatron_14_SuperiorDread")

# ================================================================ Bard: College of Spirits (UA 2025 Horror)
SPIRITS = "3669d6ce-d951-4491-8c23-fe2fa922357c"
SPIRIT_NAMES = ["Beloved", "Sharpshooter", "Avenger", "Renegade", "Fortune Teller", "Wayfarer", "Trickster", "Shade",
                "Arsonist", "Coward"]
G.passive("Spirits_14_MysticalConnection", "Mystical Connection",
          "Whenever you roll on the Spirits from Beyond table, you roll twice and choose: the second spirit is offered as a free switch.",
          {}, icon="Spirits_3_SpiritsFromBeyond", comment="SubclassFeatures.lua rolls the second spirit (the die dnd55e uses).")
for i, nm in enumerate(SPIRIT_NAMES):
    clear = ";".join(f"RemoveStatus(SELF,SPIRITS_FROM_BEYOND_{k})" for k in range(10))
    G.status(f"APO_MYSTICAL_CONNECTION_{i}", f"Mystical Connection: {nm}",
             f"Your second roll on the Spirits from Beyond table: {nm}. You can switch to it (no action).", {
                 "Boosts": f"UnlockSpell(Shout_ApoMysticalConnection_{i})", "StackId": "APO_MYSTICAL_CONNECTION"},
             icon="Spirits_3_SpiritsFromBeyond")
    G.spell(f"Shout_ApoMysticalConnection_{i}", f"Mystical Connection: take the {nm}",
            f"Take the {nm} instead of the spirit you rolled first.", {
                "SpellType": "Shout", "TargetConditions": "Self()",
                "SpellProperties": f"{clear};RemoveStatus(SELF,APO_MYSTICAL_CONNECTION_{i});ApplyStatus(SELF,SPIRITS_FROM_BEYOND_{i},100,-1)",
                "UseCosts": "", "VerbalIntent": "Buff"},
            icon="Spirits_3_SpiritsFromBeyond")
node(SPIRITS, "SpiritsCollege", 14, "Spirits_14_MysticalConnection")

# ================================================================ Ranger: Hollow Warden (UA 2025 Horror)
HOLLOW = "e5e8acd6-4fd3-4295-8e78-3a77b8c30f2d"
G.passive("HollowWarden_15_AncientEndurance", "Ancient Endurance",
          "Timeless: you have Immunity to Exhaustion. Persistent Hunt: if you drop to 0 Hit Points while transformed by Wrath of the Wild and don't die outright, you can expend a level 4+ spell slot; your Hit Points instead become five times the slot's level.",
          {"Boosts": "StatusImmunity(EXHAUSTED);IF(HasStatus('WRATH_OF_THE_WILD',context.Source) and not HasStatus('APO_PERSISTENT_HUNT_SPENT',context.Source)):DownedStatus(APO_PERSISTENT_HUNT_DOWNED,7)",
           "BoostContext": "OnStatusApplied;OnStatusRemoved"}, icon="PassiveFeature_Generic_Magical",
          comment="SubclassFeatures.lua: Persistent Hunt (spends the lowest level 4+ slot you have).")
G.status("APO_PERSISTENT_HUNT_DOWNED", "Persistent Hunt", None, {"OnApplyFunctors": "RegainHitPoints(1,Guaranteed)"},
         using="RELENTLESS_ENDURANCE_DOWNED")
G.status("APO_PERSISTENT_HUNT_SPENT", "Persistent Hunt", None, {
    "StackId": "APO_PERSISTENT_HUNT_SPENT", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Set when no level 4+ slot was left, so the next drop goes down normally instead of looping.")
node(HOLLOW, "HollowWarden", 15, "HollowWarden_15_AncientEndurance")


# ================================================================ group 2 (2026-10-03)
ALL_TYPES = ALL_BUT_FORCE_RADIANT + ["Force", "Radiant"]
EXTRAPLANAR = "(Tagged('ABERRATION',context.Target) or Tagged('CELESTIAL',context.Target) or Tagged('ELEMENTAL',context.Target) or Tagged('FEY',context.Target) or Tagged('FIEND',context.Target))"
NONMAGICAL_BPS = "Resistance(Bludgeoning,ResistantToNonMagical);Resistance(Piercing,ResistantToNonMagical);Resistance(Slashing,ResistantToNonMagical)"


def once(spell_id, status, title, text, turns, cost_action, res, replenish="Rest", icon=None, extra=None):
    """A once-per-rest self buff: the shout, its resource and the passive boost that grants both."""
    G.spell(spell_id, title, text, {
        "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": f"ApplyStatus({status},100,{turns})",
        "TooltipStatusApply": f"ApplyStatus({status},100,{turns})", "UseCosts": f"{cost_action}:1;{res}:1",
        "VerbalIntent": "Buff", **(extra or {})}, icon=icon)
    return f"UnlockSpell({spell_id});" + limited(res, title, text, replenish)


# ---------------------------------------------------------------- Paladin: Oath of Conquest (XGE)
CONQUEST = "06cd782b-69b2-4200-93ea-77a611f87363"
G.passive("Conquest_15_ScornfulRebuke", "Scornful Rebuke",
          "Whenever a creature hits you with an attack, it takes Psychic damage equal to your Charisma modifier (minimum 1).", {
              "StatsFunctorContext": "OnAttacked", "Conditions": "HasDamageEffectFlag(DamageFlags.Hit) and not SpellTypeIs(SpellType.Throw)",
              "StatsFunctors": "DealDamage(SWAP,max(1,CharismaModifier),Psychic,Magical)"}, icon="Action_Paladin_DreadfulAspect")
G.status("APO_INVINCIBLE_CONQUEROR", "Invincible Conqueror",
         "Resistance to all damage, one additional attack when you take the Attack action, and your melee weapon attacks score a Critical Hit on a 19 or 20.", {
             "Boosts": ";".join(f"Resistance({t},Resistant)" for t in ALL_TYPES) + ";IF(IsMeleeWeaponAttack()):ReduceCriticalAttackThreshold(1)",
             "Passives": "ExtraAttack_2", "StackId": "APO_INVINCIBLE_CONQUEROR"}, icon="Action_Paladin_DreadfulAspect")
G.passive("Conquest_20_InvincibleConqueror", "Invincible Conqueror",
          "As an action, once per Long Rest: for 1 minute you have Resistance to all damage, make one additional attack with the Attack action, and score a Critical Hit with melee weapon attacks on a 19 or 20.", {
              "Boosts": once("Shout_ApoInvincibleConqueror", "APO_INVINCIBLE_CONQUEROR", "Invincible Conqueror",
                             "Become an avatar of conquest for 1 minute.", 10, "ActionPoint", "ApoInvincibleConqueror",
                             icon="Action_Paladin_DreadfulAspect")},
          icon="Action_Paladin_DreadfulAspect")
node(CONQUEST, "Conquest", 15, "Conquest_15_ScornfulRebuke")
node(CONQUEST, "Conquest", 20, "Conquest_20_InvincibleConqueror")

# ---------------------------------------------------------------- Paladin: Oath of the Crown (SCAG)
CROWN = "e3a25a7a-e793-4b99-9d4a-0fbc17fcc1ff"
G.passive("Crown_15_UnyieldingSpirit", "Unyielding Spirit",
          "You have Advantage on saving throws to avoid becoming Paralyzed or Stunned.", {"Boosts": "Tag(PARALYZED_ADV)"},
          icon="PassiveFeature_Generic_Magical", comment="Stunned has no *_ADV tag in the engine: only Paralyzed is covered.")
G.status("APO_EXALTED_CHAMPION_ALLY", "Exalted Champion", "Advantage on Death Saving Throws and Wisdom saving throws.", {
    "Boosts": "Advantage(DeathSavingThrow);Advantage(SavingThrow,Wisdom)", "StackId": "APO_EXALTED_CHAMPION_ALLY"},
    icon="PassiveFeature_Generic_Magical")
G.status("APO_EXALTED_CHAMPION", "Exalted Champion",
         "Resistance to Bludgeoning, Piercing and Slashing damage from nonmagical attacks; you and your allies within 30 feet have Advantage on Wisdom saving throws and Death Saving Throws.", {
             "Boosts": NONMAGICAL_BPS + ";Advantage(SavingThrow,Wisdom)", "AuraRadius": "9",
             "AuraStatuses": "IF(Ally() and not Self()):ApplyStatus(APO_EXALTED_CHAMPION_ALLY)", "StackId": "APO_EXALTED_CHAMPION",
             "RemoveEvents": "OnStatusApplied", "RemoveConditions": "HasAnyStatus({'SG_Incapacitated'})"}, icon="PassiveFeature_Generic_Magical")
G.passive("Crown_20_ExaltedChampion", "Exalted Champion",
          "As an action, once per Long Rest, for 1 hour: Resistance to nonmagical Bludgeoning, Piercing and Slashing damage, and you and your allies within 30 feet have Advantage on Wisdom saving throws (allies also on Death Saving Throws).", {
              "Boosts": once("Shout_ApoExaltedChampion", "APO_EXALTED_CHAMPION", "Exalted Champion", "Inspire those who fight beside you for 1 hour.",
                             600, "ActionPoint", "ApoExaltedChampion", icon="PassiveFeature_Generic_Magical")},
          icon="PassiveFeature_Generic_Magical")
node(CROWN, "Crown", 15, "Crown_15_UnyieldingSpirit")
node(CROWN, "Crown", 20, "Crown_20_ExaltedChampion")

# ---------------------------------------------------------------- Paladin: Oath of the Watchers (TCoE)
WATCHERS = "403102da-744a-4f16-b392-c1da7e9bbf2c"
G.status("APO_VIGILANT_REBUKE", "Vigilant Rebuke", None, {
    "OnApplyFunctors": "DealDamage(2d8+CharismaModifier,Force,Magical)", "StackId": "APO_VIGILANT_REBUKE",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.passive("Watchers_15_VigilantRebuke", "Vigilant Rebuke",
          "When you or a creature you can see within 30 feet succeeds on an Intelligence, Wisdom or Charisma saving throw, you can use your Reaction to deal 2d8 + your Charisma modifier Force damage to the creature that forced the save.",
          {}, icon="Spell_Abjuration_MagicCircle", comment="SubclassFeatures.lua (saving throw event; spends your Reaction).")
G.status("APO_MORTAL_BULWARK_RESISTED", "Resisted banishment", "Can't be banished by Mortal Bulwark for 24 hours.", {
    "StackId": "APO_MORTAL_BULWARK_RESISTED", "StatusPropertyFlags": "DisableOverhead"})
G.status("APO_MORTAL_BULWARK", "Mortal Bulwark",
         "Advantage on attack rolls against Aberrations, Celestials, Elementals, Fey and Fiends; a creature you hit makes a Charisma saving throw or is banished.", {
             "Boosts": f"IF({EXTRAPLANAR}):Advantage(AttackRoll)", "StackId": "APO_MORTAL_BULWARK"},
         icon="Spell_Abjuration_MagicCircle")
G.passive("Watchers_20_MortalBulwark", "Mortal Bulwark",
          "As a Bonus Action, once per Long Rest (or by expending a level 5 spell slot), for 1 minute: Advantage on attack rolls against Aberrations, Celestials, Elementals, Fey and Fiends, and a creature of those kinds you hit makes a Charisma saving throw or is banished (on a success it can't be banished this way for 24 hours).", {
              "Boosts": once("Shout_ApoMortalBulwark", "APO_MORTAL_BULWARK", "Mortal Bulwark", "Defend the mortal realms for 1 minute.",
                             10, "BonusActionPoint", "ApoMortalBulwark", icon="Spell_Abjuration_MagicCircle")
                        + ";UnlockSpell(Shout_ApoMortalBulwark_Slot)",
              "StatsFunctorContext": "OnDamage",
              "Conditions": f"HasStatus('APO_MORTAL_BULWARK',context.Source) and IsAttack() and {EXTRAPLANAR} and not HasStatus('APO_MORTAL_BULWARK_RESISTED')",
              "StatsFunctors": "IF(not SavingThrow(Ability.Charisma, SourceSpellDC())):ApplyStatus(BANISHED,100,10);IF(not HasStatus('BANISHED')):ApplyStatus(APO_MORTAL_BULWARK_RESISTED,100,1440)"},
          icon="Spell_Abjuration_MagicCircle")
G.spell("Shout_ApoMortalBulwark_Slot", "Mortal Bulwark (level 5 slot)", "Use Mortal Bulwark again by expending a level 5 spell slot.", {
    "UseCosts": "BonusActionPoint:1;SpellSlotsGroup:1:1:5",
    "RequirementConditions": "not HasActionResource('ApoMortalBulwark',1,0,false,false,context.Source)"},
    using="Shout_ApoMortalBulwark", icon="Spell_Abjuration_MagicCircle")
node(WATCHERS, "Watchers", 15, "Watchers_15_VigilantRebuke")
node(WATCHERS, "Watchers", 20, "Watchers_20_MortalBulwark")

# ---------------------------------------------------------------- Paladin: Oathbreaker (DMG 2014, as the base game)
OATHBREAKER = "f0d6f933-4532-463f-b378-a1e8b0164325"
G.passive("Oathbreaker_15_SupernaturalResistance", "Supernatural Resistance",
          "You have Resistance to Bludgeoning, Piercing and Slashing damage from nonmagical attacks.", {"Boosts": NONMAGICAL_BPS},
          icon="PassiveFeature_Generic_Magical")
G.status("APO_DREAD_LORD_FEAR", "Dread Lord", None, {
    "StackId": "APO_DREAD_LORD_FEAR", "TickType": "StartTurn",
    "TickFunctors": "IF(HasStatus('SG_Frightened')):DealDamage(4d10,Psychic,Magical)",
    "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.status("APO_DREAD_LORD_SHADOW", "Draped in Shadow", "Creatures that rely on sight have Disadvantage on attack rolls against you.", {
    "Boosts": "Disadvantage(AttackTarget)", "StackId": "APO_DREAD_LORD_SHADOW"}, icon="Spell_Evocation_Darkness")
G.status("APO_DREAD_LORD", "Dread Lord",
         "An aura of gloom (30 feet): Frightened enemies that start their turn in it take 4d10 Psychic damage, you and your allies in it are draped in shadow, and you can make Shadow Strike attacks.", {
             "Boosts": "UnlockSpell(Target_ApoDreadLordShadowStrike)", "AuraRadius": "9",
             "AuraStatuses": "IF(Enemy()):ApplyStatus(APO_DREAD_LORD_FEAR);IF(Ally() or Self()):ApplyStatus(APO_DREAD_LORD_SHADOW)",
             "StackId": "APO_DREAD_LORD"}, icon="Spell_Evocation_Darkness")
G.spell("Target_ApoDreadLordShadowStrike", "Shadow Strike", "Melee spell attack against a creature in your aura: 3d10 + your Charisma modifier Necrotic damage.", {
    "SpellType": "Target", "TargetRadius": "9", "TargetConditions": "Character() and not Self() and not Dead()",
    "SpellRoll": "Attack(AttackType.MeleeSpellAttack)", "SpellSuccess": "DealDamage(3d10+CharismaModifier,Necrotic,Magical)",
    "TooltipDamageList": "DealDamage(3d10+CharismaModifier,Necrotic)", "TooltipAttackSave": "MeleeSpellAttack",
    "UseCosts": "BonusActionPoint:1", "SpellFlags": "IsSpell;IsHarmful", "VerbalIntent": "Damage", "DamageType": "Necrotic"},
    icon="Spell_Evocation_Darkness")
G.passive("Oathbreaker_20_DreadLord", "Dread Lord",
          "As an action, once per Long Rest, surround yourself with a 30-foot aura of gloom for 1 minute: Frightened enemies starting their turn in it take 4d10 Psychic damage, attackers relying on sight have Disadvantage against you and your allies in it, and as a Bonus Action you can make a Shadow Strike (3d10 + Charisma modifier Necrotic).", {
              "Boosts": once("Shout_ApoDreadLord", "APO_DREAD_LORD", "Dread Lord", "Surround yourself with an aura of gloom for 1 minute.",
                             10, "ActionPoint", "ApoDreadLord", icon="Spell_Evocation_Darkness")},
          icon="Spell_Evocation_Darkness")
node(OATHBREAKER, "Oathbreaker", 15, "Oathbreaker_15_SupernaturalResistance")
node(OATHBREAKER, "Oathbreaker", 20, "Oathbreaker_20_DreadLord")

# ---------------------------------------------------------------- Fighter: Cavalier (UA 2025 Subclasses Update)
CAVALIER = "ef6183fe-474b-440b-bd03-6e5cecc7e001"
G.status("APO_FEROCIOUS_CHARGE_SAVED", "Ferocious Charger", None, {
    "StackId": "APO_FEROCIOUS_CHARGE_SAVED", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.status("APO_FEROCIOUS_CHARGE_NEAR", "Ferocious Charger", None, {
    "OnApplyConditions": "not HasStatus('APO_FEROCIOUS_CHARGE_SAVED')",
    "OnApplyRoll": "not SavingThrow(Ability.Strength, SourceSpellDC(10, context.Source, Ability.Strength))",
    "OnApplySuccess": "ApplyStatus(PRONE,100,1)", "OnApplyFunctors": "ApplyStatus(APO_FEROCIOUS_CHARGE_SAVED,100,1)",
    "StackId": "APO_FEROCIOUS_CHARGE_NEAR", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Strength save DC 8 + your Strength modifier and Proficiency Bonus, once per creature per turn; Prone on a failure (the push option isn't offered).")
G.status("APO_FEROCIOUS_CHARGER", "Ferocious Charger",
         "First round of combat: +10 feet Speed, your movement doesn't provoke Opportunity Attacks, and a creature you move within 5 feet of makes a Strength saving throw or falls Prone.", {
             "Boosts": "ActionResource(Movement,3,0);IgnoreLeaveAttackRange()", "AuraRadius": "1.5",
             "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_FEROCIOUS_CHARGE_NEAR,100,0)", "StackId": "APO_FEROCIOUS_CHARGER"},
         icon="PassiveFeature_HuntersMark")
G.passive("Cavalier_15_FerociousCharger", "Ferocious Charger",
          "During the first round of each combat your Speed increases by 10 feet and your movement doesn't provoke Opportunity Attacks; a creature you move within 5 feet of that round makes a Strength saving throw (DC 8 + your Strength modifier and Proficiency Bonus) or has the Prone condition.", {
              "StatsFunctorContext": "OnCombatStarted", "StatsFunctors": "ApplyStatus(SELF,APO_FEROCIOUS_CHARGER,100,1)"},
          icon="PassiveFeature_HuntersMark")
G.passive("Cavalier_18_VigilantDefender", "Vigilant Defender",
          "In combat you get a special Reaction once on every creature's turn except yours, usable only for an Opportunity Attack and not on a turn you use your normal Reaction.", {
              "Boosts": "UnlockInterrupt(Interrupt_ApoVigilantDefender);ActionResource(ApoVigilantDefender,1,0)"},
          icon="PassiveFeature_HuntersMark", comment="SubclassFeatures.lua refills the special Reaction at each other creature's turn.")
G.resource("ApoVigilantDefender", 1, "Never", "Vigilant Defender", "A special Reaction for Opportunity Attacks on another creature's turn.")
G.interrupt("Interrupt_ApoVigilantDefender", "Vigilant Defender",
            "Make an Opportunity Attack with your special Reaction.", {
                "InterruptContext": "OnLeaveAttackRange", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
                "Conditions": "Enemy(context.Source,context.Observer) and not HasActionResource('ReactionActionPoint',1,0,false,false,context.Observer) and not Dead(context.Observer) and not HasAnyStatus({'SG_Incapacitated'},{},{},context.Observer)",
                "Properties": "UseSpell(OBSERVER_SOURCE,Target_MainHandAttack_OpportunityAttack,true,true,true)",
                "Cost": "ApoVigilantDefender:1", "Stack": "ApoVigilantDefender", "InterruptDefaultValue": "Enabled"},
            icon="PassiveFeature_HuntersMark")
node(CAVALIER, "Cavalier", 15, "Cavalier_15_FerociousCharger")
node(CAVALIER, "Cavalier", 18, "Cavalier_18_VigilantDefender")

# ---------------------------------------------------------------- Fighter: Arcane Archer (XGE, as the base game)
ARCHER = "537d34a9-c60d-4f1b-be41-312ab5d8c792"
G.passive("ArcaneArcher_15_EverReadyShot", "Ever-Ready Shot",
          "If you roll Initiative and have no uses of Arcane Shot remaining, you regain one.", {
              "StatsFunctorContext": "OnCombatStarted",
              "Conditions": "not HasActionResource('ArcaneShot',1,0,false,false,context.Source)",
              "StatsFunctors": "RestoreResource(SELF,ArcaneShot,1,0)"}, icon="Action_ArcaneArcher_BurstingArrow")
IMPROVED = {  # option: (damage type, extra dice at 18)
    "BanishingArrow": ("Force", "2d6"), "BeguilingArrow": ("Psychic", "2d6"), "BurstingArrow": ("Force", "2d6"),
    "EnfeeblingArrow": ("Necrotic", "2d6"), "GraspingArrow": ("Poison", "2d6"), "SeekingArrow": ("Force", "1d6"),
    "ShadowArrow": ("Psychic", "2d6"),
}
G.passive("ArcaneArcher_18_ImprovedShots", "Improved Shots",
          "Your Arcane Shot options deal more damage: Bursting, Enfeebling, Grasping, Shadow and Beguiling Arrow 4d6, Seeking Arrow 2d6, and Banishing Arrow also deals 2d6 Force.", {
              "Boosts": ";".join(f"IF(SpellId('Projectile_ArcaneShot_{k}')):DamageBonus({dice},{t})" for k, (t, dice) in IMPROVED.items())},
          icon="Action_ArcaneArcher_BurstingArrow")
node(ARCHER, "ArcaneArcher", 15, "ArcaneArcher_15_EverReadyShot")
node(ARCHER, "ArcaneArcher", 18, "ArcaneArcher_18_ImprovedShots")

# ---------------------------------------------------------------- Monk: Kensei, Sun Soul, Drunken Master (XGE)
KENSEI = "92b14b25-7da0-440e-95d9-08df115936fc"
G.resource("ApoUnerringAccuracy", 1, "Turn", "Unerring Accuracy", "Reroll a missed monk weapon attack once per turn.")
G.interrupt("Interrupt_ApoUnerringAccuracy", "Unerring Accuracy",
            "When you miss with a monk weapon attack on your turn, reroll it (once per turn).", {
                "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                "Conditions": "not Dead(context.Observer) and HasInterruptedAttack() and Self(context.Observer,context.Source) and IsMonkWeaponAttack() and not AnyEntityIsItem() and IsRerollInterruptInteresting(context.Source)",
                "Properties": "SetReroll(19,true)", "Cost": "ApoUnerringAccuracy:1", "Stack": "ApoUnerringAccuracy",
                "InterruptDefaultValue": "Enabled"}, icon="Action_Paladin_SacredWeapon")
G.passive("Kensei_17_UnerringAccuracy", "Unerring Accuracy",
          "If you miss with an attack roll using a monk weapon on your turn, you can reroll it (once on each of your turns).",
          {"Boosts": "UnlockInterrupt(Interrupt_ApoUnerringAccuracy);ActionResource(ApoUnerringAccuracy,1,0)"}, icon="Action_Paladin_SacredWeapon")
node(KENSEI, "Kensei", 17, "Kensei_17_UnerringAccuracy")

SUNSOUL = "878250ea-7516-4989-812a-be1d7c9a7726"
G.status("APO_SUN_SHIELD", "Sun Shield", "You shed Bright Light in a 30-foot radius; a creature that hits you with a melee attack can be burned (Reaction).", {
    "Boosts": "GameplayLight(9,false,0.1)", "StackId": "APO_SUN_SHIELD", "StatusGroups": "SG_Light"}, icon="SunSoul_11_SearingSunburst")
G.spell("Target_ApoSunShield", "Sun Shield", "Radiant damage equal to 5 + your Wisdom modifier to a creature that hit you in melee.", {
    "SpellType": "Target", "TargetRadius": "9", "TargetConditions": "Character()", "SpellProperties": "DealDamage(5+WisdomModifier,Radiant,Magical)",
    "TooltipDamageList": "DealDamage(5+WisdomModifier,Radiant)", "SpellFlags": "IsHarmful", "VerbalIntent": "Damage", "DamageType": "Radiant"},
    icon="SunSoul_11_SearingSunburst")
G.interrupt("Interrupt_ApoSunShield", "Sun Shield", "When a creature hits you with a melee attack while your light shines, deal 5 + your Wisdom modifier Radiant damage to it.", {
    "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and Enemy(context.Source,context.Observer) and HasStatus('APO_SUN_SHIELD',context.Observer) and IsHit() and IsMeleeAttack() and not AnyEntityIsItem() and HasLastAttackTriggered()",
    "Properties": "UseSpell(SWAP,Target_ApoSunShield,true,true,true)", "Cost": "ReactionActionPoint:1", "Stack": "ApoSunShield",
    "InterruptDefaultValue": "Ask;Enabled"}, icon="SunSoul_11_SearingSunburst")
G.passive("SunSoul_17_SunShield", "Sun Shield",
          "You shed Bright Light in a 30-foot radius (toggle). While it shines, when a creature hits you with a melee attack you can use your Reaction to deal 5 + your Wisdom modifier Radiant damage to it.", {
              "Properties": "IsToggled;ToggledDefaultOn;ToggledDefaultAddToHotbar;Highlighted",
              "ToggleOnFunctors": "ApplyStatus(SELF,APO_SUN_SHIELD,100,-1)", "ToggleOffFunctors": "RemoveStatus(SELF,APO_SUN_SHIELD)",
              "ToggleOffContext": "OnToggleOff", "Boosts": "UnlockInterrupt(Interrupt_ApoSunShield)"}, icon="SunSoul_11_SearingSunburst")
node(SUNSOUL, "SunSoul", 17, "SunSoul_17_SunShield")

DRUNKEN = "dbffd3ed-ef5c-4a0d-8b3b-86f017c30e21"
G.resource("ApoIntoxicatedFrenzy", 3, "Never", "Intoxicated Frenzy", "Additional Flurry of Blows attacks against different creatures this turn.")
G.status("APO_FRENZY_STRUCK", "Struck by the frenzy", None, {
    "StackId": "APO_FRENZY_STRUCK", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.spell("Target_ApoIntoxicatedFrenzy", "Intoxicated Frenzy", "An additional Flurry of Blows strike against a creature you haven't struck with it this turn.", {
    "UseCosts": "ApoIntoxicatedFrenzy:1", "TargetConditions": "not Self() and not Dead() and not HasStatus('APO_FRENZY_STRUCK',context.Target,context.Source)",
    "SpellProperties": "ApplyStatus(APO_FRENZY_STRUCK,100,1)"}, using="Target_UnarmedAttack", icon="Action_Monk_FlurryOfBlows")
G.passive("DrunkenMaster_17_IntoxicatedFrenzy", "Intoxicated Frenzy",
          "When you use Flurry of Blows you can make up to three additional Flurry attacks, each against a different creature this turn.", {
              "Boosts": "UnlockSpell(Target_ApoIntoxicatedFrenzy);ActionResource(ApoIntoxicatedFrenzy,3,0)"},
          icon="Action_Monk_FlurryOfBlows", comment="SubclassFeatures.lua gives the three attacks when you use Flurry of Blows (and empties them at turn end).")
node(DRUNKEN, "DrunkenMaster", 17, "DrunkenMaster_17_IntoxicatedFrenzy")

# ---------------------------------------------------------------- Rogue: Swashbuckler (XGE)
SWASH = "0a0f8dbb-ca06-4753-ac64-7c6876deeeae"
G.status("APO_ELEGANT_MANEUVER", "Elegant Maneuver", "Advantage on your next Acrobatics or Athletics check this turn.", {
    "Boosts": "Advantage(Skill,Acrobatics);Advantage(Skill,Athletics)", "StackId": "APO_ELEGANT_MANEUVER"}, icon="PassiveFeature_ExtraAttack")
G.spell("Shout_ApoElegantManeuver", "Elegant Maneuver", "Advantage on your next Dexterity (Acrobatics) or Strength (Athletics) check this turn.", {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_ELEGANT_MANEUVER,100,1)",
    "UseCosts": "BonusActionPoint:1", "VerbalIntent": "Buff"}, icon="PassiveFeature_ExtraAttack")
G.passive("Swashbuckler_13_ElegantManeuver", "Elegant Maneuver",
          "As a Bonus Action, gain Advantage on the next Dexterity (Acrobatics) or Strength (Athletics) check you make this turn.",
          {"Boosts": "UnlockSpell(Shout_ApoElegantManeuver)"}, icon="PassiveFeature_ExtraAttack")
G.interrupt("Interrupt_ApoMasterDuelist", "Master Duelist", "If you miss with an attack roll, roll it again with Advantage (once per Short Rest).", {
    "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "not Dead(context.Observer) and HasInterruptedAttack() and Self(context.Observer,context.Source) and not AnyEntityIsItem() and IsRerollInterruptInteresting(context.Source)",
    "Properties": "SetAdvantage()", "Cost": "ApoMasterDuelist:1", "Stack": "ApoMasterDuelist", "InterruptDefaultValue": "Ask;Enabled"},
    icon="PassiveFeature_ExtraAttack")
G.passive("Swashbuckler_17_MasterDuelist", "Master Duelist",
          "If you miss with an attack roll, you can roll it again with Advantage; once per Short or Long Rest.", {
              "Boosts": "UnlockInterrupt(Interrupt_ApoMasterDuelist);" + limited("ApoMasterDuelist", "Master Duelist", "Turn a miss around.", "ShortRest")},
          icon="PassiveFeature_ExtraAttack")
node(SWASH, "Swashbuckler", 13, "Swashbuckler_13_ElegantManeuver")
node(SWASH, "Swashbuckler", 17, "Swashbuckler_17_MasterDuelist")

# ---------------------------------------------------------------- Cleric: Forge (XGE), Twilight (TCoE), Tempest, Nature (PHB 2014)
G.passive("ForgeDomain_17_SaintOfForgeAndFire", "Saint of Forge and Fire",
          "You have Immunity to Fire damage, and while wearing Heavy Armor you have Resistance to Bludgeoning, Piercing and Slashing damage from nonmagical attacks.", {
              "Boosts": "Resistance(Fire,Immune);IF(HasHeavyArmor()):" + NONMAGICAL_BPS.replace(";", ";IF(HasHeavyArmor()):"),
              "BoostContext": "OnEquip;OnCreate"}, icon="Action_DivineStrike_Fire_Melee")
node("defe59d4-62be-4428-80cd-c34a10a4cb0d", "ForgeDomain", 17, "ForgeDomain_17_SaintOfForgeAndFire")
G.status("APO_TWILIGHT_SHROUD", "Twilight Shroud", "Half Cover: +2 to AC and Dexterity saving throws.", {
    "Boosts": "AC(2);RollBonus(SavingThrow,2,Dexterity)", "StackId": "APO_TWILIGHT_SHROUD"}, icon="Action_Paladin_AuraOfWarding")
G.status("APO_TWILIGHT_SHROUD_AURA", "Twilight Shroud", None, {
    "AuraRadius": "9", "AuraStatuses": "IF(Ally() or Self()):ApplyStatus(APO_TWILIGHT_SHROUD)", "StackId": "APO_TWILIGHT_SHROUD_AURA",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.passive("TwilightDomain_17_TwilightShroud", "Twilight Shroud",
          "You and your allies have Half Cover while in the sphere of your Twilight Sanctuary.", {
              "StatsFunctorContext": "OnStatusApplied;OnStatusRemoved",
              "Conditions": "StatusId('TWILIGHT_SANCTUARY_AURA')",
              "StatsFunctors": "IF(context.HasContextFlag(StatsFunctorContext.OnStatusApplied)):ApplyStatus(SELF,APO_TWILIGHT_SHROUD_AURA,100,10);IF(context.HasContextFlag(StatsFunctorContext.OnStatusRemoved)):RemoveStatus(SELF,APO_TWILIGHT_SHROUD_AURA)"},
          icon="Action_Paladin_AuraOfWarding")
node("c7da9e63-0991-4492-b966-26e8533866d1", "TwilightDomain", 17, "TwilightDomain_17_TwilightShroud")
G.passive("TempestDomain_17_Stormborn", "Stormborn", "You have a Fly Speed equal to your Speed (outdoors).",
          {"Boosts": "UnlockSpell(Projectile_Fly_Spell)"}, icon="PassiveFeature_WrathOfTheStorm_Lightning",
          comment="BG3 doesn't tell outdoors from indoors: the Fly Speed is always on.")
node("0630b55b-36f4-41d2-aacc-28e99d6ae252", "TempestDomain", 17, "TempestDomain_17_Stormborn")

# ---------------------------------------------------------------- Druid: Spores (TCoE), Dreams (XGE)
G.passive("Spores_14_FungalBody", "Fungal Body",
          "You can't be Blinded, Frightened or Poisoned (Deafened isn't a condition in the game), and a Critical Hit against you counts as a normal hit unless you're Incapacitated.", {
              "Boosts": "StatusImmunity(SG_Blinded);StatusImmunity(SG_Frightened);StatusImmunity(SG_Poisoned);"
                        "IF(not HasAnyStatus({'SG_Incapacitated'},{},{},context.Source)):CriticalHit(AttackTarget,Success,Never)",
              "BoostContext": "OnStatusApplied;OnStatusRemoved"}, icon="PassiveFeature_Generic_Magical")
node("288c9d1e-ab18-46dd-8fa3-d4fcfa44147a", "CircleOfTheSpores", 14, "Spores_14_FungalBody")
G.spell("Target_ApoWalkerInDreams_Scrying", "Walker in Dreams: Scrying", "Cast Scrying without a spell slot (once per Long Rest).", {
    "UseCosts": "ActionPoint:1;ApoWalkerInDreams:1"}, using="Target_Scrying")
G.passive("Dreams_14_WalkerInDreams", "Walker in Dreams",
          "Once per Long Rest you can cast Scrying without a spell slot. (Dream and the special Teleportation Circle aren't in the game.)", {
              "Boosts": "UnlockSpell(Target_ApoWalkerInDreams_Scrying);"
                        + limited("ApoWalkerInDreams", "Walker in Dreams", "Travel the dreamlands.", "Rest")}, icon="PassiveFeature_Generic_Magical")
node("aba806c9-d349-4c70-9a1a-0cb0ae699e3f", "CircleOfDreams", 14, "Dreams_14_WalkerInDreams")

# ---------------------------------------------------------------- Ranger: Swarmkeeper (TCoE)
G.status("APO_SWARMING_DISPERSAL", "Swarming Dispersal", "Teleport up to 30 feet (free).", {
    "Boosts": "UnlockSpell(Target_ApoSwarmingDispersal_Teleport)", "StackId": "APO_SWARMING_DISPERSAL"}, icon="PassiveFeature_Generic_Magical")
G.spell("Target_ApoSwarmingDispersal_Teleport", "Swarming Dispersal", "Teleport to an unoccupied space you can see within 30 feet.", {
    "TargetRadius": "9", "UseCosts": "", "SpellProperties": "GROUND:TeleportSource();GROUND:RemoveStatus(SELF,APO_SWARMING_DISPERSAL)",
    "RechargeValues": "", "RequirementConditions": "", "RequirementEvents": ""}, using="Target_MistyStep", icon="PassiveFeature_Generic_Magical")
G.interrupt("Interrupt_ApoSwarmingDispersal", "Swarming Dispersal",
            "When you take damage, use your Reaction to gain Resistance to it and vanish into your swarm: you can then teleport up to 30 feet.", {
                "InterruptContext": "OnPreDamage", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and HasDamageEffectFlag(DamageFlags.Hit)",
                "Properties": "ApplyStatus(OBSERVER_OBSERVER,UNCANNY_DODGE_REDUCE_DAMAGE,100,0);ApplyStatus(OBSERVER_OBSERVER,APO_SWARMING_DISPERSAL,100,1)",
                "Cost": "ReactionActionPoint:1;ApoSwarmingDispersal:1", "Stack": "ApoSwarmingDispersal", "InterruptDefaultValue": "Ask;Enabled"},
            icon="PassiveFeature_Generic_Magical")
G.passive("Swarmkeeper_15_SwarmingDispersal", "Swarming Dispersal",
          "When you take damage, you can use your Reaction to gain Resistance to that damage and teleport up to 30 feet. Uses: your Proficiency Bonus per Long Rest.", {
              "Boosts": "UnlockInterrupt(Interrupt_ApoSwarmingDispersal);ActionResource(ApoSwarmingDispersal,5,0);IF(CharacterLevelGreaterThan(16)):ActionResource(ApoSwarmingDispersal,1,0)"},
          icon="PassiveFeature_Generic_Magical")
G.resource("ApoSwarmingDispersal", 6, "Rest", "Swarming Dispersal", "Vanish into your swarm.")
node("54ad9a98-9656-4aa5-858e-b302f83c4577", "Swarmkeeper", 15, "Swarmkeeper_15_SwarmingDispersal")


# ---------------------------------------------------------------- Barbarian: Path of the Giant (Bigby Presents: Glory of the Giants)
GIANT = "bdd02775-b9ee-480c-a260-d844580453b4"
GIANT_RAGE = "(HasStatus('RAGE_GIANT',context.Source) or HasStatus('RAGE_GIANT_2',context.Source))"
for el in ("Acid", "Cold", "Fire", "Lightning", "Thunder"):
    G.status(f"APO_COLOSSUS_CLEAVER_{el.upper()}", "Demiurgic Colossus", f"Elemental Cleaver deals 2d6 {el} damage.", {
        "Boosts": f"IF(IsMeleeWeaponAttack() or IsRangedWeaponAttack()):DamageBonus(1d6,{el})", "StackId": "APO_COLOSSUS_CLEAVER",
        "StatusPropertyFlags": "DisableCombatlog"}, icon=icon_of("Shout_ElementalCleaver"))
G.passive("GiantPath_14_DemiurgicColossus", "Demiurgic Colossus",
          "While raging you grow to Huge, and your Elemental Cleaver's extra damage increases to 2d6. (Reach +10 feet and Mighty Impel on Large creatures aren't implemented.)", {
              "BoostContext": "OnStatusApplied;OnStatusRemoved",
              "Boosts": f"IF({GIANT_RAGE}):ObjectSize(+1);IF({GIANT_RAGE}):ScaleMultiplier(1.25)"},
          icon=icon_of("RageGiantUnlock"), comment="SubclassFeatures.lua adds the Cleaver's second d6 when you cast Elemental Cleaver.")
node(GIANT, "GiantPath", 14, "GiantPath_14_DemiurgicColossus")

# ---------------------------------------------------------------- Cleric: Nature Domain 17 Master of Nature (PHB 2014, as the base game)
G.status("APO_MASTER_OF_NATURE", "Commanded by Nature", "Under your command until the end of its next turn.", {
    "Boosts": "FactionOverride(Source)", "StackId": "APO_MASTER_OF_NATURE", "StatusPropertyFlags": "LoseControl",
    "StatusGroups": "SG_Charmed"}, icon=icon_of("Shout_CharmAnimalsAndPlants"),
    comment="The base game's Dominate Beast mechanism (FactionOverride + LoseControl), one turn at a time.")
G.spell("Shout_ApoMasterOfNature", "Master of Nature",
        "Command every creature charmed by your Charm Animals and Plants: you control each one on its next turn.", {
            "SpellType": "Shout", "AreaRadius": "18",
            "TargetConditions": "HasStatus('CHARM_ANIMALS_AND_PLANTS',context.Target,context.Source) and not Self()",
            "SpellProperties": "ApplyStatus(APO_MASTER_OF_NATURE,100,1)", "TooltipStatusApply": "ApplyStatus(APO_MASTER_OF_NATURE,100,1)",
            "UseCosts": "BonusActionPoint:1", "VerbalIntent": "Control"}, icon=icon_of("Shout_CharmAnimalsAndPlants"))
G.passive("NatureDomain_17_MasterOfNature", "Master of Nature",
          "As a Bonus Action, command the Beasts and Plants charmed by your Charm Animals and Plants: you control what each does on its next turn.",
          {"Boosts": "UnlockSpell(Shout_ApoMasterOfNature)"}, icon=icon_of("Shout_CharmAnimalsAndPlants"))
node("c668b65d-2848-4feb-981f-eb54cc5ceb15", "NatureDomain", 17, "NatureDomain_17_MasterOfNature")

# ---------------------------------------------------------------- Monk: Warrior of the Mystic Arts (UA 2026 Mystic Subclasses)
# The third-caster table past 12 (slots: L13 +2 level 3, L16 +1 level 3, L19 +1 level 4; prepared spells +1 at 13, 14,
# 16, 19, 20 - new picks from the Sorcerer level 3 / 4 lists, as dnd55e picks from the level 2 list at 7-12).
MYSTIC = "8514c075-f719-4540-a8c6-08b516a302d8"
SORC3, SORC4 = "dcbaf2ae-1f45-453e-ab83-cd154f8277a4", "5fe40622-1d3e-4cc1-8d89-e66fe51d8c5c"
G.passive("MysticArts_17_ImprovedMysticFightingStyle", "Improved Mystic Fighting Style",
          "When you cast a level 1 or 2 Sorcerer spell with your action on your turn, you can still make an attack as part of the Attack action (BG3's Improved War Magic).",
          {}, using="EldritchKnight_ImprovedWarMagic", icon=icon_of("EldritchKnight_ImprovedWarMagic"))
node(MYSTIC, "MysticArts", 13, boosts="ActionResource(SpellSlot,2,3)", selectors=f"SelectSpells({SORC3},1,1)")
node(MYSTIC, "MysticArts", 14, selectors=f"SelectSpells({SORC3},1,1)")
node(MYSTIC, "MysticArts", 15, selectors=f"SelectSpells({SORC3},0,1)")
node(MYSTIC, "MysticArts", 16, boosts="ActionResource(SpellSlot,1,3)", selectors=f"SelectSpells({SORC3},1,1)")
node(MYSTIC, "MysticArts", 17, "MysticArts_17_ImprovedMysticFightingStyle", selectors=f"SelectSpells({SORC3},0,1)")
node(MYSTIC, "MysticArts", 18, selectors=f"SelectSpells({SORC3},0,1)")
node(MYSTIC, "MysticArts", 19, boosts="ActionResource(SpellSlot,1,4)", selectors=f"SelectSpells({SORC4},1,1)")
node(MYSTIC, "MysticArts", 20, selectors=f"SelectSpells({SORC4},1,1)")

# ================================================================ dnd55e's third-party subclasses (sources: docs/SUBCLASS_SOURCING.md, 2026-10-03)
# ---------------------------------------------------------------- Barbarian: Shadow Gnawer 14 Corrosive Haze (Book of Ebon Tides, Open Design)
SHADOW_GNAWER = "636456e2-93bc-4567-aae5-0abb0aad450e"
G.status("APO_CORROSIVE_HAZE_SAVED", "Corrosive Haze", "Already tested against the haze this turn.", {
    "StackId": "APO_CORROSIVE_HAZE_SAVED", "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.status("APO_CORROSIVE_HAZE_NEAR", "Corrosive Haze", None, {
    "OnApplyConditions": "not HasStatus('APO_CORROSIVE_HAZE_SAVED') and not Tagged('OOZE')",
    "OnApplyRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC(10, context.Source, Ability.Constitution))",
    "OnApplySuccess": "ApplyStatus(BLINDED,100,1)", "OnApplyFunctors": "ApplyStatus(APO_CORROSIVE_HAZE_SAVED,100,1)",
    "StackId": "APO_CORROSIVE_HAZE_NEAR", "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"})
G.status("APO_CORROSIVE_HAZE", "Corrosive Haze",
         "While you rage, a hostile creature within 10 feet of you makes a Constitution saving throw (DC 8 + your Proficiency Bonus and Constitution modifier) or is Blinded until the start of its next turn.", {
             "AuraRadius": "3", "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_CORROSIVE_HAZE_NEAR,100,0)",
             "RemoveConditions": "not HasStatus('SG_Rage')", "RemoveEvents": "OnStatusRemoved", "StackId": "APO_CORROSIVE_HAZE",
             "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"}, icon=icon_of("Spell_Conjuration_FogCloud"))
G.passive("ShadowGnawer_14_CorrosiveHaze", "Corrosive Haze",
          "Your Shadow Smoke is more potent: while you rage, a hostile creature within 10 feet of you makes a Constitution saving throw (DC 8 + your Proficiency Bonus and Constitution modifier) or is Blinded until the start of its next turn, once per creature per turn. Oozes and other creatures that don't rely on eyesight are immune. (The aura is always on while you rage, not only while the Shadow Smoke is up.)", {
              "StatsFunctorContext": "OnStatusApplied", "Conditions": "HasStatus('SG_Rage', context.Source)",
              "StatsFunctors": "ApplyStatus(SELF,APO_CORROSIVE_HAZE,100,-1)"},
          icon=icon_of("Spell_Conjuration_FogCloud"))
node(SHADOW_GNAWER, "ShadowGnawer", 14, "ShadowGnawer_14_CorrosiveHaze")

# ---------------------------------------------------------------- Cleric: Shadow Domain 17 Army of Shadow (Book of Ebon Tides, Open Design)
SHADOW_DOMAIN = "976b6b96-3c5a-4d06-86ee-c2a809bdb3e8"
G.spell("Target_ApoShadowGrasp_Army", "Shadow Grasp: Army of Shadow",
        "Use Shadow Grasp on up to 6 creatures (your Proficiency Bonus at level 17) with a single use of Channel Divinity.", {
            "AmountOfTargets": "6", "DescriptionParams": "Distance(9);6"}, using="Target_ShadowGrasp", icon=icon_of("Target_ShadowGrasp"))
G.passive("ShadowDomain_17_ArmyOfShadow", "Army of Shadow",
          "When you use Shadow Grasp, you can affect a number of creatures equal to your Proficiency Bonus (6).",
          {"Boosts": "UnlockSpell(Target_ApoShadowGrasp_Army)"}, icon=icon_of("Target_ShadowGrasp"))
node(SHADOW_DOMAIN, "ShadowDomain", 17, "ShadowDomain_17_ArmyOfShadow")

# ---------------------------------------------------------------- Cleric: Mind Domain 17 Bend Reality (Exploring Eberron, Keith Baker)
MIND_DOMAIN = "c20c34ee-5e13-4755-9116-a350f50454e7"
G.interrupt("Interrupt_ApoBendReality", "Bend Reality",
            "When an ally fails a saving throw, replace the roll with a 20.", {
                "InterruptContext": "OnPostRoll", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
                "Conditions": "not Dead(context.Observer) and HasInterruptedSavingThrow() and Ally(context.Target, context.Observer) and not AnyEntityIsItem() and IsSetInterruptInteresting(20)",
                "Properties": "SetRoll(20)", "Cost": "ApoBendReality:1", "InterruptDefaultValue": "Ask;Enabled"},
            icon=icon_of("Interrupt_Portent_20", "PassiveFeature_Portent_20"))
G.passive("MindDomain_17_BendReality", "Bend Reality",
          "When you see an ally fail a saving throw, you can use your Reaction to replace the roll with a 20. Once per Short or Long Rest.",
          {"Boosts": "UnlockInterrupt(Interrupt_ApoBendReality);" + limited("ApoBendReality", "Bend Reality", "Replace an ally's failed saving throw with a 20.", "ShortRest")},
          icon=icon_of("Interrupt_Portent_20", "PassiveFeature_Portent_20"))
node(MIND_DOMAIN, "MindDomain", 17, "MindDomain_17_BendReality")

# ---------------------------------------------------------------- Rogue: Highway Rider 13 True Grit (Grim Hollow Player's Guide)
HIGHWAY = "8e20bc2e-8a65-472d-8e14-66d91edfcdd3"
G.passive("HighwayRider_13_TrueGrit", "True Grit",
          "You gain proficiency in Constitution saving throws. (The Evasion-style rule for Constitution saves that deal half damage isn't implemented: the engine's Evasion is Dexterity-only.)",
          {"Boosts": "ProficiencyBonus(SavingThrow,Constitution)"}, icon=icon_of("Evasion", "PassiveFeature_Evasion"))
node(HIGHWAY, "HighwayRider", 13, "HighwayRider_13_TrueGrit")

# Desperado (17): reduced to 0 HP, spend your Reaction for one Hair Trigger action before you fall. Built like Persistent Hunt:
# a conditional DownedStatus stand-in holds you at 1 HP, SubclassFeatures.lua fires the free attack and then drops you.
G.status("APO_DESPERADO_SPENT", "Desperado", "You used your Reaction on Desperado.", {
    "StackId": "APO_DESPERADO_SPENT", "StatusPropertyFlags": "DisableOverhead"})
G.status("APO_DESPERADO_DOWNED", "Desperado", None, {
    "OnApplyFunctors": "ApplyStatus(APO_DESPERADO_SPENT,100,1);RegainHitPoints(1,Guaranteed)"},
    using="RELENTLESS_ENDURANCE_DOWNED")
G.status("APO_DESPERADO_ADVANTAGE", "Desperado", "Advantage on your Hair Trigger attack.", {
    "Boosts": "Advantage(AttackRoll)", "StackId": "APO_DESPERADO_ADVANTAGE", "StatusPropertyFlags": "DisableOverhead"})
G.passive("HighwayRider_17_Desperado", "Desperado",
          "When you are reduced to 0 Hit Points, you can use your Reaction to take a Hair Trigger action immediately before you fall: a free weapon attack with Advantage against the nearest hostile creature in reach. (The other Hair Trigger options - moving, Dodge, using an object - aren't offered.)", {
              "Boosts": "IF(not HasStatus('APO_DESPERADO_SPENT',context.Source) and HasActionResource('ReactionActionPoint',1,0,false,false,context.Source)):DownedStatus(APO_DESPERADO_DOWNED,7)"},
          icon=icon_of("Projectile_MainHandAttack_Firearm"), comment="SubclassFeatures.lua (Desperado).")
node(HIGHWAY, "HighwayRider", 17, "HighwayRider_17_Desperado")

# ---------------------------------------------------------------- Rogue: Arachnoid Stalker 13 Web Walker (Valda's Spire of Secrets, 2024 version)
ARACHNOID = "d69b2fcd-c3e9-40c7-b857-23c9c5dcd668"
G.passive("ArachnoidStalker_13_WebWalker", "Web Walker",
          "Webs never hinder you, and your Web charges are fully restored at the start of each of your turns and on every rest (Web at will).", {
              "Boosts": "StatusImmunity(WEB)", "StatsFunctorContext": "OnTurn;OnShortRest;OnLongRest",
              "StatsFunctors": "RestoreResource(Web_ArachnoidStalker,2,0)"},
          icon=icon_of("Spell_Conjuration_Web"))
node(ARACHNOID, "ArachnoidStalker", 13, "ArachnoidStalker_13_WebWalker")

# ================================================================ References/Subclasses/missing_subclass_ref.txt (2026-10-04)
# Druid: Circle of the Unbroken 14 Nature Armor (Griffon's Saddlebag, Book One). Its Shillelagh d12 at 14 is already
# dnd55e's Shillelagh scaling (d12 from character level 10), so only Nature Armor is new.
UNBROKEN = "c52f35d8-1fb6-483a-957a-372db8ce01db"
G.passive("Unbroken_14_NatureArmor", "Nature Armor",
          "At the start of each of your turns, you gain Hit Points equal to half your Druid level + your Wisdom modifier. (The Shillelagh d12 this level also grants is already in dnd55e's Shillelagh.)",
          {"StatsFunctorContext": "OnTurn", "StatsFunctors": "RegainHitPoints(ClassLevel(Druid)/2+WisdomModifier)"},
          icon=icon_of("Spell_Transmutation_Barkskin", "PassiveFeature_Generic_Magical"))
node(UNBROKEN, "CircleOfTheUnbroken", 14, "Unbroken_14_NatureArmor")

# Barbarian: Path of the Fractured 14 Better Half (Grim Hollow). SubclassFeatures.lua: half-max temp HP and the Rage swap.
FRACTURED = "c6417c1d-3d25-48f4-86ab-0a1d4d69be6f"
G.status("APO_BETTER_HALF_DOWNED", "Better Half", None, {"OnApplyFunctors": "RegainHitPoints(1,Guaranteed)"},
         using="RELENTLESS_ENDURANCE_DOWNED")
G.passive("Fractured_14_BetterHalf", "Better Half",
          "Once per Long Rest, when you drop to 0 Hit Points you instead drop to 1 Hit Point and gain Temporary Hit Points equal to half your Hit Point maximum. You also swap whether you are raging.", {
              "Boosts": "IF(HasActionResource('ApoBetterHalf',1,0,false,false,context.Source)):DownedStatus(APO_BETTER_HALF_DOWNED,7);"
                        + limited("ApoBetterHalf", "Better Half", "Drop to 1 Hit Point instead of 0.", "Rest")},
          icon=icon_of("Action_Barbarian_Rage", "PassiveFeature_Generic_Magical"), comment="SubclassFeatures.lua (BetterHalf).")
node(FRACTURED, "Fractured", 14, "Fractured_14_BetterHalf")

# Cleric: Astral Domain 17 Supreme Switching (Griffon's Saddlebag, Book One): Spatial Exchange against a hostile creature.
ASTRAL = "09684867-c032-4676-a80b-99a317d39fad"
G.spell("Target_ApoSupremeSwitching", "Supreme Switching",
        "Target a hostile creature with Spatial Exchange: it makes a Charisma saving throw against your spell save DC. On a failure it switches places with you; on a success neither of you moves. (Casting a touch spell as part of the swap isn't implemented.)", {
            "SpellRoll": "not SavingThrow(Ability.Charisma,SourceSpellDC())", "SpellSuccess": "SwapPlaces()", "SpellProperties": "",
            "TargetConditions": "Enemy() and Character() and not Dead()", "TooltipAttackSave": "Charisma",
            "UseCosts": "BonusActionPoint:1;ChannelDivinity:1"}, using="Target_SpatialExchange", icon="Action_BenignTransposition_Swap")
G.passive("Astral_17_SupremeSwitching", "Supreme Switching",
          "Your Spatial Exchange can target a hostile creature: it makes a Charisma saving throw against your spell save DC and, on a failure, switches places with you.",
          {"Boosts": "UnlockSpell(Target_ApoSupremeSwitching)"}, icon="Action_BenignTransposition_Swap")
node(ASTRAL, "AstralDomain", 17, "Astral_17_SupremeSwitching")

# Fighter: Viking 15 Marauder's Reprisal / 18 Unstoppable Assault (Northlands Worldbook)
VIKING = "241461f3-7cb5-4fc3-abdf-d56b869e3757"
MARAUDER = "ApoMaraudersReprisal"
G.status("APO_MARAUDER_BLOODIED", "Marauder's Reprisal", "You used Marauder's Reprisal for becoming Bloodied.", {
    "RemoveEvents": "OnHeal", "RemoveConditions": "not HasHPPercentageLessThan(50,context.Source)", "StackId": "APO_MARAUDER_BLOODIED",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.status("APO_MARAUDER_THP", "Marauder's Reprisal", "Temporary Hit Points equal to half your Fighter level.", {
    "Boosts": "TemporaryHP(ClassLevel(Fighter)/2)", "RemoveConditions": "not HasTemporaryHP()", "RemoveEvents": "OnDamage",
    "StackId": "APO_MARAUDER_THP", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"})
G.spell("Target_ApoMaraudersReprisal", "Marauder's Reprisal",
        "Make an Opportunity Attack against the creature that hurt you. On a hit, it deals double weapon dice damage and you gain Temporary Hit Points equal to half your Fighter level.", {
            "SpellType": "Target", "TargetRadius": "MeleeMainWeaponRange", "TargetConditions": "Character() and not Self() and not Dead()",
            "SpellRoll": "Attack(AttackType.MeleeWeaponAttack)",
            "SpellSuccess": "DealDamage(MainMeleeWeapon,MainMeleeWeaponDamageType);DealDamage(MainMeleeWeapon,MainMeleeWeaponDamageType);ApplyStatus(SELF,APO_MARAUDER_THP,100,-1);ExecuteWeaponFunctors(MainHand)",
            "TooltipDamageList": "DealDamage(MainMeleeWeapon,MainMeleeWeaponDamageType)", "UseCosts": f"{MARAUDER}:1",
            "SpellFlags": "IsHarmful;IsMelee", "VerbalIntent": "Damage"}, using="Target_MainHandAttack", icon="Action_Barbarian_RecklessAttack")
G.interrupt("Interrupt_ApoMaraudersReprisal", "Marauder's Reprisal",
            "When you first become Bloodied or a creature scores a Critical Hit against you, make an Opportunity Attack against it with double weapon dice and gain Temporary Hit Points. (Strikes the creature that hit you, not the nearest enemy.)", {
                "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                "Conditions": f"IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and Enemy(context.Source,context.Observer) and IsHit() and not AnyEntityIsItem() and HasActionResource('{MARAUDER}',1,0,false,false,context.Observer) and (IsCritical() or (HasHPPercentageLessThan(50,context.Observer) and not HasStatus('APO_MARAUDER_BLOODIED',context.Observer)))",
                "Properties": "UseSpell(SWAP,Target_ApoMaraudersReprisal,true,true,true);IF(not IsCritical()):ApplyStatus(OBSERVER_OBSERVER,APO_MARAUDER_BLOODIED,100,-1)",
                "Cost": "ReactionActionPoint:1", "Stack": "ApoMaraudersReprisal", "InterruptDefaultValue": "Ask;Enabled"},
            icon="Action_Barbarian_RecklessAttack")
G.passive("Viking_15_MaraudersReprisal", "Marauder's Reprisal",
          "When you first become Bloodied or a creature scores a Critical Hit against you, you can use your Reaction to make an Opportunity Attack against it. On a hit it deals double weapon dice damage and you gain Temporary Hit Points equal to half your Fighter level. Uses equal to your Proficiency Bonus per Long Rest.", {
              "Boosts": "UnlockInterrupt(Interrupt_ApoMaraudersReprisal);" + limited(MARAUDER, "Marauder's Reprisal", "Reprisal Opportunity Attacks.", "Rest", 5)
                        + f";IF(CharacterLevelGreaterThan(16)):ActionResource({MARAUDER},1,0)"},
          icon="Action_Barbarian_RecklessAttack")
node(VIKING, "Viking", 15, "Viking_15_MaraudersReprisal")

UNSTOPPABLE_HIT = "IF(IsMeleeWeaponAttack()):DamageBonus(MainMeleeWeapon)"
G.status("APO_UNSTOPPABLE_ASSAULT", "Unstoppable Assault",
         "This turn you make additional attacks equal to half your Proficiency Bonus; your weapon attacks deal double weapon dice and a creature you hit makes a Strength saving throw (DC 8 + Proficiency Bonus + Strength modifier) or is shoved 10 feet.", {
             "Boosts": UNSTOPPABLE_HIT, "Passives": "ExtraAttack_2", "StackId": "APO_UNSTOPPABLE_ASSAULT", "RemoveEvents": "OnTurn"},
         icon="Action_Barbarian_RecklessAttack")
G.passive("Viking_18_UnstoppableAssault", "Unstoppable Assault",
          "As an action, once per Long Rest, spin your weapon in a furious arc: until the end of your turn you make additional attacks equal to half your Proficiency Bonus, your weapon attacks deal double weapon dice, and creatures you hit make a Strength saving throw (DC 8 + Proficiency Bonus + Strength modifier) or are shoved 10 feet.", {
              "Boosts": once("Shout_ApoUnstoppableAssault", "APO_UNSTOPPABLE_ASSAULT", "Unstoppable Assault", "Spin your weapon in a furious arc.", 1,
                             "ActionPoint", "ApoUnstoppableAssault", icon="Action_Barbarian_RecklessAttack"),
              "StatsFunctorContext": "OnDamage",
              "Conditions": "HasStatus('APO_UNSTOPPABLE_ASSAULT',context.Source) and IsMeleeWeaponAttack() and IsHit()",
              "StatsFunctors": "ApplyStatus(APO_UNSTOPPABLE_SHOVE,100,0)"},
          icon="Action_Barbarian_RecklessAttack")
G.status("APO_UNSTOPPABLE_SHOVE", "Unstoppable Assault", "Pushed 10 feet.", {
    "OnApplyRoll": "not SavingThrow(Ability.Strength,SourceSpellDC(8,context.Source,Ability.Strength))",
    "OnApplySuccess": "Force(-3,OriginToEntity,Neutral,false,true)", "StackId": "APO_UNSTOPPABLE_SHOVE",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
node(VIKING, "Viking", 18, "Viking_18_UnstoppableAssault")

# Rogue: Blade of Radiance 13 Saintly Revelations / 17 Final Judgement (Steinhardt's Guide to the Eldritch Hunt)
BLADE = "e77b882d-60d9-4f2e-81bb-03f795327312"
CLERIC_CANTRIPS = "2f43a103-5bf1-4534-b14f-663decc0c525"
FINAL = "BladeOfRadiance_17_FinalJudgement"
REVELATIONS = (("Target_ProtectionFromEvilAndGood", "Protection from Evil and Good", "Spell_Abjuration_ProtectionFromEvilAndGood"),
               ("Target_Heroism", "Heroism", "Spell_Enchantment_Heroism"), ("Target_ShieldOfFaith", "Shield of Faith", "Spell_Abjuration_ShieldOfFaith"))
for base, title, icon in REVELATIONS:
    for suffix, flags in (("", "IsConcentration;IsSpell"), ("_NoConc", "IsSpell")):
        G.spell(f"{base}_ApoRevelation{suffix}", title + (" (no concentration)" if suffix else ""),
                f"Cast {title} on yourself at will, with no components; Wisdom is your spellcasting modifier."
                + (" You needn't concentrate on it, but only one Saintly Revelation can be active." if suffix else ""),
                {"UseCosts": "BonusActionPoint:1" if base == "Target_ShieldOfFaith" else "ActionPoint:1", "TargetRadius": "1.5" if base != "Target_ShieldOfFaith" else "18",
                 "TargetConditions": "Self()", "SpellFlags": flags, "MemoryCost": "0", "Level": "0"}, using=base, icon=icon)
G.passive("BladeOfRadiance_13_SaintlyRevelations", "Saintly Revelations",
          "You learn two cleric cantrips of your choice. You can cast Protection from Evil and Good, Heroism and Shield of Faith at will, with no components, only on yourself; Wisdom is your spellcasting modifier. (At 17th level you needn't concentrate on them.)", {
              "Boosts": "".join(f"IF(not HasPassive('{FINAL}',context.Source)):UnlockSpell({b}_ApoRevelation);" for b, _, _ in REVELATIONS)},
          icon="Spell_Abjuration_ShieldOfFaith")
node(BLADE, "BladeOfRadiance", 13, "BladeOfRadiance_13_SaintlyRevelations",
     selectors=f"SelectSpells({CLERIC_CANTRIPS},2,0,SaintlyRevelationsCantrips)")

G.status("APO_FINAL_JUDGEMENT", "Final Judgement",
         "Your sanctified blade sheds bright light in a 30-foot radius and dim light 30 feet further, and your melee weapon attacks deal an extra 2d4 Radiant damage.", {
             "Boosts": "GameplayLight(18,false,0.1);IF(IsMeleeWeaponAttack()):DamageBonus(2d4,Radiant)", "StackId": "APO_FINAL_JUDGEMENT",
             "StatusGroups": "SG_Light"}, icon="Action_Paladin_SacredWeapon")
G.spell("Shout_ApoFinalJudgementOn", "Final Judgement: Light the Blade",
        "Speak the command word (no action): your sanctified blade blazes and your melee attacks deal an extra 2d4 Radiant damage.", {
            "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "ApplyStatus(APO_FINAL_JUDGEMENT,100,-1)",
            "TooltipStatusApply": "ApplyStatus(APO_FINAL_JUDGEMENT,100,-1)", "UseCosts": "",
            "RequirementConditions": "not HasStatus('APO_FINAL_JUDGEMENT',context.Source)", "VerbalIntent": "Buff"}, icon="Action_Paladin_SacredWeapon")
G.spell("Shout_ApoFinalJudgementOff", "Final Judgement: Douse the Blade", "Speak the command word again: the light and the extra damage end.", {
    "SpellType": "Shout", "TargetConditions": "Self()", "SpellProperties": "RemoveStatus(APO_FINAL_JUDGEMENT)", "UseCosts": "",
    "RequirementConditions": "HasStatus('APO_FINAL_JUDGEMENT',context.Source)", "VerbalIntent": "Buff"}, icon="Action_Paladin_SacredWeapon")
GUARD_TEXT = ("Cast Spirit Guardians (Radiant) with no components. Once per Long Rest, or again for three Divine points. "
              "(Creatures in the area count as within 5 feet of an enemy for your Sneak Attack isn't implemented.)")
G.spell("Shout_ApoFinalJudgementGuardians", "Final Judgement: Spirit Guardians", GUARD_TEXT, {
    "UseCosts": "ActionPoint:1;ApoFinalJudgementGuardians:1", "SpellContainerID": None, "SpellFlags": "IsConcentration;IsSpell;IsHarmful"},
    using="Shout_SpiritGuardians_Radiant", icon="Spell_Conjuration_SpiritGuardians")
G.spell("Shout_ApoFinalJudgementGuardians_DivinePoints", "Final Judgement: Spirit Guardians (3 Divine points)", GUARD_TEXT, {
    "UseCosts": "ActionPoint:1;DivinePoint:3", "SpellContainerID": None, "SpellFlags": "IsConcentration;IsSpell;IsHarmful",
    "RequirementConditions": "not HasActionResource('ApoFinalJudgementGuardians',1,0,false,false,context.Source)"},
    using="Shout_SpiritGuardians_Radiant", icon="Spell_Conjuration_SpiritGuardians")
G.passive(FINAL, "Final Judgement",
          "Your sanctified blade can blaze with holy light (30-foot bright, 30 feet dim) and deal an extra 2d4 Radiant damage with melee attacks. Once per Long Rest (or for three Divine points) you can cast Spirit Guardians with no components. You no longer concentrate on Saintly Revelations, though only one can be active.", {
              "Boosts": "UnlockSpell(Shout_ApoFinalJudgementOn);UnlockSpell(Shout_ApoFinalJudgementOff);UnlockSpell(Shout_ApoFinalJudgementGuardians);UnlockSpell(Shout_ApoFinalJudgementGuardians_DivinePoints);"
                        + "".join(f"UnlockSpell({b}_ApoRevelation_NoConc);" for b, _, _ in REVELATIONS)
                        + limited("ApoFinalJudgementGuardians", "Final Judgement", "Cast Spirit Guardians free.", "Rest")},
          icon="Action_Paladin_SacredWeapon")
node(BLADE, "BladeOfRadiance", 17, FINAL)

# Bard: College of Choreography 14 (The Griffon's Saddlebag: Book One, "College of Dance": Fast Movement +5 ft, Entrancing
# Movement adds Irresistible Dance, Endless Dance). References/Subclasses text: the page the user photographed 2026-10-04.
CHOREO = "6ecf4e50-6458-4f11-b525-644171eeb5b7"
G.passive("Choreography_14_FastMovement", "Fast Movement",
          "At 14th level your walking speed increases by another 5 feet.", {"Boosts": "ActionResource(Movement,1.5,0)"},
          icon="Spell_Transmutation_Longstrider")
G.spell("Target_IrresistibleDance_Choreography", "Entrancing Movement: Irresistible Dance",
        "Cast Otto's Irresistible Dance without expending a spell slot, requiring only somatic components. You can't do so again until you finish a Long Rest.", {
            "Cooldown": "OncePerRest", "UseCosts": "ActionPoint:1", "SpellFlags": "HasSomaticComponent;HasHighGroundRangeExtension;IsConcentration;IsSpell;CannotTargetItems;CannotTargetTerrain;IsHarmful",
            "MemoryCost": "0"}, using="Target_IrresistibleDance", icon="Spell_OttosIrresistibleDance")
G.passive("Choreography_14_EntrancingMovement", "Entrancing Movement: Irresistible Dance",
          "You can cast Otto's Irresistible Dance once per Long Rest without a spell slot, requiring only somatic components.",
          {"Boosts": "UnlockSpell(Target_IrresistibleDance_Choreography)"}, icon="Spell_OttosIrresistibleDance")
G.status("APO_ENDLESS_DANCE_ACTION", "Endless Dance", "You can use your Reaction to make one weapon attack.", {
    "TickType": "EndTurn", "Boosts": "UnlockSpell(Target_ApoEndlessDanceStrike)",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.spell("Target_ApoEndlessDanceStrike", "Endless Dance: Strike", "Use your Reaction to make one weapon attack.",
        {"UseCosts": "ReactionActionPoint:1", "SpellFlags": "IsHarmful;IsMelee;Temporary"}, using="Target_MainHandAttack")
G.spell("Target_ApoInspirationalDance_Endless", "Inspirational Dance (Endless Dance)",
        "Expend a use of Bardic Inspiration as a Bonus Action: another creature gains Temporary Hit Points equal to the Bardic Inspiration die + your Charisma modifier and can use its Reaction to move, Disengage, Dodge or make one weapon attack. You also take the Dodge action as part of this bonus action.", {
            "SpellProperties": "ApplyStatus(INSPIRATIONAL_DANCE,100,-1);ApplyStatus(APO_ENDLESS_DANCE_ACTION,100,1);ApplyStatus(SELF,DODGE,100,1)",
            "TooltipStatusApply": "ApplyStatus(INSPIRATIONAL_DANCE,100,-1);ApplyStatus(DODGE,100,1)"},
        using="Target_InspirationalDance", icon="Choreography_3_InspirationalDance")
G.spell("Shout_ApoEndlessDodge", "Endless Dance: Dodge", "Take the Dodge action as a Bonus Action.",
        {"UseCosts": "BonusActionPoint:1"}, using="Shout_Dodge", icon="Action_Dodge")
G.passive("Choreography_14_EndlessDance", "Endless Dance",
          "Your Inspirational Dance can also let the creature use its Reaction to make one weapon attack, and you can take the Dodge action as a Bonus Action, or as part of the Bonus Action you spend on a Bardic Inspiration die. (Inspirational Dance (Endless Dance) is the upgraded version of Inspirational Dance.)",
          {"Boosts": "UnlockSpell(Target_ApoInspirationalDance_Endless);UnlockSpell(Shout_ApoEndlessDodge)"}, icon="Choreography_3_InspirationalDance")
node(CHOREO, "ChoreographyCollege", 14, "Choreography_14_FastMovement", "Choreography_14_EntrancingMovement", "Choreography_14_EndlessDance")

# Druid: Circle of Dragons 14 Heart of a Dragon (The Griffon's Saddlebag: Book Two; References/Subclasses/griffons_saddlebag_circle_of_dragons.txt).
# dnd55e's Dragon Shape is a polymorph (DRAGONSHAPE_10 at 10+); the 5d6 breath is the DragonShapeBreath level map (gen_levelmaps.py).
# Not built: the 30-foot breath cone, the Fly speed of exactly 40 (+10 feet of Movement stands in) and the Large form.
DRAGONS = "7a3b896a-3acd-45a3-8c79-24f5aaa4034f"
G.spell("Zone_BreathWeapon_DragonShape_Heart", "Heart of a Dragon: Breath Weapon",
        "Exhale your dragon breath without taking dragon shape. Once per Long Rest.", {
            "Cooldown": "OncePerRest"}, using="Zone_BreathWeapon_DragonShape", icon="Action_Dragonborn_BreathWeapon_FireCone")
G.status("APO_DRAGONSHAPE_HEART", "Heart of a Dragon",
         "In dragon shape: AC 16 + Dexterity (maximum 2), 10 more feet of movement and three attacks.", {
             "Boosts": "ACOverrideFormula(16,true,Wisdom);ActionResource(Movement,3,0)", "Passives": "ExtraAttack_2",
             "StackId": "APO_DRAGONSHAPE_HEART", "RemoveConditions": "not HasStatus('DRAGONSHAPE_10',context.Source)",
             "RemoveEvents": "OnStatusRemoved;OnTurn", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"},
         icon="Action_EndGameAlly_ZhentarimUnits")
G.passive("Dragons_14_HeartOfADragon", "Heart of a Dragon",
          "You can use your breath weapon without dragon shape (once per Long Rest). In dragon shape your AC is 16 + Dexterity (maximum 2), you move 10 feet further and you make three attacks when you take the Attack action.", {
              "Boosts": "UnlockSpell(Zone_BreathWeapon_DragonShape_Heart)", "StatsFunctorContext": "OnStatusApplied",
              "Conditions": "StatusId('DRAGONSHAPE_10')", "StatsFunctors": "ApplyStatus(SELF,APO_DRAGONSHAPE_HEART,100,-1)"},
          icon="Action_EndGameAlly_ZhentarimUnits")
node(DRAGONS, "CircleOfDragons", 14, "Dragons_14_HeartOfADragon")

# Sorcerer: Heroic Sorcery 14 Sorcerous Kindling / 18 Heroic Legacy (Mage Hand Press, "Reincarnated Hero"; page photographed by the
# user 2026-10-04). dnd55e kept the spell list but reworked level 6 (Mystical Maneuvers -> Extra Attack / War Magic).
HEROIC = "1d22072e-d314-4520-9446-d656210ecbdf"
G.status("APO_KINDLING_USED", "Sorcerous Kindling", "You regained Sorcery Points from Sorcerous Kindling this turn.", {
    "StackId": "APO_KINDLING_USED", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.passive("HeroicSorcery_14_SorcerousKindling", "Sorcerous Kindling",
          "Once per turn, when you score a Critical Hit with a weapon attack against a hostile creature or reduce a hostile creature to 0 Hit Points with a weapon attack, you regain 2 Sorcery Points.", {
              "StatsFunctorContext": "OnDamage",
              "Conditions": "IsWeaponAttack() and Enemy() and Character() and (HasDamageEffectFlag(DamageFlags.Critical) or HasHPLessThan(1)) and not HasStatus('APO_KINDLING_USED',context.Source)",
              "StatsFunctors": "RestoreResource(SELF,SorceryPoint,2,0);ApplyStatus(SELF,APO_KINDLING_USED,100,1)"},
          icon="PassiveFeature_ExtraAttack")
node(HEROIC, "HeroicSorcery", 14, "HeroicSorcery_14_SorcerousKindling")

G.status("APO_HEROIC_LEGACY_TRIGGER", "Heroic Legacy", "SubclassFeatures.lua gives back the damage above 20.", {
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.status("APO_HEROIC_LEGACY_ADVANTAGE", "Heroic Legacy", "Advantage on attack rolls, ability checks and saving throws until the end of your next turn.", {
    "Boosts": "Advantage(AttackRoll);Advantage(AllAbilities);Advantage(AllSavingThrows)", "StackId": "APO_HEROIC_LEGACY_ADVANTAGE"},
    icon="PassiveFeature_ExtraAttack")
G.interrupt("Interrupt_ApoHeroicLegacy", "Heroic Legacy",
            "When you would take more than 20 damage, use your Reaction to reduce the damage to 20. You then have Advantage on attack rolls, ability checks and saving throws until the end of your next turn. (The excess damage is given back right after the hit, so a blow that would drop you to 0 isn't prevented.)", {
                "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and Enemy(context.Source,context.Observer) and HasDamageEffectFlag(DamageFlags.Hit) and not AnyEntityIsItem() and TotalDamageDoneGreaterThan(20)",
                "Properties": "ApplyStatus(OBSERVER_OBSERVER,APO_HEROIC_LEGACY_TRIGGER,100,0);ApplyStatus(OBSERVER_OBSERVER,APO_HEROIC_LEGACY_ADVANTAGE,100,2)",
                "Cost": "ReactionActionPoint:1", "InterruptDefaultValue": "Ask;Enabled"}, icon="PassiveFeature_ExtraAttack")
G.passive("HeroicSorcery_18_HeroicLegacy", "Heroic Legacy",
          "When you would take more than 20 damage, you can use your Reaction to reduce it to 20. You then have Advantage on attack rolls, ability checks and saving throws until the end of your next turn.",
          {"Boosts": "UnlockInterrupt(Interrupt_ApoHeroicLegacy)"}, icon="PassiveFeature_ExtraAttack", comment="SubclassFeatures.lua (HeroicLegacy).")
node(HEROIC, "HeroicSorcery", 18, "HeroicSorcery_18_HeroicLegacy")

# Sorcerer: Frost Sorcery 14 Flash Freeze / 18 Frozen Soul ("Frost Magic", The Griffon's Saddlebag: Book One, p.167; page photographed by the
# user 2026-10-04). Not built: Flash Freeze's no-Opportunity-Attacks-on-ice movement, the five contiguous ice spaces (one ice patch
# under the attacker instead) and Wall of Ice panels that needn't touch.
FROST = "1ee59b30-e015-45f2-8a93-9ca4c4ff2bc4"
G.spell("Target_ApoFlashFreeze", "Flash Freeze",
        "Release a blast of freezing cold at the creature that hit you, dealing Cold damage equal to half your Sorcerer level + your Charisma modifier, and turn the ground there to ice.", {
            "SpellType": "Target", "TargetRadius": "3", "TargetConditions": "Character() and not Self() and not Dead()",
            "SpellProperties": "DealDamage(ClassLevel(Sorcerer)/2+CharismaModifier,Cold,Magical);GROUND:CreateSurface(2,,WaterFrozen)",
            "TooltipDamageList": "DealDamage(ClassLevel(Sorcerer)/2+CharismaModifier,Cold)", "UseCosts": "", "SpellFlags": "IsHarmful",
            "VerbalIntent": "Damage"}, icon="Surface_Ice")
G.interrupt("Interrupt_ApoFlashFreeze", "Flash Freeze",
            "When a creature within 5 feet of you hits you with an attack, use your Reaction to release a blast of freezing cold: Cold damage equal to half your Sorcerer level + your Charisma modifier, and the ground there turns to ice.", {
                "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and Enemy(context.Source,context.Observer) and IsHit() and IsMeleeAttack() and not AnyEntityIsItem()",
                "Properties": "UseSpell(SWAP,Target_ApoFlashFreeze,true,true,true)", "Cost": "ReactionActionPoint:1",
                "InterruptDefaultValue": "Ask;Enabled"}, icon="Surface_Ice")
G.passive("FrostSorcery_14_FlashFreeze", "Flash Freeze",
          "When a creature within 5 feet of you hits you with an attack, you can use your Reaction to release a blast of freezing cold, dealing Cold damage equal to half your Sorcerer level + your Charisma modifier to it, and turning the ground there to ice.",
          {"Boosts": "UnlockInterrupt(Interrupt_ApoFlashFreeze)"}, icon="Surface_Ice")
node(FROST, "FrostSorcery", 14, "FrostSorcery_14_FlashFreeze")

G.spell("Wall_WallOfIce_ApoFrozenSoul", "Frozen Soul: Wall of Ice",
        "Cast Wall of Ice without expending a spell slot. You can't do so again until you finish a Long Rest.", {
            "Cooldown": "OncePerRest", "UseCosts": "ActionPoint:1", "MemoryCost": "0"}, using="Wall_WallOfIce", icon="Spell_Evocation_WallOfIce")
G.passive("FrostSorcery_18_FrozenSoul", "Frozen Soul",
          "You are immune to Cold damage and resistant to Fire damage. You can cast Wall of Ice once per Long Rest without expending a spell slot (it doesn't count against your spells known).",
          {"Boosts": "Resistance(Cold,Immune);Resistance(Fire,Resistant);UnlockSpell(Wall_WallOfIce_ApoFrozenSoul)"}, icon="GenericIcon_DamageType_Cold")
node(FROST, "FrostSorcery", 18, "FrostSorcery_18_FrozenSoul")

# Rogue: Arachnoid Stalker 17 Paralytic Venom isn't added: dnd55e's level 9 Paralytic Venom already paralyses on a
# Constitution save (Hold Monster), so a second copy at 17 would duplicate it.

# ---------------------------------------------------------------- Fighter: Eldritch Knight, Rogue: Arcane Trickster (third casters)
# Their slots and prepared spells stopped at 12: level 13 +2 level 3 slots, 16 +1 level 3, 19 +1 level 4; a prepared
# spell more at 13, 14, 16, 19, 20 (2024 table; dnd55e's selector pattern, Wizard level 3 / 4 lists).
WIZ3, WIZ4 = "22755771-ca11-49f4-b772-13d8b8fecd93", "820b1220-0385-426d-ae15-458dc8a6f5c0"
EXISTING = {}  # existing Apotheosis node UUID -> its full attributes after the patch
for table, name, tag, existing in (
        ("2db3f02e-dfa9-4235-b9bd-28a89bf41435", "EldritchKnight", "EldritchKnightAbjEvo",
         {15: ("07070707-0707-0707-0707-070707070702", "ArcaneCharge"), 18: ("07070707-0707-0707-0707-070707070703", "EldritchKnight_ImprovedWarMagic")}),
        ("7205dbe2-5eef-4cd6-ad7f-45b3dc254f78", "ArcaneTrickster", "ArcaneTricksterIlluEnch",
         {13: ("01010101-0101-0101-0101-010101010102", "ArcaneTrickster_VersatileTrickster"), 17: ("01010101-0101-0101-0101-010101010103", "ArcaneTrickster_11_SpellThief")})):
    for lvl in range(13, 21):
        boosts = {13: "ActionResource(SpellSlot,2,3)", 16: "ActionResource(SpellSlot,1,3)", 19: "ActionResource(SpellSlot,1,4)"}.get(lvl)
        learn = 1 if lvl in (13, 14, 16, 19, 20) else 0
        sel = f"SelectSpells({WIZ4 if lvl >= 19 else WIZ3},{learn},1,{tag})"
        if lvl in existing:
            u, passive = existing[lvl]
            attrs = {"PassivesAdded": passive, "Selectors": sel}
            if boosts:
                attrs["Boosts"] = boosts
            EXISTING[u] = attrs
        else:
            node(table, name, lvl, boosts=boosts, selectors=sel)

# ---------------------------------------------------------------- Warlock 17: the fourth Pact Magic slot (2024 table: 3 slots at 11, 4 at 17)
EXISTING["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbb905"] = {
    "PassivesAdded": "Warlock_MysticArcanum_9", "Selectors": "SelectSpells(00190001-0001-0001-0001-000000000007,1,0,MysticArcanum9,,None,AlwaysPrepared,UntilRest)",
    "Boosts": "ActionResource(WarlockSpellSlot,1,5)"}

def write():
    new_nodes = []
    for table, name, level, passives, boosts, selectors in NODES:
        attrs = {"PassivesAdded": ";".join(passives)} if passives else {}
        if boosts:
            attrs["Boosts"] = boosts
        if selectors:
            attrs["Selectors"] = selectors
        new_nodes.append((G.gid(f"node:{table}:{level}"), name, level, 1, table, attrs))
    G.write_stats("SubclassFeatures", "gen_subclass_features.py", "13-20 subclass features")
    G.patch_files()
    patch_progressions(EXISTING, new_nodes, G.marker)
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.resources)} resources, {len(NODES)} nodes")
