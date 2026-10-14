-- Creeping Death (Grim Hollow Player's Guide, 8th-level Sangromancy; Scripts/gen_sangromancy.py writes the stats side).
-- "Roll the expended Hit Point Dice: the target's creeping death threshold is the roll's total. For the duration, if the creature's
-- Hit Points are reduced to or lower than its threshold, it immediately dies. As a Bonus Action you can force the target to make a
-- Constitution saving throw: on a failure roll 2d6 and add it to the threshold, on a success add half the result instead. If the
-- creature succeeds on three saves, the spell ends early."
-- The spell puts CREEPING_DEATH_<die>_<dice> on the target (dice = slot level = dice expended); this module rolls the threshold from
-- that name, watches the target's Health, kills it when an HP reduction takes it to or below the threshold, and applies the Surge
-- markers (CREEPING_DEATH_SURGE_FAIL / _SAVE, one-turn statuses it removes at once). Concentration ending removes the statuses
-- (the engine), which clears the mark here. "Reduced" is taken literally: a threshold raised above the creature's current HP kills it
-- on its next HP loss, not at once.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = function() end }
local CD = { marks = {}, count = 0 }
local MARK = "^CREEPING_DEATH_(%d+)_(%d+)$"
local NO_KILLER = "NULL_00000000-0000-0000-0000-000000000000"
local sub

local function id(guid)
    return guid and string.sub(guid, -36) or nil
end

local function roll(n, die)
    local total = 0
    for _ = 1, n do total = total + Ext.Math.Random(1, die) end
    return total
end

local function hpOf(guid)
    local e = guid and Ext.Entity.Get(guid)
    return e and e.Health and e.Health.Hp or nil
end

local function kill(target, caster)
    local ok = pcall(Osi.Die, target, 0, caster or NO_KILLER, 0, 1)
    if not ok then pcall(Osi.ApplyDamage, target, 100000, "Necrotic", caster) end
end

local function onHealth(entity)
    local g = entity and entity.Uuid and entity.Uuid.EntityUuid
    local m = g and CD.marks[g]
    if not m or not entity.Health then return end
    local hp = entity.Health.Hp
    if hp < m.hp and hp <= m.threshold then
        Log.Info(("Creeping Death: %s fell to %d HP, at or below its threshold %d: dies"):format(g, hp, m.threshold))
        CD.Clear(g)
        kill(g, m.caster)
        return
    end
    m.hp = hp
end

local function startWatching()
    if not sub then sub = Ext.Entity.Subscribe("Health", onHealth) end
end

local function stopWatching()
    if sub and CD.count == 0 then
        Ext.Entity.Unsubscribe(sub)
        sub = nil
    end
end

function CD.Clear(target)
    if CD.marks[target] then
        CD.marks[target] = nil
        CD.count = CD.count - 1
        stopWatching()
    end
end

-- the spell ends (three saves): take every Creeping Death status off the target and off the caster
function CD.End(target, caster)
    local m = CD.marks[target]
    caster = caster or (m and m.caster)
    CD.Clear(target)
    local e = Ext.Entity.Get(target)
    if e and e.StatusContainer then
        for status in pairs(e.StatusContainer.Statuses) do
            if string.match(status, MARK) or status == "CREEPING_DEATH_MARK" then Osi.RemoveStatus(target, status) end
        end
    end
    if caster then pcall(Osi.RemoveStatus, caster, "CREEPING_DEATH_CASTER") end
end

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", function(object, status, causee, _)
    local ok, err = pcall(function()
        local die, dice = string.match(status, MARK)
        if die then
            local threshold = roll(tonumber(dice), tonumber(die))
            local g = id(object)
            if not CD.marks[g] then CD.count = CD.count + 1 end
            CD.marks[g] = { threshold = threshold, saves = 0, caster = causee, hp = hpOf(object) or 0 }
            startWatching()
            Log.Info(("Creeping Death: %s marked, threshold %dd%d = %d"):format(g, tonumber(dice), tonumber(die), threshold))
        elseif status == "CREEPING_DEATH_SURGE_FAIL" or status == "CREEPING_DEATH_SURGE_SAVE" then
            local g = id(object)
            local m = CD.marks[g]
            Osi.RemoveStatus(object, status)
            if not m then return end
            local add = roll(2, 6)
            if status == "CREEPING_DEATH_SURGE_SAVE" then
                add = add // 2
                m.saves = m.saves + 1
            end
            m.threshold = m.threshold + add
            Log.Info(("Creeping Death: %s threshold +%d = %d (%d saves)"):format(g, add, m.threshold, m.saves))
            if m.saves >= 3 then CD.End(g, m.caster) end
        end
    end)
    if not ok then Log.Error("Creeping Death (StatusApplied): " .. tostring(err)) end
end)

Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", function(object, status, _, _)
    if string.match(status, MARK) then CD.Clear(id(object)) end   -- the spell ended, was dispelled or lost its concentration
end)

Ext.Osiris.RegisterListener("Died", 1, "after", function(character)
    CD.Clear(id(character))
end)

-- Steal Immortality (9th): "you gain the creature's type and its benefits". The interrupt (Interrupt_Apo_StealImmortality_<die>)
-- can't test the dying creature's type in its Properties - an IF() before ApplyStatus(OBSERVER_OBSERVER, ...) is evaluated against
-- the observer (STEAL_IMMORTALITY_UNDEAD never landed, 2026-10-13) - so the type is read here, when the interrupt is used: the hit
-- creature's tags -> STEAL_IMMORTALITY_<TYPE> on the reacting caster. Its Conditions already require one of these types.
local SI_TYPES = { "CELESTIAL", "ELEMENTAL", "FEY", "FIEND", "UNDEAD" }

local function tagsOf(ent)
    local out = {}
    pcall(function()
        for _, t in ipairs(ent.Tag.Tags) do
            local d = Ext.StaticData.Get(t, "Tag")
            if d then out[d.Name] = true end
        end
    end)
    return out
end

local function guidOf(ent)
    local ok, g = pcall(function() return ent.Uuid.EntityUuid end)
    return ok and g or nil
end

Ext.Entity.OnCreate("ServerInterruptUsed", function(e)
    local ok, err = pcall(function()
        for ient, events in pairs(e.ServerInterruptUsed.Interrupts) do
            local data = ient.InterruptData
            if data and string.find(tostring(data.Interrupt), "^Interrupt_Apo_StealImmortality_") then
                local caster = guidOf(e) or guidOf(data.Caster)
                for ev in pairs(events) do
                    local victim = ev.SwapSourceTarget and ev.Source or ev.Target
                    local tags, typ = tagsOf(victim), nil
                    for _, t in ipairs(SI_TYPES) do if tags[t] then typ = t break end end
                    if caster and typ then
                        for _, t in ipairs(SI_TYPES) do Osi.RemoveStatus(caster, "STEAL_IMMORTALITY_" .. t) end   -- recast: the newest type wins
                        Osi.ApplyStatus(caster, "STEAL_IMMORTALITY_" .. typ, -1, 1, caster)
                        Log.Info(("Steal Immortality: %s took the %s type from %s"):format(caster, typ, tostring(guidOf(victim))))
                    else
                        Log.Warn(("Steal Immortality: no type applied (caster %s, victim %s)"):format(tostring(caster), tostring(guidOf(victim))))
                    end
                end
            end
        end
    end)
    if not ok then Log.Error("Steal Immortality (ServerInterruptUsed): " .. tostring(err)) end
end)

Apotheosis.Sangromancy = CD
return CD
