-- Epic Boon feats: the PHB 2024 prerequisite "Level 19+" (client half of Scripts/gen_epic_boons.py).
--
-- Feats.lsx Requirements only parses FeatRequirementProficiency / FeatRequirementAbilityGreaterEqual and drops anything
-- else, so CharacterLevelGreaterThan(18) in the data does nothing (verified in game 2026-10-06). The parsed list,
-- Feat.FeatRequirements, is writable and the level-up screen reads it when it opens. This keeps every EpicBoon_ feat locked
-- behind an unmeetable ability check unless the controlled character is level 18 or higher - i.e. taking level 19 or 20,
-- from any class (a multiclass character's feat pick at 19+ included, as the rules allow). Which character: gatedLevel().
-- The server doesn't re-check feat requirements, so this client lock is the whole gate, and each player's client gates
-- only their own level-ups. The screen shows the lock as "Strength needs to be higher than 99"; each boon's description
-- starts "Prerequisite: Level 19+".
local Log = Apotheosis.Log
local LOCK = { { Requirement = "ApotheosisEpicBoonLevel19", Type = 0, Ability = "Strength", AbilityValue = 99 } }
local MIN_LEVEL = 18          -- the level a character has while it takes level 19
local POLL_MS = 250

local Settings = Ext.Require("MCMSettings.lua")
local enforce = true         -- MCM "epic_boon_level_gate" (default on; off = boons selectable at any level)
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

-- The character whose level-up this gates (#54, 2026-10-28: a player saw the lock at 19 levelling Tav and Shadowheart; the
-- first ClientControl entity is only a guess when several characters are controlled). In order: the character shown by an open
-- level-up screen or character sheet (their view model's SelectedCharacter, matched to a party member by its name handle), then a
-- controlled character with a level-up waiting (AvailableLevel above its level), then the first controlled character.
local function uiRoot(name)
    local function find(n, d)
        if d > 30 or not n then return nil end
        local ok, nm = pcall(function() return n.Name end)
        if ok and nm == name then return n end
        local okc, cnt = pcall(function() return n.VisualChildrenCount end)
        if okc and cnt then for i = 1, cnt do local r = find(n:VisualChild(i), d + 1); if r then return r end end end
    end
    local ok, root = pcall(Ext.UI.GetRoot)
    return ok and find(root, 0) or nil
end

local function shownCharacterName()
    for _, w in ipairs({ "CharacterLevelUp", "CharacterPanel" }) do
        local el = uiRoot(w)
        local ok, nm = pcall(function() return tostring(el.DataContext.CurrentPlayer.SelectedCharacter.Name) end)
        if el and ok and nm and nm ~= "" and nm ~= "nil" then return nm, w end
    end
end

local function levelOf(e) return e and e.EocLevel and e.EocLevel.Level end

local function pending(e)
    local ok, p = pcall(function() return e.AvailableLevel and e.AvailableLevel.Level > e.EocLevel.Level end)
    return ok and p
end

local function gatedLevel()
    local okc, controlled = pcall(Ext.Entity.GetAllEntitiesWithComponent, "ClientControl")
    controlled = okc and controlled or {}
    local okp, party = pcall(Ext.Entity.GetAllEntitiesWithComponent, "PartyMember")
    party = okp and party or {}
    local waiting = false
    for _, e in ipairs(party) do if pending(e) then waiting = true break end end
    if waiting then                      -- only then is a level-up screen possible: walk the UI (not free) for its character
        local nm, from = shownCharacterName()
        for _, e in ipairs(nm and party or {}) do
            local okh, h = pcall(function() return e.DisplayName.Name.Handle.Handle end)
            if okh and h == nm and levelOf(e) then return levelOf(e), from end
        end
        for _, e in ipairs(controlled) do
            if pending(e) and levelOf(e) then return levelOf(e), "controlled, level-up waiting" end
        end
    end
    return levelOf(controlled[1]), "controlled"
end

local function apply(lock, lvl, from)
    if lock == locked then return end
    for _, f in ipairs(boons) do
        f.FeatRequirements = lock and LOCK or {}
    end
    locked = lock
    -- Info, not Debug: a player's Script Extender log then shows why the boons were locked (#54)
    Log.Info(string.format("Epic Boon feats %s (level %s from %s, gate %s)", lock and "locked" or "unlocked", tostring(lvl),
        tostring(from), enforce and "on" or "off"))
end

local function update()
    if not boons then return end
    local lvl, from = gatedLevel()
    if lvl == nil then return end            -- no controlled character yet (menus, loading)
    apply(enforce and lvl < MIN_LEVEL, lvl, from)
end

Ext.Events.SessionLoaded:Subscribe(function()
    local v = Settings.Get("epic_boon_level_gate")
    if v ~= nil then enforce = v and true or false end
    collect()
    update()
end)

Settings.Watch(function(id, value)
    if id == "epic_boon_level_gate" then enforce = value and true or false; update() end
end)

Ext.Events.Tick:Subscribe(function()
    local now = Ext.Timer.MonotonicTime()
    if now - lastPoll < POLL_MS then return end
    lastPoll = now
    update()
end)

-- console/test hook: Mods.dnd55e_Apotheosis.EpicBoonFeatLock.State()
EpicBoonFeatLock = {
    State = function() local l, f = gatedLevel(); return { boons = boons and #boons or 0, locked = locked, level = l, from = f } end,
}
