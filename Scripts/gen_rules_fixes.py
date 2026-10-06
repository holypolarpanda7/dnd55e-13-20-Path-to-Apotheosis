"""Level 13-20 features brought in line with their rules texts (bg3_lint_rules findings, user-approved 2026-10-05).

Replaces our earlier stand-ins (none of them in the rules) with the source features - texts in the shared library
(D:\\Library\\DnD: PHB 2024 / SRD 5.2.1, excerpts/classes/Rogue.txt, text/important_FA_content.txt = Heroes of Faerun,
excerpts/classes/Artificer.txt = Eberron: Forge of the Artificer):
  Paladin 14   Cleansing Touch       -> Restoring Touch (Lay on Hands removes Blinded/Charmed/Frightened/Paralyzed/Stunned)
  Rogue 13/14  Subtle Strikes (+2)   -> nothing at 13; Devious Strikes at 14 (Daze, Knock Out, Obscure Cunning Strikes)
  Assassin 13  Infiltration Exp.     -> Envenom Weapons (Poison Cunning Strike: +2d6 Poison, ignores Resistance)
  Artificer 14 Magic Item Savant     -> Advanced Artifice (Refreshed Genius) + the table's 4th cantrip
  Banneret 18  Inspiring Surge (Imp.) -> Inspiring Commander (Bolstered Rally 60 ft, Unshakable Bravery)
  Scion 13/17  Unholy Infiltration / Murderous Intent (homebrew) -> Aura of Malevolence; Dread Incarnate (Cutthroat,
               Murderous Intent as written)
dnd55e entries we extend (Lay on Hands, the Sneak Attack spells/interrupts, the Poison Cunning Strike status) are read from
the dnd55e release at regen time, so its updates carry through. Lua: SubclassFeatures.lua (Aura of Malevolence).
Not modelled: Cunning Strike dice costs (dnd55e has none), Deafened (no such condition in BG3), attunement (Magic Item Savant).
Run: python3 Scripts/gen_rules_fixes.py
"""
import glob
import os
import re

from gen_common import DND, Gen, drop_entries, patch_progressions

G = Gen("rulesfixes", "RULES FIXES 2026-10-05")
EXISTING = {}


def dnd(entry, field):
    """A field of a dnd55e stats entry, as released (the extracted dependency pak)."""
    for f in glob.glob(os.path.join(DND, "Stats", "Generated", "Data", "*.txt")):
        s = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(rf'new entry "{re.escape(entry)}"\r?\n(.*?)(?=\r?\nnew entry |\Z)', s, re.S)
        if m:
            v = re.search(rf'data "{re.escape(field)}" "([^"]*)"', m.group(1))
            if v:
                return v.group(1)
    # not set by dnd55e itself (Target_LayOnHands is the base game's): ask the bg3-data index, base + dnd55e resolved
    import json
    import subprocess
    mcp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "bg3-data-mcp")
    code = ("import json,sys;from bg3data import server;s,a=server._testing_store(['dnd55e']);r=s.resolve(sys.argv[1],a);"
            "print(json.dumps((r or {}).get('fields',{}).get(sys.argv[2],[None])[0]))")
    out = subprocess.run(["uv", "run", "-q", "--project", mcp, "python", "-c", code, entry, field],
                         capture_output=True, text=True, env={**os.environ, "UV_PROJECT_ENVIRONMENT": os.environ.get(
                             "UV_PROJECT_ENVIRONMENT", os.path.expanduser("~/.cache/bg3-data-mcp/venv"))})
    try:
        v = json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        v = None
    if v:
        return v
    raise SystemExit(f"{entry}.{field} not found in dnd55e or the base game (gen_rules_fixes.py): {out.stderr[-300:]}")


def extend(entry, field, typ, add):
    """Override a dnd55e entry with itself plus our text appended to one field (dnd55e's own `using` pattern)."""
    G_list = {"SpellData": G.SP, "InterruptData": G.I, "StatusData": G.S}[typ]
    G_list.append(G.entry(entry, typ, {field: dnd(entry, field).rstrip(";") + ";" + add.strip(";")}, using=entry,
                          comment="extended by gen_rules_fixes.py (re-read from dnd55e at each regen)"))


