"""Grim Hollow sangromancy spells, levels 7-9 (2026-10-12): Burst Forth, Sanguine Fusillade (7th), Creeping Death, Red Rain (8th),
Steal Immortality (9th). Text: library excerpts/spells/grim-hollow_sangromancy-spells.txt (Grim Hollow Player's Guide, revised, via
the D&D Beyond forum thread; Steal Immortality's Reaction trigger and Material component are from community write-ups, unconfirmed).
VISION #5 (the 13-20 curve of every subclass dnd55e ships: the Sangromancer's Savant picks at 13/15/17 need 7th-9th level
Sangromancy spells) and #1 (non-PHB content follows dnd55e's source, built the way dnd55e builds its 1st-4th level ones).

How dnd55e builds a sangromancy spell (verified on Circle of Scarlet 2026-10-12): a sangromancy spell fails unless you expend Hit
Point Dice - as many as the spell's level, one more per slot level above. Each spell is a CONTAINER with one variant per die size
(HitPointDice06/08/10/12; the d12 one spends the Sangromancer's Full-Blooded pool), and every upcast slot level gets its own
container + variants (`X_8` = the container at an 8th-level slot, `X12_8` = its d12 variant). dice rolled = dice expended = slot
level. gen_upcasts.py leaves families that already reach 9 alone, so the ladders here run to 9 themselves.

Class tags (Scripts/data/rules_spell_classes.json via extract_rules_spells.py, Grim Hollow source) put the containers on the
class lists; the Sangromancer's own picks come from SangromancySavantL7/8/9 below (13/15/17, gen_subclass_features.py).
Sanguine Vigor (regain HP = spell level) and the rest of dnd55e's sangromancy plumbing test `IsSangromancySpell()`, a hard-coded
SpellId whitelist in dnd55e's Wizard.khn: Mods/<mod>/Scripts/thoth/helpers/ApoSangromancy.khn redefines it as dnd55e's list
(read from the released dnd55e on every regen) plus ours. The file must be written like dnd55e's own .khn files - CRLF line endings,
no comments - or the game crashes while loading modules (see write_khn()).

Script Extender half: ScriptExtender/Lua/Sangromancy.lua (Creeping Death's threshold). Visuals: Scripts/data/vfx.toml.
Owns Stats/Generated/Data/{Spell,Status,Interrupt}_Sangromancy.txt, SpellLists.lsx between SANGROMANCY markers, the .khn file, loca.
Run: python3 Scripts/gen_sangromancy.py
"""
import glob
import os
import re

from gen_common import DND, Gen, PUB, REPO

G = Gen("sangromancy", "SANGROMANCY 7-9")
DICE = (6, 8, 10, 12)
GUID = os.path.basename(PUB)
KHN = os.path.join(REPO, "Mods", GUID, "Scripts", "thoth", "helpers", "ApoSangromancy.khn")
ICON = {"BurstForth": "Spell_CrimsonLash", "Fusillade": "Spell_VibratingHumors", "CreepingDeath": "Spell_Consumption",
        "RedRain": "Spell_BloodWisp", "StealImmortality": "Spell_TheftOfVitae"}   # dnd55e's sangromancy icons until we have our own
SPELLS = []   # every spell entry name this generator writes (the .khn whitelist)
SAVANT = {7: [], 8: [], 9: []}
EXHAUST_UP = ";".join(["IF(HasStatus('APO_EXHAUSTION_5')):Kill()"]
                      + [f"IF(HasStatus('APO_EXHAUSTION_{n}')):ApplyStatus(APO_EXHAUSTION_{n + 1},100,-1)" for n in range(4, 0, -1)]
                      + ["IF(not HasStatus('SG_Exhausted')):ApplyStatus(APO_EXHAUSTION_1,100,-1)"])   # as gen_au_spells.py


def hd(d):
    return f"HitPointDice{d:02d}"


def spell(name, fields, using=None, title=None, text=None, comment=None):
    f = dict(fields)
    if title:
        f["DisplayName"] = G.h(name + ":n", title)
    if text:
        f["Description"] = G.h(name + ":d", text)
    G.SP.append(G.entry(name, "SpellData", f, using=using, comment=comment))
    SPELLS.append(name)


def status(name, title, text, fields, using=None, icon=None, comment=None):
    G.status(name, title, text, fields, using=using, icon=icon, comment=comment)


