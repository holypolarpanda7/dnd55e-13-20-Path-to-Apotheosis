"""Class, subclass and species resources that dnd55e stops growing at its level-12 cap (2026-10-13).

Found by Scripts/resource_audit.py (and the deep dive in docs/HIGH_LEVEL_AUDIT.md) after the Hit Point Dice turned out to stop at
12: dnd55e hands out these pools one step per level node up to 12 (or per Proficiency Bonus step, which it stops at +4), so a level 13+
character kept the level-12 amount. Each step here is a boost on a progression node at the level it applies (applied at that
level-up - the level-conditional passive boosts lag until the next load, see bg3-engine-gotchas), the same way gen_hit_dice.py does
for the Hit Point Dice. Texts: PHB 2024 / SRD 5.2.1 and the shared library (D:\\Library\\DnD excerpts/classes).

Subclass and class pools (steps are the increment at that level):
  Celestial Warlock   Healing Light       1 + Warlock level d6s                    +1 per level 13-20
  Circle of Dreams    Balm of the Summer  d6s equal to the Druid level             +1 per level 13-20
  Abjuration Wizard   Arcane Ward         2 x Wizard level (+ Int modifier)        +2 per level 13-20
  Circle of the Land  Natural Recovery    half the Druid level, rounded up         +1 at 13, 15, 17, 19
  Zealot Barbarian    Warrior of the Gods 4/5/6/7 dice at 3/6/12/17                +1 at 17
  Alchemist           Experimental Elixir 3/4/5 elixirs at 5/9/15                  +1 at 15
  Artificer           Magic Items         the Magic Items column: 5 at 14, 6 at 18 +1 at 14, 18
  Rune Knight         Giant's Might = Proficiency Bonus uses (+1 at 13, 17); runes known +1 at 15 is a pick (Progressions.lsx)
  Psi Warrior, Soulknife  Psionic Energy Dice  twice the Proficiency Bonus: 10 at 13, 12 at 17 (+2 each)
  Swarmkeeper         Writhing Tide       Proficiency Bonus uses                   +1 at 13, 17
Species whose uses equal the Proficiency Bonus (race nodes by character level): Dragonborn Breath Weapon, Eladrin Fey Step,
Goliath Giant Ancestry, Shadar-kai Blessing of the Raven Queen: +1 at 13 and 17.
Feats that give Proficiency Bonus uses (Lucky, Healer, Poisoner, the Giant feats, ...): dnd55e's passive has steps at
CharacterLevelGreaterThan(4) and (8); this overrides it with itself plus (12) and (16), read from the dnd55e release at each regen
(dnd55e's own `using` pattern, as gen_rules_fixes.py does), so a feat taken at level 13+ gets the right number at once.

Also here (the same rules-table check found them): the Monk's Unarmored Movement stops at +20 ft (10th level), the rules add +25 ft
at 14 and +30 ft at 18 (passives Apo_UnarmoredMovement_4 / _5, replacing the one before); the Fighter's sixth Weapon Mastery at 16.

Run: python3 Scripts/gen_class_resources.py   (after gen_hit_dice.py in regen_all.sh)
"""
import glob
import os
import re

from gen_common import DND, Gen, append_progressions, patch_progressions

G = Gen("classres", "CLASS RESOURCES 13-20")
CLASS, SUB, SPECIES = 0, 1, 2
NODES = []   # (table, name, progression type, level, {attribute: value})


def steps(table, name, ptype, resource, per_level):
    """per_level: {level: amount added at that level}."""
    for lvl, n in per_level.items():
        NODES.append((table, name, ptype, lvl, {"Boosts": f"ActionResource({resource},{n},0)"}))


