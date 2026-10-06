-- Subclass features at levels 13-20 (Scripts/gen_subclass_features.py) that need a script.
--  * Shadow Sorcery 18 Umbral Form: at 0 HP, a real Charisma save (DC 5 + half the damage); success -> 3 x Sorcerer level HP.
--  * Hollow Warden 15 Persistent Hunt: at 0 HP in Wrath of the Wild, spend a level 4+ slot -> 5 x its level HP.
--  * Hexblade 14 Masterful Hex: Infectious Hex (1d6 Necrotic to another creature within 30 ft of the cursed target)
--    and Resilient Hex (APO_RESILIENT_HEX only while you concentrate on Hex).
--  * College of Spirits 14 Mystical Connection: a second Spirits from Beyond roll, offered as a free switch.
--  * Highway Rider 17 Desperado: at 0 HP, a free Hair Trigger attack with Advantage, then you fall.
--  * Heroic Sorcery 18 Heroic Legacy: the damage above 20 is given back right after the hit.
--  * Fractured 14 Better Half: at 0 HP once per rest, 1 HP + half-max temp HP, and the Rage state swaps.
--  * Cavalier 18 Vigilant Defender (special Reaction per turn), Drunken Master 17 Intoxicated Frenzy (strikes after
--    Flurry of Blows), Watchers 15 Vigilant Rebuke (successful Int/Wis/Cha saves).
--  * Scion of the Three 13 Aura of Malevolence: damage around you after a Bloodthirst teleport.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = print }
local SF = {}
local NULL = "NULL_00000000-0000-0000-0000-000000000000"
local ABILITY = { Strength = 2, Dexterity = 3, Constitution = 4, Intelligence = 5, Wisdom = 6, Charisma = 7 }

local function short(g) return g and string.sub(g, -36) or nil end
local function has(c, p) return Osi.HasPassive(c, p) == 1 end

local function abilityMod(c, ability)
    local m = 0
    pcall(function() m = math.floor((Ext.Entity.Get(c).Stats.Abilities[ABILITY[ability]] - 10) / 2) end)
    return m
end

local function profBonus(c)
    local pb = 2
    pcall(function() pb = Ext.Entity.Get(c).Stats.ProficiencyBonus end)
    return pb
end

local function classLevel(c, class)
    local lvl = 0
    pcall(function()
        for _, cl in ipairs(Ext.Entity.Get(c).Classes.Classes) do
            local d = Ext.StaticData.Get(cl.ClassUUID, "ClassDescription")
            if d and d.Name == class then lvl = cl.Level end
        end
    end)
    return lvl
end

-- ---------------------------------------------------------------- 0 HP: Umbral Form, Persistent Hunt
local lastDamage = {}

local legacyPending = {}

function SF.HeroicLegacy(c, amount)  -- Heroic Legacy: the hit already landed, give back what was over 20
    legacyPending[c] = nil
    local e = Ext.Entity.Get(c)
    local health = e and e.Health
    if not health or (amount or 0) <= 20 then return end
    local back = amount - 20
    health.Hp = math.min(health.MaxHp, health.Hp + back)
    e:Replicate("Health")
    Log.Info("Heroic Legacy: gave back " .. back .. " HP (hit for " .. amount .. ")")
end

local lastDamageAt = {}

function SF.OnAttacked(defender, amount)
    defender = short(defender)
    lastDamage[defender] = amount
    lastDamageAt[defender] = Ext.Utils.MonotonicTime()
    if legacyPending[defender] then SF.HeroicLegacy(defender, amount) end
end

function SF.HeroicLegacyTriggered(c)  -- the OnCastHit interrupt ran after the damage: use the hit AttackedBy just recorded
    if lastDamage[c] and lastDamageAt[c] and Ext.Utils.MonotonicTime() - lastDamageAt[c] < 1500 then
        SF.HeroicLegacy(c, lastDamage[c])
    else
        legacyPending[c] = true
    end
end