# ---------------------------------------------------------------- Paladin 14 Restoring Touch (PHB 2024)
PALADIN_14 = "44444444-4444-4444-4444-444444444402"
CONDITIONS = [("Blinded", "SG_Blinded"), ("Charmed", "SG_Charmed"), ("Frightened", "SG_Frightened"),
              ("Paralyzed", "SG_Paralyzed"), ("Stunned", "SG_Stunned")]
for cond, grp in CONDITIONS:
    G.spell(f"Target_LayOnHands_Restore{cond}", f"Lay on Hands: Restore ({cond})",
            f"Restoring Touch: spend Lay on Hands to end the {cond} condition on a creature you touch.",
            {"SpellProperties": f"RemoveStatus({grp})", "SpellContainerID": "Target_LayOnHands",
             "RequirementConditions": "HasPassive('Paladin_14_RestoringTouch',context.Source)",
             "TargetConditions": f"Character() and not Dead() and HasAnyStatus({{'{grp}'}})"},
            using="Target_LayOnHands_Cure", icon="Action_Paladin_LayOnHands_Cure")
extend("Target_LayOnHands", "ContainerSpells", "SpellData", ";".join(f"Target_LayOnHands_Restore{c}" for c, _ in CONDITIONS))
G.passive("Paladin_14_RestoringTouch", "Restoring Touch",
          "When you use Lay on Hands on a creature, you can also remove the Blinded, Charmed, Frightened, Paralyzed or Stunned "
          "condition (one Lay on Hands use for each). (The rule also lists Deafened, which BG3 doesn't have.)",
          icon="Action_Paladin_LayOnHands_Cure")
EXISTING[PALADIN_14] = {"PassivesAdded": "Paladin_14_RestoringTouch"}

# ---------------------------------------------------------------- Rogue 13 (nothing) / 14 Devious Strikes (PHB 2024)
ROGUE_13, ROGUE_14 = "33333333-3333-3333-3333-333333333301", "33333333-3333-3333-3333-333333333302"
DEVIOUS = [("Daze", "Constitution", "APO_CUNNINGSTRIKE_DAZED", 1,
            "Daze: the target makes a Constitution saving throw or, on its next turn, can't take Bonus Actions or Reactions."),
           ("KnockOut", "Constitution", "APO_CUNNINGSTRIKE_KNOCKED_OUT", 10,
            "Knock Out: the target makes a Constitution saving throw or falls Unconscious for 1 minute or until it takes damage "
            "(it repeats the save at the end of each of its turns)."),
           ("Obscure", "Dexterity", "BLINDED", 1,
            "Obscure: the target makes a Dexterity saving throw or is Blinded until the end of its next turn.")]
for key, _ab, _st, _t, text in DEVIOUS:
    G.passive(f"CunningStrike_{key}", f"Cunning Strike: {text.split(':')[0]}", text + " (Devious Strikes.)",
              {"Properties": "IsToggled;ToggledDefaultAddToHotbar", "ToggleGroup": "Rogue_5_CunningStrike"},
              icon="PassiveFeature_Generic_Tactical")
G.status("APO_CUNNINGSTRIKE_DAZED", "Dazed", "Can't take Bonus Actions or Reactions this turn (Devious Strikes).",
         {"Boosts": "ActionResourceBlock(BonusActionPoint);ActionResourceBlock(ReactionActionPoint)", "TickType": "EndTurn",
          "StackId": "APO_CUNNINGSTRIKE_DAZED", "StatusGroups": "SG_Condition", "StatusPropertyFlags": "InitiateCombat"},
         icon="statIcons_Dazed")
G.status("APO_CUNNINGSTRIKE_KNOCKED_OUT", "Knocked Out",
         "Unconscious until it takes damage or succeeds on a Constitution saving throw at the end of its turn (Devious Strikes).",
         {"StackId": "APO_CUNNINGSTRIKE_KNOCKED_OUT", "TickType": "EndTurn", "RemoveEvents": "OnDamage;OnTurn",
          "RemoveConditions": "TotalDamageDoneGreaterThan(0) or SavingThrow(Ability.Constitution, ManeuverSaveDC())"},
         using="SLEEPING")
