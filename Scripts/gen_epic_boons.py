"""Generate the Epic Boons (PHB 2024 level-19 feats) - issue #1.
Since 2026-10-06 every boon is a real FEAT (Feats/Feats.lsx + FeatDescriptions.lsx) with the PHB prerequisite "Level 19+"
as a feat requirement: FeatRequirement = CharacterLevelGreaterThan(N) (base CommonConditions.khn). The class-level-19 node of
each class gets an ordinary feat pick (AllowImprovement) - "an Epic Boon feat or another feat of your choice" - and the boons
also show up in any later feat pick at character level 19+ (a multiclass character's ASI), as the rules allow.
The +1 ability (to a maximum of 30) is part of the feat: a boon that names no ability picks one of the six (ABILITY_SELECT);
a boon that restricts it (Irresistible Offense: Str/Dex, Spell Recall: Int/Wis/Cha) picks one of its per-ability variants,
each with the +1 built in, because the ability also drives the boon (casting ability, damage bonus).
Owns (rewritten every run): Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_EpicBoons.txt, Feats/Feats.lsx,
Feats/FeatDescriptions.lsx.
Patches idempotently (between markers / by UUID): Lists/PassiveLists.lsx, ActionResourceDefinitions,
Localization/English/dnd55e-Apotheosis.xml, Progressions.lsx (level-19 nodes).
Script Extender halves live in ScriptExtender/Lua/EpicBoons.lua.

Run: python3 Scripts/gen_epic_boons.py
"""
import glob
import json
import os
import re
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = glob.glob(os.path.join(REPO, "Public", "*"))[0]
DATA = os.path.join(PUB, "Stats", "Generated", "Data")
LOCA = glob.glob(os.path.join(REPO, "Mods", "*", "Localization", "English", "dnd55e-Apotheosis.xml"))[0]
NS = uuid.NAMESPACE_URL


def gid(key):
    return str(uuid.uuid5(NS, "apotheosis-epicboon:" + key))


LOCA_ROWS = {}


def h(key, text):
    """Deterministic loca handle (h + 32 hex, the width this mod already uses) with its English text."""
    handle = "h" + uuid.uuid5(NS, "apotheosis-epicboon-loca:" + key).hex
    LOCA_ROWS[handle] = text
    return handle


ABILITIES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
SHORT = {"Strength": "Str", "Dexterity": "Dex", "Constitution": "Con", "Intelligence": "Int", "Wisdom": "Wis", "Charisma": "Cha"}
ENERGY = ["Acid", "Cold", "Fire", "Lightning", "Necrotic", "Poison", "Psychic", "Radiant", "Thunder"]
SKILLS = ["Acrobatics", "AnimalHandling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation",
          "Investigation", "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion",
          "SleightOfHand", "Stealth", "Survival"]
SKILL_NAME = {"AnimalHandling": "Animal Handling", "SleightOfHand": "Sleight of Hand"}
NIGHT_RESIST = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison", "Slashing", "Thunder"]
DARK = "(HasObscuredState(ObscuredState.HeavilyObscured) or HasObscuredState(ObscuredState.LightlyObscured))"
# Bloodied for defensive boosts (resistances): the BLOODED status on the owner (context.Source), as dnd55e writes its
# status-conditioned resistances (SG_Rage, LAND_*). An HP-percentage condition there didn't follow HP (2026-10-02).
BLOODIED = "HasStatus('BLOODED', context.Source)"
# IF() boosts are only re-evaluated on their passive's BoostContext events - without one the condition stays as it was
# when the passive was added (dnd55e Fractured_6_BrainsAndBrawn: OnStatusApplied;OnStatusRemoved)
BLOODIED_CONTEXT = "OnStatusApplied;OnStatusRemoved"
ALL_DAMAGE = ["Acid", "Bludgeoning", "Cold", "Fire", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic", "Radiant", "Slashing", "Thunder"]
SCHOOLS = ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion", "Necromancy", "Transmutation"]
MENTAL = ["Intelligence", "Wisdom", "Charisma"]
QUIET = "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"

RESOURCES = [  # name, max, replenish, display, description
    ("EpicBoonPeerlessAim", 1, "Turn", "Peerless Aim", "Turn a missed attack into a hit. Returns at the start of your turn."),
    ("EpicBoonFate", 1, "ShortRest", "Improve Fate", "Add or subtract 2d4 from a nearby d20 roll. Returns when you roll Initiative or finish a rest."),
    ("EpicBoonEnergyChoice", 2, "Rest", "Energy Resistance Choices", "Choose your two Boon of Energy Resistance damage types. Resets on a Long Rest."),
    ("EpicBoonRecoveryDie", 10, "Rest", "Recover Vitality Dice", "Your pool of ten d10s for Recover Vitality. Returns on a Long Rest."),
    ("EpicBoonExpertiseChoice", 1, "Never", "Boon of Skill Expertise", "Choose the skill you gain Expertise in."),
    # phase 2 (Heroes of Faerun, Arcana Unleashed)
    ("EpicBoonFortune", 1, "Turn", "Fortune's Favor", "Reroll a failed saving throw. Returns at the start of your turn."),
    ("EpicBoonRevelry", 1, "Rest", "Inspire Dance", "Cast Otto's Irresistible Dance without a spell slot. Returns on a Long Rest."),
    ("EpicBoonTerror", 1, "ShortRest", "Flee, Fools!", "Stoke a Frightened creature's terror. Returns on a Short or Long Rest."),
    ("EpicBoonSoulDrinker", 1, "ShortRest", "Siphon Life", "Regain 50 Hit Points when an enemy drops. Returns on a Short or Long Rest."),
    ("EpicBoonOverload", 1, "ShortRest", "Spell Overload", "Surge a damaging spell. Returns when you roll Initiative or finish a rest."),
    ("EpicBoonFluidForms", 1, "Rest", "Shapechanger", "Shape-shift into another creature. Returns on a Long Rest."),
    ("EpicBoonMSMSchool", 1, "Never", "Mastered School", "Choose your Boon of Magic School Mastery school."),
    ("EpicBoonRoteChoice", 1, "Never", "Rote Casting", "Choose your Rote Casting spell."),
    ("EpicBoonSignatureChoice", 1, "Never", "Signature Arcanum", "Choose your Signature Arcanum spell."),
    ("EpicBoonSignature", 1, "Rest", "Signature Arcanum", "Cast your Signature Arcanum without a spell slot. Returns on a Long Rest."),
    # Eberron: Forge of the Artificer (2026-10-05)
    ("EpicBoonSiberysChoice", 1, "Never", "Aberrant Magic", "Choose your Boon of Siberys spell."),
    ("EpicBoonSiberys", 1, "ShortRest", "Aberrant Magic", "Cast your Boon of Siberys spell without a spell slot or components. Returns on a Short or Long Rest."),
]


def entry(name, typ, fields, using=None, comment=None):
    out = ([f"// {comment}"] if comment else []) + [f'new entry "{name}"', f'type "{typ}"']
    if using:
        out.append(f'using "{using}"')
    out += [f'data "{k}" "{v}"' for k, v in fields.items() if v is not None]
    return "\n".join(out) + "\n"


P, S, SP, I = [], [], [], []  # passives, statuses, spells, interrupts
BOONS, ABILITY_PASSIVES = [], []
FEATS = []  # (name, title handle, text handle, passives added, variant passives)
# The PHB prerequisite "Level 19+". Which value the feat list sees while the level-up screen is open (the level before or
# after the level being taken) is verified in game - see FEAT_REQ_NOTE.
FEAT_REQ = "CharacterLevelGreaterThan(18)"
FEAT_REQ_NOTE = "unverified"
# "abilities": SelectAbilities over all six (the game's ability picker); "passives": a pick of EpicBoonAbility_<Ab> passives
# (Ability() boosts aren't capped at 20, verified in game 2026-09-30). Epic Boons allow a score of up to 30.
ABILITY_SELECT = "passives"
ALL_ABILITIES_LIST = "b9149c8e-52c8-46e5-9cb6-fc39301c05fe"  # base AbilityList with all six ("Human List")


def boon(name, title, text, fields, variants=None):
    """variants: abilities the boon's own +1 may go to (restricted boons get one entry per ability, picked inside the feat)."""
    base = {"DisplayName": h(name + ":n", title), "Description": h(name + ":d", text),
            "Icon": fields.pop("Icon", "PassiveFeature_Generic_Magical"), "Properties": fields.pop("Properties", "Highlighted")}
    if not variants:
        P.append(entry(name, "PassiveData", {**base, **fields}))
        BOONS.append(name)
        FEATS.append((name, base["DisplayName"], base["Description"], [name], []))
        return
    names = []
    for ab in variants:
        vn = f"{name}_{SHORT[ab]}"
        boosts = ";".join(x for x in [f"Ability({ab},1)", fields.get("Boosts")] if x)
        P.append(entry(vn, "PassiveData", {**base, **fields, "Boosts": boosts,
                                             "DisplayName": h(vn + ":n", f"{title} (+1 {ab})")}))
        BOONS.append(vn)
        names.append(vn)
    FEATS.append((name, base["DisplayName"], base["Description"], [], names))


# ---------------------------------------------------------------- PHB 2024 boons (phase 1)
boon("EpicBoon_CombatProwess", "Boon of Combat Prowess",
     "Peerless Aim: when you miss with an attack roll, you can hit instead. Once you use this, you can't again until the start of your next turn.",
     {"Boosts": "UnlockInterrupt(Interrupt_EpicBoon_PeerlessAim);ActionResource(EpicBoonPeerlessAim,1,0)"})
I.append(entry("Interrupt_EpicBoon_PeerlessAim", "InterruptData", {
    "DisplayName": h("PeerlessAim:n", "Peerless Aim"), "Description": h("PeerlessAim:d", "Your attack misses: hit instead."),
    "Icon": "PassiveFeature_Generic_Magical", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self",
    "Container": "YesNoDecision",
    "Conditions": "not Dead(context.Observer) and HasInterruptedAttack() and Self(context.Observer,context.Source) and not AnyEntityIsItem() and IsFlatValueInterruptInteresting(99, context.Source)",
    "Properties": "AdjustRoll(OBSERVER_OBSERVER,99)", "Cost": "EpicBoonPeerlessAim:1", "InterruptDefaultValue": "Ask;Enabled"},
    comment="Boon of Combat Prowess. A natural 1 still misses (AdjustRoll can't override it) - documented gap."))

boon("EpicBoon_DimensionalTravel", "Boon of Dimensional Travel",
     "Blink Steps: immediately after you take the Attack action or the Magic action, you can teleport up to 30 feet to an unoccupied space you can see.",
     {"Boosts": None})
S.append(entry("EPIC_BLINK_STEPS", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("BlinkStatus:n", "Blink Steps"), "Description": h("BlinkStatus:d", "You can teleport up to 30 feet (free)."),
    "Icon": "Spell_Conjuration_MistyStep", "Boosts": "UnlockSpell(Target_EpicBoon_BlinkStep)", "StackId": "EPIC_BLINK_STEPS",
    "StatusPropertyFlags": "DisableCombatlog"}, comment="Applied by EpicBoons.lua after an Attack or Magic action (a cast costing an ActionPoint)."))
