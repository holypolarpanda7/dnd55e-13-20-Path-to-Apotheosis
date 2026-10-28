-- Overchannel (Wizard Evoker 14, PHB 2024): when you cast a Wizard spell of levels 1-5 that deals damage you can deal
-- its maximum damage. The first use after a Long Rest is free; each later use before the next Long Rest costs you
-- 2d12 Necrotic per spell level, +1d12 per level for every further use. Stats side: Evoker_14_Overchannel
-- (MinimumRollResult maximizes the dice; a hotbar toggle since #59). This module does the self-damage and the per-rest use
-- count, only while the toggle is on.
-- Limits: CastedSpell gives no slot level, so the spell's base level is used (an upcast spell still maximizes via
-- the passive, but is charged at its base level); the damage goes through Osi.ApplyDamage, so resistance applies.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local OC = {}
OC.PASSIVE = "Evoker_14_Overchannel"

local function roll(n, sides)
    local total = 0
    for _ = 1, n do total = total + (Ext.Random and Ext.Random(1, sides) or math.random(1, sides)) end
    return total
end

local function uses()
    PersistentVars = PersistentVars or {}
    PersistentVars.OverchannelUses = PersistentVars.OverchannelUses or {}
    return PersistentVars.OverchannelUses
end

local function qualifies(spell)
    local ok, stat = pcall(Ext.Stats.Get, spell)
    if not ok or not stat then return nil end
    local level = tonumber(stat.Level) or 0
    if level < 1 or level > 5 then return nil end
    local dmg = stat.TooltipDamageList
    if dmg == nil or dmg == "" then return nil end
    return level
end

-- the passive is a hotbar toggle (#59): true only while it is switched on
local function toggledOn(caster)
    local on = false
    pcall(function()
        for _, p in ipairs(Ext.Entity.Get(caster).PassiveContainer.Passives) do
            if p.Passive.PassiveId == OC.PASSIVE then on = p.Passive.ToggledOn == true end
        end
    end)
    return on
end

function OC.OnCast(caster, spell)
    if Osi.HasPassive(caster, OC.PASSIVE) ~= 1 or not toggledOn(caster) then return end
    local level = qualifies(spell)
    if not level then return end
    local key = tostring(caster)
    local prior = uses()[key] or 0
    uses()[key] = prior + 1
    if prior == 0 then
        Log.Info("Overchannel: free use for " .. key .. " (" .. spell .. ")")
        return
    end
    local dice = (prior + 1) * level
    local amount = roll(dice, 12)
    Log.Info("Overchannel: use " .. (prior + 1) .. " for " .. key .. " (" .. spell .. "): " .. dice .. "d12 = " .. amount .. " Necrotic")
    Osi.ApplyDamage(caster, amount, "Necrotic", caster)
end

function OC.OnLongRest()
    PersistentVars = PersistentVars or {}
    PersistentVars.OverchannelUses = {}
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("Overchannel " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(caster, spell) OC.OnCast(caster, spell) end))
Ext.Osiris.RegisterListener("LongRestFinished", 0, "after", guard("LongRestFinished", OC.OnLongRest))

Apotheosis = Apotheosis or {}
Apotheosis.Overchannel = OC
return OC
