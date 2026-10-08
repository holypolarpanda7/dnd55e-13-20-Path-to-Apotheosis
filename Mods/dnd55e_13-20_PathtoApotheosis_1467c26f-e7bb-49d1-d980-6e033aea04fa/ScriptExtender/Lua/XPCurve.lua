-- XP curve multiplier (2026-10-08). Optional: with Mod Configuration Menu (MCM) installed, the player can scale the XP
-- they earn (setting "xp_multiplier", MCM_blueprint.json). Without MCM, or at 1.0, nothing here runs and the curve in
-- XPData.txt (1.0 = level 20 by the end of the game) is untouched.
-- XPData isn't readable or writable from the Script Extender, so the scaling is applied to each XP GAIN of a party member:
--   * above 1: the extra XP is added with Osi.AddExplorationExperience (the engine does the level maths);
--   * below 1: the surplus is taken back the same way (negative add keeps the engine's counters in step), but the engine
--     has by then already flagged any level the full gain crossed (AvailableLevel + CanLevelUp) and never re-checks, so
--     the earned level is rebuilt from the scaled total: AvailableLevel, CurrentLevelExperience, CanLevelUp.
-- Only gains are scaled; losses (respec, console) pass through. Verified in game 2026-10-08, see docs/XP_CURVE.md.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local XC = {}

local Settings = Ext.Require("MCMSettings.lua")
local SETTING = "xp_multiplier"
local SCOPE_SETTING = "xp_scope"      -- "all" | "early" (levels 1-12) | "late" (levels 13-20): by the level the gain starts at
local scope = "all"
local SCOPES = { ["All levels"] = "all", ["Levels 1-12 only"] = "early", ["Levels 13-20 only"] = "late" }
local MIN_MULT, MAX_MULT = 0.25, 2.0
local START = Ext.Require("XPTable.lua")   -- total XP at which level L starts (needs the mod context: load time, not inside events)

local mult = 1.0
local sub                       -- Ext.Entity subscription while the multiplier is not 1
local baseline = {}             -- entity uuid -> the total XP we expect it to have (our own corrections included)

local function levelForTotal(total)
    local lvl = 1
    for l = 2, 20 do
        if total >= START[l] then lvl = l else break end
    end
    return lvl
end

local function uuidOf(entity)
    return entity.Uuid and entity.Uuid.EntityUuid
end

-- Rebuild the earned level after a negative correction (runs a tick later, once the engine has applied it).
local function reconcile(uuid)
    local entity = Ext.Entity.Get(uuid)
    if not (entity and entity.Experience and entity.AvailableLevel) then return end
    local total = entity.Experience.TotalExperience
    local earned = levelForTotal(total)
    local current = entity.EocLevel and entity.EocLevel.Level or 1
    local avail = entity.AvailableLevel.Level
    if earned < current then earned = current end      -- never below the level the character already has
    if avail > earned then
        entity.AvailableLevel.Level = earned
        entity:Replicate("AvailableLevel")
        Log.Info(("XPCurve: %s earned level %d (engine had flagged %d)"):format(uuid, earned, avail))
    end
    entity.Experience.CurrentLevelExperience = total - START[earned]
    entity:Replicate("Experience")
    if earned <= current and entity.CanLevelUp then
        entity:RemoveComponent("CanLevelUp")
    elseif earned > current and not entity.CanLevelUp then
        entity:CreateComponent("CanLevelUp")
    end
    baseline[uuid] = total
end

local function afterTicks(n, fn)
    local id
    id = Ext.Events.Tick:Subscribe(function()
        n = n - 1
        if n <= 0 then Ext.Events.Tick:Unsubscribe(id); fn() end
    end)
end

local function onExperience(entity)
    local uuid = uuidOf(entity)
    if not uuid or not entity.PartyMember then return end
    local total = entity.Experience.TotalExperience
    local base = baseline[uuid]
    if base == nil or total == base then baseline[uuid] = total return end
    local gain = total - base
    if gain <= 0 then baseline[uuid] = total return end
    local startLevel = levelForTotal(base)
    if (scope == "early" and startLevel > 12) or (scope == "late" and startLevel < 13) then
        baseline[uuid] = total
        return
    end
    local want = math.floor(gain * mult + 0.5)
    local diff = want - gain
    baseline[uuid] = base + want          -- what the total will be once the correction lands
    if diff == 0 then return end
    Osi.AddExplorationExperience(uuid, diff)
    if diff < 0 then afterTicks(3, function() reconcile(uuid) end) end
end

local function stop()
    if sub then Ext.Entity.Unsubscribe(sub); sub = nil end
    baseline = {}
end

local function start()
    if sub then return end
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("PartyMember")) do
        if e.Experience and uuidOf(e) then baseline[uuidOf(e)] = e.Experience.TotalExperience end
    end
    sub = Ext.Entity.Subscribe("Experience", onExperience)
    Log.Info(("XPCurve: XP gains scaled x%.2f"):format(mult))
end

local function apply(value)
    value = tonumber(value) or 1.0
    mult = math.max(MIN_MULT, math.min(MAX_MULT, value))
    if math.abs(mult - 1.0) < 1e-6 then
        if sub then Log.Info("XPCurve: back to the standard curve (x1.00)") end
        stop()
    else
        stop(); start()
    end
end

function XC.Init()
    local v = Settings.Get(SETTING)
    if v == nil then return end   -- no MCM (or no value yet): standard curve
    scope = SCOPES[Settings.Get(SCOPE_SETTING)] or scope
    apply(v)
    Settings.Watch(function(id, value)
        if id == SETTING then apply(value)
        elseif id == SCOPE_SETTING then scope = SCOPES[value] or "all" end
    end)
    -- a character joining later starts with a fresh baseline
    Ext.Osiris.RegisterListener("CharacterJoinedParty", 1, "after", function(uuid)
        local e = Ext.Entity.Get(uuid)
        if sub and e and e.Experience then baseline[uuid] = e.Experience.TotalExperience end
    end)
end

XC.Apply = apply
Apotheosis.XPCurve = XC
Ext.Events.SessionLoaded:Subscribe(XC.Init)   -- MCM has its settings loaded by then
return XC
