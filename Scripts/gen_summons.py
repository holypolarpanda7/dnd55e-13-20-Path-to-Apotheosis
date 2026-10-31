"""PHB 2024 summon spells for issue #10, as new creatures (dnd55e-style): each creature form is its own root template
(RootTemplates/Apotheosis_Summons.lsf) with its own Character stats, and the spell level is applied on summoning as a
per-level status (the dnd55e Spiritual Weapon pattern): your Proficiency Bonus, your spell attack modifier and save
DC, and the stat block's "+ spell level" rows (AC, HP, damage, Multiattack).

Pass 1: Summon Construct (Clay/Metal/Stone). (Summon Elemental: dnd55e's own, since 2026-10-03.)
Pass 2: Mordenkainen's Faithful Hound, Bigby's Hand, Animate Objects (with Lua in Summons.lua).

AC: the engine adds the Dexterity modifier to the `Armor` stat, so Armor = stat-block AC - Dex modifier.

Attacks: the Slam is the creature's unarmed attack, so the engine's Extra Attack gives the Multiattack. The creature
attacks with an ability whose modifier is +0 (Wisdom), so with your PB and spellcasting modifier added the attack
bonus equals your spell attack modifier.

Models: every creature's look comes from MODELS below (a base-game template for now). Swap a parent to give a form a
new model or effects - nothing else references it.

Spell lists: dnd55e's class lists are overridden by UUID with their current contents plus these spells (re-run after
syncing dnd55e), and the Apotheosis-owned lists (Apotheosis Ranger SLevel 4) get them too; WizardUpToL7-9 are built from the Wizard lists by gen_learn_lists.py.

Owns Stats/Generated/Data/{Character,Status,Spell,Passive,Interrupt}_Summons.txt and RootTemplates/Apotheosis_Summons.lsf.
Run: python3 Scripts/gen_summons.py
"""
import glob
import os
import re

from gen_common import Gen, PUB, DND, TARGET_ANIM

G = Gen("summons", "SUMMONS 10")
SLOT = lambda n: f"SpellSlotsGroup:1:1:{n}"
RES_TYPES = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison", "Psychic",
             "Radiant", "Slashing", "Thunder"]
PB = "ProficiencyBonusOverride(Owner.LevelMapValue(StandardProficiencyBonusScale))"
CASTER = f"{PB};RollBonus(Attack,Owner.SpellCastingAbilityModifier);SpellSaveDC(Owner.SpellCastingAbilityModifier)"
SUMMON_ANIM = "6f42f5f3-7a5a-4441-a02e-71b0450ac4b7,,;,,;c0513845-6e0e-42e8-9a8c-baa5e2b6ead6,,;fbf20742-9dbf-475b-9ff5-42e4b08064ad,,;42aaefdc-cf9b-4249-b159-285041851f69,,;,,;20e11c98-fff9-4417-88de-5bcc2368a1bd,,;,,;,,"
EXTRA_ATTACK = {1: "", 2: "ExtraAttack", 3: "ExtraAttack_2", 4: "ExtraAttack_3"}

# Placeholder models: base-game templates the new creatures inherit their look, sounds and effects from.
MODELS = {
    "ConstructClay": "6597824a-fc73-474a-b594-b3bbd8591016",   # Construct_FleshGolem
    "ConstructMetal": "f1662ccf-44cb-4e27-8810-ca2d3eea2adf",  # dnd55e AnimatedArmor_SteelDefender
    "ConstructStone": "b5bd29ba-8105-4123-920f-a2c64a4e1dfc",  # Myrmidon_Earth_ConjureElemental
}


def resistances(res=(), immune=()):
    return {f"{t}Resistance": "Immune" if t in immune else "Resistant" if t in res else "" for t in RES_TYPES}


def slam(name, title, dice, dtype, icon, text, base_level):
    """The Slam: `dice` + the spell's level, one variant per level (`name`_N) that the creature's level status
    unlocks. Not a DamageBonus boost (it would add to everything the creature deals, e.g. Heated Body's retaliation)
    and not a condition on the caster's level status (a summon's attack runs with you, the summoner, as its source:
    found 2026-10-02)."""
    for lvl in range(base_level, 10):
        G.spell(f"{name}_{lvl}", title, text, {
            "SpellType": "Target", "SpellRoll": "Attack(AttackType.MeleeUnarmedAttack)",
            "SpellSuccess": f"DealDamage({dice}+{lvl},{dtype},Magical)", "TooltipDamageList": f"DealDamage({dice}+{lvl},{dtype})",
            "TooltipAttackSave": "MeleeUnarmedAttack", "DamageType": dtype, "VerbalIntent": "Damage"},
            using="Target_UnarmedAttack", icon=icon)


def level_status(kind, form, lvl):
    return f"APO_{kind.upper()}SPIRIT_{form.upper()}_{lvl}"


