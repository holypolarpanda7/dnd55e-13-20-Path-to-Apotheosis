"""Sanguine Thief (Grim Hollow Player's Guide, Rogue; added to dnd55e in 4.13.9.0 with levels 3-12 only) levels 13-20.

Third caster on the Wizard proxy, like the Arcane Trickster (Scripts/gen_subclass_features.py): 3rd-level slots at 13 (2) and 16 (1),
a 4th-level slot at 19, a prepared spell more at 13, 14, 16, 19, 20 (PHB 2024 third-caster table). dnd55e's Sangromancy Dice are
Hit Point Dice (d8) and the pool equals the Sneak Attack dice (2 at 3 ... 6 at 11), so it grows to 7 at 13, 8 at 15, 9 at 17, 10 at 19.
Features (Grim Hollow Player's Guide, via fan-wiki summaries - the book text isn't in the library; numbers: grokipedia.com/page/Sanguine_Thief):
  13 Bloodstitch: Magic action, spend 3 Hit Point / Sangromancy Dice; 30 ft emanation; Dexterity save against your spell save DC,
     3d8 Necrotic (half on a success); a creature reduced to 0 Hit Points gives you one die back; once per Short or Long Rest.
  17 Bloody Exit: Reaction when an attack roll hits you, spend 5 dice: the attack misses, you teleport up to 30 ft and make a
     melee weapon attack (+5d8 Necrotic on a hit); once per Short or Long Rest.
Spell lists: dnd55e only ships "Sanguine Thief SLevel 1/2" (the Wizard lists plus the Sangromancy spells); levels 3 and 4 follow the same
rule (Wizard SLevel 3 / 4 + the Wizard Savant Sangromancy list's 3rd / 4th level spells), cumulative in game through MergedInto.

Owns Stats/Generated/Data/{Passive,Status,Spell,Interrupt}_SanguineThief.txt, SpellLists.lsx and Progressions.lsx between SANGUINE THIEF
13-20 markers, loca.
Run: python3 Scripts/gen_sanguine_thief.py
"""
import os
import re

from gen_common import DND, Gen, PUB, patch_progressions, SHOUT_ANIM

G = Gen("sanguinethief", "SANGUINE THIEF 13-20")
TABLE = "0d7fc95e-bc63-4f54-b839-307f5266a5b9"
SUBCLASS = "f6a59c66-01a0-4ed1-9dae-f0e5e11681a0"
ST1, ST2 = "22a5a7dd-b869-4b58-812c-74344a0df44e", "6fa0def5-0a99-4c43-bea1-215d54a21558"
WIZ3, WIZ4 = "22755771-ca11-49f4-b772-13d8b8fecd93", "820b1220-0385-426d-ae15-458dc8a6f5c0"
SAVANT = "398d9fdb-0101-4226-b2eb-08a2dae9accb"          # Wizard Savant Sangromancy (1st-4th level)
SAVANT_L3 = ["Target_BloodBond", "Target_Reanimate", "Target_SanguinePoppet"]
SAVANT_L4 = ["Target_CircleOfScarlet", "Target_DarkSacrament", "Shout_ViscousSheath"]
TAG = "SanguineThiefSpells"
ST3, ST4 = G.gid("list:SanguineThiefSLevel3"), G.gid("list:SanguineThiefSLevel4")
ST13, ST14 = G.gid("list:SanguineThiefSLevel1to3"), G.gid("list:SanguineThiefSLevel1to4")


def dnd_lists():
    t = open(os.path.join(DND, "Lists", "SpellLists.lsx"), encoding="utf-8").read()
    out = {}
    for b in re.findall(r'<node id="SpellList">(.*?)</node>', t, re.S):
        u = re.search(r'id="UUID"[^>]*value="([^"]*)"', b)
        s = re.search(r'id="Spells"[^>]*value="([^"]*)"', b)
        if u and s:
            out[u.group(1)] = [x for x in s.group(1).split(";") if x]
    return out


def union(*lists):
    seen, out = set(), []
    for lst in lists:
        for s in lst:
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def spell_lists():
    L = dnd_lists()
    for u in (ST1, ST2, WIZ3, WIZ4, SAVANT):
        assert u in L, f"dnd55e list {u} not found"
    for s in SAVANT_L3 + SAVANT_L4:
        assert s in L[SAVANT], f"{s} is no longer on dnd55e's Sangromancy Savant list"
    st3 = union(L[WIZ3], SAVANT_L3)
    st4 = union(L[WIZ4], SAVANT_L4)
    rows = []

    def node(name, comment, spells, uuid, merged=None):
        m = f'\n                    <attribute id="MergedInto" type="guid" value="{merged}"/>' if merged else ""
        rows.append(f'''                <node id="SpellList">
                    <attribute id="Comment" type="LSString" value="{comment}"/>{m}
                    <attribute id="Name" type="FixedString" value="{name}"/>
                    <attribute id="Spells" type="LSString" value="{';'.join(spells)}"/>
                    <attribute id="UUID" type="guid" value="{uuid}"/>
                </node>
''')
    node("Sanguine Thief SLevel 3", "Sanguine Thief 3rd-level spells (13-18): Wizard SLevel 3 + Sangromancy", st3, ST3)
    node("Sanguine Thief SLevel 1 to 3", "Sanguine Thief levels 1-2 merged into SLevel 3 (cumulative, as dnd55e's 1 to 2)",
         union(L[ST1], L[ST2]), ST13, merged=ST3)
    node("Sanguine Thief SLevel 4", "Sanguine Thief 4th-level spells (19-20): Wizard SLevel 4 + Sangromancy", st4, ST4)
    node("Sanguine Thief SLevel 1 to 4", "Sanguine Thief levels 1-3 merged into SLevel 4 (cumulative)",
         union(L[ST1], L[ST2], st3), ST14, merged=ST4)
    return rows