G.passive("Rogue_14_DeviousStrikes", "Devious Strikes",
          "New Cunning Strike options: Daze, Knock Out and Obscure. (Toggle one before your Sneak Attack, like the other "
          "Cunning Strike options; the dice costs aren't modelled, as in dnd55e's Cunning Strike.)",
          icon="PassiveFeature_Generic_Tactical")
SNEAK = [("Interrupt_SneakAttack", "Properties", "InterruptData"), ("Interrupt_SneakAttack_Critical", "Properties", "InterruptData"),
         ("Interrupt_SneakAttack_Rakish", "Properties", "InterruptData"), ("Interrupt_SneakAttack_Rakish_Critical", "Properties", "InterruptData"),
         ("Interrupt_SneakAttack_Poison", "Properties", "InterruptData"), ("Interrupt_SneakAttack_Poison_Critical", "Properties", "InterruptData"),
         ("Projectile_SneakAttack", "SpellSuccess", "SpellData"), ("Projectile_SneakAttack_Rakish", "SpellSuccess", "SpellData"),
         ("Projectile_SneakAttack_Poison", "SpellSuccess", "SpellData"), ("Target_SneakAttack", "SpellSuccess", "SpellData"),
         ("Target_SneakAttack_Rakish", "SpellSuccess", "SpellData"), ("Target_SneakAttack_Poison", "SpellSuccess", "SpellData")]
for entry, field, typ in SNEAK:
    terrify = re.search(r"IF\(HasPassive\('CunningStrike_Terrify'[^;]*;?", dnd(entry, field))
    if not terrify:
        raise SystemExit(f"{entry}.{field}: dnd55e's Terrify clause moved - update gen_rules_fixes.py")
    clause = terrify.group(0).rstrip(";")
    adds = [clause.replace("CunningStrike_Terrify", f"CunningStrike_{key}").replace("Ability.Wisdom", f"Ability.{ab}")
            .replace("ApplyStatus(FRIGHTENED,100,10)", f"ApplyStatus({st},100,{turns})") for key, ab, st, turns, _ in DEVIOUS]
    extend(entry, field, typ, ";".join(adds))
EXISTING[ROGUE_13] = {}
EXISTING[ROGUE_14] = {"PassivesAdded": "Rogue_14_DeviousStrikes;" + ";".join(f"CunningStrike_{k}" for k, *_ in DEVIOUS)}

# ---------------------------------------------------------------- Assassin 13 Envenom Weapons (PHB 2024)
ASSASSIN_13 = "02020202-0202-0202-0202-020202020202"
G.passive("Assassin_13_EnvenomWeapons", "Envenom Weapons",
          "When you use the Poison option of your Cunning Strike, a target that fails the saving throw also takes 2d6 Poison "
          "damage, and again each time it fails the repeat save. Your Poison damage ignores Resistance.",
          {"Boosts": "IgnoreResistance(Poison,Resistant)"}, icon="Action_DivineStrike_Poison_Ranged")
ENVENOM = "IF(HasPassive('Assassin_13_EnvenomWeapons',context.Source)):DealDamage(2d6,Poison,Magical)"
G.S.append(G.entry("CUNNINGSTRIKE_POISON", "StatusData", {"OnApplyFunctors": ENVENOM, "TickFunctors": ENVENOM},
                   using="CUNNINGSTRIKE_POISON", comment="Envenom Weapons (gen_rules_fixes.py): damage on the failed save"))
EXISTING[ASSASSIN_13] = {"PassivesAdded": "Assassin_13_EnvenomWeapons"}

# ---------------------------------------------------------------- Artificer 14 Advanced Artifice (Eberron: Forge of the Artificer)
ARTIFICER_14 = "cccccccc-cccc-cccc-cccc-ccccccccc902"
ARTIFICER_CANTRIPS = "d5f17616-b3cf-47ff-b898-3e37c3961034"  # dnd55e's level 1 cantrip list
G.passive("Artificer_14_AdvancedArtifice", "Advanced Artifice",
          "Refreshed Genius: when you finish a Short Rest, you regain one expended use of Flash of Genius. (Magic Item Savant - "
          "attuning to five magic items - has no counterpart in BG3, which has no attunement.)",
          {"StatsFunctorContext": "OnShortRest", "StatsFunctors": "RestoreResource(FlashOfGenius,1,0)"}, icon="Apo_Feat_MagicItemSavant")
