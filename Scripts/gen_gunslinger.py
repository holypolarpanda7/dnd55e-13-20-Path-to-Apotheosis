"""Generate the Gunslinger levels 13-20 (issue #6) from the Risk-dice Gunslinger dnd55e implements
(References/Classes/Gunslinger.txt). Replaces the earlier build from Mercer's older Gunslinger.

Base class: 13 Cheat Death, 14 +1 Risk Die (6), 15 Dire Gambit, 17 Critical Shot 17-20, 18 Deft Maneuver and
Risk Die d12, 19 Epic Boon (dnd55e's own level-19 node and its feat pick: the boons are feats with a level 19
prerequisite since 2026-10-06, Scripts/gen_epic_boons.py), 20 Headshot. Subclasses dnd55e ships: High Roller 14 Double or Nothing, White Hat 14 Gold
Star Hero, Spellslinger 14 Magic Bullet and its 13-20 spell table.

Owns (rewritten every run): Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_Gunslinger.txt.
Patches idempotently: Progressions.lsx (nodes by UUID), ActionResourceDefinitions, Levelmaps/LevelMapValues.lsx,
Localization. Removes the old placeholder passives from Passive.txt.
Script Extender half: ScriptExtender/Lua/Gunslinger.lua.

Run: python3 Scripts/gen_gunslinger.py && python3 Scripts/gen_epic_boons.py && python3 Scripts/build_all_class_expectations.py
"""
import glob
import os
import re
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = glob.glob(os.path.join(REPO, "Public", "*"))[0]
DATA = os.path.join(PUB, "Stats", "Generated", "Data")
LOCA = glob.glob(os.path.join(REPO, "Mods", "*", "Localization", "English", "dnd55e-Apotheosis.xml"))[0]
from gen_common import DND  # dnd55e as released (the dependency pak)
NS = uuid.NAMESPACE_URL
LOCA_ROWS = {}
MARK = "GUNSLINGER 13-20"


def gid(key):
    return str(uuid.uuid5(NS, "apotheosis-gunslinger:" + key))


def h(key, text):
    handle = "h" + uuid.uuid5(NS, "apotheosis-gunslinger-loca:" + key).hex
    LOCA_ROWS[handle] = text
    return handle


def entry(name, typ, fields, using=None, comment=None):
    out = ([f"// {comment}"] if comment else []) + [f'new entry "{name}"', f'type "{typ}"']
    if using:
        out.append(f'using "{using}"')
    out += [f'data "{k}" "{v}"' for k, v in fields.items() if v is not None]
    return "\n".join(out) + "\n"


P, S, SP, I = [], [], [], []
RANGED_CRIT = "Self(context.Source,context.Observer) and not Self() and IsCritical() and IsRangedWeaponAttack() and not AnyEntityIsItem()"
QUIET = "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"


def passive(name, title, text, fields, icon="Gunslinger_2_Risk", hidden=False):
    base = {"DisplayName": h(name + ":n", title), "Description": h(name + ":d", text), "Icon": icon,
            "Properties": "IsHidden" if hidden else "Highlighted"}
    P.append(entry(name, "PassiveData", {**base, **fields}))


# ---------------------------------------------------------------- base class
passive("Gunslinger_13_CheatDeath", "Cheat Death",
        "When you are reduced to 0 Hit Points and not killed outright, you drop to 1 Hit Point instead and regain Hit Points equal to your Gunslinger level. Once per Short or Long Rest.",
        {"StatsFunctorContext": "OnCreate;OnShortRest;OnLongRest", "StatsFunctors": "ApplyStatus(SELF,GUNSLINGER_CHEAT_DEATH,100,-1)"},
        icon="PassiveFeature_RelentlessEndurance")
S.append(entry("GUNSLINGER_CHEAT_DEATH", "StatusData", {
    "DisplayName": h("CheatDeath:n", "Cheat Death"), "Description": h("CheatDeath:d", "The next time you drop to 0 Hit Points, you drop to 1 instead and regain Hit Points equal to your Gunslinger level."),
    "Icon": "PassiveFeature_RelentlessEndurance", "Boosts": "DownedStatus(GUNSLINGER_CHEAT_DEATH_DOWNED,7)", "StackId": "GUNSLINGER_CHEAT_DEATH"},
    using="RELENTLESS_ENDURANCE", comment="Cloned from Relentless Endurance; priority 7 runs before it and Last Stand."))