local function dropToZero(c)  -- the replacement downed status left c at 1 HP: go down for real
    Osi.ApplyDamage(c, math.max(1, Osi.GetHitpoints(c)), "None", NULL)
end

local function dcGuid(value)  -- a DifficultyClass with this DC (the game ships Legacy_<n> ones)
    local best
    for _, g in ipairs(Ext.StaticData.GetAll("DifficultyClass")) do
        local d = Ext.StaticData.Get(g, "DifficultyClass")
        if d and d.Difficulties and d.Difficulties[1] == value then
            if tostring(d.Name):find("Legacy_", 1, true) == 1 then return g end
            best = best or g
        end
    end
    return best
end

-- ---------------------------------------------------------------- Highway Rider 17 Desperado
local desperado = {}  -- guid -> true while the free attack is pending

local function nearestHostile(c, range)
    local best, bestD
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local g = e.Uuid and e.Uuid.EntityUuid
        if g and g ~= c and Osi.IsDead(g) == 0 and Osi.IsEnemy(c, g) == 1 then
            local d = Osi.GetDistanceTo(c, g)
            if d and d <= range and (not bestD or d < bestD) then best, bestD = g, d end
        end
    end
    return best
end

function SF.Desperado(c)  -- APO_DESPERADO_DOWNED: you are up at 1 HP with your Reaction spent
    if desperado[c] then return end  -- the engine applies the stand-in status twice: one free attack only
    local ranged = Osi.GetEquippedItem(c, "Ranged Main Weapon") ~= nil
    local spell = ranged and "Projectile_HairTrigger" or "Target_HairTrigger"
    local foe = nearestHostile(c, ranged and 18 or 3.5)
    if not foe then
        desperado[c] = "none"
        Ext.Timer.WaitFor(300, function() desperado[c] = nil; dropToZero(c) end)
        return
    end
    desperado[c] = spell
    Log.Info("Desperado: free " .. spell .. " requested")
    SF.SpendReaction(c)
    Osi.ApplyStatus(c, "HAIR_TRIGGER", 6, 1, c)  -- unlocks the free attack spells (a moment later)
    Osi.ApplyStatus(c, "APO_DESPERADO_ADVANTAGE", 6, 1, c)
    Ext.Timer.WaitFor(400, function()
        Log.Info("Desperado: casting " .. spell)
        Osi.UseSpell(c, spell, foe)
    end)
    Ext.Timer.WaitFor(6000, function()  -- the attack never resolved: fall anyway
        if desperado[c] then Log.Warn("Desperado: the attack didn't resolve"); desperado[c] = nil; dropToZero(c) end
    end)
end

local function desperadoCasted(c, spell)
    if desperado[c] ~= spell then return end
    desperado[c] = nil
    Log.Info("Desperado: the attack resolved, falling")
    Ext.Timer.WaitFor(700, function()
        Osi.RemoveStatus(c, "APO_DESPERADO_ADVANTAGE")
        Osi.RemoveStatus(c, "HAIR_TRIGGER")
        dropToZero(c)
    end)
end

local pendingGrave = {}

-- A real engine Charisma save (proficiency, Bless, Aura of Protection... apply) against DC 5 + half the damage;
-- RollResult decides.
function SF.UmbralGrave(c)
    local dc = math.min(30, 5 + math.floor((lastDamage[c] or 0) / 2))
    local g = dcGuid(dc)
    if not g then
        Log.Warn("Umbral Form: no DifficultyClass " .. dc)
        return
    end
    pendingGrave[c] = dc
    Osi.RequestPassiveRoll(c, NULL, "SavingThrow", "Charisma", g, 0, "APO_UMBRAL_GRAVE_" .. c)
end