def spirit(kind, form, title, char, skills, base_level, ac_step, hp_step, slam_name, statuses_extra=""):
    """One summonable form: Character stats, root template and the per-level statuses (levels base..9)."""
    stats = f"Apo_{kind}Spirit_{form}"
    G.character(stats, char, using="_Base")
    tpl = G.template(f"{kind}{form}", stats, MODELS[f"{kind}{form}"], stats, title, skills=skills, level=9,
                     spellset="CommonSummonActions")
    levels = {}
    for lvl in range(base_level, 10):
        st = level_status(kind, form, lvl)
        up = lvl - base_level
        extra = EXTRA_ATTACK[lvl // 2]
        G.status(st, f"Level {lvl} {title}", f"Summoned with a level {lvl} spell slot: uses your Proficiency Bonus, spell attack modifier and spell save DC.", {
            "Boosts": f"{CASTER};AC({up});IncreaseMaxHP({hp_step * up});UnlockSpell({slam_name}_{lvl})" + statuses_extra.format(lvl=lvl),
            "Passives": extra or None, "StackId": f"APO_{kind.upper()}SPIRIT_LEVEL",
            "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"}, icon="Spell_Conjuration_ConjureElemental")
        levels[lvl] = st
    return tpl, levels


def summon_spell(root, title, text, school, base_level, forms, icon, radius="18", fields=None):
    """Linked container `root` with one child per form; each child has upcast variants base+1..9 (dnd55e/base
    Spiritual Weapon layout: Child_N with RootSpellID=Child, SpellContainerID=root, PowerLevel=N)."""
    children = [f"{root}_{f}" for f, *_ in forms]
    common = {"SpellType": "Target", "Level": str(base_level), "SpellSchool": school, "TargetRadius": radius,
              "UseCosts": "ActionPoint:1;" + SLOT(base_level), "VerbalIntent": "Summon",
              "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;CannotTargetItems;CannotTargetCharacter;IsConcentration",
              "SpellAnimation": SUMMON_ANIM,
              "PrepareEffect": "7e42016a-29f9-4922-908b-dbf010dff168", "CastEffect": "ebd046f7-066f-4acf-b671-dd451201c58b",
              "PositionEffect": "37218caf-c844-479e-830e-d4c3fc2b9591", "PrepareSound": "Spell_Prepare_ClericSummon_Gen",
              "PrepareLoopSound": "Spell_Loop_ClericSummon_Gen", "CastSound": "Spell_Cast_Summon_PlanarAlly_L6to8",
              "MemoryCost": "1", **(fields or {})}
    G.spell(root, title, text, {**common, "ContainerSpells": ";".join(children),
                                "SpellFlags": common["SpellFlags"] + ";IsLinkedSpellContainer"}, icon=icon)
    for (form, ftitle, tpl, levels, extra_status), child in zip(forms, children):
        props = lambda lvl: (f"GROUND:Summon({tpl},-1,Projectile_AiHelper_Summon_Strong,,'{root}Stack',{levels[lvl]},"
                             f"UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK{',' + extra_status if extra_status else ''})")
        G.spell(child, f"{title}: {ftitle}", text, {
            **common, "SpellContainerID": root, "SpellProperties": props(base_level),
            "TargetConditions": f"CanStand('{tpl}') and not Character() and not Self()"}, icon=icon)
        for lvl in range(base_level + 1, 10):
            G.spell(f"{child}_{lvl}", f"{title}: {ftitle}", text, {
                "SpellProperties": props(lvl), "UseCosts": "ActionPoint:1;" + SLOT(lvl), "RootSpellID": child,
                "PowerLevel": str(lvl)}, using=child, icon=icon)
    return root


# Summon Elemental: dnd55e's own Target_SummonElemental (4.12.18.1+) is used - deferred to dnd55e 2026-10-03; its
# 7th-9th level variants come from gen_upcasts.py. Target_ApoSummonElemental is retired (RETIRED below).

# ================================================================ Summon Construct (level 4)
CONSTRUCT_TEXT = ("You call forth the spirit of a Construct made of Clay, Metal or Stone (Concentration, up to 1 hour). It uses your "
                  "Proficiency Bonus, spell attack modifier and spell save DC; AC 13 + the spell's level, 40 HP + 15 for each level "
                  "above 4, and a number of Slam attacks equal to half the spell's level (1d8 + 4 + the spell's level). Clay: Berserk "
                  "Lashing. Metal: Heated Body. Stone: Stony Lethargy.")
SLAM_C = "Target_ApoConstructSpirit_Slam"
slam(SLAM_C, "Slam", "1d8+4", "Bludgeoning", "Action_Slam",
     "Melee attack with your spell attack modifier: 1d8 + 4 + the spell's level Bludgeoning damage.", 4)

# Clay: Berserk Lashing (reaction: Slam a creature that damaged it, if it can reach)
for lvl in range(4, 10):  # one per level: it makes that level's Slam (the clay level status unlocks it)
    # the reaction's Slam costs the reaction, not an action: Extra Attack keys on an action cost and would
    # otherwise queue a free Slam after every Berserk Lashing (seen 2026-10-03)
    G.spell(f"{SLAM_C}_{lvl}_Reaction", "Berserk Lashing", "The spirit Slams the creature that damaged it.",
            {"UseCosts": "ReactionActionPoint:1"}, using=f"{SLAM_C}_{lvl}")
    G.interrupt(f"Interrupt_ApoBerserkLashing_{lvl}", "Berserk Lashing",
                "When a creature damages the spirit, it makes a Slam attack against that creature as a reaction.", {
                    "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
                    "Conditions": "IsAbleToReact(context.Observer) and Enemy(context.Source,context.Observer) and HasFunctor(StatsFunctorType.DealDamage) and IsHit() and not AnyEntityIsItem() and not DistanceToEntityGreaterThan(2, context.ObserverPosition, context.Source) and HasLastAttackTriggered()",
                    "Properties": f"UseSpell(SWAP,{SLAM_C}_{lvl}_Reaction,true,true,true)", "Cost": "ReactionActionPoint:1",
                    "Stack": "ApoBerserkLashing", "InterruptDefaultValue": "Enabled"}, icon="Action_Slam")
G.passive("Apo_ConstructSpirit_BerserkLashing", "Berserk Lashing",
          "Reaction: when a creature damages the spirit, the spirit makes a Slam attack against it.", icon="Action_Slam")
# Metal: Heated Body (a creature that hits it with a melee attack takes 1d10 Fire)
G.passive("Apo_ConstructSpirit_HeatedBody", "Heated Body",
          "A creature that hits the spirit with a melee attack takes 1d10 Fire damage.", {
              "StatsFunctorContext": "OnAttacked",
              "Conditions": "IsMeleeAttack() and HasDamageEffectFlag(DamageFlags.Hit) and not SpellTypeIs(SpellType.Throw)",
              "StatsFunctors": "DealDamage(SWAP,1d10,Fire,Magical)"}, icon="Spell_Evocation_FireShield_Warm")
# Stone: Stony Lethargy (a creature starting its turn within 10 ft: Wisdom save or no Opportunity Attacks, half Speed)
G.status("APO_STONY_LETHARGY", "Stony Lethargy",
         "Speed halved and can't make Opportunity Attacks (reactions) until the start of its next turn.", {
             "Boosts": "ActionResourceMultiplier(Movement,50,0);ActionResourceBlock(ReactionActionPoint)",
             "StackId": "APO_STONY_LETHARGY", "TickType": "StartTurn"}, icon="Spell_Transmutation_Slow")
G.status("APO_STONY_LETHARGY_NEAR", "Within reach of Stony Lethargy", None, {
    "StackId": "APO_STONY_LETHARGY_NEAR", "TickType": "StartTurn",
    "TickFunctors": "IF(not SavingThrow(Ability.Wisdom, SourceSpellDC())):ApplyStatus(APO_STONY_LETHARGY,100,1)",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"})
G.status("APO_STONY_LETHARGY_AURA", "Stony Lethargy",
         "A creature that starts its turn within 10 feet of the spirit makes a Wisdom saving throw against your spell save DC; on a failure its Speed is halved and it can't make Opportunity Attacks until the start of its next turn.", {
             "AuraRadius": "3", "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_STONY_LETHARGY_NEAR)",
             "StackId": "APO_STONY_LETHARGY_AURA", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"},
         icon="Spell_Transmutation_Slow")

con_forms = []
for mat, passive, extra_status in (("Clay", "Apo_ConstructSpirit_BerserkLashing", None),
                                   ("Metal", "Apo_ConstructSpirit_HeatedBody", None),
                                   ("Stone", None, "APO_STONY_LETHARGY_AURA")):
    char = {"Level": "9", "Strength": "18", "Dexterity": "10", "Constitution": "18", "Intelligence": "14", "Wisdom": "11",
            "Charisma": "5", "Armor": "17", "ArmorType": "None", "Vitality": "40",
            "ActionResources": "ActionPoint:1;BonusActionPoint:1;Movement:9;ReactionActionPoint:1",
            "UnarmedAttackAbility": "Wisdom", "UnarmedRangedAttackAbility": "Wisdom", "SpellCastingAbility": "Wisdom",
            "DarkvisionRange": "18",
            "Passives": "AttackOfOpportunity;Darkvision;DarknessRules;ShortResting" + (f";{passive}" if passive else ""),
            "PersonalStatusImmunities": "SG_Charmed;SG_Frightened;FEARED;SG_Paralyzed;SG_Poisoned",
            "DifficultyStatuses": "STATUS_EASY:PLAYER_BONUSES_EASYMODE", **resistances(("Poison",))}
    tpl, levels = spirit("Construct", mat, f"{mat} Construct Spirit", char, ["Shout_Dodge"], 4, 1, 15, SLAM_C,
                         ";UnlockInterrupt(Interrupt_ApoBerserkLashing_{lvl})" if mat == "Clay" else "")
    con_forms.append((mat, mat, tpl, levels, extra_status))
summon_spell("Target_ApoSummonConstruct", "Summon Construct", CONSTRUCT_TEXT, "Conjuration", 4, con_forms,
             "Spell_Conjuration_FindFamiliar")

# ================================================================ pass 2 (Summons.lua drives the parts stats can't)
MODELS.update({
    "FaithfulHound": "da1c7ba6-e01d-4a88-a7b1-0b0447b0c60a",   # LOW_Dog_Ghost_Houndmasters (a phantom dog)
    "BigbysHand": "eddf2b83-21d3-4d6f-b958-c30f00dbbb92",      # the Mage Hand summon
    "AnimatedObjectMedium": "2facfc7e-5fe9-4a8d-9fec-dcb5ce6c5ebf",  # AnimatedArmor
    "AnimatedObjectLarge": "6597824a-fc73-474a-b594-b3bbd8591016",   # Construct_FleshGolem
    "AnimatedObjectHuge": "4d5fbc43-408c-4ec8-acf6-9c8d8aa456d6",    # AdamantineGolem_A
})
OBJECT_IMMUNE = "SG_Charmed;SG_Frightened;FEARED;SG_Paralyzed;SG_Poisoned;SG_Prone;SG_Stunned"
BASE_CHAR = {"Level": "9", "Strength": "10", "Dexterity": "10", "Constitution": "10", "Intelligence": "10",
             "Wisdom": "10", "Charisma": "10", "ArmorType": "None", "UnarmedAttackAbility": "Wisdom",
             "UnarmedRangedAttackAbility": "Wisdom", "SpellCastingAbility": "Wisdom",
             "DifficultyStatuses": "STATUS_EASY:PLAYER_BONUSES_EASYMODE"}

# ---------------------------------------------------------------- Mordenkainen's Faithful Hound (level 4)
G.character("Apo_FaithfulHound", {**BASE_CHAR, "Armor": "10", "Vitality": "1", "DarkvisionRange": "9",
                                   "ActionResources": "Movement:0", "Passives": "Darkvision",
                                   "PersonalStatusImmunities": OBJECT_IMMUNE, **resistances((), RES_TYPES)}, using="_Base")
HOUND_TPL = G.template("FaithfulHound", "Apo_FaithfulHound", MODELS["FaithfulHound"], "Apo_FaithfulHound",
                       "Faithful Hound", skills=[], level=9, spellset="")
G.status("APO_FAITHFUL_HOUND", "Faithful Hound",
         "A phantom watchdog: intangible and invulnerable. At the start of your turns it bites one enemy within 5 feet of it (Dexterity save or 4d8 Force damage).", {
             "Boosts": f"{CASTER};Invulnerable()", "StackId": "APO_FAITHFUL_HOUND",
             "StatusPropertyFlags": "DisableCombatlog;ApplyToDead;IsInvulnerable"}, icon="Spell_Conjuration_FindFamiliar_Dog")
G.status("APO_FAITHFUL_HOUND_OWNER", "Faithful Hound", "Your Faithful Hound keeps watch; you can take a Magic action to move it up to 30 feet.", {
    "Boosts": "UnlockSpell(Target_ApoFaithfulHound_Move)", "StackId": "APO_FAITHFUL_HOUND_OWNER",
    "StatusPropertyFlags": "DisableCombatlog"}, icon="Spell_Conjuration_FindFamiliar_Dog")
G.status("APO_FAITHFUL_HOUND_BITE", "Faithful Hound's bite", None, {
    "OnApplyRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())", "OnApplySuccess": "DealDamage(4d8,Force,Magical)",
    "StackId": "APO_FAITHFUL_HOUND_BITE", "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"},
         comment="Summons.lua applies it at the start of the caster's turn (source = the caster: your spell save DC).")
G.spell("Target_ApoFaithfulHound", "Mordenkainen's Faithful Hound",
        "You conjure a phantom watchdog for 8 hours. It is invulnerable, and at the start of each of your turns it bites one enemy within 5 feet of it: Dexterity saving throw or 4d8 Force damage. You can take a Magic action to move it up to 30 feet.", {
            "SpellType": "Target", "Level": "4", "SpellSchool": "Conjuration", "TargetRadius": "9",
            "TargetConditions": f"CanStand('{HOUND_TPL}') and not Character() and not Self()",
            "SpellProperties": f"GROUND:Summon({HOUND_TPL},4800,,,'ApoFaithfulHoundStack',APO_FAITHFUL_HOUND,UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK);GROUND:ApplyStatus(SELF,APO_FAITHFUL_HOUND_OWNER,100,4800)",
            "UseCosts": "ActionPoint:1;" + SLOT(4), "VerbalIntent": "Summon",
            "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;CannotTargetItems;CannotTargetCharacter",
            "SpellAnimation": SUMMON_ANIM,
            "MemoryCost": "1"}, icon="Spell_Conjuration_FindFamiliar_Dog")
G.spell("Target_ApoFaithfulHound_Move", "Move Faithful Hound", "Move your Faithful Hound up to 30 feet.", {
    "SpellType": "Target", "TargetRadius": "18", "TargetConditions": "not Character() and not Self()",
    "UseCosts": "ActionPoint:1", "SpellFlags": "CannotTargetItems;CannotTargetCharacter", "VerbalIntent": "Utility"},
        icon="Spell_Conjuration_FindFamiliar_Dog", comment="Summons.lua teleports the hound (clamped to 9 m from where it was).")

# ---------------------------------------------------------------- Bigby's Hand (level 5)
HAND_TEXT = ("A Large hand of magical energy (AC 20, Hit Points equal to your Hit Point maximum) that acts right after you "
             "and moves up to 60 feet: Clenched Fist (melee spell attack, 5d8 Force), Forceful Hand (Strength save or "
             "pushed 5 feet + 5 x your spellcasting modifier), Grasping Hand (Dexterity save or Grappled; then Crush: 4d6 + "
             "your spellcasting modifier Bludgeoning) or Interposing Hand (you have Half Cover). Concentration, up to 1 minute. "
             "Higher slots: Clenched Fist +2d8 and Crush +2d6 per level above 5.")
G.status("APO_BIGBYS_HAND_GRASPED", "Grasped by Bigby's Hand",
         "Grappled: Speed 0 and Disadvantage on attack rolls. At the end of each of its turns it makes a Strength (Athletics) check against the caster's spell save DC to escape.", {
             "Boosts": "ActionResourceBlock(Movement);Disadvantage(AttackRoll)", "StackId": "APO_BIGBYS_HAND_GRASPED",
             "TickType": "EndTurn", "OnTickRoll": "SkillCheck(Skill.Athletics, SourceSpellDC())",
             "OnTickSuccess": "RemoveStatus(APO_BIGBYS_HAND_GRASPED)", "StatusGroups": "SG_Condition"},
         icon="Spell_BigbysHand" )
G.status("APO_BIGBYS_HAND_PUSHED", "Forceful Hand", "Pushed away by Bigby's Hand.", {
    "StackId": "APO_BIGBYS_HAND_PUSHED", "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"},
    icon="Spell_BigbysHand", comment="Summons.lua pushes it 5 ft + 5 ft x the caster's spellcasting modifier: Force() takes "
                                     "only constants or named distances, not a formula.")
G.status("APO_BIGBYS_HAND_INTERPOSING", "Interposing Hand", "Half Cover: +2 to AC and Dexterity saving throws until the hand's next turn.", {
    "Boosts": "AC(2);RollBonus(SavingThrow,2,Dexterity)", "StackId": "APO_BIGBYS_HAND_INTERPOSING"}, icon="Spell_BigbysHand")
HAND_ICON = "Spell_BigbysHand"
# The touch effects build on Target_UnarmedAttack: with plain 1.5 m Target spells the Large floating hand never
# reached a creature it stood next to ("target" failure, 2026-10-03); the unarmed attack's melee setup does.
TOUCH = {"SpellProperties": "", "SpellSuccess": "", "SpellFail": "", "UseCosts": "ActionPoint:1"}
for lvl in range(5, 10):
    up = lvl - 5
    G.spell(f"Target_ApoBigbysHand_Fist_{lvl}", "Clenched Fist", "Melee spell attack: Force damage.", {
        **TOUCH, "TargetConditions": "Character() and not Self() and not Dead()",
        "SpellRoll": "Attack(AttackType.MeleeSpellAttack)", "SpellSuccess": f"DealDamage({5 + 2 * up}d8,Force,Magical)",
        "TooltipDamageList": f"DealDamage({5 + 2 * up}d8,Force)", "TooltipAttackSave": "MeleeSpellAttack", "DamageType": "Force",
        "VerbalIntent": "Damage"}, using="Target_UnarmedAttack", icon=HAND_ICON)
    G.spell(f"Target_ApoBigbysHand_Crush_{lvl}", "Crush", "Crush the creature the hand grasps: Bludgeoning damage.", {
        **TOUCH, "TargetConditions": "HasStatus('APO_BIGBYS_HAND_GRASPED') and not Dead()", "SpellRoll": "",
        "SpellProperties": f"DealDamage({4 + 2 * up}d6+SpellCastingAbilityModifier,Bludgeoning,Magical)",
        "TooltipDamageList": f"DealDamage({4 + 2 * up}d6+SpellCastingAbilityModifier,Bludgeoning)", "TooltipAttackSave": "",
        "DamageType": "Bludgeoning", "SpellFlags": "IsMelee;IsHarmful", "VerbalIntent": "Damage"}, using="Target_UnarmedAttack",
        icon=HAND_ICON, comment="SpellCastingAbilityModifier: a summon's damage runs with the summoner as source (2026-10-02/03).")
G.spell("Target_ApoBigbysHand_Forceful", "Forceful Hand", "Strength saving throw or pushed 5 feet + 5 feet x your spellcasting modifier.", {
    **TOUCH, "TargetConditions": "Character() and not Self() and not Dead() and TargetSizeEqualOrSmaller(Size.Huge)",
    "SpellRoll": "not SavingThrow(Ability.Strength, SourceSpellDC())", "SpellSuccess": "ApplyStatus(APO_BIGBYS_HAND_PUSHED,100,0)",
    "TooltipAttackSave": "Strength", "TooltipDamageList": "", "SpellFlags": "IsMelee;IsHarmful", "VerbalIntent": "Control"},
    using="Target_UnarmedAttack", icon=HAND_ICON)
G.spell("Target_ApoBigbysHand_Grasping", "Grasping Hand", "Dexterity saving throw or Grappled by the hand.", {
    **TOUCH, "TargetConditions": "Character() and not Self() and not Dead() and TargetSizeEqualOrSmaller(Size.Huge)",
    "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())", "SpellSuccess": "ApplyStatus(APO_BIGBYS_HAND_GRASPED,100,10)",
    "TooltipAttackSave": "Dexterity", "TooltipDamageList": "", "TooltipStatusApply": "ApplyStatus(APO_BIGBYS_HAND_GRASPED,100,10)",
    "SpellFlags": "IsMelee;IsHarmful", "VerbalIntent": "Control"}, using="Target_UnarmedAttack", icon=HAND_ICON)
G.spell("Target_ApoBigbysHand_Interposing", "Interposing Hand", "An ally gains Half Cover (+2 AC and Dexterity saves) until the hand's next turn.", {
    "SpellType": "Target", "TargetRadius": "18", "TargetConditions": "Character() and Ally() and not Self() and not Dead()",
    "SpellProperties": "ApplyStatus(APO_BIGBYS_HAND_INTERPOSING,100,1)", "TooltipStatusApply": "ApplyStatus(APO_BIGBYS_HAND_INTERPOSING,100,1)",
    "UseCosts": "ActionPoint:1", "VerbalIntent": "Buff"}, icon=HAND_ICON)
G.character("Apo_BigbysHand", {**BASE_CHAR, "Armor": "20", "Vitality": "1", "DarkvisionRange": "18",
                                "ActionResources": "ActionPoint:1;Movement:18", "Passives": "Darkvision",
                                "PersonalStatusImmunities": OBJECT_IMMUNE,
                                **resistances((), ("Poison", "Psychic"))}, using="_Base")
HAND_TPL = G.template("BigbysHand", "Apo_BigbysHand", MODELS["BigbysHand"], "Apo_BigbysHand", "Bigby's Hand",
                      skills=["Target_ApoBigbysHand_Forceful", "Target_ApoBigbysHand_Grasping", "Target_ApoBigbysHand_Interposing"],
                      level=9, spellset="")
hand_levels = {}
for lvl in range(5, 10):
    st = f"APO_BIGBYSHAND_{lvl}"
    G.status(st, f"Level {lvl} Bigby's Hand", "Uses your spell attack modifier and spell save DC; its Hit Points equal your Hit Point maximum.", {
        "Boosts": f"{CASTER};UnlockSpell(Target_ApoBigbysHand_Fist_{lvl});UnlockSpell(Target_ApoBigbysHand_Crush_{lvl})",
        "StackId": "APO_BIGBYSHAND_LEVEL", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"}, icon=HAND_ICON,
        comment="Summons.lua raises the hand's maximum HP to the caster's.")
    hand_levels[lvl] = st
G.spell("Target_ApoBigbysHand", "Bigby's Hand", HAND_TEXT, {
    "SpellType": "Target", "Level": "5", "SpellSchool": "Evocation", "TargetRadius": "36",
    "TargetConditions": f"CanStand('{HAND_TPL}') and not Character() and not Self()",
    "SpellProperties": f"GROUND:Summon({HAND_TPL},10,,,'ApoBigbysHandStack',{hand_levels[5]},UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK)",
    "UseCosts": "ActionPoint:1;" + SLOT(5), "VerbalIntent": "Summon", "MemoryCost": "1",
    "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;CannotTargetItems;CannotTargetCharacter;IsConcentration",
    "SpellAnimation": SUMMON_ANIM},
    icon=HAND_ICON)
for lvl in range(6, 10):
    G.spell(f"Target_ApoBigbysHand_{lvl}", "Bigby's Hand", HAND_TEXT, {
        "SpellProperties": f"GROUND:Summon({HAND_TPL},10,,,'ApoBigbysHandStack',{hand_levels[lvl]},UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK)",
        "UseCosts": "ActionPoint:1;" + SLOT(lvl), "RootSpellID": "Target_ApoBigbysHand", "PowerLevel": str(lvl)},
        using="Target_ApoBigbysHand", icon=HAND_ICON)

# ---------------------------------------------------------------- Animate Objects (level 5)
OBJ_SIZES = [  # size, Vitality, damage dice at level 5 (count, die), + modifier, cost in objects
    ("Medium", 10, (1, 4), False, 1),
    ("Large", 20, (2, 6), True, 2),
    ("Huge", 40, (2, 12), True, 3),
]
ANIMATE_TEXT = ("Up to your spellcasting modifier's worth of nonmagical objects (Medium or smaller: 1, Large: 2, Huge: 3) become "
                "Animated Objects (AC 15; 10/20/40 HP) that act right after you. Slam: your spell attack modifier; 1d4 + 3 / "
                "2d6 + 3 + your spellcasting modifier / 2d12 + 3 + your spellcasting modifier Force damage, +1d4/1d6/1d12 per "
                "slot level above 5. When one drops to 0 Hit Points it reverts to its object. Concentration, up to 1 minute.")
for size, hp, (n, die), plus_mod, cost in OBJ_SIZES:
    stats = f"Apo_AnimatedObject_{size}"
    G.character(stats, {**BASE_CHAR, "Strength": "16", "Intelligence": "3", "Wisdom": "3", "Charisma": "1",
                        "UnarmedAttackAbility": "Dexterity", "UnarmedRangedAttackAbility": "Dexterity",
                        "SpellCastingAbility": "Dexterity", "Armor": "15", "Vitality": str(hp), "DarkvisionRange": "9",
                        "ActionResources": "ActionPoint:1;BonusActionPoint:1;Movement:9;ReactionActionPoint:1",
                        "Passives": "AttackOfOpportunity;Darkvision;DarknessRules",
                        "PersonalStatusImmunities": "SG_Charmed;SG_Frightened;FEARED;SG_Paralyzed;SG_Poisoned",
                        **resistances((), ("Poison", "Psychic"))}, using="_Base")
    tpl = G.template(f"AnimatedObject{size}", stats, MODELS[f"AnimatedObject{size}"], stats, f"Animated Object ({size})",
                     skills=["Shout_Dodge"], level=9, spellset="CommonSummonActions")
    for lvl in range(5, 10):
        dice = f"{n + (lvl - 5)}d{die}+3" + ("+SpellCastingAbilityModifier" if plus_mod else "")
        slam_name = f"Target_ApoAnimatedObject_Slam_{size}_{lvl}"
        G.spell(slam_name, "Slam", "Melee attack with your spell attack modifier: Force damage.", {
            "SpellType": "Target", "SpellRoll": "Attack(AttackType.MeleeUnarmedAttack)",
            "SpellSuccess": f"DealDamage({dice},Force,Magical)", "TooltipDamageList": f"DealDamage({dice},Force)",
            "TooltipAttackSave": "MeleeUnarmedAttack", "DamageType": "Force", "VerbalIntent": "Damage"},
            using="Target_UnarmedAttack", icon="Action_Slam")
        st = f"APO_ANIMATEDOBJECT_{size.upper()}_{lvl}"
        G.status(st, f"Level {lvl} Animated Object", "Uses your Proficiency Bonus and spell attack modifier.", {
            "Boosts": f"{CASTER};UnlockSpell({slam_name})", "StackId": "APO_ANIMATEDOBJECT_LEVEL",
            "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;ApplyToDead"}, icon="Spell_Necromancy_AnimateDead_HigherLevel")
        G.spell(f"Target_ApoAnimatedObject_Spawn_{size}_{lvl}", f"Animated Object ({size})", "Summons.lua casts this where an animated object stood.", {
            "SpellType": "Target", "TargetRadius": "100", "TargetConditions": "not Character()",
            "SpellProperties": f"GROUND:Summon({tpl},10,,,,{st},UNSUMMON_ABLE,SHADOWCURSE_SUMMON_CHECK)",
            "UseCosts": "", "SpellFlags": "IgnoreVisionBlock;CannotTargetCharacter;CannotTargetItems",
            "SpellAnimation": SUMMON_ANIM},  # not ImmediateCast: GROUND:Summon never happens in one (2026-10-03)
            icon="Spell_Necromancy_AnimateDead_HigherLevel")
G.status("APO_ANIMATE_OBJECTS", "Animate Objects", "This object is being animated.", {
    "StackId": "APO_ANIMATE_OBJECTS", "StatusPropertyFlags": "DisableOverhead;ApplyToDead"}, icon="Spell_Necromancy_AnimateDead_HigherLevel",
         comment="Marker per slot level (APO_ANIMATE_OBJECTS_N): Summons.lua hides the object and summons its Animated Object.")
for lvl in range(5, 10):
    G.status(f"APO_ANIMATE_OBJECTS_{lvl}", "Animate Objects", None, {}, using="APO_ANIMATE_OBJECTS")
G.spell("Target_ApoAnimateObjects", "Animate Objects", ANIMATE_TEXT, {
    "SpellType": "Target", "Level": "5", "SpellSchool": "Transmutation", "TargetRadius": "36", "AmountOfTargets": "5",
    "TargetConditions": "Item() and not Dead() and TargetSizeEqualOrSmaller(Size.Huge)",
    "SpellProperties": "ApplyStatus(APO_ANIMATE_OBJECTS_5,100,1)", "UseCosts": "ActionPoint:1;" + SLOT(5),
    "VerbalIntent": "Summon", "MemoryCost": "1",
    "SpellFlags": "HasVerbalComponent;HasSomaticComponent;IsSpell;IsConcentration",
    "SpellAnimation": TARGET_ANIM}, icon="Spell_Necromancy_AnimateDead_HigherLevel")
for lvl in range(6, 10):
    G.spell(f"Target_ApoAnimateObjects_{lvl}", "Animate Objects", ANIMATE_TEXT, {
        "SpellProperties": f"ApplyStatus(APO_ANIMATE_OBJECTS_{lvl},100,1)", "UseCosts": "ActionPoint:1;" + SLOT(lvl),
        "RootSpellID": "Target_ApoAnimateObjects", "PowerLevel": str(lvl)}, using="Target_ApoAnimateObjects",
        icon="Spell_Necromancy_AnimateDead_HigherLevel")

# ================================================================ spell lists
# (class, spell level) -> spells. dnd55e lists named "5.5 <Class> SLevel <N>..." (incl. "to N"/"to Bard" copies).
CLASS_ADDS = {
    ("Wizard", 4): ["Target_ApoSummonConstruct", "Target_ApoFaithfulHound"],
    ("Bard", 5): ["Target_ApoAnimateObjects"],
    ("Sorcerer", 5): ["Target_ApoAnimateObjects", "Target_ApoBigbysHand"],
    ("Wizard", 5): ["Target_ApoAnimateObjects", "Target_ApoBigbysHand"],
}
APO_ADDS = {  # Apotheosis-owned lists, by name
    "Apotheosis Ranger SLevel 4 List": ["Target_SummonElemental"],  # dnd55e's spell
    "Apotheosis Artificer SLevel 4 List": ["Target_ApoFaithfulHound", "Target_ApoSummonConstruct"],
    "Apotheosis Artificer SLevel 5 List": ["Target_ApoAnimateObjects", "Target_ApoBigbysHand"],
}
RETIRED = {"Target_ApoSummonElemental"}  # dropped from Apotheosis-owned lists (replaced by dnd55e's spells)
NODE = re.compile(r'[ \t]*<node id="SpellList">\s*(?:(?!</node>).)*?</node>\n', re.S)


def patch_lists():
    path = os.path.join(PUB, "Lists", "SpellLists.lsx")
    s = open(path, encoding="utf-8").read()
    for name, add in APO_ADDS.items():
        m = re.search(rf'(<attribute id="Name" type="FixedString" value="{re.escape(name)}"/>\s*<attribute id="Spells" type="LSString" value=")([^"]*)', s)
        assert m, name
        have = [x for x in m.group(2).split(";") if x and x not in RETIRED]
        s = s[:m.start(2)] + ";".join(have + [a for a in add if a not in have]) + s[m.end(2):]
    open(path, "w", encoding="utf-8", newline="").write(s)
    dnd = open(os.path.join(DND, "Lists", "SpellLists.lsx"), encoding="utf-8").read()
    rows = []
    for node in NODE.findall(dnd):
        name = re.search(r'id="Name" type="FixedString" value="([^"]*)"', node)
        if not name:
            continue
        add = [sp for (cls, lvl), sps in CLASS_ADDS.items() for sp in sps
               if re.match(rf"5\.5 {cls} SLevel {lvl}( |$)", name.group(1))]
        if add:
            def extend(m):
                have = [x for x in m.group(2).split(";") if x]
                return m.group(1) + ";".join(have + [a for a in dict.fromkeys(add) if a not in have])
            rows.append("                " + re.sub(r'(id="Spells" type="LSString" value=")([^"]*)', extend, node.strip()) + "\n")
    G._between(path, rows)
    return len(rows)


if __name__ == "__main__":
    G.write_stats("Summons", "gen_summons.py", "issue #10")
    G.write_templates("Apotheosis_Summons")
    n = patch_lists()
    G.patch_loca()
    print(f"{len(G.C)} creatures, {len(G.T)} templates, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.P)} passives, "
          f"{len(G.I)} interrupts; {n} dnd55e lists overridden")
