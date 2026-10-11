"""Portal Jumper (Arcana Unleashed, Origin feat) - added to the Human origin-feat pick, 2026-10-10 (user request).

An exception to VISION.md (levels 1-12 are dnd55e's), approved 2026-10-10: dnd55e does not have the feat yet and its author
plans to add the Arcana Unleashed origin feats. Drop this generator (and PortalJumper.lua / the MCM setting) when dnd55e ships it.

Rules text (D:\\Library\\DnD excerpts/subclasses/ArcanaUnleashed.txt, "Portal Jumper", Origin Feat):
  Otherworldly Resilience. Resistance to one of Necrotic, Psychic or Radiant (choose when you select this feat).
  Portal Step. Spend 15 feet of movement to teleport to an unoccupied space you can see within 15 feet of yourself. Uses equal
  to your Proficiency Bonus, once per turn, regained on a Long Rest.

How dnd55e builds the pick: Human's "HumanHuman" progression offers SelectPassives(51988e80-..., "Human Origin Feat"), a passive
list of OriginFeat_* passives. A choice inside a feat can't be offered there, so (as dnd55e does for Magic Initiate) one
passive per resistance. Our list PortalJumperOrigin has MergedInto = dnd55e's list, so dnd55e's own list is untouched and keeps
following its updates. PortalJumper.lua adds/removes the three entries live from the MCM setting `portal_jumper`.
Uses: PB 2 (levels 1-4), +1 above levels 4/8/12/16 (the same ladder dnd55e's Lucky uses, extended to PB 6 for 13-20).

Run: python3 Scripts/gen_portal_jumper.py
"""
from gen_common import Gen

G = Gen("portaljumper", "PORTAL JUMPER 2026-10-10")
HUMAN_ORIGIN_FEAT_LIST = "51988e80-d7cc-4351-aa7d-83b8ba3f989a"   # dnd55e "Human Origin Feat"
SPELL = "Target_Apo_PortalStep"
RES = "PortalStep"
TYPES = ("Necrotic", "Psychic", "Radiant")

G.resource(RES, 6, "Rest", "Portal Step", "Teleport up to 15 feet by spending 15 feet of movement. Uses equal to your Proficiency Bonus; returns on a Long Rest.")

G.spell(SPELL, "Portal Step",
        "Spend 15 feet of movement to teleport to an unoccupied space you can see within 15 feet of yourself. You can do this "
        "a number of times equal to your Proficiency Bonus, but only once per turn, and you regain all expended uses when you "
        "finish a Long Rest.",
        {"SpellType": "Target", "Level": "0", "SpellProperties": "GROUND:TeleportSource()",
         "TargetRadius": "4.5", "TargetConditions": "CanStand('') and not Character() and not Self()",
         "UseCosts": f"Movement:4.5;{RES}:1", "Cooldown": "OncePerTurn",
         "SpellFlags": "HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold", "CastTextEvent": "Cast",
         "VerbalIntent": "Utility"},
        using="Target_MistyStep", icon="Spell_Conjuration_DimensionDoor",
        comment="Not a spell (no IsSpell/slot/verbal component): a feat benefit that costs 15 ft (4.5 m) of movement.")

LADDER = ";".join(f"IF(CharacterLevelGreaterThan({n})):ActionResource({RES},1,0)" for n in (4, 8, 12, 16))
names = []
for t in TYPES:
    n = f"OriginFeat_PortalJumper_{t}"
    names.append(n)
    G.passive(n, f"Origin Feat: Portal Jumper ({t})",
              f"Otherworldly Resilience: you have Resistance to {t} damage. Portal Step: you can spend 15 feet of movement to "
              "teleport to an unoccupied space you can see within 15 feet of yourself (a number of times equal to your "
              "Proficiency Bonus, once per turn, regained on a Long Rest).",
              {"Boosts": f"Resistance({t},Resistant);UnlockSpell({SPELL});ActionResource({RES},2,0);{LADDER}",
               "PriorityOrder": "600"},
              icon="Spell_Conjuration_DimensionDoor",
              comment="Arcana Unleashed origin feat; one entry per Otherworldly Resilience choice (dnd55e's Magic Initiate precedent).")

G.lists.append(f"""                <node id="PassiveList">
                    <attribute id="MergedInto" type="guid" value="{HUMAN_ORIGIN_FEAT_LIST}"/>
                    <attribute id="Name" type="FixedString" value="PortalJumperOrigin"/>
                    <attribute id="Passives" type="LSString" value="{','.join(names)}"/>
                    <attribute id="UUID" type="guid" value="{G.gid('list:PortalJumperOrigin')}"/>
                </node>
""")

if __name__ == "__main__":
    G.write_stats("PortalJumper", "gen_portal_jumper.py", "Portal Jumper origin feat 2026-10-10")
    G.patch_files()
    G.patch_loca()
    print(f"{len(G.P)} passives, {len(G.SP)} spell, 1 resource, list {G.gid('list:PortalJumperOrigin')} (merged into the Human origin-feat list)")