SP.append(entry("Target_EpicBoon_BlinkStep", "SpellData", {
    "SpellType": "Target", "Level": "0", "DisplayName": h("BlinkSpell:n", "Blink Step"),
    "Description": h("BlinkSpell:d", "Teleport up to 30 feet to an unoccupied space you can see."), "Icon": "Spell_Conjuration_MistyStep",
    "SpellProperties": "GROUND:TeleportSource();GROUND:RemoveStatus(SELF,EPIC_BLINK_STEPS)", "TargetRadius": "9",
    "TargetConditions": "CanStand('') and not Character() and not Self()", "RequirementConditions": "HasStatus('EPIC_BLINK_STEPS')",
    "UseCosts": "", "SpellFlags": "HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold", "CastTextEvent": "Cast"},
    using="Target_MistyStep"))

boon("EpicBoon_EnergyResistance", "Boon of Energy Resistance",
     "Energy Resistances: choose two of Acid, Cold, Fire, Lightning, Necrotic, Poison, Psychic, Radiant and Thunder (the choices reset on a Long Rest). Energy Redirection: when you take damage of a chosen type, your Reaction sends 2d12 + Constitution modifier of that type at the attacker (Dexterity save, DC 8 + Constitution modifier + Proficiency Bonus).",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_EnergyResistance);ActionResource(EpicBoonEnergyChoice,2,0)",
      "StatsFunctorContext": "OnLongRest", "StatsFunctors": ";".join(f"RemoveStatus(SELF,EPIC_ENERGY_RES_{t.upper()})" for t in ENERGY)})
SP.append(entry("Shout_EpicBoon_EnergyResistance", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("EnergyChoose:n", "Energy Resistance"),
    "Description": h("EnergyChoose:d", "Choose a damage type to resist (two per Long Rest)."), "Icon": "Spell_Abjuration_ProtectionFromEnergy",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_EnergyResistance_{t}" for t in ENERGY), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "EpicBoonEnergyChoice:1", "TargetConditions": "Self()"}))
for t in ENERGY:
    SP.append(entry(f"Shout_EpicBoon_EnergyResistance_{t}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_EnergyResistance",
        "DisplayName": h(f"EnergyChoose{t}:n", f"Energy Resistance: {t}"), "Description": h(f"EnergyChoose{t}:d", f"You resist {t} damage until your next Long Rest."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "UseCosts": "EpicBoonEnergyChoice:1", "TargetConditions": "Self()",
        "RequirementConditions": f"not HasStatus('EPIC_ENERGY_RES_{t.upper()}')",
        "SpellProperties": f"ApplyStatus(SELF,EPIC_ENERGY_RES_{t.upper()},100,-1)"}))
    S.append(entry(f"EPIC_ENERGY_RES_{t.upper()}", "StatusData", {
        "StatusType": "BOOST", "DisplayName": h(f"EnergyRes{t}:n", f"Energy Resistance: {t}"),
        "Description": h(f"EnergyRes{t}:d", f"Resistant to {t} damage; your Reaction can redirect it (Boon of Energy Resistance)."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "Boosts": f"Resistance({t},Resistant)", "StackId": f"EPIC_ENERGY_RES_{t.upper()}",
        "StatusPropertyFlags": "IgnoreResting"}))
    SP.append(entry(f"Target_EpicBoon_EnergyRedirection_{t}", "SpellData", {
        "SpellType": "Target", "Level": "0", "DisplayName": h(f"Redirect{t}:n", f"Energy Redirection ({t})"),
        "Description": h(f"Redirect{t}:d", f"Redirect {t} damage: 2d12 + Constitution modifier, Dexterity save."),
        "Icon": "Spell_Abjuration_ProtectionFromEnergy", "TargetRadius": "18", "TargetConditions": "Character() and not Dead() and not Self()",
        "SpellRoll": "not SavingThrow(Ability.Dexterity, 8+ConstitutionModifier+ProficiencyBonus)",
        "SpellSuccess": f"DealDamage(2d12+ConstitutionModifier,{t},Magical)", "TooltipDamageList": f"DealDamage(2d12+ConstitutionModifier,{t})",
        "TooltipAttackSave": "Dexterity", "UseCosts": "", "SpellFlags": "IsHarmful", "CastTextEvent": "Cast"},
        comment="Cast by EpicBoons.lua (spends your Reaction) at whoever dealt the damage." if t == ENERGY[0] else None))

boon("EpicBoon_Fate", "Boon of Fate",
     "Improve Fate: when you or a creature within 60 feet succeeds on or fails a d20 roll, you can roll 2d4 and add it to or subtract it from the roll. Usable again when you roll Initiative or finish a Short or Long Rest.",
     {"Boosts": "UnlockInterrupt(Interrupt_EpicBoon_Fate_AllyAttack);UnlockInterrupt(Interrupt_EpicBoon_Fate_AllySave);"
                "UnlockInterrupt(Interrupt_EpicBoon_Fate_EnemyAttack);UnlockInterrupt(Interrupt_EpicBoon_Fate_EnemySave);ActionResource(EpicBoonFate,1,0)"})
for key, cond, sign, label in [
        ("AllyAttack", "HasInterruptedAttack() and (Self(context.Observer,context.Source) or Ally(context.Source,context.Observer))", "", "Improve Fate: bless an attack"),
        ("AllySave", "HasInterruptedSavingThrow() and (Self(context.Observer,context.Target) or Ally(context.Target,context.Observer))", "", "Improve Fate: bless a save"),
        ("EnemyAttack", "HasInterruptedAttack() and Enemy(context.Source,context.Observer)", "0-", "Improve Fate: curse an attack"),
        ("EnemySave", "HasInterruptedSavingThrow() and Enemy(context.Target,context.Observer)", "0-", "Improve Fate: curse a save")]:
    I.append(entry(f"Interrupt_EpicBoon_Fate_{key}", "InterruptData", {
        "DisplayName": h(f"Fate{key}:n", label), "Description": h(f"Fate{key}:d", ("Add" if not sign else "Subtract") + " 2d4 to the roll."),
        "Icon": "PassiveFeature_Generic_Magical", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Nearby", "Container": "YesNoDecision",
        # attack rolls belong to the attacker: say so, as base Cutting Words does (IsFlatValueInterruptInteresting(8,
        # context.Source)); without it the enemy-attack reaction never fired on a real wolf's bites (2026-10-02)
        "Conditions": f"not Dead(context.Observer) and {cond} and not AnyEntityIsItem() and "
                      f"IsFlatValueInterruptInteresting(8{', context.Source' if 'Attack' in key else ''})",
        "Properties": f"AdjustRoll(OBSERVER_OBSERVER,{sign}2d4)", "Cost": "EpicBoonFate:1", "InterruptDefaultValue": "Ask;Enabled"}))

boon("EpicBoon_Fortitude", "Boon of Fortitude",
     "Fortified Health: your Hit Point maximum increases by 40. Whenever you regain Hit Points, you regain extra Hit Points equal to your Constitution modifier (once per turn).",
     {"Boosts": "IncreaseMaxHP(40)", "StatsFunctorContext": "OnHealed",
      "StatsFunctors": "IF(not HasStatus('EPIC_FORTITUDE_USED')):ApplyStatus(SELF,EPIC_FORTITUDE_HEAL,100,0)"})
S.append(entry("EPIC_FORTITUDE_HEAL", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("FortHeal:n", "Fortified Health"), "Icon": "PassiveFeature_Generic_Magical",
    "OnApplyFunctors": "ApplyStatus(EPIC_FORTITUDE_USED,100,1);RegainHitPoints(max(1,ConstitutionModifier))",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}))
S.append(entry("EPIC_FORTITUDE_USED", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("FortUsed:n", "Fortified Health used"), "Icon": "PassiveFeature_Generic_Magical",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}))

boon("EpicBoon_IrresistibleOffense", "Boon of Irresistible Offense",
     "Overcome Defenses: your Bludgeoning, Piercing and Slashing damage ignores Resistance. Overwhelming Strike: when you roll a 20 on an attack roll, deal extra damage equal to the ability score this boon increased.",
     {"Boosts": "IgnoreResistance(Bludgeoning,Resistant);IgnoreResistance(Piercing,Resistant);IgnoreResistance(Slashing,Resistant)",
      "StatsFunctorContext": "OnAttack", "StatsFunctors": "IF(IsCritical()):ApplyStatus(EPIC_OVERWHELMING_MARK,100,0)"},
     variants=["Strength", "Dexterity"])
S.append(entry("EPIC_OVERWHELMING_MARK", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("Overwhelm:n", "Overwhelming Strike"), "Icon": "PassiveFeature_Generic_Magical",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
    comment="Marks a critical hit's target; EpicBoons.lua deals the extra damage (= the boosted ability score)."))

boon("EpicBoon_Recovery", "Boon of Recovery",
     "Last Stand: when you would drop to 0 Hit Points, you drop to 1 instead and regain half your Hit Point maximum (once per Long Rest). Recover Vitality: a pool of ten d10s; as a Bonus Action, spend dice and regain that many Hit Points.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_RecoverVitality);ActionResource(EpicBoonRecoveryDie,10,0)",
      "StatsFunctorContext": "OnCreate;OnLongRest", "StatsFunctors": "ApplyStatus(SELF,EPIC_LAST_STAND,100,-1)",
      "Properties": "Highlighted;OncePerLongRest"})
