-- Portal Jumper (Arcana Unleashed origin feat): the MCM switch "portal_jumper" (Scripts/gen_portal_jumper.py has the feat).
--
-- The three OriginFeat_PortalJumper_* passives sit in our PassiveList PortalJumperOrigin, which is MergedInto dnd55e's
-- "Human Origin Feat" list (the variant-human pick at character creation). With the setting off we take them out of that
-- list at runtime, so the character-creation / level-up screens no longer offer the feat; nothing already granted is
-- removed. No MCM = always offered. Runs in both contexts (the lists are read by the client UI and by the server).
local Log = Apotheosis.Log
local HUMAN_LIST = "51988e80-d7cc-4351-aa7d-83b8ba3f989a"        -- dnd55e "Human Origin Feat"
local OWN_LIST = "e74c0a6b-aeb0-56e6-b4fe-f0b75bafaeb8"          -- PortalJumperOrigin (MergedInto HUMAN_LIST)
local NO_GUID = "00000000-0000-0000-0000-000000000000"
local NAMES = { "OriginFeat_PortalJumper_Necrotic", "OriginFeat_PortalJumper_Psychic", "OriginFeat_PortalJumper_Radiant" }

local Settings = Ext.Require("MCMSettings.lua")
local enabled = true

local function isOurs(p)
    for _, n in ipairs(NAMES) do if p == n then return true end end
    return false
end

local function listOf(id)
    local ok, l = pcall(Ext.StaticData.Get, id, "PassiveList")
    return ok and l or nil
end

local function apply()
    local human, own = listOf(HUMAN_LIST), listOf(OWN_LIST)
    if not human then Log.Warn("Portal Jumper: dnd55e's Human origin-feat list not found"); return end
    local keep = {}
    for _, p in ipairs(human.Passives) do
        if not isOurs(p) then keep[#keep + 1] = p end
    end
    if enabled then
        for _, n in ipairs(NAMES) do keep[#keep + 1] = n end
    end
    local ok, err = pcall(function() human.Passives = keep end)
    if own then pcall(function() own.MergedInto = enabled and HUMAN_LIST or NO_GUID end) end
    if ok then
        Log.Info(string.format("Portal Jumper %s in the Human origin-feat list (%d entries)", enabled and "offered" or "hidden", #keep))
    else
        Log.Error("Portal Jumper: could not edit the origin-feat list: " .. tostring(err))
    end
end

Ext.Events.SessionLoaded:Subscribe(function()
    local v = Settings.Get("portal_jumper")
    if v ~= nil then enabled = v and true or false end
    apply()
end)

Settings.Watch(function(id, value)
    if id == "portal_jumper" then enabled = value and true or false; apply() end
end)

-- console/test hook: Mods.dnd55e_Apotheosis.PortalJumper.State()
PortalJumper = {
    State = function()
        local human = listOf(HUMAN_LIST)
        local present = {}
        if human then for _, p in ipairs(human.Passives) do if isOurs(p) then present[#present + 1] = p end end end
        return { enabled = enabled, offered = present, total = human and #human.Passives or 0 }
    end,
}
