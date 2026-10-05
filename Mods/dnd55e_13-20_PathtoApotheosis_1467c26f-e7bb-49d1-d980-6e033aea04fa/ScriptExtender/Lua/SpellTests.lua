-- =====================================================================
-- Apotheosis level 7-9 spell functional tests.
--
-- The 40 spells in Spell_Epic79.txt are force-cast and their PRIMARY
-- observable is verified (a status landing, HP dropping, a dead target).
-- Each spell is assigned to exactly ONE subclass whose parent class can
-- actually learn it (validated against SpellLists.lsx), so the coverage
-- is divided across the same subclass sessions the feature tests use.
--
-- This reuses FeatureTests.lua's helpers (host/ally/spawn/poll/cast) via
-- _G.ApotheosisFeatureTests, so both suites share one target doctrine.
--
-- Console entry points (registered in BootstrapServer.lua):
--   !apospelllist                 -- list every spell test grouped by subclass
--   !apospells <Subclass>         -- run all spell tests for one subclass
--   !apospell  <SpellStatId>      -- run one spell test by stat id
--
-- Outcome log markers (parsed like the feature tests):
--   SpellTest <Spell>: PASS
--   SpellTest <Spell>: FAILED <reason>
--   SpellTest <Spell>: SKIP (manual) <instructions>
--   SubclassSpells <Subclass>: ALL CHECKS PASSED | FAILED
-- =====================================================================

local ST = { bySubclass = {}, byId = {} }

local function log()
    if Apotheosis and Apotheosis.Log then return Apotheosis.Log end
    local TAG = "[Apotheosis]"
    return {
        Info = function(...) Ext.Utils.Print(TAG, ...) end,
        Warn = function(...) Ext.Utils.PrintWarning(TAG, ...) end,
        Error = function(...) Ext.Utils.PrintError(TAG, ...) end,
        Debug = function(...) end,
    }
end

local function FT()
    return _G.ApotheosisFeatureTests
end

-- Current HP of a character, or nil if unreadable.
local function currentHp(guid)
    local ok, ent = pcall(Ext.Entity.Get, guid)
    if ok and ent and ent.Health and ent.Health.Hp then
        return ent.Health.Hp
    end
    return nil
end