S.append(entry("EPIC_LAST_STAND", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("LastStand:n", "Last Stand"), "Description": h("LastStand:d", "The next time you would drop to 0 Hit Points, you drop to 1 and regain half your Hit Point maximum."),
    "Icon": "PassiveFeature_RelentlessEndurance", "Boosts": "DownedStatus(EPIC_LAST_STAND_DOWNED,6)", "StackId": "EPIC_LAST_STAND",
    "StatusGroups": "SG_RemoveOnRespec", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead;IgnoreResting"},
    comment="Boon of Recovery, cloned from Relentless Endurance (priority 6 beats it). EpicBoons.lua heals to 1 + half max HP."))
S.append(entry("EPIC_LAST_STAND_DOWNED", "StatusData", {
    "OnApplyFunctors": "RemoveStatus(EPIC_LAST_STAND);RegainHitPoints(1,Guaranteed)"}, using="RELENTLESS_ENDURANCE_DOWNED"))
SP.append(entry("Shout_EpicBoon_RecoverVitality", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Vitality:n", "Recover Vitality"),
    "Description": h("Vitality:d", "Spend d10s from your Recover Vitality pool to regain Hit Points."), "Icon": "Skill_Fighter_SecondWind",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_RecoverVitality_{n}" for n in (1, 2, 3, 5, 10)), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "BonusActionPoint:1;EpicBoonRecoveryDie:1", "TargetConditions": "Self()"}))
for n in (1, 2, 3, 5, 10):
    SP.append(entry(f"Shout_EpicBoon_RecoverVitality_{n}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_RecoverVitality",
        "DisplayName": h(f"Vitality{n}:n", f"Recover Vitality ({n}d10)"), "Description": h(f"Vitality{n}:d", f"Spend {n} dice: regain {n}d10 Hit Points."),
        "Icon": "Skill_Fighter_SecondWind", "UseCosts": f"BonusActionPoint:1;EpicBoonRecoveryDie:{n}", "TargetConditions": "Self()",
        "SpellProperties": f"RegainHitPoints({n}d10)", "TooltipDamageList": f"RegainHitPoints({n}d10)"}))

boon("EpicBoon_Skill", "Boon of Skill",
     "All-Around Adept: you gain proficiency in all skills. Expertise: choose one skill in which you lack Expertise and gain Expertise in it.",
     {"Boosts": ";".join(f"ProficiencyBonus(Skill,{s})" for s in SKILLS) + ";UnlockSpell(Shout_EpicBoon_Expertise);ActionResource(EpicBoonExpertiseChoice,1,0)"})
SP.append(entry("Shout_EpicBoon_Expertise", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Expertise:n", "Boon of Skill: Expertise"),
    "Description": h("Expertise:d", "Choose one skill to gain Expertise in (once)."), "Icon": "PassiveFeature_Generic_Magical",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_Expertise_{s}" for s in SKILLS), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "EpicBoonExpertiseChoice:1", "TargetConditions": "Self()"}))
for s_ in SKILLS:
    nm = SKILL_NAME.get(s_, s_)
    SP.append(entry(f"Shout_EpicBoon_Expertise_{s_}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_Expertise",
        "DisplayName": h(f"Expertise{s_}:n", f"Expertise: {nm}"), "Description": h(f"Expertise{s_}:d", f"Gain Expertise in {nm}."),
        "Icon": "PassiveFeature_Generic_Magical", "UseCosts": "EpicBoonExpertiseChoice:1", "TargetConditions": "Self()",
        "SpellProperties": f"ApplyStatus(SELF,EPIC_EXPERTISE_{s_.upper()},100,-1)"}))
    S.append(entry(f"EPIC_EXPERTISE_{s_.upper()}", "StatusData", {
        "StatusType": "BOOST", "DisplayName": h(f"ExpertiseSt{s_}:n", f"Expertise: {nm}"), "Icon": "PassiveFeature_Generic_Magical",
        "Boosts": f"ExpertiseBonus({s_})", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;IgnoreResting"}))

boon("EpicBoon_Speed", "Boon of Speed",
     "Escape Artist: as a Bonus Action, you can take the Disengage action, which also ends the Grappled condition on you. Quickness: your Speed increases by 30 feet.",
     {"Boosts": "ActionResource(Movement,9,0);UnlockSpell(Shout_EpicBoon_EscapeArtist)"})
SP.append(entry("Shout_EpicBoon_EscapeArtist", "SpellData", {
    "DisplayName": h("Escape:n", "Escape Artist"), "Description": h("Escape:d", "Disengage as a Bonus Action and end the Grappled condition on yourself."),
    "SpellProperties": "ApplyStatus(DISENGAGE,100,1);RemoveStatus(SELF,GRAPPLED)"}, using="Shout_Disengage_BonusAction"))

boon("EpicBoon_SpellRecall", "Boon of Spell Recall",
     "Free Casting: whenever you cast a spell with a level 1-4 spell slot, roll 1d4. If the number matches the slot's level, the slot isn't expended. (Requires the Spellcasting feature.)",
     {"Boosts": None}, variants=["Intelligence", "Wisdom", "Charisma"])

boon("EpicBoon_NightSpirit", "Boon of the Night Spirit",
     "Merge with Shadows: while in Dim Light or Darkness, you can become Invisible as a Bonus Action until you take an action, Bonus Action or Reaction. Shadowy Form: while in Dim Light or Darkness, you resist all damage except Psychic and Radiant.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_MergeWithShadows);" + ";".join(f"IF({DARK}):Resistance({t},Resistant)" for t in NIGHT_RESIST)})
SP.append(entry("Shout_EpicBoon_MergeWithShadows", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Merge:n", "Merge with Shadows"),
    "Description": h("Merge:d", "In Dim Light or Darkness: become Invisible until you act."), "Icon": "Action_Cleric_ChannelDivinity_CloakOfShadows",
    "UseCosts": "BonusActionPoint:1", "TargetConditions": "Self()", "RequirementConditions": DARK,
    "SpellProperties": "ApplyStatus(SELF,EPIC_MERGE_WITH_SHADOWS,100,-1)", "SpellFlags": "Invisible", "CastTextEvent": "Cast"}))
S.append(entry("EPIC_MERGE_WITH_SHADOWS", "StatusData", {
    "DisplayName": h("MergeSt:n", "Merged with Shadows"), "Description": h("MergeSt:d", "Invisible until you take an action, Bonus Action or Reaction.")},
    using="CLOAK_OF_SHADOWS_MONK"))

boon("EpicBoon_Truesight", "Boon of Truesight", "Truesight: you have Truesight with a range of 60 feet.",
     {"StatsFunctorContext": "OnCreate;OnLongRest;OnShortRest", "StatsFunctors": "ApplyStatus(SELF,TRUESIGHT,100,-1)"})

# ---------------------------------------------------------------- phase 2: Heroes of Faerun + Arcana Unleashed
# References/Feats/EpicBoons.txt. Script Extender halves in EpicBoons.lua (search "phase 2").

def st(name, fields, using=None, comment=None):
    S.append(entry(name, "StatusData", {"StatusType": "BOOST", "Icon": "PassiveFeature_Generic_Magical",
                                        "StatusPropertyFlags": QUIET, **fields}, using=using, comment=comment))


boon("EpicBoon_Bloodshed", "Boon of Bloodshed",
     "Killer's Fortune: when an enemy you can see is reduced to 0 Hit Points, you have Advantage on your next attack roll before the end of your next turn. Power from Pain: once per turn, when you hit with an attack roll while Bloodied, deal extra damage equal to your Proficiency Bonus of the attack's type.",
     {"Boosts": None})
st("EPIC_KILLERS_FORTUNE", {"DisplayName": h("Killers:n", "Killer's Fortune"), "Description": h("Killers:d", "Advantage on your next attack roll."),
                            "Boosts": "Advantage(AttackRoll)", "RemoveEvents": "OnAttack", "RemoveConditions": "IsAttack()",
                            "StatusPropertyFlags": None})
st("EPIC_POWER_FROM_PAIN_USED", {"DisplayName": h("PainUsed:n", "Power from Pain used")})

boon("EpicBoon_BountifulHealth", "Boon of Bountiful Health",
     "Augmented Health: whenever you gain Temporary Hit Points, you gain 5 more. Superior Recuperation: when you spend Hit Point Dice to regain Hit Points, each die heals its maximum.",
     {"Boosts": None})
st("EPIC_SUPERIOR_RECUPERATION", {"DisplayName": h("Recup:n", "Superior Recuperation"), "Boosts": "MaximizeHealing(Incoming)"})

boon("EpicBoon_Communication", "Boon of Communication",
     "Cunning Speaker, Gifted Interpreter and Mental Communication (telepathy 120 feet). BG3 has no hostile-influence penalty, language barrier or telepathy, so this boon gives only its ability increase.",
     {"Boosts": None}, variants=MENTAL)

boon("EpicBoon_DesperateResilience", "Boon of Desperate Resilience",
     "Defense of Body and Mind: while you are Bloodied, you have Resistance to every damage type except Force.",
     {"Boosts": ";".join(f"IF({BLOODIED}):Resistance({d},Resistant)" for d in ALL_DAMAGE), "BoostContext": BLOODIED_CONTEXT},
     variants=["Strength", "Constitution"])

boon("EpicBoon_ExquisiteRadiance", "Boon of Exquisite Radiance",
     "Powerful Radiance: once per Long Rest, when you roll Radiant damage, each die rolls its maximum. Eternal Rest (creatures you kill can't become Undead) has no BG3 equivalent.",
     {"StatsFunctorContext": "OnCreate;OnLongRest", "StatsFunctors": "ApplyStatus(SELF,EPIC_POWERFUL_RADIANCE,100,-1)"})
st("EPIC_POWERFUL_RADIANCE", {"DisplayName": h("Radiance:n", "Powerful Radiance"),
                              "Description": h("Radiance:d", "Your next Radiant damage roll uses the highest number on each die."),
                              "Boosts": "IF(MainDamageTypeIs(DamageType.Radiant)):MinimumRollResult(Damage,20)",
                              "StatusPropertyFlags": "IgnoreResting"}, comment="EpicBoons.lua removes it after one Radiant damage roll.")

boon("EpicBoon_FluidForms", "Boon of Fluid Forms",
     "Shapechanger: once per Long Rest, as a Magic action, shape-shift into a Beast or Monstrosity for 1 hour, gaining Temporary Hit Points equal to the form's Hit Points plus 20 (Hardy Transformation). It ends when they run out or you take a Magic action to revert.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_FluidForms);UnlockSpell(Shout_EpicBoon_FluidForms_Revert);ActionResource(EpicBoonFluidForms,1,0)"},
     variants=MENTAL)
FLUID = [("Sheep", "SHEEP", 3), ("DireWolf", "DIREWOLF", 37), ("ShadowMastiff", "SHADOWMASTIFF", 33),
         ("PhaseSpider", "PHASESPIDER", 24), ("Minotaur", "MINOTAUR", 84)]  # the True Polymorph forms (#20)
SP.append(entry("Shout_EpicBoon_FluidForms", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Fluid:n", "Shapechanger"),
    "Description": h("Fluid:d", "Shape-shift into another creature for 1 hour."), "Icon": "Spell_Transmutation_Polymorph",
    "ContainerSpells": ";".join(f"Shout_EpicBoon_FluidForms_{k}" for k, _, _ in FLUID), "SpellFlags": "IsLinkedSpellContainer",
    "UseCosts": "ActionPoint:1;EpicBoonFluidForms:1", "TargetConditions": "Self()"}))
for k, form, hp in FLUID:
    SP.append(entry(f"Shout_EpicBoon_FluidForms_{k}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_FluidForms",
        "DisplayName": h(f"Fluid{k}:n", f"Shapechanger: {k}"), "Description": h(f"Fluid{k}:d", f"Become a {k} ({hp} + 20 temporary Hit Points)."),
        "Icon": "Spell_Transmutation_Polymorph", "UseCosts": "ActionPoint:1;EpicBoonFluidForms:1", "TargetConditions": "Self()",
        "SpellProperties": f"ApplyStatus(SELF,TRUE_POLYMORPH_{form},100,600)"}))
    st(f"TRUE_POLYMORPH_TEMPHP_{form}_HARDY", {"DisplayName": h(f"Hardy{k}:n", "Hardy Transformation"),
                                              "Boosts": f"TemporaryHP({hp + 20})", "StackId": "TRUE_POLYMORPH_TEMPHP", "StackType": "Overwrite"},
       comment="Boon of Fluid Forms: the form's HP + 20. TruePolymorph.lua applies it for a self-cast Fluid Forms shape.")
