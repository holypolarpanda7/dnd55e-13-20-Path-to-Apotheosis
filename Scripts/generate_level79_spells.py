"""Generate the PHB 2024 level 7-9 spell layer for Path to Apotheosis.

Single source of truth for every NEW high-level spell: design tables below
emit stats, support statuses, localization, spell-list registration, and the
design doc. Tweak a design here and re-run; all outputs regenerate.

Outputs:
  Public/<guid>/Stats/Generated/Data/Spell_Epic79.txt      (overwritten)
  Public/<guid>/Stats/Generated/Data/Status_Epic79.txt     (overwritten)
  Mods/<guid>/Localization/English/dnd55e-Apotheosis.xml  (hsp*/hst* entries replaced)
  Public/<guid>/Lists/SpellLists.lsx                       (spells unioned into class lists)
  docs/SPELLS-7-9.md                                       (overwritten)

Run: python Scripts/generate_level79_spells.py

Design doctrine:
- Every spell inherits a PROVEN parent via `using` (vanilla or Apotheosis) so
  animations, sounds, and targeting come free; only mechanics are overridden.
- Spells with no direct BG3 translation (plane travel, downtime rituals) are
  redesigned into meaningful combat/utility effects; the doc records each call.
- Two spells carry Script Extender riders (see BootstrapServer.lua):
  Finger of Death raises a zombie from its kill; Clone revives its bearer.
"""

from __future__ import annotations

import re
from pathlib import Path

GUID = "dnd55e_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa"
OUT_SPELLS = Path(f"Public/{GUID}/Stats/Generated/Data/Spell_Epic79.txt")
OUT_STATUSES = Path(f"Public/{GUID}/Stats/Generated/Data/Status_Epic79.txt")
LOCA = Path(f"Mods/{GUID}/Localization/English/dnd55e-Apotheosis.xml")
SPELL_LISTS = Path(f"Public/{GUID}/Lists/SpellLists.lsx")
DOC = Path("docs/SPELLS-7-9.md")


def handle(prefix: str, hid: int) -> str:
    return prefix + "0" * 24 + f"{hid:04d}"


def slot_cost(level: int) -> str:
    return f"ActionPoint:1;SpellSlotsGroup:1:1:{level}"


# ---------------------------------------------------------------------------
# Spell designs.  classes: wiz sor clr dru brd wlk (list registration below).
# hid: stable loca handle id (name = hid, description = hid+1). Never reuse.
# ---------------------------------------------------------------------------

