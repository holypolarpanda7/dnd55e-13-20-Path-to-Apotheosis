-- Overchannel (Wizard Evoker 14, PHB 2024): when you cast a Wizard spell of levels 1-5 that deals damage you can deal
-- its maximum damage. The first use after a Long Rest is free; each later use before the next Long Rest costs you
-- 2d12 Necrotic per spell level, +1d12 per level for every further use. Stats side: Evoker_14_Overchannel
-- unlocks Interrupt_Apo_Overchannel, a Yes/No prompt on each qualifying cast (no reaction spent); Yes applies APO_OVERCHANNEL
-- (MinimumRollResult maximizes the dice). This module does the self-damage and the per-rest use count for casts made under
-- APO_OVERCHANNEL, then removes it so it covers that one spell: a moment after the cast (a hotbar Magic Missile's last dart can
-- land after CastedSpell: 26 instead of 30 in game) and at the latest when the caster starts another spell (UsingSpell comes
-- before that spell's prompt). Replaced the 1.0.5.0 hotbar toggle (#59), 2026-10-29.
-- The damage is charged per level of the SPELL SLOT used (PHB 2024): CastedSpell names no slot, so the caster's spell slots are
-- read on UsingSpell and compared on CastedSpell (no slot spent, e.g. a scripted cast: the spell's own level). It "can't be
-- reduced": Osi.ApplyDamage goes through resistance, so a caster resistant to Necrotic is charged double (immunity still
-- blocks it). #57 item 5, 2026-10-28.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local OC = {}
OC.PASSIVE = "Evoker_14_Overchannel"
OC.STATUS = "APO_OVERCHANNEL"
OC.LINGER_MS = 3000   -- how long APO_OVERCHANNEL outlives the cast, for projectiles still in flight

OC.TestDie = nil   -- tests: every die of the next drawback rolls this value (set by a test case's setup `lua` step)

local function roll(n, sides)
    local total = 0
    for _ = 1, n do total = total + (OC.TestDie or (Ext.Random and Ext.Random(1, sides) or math.random(1, sides))) end
    return total
end

local function slots(caster)
    local out = {}
    pcall(function()
        for u, entries in pairs(Ext.Entity.Get(caster).ActionResources.Resources) do
            local def = Ext.StaticData.Get(u, "ActionResource")
            if def and (def.Name == "SpellSlot" or def.Name == "WarlockSpellSlot") then
                for _, x in ipairs(entries) do out[x.Level] = (out[x.Level] or 0) + x.Amount end
            end
        end
    end)
    return out
end

local before = {}   -- caster -> spell slots when the cast started

local function id(c) return string.sub(tostring(c), -36) end   -- Osiris passes Name_uuid, scripts often the bare uuid

local function resistsNecrotic(caster)
    local ok, flags = pcall(function()
        return tostring(Ext.Entity.Get(caster).Resistances.Resistances[Ext.Enums.DamageType.Necrotic.Value + 1])
    end)
    return ok and flags and flags:find("Resistant") ~= nil
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

-- Yes on the Overchannel prompt for this cast
local function chosen(caster)
    return Osi.HasActiveStatus(caster, OC.STATUS) == 1
end

local generation = {}   -- caster -> spells started; a delayed removal only acts if no new spell started since

function OC.OnUsing(caster)
    if Osi.HasPassive(caster, OC.PASSIVE) ~= 1 then return end
    generation[id(caster)] = (generation[id(caster)] or 0) + 1
    if chosen(caster) then Osi.RemoveStatus(caster, OC.STATUS) end   -- left over from the previous spell
    before[id(caster)] = slots(caster)
end

function OC.SetUses(caster, n)   -- tests: uses since the last Long Rest
    uses()[id(caster)] = n
end

function OC.OnCast(caster, spell)
    local was = before[id(caster)]
    before[id(caster)] = nil
    if not chosen(caster) then return end
    local gen = generation[id(caster)]
    Ext.Timer.WaitFor(OC.LINGER_MS, function()   -- one spell only
        if generation[id(caster)] == gen and chosen(caster) then Osi.RemoveStatus(caster, OC.STATUS) end
    end)
    local level = qualifies(spell)
    if not level then return end
    if was then   -- the slot actually spent: the highest level whose count went down
        local now, spent = slots(caster), nil
        for lvl, n in pairs(was) do if (now[lvl] or 0) < n and (not spent or lvl > spent) then spent = lvl end end
        if spent and spent >= 1 then level = spent end
    end
    if level > 5 then return end   -- Overchannel only works with a 1st- to 5th-level slot
    local key = id(caster)
    local prior = uses()[key] or 0
    uses()[key] = prior + 1
    if prior == 0 then
        Log.Info("Overchannel: free use for " .. key .. " (" .. spell .. ")")
        return
    end
    local dice = (prior + 1) * level
    local amount = roll(dice, 12)
    OC.TestDie = nil   -- one cast only
    local resisted = resistsNecrotic(caster)
    Log.Info("Overchannel: use " .. (prior + 1) .. " for " .. key .. " (" .. spell .. ", slot level " .. level .. "): " .. dice
        .. "d12 = " .. amount .. " Necrotic" .. (resisted and " (doubled against the caster's resistance)" or ""))
    Osi.ApplyDamage(caster, resisted and amount * 2 or amount, "Necrotic", caster)
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

Ext.Osiris.RegisterListener("UsingSpell", 5, "before", guard("UsingSpell", function(caster) OC.OnUsing(caster) end))
Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(caster, spell) OC.OnCast(caster, spell) end))
Ext.Osiris.RegisterListener("LongRestFinished", 0, "after", guard("LongRestFinished", OC.OnLongRest))

Apotheosis = Apotheosis or {}
Apotheosis.Overchannel = OC
return OC
