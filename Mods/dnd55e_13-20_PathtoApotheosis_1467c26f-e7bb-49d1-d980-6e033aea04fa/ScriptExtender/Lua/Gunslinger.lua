-- Gunslinger 13-20 (issue #6): the scripted parts of Scripts/gen_gunslinger.py's features.
--  * Standing statuses passives can't apply when gained at level-up (OnCreate doesn't run then):
--    Cheat Death (only on reaching Gunslinger 13, so a level-up never refills a spent use) and the
--    Gold Star Hero aura.
--  * Iron-Clad Law: Lay Down the Law's ally also resists B/P/S until the start of the White Hat's next turn.
--  * Double or Nothing: while toggled on, a ranged Critical Hit rolls a d20 - 10+ doubles the hit's damage
--    (dice rolled four times instead of twice), 9 or lower halves it (a normal hit).
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local GS = {}
local GUNSLINGER = "b6cd23fa-ec1a-44a6-86c5-693201654dba"

local function has(c, p) return Osi.HasPassive(c, p) == 1 end

local function classLevel(c, classUuid)
    local ok, lvl = pcall(function()
        for _, cl in pairs(Ext.Entity.Get(c).Classes.Classes) do
            if tostring(cl.ClassUUID) == classUuid then return cl.Level end
        end
        return 0
    end)
    return ok and lvl or 0
end

function GS.OnLeveledUp(c)
    if has(c, "Gunslinger_13_CheatDeath") and classLevel(c, GUNSLINGER) == 13
        and Osi.HasActiveStatus(c, "GUNSLINGER_CHEAT_DEATH") ~= 1 then
        Osi.ApplyStatus(c, "GUNSLINGER_CHEAT_DEATH", -1, 1, c)
    end
    if has(c, "WhiteHat_14_GoldStarHero") and Osi.HasActiveStatus(c, "WHITEHAT_GOLD_STAR_AURA") ~= 1 then
        Osi.ApplyStatus(c, "WHITEHAT_GOLD_STAR_AURA", -1, 1, c)
    end
end

-- ---------------------------------------------------------------- Iron-Clad Law
local ironclad = {}  -- White Hat guid -> { ally guid, ... }

function GS.OnStatusApplied(target, status, causee)
    if status ~= "LAY_DOWN_THE_LAW" or not causee then return end
    local wh = string.sub(causee, -36)
    if not has(wh, "WhiteHat_14_GoldStarHero") then return end
    Osi.ApplyStatus(target, "WHITEHAT_IRONCLAD_LAW", -1, 1, wh)
    ironclad[wh] = ironclad[wh] or {}
    table.insert(ironclad[wh], target)
    Log.Info("Iron-Clad Law: " .. tostring(target) .. " resists B/P/S until " .. wh .. "'s next turn")
end

function GS.OnTurnStarted(c)
    local wh = string.sub(c, -36)
    for _, ally in ipairs(ironclad[wh] or {}) do Osi.RemoveStatus(ally, "WHITEHAT_IRONCLAD_LAW") end
    ironclad[wh] = nil
end

-- ---------------------------------------------------------------- Double or Nothing
local function hasFlag(flags, name)  -- tostring(flags) = "DamageFlags(Projectile,Hit,Critical)"
    for f in tostring(flags):gmatch("[%w_]+") do if f == name then return true end end
    return false
end

-- BeforeDealDamage (verified 2026-10-02): e.Attack holds the hit's DamageList/TotalDamageDone, e.Hit the flags.
local function scaleList(list, mult)
    local total = 0
    for _, d in pairs(list or {}) do
        d.Amount = math.max(0, math.floor(d.Amount * mult + 0.5))
        total = total + d.Amount
    end
    return total
end

function GS.BeforeDealDamage(e)
    local hit = e.Hit
    local attacker = hit and hit.Inflicter
    if not attacker or not attacker.Uuid then return end
    local guid = attacker.Uuid.EntityUuid
    if Osi.HasActiveStatus(guid, "HIGHROLLER_DOUBLE_OR_NOTHING") ~= 1 then return end
    local kind = tostring(hit.SpellAttackType)
    if not hasFlag(hit.EffectFlags, "Critical") or not kind:find("^Ranged.*WeaponAttack$") then return end
    local d20 = Ext.Math.Random(1, 20)
    local mult = d20 >= 10 and 2 or 0.5  -- crit dice x2 -> x4, or back to x1 (a normal hit)
    local before = e.Attack.TotalDamageDone
    local total = scaleList(e.Attack.DamageList, mult)
    e.Attack.TotalDamageDone = total
    pcall(function() scaleList(hit.DamageList, mult) hit.TotalDamageDone = total end)
    Log.Info(string.format("Double or Nothing: %s rolled %d - %s (%d -> %d damage)", guid, d20,
        d20 >= 10 and "damage dice x4" or "a normal hit", before, total))
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("Gunslinger " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("LeveledUp", 1, "after", guard("LeveledUp", function(c) GS.OnLeveledUp(c) end))
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(t, s, c) GS.OnStatusApplied(t, s, c) end))
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c) GS.OnTurnStarted(c) end))
-- White Hat 14 Stunned Surrender: the stun ends early if the creature takes any damage (the status's own RemoveEvents carry the
-- end-of-turn Wisdom save, and a status has only one RemoveConditions).
-- The Critical Hit that causes the stun lands its damage after the status (seen in game 2026-11-11): damage within a second
-- of the stun is that hit, not a new one.
local surrenderAt = {}
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(t, s)
    if s == "WHITEHAT_STUNNED_SURRENDER" then surrenderAt[string.sub(t, -36)] = Ext.Utils.MonotonicTime() end
end))
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, _, _, _, amount)
    if (amount or 0) <= 0 or Osi.HasActiveStatus(defender, "WHITEHAT_STUNNED_SURRENDER") ~= 1 then return end
    local at = surrenderAt[string.sub(defender, -36)]
    if at and Ext.Utils.MonotonicTime() - at < 1000 then return end
    Osi.RemoveStatus(defender, "WHITEHAT_STUNNED_SURRENDER")
end))
Ext.Events.BeforeDealDamage:Subscribe(guard("BeforeDealDamage", GS.BeforeDealDamage))

_G.ApotheosisGunslinger = GS
return GS
