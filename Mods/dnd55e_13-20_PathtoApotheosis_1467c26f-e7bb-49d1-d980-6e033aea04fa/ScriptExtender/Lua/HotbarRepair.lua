-- Hotbar repair: toggled passives a character has but no hotbar shows. A passive with IsToggled;ToggledDefaultAddToHotbar
-- gets its Passives-bar button only when it is GRANTED; a passive a character receives when an existing save loads (a mod
-- update adds it to a level already taken - the game applies the new progression entries on load) never gets one. Seen
-- 2026-10-29: a Berserker L20 made with 1.0.4.0 had all 9 Brutal Strike toggles of 1.0.5.0 (incl. dnd55e 4.14's own
-- Forceful/Hamstring Blow) and none on the bar, so Brutal Strike had no effect to choose; Overchannel's 1.0.5.0 toggle was
-- stuck ON the same way (#59). On LevelGameplayStarted (and when someone joins the party) each such passive is put on the
-- character's Passives bar (HotbarContainer DefaultBarContainer, bar Index 3), once per character and passive
-- (PersistentVars), so a button the player removes on purpose stays removed. Any mod's toggles, not only ours.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print }
local HR = {}
HR.PASSIVES_BAR = 3          -- keyboard layout's Passives-tab bar, used when no bar holds a passive yet (verified 2026-10-29)

local toggled = nil          -- passive name -> true, for every PassiveData with IsToggled + ToggledDefaultAddToHotbar

local function hasFlag(props, flag)
    if type(props) == "string" then return props:find(flag, 1, true) ~= nil end
    if type(props) == "table" then
        for _, v in pairs(props) do if v == flag then return true end end
    end
    return false
end

local function toggledPassives()
    if toggled then return toggled end
    toggled = {}
    for _, name in ipairs(Ext.Stats.GetStats("PassiveData")) do
        local ok, stat = pcall(Ext.Stats.Get, name)
        if ok and stat and hasFlag(stat.Properties, "IsToggled") and hasFlag(stat.Properties, "ToggledDefaultAddToHotbar") then
            toggled[name] = true
        end
    end
    return toggled
end

local function repaired(uuid)
    PersistentVars = PersistentVars or {}
    PersistentVars.HotbarRepaired = PersistentVars.HotbarRepaired or {}
    PersistentVars.HotbarRepaired[uuid] = PersistentVars.HotbarRepaired[uuid] or {}
    return PersistentVars.HotbarRepaired[uuid]
end

-- put the character's missing toggles on its Passives bar; returns the names added
function HR.Repair(entity)
    local added = {}
    local ok, err = pcall(function()
        local hc = entity.HotbarContainer
        local uuid = entity.Uuid and entity.Uuid.EntityUuid
        if not hc or not uuid or not entity.PassiveContainer then return end
        local bars = hc.Containers and hc.Containers.DefaultBarContainer
        if not bars then return end
        local done, want = repaired(uuid), toggledPassives()
        local changed = false
        local mine = {}
        for _, p in ipairs(entity.PassiveContainer.Passives) do
            local okp, name = pcall(function() return p.Passive.PassiveId end)
            if okp and name and want[name] then table.insert(mine, name) end
        end
        -- Two layouts share DefaultBarContainer (bar.Controller 0 = mouse/keyboard, 1 = controller), each with its own
        -- passives bar: keyboard Index 3, controller its bar 1 next to NonLethal (2026-10-29). Bars are reached by index: an
        -- element appended to a bar reached through ipairs() didn't stick (a copy).
        for _, layout in ipairs({ 0, 1 }) do
            local onBar, target, best = {}, nil, -1
            for i = 1, #bars do
                local bar = bars[i]
                if bar.Controller == layout then
                    local n = 0
                    for j = 1, #bar.Elements do
                        local el = bar.Elements[j]
                        if el.Passive and el.Passive ~= "" then onBar[el.Passive] = true n = n + 1 end
                    end
                    if n > best or (n == best and n == 0 and layout == 0 and bar.Index == HR.PASSIVES_BAR) then target, best = bar, n end
                end
            end
            if target then
                local used = {}
                for j = 1, #target.Elements do used[target.Elements[j].Slot] = true end
                for _, name in ipairs(mine) do
                    local key = layout == 0 and name or (name .. "@" .. layout)
                    if not onBar[name] and not done[key] then
                        local slot = 0
                        while used[slot] do slot = slot + 1 end
                        used[slot] = true
                        target.Elements[#target.Elements + 1] = {
                            Slot = slot, Delete = false, IsNew = true, Passive = name,
                            SpellId = { SourceType = "Sentinel", OriginatorPrototype = "", Prototype = "",
                                        Source = "00000000-0000-0000-0000-000000000000",
                                        ProgressionSource = "00000000-0000-0000-0000-000000000000" },
                        }
                        onBar[name], done[key], changed = true, true, true
                        if layout == 0 then table.insert(added, name) end
                    end
                end
            end
        end
        if changed then entity:Replicate("HotbarContainer") end
    end)
    if not ok then Log.Warn("HotbarRepair: " .. tostring(err)) end
    return added
end

function HR.RepairAll()
    local total = 0
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("HotbarContainer")) do
        local added = HR.Repair(e)
        if #added > 0 then
            total = total + #added
            Log.Info("HotbarRepair: put " .. table.concat(added, ", ") .. " on the Passives bar of "
                .. tostring(e.Uuid and e.Uuid.EntityUuid))
        end
    end
    return total
end

if Ext.Osiris and Ext.Osiris.RegisterListener then
    Ext.Osiris.RegisterListener("LevelGameplayStarted", 2, "after", function() HR.RepairAll() end)
    Ext.Osiris.RegisterListener("CharacterJoinedParty", 1, "after", function(c)
        local e = Ext.Entity.Get(c)
        if e then HR.Repair(e) end
    end)
end

Apotheosis = Apotheosis or {}
Apotheosis.HotbarRepair = HR
return HR