S.append(entry("GUNSLINGER_CHEAT_DEATH_DOWNED", "StatusData", {
    "DisplayName": h("CheatDeathDown:n", "Cheat Death"),
    "OnApplyFunctors": "RemoveStatus(GUNSLINGER_CHEAT_DEATH);RegainHitPoints(1+ClassLevel(Gunslinger),Guaranteed)"},
    using="RELENTLESS_ENDURANCE_DOWNED"))

passive("Gunslinger_15_DireGambit", "Dire Gambit", "Whenever you roll Initiative or score a Critical Hit, you regain one expended Risk Die.",
        {"StatsFunctorContext": "OnAttack", "StatsFunctors": "IF(IsCritical()):RestoreResource(SELF,Risk,1,0)"})
passive("Gunslinger_15_DireGambit_Initiative", "Dire Gambit", "Regain a Risk Die when you roll Initiative.",
        {"StatsFunctorContext": "OnCombatStarted", "StatsFunctors": "RestoreResource(SELF,Risk,1,0)"}, hidden=True)

passive("Gunslinger_17_CriticalShot", "Critical Shot", "Your attack rolls with Ranged weapons score a Critical Hit on a roll of 17-20 on the d20.",
        {"Boosts": "IF(IsRangedWeaponAttack()):ReduceCriticalAttackThreshold(1)"}, icon="PassiveFeature_ImprovedCritical")

passive("Gunslinger_18_DeftManeuver", "Deft Maneuver",
        "You gain a special Bonus Action each turn that you can use only for a maneuver. Your maneuvers here never cost a Bonus Action, so they are always ready to use alongside your other actions. Your Risk Die becomes a d12.",
        {}, icon="Gunslinger_2_Risk")

passive("Gunslinger_20_Headshot", "Headshot",
        "When you score a Critical Hit with a Ranged weapon, you can make it a Headshot: a creature with fewer than 100 Hit Points dies, any other takes an extra 10d10 damage of the weapon's type. Once per Short or Long Rest; expend three Risk Dice to use it again.",
        {"Boosts": "ActionResource(GunslingerHeadshot,1,0);UnlockInterrupt(Interrupt_Gunslinger_Headshot);UnlockSpell(Shout_Gunslinger_HeadshotReload)"},
        icon="Gunslinger_5_GutShot")
I.append(entry("Interrupt_Gunslinger_Headshot", "InterruptData", {
    "DisplayName": h("HeadshotI:n", "Headshot"), "Description": h("HeadshotI:d", "Make this Critical Hit a Headshot: the target dies if it has fewer than 100 Hit Points; otherwise it takes an extra 10d10 damage."),
    "Icon": "Gunslinger_5_GutShot", "InterruptContext": "OnCastHit", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": RANGED_CRIT + " and Character(context.Target)",
    "Properties": "IF(HasHPLessThan(100,context.Target)):ApplyStatus(GUNSLINGER_HEADSHOT,100,0);IF(not HasHPLessThan(100,context.Target)):DealDamage(10d10,MainRangedWeaponDamageType)",
    "Cost": "GunslingerHeadshot:1", "InterruptDefaultValue": "Ask;Enabled",
    "EnableCondition": "not HasStatus('SG_Polymorph') or HasAnyStatus({'SG_Disguise'})", "EnableContext": "OnStatusApplied;OnStatusRemoved"}))
S.append(entry("GUNSLINGER_HEADSHOT", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("HeadshotSt:n", "Headshot"), "Icon": "Gunslinger_5_GutShot",
    "OnApplyFunctors": "Kill()", "StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator"},
    comment="Kill() from interrupt Properties did nothing (2026-10-02); a status runs it on its owner, the target."))
SP.append(entry("Shout_Gunslinger_HeadshotReload", "SpellData", {
    "SpellType": "Shout", "Level": "0", "DisplayName": h("HeadshotR:n", "Headshot: Spend Risk Dice"),
    "Description": h("HeadshotR:d", "Expend three Risk Dice to use Headshot again."), "Icon": "Gunslinger_5_GutShot",
    "UseCosts": "Risk:3", "TargetConditions": "Self()", "AIFlags": "CanNotUse",
    "RequirementConditions": "not HasActionResource('GunslingerHeadshot',1,0,false,false,context.Source)",
    "SpellProperties": "RestoreResource(SELF,GunslingerHeadshot,1,0)", "SpellFlags": "IgnoreSilence;NoCameraMove"}))