SPELLS = [
    # ============================= LEVEL 7 =============================
    dict(entry="Projectile_Apo_DelayedBlastFireball", using="Projectile_Fireball",
         level=7, school="Evocation", hid=7001, classes=["sor", "wiz"],
         name="Delayed Blast Fireball",
         desc="A bead of fire streaks out and detonates with catastrophic force, dealing 12d6 Fire damage to everything caught in the blast.",
         design="Straight damage upgrade of Fireball; the 5e delay mechanic has no BG3 turn hook, traded for raw payload.",
         fields={
             "SpellSuccess": "DealDamage(12d6,Fire,Magical)",
             "SpellFail": "DealDamage((12d6)/2,Fire,Magical)",
             "TooltipDamageList": "DealDamage(12d6,Fire)",
         }),
    dict(entry="Shout_Apo_DivineWord", using="Shout_DestructiveWave",
         level=7, school="Evocation", hid=7003, classes=["clr"],
         name="Divine Word",
         desc="As a Bonus Action you utter a word of power. Each enemy within 9m makes a Charisma save. On a failure: 20 HP or fewer, it dies; 21-30 HP, Blinded and Stunned for 1 hour; 31-40 HP, Blinded for 10 minutes. A Celestial, Elemental, Fey or Fiend that fails is cast back to its home plane.",
         design="PHB 2024 (user decision 2026-10-04, replacing scaled 50/100/150 thresholds): Bonus Action; HP tiers 20/30/40; the 41-50 "
                "Deafened-only tier and the Deafened parts have no BG3 status; 1 hour = 600 turns, 10 minutes = 100; the planar banishment "
                "(can't return for 24 hours) is Kill() like the base game's Dispel Evil and Good dismissal, with its Raphael guard.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Charisma, SourceSpellDC())",
             "SpellSuccess": "IF((Tagged('CELESTIAL') or Tagged('ELEMENTAL') or Tagged('FEY') or Tagged('FIEND')) and not Tagged('LOW_HOUSEOFHOPE_IDENTIFY_RAPHAEL') and not Tagged('LOW_HOUSEOFHOPE_RAPHAELIAN_CAMBION')):Kill();"
                             "IF(HasHPLessThan(21)):Kill();"
                             "IF(HasHPLessThan(31) and not HasHPLessThan(21)):ApplyStatus(STUNNED,100,600);"
                             "IF(HasHPLessThan(31) and not HasHPLessThan(21)):ApplyStatus(BLINDED,100,600);"
                             "IF(HasHPLessThan(41) and not HasHPLessThan(31)):ApplyStatus(BLINDED,100,100)",
             "SpellFail": "",
             "TooltipDamageList": "",
             "AreaRadius": "9",
             "TargetConditions": "Enemy() and not Dead()",
             "UseCosts": "BonusActionPoint:1;SpellSlotsGroup:1:1:7",
         }),
    dict(entry="Target_Apo_FingerOfDeath", using="Target_Blight",
         level=7, school="Necromancy", hid=7005, classes=["sor", "wlk", "wiz"],
         name="Finger of Death",
         desc="Negative energy ravages a creature for 7d8+30 Necrotic damage (Constitution save for half). A humanoid slain by this spell rises at the start of the next turn as a zombie under your command.",
         design="Zombie-on-kill implemented as a Script Extender rider on the APO_FINGER_OF_DEATH marker.",
         fields={
             "SpellSuccess": "DealDamage(7d8+30,Necrotic,Magical);ApplyStatus(APO_FINGER_OF_DEATH,100,1)",
             "SpellFail": "DealDamage((7d8+30)/2,Necrotic,Magical)",
             "TooltipDamageList": "DealDamage(7d8+30,Necrotic)",
         }),
    dict(entry="Target_Apo_FireStorm", using="Target_FlameStrike",
         level=7, school="Evocation", hid=7007, classes=["clr", "dru", "sor"],
         name="Fire Storm",
         desc="A storm of roaring flame fills a wide area, dealing 7d10 Fire damage (Dexterity save for half).",
         design="FlameStrike chassis widened to 8m, single fire payload.",
         fields={
             "SpellSuccess": "DealDamage(7d10,Fire,Magical)",
             "SpellFail": "DealDamage((7d10)/2,Fire,Magical)",
             "TooltipDamageList": "DealDamage(7d10,Fire)",
             "AreaRadius": "8",
         }),
    dict(entry="Zone_Apo_PrismaticSpray", using="Zone_ConeOfCold",
         level=7, school="Evocation", hid=7009, classes=["sor", "wiz"],
         name="Prismatic Spray",
         desc="Eight rays of clashing colour flash from your hand in a cone, battering everything caught in them with 2d6 each of Fire, Cold, Lightning, Acid and Poison damage (Dexterity save for half).",
         design="Random-ray table flattened into a fixed five-type barrage - same expected damage, resist-proof spread.",
         fields={
             "SpellSuccess": "DealDamage(2d6,Fire,Magical);DealDamage(2d6,Cold,Magical);DealDamage(2d6,Lightning,Magical);DealDamage(2d6,Acid,Magical);DealDamage(2d6,Poison,Magical)",
             "SpellFail": "DealDamage((2d6)/2,Fire,Magical);DealDamage((2d6)/2,Cold,Magical);DealDamage((2d6)/2,Lightning,Magical);DealDamage((2d6)/2,Acid,Magical);DealDamage((2d6)/2,Poison,Magical)",
             "TooltipDamageList": "DealDamage(2d6,Fire);DealDamage(2d6,Cold);DealDamage(2d6,Lightning);DealDamage(2d6,Acid);DealDamage(2d6,Poison)",
         }),
    dict(entry="Target_Apo_Forcecage", using="Target_ResilientSphere",
         level=7, school="Evocation", hid=7011, classes=["brd", "wlk", "wiz"],
         name="Forcecage",
         desc="A cage of invisible force imprisons an enemy for 3 turns: it cannot act, and nothing can harm it. No saving throw, no concentration.",
         design="Otiluke's sphere turned offensive: guaranteed 3-turn removal of one enemy (nothing in, nothing out) mirrors the 5e no-save cage.",
         fields={
             "TargetConditions": "Enemy() and not Dead()",
             "SpellProperties": "ApplyStatus(RESILIENT_SPHERE,100,3)",
             "TooltipStatusApply": "ApplyStatus(RESILIENT_SPHERE,100,3)",
             "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsHarmful",
         }),
    dict(entry="Target_Apo_MordenkainensSword", using="Target_SpiritualWeapon_Greatsword",
         level=7, school="Evocation", hid=7013, classes=["brd", "wiz"],
         name="Mordenkainen's Sword",
         desc="You conjure a blade of pure force that fights at your command, striking with the strength of a 7th-level summoning.",
         design="Spiritual Weapon greatsword chassis at spell level 7 (summon scaling handles the rest).",
         fields={}),
    dict(entry="Shout_Apo_ConjureCelestial", using="Shout_SpiritGuardians",
         level=7, school="Conjuration", hid=7015, classes=["clr"],
         name="Conjure Celestial",
         desc="A celestial spirit surrounds you: enemies within 9m suffer 3d8 Radiant damage each turn (Wisdom save), while nearby allies are continually Blessed.",
         design="2024's radiant-spirit version as a dual aura on the Spirit Guardians engine: wrath for enemies, Bless for allies.",
         fields={
             "SpellProperties": "ApplyStatus(SELF,APO_CELESTIAL_AURA,100,10)",
             "TooltipStatusApply": "ApplyStatus(APO_CELESTIAL_AURA,100,10)",
         }),
    dict(entry="Target_Apo_Etherealness", using="Target_Invisibility_Greater",
         level=7, school="Transmutation", hid=7017, classes=["brd", "sor", "wlk", "wiz"],
         name="Etherealness",
         desc="You step partly into the Ethereal Plane for 10 turns: unseen by material eyes and drifting free, with greatly extended movement.",
         design="Border-Ethereal travel translated to Greater Invisibility + bonus movement - the scouting/escape role the plane serves.",
         fields={
             "SpellProperties": "ApplyStatus(GREATER_INVISIBILITY,100,10);ApplyStatus(APO_ETHEREAL,100,10)",
             "TooltipStatusApply": "ApplyStatus(GREATER_INVISIBILITY,100,10);ApplyStatus(APO_ETHEREAL,100,10)",
         }),
    dict(entry="Target_Apo_MirageArcane", using="Target_FlameStrike",
         level=7, school="Illusion", hid=7019, classes=["brd", "dru", "wiz"],
         name="Mirage Arcane",
         desc="You rewrite the terrain in enemy minds across a huge area. Those who fail an Intelligence save wander lost: Slowed for 3 turns and Blinded for 2.",
         design="Terrain illusion re-cast as a large-area mass disorientation debuff (illusory ground is not expressible in BG3).",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
             "SpellSuccess": "ApplyStatus(SLOW,100,3);ApplyStatus(BLINDED,100,2)",
             "SpellFail": "",
             "TooltipDamageList": "",
             "TooltipStatusApply": "ApplyStatus(SLOW,100,3);ApplyStatus(BLINDED,100,2)",
             "AreaRadius": "12",
             "TargetConditions": "Enemy() and not Dead()",
         }),
    dict(entry="Shout_Apo_MagnificentMansion", using="Shout_PrayerOfHealing",
         level=7, school="Conjuration", hid=7021, classes=["brd", "wiz"],
         name="Mordenkainen's Magnificent Mansion",
         desc="The mansion's door opens a crack: allies around you snatch a moment of its comfort, healing 4d8 and gaining Sanctuary for 2 turns.",
         design="Downtime demiplane turned into a mid-combat respite: group heal + short Sanctuary.",
         fields={
             "SpellProperties": "RegainHitPoints(4d8);ApplyStatus(SANCTUARY,100,2)",
             "TooltipDamageList": "RegainHitPoints(4d8)",
             "TooltipStatusApply": "ApplyStatus(SANCTUARY,100,2)",
         }),
    dict(entry="Target_Apo_PlaneShift", using="Target_Banishment",
         level=7, school="Conjuration", hid=7023, classes=["clr", "dru", "sor", "wlk", "wiz"],
         name="Plane Shift",
         desc="You hurl an enemy through the planes. On a failed Charisma save it is banished for 3 turns - no concentration required.",
         design="Offensive use only (party travel has no BG3 hook): Banishment chassis, CHA save, concentration-free.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Charisma, SourceSpellDC())",
             "SpellSuccess": "ApplyStatus(BANISHED,100,3)",
             "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsHarmful",
         }),
    dict(entry="Target_Apo_PowerWordFortify", using="Target_DeathWard",
         level=7, school="Enchantment", hid=7025, classes=["brd", "clr"],
         name="Power Word Fortify",
         desc="A word of pure vitality wraps a creature in 60 temporary hit points.",
         design="2024 spell: 120 THP split among six becomes 60 THP on one target - equal power at BG3's party scale.",
         fields={
             "SpellProperties": "ApplyStatus(APO_FORTIFIED,100,-1)",
             "TooltipStatusApply": "ApplyStatus(APO_FORTIFIED,100,-1)",
         }),
    dict(entry="Target_Apo_ReverseGravity", using="Target_FlameStrike",
         level=7, school="Transmutation", hid=7027, classes=["dru", "sor", "wiz"],
         name="Reverse Gravity",
         desc="Gravity inverts across the area: creatures that fail a Dexterity save are slammed skyward and back down for 6d6 Bludgeoning damage and knocked Prone.",
         design="Vertical physics approximated by slam damage + Prone across a 9m disc.",
         fields={
             "SpellSuccess": "DealDamage(6d6,Bludgeoning,Magical);ApplyStatus(PRONE,100,1)",
             "SpellFail": "DealDamage((6d6)/2,Bludgeoning,Magical)",
             "TooltipDamageList": "DealDamage(6d6,Bludgeoning)",
             "AreaRadius": "9",
         }),
    dict(entry="Target_Apo_Sequester", using="Target_ResilientSphere",
         level=7, school="Transmutation", hid=7029, classes=["wiz"],
         name="Sequester",
         desc="You hide an ally outside the world's reach: for 3 turns nothing can touch them, and they cannot act.",
         design="Protective stasis - the sphere pointed at an ally: emergency invulnerability.",
         fields={
             "TargetConditions": "Ally() and not Dead()",
             "SpellProperties": "ApplyStatus(RESILIENT_SPHERE,100,3)",
             "TooltipStatusApply": "ApplyStatus(RESILIENT_SPHERE,100,3)",
             "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent",
         }),
    dict(entry="Target_Apo_Simulacrum", using="Target_DeathWard",
         level=7, school="Illusion", hid=7031, classes=["wiz"],
         name="Simulacrum",
         desc="A snow-built double acts through you for 5 turns, granting an additional action and bonus action each round.",
         design="The duplicate acts through its creator: Haste-class action economy without lethargy or concentration, time-boxed to 5 turns.",
         fields={
             "SpellProperties": "ApplyStatus(APO_SIMULACRUM,100,5)",
             "TooltipStatusApply": "ApplyStatus(APO_SIMULACRUM,100,5)",
         }),
    dict(entry="Target_Apo_Symbol", using="Target_FlameStrike",
         level=7, school="Abjuration", hid=7033, classes=["brd", "clr", "dru", "wiz"],
         name="Symbol",
         desc="A glyph of stunning power erupts: creatures in the area that fail an Intelligence save take 7d10 Psychic damage and are Stunned for a turn.",
         design="The 'stunning' symbol variant, cast as an instant AoE (BG3 has no readied-trigger glyphs above Glyph of Warding).",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
             "SpellSuccess": "DealDamage(7d10,Psychic,Magical);ApplyStatus(STUNNED,100,1)",
             "SpellFail": "DealDamage((7d10)/2,Psychic,Magical)",
             "TooltipDamageList": "DealDamage(7d10,Psychic)",
         }),
    dict(entry="Target_Apo_Teleport", using="Target_MistyStep",
         level=7, school="Conjuration", hid=7035, classes=["brd", "sor", "wiz"],
         name="Teleport",
         desc="You vanish and reappear anywhere you can see, up to 30m away.",
         design="Long-range battlefield blink; overworld teleportation already exists as fast travel.",
         fields={
             "TargetRadius": "30",
         }),

    # ============================= LEVEL 8 =============================
    dict(entry="Shout_Apo_AnimalShapes", using="Shout_PrayerOfHealing",
         level=8, school="Transmutation", hid=8001, classes=["dru"],
         name="Animal Shapes",
         desc="Allies around you take on bestial vigour for 10 turns: 30 temporary hit points and surging speed.",
         design="Mass ally polymorph flattened to a strong pack-buff (true form-swapping is engine-owned).",
         fields={
             "SpellProperties": "ApplyStatus(APO_BESTIAL,100,10)",
             "TooltipStatusApply": "ApplyStatus(APO_BESTIAL,100,10)",
             "TooltipDamageList": "",
         }),
    dict(entry="Shout_Apo_AntimagicField", using="Shout_SpiritGuardians",
         level=8, school="Abjuration", hid=8003, classes=["clr", "wiz"],
         name="Antimagic Field",
         desc="A 3m sphere of dead magic follows you for 10 turns: enemies inside are continually Silenced, strangling their casting.",
         design="Full spell-negation is not expressible; the field Silences every enemy inside it each turn - casters must leave or go dark.",
         fields={
             "SpellProperties": "ApplyStatus(SELF,APO_ANTIMAGIC_AURA,100,10)",
             "TooltipStatusApply": "ApplyStatus(APO_ANTIMAGIC_AURA,100,10)",
         }),
    dict(entry="Target_Apo_Antipathy", using="Target_Blindness",
         level=8, school="Enchantment", hid=8005, classes=["dru", "wiz"],
         name="Antipathy/Sympathy",
         desc="You become anathema to one creature: on a failed Wisdom save it is Frightened of you for 5 turns.",
         design="The antipathy half, single-target: a long unconditional fear with no concentration.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC())",
             "SpellSuccess": "ApplyStatus(FRIGHTENED,100,5)",
             "TooltipStatusApply": "ApplyStatus(FRIGHTENED,100,5)",
         }),
    dict(entry="Target_Apo_Befuddlement", using="Target_Feeblemind",
         level=8, school="Enchantment", hid=8007, classes=["brd", "dru", "wlk", "wiz"],
         name="Befuddlement",
         desc="You blast the mind of a creature, shattering its intellect and personality (PHB 2024 successor to Feeblemind).",
         design="2024 rename of the existing Feeblemind implementation; mechanics inherited unchanged.",
         fields={}),
    dict(entry="Target_Apo_Clone", using="Target_DeathWard",
         level=8, school="Necromancy", hid=8009, classes=["wiz"],
         name="Clone",
         desc="A hidden clone stands ready. The next time the target falls, the clone takes their place: they rise again at full strength.",
         design="Death-contingency via Script Extender rider on APO_CLONE - full revive on going down, once.",
         fields={
             "SpellProperties": "ApplyStatus(APO_CLONE,100,-1)",
             "TooltipStatusApply": "ApplyStatus(APO_CLONE,100,-1)",
         }),
    dict(entry="Shout_Apo_ControlWeather", using="Shout_SpiritGuardians",
         level=8, school="Transmutation", hid=8011, classes=["clr", "dru", "wiz"],
         name="Control Weather",
         desc="You bend the sky itself: for 5 turns a storm rages 18m around you, shocking enemies for 2d10 Lightning damage each turn (Constitution save).",
         design="Weather control focused into its combat expression: a huge personal storm-cell.",
         fields={
             "SpellProperties": "ApplyStatus(SELF,APO_STORM_AURA,100,5)",
             "TooltipStatusApply": "ApplyStatus(APO_STORM_AURA,100,5)",
         }),
    dict(entry="Target_Apo_Demiplane", using="Target_DeathWard",
         level=8, school="Conjuration", hid=8013, classes=["sor", "wlk", "wiz"],
         name="Demiplane",
         desc="You shove an ally through a shadowy door into your demiplane: for 2 turns nothing can reach them, and they cannot act.",
         design="Pocket-dimension refuge: brief total protection at the cost of the ally's turns.",
         fields={
             "SpellProperties": "ApplyStatus(RESILIENT_SPHERE,100,2)",
             "TooltipStatusApply": "ApplyStatus(RESILIENT_SPHERE,100,2)",
         }),
    dict(entry="Target_Apo_DominateMonster", using="Target_DominatePerson",
         level=8, school="Enchantment", hid=8015, classes=["brd", "sor", "wlk", "wiz"],
         name="Dominate Monster",
         desc="You seize the will of any creature - beast, fiend, dragon or worse. On a failed Wisdom save it fights for you.",
         design="Dominate Person with the humanoid restriction lifted.",
         fields={
             "TargetConditions": "Character() and not Dead() and not Self()",
         }),
    dict(entry="Target_Apo_Earthquake", using="Target_FlameStrike",
         level=8, school="Evocation", hid=8017, classes=["clr", "dru", "sor"],
         name="Earthquake",
         desc="The ground heaves across a huge area: creatures that fail a Dexterity save take 5d12 Bludgeoning damage and are knocked Prone amid the churned earth.",
         design="Fissures and collapse become slam damage + Prone + a lingering mud field.",
         fields={
             "SpellSuccess": "DealDamage(5d12,Bludgeoning,Magical);ApplyStatus(PRONE,100,1)",
             "SpellFail": "DealDamage((5d12)/2,Bludgeoning,Magical)",
             "TooltipDamageList": "DealDamage(5d12,Bludgeoning)",
             "AreaRadius": "12",
             "SpellProperties": "GROUND:CreateSurface(6,3,Mud)",
         }),
    dict(entry="Shout_Apo_HolyAura", using="Shout_SpiritGuardians",
         level=8, school="Abjuration", hid=8019, classes=["clr"],
         name="Holy Aura",
         desc="Divine radiance mantles you for 5 turns: allies within 9m are continually Blessed.",
         design="The 5e save/attack-shield rendered as a perpetual Bless aura on the party.",
         fields={
             "SpellProperties": "ApplyStatus(SELF,APO_HOLY_AURA,100,5)",
             "TooltipStatusApply": "ApplyStatus(APO_HOLY_AURA,100,5)",
         }),
    dict(entry="Target_Apo_IncendiaryCloud", using="Target_Cloudkill",
         level=8, school="Conjuration", hid=8021, classes=["sor", "wiz"],
         name="Incendiary Cloud",
         desc="A roiling cloud of embers ignites: creatures inside take 10d8 Fire damage (Dexterity save for half) and the ground burns on.",
         design="Cloudkill chassis converted to fire: heavy initial burn plus a lingering fire field.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Dexterity, SourceSpellDC())",
             "SpellSuccess": "DealDamage(10d8,Fire,Magical)",
             "SpellFail": "DealDamage((10d8)/2,Fire,Magical)",
             "TooltipDamageList": "DealDamage(10d8,Fire)",
             "SpellProperties": "GROUND:CreateSurface(6,3,Fire)",
         }),
    dict(entry="Target_Apo_Maze", using="Target_Banishment",
         level=8, school="Conjuration", hid=8023, classes=["wiz"],
         name="Maze",
         desc="You cast an enemy into an extradimensional labyrinth. On a failed Intelligence save it is gone for 2 turns, wandering the maze.",
         design="Banishment chassis keyed to Intelligence - brutal against low-INT bruisers, trivial for keen minds, exactly as written.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Intelligence, SourceSpellDC())",
             "SpellSuccess": "ApplyStatus(BANISHED,100,2)",
         }),
    dict(entry="Target_Apo_MindBlank", using="Target_DeathWard",
         level=8, school="Abjuration", hid=8025, classes=["brd", "wiz"],
         name="Mind Blank",
         desc="Until your next long rest, one creature's mind is a locked vault: immune to Psychic damage and to being Charmed.",
         design="Direct translation - psychic immunity + charm immunity until long rest.",
         fields={
             "SpellProperties": "ApplyStatus(APO_MIND_BLANK,100,-1)",
             "TooltipStatusApply": "ApplyStatus(APO_MIND_BLANK,100,-1)",
         }),
    dict(entry="Target_Apo_Sunburst", using="Target_FlameStrike",
         level=8, school="Evocation", hid=8027, classes=["clr", "dru", "sor", "wiz"],
         name="Sunburst",
         desc="Brilliant sunlight flashes in a 9m sphere: 12d6 Radiant damage, and creatures that fail a Constitution save are Blinded for 2 turns.",
         design="Direct translation on the FlameStrike chassis.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
             "SpellSuccess": "DealDamage(12d6,Radiant,Magical);ApplyStatus(BLINDED,100,2)",
             "SpellFail": "DealDamage((12d6)/2,Radiant,Magical)",
             "TooltipDamageList": "DealDamage(12d6,Radiant)",
             "AreaRadius": "9",
         }),
    dict(entry="Target_Apo_Telepathy", using="Target_DeathWard",
         level=8, school="Divination", hid=8029, classes=["wiz"],
         name="Telepathy",
         desc="You forge a telepathic bond with an ally until your next long rest, steeling their mind: advantage on Wisdom, Intelligence and Charisma saving throws.",
         design="The link's tactical value expressed as mental-save advantage on the bonded ally.",
         fields={
             "SpellProperties": "ApplyStatus(APO_TELEPATHIC_BOND,100,-1)",
             "TooltipStatusApply": "ApplyStatus(APO_TELEPATHIC_BOND,100,-1)",
         }),
    dict(entry="Zone_Apo_Tsunami", using="Zone_ConeOfCold",
         level=8, school="Evocation", hid=8031, classes=["dru"],
         name="Tsunami",
         desc="A wall of water crashes through everything before you: 6d10 Bludgeoning damage (Dexterity save for half), leaving the ground awash.",
         design="The travelling wave compressed into one crushing cone + water surface for elemental follow-ups.",
         fields={
             "SpellSuccess": "DealDamage(6d10,Bludgeoning,Magical)",
             "SpellFail": "DealDamage((6d10)/2,Bludgeoning,Magical)",
             "TooltipDamageList": "DealDamage(6d10,Bludgeoning)",
             "SpellProperties": "GROUND:CreateSurface(4,2,Water)",
         }),

    # ============================= LEVEL 9 =============================
    dict(entry="Target_Apo_AstralProjection", using="Target_DeathWard",
         level=9, school="Necromancy", hid=9001, classes=["clr", "wlk", "wiz"],
         name="Astral Projection",
         desc="Your silver-corded astral self takes the field for 10 turns: flying free, with your material body's wounds dulled to resistance against physical harm.",
         design="Projection rendered as an astral-form self buff: Fly + physical resistance while concentration holds.",
         fields={
             "SpellProperties": "ApplyStatus(FLY,100,10);ApplyStatus(APO_ASTRAL_FORM,100,10)",
             "TooltipStatusApply": "ApplyStatus(FLY,100,10);ApplyStatus(APO_ASTRAL_FORM,100,10)",
             "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsConcentration",
         }),
    dict(entry="Target_Apo_Imprisonment", using="Target_FleshToStone",
         level=9, school="Abjuration", hid=9003, classes=["wlk", "wiz"],
         name="Imprisonment",
         desc="You bind a creature outside time and space. On a failed Wisdom save it is Petrified - permanently, until someone breaks the binding.",
         design="Save-or-lose in the Power Word Kill design space: permanent petrification stands in for the eternal prison.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC())",
             "SpellSuccess": "ApplyStatus(PETRIFIED,100,-1)",
             "SpellFail": "",
             "TooltipStatusApply": "ApplyStatus(PETRIFIED,100,-1)",
         }),
    dict(entry="Target_Apo_Shapechange", using="Target_DeathWard",
         level=9, school="Transmutation", hid=9005, classes=["dru", "wiz"],
         name="Shapechange",
         desc="You assume a colossal primal form for 10 turns: 60 temporary hit points, hardened hide, and tremendous stride.",
         design="Creature-form catalogue flattened to one 'apex form' package (engine owns true model swaps).",
         fields={
             "SpellProperties": "ApplyStatus(APO_COLOSSUS,100,10)",
             "TooltipStatusApply": "ApplyStatus(APO_COLOSSUS,100,10)",
             "SpellFlags": "IsSpell;HasVerbalComponent;HasSomaticComponent;IsConcentration",
         }),
    dict(entry="Shout_Apo_StormOfVengeance", using="Shout_SpiritGuardians",
         level=9, school="Conjuration", hid=9007, classes=["dru"],
         name="Storm of Vengeance",
         desc="A churning stormcloud blankets the battlefield for 5 turns: every enemy within 18m is lashed for 4d6 Lightning damage each turn (Constitution save).",
         design="The five-round escalating storm flattened to its strongest sustained round, kept at full 18m scale.",
         fields={
             "SpellProperties": "ApplyStatus(SELF,APO_VENGEANCE_AURA,100,5)",
             "TooltipStatusApply": "ApplyStatus(APO_VENGEANCE_AURA,100,5)",
             "Icon": "Apo_Spell_StormOfVengeance",  # Icons/src (ComfyUI + BG3 icon LoRA, 2026-10-04)
         }),
    dict(entry="Target_Apo_TrueResurrection", using="Target_Resurrection",
         level=9, school="Necromancy", hid=9009, classes=["clr", "dru"],
         name="True Resurrection",
         desc="You restore a dead companion to life whole and unmarred: full hit points and a lingering blessing.",
         design="Resurrection at 100% HP plus 3-turn Bless - death undone without a scar.",
         fields={
             "SpellProperties": "Resurrect(100);ApplyStatus(BLESS,100,3)",
         }),
    dict(entry="Target_Apo_Weird", using="Target_FlameStrike",
         level=9, school="Illusion", hid=9011, classes=["wlk", "wiz"],
         name="Weird",
         desc="You drag every enemy in the area into their own worst nightmare: 12d10 Psychic damage (Wisdom save for half), and those who fail are Frightened for 2 turns.",
         design="Mass phantasmal killer as a one-shot AoE terror burst.",
         fields={
             "SpellRoll": "not SavingThrow(Ability.Wisdom, SourceSpellDC())",
             "SpellSuccess": "DealDamage(12d10,Psychic,Magical);ApplyStatus(FRIGHTENED,100,2)",
             "SpellFail": "DealDamage((12d10)/2,Psychic,Magical)",
             "TooltipDamageList": "DealDamage(12d10,Psychic)",
             "AreaRadius": "9",
         }),
]