-- ---------------------------------------------------------------------
-- Spell -> subclass assignment (design source of truth).
--
-- verify field:
--   { self   = {status...} }  cast at host,  expect any status on host
--   { ally   = {status...} }  cast at ally,  expect any status on the ally
--   { enemy  = {status...} }  cast at a hostile wolf, expect any status
--                             on it (a lethal spell that kills it instead
--                             also passes)
--   { damage = true }         cast at a hostile wolf, expect its HP to
--                             drop or the wolf to die
--   { manual = "instructions" }  visual-only (summon / teleport / revive)
--
-- level is the class level at which the slot (and thus the spell) unlocks:
--   7th -> 13, 8th -> 15, 9th -> 17.
-- ---------------------------------------------------------------------
local ASSIGN = {
    -- ---- Level 7 (unlocks at class level 13) ------------------------
    { sub = "EvocationSchool",     cls = "Wizard",   spell = "Projectile_Apo_DelayedBlastFireball", name = "Delayed Blast Fireball", lvl = 13, verify = { damage = true } },
    { sub = "LightDomain",         cls = "Cleric",   spell = "Shout_Apo_DivineWord",                name = "Divine Word",            lvl = 13, verify = { enemy = { "STUNNED", "BLINDED" } } },
    { sub = "NecromancySchool",    cls = "Wizard",   spell = "Target_Apo_FingerOfDeath",            name = "Finger of Death",        lvl = 13, verify = { enemy = { "APO_FINGER_OF_DEATH" } }, extra = "On kill, the humanoid rises as a zombie on your side (Script Extender rider) - confirm visually with a humanoid target." },
    { sub = "DraconicBloodline",   cls = "Sorcerer", spell = "Target_Apo_FireStorm",                name = "Fire Storm",             lvl = 13, verify = { damage = true } },
    { sub = "WildMagic",           cls = "Sorcerer", spell = "Zone_PrismaticSpray_Fire",             name = "Prismatic Spray",        lvl = 13, verify = { damage = true } },
    { sub = "Fiend",               cls = "Warlock",  spell = "Target_Apo_Forcecage",                name = "Forcecage",              lvl = 13, verify = { enemy = { "RESILIENT_SPHERE" } } },
    { sub = "SwordsCollege",       cls = "Bard",     spell = "Target_Apo_MordenkainensSword",       name = "Mordenkainen's Sword",   lvl = 13, verify = { manual = "cast at a hostile wolf; a spiritual greatsword should be summoned and attack. Verify the summon appears on the turn order." } },
    { sub = "LifeDomain",          cls = "Cleric",   spell = "Shout_Apo_ConjureCelestial",          name = "Conjure Celestial",      lvl = 13, verify = { self = { "APO_CELESTIAL_AURA" } } },
    { sub = "BladesingingSchool",  cls = "Wizard",   spell = "Target_Apo_Etherealness",             name = "Etherealness",           lvl = 13, verify = { self = { "APO_ETHEREAL" } } },
    { sub = "GlamourCollege",      cls = "Bard",     spell = "Target_Apo_MirageArcane",             name = "Mirage Arcane",          lvl = 13, verify = { enemy = { "SLOW", "BLINDED" } } },
    { sub = "LoreCollege",         cls = "Bard",     spell = "Shout_Apo_MagnificentMansion",        name = "Magnificent Mansion",    lvl = 13, verify = { self = { "SANCTUARY" } } },
    { sub = "GreatOldOne",         cls = "Warlock",  spell = "Target_Apo_PlaneShift",               name = "Plane Shift",            lvl = 13, verify = { enemy = { "BANISHED" } } },
    { sub = "ValorCollege",        cls = "Bard",     spell = "Target_Apo_PowerWordFortify",         name = "Power Word Fortify",     lvl = 13, verify = { self = { "APO_FORTIFIED" } } },
    { sub = "AberrantSorcery",     cls = "Sorcerer", spell = "Target_Apo_ReverseGravity",           name = "Reverse Gravity",        lvl = 13, verify = { enemy = { "PRONE" } } },
    { sub = "TransmutationSchool", cls = "Wizard",   spell = "Target_Apo_Sequester",                name = "Sequester",              lvl = 13, verify = { ally = { "RESILIENT_SPHERE" } } },
    { sub = "ConjurationSchool",   cls = "Wizard",   spell = "Target_Apo_Simulacrum",               name = "Simulacrum",             lvl = 13, verify = { self = { "APO_SIMULACRUM" } } },
    { sub = "KnowledgeDomain",     cls = "Cleric",   spell = "Target_Apo_Symbol",                   name = "Symbol",                 lvl = 13, verify = { enemy = { "STUNNED" } } },
    { sub = "ClockworkSorcery",    cls = "Sorcerer", spell = "Target_Apo_Teleport",                 name = "Teleport",               lvl = 13, verify = { manual = "cast at a distant point of ground; the caster should blink to it (Misty Step, 30m range)." } },

    -- ---- Level 8 (unlocks at class level 15) ------------------------
    { sub = "CircleOfTheMoon",     cls = "Druid",    spell = "Shout_Apo_AnimalShapes",              name = "Animal Shapes",          lvl = 15, verify = { self = { "APO_BESTIAL" } } },
    { sub = "AbjurationSchool",    cls = "Wizard",   spell = "Shout_Apo_AntimagicField",            name = "Antimagic Field",        lvl = 15, verify = { self = { "APO_ANTIMAGIC_AURA" } } },
    { sub = "CircleOfTheLand",     cls = "Druid",    spell = "Target_Apo_Antipathy",                name = "Antipathy/Sympathy",     lvl = 15, verify = { enemy = { "FRIGHTENED" } } },
    { sub = "EnchantmentSchool",   cls = "Wizard",   spell = "Target_Apo_Befuddlement",             name = "Befuddlement",           lvl = 15, verify = { enemy = { "FEEBLEMIND" } } },
    { sub = "NecromancySchool",    cls = "Wizard",   spell = "Target_Apo_Clone",                    name = "Clone",                  lvl = 15, verify = { self = { "APO_CLONE" } }, extra = "When downed while APO_CLONE is active you are fully revived once (Script Extender rider) - stage separately with a lethal hit to confirm the revive." },
    { sub = "CircleOfTheSea",      cls = "Druid",    spell = "Shout_Apo_ControlWeather",            name = "Control Weather",        lvl = 15, verify = { self = { "APO_STORM_AURA" } } },
    { sub = "Archfey",             cls = "Warlock",  spell = "Target_Apo_Demiplane",                name = "Demiplane",              lvl = 15, verify = { self = { "RESILIENT_SPHERE" } } },
    { sub = "GreatOldOne",         cls = "Warlock",  spell = "Target_DominateMonster",          name = "Dominate Monster",       lvl = 15, verify = { enemy = { "DOMINATE_PERSON" } } },
    { sub = "CircleOfTheLand",     cls = "Druid",    spell = "Target_Apo_Earthquake",               name = "Earthquake",             lvl = 15, verify = { enemy = { "PRONE" } } },
    { sub = "WarDomain",           cls = "Cleric",   spell = "Shout_Apo_HolyAura",                  name = "Holy Aura",              lvl = 15, verify = { self = { "APO_HOLY_AURA" } } },
    { sub = "SpellfireSorcery",    cls = "Sorcerer", spell = "Target_Apo_IncendiaryCloud",          name = "Incendiary Cloud",       lvl = 15, verify = { damage = true } },
    { sub = "ConjurationSchool",   cls = "Wizard",   spell = "Target_Apo_Maze",                     name = "Maze",                   lvl = 15, verify = { enemy = { "BANISHED" } } },
    { sub = "AbjurationSchool",    cls = "Wizard",   spell = "Target_Apo_MindBlank",                name = "Mind Blank",             lvl = 15, verify = { self = { "APO_MIND_BLANK" } } },
    { sub = "CircleOfStars",       cls = "Druid",    spell = "Target_Apo_Sunburst",                 name = "Sunburst",               lvl = 15, verify = { enemy = { "BLINDED" } } },
    { sub = "DivinationSchool",    cls = "Wizard",   spell = "Target_Apo_Telepathy",                name = "Telepathy",              lvl = 15, verify = { ally = { "APO_TELEPATHIC_BOND" } } },
    { sub = "CircleOfTheSea",      cls = "Druid",    spell = "Zone_Apo_Tsunami",                    name = "Tsunami",                lvl = 15, verify = { damage = true } },

    -- ---- Level 9 (unlocks at class level 17) ------------------------
    { sub = "Celestial",           cls = "Warlock",  spell = "Target_Apo_AstralProjection",         name = "Astral Projection",      lvl = 17, verify = { self = { "APO_ASTRAL_FORM" } } },
    { sub = "Fiend",               cls = "Warlock",  spell = "Target_Apo_Imprisonment",             name = "Imprisonment",           lvl = 17, verify = { enemy = { "PETRIFIED" } } },
    { sub = "CircleOfTheMoon",     cls = "Druid",    spell = "Target_Apo_Shapechange",              name = "Shapechange",            lvl = 17, verify = { self = { "APO_COLOSSUS" } } },
    { sub = "CircleOfTheSea",      cls = "Druid",    spell = "Shout_Apo_StormOfVengeance",          name = "Storm of Vengeance",     lvl = 17, verify = { self = { "APO_VENGEANCE_AURA" } } },
    { sub = "GraveDomain",         cls = "Cleric",   spell = "Target_Apo_TrueResurrection",         name = "True Resurrection",      lvl = 17, verify = { manual = "target a DEAD ally; it should return to life at full HP with a short Bless. Stage with !apospawn wolf friendly, kill it, then cast." } },
    { sub = "IllusionSchool",      cls = "Wizard",   spell = "Target_Apo_Weird",                    name = "Weird",                  lvl = 17, verify = { enemy = { "FRIGHTENED" } } },
}