# ---------------------------------------------------------------- 13 Bloodstitch
G.status("APO_BLOODSTITCH_DIE", "Bloodstitch", "You regain a Hit Point Die.",
         {"StatusPropertyFlags": "DisableOverhead;DisablePortraitIndicator", "StackId": "APO_BLOODSTITCH_DIE",
          "OnApplyFunctors": "RestoreResource(HitPointDice08,1,0)"}, icon="Apo_Spell_Bloodstitch")
BS_TEXT = ("As a Magic action, spend 3 Hit Point Dice (Sangromancy Dice) to loose needle-like shards of blood in a 9 m (30 ft) emanation. "
           "Each enemy makes a Dexterity saving throw against your spell save DC, taking 3d8 Necrotic damage on a failed save or half as much on a "
           "success. Each creature reduced to 0 Hit Points gives you back one Hit Point Die. Once per Short or Long Rest.")
G.spell("Shout_Apo_Bloodstitch", "Bloodstitch", BS_TEXT,
        {"SpellType": "Shout", "Level": "0", "SpellSchool": "Necromancy", "AreaRadius": "9", "MemoryCost": "0",
         "TargetConditions": "Enemy() and not Dead()", "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())",
         "SpellSuccess": "DealDamage(3d8,Necrotic,Magical)",
         "SpellFail": "DealDamage((3d8)/2,Necrotic,Magical)",
         "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsHarmful", "TooltipAttackSave": "Dexterity",
         "TooltipDamageList": "DealDamage(3d8,Necrotic)", "TooltipOnSave": "f762efbb-f8f1-493e-b248-2de1567b4bd2",
         "UseCosts": "ActionPoint:1;HitPointDice08:3", "Cooldown": "OncePerShortRest", "VerbalIntent": "Damage", "ContainerSpells": "", "SpellContainerID": "",
         "SpellStyleGroup": "Class", "CastSound": "Spell_Cast_Cleric_DestructiveWave_L4to5",
         "TargetSound": "Spell_Impact_Cleric_DestructiveWave_L4to5"},
        using="Shout_DestructiveWave", icon="Apo_Spell_Bloodstitch",
        comment="Shout_DestructiveWave's animation and effects; Hit Point Dice cost as dnd55e's Sangromancy spells (HitPointDice08:n).")
G.passive("SanguineThief_13_Bloodstitch", "Bloodstitch", BS_TEXT,
          {"Boosts": "UnlockSpell(Shout_Apo_Bloodstitch)", "Conditions": "SpellId('Shout_Apo_Bloodstitch') and HasHPLessThan(1) and Enemy() and Character()",
           "StatsFunctorContext": "OnDamage", "StatsFunctors": "ApplyStatus(SELF,APO_BLOODSTITCH_DIE,100,0)"},
          icon="Apo_Spell_Bloodstitch",
          comment="The die comes back through an OnDamage passive functor, as dnd55e DarkOnesBlessing: an OnCastHit interrupt runs before the zone's damage "
                  "lands and an OnDeath one after the combat and the statuses are gone (both tried in game 2026-10-16).")

# ---------------------------------------------------------------- 17 Bloody Exit
BE_TEXT = ("When an attack roll hits you, you can use your Reaction and spend 5 Hit Point Dice (Sangromancy Dice): the attack misses, you "
           "strike back with one melee weapon attack, which deals an extra 5d8 Necrotic damage on a hit, and until the end of your next turn you can "
           "teleport up to 9 m (30 ft) to an unoccupied space you can see without an action. Once per Short or Long Rest.")
G.status("APO_BLOODY_EXIT_STEP", "Bloody Exit", "You can teleport up to 9 m (30 ft) to an unoccupied space you can see, without an action.",
         {"Boosts": "UnlockSpell(Target_Apo_BloodyExit_Teleport)", "StatusPropertyFlags": "DisableOverhead", "StackId": "APO_BLOODY_EXIT_STEP"},
         icon="Apo_Spell_BloodyExit", comment="A reaction has no position to choose, so the teleport is a free spell for your next turn (UseSpell with a position did nothing, 2026-10-16).")