EVERY = range(13, 21)
steps("26e6c591-746b-4ba2-b46b-218f3a24fb84", "Celestial", SUB, "HealingLight", {l: 1 for l in EVERY})
steps("aba806c9-d349-4c70-9a1a-0cb0ae699e3f", "CircleOfDreams", SUB, "Balm", {l: 1 for l in EVERY})
steps("9f0fd3ac-7520-45fa-9f7d-08b1ca6eacf3", "AbjurationSchool", SUB, "ArcaneWard", {l: 2 for l in EVERY})
steps("ba1f14d6-d40b-47ce-b071-91b491d87b27", "CircleOfTheLand", SUB, "NaturalRecoveryPoint", {l: 1 for l in (13, 15, 17, 19)})
steps("c5fb3d32-6c46-4c9e-a2c9-8849f52e16e4", "ZealotPath", SUB, "WarriorOfTheGods", {17: 1})
steps("c36e28a1-2fd5-475b-9689-09b83c9fd63d", "Alchemist", SUB, "ExperimentalElixir", {15: 1})
steps("1e84493e-aeff-4d0e-b3ae-6c2187245d23", "Artificer", CLASS, "ReplicateMagicItem", {14: 1, 18: 1})
RUNE_KNIGHT = "b8a2b9b8-8c2e-47bd-aae9-35e191ec1162"
# dnd55e 4.14 (2026-10-24): runes are SelectPassives picks with a resource each (5th rune at 15 = Progressions.lsx), Giant's Might
# has Proficiency Bonus uses (2/3/4 at 3/5/9) and Runic Shield Constitution-modifier uses (no level steps)
steps(RUNE_KNIGHT, "RuneKnight", SUB, "GiantsMight", {13: 1, 17: 1})
steps("df42bb97-2d97-44f0-8cb2-379e83208408", "PsiWarrior", SUB, "PsiWarrior", {13: 2, 17: 2})
steps("abc7b271-82a1-4139-9653-4c90a7984a38", "Soulknife", SUB, "Soulknife", {13: 2, 17: 2})
steps("54ad9a98-9656-4aa5-858e-b302f83c4577", "Swarmkeeper", SUB, "WrithingTidePoint", {13: 1, 17: 1})
for table, name, resource in [("e2472b4f-682a-4ac8-b11c-723f921fd7a1", "Dragonborn", "BreathWeapon"),
                              ("ec2603e5-cf91-47da-b02b-0df881a55c23", "Eladrin", "Eladrin"),
                              ("fba1e7f8-9ccf-46cb-9a00-566943a25242", "Goliath", "Goliath"),
                              ("04dc5432-4d5a-45f1-acb4-a5bec09be5dc", "ShadarKai", "ShadarKai")]:
    steps(table, name, SPECIES, resource, {13: 1, 17: 1})

# Monk: Unarmored Movement +25 ft at 14 and +30 ft at 18 (PHB 2024; the base game's passives stop at +20 ft, 3 x 1.5 m per 5 ft)
MONK = "fe1319a2-86be-469c-aab5-e3b0bd714e0e"
UM = {14: (7.5, "25", "UnarmoredMovement_3"), 18: (9, "30", "Apo_UnarmoredMovement_4")}
for lvl, (metres, feet, prev) in UM.items():
    name = f"Apo_UnarmoredMovement_{4 if lvl == 14 else 5}"
    G.passive(name, f"Unarmored Movement {4 if lvl == 14 else 5}",
              f"Your Speed increases by [1] while you aren't wearing armor or wielding a Shield ({feet} feet at Monk level {lvl}).",
              {"DescriptionParams": f"Distance({metres:g})", "Boosts": f"ActionResource(Movement,{metres:g},0)"},
              icon="PassiveFeature_UnarmoredMovement_3", using="UnarmoredMovement_3",
              comment=f"Monk {lvl}: +{feet} ft (PHB 2024 Monk Features table)")
    NODES.append((MONK, "Monk", CLASS, lvl, {"PassivesAdded": name, "PassivesRemoved": prev}))
# Fighter: a sixth Weapon Mastery at 16 (the table's Weapon Mastery column: 3, 4 at 4, 5 at 10, 6 at 16; dnd55e's nodes stop at 10)
FIGHTER_16 = "d4e5f6a7-b8c9-40d1-e2f3-a4b5c6d7e8f9"   # PTA's Fighter level 16 node (the feat / Ability Score Improvement): the mastery pick joins it
MASTERY_PICK = "SelectPassives(b9543135-eceb-4ca9-b9fc-43befc11de3b,1,WeaponMasteryList)"

# feat / background passives whose uses are the Proficiency Bonus: passive -> resource
PB_PASSIVES = {
    "AdrenalineRush": "AdrenalineRush", "EmberOfTheFireGiant": "SearingIgnition", "FairyTrickster": "FairyTrickster",
    "FuryOfTheFrostGiant": "FrigidRetaliation", "GuileOfTheCloudGiant": "CloudyEscape", "Healer": "Healer",
    "KeennessOfTheStoneGiant": "StoneThrow", "Lucky_Unlock": "LuckPoint", "Poisoner": "Poisoner",
    "PurpleDragonCommandant": "EncourageAlly", "SoulOfTheStormGiant": "MaelstromAura", "SpellfireSpark": "SacredFlame",
    "StrikeOfTheGiants": "StrikeOfTheGiants",
}