SP.append(entry("Shout_EpicBoon_FluidForms_Revert", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("FluidRevert:n", "Return to True Form"),
    "Description": h("FluidRevert:d", "End your Shapechanger form."), "Icon": "Spell_Transmutation_Polymorph",
    "UseCosts": "ActionPoint:1", "TargetConditions": "Self()",
    "RequirementConditions": " or ".join(f"HasStatus('TRUE_POLYMORPH_{f}')" for _, f, _ in FLUID),
    "SpellProperties": ";".join(f"RemoveStatus(SELF,TRUE_POLYMORPH_{f})" for _, f, _ in FLUID)}))

boon("EpicBoon_FortunesFavor", "Boon of Fortune's Favor",
     "Saving Throw Reroll: when you fail a saving throw, you can reroll it and must use the new roll. Once you use this, you can't again until the start of your next turn.",
     {"Boosts": "UnlockInterrupt(Interrupt_EpicBoon_FortunesFavor);ActionResource(EpicBoonFortune,1,0)"})
I.append(entry("Interrupt_EpicBoon_FortunesFavor", "InterruptData", {
    "DisplayName": h("Fortune:n", "Fortune's Favor"), "Description": h("Fortune:d", "You failed a saving throw: reroll it."),
    "Icon": "PassiveFeature_Generic_Magical", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "not Dead(context.Observer) and HasInterruptedSavingThrow() and Self(context.Observer,context.Target) and not AnyEntityIsItem() and IsRerollInterruptInteresting()",
    "Properties": "SetReroll(19,true)", "Cost": "EpicBoonFortune:1", "InterruptDefaultValue": "Ask;Enabled"},
    comment="As base Fighter Indomitable (SetReroll(19,true) = reroll, use the new roll)."))