G.spell("Target_Apo_BloodyExit_Teleport", "Bloody Exit: Teleport", "Teleport up to 9 m (30 ft) to an unoccupied space you can see.",
        {"UseCosts": "", "MemoryCost": "0", "Level": "0", "SpellFlags": "HasVerbalComponent;Temporary", "RechargeValues": "",
         "SpellProperties": "GROUND:TeleportSource();GROUND:RemoveStatus(SELF,APO_BLOODY_EXIT_STEP)", "ContainerSpells": ""},
        using="Target_MistyStep", icon="Apo_Spell_BloodyExit")
G.spell("Target_Apo_BloodyExit_Strike", "Bloody Exit: Strike", "Make one melee weapon attack; on a hit it deals an extra 5d8 Necrotic damage.",
        {"UseCosts": "", "DualWieldingUseCosts": "", "SpellFlags": "IsAttack;IsMelee;IsHarmful;Temporary",
         "SpellProperties": "", "TooltipDamageList": "DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType);DealDamage(5d8,Necrotic)",
         "SpellSuccess": "DealDamage(max(1,MainMeleeWeapon), MainMeleeWeaponDamageType);ExecuteWeaponFunctors(MainHand);DealDamage(5d8,Necrotic,Magical)"},
        using="Target_MainHandAttack", icon="Apo_Spell_BloodyExit")
G.resource("ApoBloodyExit", 1, "ShortRest", "Bloody Exit", "Bloody Exit can be used once per Short or Long Rest.")   # an interrupt's Cooldown isn't enforced: dnd55e YouDieOnMyCommand uses a resource too
G.interrupt("Interrupt_Apo_BloodyExit", "Bloody Exit", BE_TEXT,
            {"InterruptContext": "OnPostRoll", "InterruptContextScope": "Self", "Container": "YesNoDecision",
             "Conditions": "IsAbleToReact(context.Observer) and Self(context.Target,context.Observer) and HasInterruptedAttack() and "
                           "IsFlatValueInterruptInteresting(99, context.Source) and not AnyEntityIsItem()",
             "Cost": "ReactionActionPoint:1;ApoBloodyExit:1;HitPointDice08:5",
             "Properties": "IF(HasInterruptedAttack()):AdjustRoll(-99);ApplyStatus(OBSERVER_OBSERVER,APO_BLOODY_EXIT_STEP,100,2);"
                           "IF(not DistanceToEntityGreaterThan(3,context.ObserverPosition,context.Source)):UseSpell(OBSERVER_SOURCE,Target_Apo_BloodyExit_Strike,true,true,true)",
             "InterruptDefaultValue": "Ask;Enabled"},
            icon="Apo_Spell_BloodyExit",
            comment="OnPostRoll + AdjustRoll as the Shield spell (Interrupt_MAG_Shield); the cost is a Reaction and five d8 Hit Point Dice.")
G.passive("SanguineThief_17_BloodyExit", "Bloody Exit", BE_TEXT, {"Boosts": "UnlockInterrupt(Interrupt_Apo_BloodyExit);ActionResource(ApoBloodyExit,1,0)"},
          icon="Apo_Spell_BloodyExit")

# ---------------------------------------------------------------- progression 13-20
NODES = []
for lvl in range(13, 21):
    boosts = []
    if lvl in (13, 15, 17, 19):
        boosts.append("ActionResource(HitPointDice08,1,0)")   # Sangromancy Dice = Sneak Attack dice (7, 8, 9, 10)
    slot = {13: "ActionResource(SpellSlot,2,3)", 16: "ActionResource(SpellSlot,1,3)", 19: "ActionResource(SpellSlot,1,4)"}.get(lvl)
    if slot:
        boosts.append(slot)
    passives = {13: ["UnlockedSpellSlotLevel3", "SanguineThief_13_Bloodstitch"], 17: ["SanguineThief_17_BloodyExit"],
                }.get(lvl, [])
    learn = 1 if lvl in (13, 14, 16, 19, 20) else 0
    attrs = {"Selectors": f"SelectSpells({ST4 if lvl >= 19 else ST3},{learn},1,{TAG})"}
    if passives:
        attrs["PassivesAdded"] = ";".join(passives)
    if boosts:
        attrs["Boosts"] = ";".join(boosts)
    NODES.append((G.gid(f"node:SanguineThief:{lvl}"), "SanguineThief", lvl, 1, TABLE, attrs))


def write():
    G.write_stats("SanguineThief", "gen_sanguine_thief.py", "Sanguine Thief 13-20")
    G.patch_files()
    G._between(os.path.join(PUB, "Lists", "SpellLists.lsx"), spell_lists())
    patch_progressions({}, NODES, G.marker)
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.I)} interrupts, {len(NODES)} nodes, 4 lists")