def names(sid, s, base):
    """(container name, {die: variant name}) at slot s."""
    suf = "" if s == base else f"_{s}"
    return sid + suf, {d: f"{sid}{d}{suf}" for d in DICE}


def ladder(sid, base, title, text, upcast, icon, common, per_variant, container_extra=None, first=None):
    """Container + die variants for slot levels base..9, dnd55e's pattern. common: fields of the container/chassis (and so of
    every variant); per_variant(s, d) -> the fields that depend on slot / die (UseCosts, damage, DescriptionParams...)."""
    SAVANT[base].append(sid)
    for s in range(base, 10):
        cn, vn = names(sid, s, base)
        slot_cost = f"ActionPoint:1;SpellSlotsGroup:1:1:{s}"
        if s == base:
            spell(cn, {**common, "Level": str(base), "TooltipUpcastDescription": G.h(sid + ":up", upcast), "Icon": icon, **(container_extra or {}),
                       **per_variant(s, 6), "ContainerSpells": ";".join(vn[d] for d in DICE) + ";", "UseCosts": slot_cost + ";",
                       "SpellFlags": common["SpellFlags"] + ";IsLinkedSpellContainer"}, using=first,
                  title=title, text=text, comment=f"{title}, level {base} Sangromancy ({sid}); {len(DICE)} Hit Point Die variants")
            for d in DICE:
                spell(vn[d], {"SpellContainerID": cn, "ContainerSpells": "", "SpellFlags": common["SpellFlags"], **per_variant(s, d)}, using=cn,
                      title=f"{title} (d{d})")
        else:
            bc, bv = names(sid, base, base)
            spell(cn, {"RootSpellID": bc, "PowerLevel": str(s), **per_variant(s, 6), "ContainerSpells": ";".join(vn[d] for d in DICE) + ";",
                       "UseCosts": slot_cost + ";"}, using=bc)
            for d in DICE:
                spell(vn[d], {"SpellContainerID": cn, "RootSpellID": bv[d], "PowerLevel": str(s), **per_variant(s, d)}, using=bv[d])


# ---------------------------------------------------------------------------------------------------- Burst Forth (7th)
BF_TEXT = ("As part of casting this spell, you must expend [1] Hit Point Dice or the spell automatically fails. You teleport inside a "
           "creature that you can see within range and burst forth from it in a fountain of gore in the nearest unoccupied space. "
           "The target makes a Constitution saving throw, taking [2] on a failed save or half as much damage on a successful one.")
BF_UP = "You expend one additional Hit Point Die for each spell slot level above 7."


def bf(s, d):
    dmg = f"{s}d{d}+SpellCastingAbilityModifier"
    return {"SpellSuccess": f"DealDamage({dmg},Necrotic,Magical)", "SpellFail": f"DealDamage(({dmg})/2,Necrotic,Magical)",
            "TooltipDamageList": f"DealDamage({dmg},Necrotic)", "DescriptionParams": f"{s};DealDamage({dmg},Necrotic)",
            "UseCosts": f"ActionPoint:1;SpellSlotsGroup:1:1:{s};{hd(d)}:{s}"}


ladder("Target_BurstForth", 7, "Burst Forth", BF_TEXT, BF_UP, ICON["BurstForth"],
       {"SpellType": "Target", "SpellSchool": "Conjuration", "TargetRadius": "60", "DamageType": "Necrotic", "TooltipAttackSave": "Constitution",
        "TargetConditions": "Character() and not Dead() and not Self()", "SpellRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
        "SpellProperties": "GROUND:TeleportSource(true,true)", "SpellFlags": "HasVerbalComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
        "PrepareEffect": "@PTA_BurstForth_PrepareEffect", "CastEffect": "@PTA_BurstForth_CastEffect", "TargetEffect": "@PTA_BurstForth_TargetEffect"},
       bf, first="Target_Blight")

# ------------------------------------------------------------------------------------ Sanguine Fusillade (7th) + its darts
SF_TEXT = ("You crystalize your foe's blood into razor darts that burst forth to strike your enemies. As part of casting this spell, you must "
           "expend [1] Hit Point Dice or the spell automatically fails. Roll the Hit Point Dice expended to cast the spell. Choose a "
           "creature that you can see within range. The target takes [2] Piercing damage. When a creature takes this damage, [3] crimson "
           "darts burst from it. You can direct each dart (a free action: the Fusillade Darts spell, once) at a creature within range: "
           "make a ranged spell attack for each; on a hit it takes [4] Piercing damage.")