boon("EpicBoon_PoisonMastery", "Boon of Poison Mastery",
     "Antitoxic: Immunity to Poison damage and the Poisoned condition. Perfect Poisoner: once per turn, when you roll Poison damage, each die rolls its maximum.",
     {"Boosts": "Resistance(Poison,Immune);StatusImmunity(SG_Poisoned)",
      "StatsFunctorContext": "OnCreate", "StatsFunctors": "ApplyStatus(SELF,EPIC_PERFECT_POISONER,100,-1)"})
st("EPIC_PERFECT_POISONER", {"DisplayName": h("Poisoner:n", "Perfect Poisoner"),
                             "Boosts": "IF(MainDamageTypeIs(DamageType.Poison)):MinimumRollResult(Damage,20)", "StatusPropertyFlags": "IgnoreResting"},
   comment="EpicBoons.lua removes it after a Poison damage roll and restores it at the start of your turn.")

boon("EpicBoon_Revelry", "Boon of Revelry",
     "Inspire Dance: you always have Otto's Irresistible Dance prepared and can cast it once per Long Rest without a slot or components; damage doesn't break your Concentration on it. Sing Out: a creature charmed by your dance can't cast spells with Verbal components.",
     {"Boosts": "UnlockSpell(Target_IrresistibleDance);UnlockSpell(Target_EpicBoon_IrresistibleDance);ActionResource(EpicBoonRevelry,1,0)"},
     variants=MENTAL)
SP.append(entry("Target_EpicBoon_IrresistibleDance", "SpellData", {
    "DisplayName": h("Dance:n", "Inspire Dance"), "Description": h("Dance:d", "Otto's Irresistible Dance, without a spell slot or components."),
    "UseCosts": "ActionPoint:1;EpicBoonRevelry:1",
    "SpellFlags": "HasHighGroundRangeExtension;IsConcentration;IsSpell;CannotTargetItems;CannotTargetTerrain;IsHarmful"},
    using="Target_IrresistibleDance"))
st("EPIC_REVELRY_FOCUS", {"DisplayName": h("RevFocus:n", "Inspire Dance"), "Boosts": "ConcentrationIgnoreDamage(Enchantment)"},
   comment="While your dance holds: damage doesn't break the Concentration (EpicBoons.lua applies and removes it).")
st("EPIC_SING_OUT", {"DisplayName": h("SingOut:n", "Sing Out"), "Description": h("SingOut:d", "Sings delightful nonsense: can't cast spells with Verbal components."),
                     "Boosts": "BlockVerbalComponent()", "StatusPropertyFlags": None})

boon("EpicBoon_Terror", "Boon of Terror",
     "Fearless: Immunity to the Frightened condition. Flee, Fools!: when a Frightened creature you can see starts its turn within 60 feet, you can use your Reaction to make it pass a Wisdom save (DC 8 + Charisma modifier + Proficiency Bonus) or flee; once per Short or Long Rest. Intimidating: proficiency and Expertise in Intimidation.",
     {"Boosts": "StatusImmunity(SG_Frightened);ProficiencyBonus(Skill,Intimidation);ExpertiseBonus(Intimidation);ActionResource(EpicBoonTerror,1,0)"},
     variants=["Charisma"])
SP.append(entry("Target_EpicBoon_FleeFools", "SpellData", {
    "SpellType": "Target", "Level": "0", "DisplayName": h("Flee:n", "Flee, Fools!"), "Description": h("Flee:d", "The creature flees on a failed Wisdom save."),
    "Icon": "Spell_Enchantment_CommandFlee", "TargetRadius": "18", "TargetConditions": "Character() and not Dead() and not Self()",
    "SpellRoll": "not SavingThrow(Ability.Wisdom, 8+CharismaModifier+ProficiencyBonus)", "SpellSuccess": "ApplyStatus(COMMAND_FLEE,100,1)",
    "UseCosts": "", "SpellFlags": "IsHarmful", "TooltipAttackSave": "Wisdom"}, comment="Cast by EpicBoons.lua (real save) as a Reaction."))

boon("EpicBoon_BrightSun", "Boon of the Bright Sun",
     "Daylight Presence: as a Bonus Action, you radiate a 30-foot emanation of sunlight until you dismiss it, die or are Incapacitated; it dispels overlapping magical Darkness. Fortifying Light: at the start of each of your turns, you and allies you can see in it gain 10 Temporary Hit Points.",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_DaylightPresence);UnlockSpell(Shout_EpicBoon_DaylightPresence_Dismiss)"},
     variants=["Constitution", "Wisdom", "Charisma"])
SP.append(entry("Shout_EpicBoon_DaylightPresence", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("Daylight:n", "Daylight Presence"), "Description": h("Daylight:d", "Radiate sunlight in a 30-foot emanation."),
    "Icon": "Spell_Evocation_Daylight", "UseCosts": "BonusActionPoint:1", "TargetConditions": "Self()",
    "RequirementConditions": "not HasStatus('EPIC_DAYLIGHT_PRESENCE')", "SpellProperties": "ApplyStatus(SELF,EPIC_DAYLIGHT_PRESENCE,100,-1)"}))
SP.append(entry("Shout_EpicBoon_DaylightPresence_Dismiss", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("DaylightOff:n", "Dismiss Daylight Presence"), "Description": h("DaylightOff:d", "End your Daylight Presence."),
    "Icon": "Spell_Evocation_Daylight", "UseCosts": "", "TargetConditions": "Self()",
    "RequirementConditions": "HasStatus('EPIC_DAYLIGHT_PRESENCE')", "SpellProperties": "RemoveStatus(SELF,EPIC_DAYLIGHT_PRESENCE)"}))
st("EPIC_DAYLIGHT_PRESENCE", {"DisplayName": h("DaylightSt:n", "Daylight Presence"), "Description": h("DaylightSt:d", "You radiate sunlight in a 30-foot emanation."),
                              "Icon": "Spell_Evocation_Daylight", "Boosts": "GameplayLight(9,false,0.1,true)",
                              "RemoveConditions": "HasStatus('SG_Incapacitated') or Dead()", "RemoveEvents": "OnStatusApplied",
                              "StatusPropertyFlags": "IgnoreResting"}, comment="EpicBoons.lua: Fortifying Light each turn, dispels Darkness.")
st("EPIC_FORTIFYING_LIGHT", {"DisplayName": h("Fortifying:n", "Fortifying Light"), "Boosts": "TemporaryHP(10)",
                             "RemoveConditions": "not HasTemporaryHP()", "RemoveEvents": "OnDamage", "StatusPropertyFlags": None},
   comment="dnd55e DEFENSIVE_FIELD/RALLY pattern; GainTemporaryHitPoints(10) on a duration-0 status granted nothing (2026-10-02).")

boon("EpicBoon_FuriousStorm", "Boon of the Furious Storm",
     "Eye of the Storm: Resistance to Lightning and Thunder damage, Immunity while you are Bloodied. Storm's Strength: creatures have Disadvantage on saving throws against your spells that deal Lightning or Thunder damage. (Requires the Spellcasting or Pact Magic feature.)",
     {"Boosts": "Resistance(Lightning,Resistant);Resistance(Thunder,Resistant);"
                f"IF({BLOODIED}):Resistance(Lightning,Immune);IF({BLOODIED}):Resistance(Thunder,Immune)"
                # Storm's Strength: Heightened Spell's own mechanism (a caster-side variant), verified in game 2026-10-02
                ";UnlockSpellVariant(HasSpellFlag(SpellFlags.Spell) and (SpellDamageTypeIs(DamageType.Lightning) or "
                "SpellDamageTypeIs(DamageType.Thunder)),ModifySavingThrowDisadvantage())", "BoostContext": BLOODIED_CONTEXT},
     variants=MENTAL)

boon("EpicBoon_SoulDrinker", "Boon of the Soul Drinker",
     "Grave Resistance: Resistance to Cold and Necrotic damage. Siphon Life: when an enemy within 120 feet is reduced to 0 Hit Points, you can use your Reaction to regain 50 Hit Points; once per Short or Long Rest.",
     {"Boosts": "Resistance(Cold,Resistant);Resistance(Necrotic,Resistant);ActionResource(EpicBoonSoulDrinker,1,0)"})
st("EPIC_SIPHON_LIFE", {"DisplayName": h("Siphon:n", "Siphon Life"), "OnApplyFunctors": "RegainHitPoints(50)", "StatusPropertyFlags": None})

