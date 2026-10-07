-- Epic Boon feats: the PHB 2024 prerequisite "Level 19+" (client half of Scripts/gen_epic_boons.py).
--
-- Feats.lsx Requirements only parses FeatRequirementProficiency / FeatRequirementAbilityGreaterEqual and drops anything
-- else, so CharacterLevelGreaterThan(18) in the data does nothing (verified in game 2026-10-06). The parsed list,
-- Feat.FeatRequirements, is writable and the level-up screen reads it when it opens. This keeps every EpicBoon_ feat locked
-- behind an unmeetable ability check unless the controlled character is level 18 or higher - i.e. taking level 19 or 20,
-- from any class (a multiclass character's feat pick at 19+ included, as the rules allow).
-- The server doesn't re-check feat requirements, so this client lock is the whole gate, and each player's client gates
-- only their own level-ups. The screen shows the lock as "Strength needs to be higher than 99"; each boon's description
-- starts "Prerequisite: Level 19+".
local Log = Apotheosis.Log
local LOCK = { { Requirement = "ApotheosisEpicBoonLevel19", Type = 0, Ability = "Strength", AbilityValue = 99 } }
local MIN_LEVEL = 18          -- the level a character has while it takes level 19
local POLL_MS = 250

local boons = nil             -- the EpicBoon_ feat resources
local locked = nil            -- current state (nil = not applied yet)
local lastPoll = 0

local function collect()
    boons = {}
    for _, id in pairs(Ext.StaticData.GetAll("Feat")) do
        local f = Ext.StaticData.Get(id, "Feat")
        if f and string.sub(tostring(f.Name), 1, 9) == "EpicBoon_" then boons[#boons + 1] = f end
    end
    Log.Info(string.format("Epic Boon lock: %d boon feats", #boons))
end

local function controlledLevel()
    local ok, lvl = pcall(function()
        local e = Ext.Entity.GetAllEntitiesWithComponent("ClientControl")[1]
        return e and e.EocLevel and e.EocLevel.Level
    end)
    return ok and lvl or nil
end

local function apply(lock)
    if lock == locked then return end
    for _, f in ipairs(boons) do
        f.FeatRequirements = lock and LOCK or {}
    end
    locked = lock
    Log.Debug("Epic Boon feats " .. (lock and "locked" or "unlocked"))
end

local function update()
    if not boons then return end
    local lvl = controlledLevel()
    if lvl == nil then return end            -- no controlled character yet (menus, loading)
    apply(lvl < MIN_LEVEL)
end

Ext.Events.SessionLoaded:Subscribe(function()
    collect()
    update()
end)

Ext.Events.Tick:Subscribe(function()
    local now = Ext.Timer.MonotonicTime()
    if now - lastPoll < POLL_MS then return end
    lastPoll = now
    update()
end)

-- console/test hook: Mods.dnd55e_Apotheosis.EpicBoonFeatLock.State()
EpicBoonFeatLock = {
    State = function() return { boons = boons and #boons or 0, locked = locked, level = controlledLevel() } end,
}