SF_UP = "You expend one additional Hit Point Die and create another dart for each spell slot level above 7."


def sf(s, d):
    dart = f"Projectile_SanguineFusillade_Dart_{d}_{s}"
    return {"SpellProperties": f"DealDamage({s}d{d},Piercing,Magical);ApplyStatus(SELF,SANGUINE_FUSILLADE_{d}_{s},100,2)",
            "TooltipDamageList": f"DealDamage({s}d{d},Piercing)", "DescriptionParams": f"{s};DealDamage({s}d{d},Piercing);{s};DealDamage(1d{d},Piercing)",
            "UseCosts": f"ActionPoint:1;SpellSlotsGroup:1:1:{s};{hd(d)}:{s}"}


ladder("Target_SanguineFusillade", 7, "Sanguine Fusillade", SF_TEXT, SF_UP, ICON["Fusillade"],
       {"SpellType": "Target", "SpellSchool": "Evocation", "TargetRadius": "18", "DamageType": "Piercing",
        "TargetConditions": "Character() and not Dead() and not Self()", "SpellRoll": "", "SpellSuccess": "", "SpellFail": "",
        "TooltipAttackSave": "", "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsHarmful",
        "PrepareEffect": "@PTA_Fusillade_PrepareEffect", "CastEffect": "@PTA_Fusillade_CastEffect", "TargetEffect": "@PTA_Fusillade_TargetEffect"},
       sf, first="Target_Blight")
for s in range(7, 10):
    for d in DICE:
        dart = f"Projectile_SanguineFusillade_Dart_{d}_{s}"
        spell(dart, {"SpellType": "Projectile", "Level": "0", "SpellSchool": "Evocation", "UseCosts": "", "AmountOfTargets": str(s), "DamageType": "Piercing",
                     "SpellRoll": "Attack(AttackType.RangedSpellAttack)", "SpellSuccess": f"DealDamage(1d{d},Piercing,Magical)", "SpellFail": "",
                     "TooltipDamageList": f"DealDamage(1d{d},Piercing)", "DescriptionParams": f"{s};DealDamage(1d{d},Piercing)",
                     "TargetRadius": "18", "TargetConditions": "not Self() and not Dead()", "SpellProperties": "",
                     "SpellFlags": "IsSpell;HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold;IsHarmful", "Icon": ICON["Fusillade"],
                     "SpellStyleGroup": "Class", "PrepareEffect": "", "CastEffect": "@PTA_Fusillade_DartCastEffect",
                     "TargetEffect": "@PTA_Fusillade_TargetEffect", "HitEffect": ""},
              using="Projectile_ScorchingRay", title=f"Fusillade Darts (d{d})",
              text="The crimson darts of your Sanguine Fusillade: [1] darts, each a ranged spell attack, each dealing [2] on a hit. You can send "
                   "them at one creature or several.")
        status(f"SANGUINE_FUSILLADE_{d}_{s}", "Sanguine Fusillade", f"{s} crimson darts are ready: cast Fusillade Darts (d{d}).",
               {"StackId": "SANGUINE_FUSILLADE", "Boosts": f"UnlockSpell({dart})", "RemoveConditions": f"SpellId('{dart}')", "RemoveEvents": "OnSpellCast"},
               icon=ICON["Fusillade"])

# ----------------------------------------------------------------------------------------------- Creeping Death (8th)
CD_TEXT = ("As part of casting this spell, you must expend [1] Hit Point Dice or the spell automatically fails. Roll the expended Hit Point Dice: "
           "the target's creeping death threshold is equal to the roll's total. For the duration, if the creature's Hit Points are reduced to or "
           "lower than its creeping death threshold, it immediately dies. As a Bonus Action, you can force the target to make a Constitution "
           "saving throw. On a failed save, roll 2d6 and add the result to its threshold; on a successful save, add half the result instead. "
           "If the creature succeeds on three saving throws, which don't have to be consecutive, this spell ends early.")
CD_UP = "You expend one additional Hit Point Die for each spell slot level above 8."