def dnd_field(entry, field, files="*.txt"):
    """A field of a dnd55e stats entry, as released (the extracted dependency pak)."""
    for f in glob.glob(os.path.join(DND, "Stats", "Generated", "Data", files)):
        s = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(rf'new entry "{re.escape(entry)}"\r?\n(.*?)(?=\r?\nnew entry |\Z)', s, re.S)
        if m:
            v = re.search(rf'data "{field}" "([^"]*)"', m.group(1))
            if v:
                return v.group(1)
    raise SystemExit(f"{entry}.{field} not found in the dnd55e release (gen_class_resources.py)")


def dnd_boosts(entry):
    return dnd_field(entry, "Boosts", "Passive*.txt")


# Circle of Dreams: Balm of the Summer Court spends up to half the Druid level (rounded up) in dice at once; dnd55e's variants stop at
# 6 dice (level 12). Seven to ten dice at 14, 16, 18, 20: the same spell with the numbers changed (Target_Balm_N, BALM_TEMPHP_N).
def balm_variants():
    for n in range(7, 11):
        level = 2 * n - 2   # 14, 16, 18, 20
        G.S.append(G.entry(f"BALM_TEMPHP_{n}", "StatusData", {"DescriptionParams": str(n), "StackPriority": str(n), "Boosts": f"TemporaryHP({n});"},
                           using="BALM_TEMPHP_6", comment=f"Balm of the Summer Court, {n} dice (Druid level {level})"))
        G.SP.append(G.entry(f"Target_Balm_{n}", "SpellData", {
            "SpellProperties": f"RegainHitPoints({n}d6);ApplyStatus(BALM_TEMPHP_{n},100,-1);",
            "RequirementConditions": f"ClassLevelHigherOrEqualThan({level},'Druid',context.Source);",
            "TooltipDamageList": f"RegainHitPoints({n}d6);", "TooltipStatusApply": f"ApplyStatus(BALM_TEMPHP_{n},100,-1);",
            "UseCosts": f"BonusActionPoint:1;Balm:{n}", "PowerLevel": str(n)}, using="Target_Balm_6"))
    cont = dnd_field("Target_Balm", "ContainerSpells", "Spell*.txt").rstrip(";")
    if "Target_Balm_7" not in cont:
        G.SP.append(G.entry("Target_Balm", "SpellData", {"ContainerSpells": cont + ";" + ";".join(f"Target_Balm_{n}" for n in range(7, 11)) + ";"},
                            using="Target_Balm", comment="Balm of the Summer Court: the 7-10 dice variants (re-read from dnd55e at each regen)"))


def extend_pb_passives():
    for passive, resource in PB_PASSIVES.items():
        boosts = dnd_boosts(passive)
        assert "CharacterLevelGreaterThan(8)" in boosts, f"{passive}: no Proficiency Bonus steps to extend"
        if "CharacterLevelGreaterThan(12)" in boosts:
            continue   # dnd55e caught up
        add = "".join(f"IF(CharacterLevelGreaterThan({n})):ActionResource({resource},1,0);" for n in (12, 16))
        G.P.append(G.entry(passive, "PassiveData", {"Boosts": boosts.rstrip(";") + ";" + add.rstrip(";")}, using=passive,
                           comment="Proficiency Bonus uses: +1 at level 13 and 17 (gen_class_resources.py; re-read from dnd55e at each regen)"))


# Zealot: the pool reaches 7 dice at level 17; dnd55e's spend variants stop at 6
def zealot_variant():
    G.SP.append(G.entry("Shout_WarriorOfTheGods_7", "SpellData", {
        "SpellProperties": "RegainHitPoints(7d12+ConstitutionModifier);", "TooltipDamageList": "RegainHitPoints(7d12+ConstitutionModifier);",
        "UseCosts": "BonusActionPoint:1;WarriorOfTheGods:7;", "PowerLevel": "7"}, using="Shout_WarriorOfTheGods_6"))
    cont = dnd_field("Shout_WarriorOfTheGods", "ContainerSpells", "Spell*.txt").rstrip(";")
    if "_7" not in cont:
        G.SP.append(G.entry("Shout_WarriorOfTheGods", "SpellData", {"ContainerSpells": cont + ";Shout_WarriorOfTheGods_7;"},
                            using="Shout_WarriorOfTheGods", comment="Warrior of the Gods: the 7 dice variant (re-read from dnd55e at each regen)"))