for _, e in ipairs(ASSIGN) do
    ST.byId[e.spell] = e
    local list = ST.bySubclass[e.sub]
    if not list then list = {}; ST.bySubclass[e.sub] = list end
    list[#list + 1] = e
end

-- ---------------------------------------------------------------------
-- Runner for a single spell-test entry. cb(passOk|nil).
-- ---------------------------------------------------------------------
function ST.RunEntry(e, cb)
    local L = log()
    local ft = FT()
    cb = cb or function() end
    if not ft then
        L.Error("SpellTest " .. e.name .. ": FAILED FeatureTests module not loaded")
        cb(false); return
    end

    local v = e.verify
    if v.manual then
        L.Warn("SpellTest " .. e.name .. ": SKIP (manual) " .. tostring(v.manual))
        cb(nil); return
    end

    local ok, err = pcall(function()
        local host = ft.GetHost()
        local ctx = { spawned = {} }

        local function finish(passOk, reason)
            for _, guid in ipairs(ctx.spawned) do ft.RemoveSpawned(guid) end
            if passOk then
                L.Info("SpellTest " .. e.name .. ": PASS")
            else
                L.Error("SpellTest " .. e.name .. ": FAILED " .. tostring(reason or "unknown"))
            end
            if e.extra and passOk then
                L.Info("    note: " .. e.extra)
            end
            cb(passOk)
        end

        -- self-buff: cast at host, poll host.
        if v.self then
            ft.UseSpellOn(host, e.spell, host, function()
                ft.ExpectAnyStatus(host, v.self, ft.Config.AuraTimeoutMs, function(found, which)
                    finish(found, found and nil
                        or ("host never gained any of {" .. table.concat(v.self, ", ") .. "}"))
                end)
            end)
            return
        end

        -- ally-buff: real party ally, else a spawned friendly wolf.
        if v.ally then
            local ally = ft.GetAlly(host)
            local function castAtAlly(target)
                ft.UseSpellOn(host, e.spell, target, function()
                    ft.ExpectAnyStatus(target, v.ally, ft.Config.AuraTimeoutMs, function(found)
                        finish(found, found and nil
                            or ("ally never gained any of {" .. table.concat(v.ally, ", ") .. "}"))
                    end)
                end)
            end
            if ally then
                castAtAlly(ally)
            else
                ft.SpawnCreature(host, "wolf", "friendly", 2, 2, function(guid, why)
                    if not guid then finish(false, "no ally and friendly spawn failed: " .. tostring(why)); return end
                    ctx.spawned[#ctx.spawned + 1] = guid
                    castAtAlly(guid)
                end)
            end
            return
        end

        -- enemy status / damage: spawn a hostile wolf.
        ft.SpawnCreature(host, "wolf", "hostile", 3, 2, function(guid, why)
            if not guid then finish(false, "hostile spawn failed: " .. tostring(why)); return end
            ctx.spawned[#ctx.spawned + 1] = guid

            if v.damage then
                local before = currentHp(guid)
                ft.UseSpellOn(host, e.spell, guid, function()
                    local after = currentHp(guid)
                    local dead = Osi.IsDead(guid) == 1
                    if dead then
                        finish(true); return
                    end
                    if before and after then
                        finish(after < before, after < before and nil
                            or ("target HP did not drop (" .. tostring(before) .. " -> " .. tostring(after) .. ")"))
                    else
                        finish(false, "could not read target HP to confirm damage")
                    end
                end)
                return
            end

            -- enemy status (a lethal resolution that kills the target also passes)
            ft.UseSpellOn(host, e.spell, guid, function()
                ft.ExpectAnyStatus(guid, v.enemy, ft.Config.AuraTimeoutMs, function(found)
                    if found then finish(true); return end
                    if Osi.IsDead(guid) == 1 then finish(true); return end
                    finish(false, "target never gained any of {" .. table.concat(v.enemy, ", ")
                        .. "} (a save may have succeeded - re-run)")
                end)
            end)
        end)
    end)

    if not ok then
        L.Error("SpellTest " .. e.name .. ": FAILED runtime error: " .. tostring(err))
        cb(false)
    end
end

-- ---------------------------------------------------------------------
-- Run every spell test for a subclass, sequentially, then a summary line.
-- ---------------------------------------------------------------------
function ST.RunForSubclass(subclass)
    local L = log()
    local list = ST.bySubclass[subclass]
    if not list then
        L.Warn("SubclassSpells " .. tostring(subclass) .. ": no spell tests assigned (run !apospelllist)")
        return
    end
    L.Info("SubclassSpells " .. subclass .. ": running " .. tostring(#list) .. " spell test(s)")
    local i, allPass = 0, true
    local function nextTest()
        i = i + 1
        if i > #list then
            L.Info("SubclassSpells " .. subclass .. ": " .. (allPass and "ALL CHECKS PASSED" or "FAILED"))
            return
        end
        ST.RunEntry(list[i], function(passOk)
            if passOk == false then allPass = false end
            nextTest()
        end)
    end
    nextTest()
end

function ST.RunOne(spellId)
    local e = ST.byId[spellId]
    if not e then
        log().Error("SpellTest: unknown spell id '" .. tostring(spellId) .. "' (run !apospelllist)")
        return
    end
    ST.RunEntry(e, function() end)
end

function ST.List()
    local L = log()
    local subs = {}
    for s in pairs(ST.bySubclass) do subs[#subs + 1] = s end
    table.sort(subs)
    L.Info("Level 7-9 spell tests (" .. tostring(#ASSIGN) .. " spells across " .. tostring(#subs) .. " subclasses):")
    for _, s in ipairs(subs) do
        local list = ST.bySubclass[s]
        L.Info("  " .. s .. " (" .. list[1].cls .. "):")
        for _, e in ipairs(list) do
            local kind = e.verify.self and "self-buff" or e.verify.ally and "ally-buff"
                or e.verify.enemy and "enemy-status" or e.verify.damage and "damage"
                or e.verify.manual and "MANUAL" or "?"
            L.Info(string.format("      L%d  %-24s %s [%s]", e.lvl, e.name, e.spell, kind))
        end
    end
end

_G.ApotheosisSpellTests = ST
return ST