def cd(s, d):
    return {"SpellProperties": f"ApplyStatus(CREEPING_DEATH_{d}_{s},100,10);ApplyStatus(CREEPING_DEATH_MARK,100,10);ApplyStatus(SELF,CREEPING_DEATH_CASTER,100,10)",
            "DescriptionParams": f"{s}", "UseCosts": f"ActionPoint:1;SpellSlotsGroup:1:1:{s};{hd(d)}:{s}"}


ladder("Target_CreepingDeath", 8, "Creeping Death", CD_TEXT, CD_UP, ICON["CreepingDeath"],
       {"SpellType": "Target", "SpellSchool": "Necromancy", "TargetRadius": "18", "DamageType": "None", "TooltipAttackSave": "",
        "TargetConditions": "Character() and not Dead() and not Self()", "SpellRoll": "", "SpellSuccess": "", "SpellFail": "",
        "TooltipDamageList": "", "SpellFlags": "HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;IsConcentration;IsHarmful",
        "PrepareEffect": "@PTA_CreepingDeath_PrepareEffect", "CastEffect": "@PTA_CreepingDeath_CastEffect", "TargetEffect": "@PTA_CreepingDeath_TargetEffect"},
       cd, first="Target_Blight")
for s in range(8, 10):
    for d in DICE:
        status(f"CREEPING_DEATH_{d}_{s}", "Creeping Death",
               f"Creeping death threshold: the roll of {s}d{d}, set when the spell is cast. If this creature's Hit Points are reduced to or lower than it, "
               "it dies. Each failed Constitution save the caster forces raises it by 2d6 (half on a success); three successes end the spell.",
               {"StackId": "CREEPING_DEATH", "StatusPropertyFlags": "DisableOverhead"}, icon=ICON["CreepingDeath"],
               comment="Marker: ScriptExtender/Lua/Sangromancy.lua rolls the threshold from this name (dice, die) and watches the target's Hit Points.")
status("CREEPING_DEATH_MARK", "Creeping Death", "Doomed by creeping death (see the spell). The caster can force Constitution saves as a Bonus Action.",
       {"StackId": "CREEPING_DEATH_MARK"}, icon=ICON["CreepingDeath"])
status("CREEPING_DEATH_CASTER", "Creeping Death", "Bonus Action: force the doomed creature to make a Constitution save (Creeping Death: Surge).",
       {"StackId": "CREEPING_DEATH_CASTER", "Boosts": "UnlockSpell(Target_Apo_CreepingDeath_Surge)"}, icon=ICON["CreepingDeath"])
status("CREEPING_DEATH_SURGE_FAIL", "Creeping Death", "The creature failed: its threshold rises by 2d6.",
       {"StackId": "CREEPING_DEATH_SURGE_FAIL", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}, icon=ICON["CreepingDeath"],
       comment="One-turn marker: Sangromancy.lua applies the effect on StatusApplied and removes it at once.")