# ---------------------------------------------------------------- High Roller 14: Double or Nothing (Gunslinger.lua)
passive("HighRoller_14_DoubleOrNothing", "Double or Nothing",
        "While this is on, each Critical Hit you score with a Ranged weapon is a gamble: roll a d20. On 10 or higher its damage dice are rolled four times instead of twice; on 9 or lower it becomes a normal hit.",
        {"Properties": "Highlighted;IsToggled;ToggledDefaultAddToHotbar",
         "ToggleOnFunctors": "ApplyStatus(SELF,HIGHROLLER_DOUBLE_OR_NOTHING,100,-1)",
         "ToggleOffFunctors": "RemoveStatus(SELF,HIGHROLLER_DOUBLE_OR_NOTHING)", "ToggleGroup": "HighRollerDoubleOrNothing"},
        icon="HighRoller_3_LiarsDice")
S.append(entry("HIGHROLLER_DOUBLE_OR_NOTHING", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("DoN:n", "Double or Nothing"),
    "Description": h("DoN:d", "Your ranged Critical Hits are a gamble: 10+ on a d20 doubles their damage, 9 or lower makes them normal hits."),
    "Icon": "HighRoller_3_LiarsDice", "StatusPropertyFlags": "IgnoreResting;DisableOverhead;DisableCombatlog"},
    comment="Gunslinger.lua rolls the d20 and scales the hit's damage."))

# ---------------------------------------------------------------- White Hat 14: Gold Star Hero
passive("WhiteHat_14_GoldStarHero", "Gold Star Hero",
        "Improved Aura: allies within 30 feet of you have Advantage on saving throws against being Frightened while you aren't Incapacitated. Iron-Clad Law: an ally you protect with Lay Down the Law has Resistance to Bludgeoning, Piercing and Slashing damage until the start of your next turn. Stunned Surrender: a creature you score a Critical Hit against makes a Wisdom saving throw against your maneuver DC or is Stunned.",
        {"StatsFunctorContext": "OnCreate;OnShortRest;OnLongRest",
         "StatsFunctors": "ApplyStatus(SELF,WHITEHAT_GOLD_STAR_AURA,100,-1)"}, icon="Spell_Enchantment_Heroism")
passive("WhiteHat_14_GoldStarHero_Surrender", "Stunned Surrender", "Critical Hits can stun.",
        {"StatsFunctorContext": "OnDamage",
         "Conditions": "HasDamageEffectFlag(DamageFlags.Critical) and not HasDamageEffectFlag(DamageFlags.Miss) and Character()",
         "StatsFunctors": "IF(not SavingThrow(Ability.Wisdom,ManeuverSaveDC())):ApplyStatus(WHITEHAT_STUNNED_SURRENDER,100,10)"},
        hidden=True)
# The maneuver DC is 8 + Dexterity modifier + PB; ManeuverSaveDC() (8 + PB + the higher of Str/Dex) is the closest
# shipped helper and equals it unless Strength is the higher score.
S.append(entry("WHITEHAT_GOLD_STAR_AURA", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("GoldAura:n", "Gold Star Hero"),
    "Description": h("GoldAura:d", "Allies within 30 feet have Advantage on saving throws against being Frightened."),
    "Icon": "Spell_Enchantment_Heroism", "AuraRadius": "9",
    "AuraStatuses": "IF(Ally() and not Self() and not Tagged('INANIMATE') and not HasStatus('SG_Incapacitated',context.Source)):ApplyStatus(WHITEHAT_STEELY_EYED_ALLY)",
    "StatusPropertyFlags": "IgnoreResting;DisableOverhead;DisableCombatlog;DisablePortraitIndicator", "StatusGroups": "SG_RemoveOnRespec"}))
S.append(entry("WHITEHAT_STEELY_EYED_ALLY", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("SteelyAlly:n", "Steely-Eyed"),
    "Description": h("SteelyAlly:d", "Advantage on saving throws against being Frightened."), "Icon": "Spell_Enchantment_Heroism",
    "Boosts": "Tag(FRIGHTENED_ADV)", "StatusPropertyFlags": "DisableOverhead;DisableCombatlog"},
    comment="Tag(FRIGHTENED_ADV) is Halfling Brave's mechanism."))