# Beast Master companions and the Steel Defender: dnd55e summons a different template per band of two levels up to 11 (companion HP
# 5 x level: 55 at 11); the 11+ template stayed for good, so a level 20 Ranger's beast had 55 hit points (PHB 2024: 5 + 5 x level) and
# the Proficiency Bonus of level 11. Bands for 13, 15, 17, 19: the same template, with a status applied on summoning that raises its
# hit points by 10 per band and sets its Proficiency Bonus to the owner's (the pattern of gen_summons.py).
SUMMON_BANDS = [("Target_RangersCompanion_Bear", "Ranger"), ("Target_RangersCompanion_Boar", "Ranger"), ("Target_RangersCompanion_GiantSpider", "Ranger"),
                ("Target_RangersCompanion_Raven", "Ranger"), ("Target_RangersCompanion_Wolf", "Ranger"), ("Target_SteelDefender", "Artificer")]
BANDS = (13, 15, 17, 19)


def summon_bands():
    for k, level in enumerate(BANDS, 1):
        G.S.append(G.entry(f"APO_SUMMON_HIGH_{level}", "StatusData", {
            "StatusType": "BOOST", "DisplayName": G.h(f"summon{level}:n", f"Companion at level {level}"),
            "Description": G.h(f"summon{level}:d", f"Hit points +[1] over the level 11 form, and your Proficiency Bonus."),
            "DescriptionParams": str(10 * k), "StackId": "APO_SUMMON_HIGH", "StackPriority": str(k),
            "Boosts": f"ProficiencyBonusOverride(Owner.LevelMapValue(StandardProficiencyBonusScale));IncreaseMaxHP({10 * k})",
            "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"},
            comment=f"Beast Master companion / Steel Defender at {level}+: +{10 * k} hit points (dnd55e's 11+ template stays)"))
    for spell, klass in SUMMON_BANDS:
        props = dnd_field(spell, "SpellProperties", "Spell*.txt")
        segs = [x for x in props.split(";") if x.strip()]
        last = segs[-1]
        m = re.match(rf"(GROUND:)?IF\(ClassLevelHigherOrEqualThan\(11,'{klass}'(?:,context\.Source)?\)\):Summon\((.*)\)$", last)
        assert m, f"{spell}: unexpected last summon band: {last}"
        if f"ClassLevelHigherOrEqualThan(13,'{klass}'" in props:
            continue   # dnd55e caught up
        ground, args = m.group(1) or "", m.group(2)
        out = segs[:-1] + [f"{ground}IF(ClassLevelHigherOrEqualThan(11,'{klass}') and not ClassLevelHigherOrEqualThan(13,'{klass}')):Summon({args})"]
        for level in BANDS:
            cap = f" and not ClassLevelHigherOrEqualThan({level + 2},'{klass}')" if level < 19 else ""
            out.append(f"{ground}IF(ClassLevelHigherOrEqualThan({level},'{klass}'){cap}):Summon({args},APO_SUMMON_HIGH_{level})")
        G.SP.append(G.entry(spell, "SpellData", {"SpellProperties": ";".join(out) + ";"}, using=spell,
                            comment="summon bands for levels 13-19 added (re-read from dnd55e at each regen)"))


# Sun Soul Monk: Searing Arc Strike spends more ki for a higher level Burning Hands (3d6 + 1d6 per level, 2 ki + 1 per level above the
# first); dnd55e's variants run 1-5 at Monk levels 4, 6, 8, 10, 12 - one more level every two Monk levels: 6 to 9 at 14, 16, 18, 20.
def searing_arc_variants():
    for lvl in range(6, 10):
        monk = 2 * lvl + 2
        G.SP.append(G.entry(f"Zone_SearingArcStrike_{lvl}", "SpellData", {
            "SpellSuccess": f"DealDamage({lvl + 2}d6, Fire,Magical);", "DescriptionParams": f"DealDamage({lvl + 2}d6,Fire)",
            "TooltipDamageList": f"DealDamage({lvl + 2}d6,Fire)", "UseCosts": f"BonusActionPoint:1;KiPoint:{lvl + 1};",
            "PowerLevel": str(lvl), "RequirementConditions": f"ClassLevelHigherOrEqualThan({monk},'Monk',context.Source);"},
            using="Zone_SearingArcStrike_5", comment=f"Searing Arc Strike at spell level {lvl} (Monk {monk})"))
    cont = dnd_field("Zone_SearingArcStrike", "ContainerSpells", "Spell*.txt").rstrip(";")
    if "_6" not in cont:
        G.SP.append(G.entry("Zone_SearingArcStrike", "SpellData", {"ContainerSpells": cont + ";" + ";".join(f"Zone_SearingArcStrike_{n}" for n in range(6, 10)) + ";"},
                            using="Zone_SearingArcStrike", comment="Searing Arc Strike: spell levels 6-9 (re-read from dnd55e at each regen)"))