status("CREEPING_DEATH_SURGE_SAVE", "Creeping Death", "The creature saved: its threshold rises by half of 2d6.",
       {"StackId": "CREEPING_DEATH_SURGE_SAVE", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"}, icon=ICON["CreepingDeath"])
spell("Target_Apo_CreepingDeath_Surge", {
    "SpellType": "Target", "Level": "0", "SpellSchool": "Necromancy", "UseCosts": "BonusActionPoint:1", "TargetRadius": "18",
    "TargetConditions": "Character() and not Dead() and HasStatus('CREEPING_DEATH_MARK')", "SpellRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
    "SpellSuccess": "ApplyStatus(CREEPING_DEATH_SURGE_FAIL,100,1)", "SpellFail": "ApplyStatus(CREEPING_DEATH_SURGE_SAVE,100,1)",
    "TooltipAttackSave": "Constitution", "SpellFlags": "HasSomaticComponent;IsSpell;IsHarmful", "VerbalIntent": "Damage", "SpellStyleGroup": "Class",
    "Icon": ICON["CreepingDeath"], "PrepareEffect": "", "CastEffect": "@PTA_CreepingDeath_CastEffect", "TargetEffect": "@PTA_CreepingDeath_TargetEffect"},
    using="Target_Blight", title="Creeping Death: Surge",
    text="Bonus Action: the creature doomed by your Creeping Death makes a Constitution saving throw. On a failed save, its creeping death threshold "
         "rises by 2d6; on a successful save, by half that. Three successful saves end the spell.")

# --------------------------------------------------------------------------------------------------------- Red Rain (8th)
RR_TEXT = ("As part of casting this spell, you must expend [1] Hit Point Dice or the spell automatically fails. The sky darkens and thick droplets "
           "of blood rain over the battlefield. Each enemy Beast and Plant must succeed on a Wisdom saving throw or be Frightened for 1 minute. "
           "For every 10 minutes (100 turns) that a creature is exposed to the rain, it gains 1 level of Exhaustion and takes 2d10 Necrotic damage, "
           "and its Hit Point maximum decreases by 11 per level of exhaustion until a Long Rest. (A 5-mile area and a 10-minute casting time don't "
           "fit BG3: the rain covers the area around you and only your enemies are caught in it.)")
RR_UP = "You expend one additional Hit Point Die for each spell slot level above 8."


def rr(s, d):
    return {"SpellProperties": "ApplyStatus(SELF,RED_RAIN,100,-1)", "DescriptionParams": f"{s}",
            "UseCosts": f"ActionPoint:1;SpellSlotsGroup:1:1:{s};{hd(d)}:{s}"}


ladder("Shout_RedRain", 8, "Red Rain", RR_TEXT, RR_UP, ICON["RedRain"],
       {"SpellType": "Shout", "SpellSchool": "Conjuration", "TargetConditions": "Self()", "DamageType": "None",
        "TooltipStatusApply": "ApplyStatus(RED_RAIN,100,-1)",
        "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;IsConcentration;IsHarmful",
        "PrepareEffect": "@PTA_RedRain_PrepareEffect", "CastEffect": "@PTA_RedRain_CastEffect"},
       rr, first="Shout_SpiritGuardians")
status("RED_RAIN", "Red Rain", "Blood rains over the battlefield: enemies in the rain are exposed to it (see the spell).",
       {"StackId": "RED_RAIN", "AuraRadius": "36", "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(RED_RAIN_EXPOSED,100,-1)",
        "StatusEffect": "@PTA_RedRain_StatusEffect"}, icon=ICON["RedRain"])
status("RED_RAIN_EXPOSED", "Exposed to the Red Rain",
       "Blood rains on you. A Beast or Plant that fails a Wisdom saving throw is Frightened. After 10 minutes (100 turns) in the rain you take "
       "2d10 Necrotic damage, gain a level of Exhaustion and your Hit Point maximum drops.",
       {"StackId": "RED_RAIN_EXPOSED", "TickType": "StartTurn", "TickFunctors": "IF(not HasStatus('RED_RAIN_DOSE')):ApplyStatus(RED_RAIN_DOSE,100,100)",
        "OnApplyFunctors": "IF((Tagged('BEAST') or Tagged('PLANT')) and not SavingThrow(Ability.Wisdom, SourceSpellDC(Cause))):ApplyStatus(FRIGHTENED,100,10)",
        "StatusPropertyFlags": "DisableOverhead"}, icon=ICON["RedRain"],
       comment="The aura keeps this on everyone in the rain; each of its ticks starts a RED_RAIN_DOSE (a real 100-turn duration that an aura "
               "re-application cannot reset), whose end is the 10 minutes of exposure.")
status("RED_RAIN_DOSE", "Red Rain: dose", "Ten minutes of exposure to the rain end here: Necrotic damage, a level of Exhaustion, a lower Hit Point maximum.",
       {"StackId": "RED_RAIN_DOSE", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator;RemoveOnLongRest",
        "OnRemoveFunctors": "DealDamage(2d10,Necrotic,Magical);" + EXHAUST_UP + ";"
                            + ";".join(f"IF(HasStatus('RED_RAIN_DRAIN_{n}')):ApplyStatus(RED_RAIN_DRAIN_{n + 1},100,-1)" for n in range(4, 0, -1))
                            + ";IF(not HasStatus('RED_RAIN_DRAIN_1')):ApplyStatus(RED_RAIN_DRAIN_1,100,-1)"}, icon=ICON["RedRain"])
for n in range(1, 6):
    status(f"RED_RAIN_DRAIN_{n}", "Red Rain: drained", f"Hit Point maximum -{11 * n}. A Long Rest ends it.",
           {"StackId": "RED_RAIN_DRAIN", "StackPriority": str(n), "Boosts": f"IncreaseMaxHP(-{11 * n})",
            "StatusPropertyFlags": "RemoveOnLongRest", "StatusGroups": "SG_RemoveOnRespec"}, icon=ICON["RedRain"])

# -------------------------------------------------------------------------------------------------- Steal Immortality (9th)
SI_TEXT = ("As part of casting this spell, you must expend [1] Hit Point Dice or the spell automatically fails. Reaction: when a Celestial, Elemental, "
           "Fey, Fiend, or Undead creature you can see within range is reduced to 0 Hit Points, roll the Hit Point Dice expended and gain Temporary "
           "Hit Points equal to twice the roll's total. You gain that creature's type in addition to your own. While the spell lasts you have Immunity "
           "to the Poisoned condition and Resistance to Bludgeoning, Piercing and Slashing damage, and a benefit by type: Celestial: Resistance to "
           "Radiant and Necrotic, and flight. Elemental: Resistance to Acid, Cold, Fire, Lightning and Thunder. Fey: a Bonus Action to turn Invisible "
           "until your next turn, or to teleport up to 60 feet. Fiend: Resistance to Cold and Fire, and flight. Undead: Immunity to Necrotic damage "
           "and to the Charmed and Frightened conditions. You keep the type until you cast the spell again or are reduced to 0 Hit Points.")
SI_TYPES = {  # type: (boosts, extra text)
    "CELESTIAL": ("Resistance(Radiant,Resistant);Resistance(Necrotic,Resistant);UnlockSpell(Projectile_Fly)", "Resistance to Radiant and Necrotic damage; flight."),
    "ELEMENTAL": ("Resistance(Acid,Resistant);Resistance(Cold,Resistant);Resistance(Fire,Resistant);Resistance(Lightning,Resistant);Resistance(Thunder,Resistant)",
                  "Resistance to Acid, Cold, Fire, Lightning and Thunder damage."),
    "FEY": ("UnlockSpell(Shout_Apo_StealImmortality_Invisible);UnlockSpell(Target_Apo_StealImmortality_FeyStep)", "A Bonus Action to turn Invisible or teleport 60 feet."),
    "FIEND": ("Resistance(Cold,Resistant);Resistance(Fire,Resistant);UnlockSpell(Projectile_Fly)", "Resistance to Cold and Fire damage; flight."),
    "UNDEAD": ("Resistance(Necrotic,Immune);StatusImmunity(SG_Charmed);StatusImmunity(SG_Frightened)", "Immunity to Necrotic damage, and to Charmed and Frightened."),
}
SI_COND = ("not Dead(context.Observer) and not Self(context.Target,context.Observer) and HasDamageEffectFlag(DamageFlags.Hit) and "
           "HasFunctor(StatsFunctorType.DealDamage) and HasHPLessThan(1,context.Target) and not DistanceToEntityGreaterThan(90, context.ObserverPosition, context.Target) and ("
           + " or ".join(f"Tagged('{t}', context.Target)" for t in SI_TYPES) + ")")
for t, (boosts, text) in SI_TYPES.items():
    status(f"STEAL_IMMORTALITY_{t}", f"Steal Immortality ({t.capitalize()})",
           f"You have the {t.capitalize()} type as well as your own: Immunity to Poisoned, Resistance to Bludgeoning, Piercing and Slashing damage. {text} "
           "Ends when you cast the spell again or are reduced to 0 Hit Points.",
           {"StackId": "STEAL_IMMORTALITY", "Boosts": "StatusImmunity(SG_Poisoned);Resistance(Bludgeoning,Resistant);Resistance(Piercing,Resistant);"
                                                    f"Resistance(Slashing,Resistant);Tag({t});{boosts}",
            "RemoveConditions": "HasHPLessThan(1)", "RemoveEvents": "OnDamage", "StatusEffect": "@PTA_StealImmortality_StatusEffect"},
           icon=ICON["StealImmortality"])
for d in DICE:
    status(f"STEAL_IMMORTALITY_THP_{d}", "Steal Immortality", f"Temporary Hit Points: twice the roll of 9d{d}.",
           {"StackId": "STEAL_IMMORTALITY_THP", "OnApplyFunctors": f"RegainTemporaryHitPoints(18d{d})", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"},
           icon=ICON["StealImmortality"], comment="2 x 9d{d}: written as 18d{d} (same mean; dice can't be multiplied in a functor).".replace("{d}", str(d)))
    G.interrupt(f"Interrupt_Apo_StealImmortality_{d}", "Steal Immortality", "Take the creature's type and a share of its life.",
                {"InterruptContext": "OnCastHit", "InterruptContextScope": "Nearby", "Container": "YesNoDecision", "Conditions": SI_COND,
                 "Properties": f"ApplyStatus(OBSERVER_OBSERVER,STEAL_IMMORTALITY_THP_{d},100,0);"
                               + ";".join(f"IF(Tagged('{t}', context.Target)):ApplyStatus(OBSERVER_OBSERVER,STEAL_IMMORTALITY_{t},100,-1)" for t in SI_TYPES),
                 "Cost": f"ReactionActionPoint:1;SpellSlotsGroup:1:1:9;{hd(d)}:9", "Stack": "ApoStealImmortality", "InterruptDefaultValue": "Ask;Enabled"},
                icon=ICON["StealImmortality"])
SAVANT[9].append("Shout_StealImmortality")
spell("Shout_StealImmortality", {
    "SpellType": "Shout", "Level": "9", "SpellSchool": "Transmutation", "TargetConditions": "Self()", "ContainerSpells": ";".join(f"Shout_StealImmortality{d}" for d in DICE) + ";",
    "UseCosts": "ReactionActionPoint:1;SpellSlotsGroup:1:1:9;", "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;IsLinkedSpellContainer", "VerbalIntent": "Utility",
    "SpellStyleGroup": "Class", "Icon": ICON["StealImmortality"], "DescriptionParams": "9", "SpellProperties": ""}, using="Shout_Shield_Wizard",
      title="Steal Immortality", text=SI_TEXT, comment="Level 9 Sangromancy; a Reaction (an interrupt per die size). Trigger and component from community write-ups, unconfirmed.")
for d in DICE:
    spell(f"Shout_StealImmortality{d}", {"SpellContainerID": "Shout_StealImmortality", "ContainerSpells": "", "InterruptPrototype": f"Interrupt_Apo_StealImmortality_{d}",
                                          "UseCosts": f"ReactionActionPoint:1;SpellSlotsGroup:1:1:9;{hd(d)}:9", "SpellProperties": "",
                                          "PrepareEffect": "", "CastEffect": "@PTA_StealImmortality_CastEffect"},
          using="Shout_StealImmortality", title=f"Steal Immortality (d{d})")
spell("Shout_Apo_StealImmortality_Invisible", {"SpellType": "Shout", "Level": "0", "SpellSchool": "Illusion", "UseCosts": "BonusActionPoint:1", "TargetConditions": "Self()",
                                              "SpellProperties": "ApplyStatus(SELF,APO_STEAL_IMMORTALITY_INVISIBLE,100,2)", "SpellFlags": "IgnoreSilence;Invisible",
                                              "VerbalIntent": "Utility", "SpellStyleGroup": "Class", "Icon": "Spell_Illusion_GreaterInvisibility",
                                              "SpellAnimation": "9122eb08-93f1-4010-a275-f5ae3ec7c76e,,;,,;9fb11cca-02d4-4d2f-955f-2826c0553b17,,;5103d398-d8de-4aa4-9633-db2e1b7f6254,,;5301d674-b7da-47b6-b4cf-2802ba33a9e9,,;,,;86b3cf93-21fb-4a3d-bed9-97d0a567d084,,;,,;,,"},
      title="Fey Step: Vanish", text="Steal Immortality (Fey): become Invisible until the start of your next turn.")
status("APO_STEAL_IMMORTALITY_INVISIBLE", "Invisible", "Invisible until the start of your next turn.", {"StackId": "APO_STEAL_IMMORTALITY_INVISIBLE"},
       using="GREATER_INVISIBILITY", comment="As Ranger Nature's Veil: the 2024 Invisible condition doesn't end when you attack.")
spell("Target_Apo_StealImmortality_FeyStep", {"UseCosts": "BonusActionPoint:1", "Level": "0", "SpellStyleGroup": "Class"}, using="Target_MistyStep",
      title="Fey Step: Teleport", text="Steal Immortality (Fey): teleport up to 18 metres (60 feet) to an unoccupied space you can see.")


# ------------------------------------------------------------------------------------------------------------- lists + khn
def savant_lists():
    out = []
    for lvl, spells in sorted(SAVANT.items()):
        out.append(f'''                <node id="SpellList">
                    <attribute id="Comment" type="LSString" value="Sangromancy Savant L{lvl}: Grim Hollow level {lvl} Sangromancy spells (Sangromancer Savant picks at 13/15/17)"/>
                    <attribute id="Name" type="FixedString" value="SangromancySavantL{lvl}"/>
                    <attribute id="Spells" type="LSString" value="{';'.join(spells)}"/>
                    <attribute id="UUID" type="guid" value="{SAVANT_UUID[lvl]}"/>
                </node>
''')
    return out


SAVANT_UUID = {lvl: G.gid(f"list:SangromancySavantL{lvl}") for lvl in (7, 8, 9)}


def write_khn():
    """IsSangromancySpell(): dnd55e's whitelist (read from the released dnd55e) plus every spell entry this generator writes."""
    root = os.path.dirname(os.path.dirname(DND))   # .../<dnd55e>/Public/DnD2024_x -> .../<dnd55e>
    src = glob.glob(os.path.join(root, "Mods", "DnD2024*", "Scripts", "thoth", "helpers", "Wizard.khn"))
    assert src, f"dnd55e's Wizard.khn not found under {root}"
    text = open(src[0], encoding="utf-8").read()
    m = re.search(r"function IsSangromancySpell\(\)\s*return(.*?)\nend", text, re.S)
    assert m, "IsSangromancySpell() not found in dnd55e's Wizard.khn"
    theirs = re.findall(r"SpellId\('([^']+)'\)", m.group(1))
    # the Fey bonus actions, Creeping Death's Surge and the darts are features of a spell, not sangromancy spells with slot costs
    ids = theirs + [n for n in SPELLS if n not in theirs and not n.startswith(("Target_Apo_", "Shout_Apo_", "Projectile_SanguineFusillade_Dart"))]
    body = "\n    | ".join(f"SpellId('{i}')" for i in ids)
    os.makedirs(os.path.dirname(KHN), exist_ok=True)
    # EXACTLY dnd55e's file style: CRLF line endings and no comments. A .khn that starts with `//` comment lines and uses LF crashed the
    # game while it loaded modules (found by bisecting the pak, 2026-10-12: the same file in dnd55e's style - even redefining
    # IsSangromancySpell under its real name - loads). The provenance of this file is this docstring and .gitattributes.
    open(KHN, "w", encoding="utf-8", newline="").write(
        "function IsSangromancySpell()\r\n    return " + "\r\n    | ".join(f"SpellId('{i}')" for i in ids) + "\r\nend\r\n")
    return len(theirs), len(ids) - len(theirs)


def resolve_effects():
    """'@PTA_X' effect names -> their MultiEffectInfo UUIDs from vfx_generated.json (built by bg3_fx_build); fields stay empty until built."""
    import json
    gen_path = os.path.join(REPO, "Scripts", "data", "vfx_generated.json")
    gen = json.load(open(gen_path, encoding="utf-8")) if os.path.exists(gen_path) else {}
    missing = set()

    def sub(m):
        n = m.group(1)
        if n in gen:
            return gen[n]["uuid"]
        missing.add(n)
        return ""
    for lst in (G.SP, G.S):
        for i, e in enumerate(lst):
            lst[i] = re.sub(r'@(PTA_\w+)', sub, e)
    return missing


if __name__ == "__main__":
    miss = resolve_effects()
    G.write_stats("Sangromancy", "gen_sangromancy.py", "Grim Hollow Sangromancy 7-9")
    G._between(os.path.join(PUB, "Lists", "SpellLists.lsx"), savant_lists())
    G.patch_loca()
    n_theirs, n_ours = write_khn()
    print(f"{len(G.SP)} spells, {len(G.S)} statuses, {len(G.I)} interrupts; IsSangromancySpell(): {n_theirs} of dnd55e's + {n_ours} ours"
          + (f"; effects not built yet: {', '.join(sorted(miss))}" if miss else ""))