S.append(entry("WHITEHAT_IRONCLAD_LAW", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("IronClad:n", "Iron-Clad Law"),
    "Description": h("IronClad:d", "Resistance to Bludgeoning, Piercing and Slashing damage."), "Icon": "Action_MagicItem_ProtectionFromMissiles",
    "Boosts": "Resistance(Bludgeoning,Resistant);Resistance(Piercing,Resistant);Resistance(Slashing,Resistant)", "StackId": "WHITEHAT_IRONCLAD_LAW"},
    comment="Applied by Gunslinger.lua with Lay Down the Law, until the start of the White Hat's next turn."))
S.append(entry("WHITEHAT_STUNNED_SURRENDER", "StatusData", {
    "DisplayName": h("Surrender:n", "Surrendered"),
    "Description": h("Surrender:d", "Stunned. Ends if the creature takes damage, and it repeats the Wisdom saving throw at the end of each of its turns."),
    "StackId": "WHITEHAT_STUNNED_SURRENDER", "RemoveEvents": "OnDamage", "RemoveConditions": "true",
    "TickType": "EndTurn", "OnTickRoll": "SavingThrow(Ability.Wisdom,ManeuverSaveDC())",
    "OnTickSuccess": "RemoveStatus(SELF,WHITEHAT_STUNNED_SURRENDER)"}, using="STUNNED"))

# ---------------------------------------------------------------- Spellslinger 14: Magic Bullet
passive("Spellslinger_14_MagicBullet", "Magic Bullet",
        "When you make a spell attack roll, you can expend a Risk Die to fire it as a ranged weapon attack: add the Risk Die to the attack roll, and on a hit the target also takes your ranged weapon's normal damage.",
        {"Boosts": "UnlockInterrupt(Interrupt_Spellslinger_MagicBullet)", "StatsFunctorContext": "OnAttack",
         "Conditions": "IsSpell()",
         "StatsFunctors": "IF(HasStatus('SPELLSLINGER_MAGIC_BULLET',context.Source) and not IsMiss()):DealDamage(MainRangedWeapon,MainRangedWeaponDamageType,Magical,,0,,true,true,false,true);RemoveStatus(SELF,SPELLSLINGER_MAGIC_BULLET)"},
        icon="Spell_Evocation_FingerGuns")
I.append(entry("Interrupt_Spellslinger_MagicBullet", "InterruptData", {
    "DisplayName": h("MagicBulletI:n", "Magic Bullet"), "Description": h("MagicBulletI:d", "Add a Risk Die to this spell attack roll; on a hit, it also deals your ranged weapon's damage."),
    "Icon": "Spell_Evocation_FingerGuns", "InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
    "Conditions": "not Dead(context.Observer) and HasInterruptedAttack() and Self(context.Observer,context.Source) and (IsAttackType(AttackType.RangedSpellAttack) or IsAttackType(AttackType.MeleeSpellAttack)) and not AnyEntityIsItem()",
    "Properties": "AdjustRoll(OBSERVER_OBSERVER,LevelMapValue(Risk));ApplyStatus(OBSERVER_OBSERVER,SPELLSLINGER_MAGIC_BULLET,100,1)",
    "Cost": "Risk:1", "InterruptDefaultValue": "Ask;Enabled"},
    comment="dnd55e's maneuvers cost a Risk Die and no Bonus Action; Magic Bullet follows them."))
S.append(entry("SPELLSLINGER_MAGIC_BULLET", "StatusData", {
    "StatusType": "BOOST", "DisplayName": h("MagicBullet:n", "Magic Bullet"), "Icon": "Spell_Evocation_FingerGuns",
    "StatusPropertyFlags": QUIET, "StackId": "SPELLSLINGER_MAGIC_BULLET"}))

RESOURCES = [("GunslingerHeadshot", 1, "ShortRest", "Headshot", "Make a Critical Hit a Headshot. Returns on a Short or Long Rest, or by expending three Risk Dice.")]