boon("EpicBoon_EruptingSpellpower", "Boon of Erupting Spellpower",
     "Spell Overload: as a free action, ready an overload; the next damaging spell you cast with a spell slot treats any 1 or 2 on a damage die as a 3, and creatures it damages are knocked Prone. Returns when you roll Initiative or finish a Short or Long Rest. (Requires the Spellcasting or Pact Magic feature.)",
     {"Boosts": "ActionResource(EpicBoonOverload,1,0);UnlockSpell(Shout_EpicBoon_SpellOverload);UnlockSpell(Shout_EpicBoon_SpellOverload_Cancel)"},
     variants=MENTAL)
SP.append(entry("Shout_EpicBoon_SpellOverload", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("OverloadArm:n", "Spell Overload"), "Description": h("OverloadArm:d", "Your next damaging spell cast with a spell slot treats 1s and 2s on damage dice as 3s and knocks the creatures it damages Prone."),
    "Icon": "Spell_Evocation_Thunderwave", "UseCosts": "", "TargetConditions": "Self()",
    "RequirementConditions": "not HasStatus('EPIC_SPELL_OVERLOAD_ARMED')", "SpellProperties": "ApplyStatus(SELF,EPIC_SPELL_OVERLOAD_ARMED,100,-1)",
    "SpellFlags": "IgnoreSilence"}))
SP.append(entry("Shout_EpicBoon_SpellOverload_Cancel", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("OverloadOff:n", "Cancel Spell Overload"), "Description": h("OverloadOff:d", "Stop readying Spell Overload."),
    "Icon": "Spell_Evocation_Thunderwave", "UseCosts": "", "TargetConditions": "Self()",
    "RequirementConditions": "HasStatus('EPIC_SPELL_OVERLOAD_ARMED')", "SpellProperties": "RemoveStatus(SELF,EPIC_SPELL_OVERLOAD_ARMED)",
    "SpellFlags": "IgnoreSilence"}))
st("EPIC_SPELL_OVERLOAD_ARMED", {"DisplayName": h("OverloadArmed:n", "Spell Overload ready"), "StatusPropertyFlags": "IgnoreResting"})
st("EPIC_SPELL_OVERLOAD", {"DisplayName": h("Overload:n", "Spell Overload"), "Boosts": "MinimumRollResult(Damage,3)"},
   comment="On the caster while the surged spell resolves (EpicBoons.lua), like Elemental Adept's MinimumRollResult(Damage,2).")

boon("EpicBoon_IronMind", "Boon of the Iron Mind",
     "Unshakable Focus: taking damage never breaks your Concentration. (BG3 conditions that end Concentration on their own, such as being stunned, still do.)",
     {"Boosts": ";".join(f"ConcentrationIgnoreDamage({sch})" for sch in SCHOOLS)})


# Boon of Magic School Mastery: school -> Rote Casting (a level 1 spell, at will, no slot or components) and Signature
# Arcanum (a level 1-7 spell, once per Long Rest without a slot). Spell pool: Scripts/data/magic_school_spells.json
# (the class spell lists, exported with bg3-data-mcp; container spells are left out). Pickers follow Spell Mastery.
# The Magic School Mastery spell copies (`using` the original) go in their own file, sorting after every other one.
SP_LATE = []
MSM = json.load(open(os.path.join(REPO, "Scripts", "data", "magic_school_spells.json"), encoding="utf-8"))
# Signature pickers are split by spell level: a 44-spell container (ContainerSpells ~2080 chars) hung the game at
# LoadModule, 43 (2030 chars) loaded - bisected 2026-10-02. The largest shipped container is 42 spells / ~1000 chars.
SIG_BANDS = (("13", "1-3", range(1, 4)), ("47", "4-7", range(4, 8)))
boon("EpicBoon_MagicSchoolMastery", "Boon of Magic School Mastery",
     "Mastered School: choose a school of magic. Rote Casting: a level 1 spell of that school is always prepared and you can cast it without a spell slot or components. Signature Arcanum: a level 7 or lower spell of that school is always prepared; cast it once per Long Rest without a spell slot. (Requires the Spellcasting or Pact Magic feature; spells with variant menus aren't offered.)",
     {"Boosts": "UnlockSpell(Shout_EpicBoon_MSM_School);ActionResource(EpicBoonMSMSchool,1,0);ActionResource(EpicBoonRoteChoice,1,0);"
                "ActionResource(EpicBoonSignatureChoice,1,0);ActionResource(EpicBoonSignature,1,0)"}, variants=MENTAL)


def picker(name, title, desc, children, cost):
    SP.append(entry(name, "SpellData", {"SpellType": "Shout", "Level": "0", "DisplayName": h(name + ":n", title),
                                        "Description": h(name + ":d", desc), "Icon": "PassiveFeature_Generic_Magical",
                                        "ContainerSpells": ";".join(children), "SpellFlags": "IsLinkedSpellContainer",
                                        "UseCosts": cost, "TargetConditions": "Self()"}))


def free_copy(spell, suffix, extra_cost, strip_components, info=None, label=None):
    info = info or MSM["spells"][spell]
    label = label or ("Rote" if suffix == "EpicRote" else "Signature")
    costs = ";".join(c for c in info["costs"].split(";") if c and not c.startswith("SpellSlotsGroup") and not c.startswith("WarlockSpellSlot"))
    costs = ";".join(c for c in [costs, extra_cost] if c)
    flags = info["flags"]
    if strip_components:
        flags = ";".join(f for f in flags.split(";") if f and f not in ("HasVerbalComponent", "HasSomaticComponent"))
    SP_LATE.append(entry(f"{spell}_{suffix}", "SpellData", {"UseCosts": costs, "SpellFlags": flags,
                                                       "DisplayName": h(f"{spell}_{suffix}:n", f"{info['name']} ({label})")},
                    using=spell))


picker("Shout_EpicBoon_MSM_School", "Mastered School", "Choose your school of magic.",
       [f"Shout_EpicBoon_MSM_School_{sch}" for sch in SCHOOLS], "EpicBoonMSMSchool:1")
for sch in SCHOOLS:
    pool = MSM["schools"].get(sch, {})
    rote = sorted(pool.get("1", []))
    sig = sorted(sp for lv in pool.values() for sp in lv)
    SP.append(entry(f"Shout_EpicBoon_MSM_School_{sch}", "SpellData", {
        "SpellType": "Shout", "Level": "0", "SpellContainerID": "Shout_EpicBoon_MSM_School",
        "DisplayName": h(f"MSM{sch}:n", f"Mastered School: {sch}"), "Description": h(f"MSM{sch}:d", f"Master the {sch} school."),
        "Icon": "PassiveFeature_Generic_Magical", "UseCosts": "EpicBoonMSMSchool:1", "TargetConditions": "Self()",
        "SpellProperties": f"ApplyStatus(SELF,EPIC_MSM_{sch.upper()},100,-1)"}))
    st(f"EPIC_MSM_{sch.upper()}", {"DisplayName": h(f"MSMSt{sch}:n", f"Mastered School: {sch}"),
                                   "Boosts": f"UnlockSpell(Shout_EpicBoon_MSM_Rote_{sch});" + ";".join(
                                       f"UnlockSpell(Shout_EpicBoon_MSM_Signature_{sch}_L{b})" for b, _, lv in SIG_BANDS
                                       if any(MSM["spells"][x]["level"] in lv for x in sig)),
                                   "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;IgnoreResting", "StatusGroups": "SG_RemoveOnRespec"})
    picker(f"Shout_EpicBoon_MSM_Rote_{sch}", f"Rote Casting ({sch})", f"Choose a level 1 {sch} spell to cast at will.",
           [f"Shout_EpicBoon_MSM_RotePick_{sp}" for sp in rote], "EpicBoonRoteChoice:1")
    for b, label_, lv in SIG_BANDS:
        band = [sp for sp in sig if MSM["spells"][sp]["level"] in lv]
        if band:
            picker(f"Shout_EpicBoon_MSM_Signature_{sch}_L{b}", f"Signature Arcanum ({sch}, level {label_})",
                   f"Choose a level {label_} {sch} spell.", [f"Shout_EpicBoon_MSM_SigPick_{sp}" for sp in band],
                   "EpicBoonSignatureChoice:1")
    for kind, spells, res_, status_prefix, suffix, extra, strip in (
            ("Rote", rote, "EpicBoonRoteChoice", "EPIC_MSM_ROTE_", "EpicRote", "", True),
            ("Sig", sig, "EpicBoonSignatureChoice", "EPIC_MSM_SIG_", "EpicSignature", "EpicBoonSignature:1", False)):
        for sp in spells:
            info = MSM["spells"][sp]
            label = "Rote Casting" if kind == "Rote" else "Signature Arcanum"
            SP.append(entry(f"Shout_EpicBoon_MSM_{kind}Pick_{sp}", "SpellData", {
                "SpellType": "Shout", "Level": "0", "SpellContainerID": f"Shout_EpicBoon_MSM_Rote_{sch}" if kind == "Rote" else
                f"Shout_EpicBoon_MSM_Signature_{sch}_L{next(b for b, _, lv in SIG_BANDS if info['level'] in lv)}",
                "DisplayName": h(f"MSM{kind}Pick{sp}:n", f"{label}: {info['name']} (level {info['level']})"),
                "Description": h(f"MSM{kind}Pick{sp}:d", f"Choose {info['name']} as your {label} spell."),
                "Icon": "PassiveFeature_Generic_Magical", "UseCosts": f"{res_}:1", "TargetConditions": "Self()",
                "SpellProperties": f"ApplyStatus(SELF,{status_prefix}{sp.upper()},100,-1)"}))
            st(f"{status_prefix}{sp.upper()}", {"DisplayName": h(f"MSM{kind}St{sp}:n", f"{label}: {info['name']}"),
                                                 "Boosts": f"UnlockSpell({sp});UnlockSpell({sp}_{suffix})",
                                                 "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;IgnoreResting", "StatusGroups": "SG_RemoveOnRespec"})
            free_copy(sp, suffix, extra, strip)


