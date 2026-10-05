-- Prismatic Spray (PHB 2024), with Stats/Generated/Data/Spell_Zone.txt. 2026-10-05.
--  * The spell's Dexterity save marks each creature APO_PRISMATIC_STRUCK (failed) or APO_PRISMATIC_GRAZED (saved); here
--    it gets its d8 (an 8 = two rays, rerolling 8s) and the ray(s), dealt by the caster: 1-5 = 12d6 of the ray's type
--    (half on a save; Evasion: half on a failed save, none on a success), 6 indigo and 7 violet on a failed save only.
--  * Indigo (APO_PRISMATIC_INDIGO): a Constitution save at the end of each of its turns until three successes (ends)
--    or three failures (Petrified until Greater Restoration). The count lives on the creature (survives save/load).
--  * Violet (APO_PRISMATIC_VIOLET): Blinded until the caster's next turn starts, then a Wisdom save; a failure sends
--    it to another plane (APO_PRISMATIC_BANISHED, for good).
-- Follow-up saves use the DC of the creature's Dexterity save against this cast (so DC items and boosts count).
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local PS = {}
local NULL = "NULL_00000000-0000-0000-0000-000000000000"
local INDIGO, INDIGO_TICK = "APO_PRISMATIC_INDIGO", "APO_PRISMATIC_INDIGO_TICK"
local VIOLET, VIOLET_PENDING = "APO_PRISMATIC_VIOLET", "APO_PRISMATIC_VIOLET_PENDING"
local ABILITY = { Strength = 2, Dexterity = 3, Constitution = 4, Intelligence = 5, Wisdom = 6, Charisma = 7 }

Ext.Vars.RegisterUserVariable("ApoPrismIndigo", { Server = true, Persistent = true })  -- on the creature: {s, f, dc}
Ext.Vars.RegisterUserVariable("ApoPrismViolet", { Server = true, Persistent = true })  -- on the caster: {target = dc}

local function short(g) return g and string.sub(g, -36) or nil end

local function dcGuid(value)  -- a DifficultyClass with this DC (the game ships Legacy_<n> ones)
    local best
    for _, g in ipairs(Ext.StaticData.GetAll("DifficultyClass")) do
        local d = Ext.StaticData.Get(g, "DifficultyClass")
        if d and d.Difficulties and d.Difficulties[1] == value then
            if tostring(d.Name):find("Legacy_", 1, true) == 1 then return g end
            best = best or g
        end
    end
    return best
end

-- ---------------------------------------------------------------- the d8s
local function d8() return Ext.Math.Random(1, 8) end

function PS.Roll()  -- one creature's rays: {n} or, on an 8, two rolls rerolling 8s
    local r = d8()
    if r < 8 then return { r } end
    local a, b
    repeat a = d8() until a < 8
    repeat b = d8() until b < 8
    return { a, b }
end

local DAMAGE = { "FIRE", "ACID", "LIGHTNING", "POISON", "COLD" }

local function evades(g)  -- Evasion and the like: an AreaDamageEvade() boost
    local ok, res = pcall(function()
        for _, b in pairs(Ext.Entity.Get(g).BoostsContainer.Boosts) do
            if tostring(b.Type) == "AreaDamageEvade" and #b.Boosts > 0 then return true end
        end
        return false
    end)
    return ok and res
end