# ---------------------------------------------------------------- progression nodes
WIZ3, WIZ4 = "22755771-ca11-49f4-b772-13d8b8fecd93", "820b1220-0385-426d-ae15-458dc8a6f5c0"  # dnd55e "5.5 Wizard SLevel 3/4"
SEL = lambda lst: f"SelectSpells({lst},1,1,EldritchKnightAbjEvo)"
NODES = {  # uuid -> attributes (PassivesAdded / Boosts / Selectors); None = delete the node
    "dddddddd-dddd-dddd-dddd-ddddddddd901": {"PassivesAdded": "Gunslinger_13_CheatDeath"},
    "dddddddd-dddd-dddd-dddd-ddddddddd902": {"Boosts": "ActionResource(Risk,1,0)"},
    "dddddddd-dddd-dddd-dddd-ddddddddd903": {"PassivesAdded": "Gunslinger_15_DireGambit;Gunslinger_15_DireGambit_Initiative"},
    "dddddddd-dddd-dddd-dddd-ddddddddd905": {"PassivesAdded": "Gunslinger_17_CriticalShot"},
    "dddddddd-dddd-dddd-dddd-ddddddddd906": {"PassivesAdded": "Gunslinger_18_DeftManeuver"},
    "dddddddd-dddd-dddd-dddd-ddddddddd907": None,  # level 19 lives on dnd55e's own node (override below)
    "dddddddd-dddd-dddd-dddd-ddddddddd908": {"PassivesAdded": "Gunslinger_20_Headshot"},
    "75757575-7575-7575-7575-757575757501": {"PassivesAdded": "HighRoller_14_DoubleOrNothing"},
    "7a111111-0000-0000-0000-000000000115": None, "7a111111-0000-0000-0000-000000000118": None,
    "79797979-7979-7979-7979-797979797901": {"PassivesAdded": "WhiteHat_14_GoldStarHero;WhiteHat_14_GoldStarHero_Surrender"},
    "7c333333-0000-0000-0000-000000000115": None, "7c333333-0000-0000-0000-000000000118": None,
    # Spellslinger table: prepared 9/10/10/11/11/11/12/13 at 13-20; 3rd-level slots 2 at 13, 3 at 16; one 4th at 19
    "7b222222-0000-0000-0000-000000000113": {"Boosts": "ActionResource(SpellSlot,2,3)", "Selectors": SEL(WIZ3)},
    "aa777777-7777-7777-7777-777777777701": {"PassivesAdded": "Spellslinger_14_MagicBullet", "Selectors": SEL(WIZ3)},
    "7b222222-0000-0000-0000-000000000115": None,
    "7b222222-0000-0000-0000-000000000116": {"Boosts": "ActionResource(SpellSlot,1,3)", "Selectors": SEL(WIZ3)},
    "7b222222-0000-0000-0000-000000000117": None, "7b222222-0000-0000-0000-000000000118": None,
    "7b222222-0000-0000-0000-000000000119": {"Boosts": "ActionResource(SpellSlot,1,4)", "Selectors": SEL(WIZ4)},
    "7b222222-0000-0000-0000-000000000120": {"Selectors": SEL(WIZ4)},
}
DND_L19 = "465b1578-a2dd-476a-b4ac-d3955332b5f3"  # dnd55e Gunslinger level 19 (HP die + feat pick): no override
OLD_PASSIVES = ["Gunslinger_LightningReload", "Gunslinger_ViciousIntent", "Gunslinger_HemorrhagingCritical",
                "HighRoller_14_DoubleOrNothing", "HighRoller_15_StackedDeck", "HighRoller_18_Jackpot",
                "WhiteHat_14_GoldStarHero", "WhiteHat_15_Peacekeeper", "WhiteHat_18_LawgiversReach",
                "Spellslinger_14_MagicBullet", "SpellSlinger_15_ArcaneBarrage", "SpellSlinger_18_SpellStorm"]
NODE_RE = re.compile(r'[ \t]*<node id="Progression">(?:(?!</node>).)*?</node>\n', re.S)


def patch_progressions():
    path = os.path.join(PUB, "Progressions", "Progressions.lsx")
    s = open(path, encoding="utf-8").read()
    seen = set()

    def fix(m):
        b = m.group(0)
        u = re.search(r'id="UUID" type="guid" value="([^"]*)"', b).group(1)
        if u not in NODES:
            return b
        seen.add(u)
        want = NODES[u]
        if want is None:
            return ""
        ind = re.search(r'\n(\s*)<attribute id="Level"', b).group(1)
        for k in ("PassivesAdded", "Boosts", "Selectors"):
            b = re.sub(rf'\s*<attribute id="{k}" type="LSString" value="[^"]*"/>', "", b)
        add = "".join(f'\n{ind}<attribute id="{k}" type="LSString" value="{v}"/>' for k, v in want.items())
        return re.sub(r'(\n\s*<attribute id="Level")', add + r"\1", b, count=1)

    s = NODE_RE.sub(fix, s)
    missing = [u for u, w in NODES.items() if w is not None and u not in seen]
    assert not missing, f"progression nodes not found: {missing}"
    # dnd55e's level-19 node was overridden here until 2026-10-06 to drop its feat pick for the old Epic Boon passive pick; the
    # boons are feats now, so dnd55e's node (HP die + feat pick) is right as it is - remove the old override
    s = NODE_RE.sub(lambda m: "" if DND_L19 in m.group(0) else m.group(0), s)
    open(path, "w", encoding="utf-8", newline="").write(s)