# Illusionist Phantasmal Creatures (user decision 2026-10-13: follow dnd55e's design). dnd55e's Illusion version of Summon Beast / Summon Fey
# summons the creature at the highest slot level the Wizard has: Wizard 5 -> level 3, 7 -> 4, 9 -> 5, 11 -> 6 (templates Wolf_3 ... Wolf_6). The
# slots go on to 7th, 8th and 9th at Wizard 13, 15 and 17 and PTA already has those summon levels (Wolf_7-9, GiantEagle_7-9, RedCap_7-9 from
# gen_upcasts.py), so the bands continue: the same call with the level 7, 8, 9 creature.
ILLUSIONS = [("Target_SummonBeast_Wolf_Illusion", "Target_SummonBeast_Wolf"), ("Target_SummonBeast_GiantEagle_Illusion", "Target_SummonBeast_GiantEagle"),
             ("Target_SummonFey_Illusion", "Target_SummonFey")]


def pta_summon_template(spell):
    for f in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Public", "*", "Stats", "Generated", "Data", "Spell_Upcast79.txt")):
        t = open(f, encoding="utf-8").read()
        m = re.search(rf'new entry "{spell}"\r?\n.*?data "SpellProperties" "[^"]*?Summon\(([0-9a-f-]{{36}})', t, re.S)
        if m:
            return m.group(1)
    raise SystemExit(f"{spell}: not in Spell_Upcast79.txt - run gen_upcasts.py once, then this generator (gen_class_resources.py)")


def illusion_bands():
    for spell, upcast in ILLUSIONS:
        props = dnd_field(spell, "SpellProperties", "Spell*.txt")
        segs = [x for x in props.split(";") if x.strip()]
        last = segs[-1]
        m = re.match(r"(GROUND:)?IF\(ClassLevelHigherOrEqualThan\(11,'Wizard'\)\):Summon\(([0-9a-f-]{36})(.*)\)$", last)
        assert m, f"{spell}: unexpected last band: {last}"
        if "ClassLevelHigherOrEqualThan(13,'Wizard'" in props:
            continue
        ground, rest = m.group(1) or "", m.group(3)
        out = segs[:-1] + [f"{ground}IF(ClassLevelHigherOrEqualThan(11,'Wizard') and not ClassLevelHigherOrEqualThan(13,'Wizard')):Summon({m.group(2)}{rest})"]
        for wizard, level in ((13, 7), (15, 8), (17, 9)):
            cap = f" and not ClassLevelHigherOrEqualThan({wizard + 2},'Wizard')" if wizard < 17 else ""
            out.append(f"{ground}IF(ClassLevelHigherOrEqualThan({wizard},'Wizard'){cap}):Summon({pta_summon_template(f'{upcast}_{level}')}{rest})")
        G.SP.append(G.entry(spell, "SpellData", {"SpellProperties": ";".join(out) + ";"}, using=spell,
                            comment="Illusion summon bands for Wizard 13, 15, 17 = spell levels 7-9 (re-read from dnd55e at each regen)"))


def write():
    illusion_bands()
    searing_arc_variants()
    summon_bands()
    extend_pb_passives()
    balm_variants()
    zealot_variant()
    new_nodes = [(G.gid(f"node:{table}:{level}:{';'.join(attrs.values())}"), name, level, ptype, table, attrs)
                 for table, name, ptype, level, attrs in NODES]
    G.write_stats("ClassResources", "gen_class_resources.py", "class resources 13-20")
    G.patch_files()
    patch_progressions({}, new_nodes, G.marker)
    append_progressions({FIGHTER_16: {"Selectors": MASTERY_PICK}})
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(NODES)} nodes, {len(G.P)} passives, {len(G.SP)} spells, {len(G.S)} statuses")
