-- Optional Mod Configuration Menu settings, shared by the server and client contexts (2026-10-08, docs/XP_CURVE.md).
-- Without MCM every Get returns nil and the callers keep their defaults. MCM injects the global `MCM` into mods that load
-- AFTER it; for mods loaded before it only the copies on Mods.BG3MCM exist, so fall back to those.
local S = {}

function S.Get(id)
    if type(MCM) == "table" and type(MCM.Get) == "function" then return MCM.Get(id) end
    local api = Mods and Mods.BG3MCM
    if api and type(api.Get) == "function" then return api.Get({ settingId = id, modUUID = ModuleUUID }) end
end

-- cb(settingId, value) when the player saves one of this mod's settings in MCM.
function S.Watch(cb)
    local ok, ev = pcall(function() return Ext.ModEvents.BG3MCM["MCM_Setting_Saved"] end)
    if not (ok and ev) then return end
    ev:Subscribe(function(p)
        if p and p.modUUID == ModuleUUID and p.settingId then cb(p.settingId, p.value) end
    end)
end

-- "debug_logging": verbose [dbg] traces in the Script Extender log (both contexts).
Ext.Events.SessionLoaded:Subscribe(function()
    local v = S.Get("debug_logging")
    if v ~= nil then Apotheosis.DEBUG = v and true or false end
end)
S.Watch(function(id, value)
    if id == "debug_logging" then Apotheosis.DEBUG = value and true or false end
end)

Apotheosis.MCMSettings = S
return S