function SF.UmbralGraveResult(c, success)
    local dc = pendingGrave[c]
    pendingGrave[c] = nil
    Log.Info(string.format("Umbral Form: Strength of the Grave Charisma save vs DC %d -> %s", dc or -1, success and "success" or "failure"))
    if success then
        Osi.SetHitpoints(c, math.max(1, math.min(Osi.GetMaxHitpoints(c), 3 * classLevel(c, "Sorcerer"))))
    else
        Osi.RemoveStatus(c, "APO_UMBRAL_FORM")  -- 0 HP ends the form (Incapacitated) and its protection
        dropToZero(c)
    end
end

function SF.PersistentHunt(c)
    Ext.Timer.WaitFor(200, function()
        local spent
        pcall(function()
            local best
            for u, entries in pairs(Ext.Entity.Get(c).ActionResources.Resources) do
                local def = Ext.StaticData.Get(u, "ActionResource")
                if def and def.Name == "SpellSlot" then
                    for _, en in ipairs(entries) do
                        if en.Level and en.Level >= 4 and en.Amount >= 1 and (not best or en.Level < best.Level) then best = en end
                    end
                end
            end
            if best then
                best.Amount = best.Amount - 1
                Ext.Entity.Get(c):Replicate("ActionResources")
                spent = best.Level
            end
        end)
        if spent then
            Osi.SetHitpoints(c, math.min(Osi.GetMaxHitpoints(c), 5 * spent))
            Log.Info(string.format("Persistent Hunt: %s spends a level %d slot and stays up with %d HP", c, spent, 5 * spent))
        else
            Osi.ApplyStatus(c, "APO_PERSISTENT_HUNT_SPENT", 6, 1, c)
            Log.Info("Persistent Hunt: no level 4+ slot left")
            Ext.Timer.WaitFor(100, function() dropToZero(c) end)
        end
    end)
end

-- ---------------------------------------------------------------- Masterful Hex
function SF.InfectiousHex(target, warlock)
    local best, bestD
    local tx, ty, tz = Osi.GetPosition(target)
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local ok, g = pcall(function() return e.Uuid.EntityUuid end)
        if ok and g and g ~= target and g ~= warlock and Osi.IsDead(g) == 0 and Osi.IsEnemy(warlock, g) == 1 then
            local x, y, z = Osi.GetPosition(g)
            local d = x and math.sqrt((x - tx) ^ 2 + (y - ty) ^ 2 + (z - tz) ^ 2) or math.huge
            if d <= 9 and (not bestD or d < bestD) then best, bestD = g, d end
        end
    end
    if best then
        Osi.ApplyStatus(best, "APO_INFECTIOUS_HEX_DAMAGE", 0, 1, warlock)
        Log.Info("Infectious Hex: 1d6 Necrotic to " .. best)
    end
end

function SF.OnCasted(caster, spell)
    local el = spell:match("^Shout_ElementalCleaver_(%a+)$")
    if el and has(caster, "GiantPath_14_DemiurgicColossus") then  -- Demiurgic Colossus: the Cleaver's second d6
        Osi.ApplyStatus(caster, "APO_COLOSSUS_CLEAVER_" .. el:upper(), 60, 1, caster)
    end
    if not has(caster, "Hexblade_14_MasterfulHex") then return end
    if spell:sub(1, 10) == "Target_Hex" then
        Osi.ApplyStatus(caster, "APO_RESILIENT_HEX", -1, 1, caster)
    else
        local ok, conc = pcall(function() return Ext.Stats.Get(spell).SpellFlags end)
        local isConc = false
        if ok and conc then for _, f in ipairs(conc) do if f == "IsConcentration" then isConc = true end end end
        if isConc then Osi.RemoveStatus(caster, "APO_RESILIENT_HEX") end  -- a new Concentration spell ends Hex
    end
end

function SF.OnTurnStarted(c)
    if Osi.HasActiveStatus(c, "APO_RESILIENT_HEX") == 1 then
        local conc
        pcall(function() conc = Ext.Entity.Get(c).Concentration.SpellId.OriginatorPrototype end)
        if not conc or tostring(conc):sub(1, 10) ~= "Target_Hex" then Osi.RemoveStatus(c, "APO_RESILIENT_HEX") end
    end