function PS.Struck(target, caster, failed)
    local rays = {}  -- tests pin the rays with APO_PRISM_FORCE_<n> (two of them = two rays)
    for n = 1, 7 do
        if Osi.HasActiveStatus(target, "APO_PRISM_FORCE_" .. n) == 1 then rays[#rays + 1] = n end
    end
    if #rays == 0 then rays = PS.Roll() end
    local evade = evades(target)
    for _, r in ipairs(rays) do
        if r <= 5 then
            local half = not failed or evade
            if failed or not evade then
                Osi.ApplyStatus(target, "APO_PRISMATIC_" .. DAMAGE[r] .. (half and "_HALF" or ""), 0, 1, caster)
            end
        elseif failed then
            Osi.ApplyStatus(target, r == 6 and INDIGO or VIOLET, -1, 1, caster)
        end
    end
    Log.Info(string.format("Prismatic Spray: %s %s its save, ray %s%s", target, failed and "failed" or "made",
        table.concat(rays, "+"), evade and " (Evasion)" or ""))
end

-- ---------------------------------------------------------------- spell DC: from the Dexterity save against the cast
local lastDex = {}  -- guid -> {dc, time}

function PS.OnSave(c)
    if tostring(c.Ability) ~= "Dexterity" then return end
    local dc = c.ConditionRoll and c.ConditionRoll.Difficulty
    if not dc or dc <= 0 then return end
    local function g(h) local ok, v = pcall(function() return h.Uuid.EntityUuid end) return ok and v or nil end
    local now = Ext.Utils.MonotonicTime()
    for _, x in ipairs({ g(c.Source), g(c.Target) }) do lastDex[x] = { dc = dc, t = now } end
end

local function spellDC(caster)  -- fallback: 8 + proficiency + the casting ability of the caster's Prismatic Spray
    local e = Ext.Entity.Get(caster)
    local ability = "Intelligence"
    for _, s in pairs(e.SpellBook and e.SpellBook.Spells or {}) do
        if s.Id.OriginatorPrototype == "Zone_PrismaticSpray" then ability = tostring(s.SpellCastingAbility) break end
    end
    return 8 + e.Stats.ProficiencyBonus + e.Stats.AbilityModifiers[ABILITY[ability] or 5]
end

local function dcFor(target, caster)
    local r = lastDex[target]
    if r and Ext.Utils.MonotonicTime() - r.t < 15000 then return r.dc end
    local ok, dc = pcall(spellDC, caster)
    return ok and dc or 15
end

local function save(c, ability, dc, event)
    local g = dcGuid(math.max(1, math.min(30, dc)))
    if not g then Log.Warn("Prismatic Spray: no DifficultyClass " .. dc) return end
    Osi.RequestPassiveRoll(c, NULL, "SavingThrow", ability, g, 0, event)
end

-- ---------------------------------------------------------------- indigo
function PS.IndigoApplied(target, caster)
    Ext.Entity.Get(target).Vars.ApoPrismIndigo = { s = 0, f = 0, dc = dcFor(target, caster) }
    Osi.ApplyStatus(target, INDIGO_TICK, 6, 1, caster)
end

function PS.IndigoTurnEnded(target)  -- APO_PRISMATIC_INDIGO_TICK ran out: the end of the creature's turn
    local st = Ext.Entity.Get(target).Vars.ApoPrismIndigo
    if not st or Osi.HasActiveStatus(target, INDIGO) ~= 1 or Osi.IsDead(target) == 1 then return end
    save(target, "Constitution", st.dc, "APO_PRISM_INDIGO_" .. target)
end

function PS.IndigoResult(target, success)
    local e = Ext.Entity.Get(target)
    local st = e.Vars.ApoPrismIndigo
    if not st then return end
    if success then st.s = st.s + 1 else st.f = st.f + 1 end
    Log.Info(string.format("Prismatic Spray indigo: %s Constitution save %s (%d successes, %d failures)", target,
        success and "succeeded" or "failed", st.s, st.f))
    if st.s >= 3 or st.f >= 3 then
        e.Vars.ApoPrismIndigo = nil
        Osi.RemoveStatus(target, INDIGO)
        if st.f >= 3 then Osi.ApplyStatus(target, "PETRIFIED", -1, 1, NULL) end
    else
        e.Vars.ApoPrismIndigo = st
        Osi.ApplyStatus(target, INDIGO_TICK, 6, 1, NULL)
    end
end

-- ---------------------------------------------------------------- violet
function PS.VioletApplied(target, caster)
    local e = Ext.Entity.Get(caster)
    local pending = e.Vars.ApoPrismViolet or {}
    pending[target] = dcFor(target, caster)
    e.Vars.ApoPrismViolet = pending
    Osi.ApplyStatus(caster, VIOLET_PENDING, 6, 1, caster)
end

function PS.CasterTurnStarted(caster)  -- APO_PRISMATIC_VIOLET_PENDING ran out: the start of the caster's next turn
    local e = Ext.Entity.Get(caster)
    local pending = e.Vars.ApoPrismViolet
    if not pending then return end
    e.Vars.ApoPrismViolet = nil
    for target, dc in pairs(pending) do
        if Osi.HasActiveStatus(target, VIOLET) == 1 and Osi.IsDead(target) ~= 1 then
            save(target, "Wisdom", dc, "APO_PRISM_VIOLET_" .. target)
        end
    end
end

function PS.VioletResult(target, success)
    Osi.RemoveStatus(target, VIOLET)
    Log.Info(string.format("Prismatic Spray violet: %s Wisdom save %s", target, success and "succeeded" or "failed - sent to another plane"))
    if not success then Osi.ApplyStatus(target, "APO_PRISMATIC_BANISHED", -1, 1, NULL) end
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("PrismaticSpray " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(target, status, causee)
    if status == "APO_PRISMATIC_STRUCK" or status == "APO_PRISMATIC_GRAZED" then
        PS.Struck(short(target), short(causee), status == "APO_PRISMATIC_STRUCK")
    elseif status == INDIGO then
        PS.IndigoApplied(short(target), short(causee))
    elseif status == VIOLET then
        PS.VioletApplied(short(target), short(causee))
    end
end))

Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("StatusRemoved", function(target, status)
    if status == INDIGO_TICK then
        PS.IndigoTurnEnded(short(target))
    elseif status == VIOLET_PENDING then
        PS.CasterTurnStarted(short(target))
    elseif status == INDIGO then  -- ended some other way (three successes, Freedom of Movement, death...)
        local e = Ext.Entity.Get(target)
        if e and e.Vars.ApoPrismIndigo then e.Vars.ApoPrismIndigo = nil end
        Osi.RemoveStatus(target, INDIGO_TICK)
    end
end))

Ext.Osiris.RegisterListener("RollResult", 6, "after", guard("RollResult", function(ev, _, _, result)
    if type(ev) ~= "string" then return end
    if ev:sub(1, 17) == "APO_PRISM_INDIGO_" then
        PS.IndigoResult(ev:sub(18), result == 1)
    elseif ev:sub(1, 17) == "APO_PRISM_VIOLET_" then
        PS.VioletResult(ev:sub(18), result == 1)
    end
end))

Ext.Entity.OnCreateDeferred("SavingThrowRolledEvent", function(_, _, c)
    local ok, err = pcall(PS.OnSave, c)
    if not ok then Log.Error("PrismaticSpray SavingThrowRolledEvent: " .. tostring(err)) end
end)

return PS