# Boon of Siberys (Eberron: Forge of the Artificer, 2025; added 2026-10-05). Aberrant Magic: a level 1-8 Sorcerer spell or
# a Siberys Dragonmark Spells table spell, always prepared, cast once per Short or Long Rest without a slot or components
# and with any slots; Int, Wis or Cha is its spellcasting ability. The +1 goes to any ability (the ordinary ability pick),
# so the three variants are the casting ability only - named _Cast<Abi> so EpicBoons.lua doesn't read them as boons with
# a built-in +1. The ability goes on UnlockSpell's last argument, chosen in the pick status by IF(HasPassive(...)) as the
# base game's ABERRANT_SHAPE unlocks by passive. Pool: Scripts/data/siberys_spells.json (export_siberys_spells.py);
# container spells aren't offered, as for Magic School Mastery.
SIB = json.load(open(os.path.join(REPO, "Scripts", "data", "siberys_spells.json"), encoding="utf-8"))
SLOT_CAST = "d136c5d9-0ff0-43da-acce-a74a07f8d6bf"  # cast with spell slots (the base game's racial/feat UnlockSpell)
SIB_BANDS = (("L1", "a level 1 Sorcerer spell", lambda v: not v["table"] and v["level"] == 1),
             ("L2", "a level 2 Sorcerer spell", lambda v: not v["table"] and v["level"] == 2),
             ("L34", "a level 3-4 Sorcerer spell", lambda v: not v["table"] and v["level"] in (3, 4)),
             ("L58", "a level 5-8 Sorcerer spell", lambda v: not v["table"] and v["level"] >= 5),
             ("Mark", "a Siberys Dragonmark spell", lambda v: v["table"]))
SIB_TEXT = ("Aberrant Magic: choose a level 8 or lower Sorcerer spell or a Siberys Dragonmark spell (Animal Shapes, Control "
            "Weather, Demiplane, Heroes' Feast, Maze, Mind Blank, Plane Shift, Project Image, Regenerate, Symbol, Teleport, "
            "True Seeing). You always have it prepared. You can cast it once without a spell slot or components, regaining "
            "that use when you finish a Short or Long Rest, and with any spell slots of its level. {ab} is your spellcasting "
            "ability for it. (Spells with variant menus aren't offered.)")
for ab in MENTAL:
    vn = f"EpicBoon_Siberys_Cast{SHORT[ab]}"
    P.append(entry(vn, "PassiveData", {
        "DisplayName": h(vn + ":n", f"Boon of Siberys ({ab} spellcasting)"), "Description": h(vn + ":d", SIB_TEXT.format(ab=ab)),
        "Icon": "PassiveFeature_Generic_Magical", "Properties": "Highlighted",
        "Boosts": ";".join(f"UnlockSpell(Shout_EpicBoon_Sib_{b})" for b, _, _ in SIB_BANDS)
                  + ";ActionResource(EpicBoonSiberysChoice,1,0);ActionResource(EpicBoonSiberys,1,0)"}))
    BOONS.append(vn)
for b, what, keep in SIB_BANDS:
    band = sorted(sp for sp, v in SIB["spells"].items() if keep(v))
    picker(f"Shout_EpicBoon_Sib_{b}", f"Aberrant Magic ({what})", f"Choose {what} for your Boon of Siberys.",
           [f"Shout_EpicBoon_Sib_Pick_{sp}" for sp in band], "EpicBoonSiberysChoice:1")
    for sp in band:
        info = SIB["spells"][sp]
        SP.append(entry(f"Shout_EpicBoon_Sib_Pick_{sp}", "SpellData", {
            "SpellType": "Shout", "Level": "0", "SpellContainerID": f"Shout_EpicBoon_Sib_{b}",
            "DisplayName": h(f"SibPick{sp}:n", f"Aberrant Magic: {info['name']} (level {info['level']})"),
            "Description": h(f"SibPick{sp}:d", f"Choose {info['name']} as your Boon of Siberys spell."),
            "Icon": "PassiveFeature_Generic_Magical", "UseCosts": "EpicBoonSiberysChoice:1", "TargetConditions": "Self()",
            "SpellProperties": f"ApplyStatus(SELF,EPIC_SIB_{sp.upper()},100,-1)"}))
        st(f"EPIC_SIB_{sp.upper()}", {"DisplayName": h(f"SibSt{sp}:n", f"Aberrant Magic: {info['name']}"),
                                      "Boosts": ";".join(
                                          f"IF(HasPassive('EpicBoon_Siberys_Cast{SHORT[ab]}',context.Source)):UnlockSpell({sp},AddChildren,{SLOT_CAST},,{ab});"
                                          f"IF(HasPassive('EpicBoon_Siberys_Cast{SHORT[ab]}',context.Source)):UnlockSpell({sp}_EpicSiberys,Singular,,,{ab})"
                                          for ab in MENTAL),
                                      "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;IgnoreResting", "StatusGroups": "SG_RemoveOnRespec"})
        free_copy(sp, "EpicSiberys", "EpicBoonSiberys:1", True, info=info, label="Aberrant Magic")


# ---------------------------------------------------------------- ability pick
for ab in ABILITIES:
    n = f"EpicBoonAbility_{SHORT[ab]}"
    P.append(entry(n, "PassiveData", {"DisplayName": h(n + ":n", f"Epic Boon: +1 {ab}"),
                                      "Description": h(n + ":d", f"Increase your {ab} score by 1 (to a maximum of 30)."),
                                      "Icon": "PassiveFeature_Generic_Magical", "Properties": "Highlighted", "Boosts": f"Ability({ab},1)"}))
    ABILITY_PASSIVES.append(n)
ABILITY_LIST = gid("list:ability")


# ---------------------------------------------------------------- write / patch
# A spell with no SpellAnimation (own or inherited) never finishes casting - verified in game 2026-09-30.
ANIM = {"Shout": "9122eb08-93f1-4010-a275-f5ae3ec7c76e,,;,,;9fb11cca-02d4-4d2f-955f-2826c0553b17,,;5103d398-d8de-4aa4-9633-db2e1b7f6254,,;5301d674-b7da-47b6-b4cf-2802ba33a9e9,,;,,;86b3cf93-21fb-4a3d-bed9-97d0a567d084,,;,,;,,",
        "Target": "3ff87abf-1ea1-4c32-aadf-c822d74c7dc0,,;,,;ab7b6aac-b3c9-4918-8f17-f777a94dcb5e,,;57211a11-ed0b-46d7-9369-81df25a85df6,,;d8925ce4-d6d9-400c-92f5-ad772ef7f178,,;,,;eadedcce-d01b-4fbb-a1ae-d218f13aa5d6,,;,,;,,"}


def animate(block):
    if 'using "' in block or '"ContainerSpells"' in block or '"SpellAnimation"' in block:
        return block
    m = re.search(r'data "SpellType" "(\w+)"', block)
    if not m or m.group(1) not in ANIM:
        return block
    return block.rstrip("\n") + f'\ndata "SpellAnimation" "{ANIM[m.group(1)]}"\n'