end

-- ---------------------------------------------------------------- Mystical Connection
local switching = {}

function SF.SpiritRolled(bard, idx)
    if not has(bard, "Spirits_14_MysticalConnection") or switching[bard] then return end
    local die = 10  -- dnd55e's die: d6 / d8 (Font of Inspiration) / d10 (Magical Secrets) - always d10 by level 14
    if Osi.HasPassive(bard, "Bard_10_MagicalSecrets") ~= 1 then die = Osi.HasPassive(bard, "FontOfInspiration") == 1 and 8 or 6 end
    local second = math.random(0, die - 1)
    if second == idx then return end  -- the same spirit: nothing to choose
    Osi.ApplyStatus(bard, "APO_MYSTICAL_CONNECTION_" .. second, -1, 1, bard)
    Log.Info(string.format("Mystical Connection: rolled spirit %d, second roll %d offered", idx, second))
end

-- ---------------------------------------------------------------- group 2: resources and save reactions
local function resource(c, name)
    local entry
    pcall(function()
        for u, entries in pairs(Ext.Entity.Get(c).ActionResources.Resources) do
            local def = Ext.StaticData.Get(u, "ActionResource")
            if def and def.Name == name then entry = entries[1] end
        end
    end)
    return entry
end

local function setResource(c, name, amount)
    local e = resource(c, name)
    if e and e.Amount ~= amount then
        e.Amount = amount
        Ext.Entity.Get(c):Replicate("ActionResources")
    end
end

function SF.SpendReaction(c) setResource(c, "ReactionActionPoint", 0) end

-- Apocalypse Domain 17 Life Beyond Death, for yourself: a Downed character gets no reaction prompt, so when you drop your
-- lowest spell slot with a charge is spent and heals 10 x its level (user decision 2026-10-06; allies keep the prompt).
function SF.LifeBeyondDeathSelf(c)
    if not has(c, "Apocalypse_17_LifeBeyondDeath") then return end
    local e = Ext.Entity.Get(c)
    local best
    for u, entries in pairs(e.ActionResources.Resources) do
        local def = Ext.StaticData.Get(u, "ActionResource")
        if def and def.Name == "SpellSlot" then
            for _, en in ipairs(entries) do
                if en.Amount >= 1 and (en.Level or 0) >= 1 and (not best or en.Level < best.Level) then best = en end
            end
        end
    end
    if not best then return end
    local lvl = best.Level
    best.Amount = best.Amount - 1
    e:Replicate("ActionResources")
    Osi.ApplyStatus(c, "APO_LIFE_BEYOND_DEATH_" .. lvl, 0, 1, c)
    Log.Info(string.format("Life Beyond Death: %s spends a level %d slot and heals %d", c, lvl, 10 * lvl))
end