# ---------------------------------------------------------------------------
# Support statuses.
# ---------------------------------------------------------------------------

STATUSES = [
    dict(entry="APO_FINGER_OF_DEATH", hid=1, name="Death's Finger",
         desc="Marked by Finger of Death. If this creature dies now, it rises as a zombie serving its killer.",
         fields={"StatusType": "BOOST", "Icon": "Spell_CircleOfDeath",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_ETHEREAL", hid=3, name="Ethereal Drift",
         desc="Partly in the Ethereal Plane: movement is greatly extended.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Transmutation_Blink",
                 "Boosts": "ActionResource(Movement,3,0)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_FORTIFIED", hid=5, name="Fortified",
         desc="Wrapped in 60 temporary hit points by a word of power.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Abjuration_ArcaneLock",
                 "Boosts": "TemporaryHP(60)",
                 "RemoveConditions": "not HasTemporaryHP()",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_SIMULACRUM", hid=7, name="Simulacrum",
         desc="A snow-built double acts through you: an additional action and bonus action each round.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Illusion_MirrorImage",
                 "Boosts": "ActionResource(ActionPoint,1,0);ActionResource(BonusActionPoint,1,0)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_BESTIAL", hid=9, name="Bestial Vigour",
         desc="Primal shape flows through you: 30 temporary hit points and surging speed.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Transmutation_Longstrider",
                 "Boosts": "TemporaryHP(30);ActionResource(Movement,3,0)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_CLONE", hid=11, name="Clone Standing By",
         desc="A hidden clone waits. The next time you fall, you rise again at full strength.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Necromancy_FalseLife",
                 "StatusPropertyFlags": "IgnoreResting",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_MIND_BLANK", hid=13, name="Mind Blank",
         desc="This mind is a locked vault: immune to Psychic damage and to being Charmed.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Abjuration_Counterspell",
                 "Boosts": "StatusImmunity(CHARMED);Resistance(Psychic,Immune)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_TELEPATHIC_BOND", hid=15, name="Telepathic Bond",
         desc="A steadying voice in your mind: advantage on Wisdom, Intelligence and Charisma saving throws.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Divination_DetectThoughts",
                 "Boosts": "Advantage(SavingThrow,Wisdom);Advantage(SavingThrow,Intelligence);Advantage(SavingThrow,Charisma)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_ASTRAL_FORM", hid=17, name="Astral Form",
         desc="Your material wounds are far away: resistant to Slashing, Piercing and Bludgeoning damage.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Evocation_AstralFlood",
                 "Boosts": "Resistance(Slashing,Resistant);Resistance(Piercing,Resistant);Resistance(Bludgeoning,Resistant)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    dict(entry="APO_COLOSSUS", hid=19, name="Colossal Form",
         desc="A towering primal shape: 60 temporary hit points, +2 Armour Class and tremendous stride.",
         fields={"StatusType": "BOOST", "Icon": "Spell_Transmutation_EnlargeReduce",
                 "Boosts": "TemporaryHP(60);ActionResource(Movement,6,0);AC(2)",
                 "StatusGroups": "SG_RemoveOnRespec"}),
    # --- Spirit-Guardians-engine auras (caster aura + victim strike pairs) ---
    dict(entry="APO_CELESTIAL_AURA", hid=21, name="Celestial Spirit", using="SPIRIT_GUARDIANS_RADIANT_AURA",
         desc="A celestial spirit attends you: enemies within 9m suffer radiant wrath; allies are continually Blessed.",
         fields={"AuraRadius": "9", "StackId": "APO_CELESTIAL_AURA",
                 "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_CELESTIAL_WRATH,100,1);IF(Ally() and not Self() and not Dead()):ApplyStatus(BLESS,100,1)"}),
    dict(entry="APO_CELESTIAL_WRATH", hid=23, name="Celestial Wrath", using="SPIRIT_GUARDIANS_RADIANT",
         desc="Scoured by celestial radiance.",
         fields={}),
    dict(entry="APO_STORM_AURA", hid=25, name="Stormcall", using="SPIRIT_GUARDIANS_RADIANT_AURA",
         desc="A storm-cell rages 18m around you, shocking enemies each turn.",
         fields={"AuraRadius": "18", "StackId": "APO_STORM_AURA",
                 "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_STORM_SHOCK,100,1)"}),
    dict(entry="APO_STORM_SHOCK", hid=27, name="Storm-Shocked", using="SPIRIT_GUARDIANS_RADIANT",
         desc="Lashed by summoned lightning.",
         fields={"OnApplyRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
                 "OnApplySuccess": "IF(not HasStatus('SPIRIT_GUARDIANS_DAMAGE_RECEIVED')):DealDamage(2d10,Lightning,Magical);IF(not HasStatus('SPIRIT_GUARDIANS_DAMAGE_RECEIVED')):ApplyStatus(SPIRIT_GUARDIANS_DAMAGE_RECEIVED,100,1)",
                 "DescriptionParams": "DealDamage(2d10,Lightning)",
                 "TooltipSave": "Constitution",
                 "TooltipDamage": "DealDamage(2d10,Lightning)"}),
    dict(entry="APO_VENGEANCE_AURA", hid=29, name="Storm of Vengeance", using="SPIRIT_GUARDIANS_RADIANT_AURA",
         desc="A vengeful stormcloud blankets 18m around you.",
         fields={"AuraRadius": "18", "StackId": "APO_VENGEANCE_AURA",
                 "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(APO_VENGEANCE_STRIKE,100,1)"}),
    dict(entry="APO_VENGEANCE_STRIKE", hid=31, name="Vengeance-Struck", using="SPIRIT_GUARDIANS_RADIANT",
         desc="Lashed by the storm of vengeance.",
         fields={"OnApplyRoll": "not SavingThrow(Ability.Constitution, SourceSpellDC())",
                 "OnApplySuccess": "IF(not HasStatus('SPIRIT_GUARDIANS_DAMAGE_RECEIVED')):DealDamage(4d6,Lightning,Magical);IF(not HasStatus('SPIRIT_GUARDIANS_DAMAGE_RECEIVED')):ApplyStatus(SPIRIT_GUARDIANS_DAMAGE_RECEIVED,100,1)",
                 "DescriptionParams": "DealDamage(4d6,Lightning)",
                 "TooltipSave": "Constitution",
                 "TooltipDamage": "DealDamage(4d6,Lightning)"}),
    dict(entry="APO_ANTIMAGIC_AURA", hid=33, name="Antimagic Field", using="SPIRIT_GUARDIANS_RADIANT_AURA",
         desc="A sphere of dead magic: enemies inside are continually Silenced.",
         fields={"AuraRadius": "3", "StackId": "APO_ANTIMAGIC_AURA",
                 "AuraStatuses": "IF(Enemy() and not Dead()):ApplyStatus(SILENCED,100,1)"}),
    dict(entry="APO_HOLY_AURA", hid=35, name="Holy Aura", using="SPIRIT_GUARDIANS_RADIANT_AURA",
         desc="Divine radiance mantles you: allies within 9m are continually Blessed.",
         fields={"AuraRadius": "9", "StackId": "APO_HOLY_AURA",
                 "AuraStatuses": "IF(Ally() and not Dead()):ApplyStatus(BLESS,100,1)"}),
]

# ---------------------------------------------------------------------------
# Spell-list registration.
# ---------------------------------------------------------------------------

L = {
    ("wiz", 7): ["00170001-0001-0001-0001-000000000001", "00170001-aaaa-0001-0001-000000000001"],
    ("wiz", 8): ["00180001-0001-0001-0001-000000000001", "00180001-aaaa-0001-0001-000000000001"],
    ("wiz", 9): ["00190001-0001-0001-0001-000000000001", "00190001-aaaa-0001-0001-000000000001"],
    # sorcerer lists are cumulative (7 / 7+8 / 7+8+9)
    ("sor", 7): ["00170001-0001-0001-0001-000000000002", "00180001-0001-0001-0001-000000000002", "00190001-0001-0001-0001-000000000002"],
    ("sor", 8): ["00180001-0001-0001-0001-000000000002", "00190001-0001-0001-0001-000000000002"],
    ("sor", 9): ["00190001-0001-0001-0001-000000000002"],
    ("clr", 7): ["00170001-0001-0001-0001-000000000003"],
    ("clr", 8): ["00180001-0001-0001-0001-000000000003"],
    ("clr", 9): ["00190001-0001-0001-0001-000000000003"],
    ("dru", 7): ["00170001-0001-0001-0001-000000000004"],
    ("dru", 8): ["00180001-0001-0001-0001-000000000004"],
    ("dru", 9): ["00190001-0001-0001-0001-000000000004"],
    # bard lists are cumulative (6+7 / 6+7+8 / 6+7+8+9)
    ("brd", 7): ["00170001-0001-0001-0001-000000000005", "00180001-0001-0001-0001-000000000005", "00190001-0001-0001-0001-000000000005"],
    ("brd", 8): ["00180001-0001-0001-0001-000000000005", "00190001-0001-0001-0001-000000000005"],
    ("brd", 9): ["00190001-0001-0001-0001-000000000005"],
    ("wlk", 7): ["00170001-0001-0001-0001-000000000007"],
    ("wlk", 8): ["00180001-0001-0001-0001-000000000007"],
    ("wlk", 9): ["00190001-0001-0001-0001-000000000007"],
    # bard Magical Secrets: every spell of the level
    ("all", 7): ["00170001-0001-0001-0001-000000000006"],
    ("all", 8): ["00180001-0001-0001-0001-000000000006"],
    ("all", 9): ["00190001-0001-0001-0001-000000000006"],
}


def emit_spells() -> str:
    out = [
        "// AUTO-GENERATED by Scripts/generate_level79_spells.py - DO NOT EDIT BY HAND.",
        "// PHB 2024 level 7-9 spells missing from BG3 + dnd55e. Designs: docs/SPELLS-7-9.md",
        "",
    ]
    for s in SPELLS:
        sptype = s["entry"].split("_", 1)[0]
        out.append(f'new entry "{s["entry"]}"')
        out.append('type "SpellData"')
        out.append(f'data "SpellType" "{ {"Projectile": "Projectile", "Shout": "Shout", "Target": "Target", "Zone": "Zone"}[sptype] }"')
        out.append(f'using "{s["using"]}"')
        out.append(f'data "Level" "{s["level"]}"')
        out.append(f'data "SpellSchool" "{s["school"]}"')
        out.append(f'data "DisplayName" "{handle("hsp", s["hid"])};1"')
        out.append(f'data "Description" "{handle("hsp", s["hid"] + 1)};1"')
        if "UseCosts" not in s["fields"]:   # a spell can set its own (Divine Word is a Bonus Action)
            out.append(f'data "UseCosts" "{slot_cost(s["level"])}"')
        for k, v in s["fields"].items():
            out.append(f'data "{k}" "{v}"')
        out.append("")
    return "\n".join(out) + "\n"


def emit_statuses() -> str:
    out = [
        "// AUTO-GENERATED by Scripts/generate_level79_spells.py - DO NOT EDIT BY HAND.",
        "// Support statuses for the level 7-9 spell layer.",
        "",
    ]
    for s in STATUSES:
        out.append(f'new entry "{s["entry"]}"')
        out.append('type "StatusData"')
        if s.get("using"):
            out.append(f'using "{s["using"]}"')
        out.append(f'data "DisplayName" "{handle("hst", s["hid"])};1"')
        out.append(f'data "Description" "{handle("hst", s["hid"] + 1)};1"')
        for k, v in s["fields"].items():
            out.append(f'data "{k}" "{v}"')
        out.append("")
    return "\n".join(out) + "\n"


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def update_loca() -> int:
    """Our hsp*/hst* strings, updated in place (stable order: gen_common.update_loca); stale ones are dropped."""
    import re
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gen_common import update_loca as write_rows
    rows = {}
    for s in SPELLS:
        rows[handle("hsp", s["hid"])], rows[handle("hsp", s["hid"] + 1)] = s["name"], s["desc"]
    for s in STATUSES:
        rows[handle("hst", s["hid"])], rows[handle("hst", s["hid"] + 1)] = s["name"], s["desc"]
    text = LOCA.read_text(encoding="utf-8")
    stale = re.compile(r'  <content contentuid="(hs[pt]\d+)" version="\d+">[^<]*</content>\n')
    text = stale.sub(lambda m: m.group(0) if m.group(1) in rows else "", text)
    LOCA.write_bytes(text.encode("utf-8"))
    write_rows(rows)
    return len(rows)


def update_spell_lists() -> int:
    text = SPELL_LISTS.read_text(encoding="utf-8")
    additions: dict[str, list[str]] = {}
    for s in SPELLS:
        targets = set()
        for c in s["classes"]:
            for uuid in L.get((c, s["level"]), []):
                targets.add(uuid)
        for uuid in L[("all", s["level"])]:
            targets.add(uuid)
        for uuid in targets:
            additions.setdefault(uuid, []).append(s["entry"])

    changed = 0
    for uuid, spells in additions.items():
        node_re = re.compile(
            r'(<node id="SpellList">(?:(?!</node>).)*?id="Spells"[^/]*?value=")([^"]*)("(?:(?!</node>).)*?id="UUID"[^/]*?value="'
            + re.escape(uuid) + r'")',
            re.S,
        )

        def repl(m: re.Match) -> str:
            existing = [x for x in m.group(2).split(";") if x]
            merged = existing + [sp for sp in spells if sp not in existing]
            return m.group(1) + ";".join(merged) + m.group(3)

        new_text, n = node_re.subn(repl, text)
        if n == 0:
            # attribute order may be UUID before Spells; try the other order
            node_re2 = re.compile(
                r'(id="UUID"[^/]*?value="' + re.escape(uuid)
                + r'"(?:(?!</node>).)*?id="Spells"[^/]*?value=")([^"]*)(")',
                re.S,
            )
            new_text, n = node_re2.subn(repl, text)
        if n == 0:
            print(f"WARNING: spell list {uuid} not found; skipped {len(spells)} spells")
            continue
        text = new_text
        changed += 1
    SPELL_LISTS.write_text(text, encoding="utf-8")
    return changed


def emit_doc() -> str:
    out = [
        "# Level 7-9 Spells — Design Matrix",
        "",
        "Generated by `Scripts/generate_level79_spells.py` (the design source of",
        "truth — edit the tables there and re-run; this file is overwritten).",
        "",
        "Spells already implemented before this layer: Regenerate, Resurrection,",
        "Project Image, Power Word Stun, Glibness, Feeblemind, Foresight,",
        "True Polymorph, Wish, Meteor Swarm, Gate, Time Stop, Mass Heal,",
        "Prismatic Wall, Power Word Kill, Power Word Heal.",
        "",
        "Out of scope: Blade of Disaster (not in the PHB 2024 core list).",
        "",
        "Script Extender riders (BootstrapServer.lua): Finger of Death raises a",
        "zombie from humanoids it kills; Clone fully revives its bearer once.",
        "",
    ]
    for lvl in (7, 8, 9):
        out.append(f"## Level {lvl}")
        out.append("")
        out.append("| Spell | Classes | Design call |")
        out.append("| --- | --- | --- |")
        for s in SPELLS:
            if s["level"] == lvl:
                out.append(f"| **{s['name']}** (`{s['entry']}`) | {', '.join(s['classes'])} | {s['design']} |")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    OUT_SPELLS.write_text(emit_spells(), encoding="utf-8")
    OUT_STATUSES.write_text(emit_statuses(), encoding="utf-8")
    n_loca = update_loca()
    n_lists = update_spell_lists()
    DOC.write_text(emit_doc(), encoding="utf-8")
    print(f"Spells: {len(SPELLS)}  Statuses: {len(STATUSES)}  Loca entries: {n_loca}  Lists updated: {n_lists}")
    print(f"Wrote {OUT_SPELLS}, {OUT_STATUSES}, {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