def patch_between(path, block):
    s = open(path, encoding="utf-8").read()
    start, end = f"                <!-- {MARK} BEGIN", f"<!-- {MARK} END -->\n"
    if start in s:
        s = s[:s.index(start)] + block + s[s.index(end) + len(end):]
    else:
        i = s.rindex("            </children>")
        s = s[:i] + block + s[i:]
    open(path, "w", encoding="utf-8", newline="").write(s)


def wrap(rows):
    return f"                <!-- {MARK} BEGIN (Scripts/gen_gunslinger.py) -->\n" + "".join(rows) + f"                <!-- {MARK} END -->\n"


def patch_resources():
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
    patch_between(glob.glob(os.path.join(PUB, "ActionResourceDefinitions", "*.lsx"))[0], wrap(rows))


def patch_levelmap():
    """dnd55e's Risk die series (d8, d10 at 10) plus the d12 at 18, under dnd55e's UUID."""
    row = """                <node id="LevelMapSeries">
                    <attribute id="Level1" type="LSString" value="1d8"/>
                    <attribute id="Level10" type="LSString" value="1d10"/>
                    <attribute id="Level18" type="LSString" value="1d12"/>
                    <attribute id="Name" type="FixedString" value="Risk"/>
                    <attribute id="PreferredClassUUID" type="guid" value="b6cd23fa-ec1a-44a6-86c5-693201654dba"/>
                    <attribute id="UUID" type="guid" value="f2694731-e5cf-40a4-a9bd-b24b602fb54e"/>
                </node>
"""
    patch_between(os.path.join(PUB, "Levelmaps", "LevelMapValues.lsx"), wrap([row]))


def drop_old_passives():
    path = os.path.join(DATA, "Passive.txt")
    s = open(path, encoding="utf-8").read()
    for n in OLD_PASSIVES:
        s = re.sub(rf'(?:\r?\n)*new entry "{n}"\r?\n(?:(?!new entry ).)*', "\n\n", s, flags=re.S)
    s = re.sub(r"\n{3,}", "\n\n", s)
    open(path, "w", encoding="utf-8", newline="").write(s)


def patch_loca():
    from gen_common import update_loca
    update_loca(LOCA_ROWS)


ANIM = "9122eb08-93f1-4010-a275-f5ae3ec7c76e,,;,,;9fb11cca-02d4-4d2f-955f-2826c0553b17,,;5103d398-d8de-4aa4-9633-db2e1b7f6254,,;5301d674-b7da-47b6-b4cf-2802ba33a9e9,,;,,;86b3cf93-21fb-4a3d-bed9-97d0a567d084,,;,,;,,"


def write_stats():
    head = ("// GENERATED by Scripts/gen_gunslinger.py (Gunslinger 13-20, issue #6) - edit the generator, not this file.\n"
            "// Script Extender half: ScriptExtender/Lua/Gunslinger.lua\n\n")
    spells = [x.rstrip("\n") + f'\ndata "SpellAnimation" "{ANIM}"\n' for x in SP]  # a spell without one never finishes casting
    for fname, rows in (("Passive_Gunslinger.txt", P), ("Status_Gunslinger.txt", S), ("Spell_Gunslinger.txt", spells),
                        ("Interrupt_Gunslinger.txt", I)):
        with open(os.path.join(DATA, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(head + "\n".join(rows))


if __name__ == "__main__":
    drop_old_passives()
    write_stats()
    patch_resources()
    patch_levelmap()
    patch_progressions()
    patch_loca()
    print(f"{len(P)} passives, {len(S)} statuses, {len(SP)} spells, {len(I)} interrupts, {len(LOCA_ROWS)} strings")