local function inCombatWith(c)  -- characters near c (60 m) that are in combat
    local out, cx, cy, cz = {}, Osi.GetPosition(c)
    if not cx then return out end
    for _, e in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local ok, g = pcall(function() return e.Uuid.EntityUuid end)
        if ok and g and Osi.IsInCombat(g) == 1 then
            local x, y, z = Osi.GetPosition(g)
            if x and math.sqrt((x - cx) ^ 2 + (z - cz) ^ 2) < 60 then out[#out + 1] = g end
        end
    end
    return out
end

-- Cavalier 18 Vigilant Defender: the special Reaction is there on every other creature's turn, never on your own
function SF.VigilantDefenderTurn(current)
    for _, g in ipairs(inCombatWith(current)) do
        if has(g, "Cavalier_18_VigilantDefender") then setResource(g, "ApoVigilantDefender", g == current and 0 or 1) end
    end
end

-- Drunken Master 17 Intoxicated Frenzy: three extra strikes after Flurry of Blows, gone at the start of your turn
function SF.FlurryUsed(monk, target)
    if not has(monk, "DrunkenMaster_17_IntoxicatedFrenzy") then return end
    setResource(monk, "ApoIntoxicatedFrenzy", 3)
    if target then Osi.ApplyStatus(target, "APO_FRENZY_STRUCK", 6, 1, monk) end
end

-- Watchers 15 Vigilant Rebuke: a successful Int/Wis/Cha save by you or an ally within 30 feet
local MENTAL = { Intelligence = true, Wisdom = true, Charisma = true }
local seenSaves = {}

function SF.OnSave(c)
    local key = tostring(c.ConditionRoll.RollUuid)
    if seenSaves[key] then return end
    seenSaves[key] = true
    if not MENTAL[tostring(c.Ability)] then return end
    if c.ConditionRoll.Roll.Result.Total < c.ConditionRoll.Difficulty then return end
    local function g(h) local ok2, v = pcall(function() return h.Uuid.EntityUuid end) return ok2 and v or nil end
    local saver, source = g(c.Target), g(c.Source)
    local sc = tostring(c.SpellCastUuid)
    if sc ~= "00000000-0000-0000-0000-000000000000" and sc ~= "nil" then saver, source = source, saver end
    if c.ConditionRoll.SwappedSourceAndTarget then saver, source = source, saver end
    if not saver or not source or saver == source then return end
    for _, w in ipairs(inCombatWith(saver)) do
        if has(w, "Watchers_15_VigilantRebuke") and (w == saver or Osi.IsAlly(w, saver) == 1) and Osi.IsEnemy(w, source) == 1 then
            local x1, y1, z1 = Osi.GetPosition(w)
            local x2, y2, z2 = Osi.GetPosition(saver)
            local react = resource(w, "ReactionActionPoint")
            if x1 and math.sqrt((x1 - x2) ^ 2 + (z1 - z2) ^ 2) <= 9 and react and react.Amount >= 1 then
                react.Amount = react.Amount - 1
                Ext.Entity.Get(w):Replicate("ActionResources")
                Osi.ApplyStatus(source, "APO_VIGILANT_REBUKE", 0, 1, w)
                Log.Info("Vigilant Rebuke: " .. source .. " takes 2d8 + Charisma Force damage")
                return
            end
        end
    end
end

-- ---------------------------------------------------------------- Fractured 14 Better Half
function SF.BetterHalf(c)  -- APO_BETTER_HALF_DOWNED: up at 1 HP; half-max temp HP, swap raging, use up the once-per-rest
    setResource(c, "ApoBetterHalf", 0)
    local e = Ext.Entity.Get(c)
    local health = e and e.Health
    if health then
        health.TemporaryHp = math.floor(health.MaxHp / 2)
        e:Replicate("Health")
    else
        Log.Warn("Better Half: no Health component, temp HP skipped")
    end
    local raging = false
    local ids = {}
    for _, id in pairs(e.StatusContainer and e.StatusContainer.Statuses or {}) do ids[#ids + 1] = tostring(id) end
    for _, id in ipairs(ids) do
        if id:match("^RAGE") then raging = true; Osi.RemoveStatus(c, id) end
    end
    if not raging then Osi.UseSpell(c, "Shout_Rage", c) end
    Log.Info("Better Half: 1 HP, temp HP " .. tostring(health and health.TemporaryHp) .. ", raging was " .. tostring(raging))
end

-- ---------------------------------------------------------------- Scion of the Three 13 Aura of Malevolence (Heroes of Faerun)
-- After a Bloodthirst teleport: each enemy within 10 feet of where you land takes damage equal to your Intelligence modifier,
-- of your Dread Allegiance's type (Bane Psychic, Bhaal Poison, Myrkul Necrotic). The rule's "ignores Resistance" isn't modelled.
local MALEVOLENCE = { DREAD_ALLEGIANCE_1 = "Psychic", DREAD_ALLEGIANCE_2 = "Poison", DREAD_ALLEGIANCE_3 = "Necrotic" }

function SF.AuraOfMalevolence(c)
    if not has(c, "DeadThree_13_AuraOfMalevolence") then return end
    local dtype
    for st, t in pairs(MALEVOLENCE) do
        if Osi.HasActiveStatus(c, st) == 1 then dtype = t end
    end
    if not dtype then return end
    local dmg = math.max(1, abilityMod(c, "Intelligence"))
    Ext.Timer.WaitFor(800, function()   -- the jump has landed
        local x, _, z = Osi.GetPosition(c)
        if not x then return end
        for _, g in ipairs(inCombatWith(c)) do
            local gx, _, gz = Osi.GetPosition(g)
            if g ~= c and gx and Osi.IsEnemy(c, g) == 1 and Osi.IsDead(g) ~= 1 and math.sqrt((gx - x) ^ 2 + (gz - z) ^ 2) <= 3 then
                Osi.ApplyDamage(g, dmg, dtype, c)
                Log.Info(string.format("Aura of Malevolence: %s takes %d %s", g, dmg, dtype))
            end
        end
    end)
end

-- ---------------------------------------------------------------- listeners
local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("SubclassFeatures " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, _, _, _, amount)
    SF.OnAttacked(defender, amount)
end))

Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(target, status, causee)
    target = short(target)
    if status == "APO_UMBRAL_GRAVE_DOWNED" then
        SF.UmbralGrave(target)
    elseif status == "APO_PERSISTENT_HUNT_DOWNED" then
        SF.PersistentHunt(target)
    elseif status == "APO_DESPERADO_DOWNED" then
        SF.Desperado(target)
    elseif status == "APO_HEROIC_LEGACY_TRIGGER" then
        SF.HeroicLegacyTriggered(target)
    elseif status == "DOWNED" then
        SF.LifeBeyondDeathSelf(target)
    elseif status == "APO_BETTER_HALF_DOWNED" then
        SF.BetterHalf(target)
    elseif status == "APO_INFECTIOUS_HEX" and causee then
        SF.InfectiousHex(target, short(causee))
    elseif status:match("^SPIRITS_FROM_BEYOND_%d$") then
        SF.SpiritRolled(target, tonumber(status:match("(%d)$")))
    end