def write_stats():
    head = ("// GENERATED by Scripts/gen_epic_boons.py (Epic Boons, issue #1) - edit the generator, not this file.\n"
            "// Script Extender half: ScriptExtender/Lua/EpicBoons.lua\n\n")
    for fname, rows in (("Passive_EpicBoons.txt", P), ("Status_EpicBoons.txt", S), ("Spell_EpicBoons.txt", [animate(x) for x in SP]),
                        ("Interrupt_EpicBoons.txt", I), ("Spell_ZZ_EpicBoons_MSM.txt", SP_LATE)):
        with open(os.path.join(DATA, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(head + "\n".join(rows))


def patch_between(path, start, end, block, anchor):
    s = open(path, encoding="utf-8").read()
    if start in s:
        s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
    else:
        i = s.rindex(anchor)
        s = s[:i] + block + s[i:]
    open(path, "w", encoding="utf-8", newline="").write(s)


def _plist(name, passives, uid):
    return f"""                <node id="PassiveList">
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="Passives" type="LSString" value="{','.join(passives)}"/>
                    <attribute id="UUID" type="guid" value="{uid}"/>
                </node>
"""


def patch_lists():
    """The six +1 picks, and per restricted boon the list of its per-ability variants (picked inside its feat)."""
    path = os.path.join(PUB, "Lists", "PassiveLists.lsx")
    block = ("                <!-- EPIC BOONS BEGIN (Scripts/gen_epic_boons.py) -->\n" + _plist("EpicBoonAbility", ABILITY_PASSIVES, ABILITY_LIST)
             + "".join(_plist(name, variants, gid("list:variants:" + name)) for name, _, _, _, variants in FEATS if variants)
             + "                <!-- EPIC BOONS END -->\n")
    patch_between(path, "                <!-- EPIC BOONS BEGIN", "<!-- EPIC BOONS END -->\n", block, "            </children>")


FEAT_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="8" revision="0" build="500"/>
    <region id="{region}">
        <node id="root">
            <children>
"""
FEAT_TAIL = """            </children>
        </node>
    </region>
</save>
"""


def write_feats(probe=False):
    """Feats/Feats.lsx + FeatDescriptions.lsx: one feat per boon, prerequisite FEAT_REQ. probe: also a copy of the first boon
    whose prerequisite is one level lower (EpicBoonProbe), for the in-game check of which level the feat list sees."""
    d = os.path.join(PUB, "Feats")
    os.makedirs(d, exist_ok=True)
    rows = list(FEATS)
    if probe:  # test-only feats, never committed: EPIC_BOON_PROBE=1 when regenerating for the in-game check
        name, dn, desc, added, variants = rows[0]
        rows.append(("EpicBoonProbe", h("probe:n", "PROBE: Combat Prowess (level > 17)"), desc, added, variants))
        rows.append(("EpicBoonProbeAbilities", h("probe2:n", "PROBE: Combat Prowess (level > 17, ability picker)"), desc, added, variants))
        rows.append(("EpicBoonProbeNever", h("probe3:n", "PROBE: Combat Prowess (level > 30)"), desc, added, variants))
    feats, descs = [], []
    for name, dn, desc, added, variants in rows:
        if variants:
            sel = f"SelectPassives({gid('list:variants:' + name)},1,EpicBoon)"
        elif ABILITY_SELECT == "abilities" or name == "EpicBoonProbeAbilities":
            sel = f"SelectAbilities({ALL_ABILITIES_LIST},1,1,EpicBoonAbility)"
        else:
            sel = f"SelectPassives({ABILITY_LIST},1,EpicBoonAbility)"
        req = {"EpicBoonProbeNever": "CharacterLevelGreaterThan(30)"}.get(name, "CharacterLevelGreaterThan(17)" if name.startswith("EpicBoonProbe") else FEAT_REQ)
        fid = gid("feat:" + name)
        feats.append(f"""                <node id="Feat">
                    <attribute id="Name" type="FixedString" value="{name}"/>
""" + (f"""                    <attribute id="PassivesAdded" type="LSString" value="{';'.join(added)}"/>
""" if added else "") + f"""                    <attribute id="Requirements" type="LSString" value="{req}"/>
                    <attribute id="Selectors" type="LSString" value="{sel}"/>
                    <attribute id="UUID" type="guid" value="{fid}"/>
                </node>
""")
        descs.append(f"""                <node id="FeatDescription">
                    <attribute id="Description" type="TranslatedString" handle="{desc}" version="1"/>
                    <attribute id="DisplayName" type="TranslatedString" handle="{dn}" version="1"/>
                    <attribute id="ExactMatch" type="FixedString" value="{name}"/>
                    <attribute id="FeatId" type="guid" value="{fid}"/>
                    <attribute id="UUID" type="guid" value="{gid('featdesc:' + name)}"/>
                </node>
""")
    for fname, region, body in (("Feats.lsx", "Feats", feats), ("FeatDescriptions.lsx", "FeatDescriptions", descs)):
        with open(os.path.join(d, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(FEAT_HEAD.format(region=region) + "".join(body) + FEAT_TAIL)
    return len(rows)


def patch_resources():
    path = glob.glob(os.path.join(PUB, "ActionResourceDefinitions", "*.lsx"))[0]
    rows = []
    for name, mx, rep, disp, desc in RESOURCES:
        rows.append(f"""                <node id="ActionResourceDefinition">
                    <attribute id="DisplayName" type="TranslatedString" handle="{h('res:' + name + ':n', disp)}" version="1"/>
                    <attribute id="Description" type="TranslatedString" handle="{h('res:' + name + ':d', desc)}" version="1"/>
                    <attribute id="IsHidden" type="bool" value="false"/>
                    <attribute id="MaxLevel" type="uint32" value="0"/>
                    <attribute id="MaxValue" type="uint32" value="{mx}"/>
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="ReplenishType" type="FixedString" value="{rep}"/>
                    <attribute id="ShowOnActionResourcePanel" type="bool" value="true"/>
                    <attribute id="UUID" type="guid" value="{gid('res:' + name)}"/>
                </node>
""")
    block = "                <!-- EPIC BOONS BEGIN (Scripts/gen_epic_boons.py) -->\n" + "".join(rows) + "                <!-- EPIC BOONS END -->\n"
    patch_between(path, "                <!-- EPIC BOONS BEGIN", "<!-- EPIC BOONS END -->\n", block, "            </children>")


def patch_loca():
    from gen_common import update_loca
    update_loca(LOCA_ROWS)


# The PHB classes plus dnd55e classes whose own source gives an Epic Boon at 19 (Gunslinger: gen_gunslinger.py
# overrides dnd55e's level-19 node to drop its ASI)
# Artificer: Eberron - Forge of the Artificer (2025) also gives an Epic Boon at 19 (added 2026-10-03)
PHB_CLASSES = {"Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
               "Gunslinger"}


def patch_progressions():
    """Each class's level-19 node: an ordinary feat pick (AllowImprovement) - the Epic Boon feats are on the feat list from
    character level 19 - and none of the old EpicBoon/EpicBoonAbility passive picks (before 2026-10-06)."""
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()
    done = []

    def fix(m):
        b = m.group(0)
        name = re.search(r'id="Name" type="LSString" value="([^"]*)"', b)
        lvl = re.search(r'id="Level" type="uint8" value="(\d+)"', b)
        if not (name and lvl and name.group(1) in PHB_CLASSES and lvl.group(1) == "19") or "IsMulticlass" in b:
            return b
        def drop_boon_picks(mm):
            keep = ";".join(x for x in mm.group(2).split(";") if x and "EpicBoon" not in x)
            return f"{mm.group(1)}{keep}{mm.group(3)}" if keep else ""
        b = re.sub(r'(\s*<attribute id="Selectors" type="LSString" value=")([^"]*)("/>)', drop_boon_picks, b)
        if 'id="AllowImprovement"' not in b:
            b = re.sub(r'(\s*)(<attribute id="Level")', r'\1<attribute id="AllowImprovement" type="bool" value="true"/>\1\2', b, count=1)
        done.append(name.group(1))
        return b

    s = re.sub(r'<node id="Progression">(?:(?!</node>).)*?</node>', fix, s, flags=re.S)
    open(path, "w", encoding="utf-8", newline="").write(s)
    return done


if __name__ == "__main__":
    write_stats()
    n_feats = write_feats(probe=os.environ.get("EPIC_BOON_PROBE") == "1")
    patch_lists()
    patch_resources()
    patch_loca()
    classes = patch_progressions()
    print(f"{n_feats} feats ({FEAT_REQ}, prerequisite level {FEAT_REQ_NOTE}; +1 via {ABILITY_SELECT}), {len(BOONS)} boon entries, {len(ABILITY_PASSIVES)} ability options, {len(P)} passives, {len(S)} statuses, "
          f"{len(SP)} spells, {len(I)} interrupts, {len(LOCA_ROWS)} strings; level 19 set for {sorted(classes)}")