EXISTING[ARTIFICER_14] = {"PassivesAdded": "Artificer_14_AdvancedArtifice",
                          "Selectors": f"SelectSpells({ARTIFICER_CANTRIPS},1,0,,,,AlwaysPrepared)"}

# ---------------------------------------------------------------- Banneret 18 Inspiring Commander (Heroes of Faerun)
BANNERET_18 = "09090909-0909-0909-0909-090909090903"
RALLY = " or ".join(f"SpellId('{s}')" for b in ("Target_GroupRecovery", "Target_RallyingSurge")
                    for s in [b] + [f"{b}_{i}" for i in range(1, 7)])
G.passive("Banneret_18_InspiringCommander", "Inspiring Commander",
          "Bolstered Rally: Group Recovery and Rallying Surge reach allies in a 60-foot Emanation. Unshakable Bravery: you have "
          "Immunity to the Charmed and Frightened conditions.",
          {"Boosts": f"UnlockSpellVariant({RALLY},ModifyTargetRadius(Multiplicative,2.0));StatusImmunity(SG_Charmed);"
                     "StatusImmunity(SG_Frightened)"}, icon="Apo_Feat_ApotheosisInspiringSurge")
EXISTING[BANNERET_18] = {"PassivesAdded": "Banneret_18_InspiringCommander"}

# ---------------------------------------------------------------- Scion of the Three 13 / 17 (Heroes of Faerun)
SCION_11, SCION_13, SCION_17 = ("05050505-0505-0505-0505-050505050501", "05050505-0505-0505-0505-050505050502",
                                "05050505-0505-0505-0505-050505050503")
G.passive("DeadThree_13_AuraOfMalevolence", "Aura of Malevolence",
          "When you use Bloodthirst and teleport, each enemy within 10 feet of your destination takes damage equal to your "
          "Intelligence modifier, of your Dread Allegiance's type (Bane: Psychic, Bhaal: Poison, Myrkul: Necrotic).",
          icon="PassiveFeature_Generic_Threat")
G.passive("DeadThree_17_DreadIncarnate", "Dread Incarnate",
          "Cutthroat: you regain one expended use of Bloodthirst when you finish a Short Rest. Murderous Intent: when you roll "
          "damage for a weapon attack (your Sneak Attack included), a 1 or 2 on a die counts as a 3.",
          {"StatsFunctorContext": "OnShortRest", "StatsFunctors": "RestoreResource(Bloodthirst,1,0)",
           "Boosts": "IF(IsWeaponAttack()):MinimumRollResult(Damage,3)"}, icon="PassiveFeature_Generic_Threat")
EXISTING[SCION_11] = None      # removed a passive dnd55e no longer grants at 11 (our old Murderous Intent move)
EXISTING[SCION_13] = {"PassivesAdded": "DeadThree_13_AuraOfMalevolence"}
EXISTING[SCION_17] = {"PassivesAdded": "DeadThree_17_DreadIncarnate"}

RETIRED_PASSIVES = ["Rogue_SubtleStrikes", "Paladin_CleansingTouch", "Assassin_InfiltrationExpertise", "Artificer_MagicItemSavant",
                    "Banneret_InspiringSurge_Improved", "DeadThree_UnholyInfiltration", "DeadThree_11_MurderousIntent"]
RETIRED_SPELLS = ["Shout_Apotheosis_CleansingTouch", "Shout_Apotheosis_InspiringSurge"]


def write():
    drop_entries("Passive.txt", RETIRED_PASSIVES)
    drop_entries("Spell_Shout.txt", RETIRED_SPELLS)
    G.write_stats("RulesFixes", "gen_rules_fixes.py", "rules-check fixes 2026-10-05")
    G.patch_files()
    patch_progressions(EXISTING, [], G.marker)
    G.patch_loca()


if __name__ == "__main__":
    write()
    print(f"{len(G.P)} passives, {len(G.S)} statuses, {len(G.SP)} spells, {len(G.I)} interrupts; "
          f"{len(EXISTING)} nodes patched, {len(RETIRED_PASSIVES) + len(RETIRED_SPELLS)} retired entries")