end))

Ext.Osiris.RegisterListener("UsingSpell", 5, "before", guard("UsingSpell", function(c, spell)
    c = short(c)
    if spell:match("^Shout_ApoMysticalConnection_") then  -- the switch applies a spirit: don't offer another
        switching[c] = true
        Ext.Timer.WaitFor(1500, function() switching[c] = nil end)
    end
end))

Ext.Osiris.RegisterListener("RollResult", 6, "after", guard("RollResult", function(ev, roller, _, result)
    if type(ev) == "string" and ev:sub(1, 17) == "APO_UMBRAL_GRAVE_" then
        SF.UmbralGraveResult(ev:sub(18), result == 1)
    end
end))

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(c, spell)
    SF.OnCasted(short(c), spell)
    if spell == "Projectile_Bloodthirst" then SF.AuraOfMalevolence(short(c)) end
    desperadoCasted(short(c), spell)
end))
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c)
    c = short(c)
    SF.OnTurnStarted(c)
    SF.VigilantDefenderTurn(c)
    if has(c, "DrunkenMaster_17_IntoxicatedFrenzy") then setResource(c, "ApoIntoxicatedFrenzy", 0) end
end))
Ext.Osiris.RegisterListener("UsingSpellOnTarget", 6, "after", guard("UsingSpellOnTarget", function(c, target, spell)
    if spell == "Target_FlurryOfBlows" or spell:sub(1, 20) == "Target_FlurryOfBlows" then SF.FlurryUsed(short(c), short(target)) end
end))
Ext.Entity.OnCreateDeferred("SavingThrowRolledEvent", function(_, _, c)
    local ok, err = pcall(SF.OnSave, c)
    if not ok then Log.Error("SubclassFeatures SavingThrowRolledEvent: " .. tostring(err)) end
end)

return SF
