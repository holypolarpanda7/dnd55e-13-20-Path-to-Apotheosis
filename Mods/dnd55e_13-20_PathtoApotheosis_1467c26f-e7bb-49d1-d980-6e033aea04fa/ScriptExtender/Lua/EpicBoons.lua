-- Epic Boons (PHB 2024 level-19 feats), Script Extender half. Stats half: Scripts/gen_epic_boons.py.
-- Only the parts stats can't express (VISION principle 4):
--   Dimensional Travel  Blink Steps after an Attack or Magic action (a cast that costs an ActionPoint)
--   Spell Recall        roll 1d4 after a level 1-4 slot spell; on a match the slot comes back
--   Irresistible Off.   Overwhelming Strike: extra damage = the boosted ability score on a critical hit
--   Recovery            Last Stand heals to 1 + half the Hit Point maximum
--   Fate                Improve Fate recharges when you roll Initiative
--   Energy Resistance   Energy Redirection: spends your Reaction to send the damage back at the attacker
-- Documented gaps: Overwhelming Strike and Peerless Aim trigger on any critical / keep natural 1s as misses;
-- Energy Redirection targets whoever damaged you and fires automatically.
local Log = Apotheosis and Apotheosis.Log or { Info = print, Warn = print, Error = print, Debug = function() end }
local EB = {}

local VARIANT_ABILITY = {
    EpicBoon_IrresistibleOffense_Str = "Strength", EpicBoon_IrresistibleOffense_Dex = "Dexterity",
    EpicBoon_SpellRecall_Int = "Intelligence", EpicBoon_SpellRecall_Wis = "Wisdom", EpicBoon_SpellRecall_Cha = "Charisma",
}
local ABILITY_INDEX = { Strength = 2, Dexterity = 3, Constitution = 4, Intelligence = 5, Wisdom = 6, Charisma = 7 }

local function has(c, passive) return Osi.HasPassive(c, passive) == 1 end

local resourceUUIDs = {}
local function resourceUUID(name)
    if resourceUUIDs[name] == nil then
        resourceUUIDs[name] = false
        for _, u in pairs(Ext.StaticData.GetAll("ActionResource")) do
            local r = Ext.StaticData.Get(u, "ActionResource")
            if r and r.Name == name then resourceUUIDs[name] = u break end
        end
    end
    return resourceUUIDs[name] or nil
end

-- entries of a resource on a character, keyed by resource level (0 for non-slot resources)
local function resourceEntries(c, name)
    local u, e = resourceUUID(name), Ext.Entity.Get(c)
    if not (u and e and e.ActionResources) then return nil, e end
    return e.ActionResources.Resources[u], e
end

local function useCosts(spell)
    local s = Ext.Stats.Get(spell)
    return s and tostring(s.UseCosts) or "", s
end

-- ---------------------------------------------------------------- Blink Steps + Spell Recall
function EB.OnCast(caster, spell)
    local costs, stat = useCosts(spell)
    if has(caster, "EpicBoon_DimensionalTravel") and costs:find("ActionPoint:") and not costs:find("BonusActionPoint:")
        and spell ~= "Target_EpicBoon_BlinkStep" then
        Osi.ApplyStatus(caster, "EPIC_BLINK_STEPS", 6.0, 1)
    end
    local recall = has(caster, "EpicBoon_SpellRecall_Int") or has(caster, "EpicBoon_SpellRecall_Wis") or has(caster, "EpicBoon_SpellRecall_Cha")
    local level = stat and tonumber(stat.Level) or 0
    if recall and level >= 1 and level <= 4 and costs:find("SpellSlot") then
        local roll = Ext.Math.Random(1, 4)
        if roll ~= level then return end
        for _, pool in ipairs({ "SpellSlot", "WarlockSpellSlot" }) do
            local entries, e = resourceEntries(caster, pool)
            for _, x in ipairs(entries or {}) do
                if x.ResourceId == level and x.Amount < x.MaxAmount then
                    x.Amount = x.Amount + 1
                    e:Replicate("ActionResources")
                    Log.Info(string.format("Spell Recall: %s rolled %d on a level %d %s - slot kept", tostring(caster), roll, level, spell))
                    return
                end
            end
        end
    end
end

-- ---------------------------------------------------------------- Energy Redirection + Overwhelming Strike
local lastDamageType = {}

-- Osi.UseSpell queues casts with IgnoreSpellRolls, so the target's saving throw would never be rolled (found
-- 2026-10-01). Strip that option from our own request when it reaches the server's cast queue.
local pendingRolled = {}
local rolledSub
local function castWithRolls(caster, spell, target)
    table.insert(pendingRolled, { spell = spell, ticks = 0 })
    if not rolledSub then
        rolledSub = Ext.Events.Tick:Subscribe(function()
            if #pendingRolled == 0 then return end
            for _, r in ipairs(Ext.System.ServerCastRequest.OsirisCastRequests) do
                for i, p in ipairs(pendingRolled) do
                    if r.Spell.OriginatorPrototype == p.spell then
                        local keep = {}
                        for _, o in ipairs(r.CastOptions) do if o ~= "IgnoreSpellRolls" then keep[#keep + 1] = o end end
                        r.CastOptions = keep
                        table.remove(pendingRolled, i)
                        break
                    end
                end
            end
            for i = #pendingRolled, 1, -1 do
                pendingRolled[i].ticks = pendingRolled[i].ticks + 1
                if pendingRolled[i].ticks > 60 then table.remove(pendingRolled, i) end
            end
        end)
    end
    Osi.UseSpell(caster, spell, target)
end

function EB.OnAttacked(defender, attacker, damageType, amount)
    if attacker and defender then lastDamageType[attacker .. "|" .. defender] = damageType end
    if not (amount and amount > 0 and attacker and attacker ~= defender and has(defender, "EpicBoon_EnergyResistance")) then return end
    if Osi.HasActiveStatus(defender, "EPIC_ENERGY_RES_" .. string.upper(tostring(damageType))) ~= 1 then return end
    if Osi.IsDead(attacker) == 1 or Osi.IsDead(defender) == 1 then return end
    local entries, e = resourceEntries(defender, "ReactionActionPoint")
    local r = entries and entries[1]
    if not r or r.Amount < 1 then return end
    r.Amount = r.Amount - 1
    e:Replicate("ActionResources")
    castWithRolls(defender, "Target_EpicBoon_EnergyRedirection_" .. tostring(damageType), attacker)  -- Dex save rolled
    Log.Info(string.format("Energy Redirection: %s redirects %s damage at %s", tostring(defender), tostring(damageType), tostring(attacker)))
end

function EB.OnCritical(attacker, target)
    for passive, ability in pairs(VARIANT_ABILITY) do
        if passive:find("IrresistibleOffense") and has(attacker, passive) then
            local e = Ext.Entity.Get(attacker)
            local score = e and e.Stats and e.Stats.Abilities[ABILITY_INDEX[ability]] or 0
            local dtype = lastDamageType[attacker .. "|" .. target] or "Bludgeoning"
            Osi.ApplyDamage(target, score, dtype, attacker)
            Log.Info(string.format("Overwhelming Strike: %s deals %d %s (%s score)", tostring(attacker), score, dtype, ability))
            return
        end
    end
end

-- ---------------------------------------------------------------- Last Stand, Fate, ability pick
function EB.OnStatus(object, status, causee)
    if status == "EPIC_LAST_STAND_DOWNED" then
        Ext.Timer.WaitFor(300, function()
            local mx = Osi.GetMaxHitpoints(object)
            Osi.SetHitpoints(object, math.min(mx, 1 + math.floor(mx / 2)))
            Log.Info("Last Stand: " .. tostring(object) .. " stays up with half their Hit Points")
        end)
    elseif status == "EPIC_OVERWHELMING_MARK" and causee then
        EB.OnCritical(causee, object)
    end
end

local hasAny  -- defined below; used here first (it was a nil global: 'attempt to call a nil value' at every combat start)
function EB.OnEnteredCombat(object)
    if hasAny(object, "EpicBoon_EruptingSpellpower") then  -- Spell Overload returns when you roll Initiative
        local entries, e = resourceEntries(object, "EpicBoonOverload")
        if entries and entries[1] and entries[1].Amount < entries[1].MaxAmount then
            entries[1].Amount = entries[1].MaxAmount
            e:Replicate("ActionResources")
        end
    end
    if not has(object, "EpicBoon_Fate") then return end
    local entries, e = resourceEntries(object, "EpicBoonFate")
    if entries and entries[1] and entries[1].Amount < entries[1].MaxAmount then
        entries[1].Amount = entries[1].MaxAmount
        e:Replicate("ActionResources")
    end
end

-- After a level-up: arm the standing statuses of boons just gained (passives gained at level-up don't run OnCreate).
-- Boons are feats since 2026-10-06, so one can arrive at any level from 19 (a multiclass character's later feat pick):
-- "just gained" is tracked per character in PersistentVars instead of by level, so a used status isn't re-armed early.
local ARMED_ON_GAIN = { EpicBoon_Recovery = "EPIC_LAST_STAND", EpicBoon_ExquisiteRadiance = "EPIC_POWERFUL_RADIANCE" }
function EB.Validate(c)
    PersistentVars = PersistentVars or {}
    PersistentVars.EpicBoonArmed = PersistentVars.EpicBoonArmed or {}
    local armed = PersistentVars.EpicBoonArmed
    for passive, status in pairs(ARMED_ON_GAIN) do
        local key = c .. "|" .. passive
        if has(c, passive) and not armed[key] then
            armed[key] = true
            if Osi.HasActiveStatus(c, status) ~= 1 then Osi.ApplyStatus(c, status, -1, 1) end
        end
    end
    -- standing statuses that don't get used up
    if has(c, "EpicBoon_Truesight") and Osi.HasActiveStatus(c, "TRUESIGHT") ~= 1 then
        Osi.ApplyStatus(c, "TRUESIGHT", -1, 1)
    end
    if has(c, "EpicBoon_PoisonMastery") and Osi.HasActiveStatus(c, "EPIC_PERFECT_POISONER") ~= 1 then
        Osi.ApplyStatus(c, "EPIC_PERFECT_POISONER", -1, 1)
    end
end

-- ---------------------------------------------------------------- phase 2 (Heroes of Faerun, Arcana Unleashed)
hasAny = function(c, base) -- a boon with per-ability variants (EpicBoon_X_Int, ...) or a plain one
    if has(c, base) then return true end
    for _, s in ipairs({ "Str", "Dex", "Con", "Int", "Wis", "Cha" }) do if has(c, base .. "_" .. s) then return true end end
    return false
end
local function res(c, name) return Osi.GetActionResourceValuePersonal(c, name, 0) or 0 end
local function spend(c, name)
    local entries, e = resourceEntries(c, name)
    local r = entries and entries[1]
    if not r or r.Amount < 1 then return false end
    r.Amount = r.Amount - 1
    e:Replicate("ActionResources")
    return true
end
local function bloodied(c)
    local hp, mx = Osi.GetHitpoints(c), Osi.GetMaxHitpoints(c)
    return hp and mx and mx > 0 and hp * 2 <= mx
end
local function profBonus(c) local ok, v = pcall(function() return Ext.Entity.Get(c).Stats.ProficiencyBonus end) return ok and v or 2 end
local function nearbyCharacters(c, radius)
    local out = {}
    for _, ent in ipairs(Ext.Entity.GetAllEntitiesWithComponent("ServerCharacter")) do
        local g = ent.Uuid and ent.Uuid.EntityUuid
        if g and Osi.IsDead(g) ~= 1 then
            local d = Osi.GetDistanceTo(g, c)
            if d and d <= radius then out[#out + 1] = g end
        end
    end
    return out
end
local function frightened(c)  -- dnd55e's FRIGHTENED is a BOOST status: check the SG_Frightened group, not FEAR type
    local ok, found = pcall(function()
        for _, sid in pairs(Ext.Entity.Get(c).StatusContainer.Statuses) do
            local s = Ext.Stats.Get(tostring(sid))
            if tostring(sid) == "FRIGHTENED" or (s and tostring(s.StatusGroups):find("SG_Frightened")) then return true end
        end
        return false
    end)
    return ok and found
end
local function spellDealsType(spell, types)
    local s = Ext.Stats.Get(spell)
    if not s then return false end
    -- SpellProperties/SpellSuccess come back as parsed functor arrays, not text: read the string fields
    local text = tostring(s.TooltipDamageList or "") .. ";" .. tostring(s.DamageType or "")
    for _, t in ipairs(types) do if text:find(t) then return true end end
    return false
end

-- an enemy dropped to 0 Hit Points (died or downed): Killer's Fortune, Siphon Life
function EB.OnEnemyDown(victim)
    for _, c in ipairs(nearbyCharacters(victim, 36)) do
        if c ~= string.sub(victim, -36) and Osi.IsEnemy(c, victim) == 1 then
            if hasAny(c, "EpicBoon_Bloodshed") and Osi.CanSee(c, victim) == 1 then
                Osi.ApplyStatus(c, "EPIC_KILLERS_FORTUNE", 12.0, 1, c)
            end
            if hasAny(c, "EpicBoon_SoulDrinker") and res(c, "EpicBoonSoulDrinker") >= 1 and res(c, "ReactionActionPoint") >= 1 then
                spend(c, "EpicBoonSoulDrinker") spend(c, "ReactionActionPoint")
                Osi.ApplyStatus(c, "EPIC_SIPHON_LIFE", 0, 1, c)
                Log.Info("Siphon Life: " .. tostring(c) .. " regains 50 Hit Points")
            end
        end
    end
end

local overloadWindow = {}
function EB.OnDamageDealt(defender, attacker, damageType, amount, cause)
    if not (attacker and defender and amount and amount > 0) or attacker == defender then return end
    -- Power from Pain: once per turn, an attack hit while Bloodied adds the Proficiency Bonus
    if cause == "Attack" and hasAny(attacker, "EpicBoon_Bloodshed") and bloodied(attacker)
        and Osi.HasActiveStatus(attacker, "EPIC_POWER_FROM_PAIN_USED") ~= 1 then
        Osi.ApplyStatus(attacker, "EPIC_POWER_FROM_PAIN_USED", 6.0, 1, attacker)
        Osi.ApplyDamage(defender, profBonus(attacker), damageType, attacker)
        Log.Info(string.format("Power from Pain: %s +%d %s", tostring(attacker), profBonus(attacker), tostring(damageType)))
    end
    -- Powerful Radiance / Perfect Poisoner: the maximized roll was used
    if damageType == "Radiant" and Osi.HasActiveStatus(attacker, "EPIC_POWERFUL_RADIANCE") == 1 then
        Ext.Timer.WaitFor(300, function() Osi.RemoveStatus(attacker, "EPIC_POWERFUL_RADIANCE") end)
    end
    if damageType == "Poison" and Osi.HasActiveStatus(attacker, "EPIC_PERFECT_POISONER") == 1 then
        Ext.Timer.WaitFor(300, function() Osi.RemoveStatus(attacker, "EPIC_PERFECT_POISONER") end)
    end
    -- Spell Overload: creatures the surged spell damages are knocked Prone
    if overloadWindow[attacker] then Osi.ApplyStatus(defender, "PRONE", 6.0, 1, attacker) end
end

function EB.OnUsingSpell(caster, spell)
    if spell:find("^Shout_HitPointDice") and hasAny(caster, "EpicBoon_BountifulHealth") then  -- Superior Recuperation
        Osi.ApplyStatus(caster, "EPIC_SUPERIOR_RECUPERATION", 6.0, 1, caster)
        Ext.Timer.WaitFor(3000, function() Osi.RemoveStatus(caster, "EPIC_SUPERIOR_RECUPERATION") end)
    end
    local costs, stat = useCosts(spell)
    if Osi.HasActiveStatus(caster, "EPIC_SPELL_OVERLOAD_ARMED") == 1 and costs:find("SpellSlot")
        and spellDealsType(spell, { "DealDamage" }) and res(caster, "EpicBoonOverload") >= 1 then
        spend(caster, "EpicBoonOverload")
        Osi.ApplyStatus(caster, "EPIC_SPELL_OVERLOAD", 6.0, 1, caster)
        overloadWindow[caster] = true
        Ext.Timer.WaitFor(4000, function() overloadWindow[caster] = nil Osi.RemoveStatus(caster, "EPIC_SPELL_OVERLOAD") end)
        Log.Info("Spell Overload: " .. tostring(caster) .. " surges " .. spell)
    end
end

function EB.OnTurnStarted(c)
    if hasAny(c, "EpicBoon_PoisonMastery") and Osi.HasActiveStatus(c, "EPIC_PERFECT_POISONER") ~= 1 then
        Osi.ApplyStatus(c, "EPIC_PERFECT_POISONER", -1, 1, c)
    end
    if Osi.HasActiveStatus(c, "EPIC_DAYLIGHT_PRESENCE") == 1 then  -- Fortifying Light
        for _, g in ipairs(nearbyCharacters(c, 9)) do
            if (g == string.sub(c, -36) or Osi.IsAlly(c, g) == 1) and Osi.CanSee(c, g) == 1 then
                Osi.ApplyStatus(g, "EPIC_FORTIFYING_LIGHT", -1, 1, c)
            end
        end
    end
    -- Flee, Fools!: a Frightened creature starts its turn within 60 feet of a Boon of Terror holder
    if frightened(c) then
        for _, holder in ipairs(nearbyCharacters(c, 18)) do
            if hasAny(holder, "EpicBoon_Terror") and Osi.IsEnemy(holder, c) == 1 and Osi.CanSee(holder, c) == 1
                and res(holder, "EpicBoonTerror") >= 1 and res(holder, "ReactionActionPoint") >= 1 then
                spend(holder, "EpicBoonTerror") spend(holder, "ReactionActionPoint")
                castWithRolls(holder, "Target_EpicBoon_FleeFools", c)
                Log.Info("Flee, Fools!: " .. tostring(holder) .. " stokes " .. tostring(c))
                break
            end
        end
    end
end

function EB.OnStatusPhase2(object, status, causee)
    if status:find("DOWNED") then EB.OnEnemyDown(object) end
    if status == "IRRESISTIBLE_DANCE" and causee and hasAny(causee, "EpicBoon_Revelry") then  -- Sing Out
        Osi.ApplyStatus(object, "EPIC_SING_OUT", 60.0, 1, causee)
    end
end

function EB.OnStatusRemoved(object, status, causee)
    if status == "IRRESISTIBLE_DANCE" then
        Osi.RemoveStatus(object, "EPIC_SING_OUT")
        if causee then Osi.RemoveStatus(causee, "EPIC_REVELRY_FOCUS") end
    end
end

function EB.OnCastPhase2(caster, spell)
    if (spell == "Target_IrresistibleDance" or spell == "Target_EpicBoon_IrresistibleDance") and hasAny(caster, "EpicBoon_Revelry") then
        Osi.ApplyStatus(caster, "EPIC_REVELRY_FOCUS", 60.0, 1, caster)
    end
end

-- Augmented Health: +5 whenever you gain Temporary Hit Points (watched every few frames for boon holders)
local lastTemp, tickN = {}, 0
function EB.TickAugmentedHealth()
    tickN = tickN + 1
    if tickN % 10 ~= 0 or not Osi.DB_Players then return end  -- the tick starts before the story's databases exist
    for _, row in pairs(Osi.DB_Players:Get(nil) or {}) do
        local c = row[1]
        if hasAny(c, "EpicBoon_BountifulHealth") then
            local e = Ext.Entity.Get(c)
            local cur = e and e.Health and e.Health.TemporaryHp or 0
            local was = lastTemp[c] or 0
            if cur > was then
                e.Health.TemporaryHp = cur + 5
                if e.Health.MaxTemporaryHp and e.Health.MaxTemporaryHp < cur + 5 then e.Health.MaxTemporaryHp = cur + 5 end
                e:Replicate("Health")
                cur = cur + 5
                Log.Info(string.format("Augmented Health: %s gains 5 more Temporary Hit Points (%d)", tostring(c), cur))
            end
            lastTemp[c] = cur
        end
    end
end

local function guard(name, fn)
    return function(...)
        local ok, err = pcall(fn, ...)
        if not ok then Log.Error("EpicBoons " .. name .. ": " .. tostring(err)) end
    end
end

Ext.Osiris.RegisterListener("CastedSpell", 5, "after", guard("CastedSpell", function(caster, spell) EB.OnCast(caster, spell) EB.OnCastPhase2(caster, spell) end))
Ext.Osiris.RegisterListener("AttackedBy", 7, "after", guard("AttackedBy", function(defender, attackerOwner, _, damageType, amount, cause)
    EB.OnAttacked(defender, attackerOwner, damageType, amount)
    EB.OnDamageDealt(defender, attackerOwner, damageType, amount, cause)
end))
Ext.Osiris.RegisterListener("StatusApplied", 4, "after", guard("StatusApplied", function(object, status, causee)
    EB.OnStatus(object, status, causee) EB.OnStatusPhase2(object, status, causee)
end))
Ext.Osiris.RegisterListener("StatusRemoved", 4, "after", guard("StatusRemoved", function(object, status, causee) EB.OnStatusRemoved(object, status, causee) end))
Ext.Osiris.RegisterListener("Died", 1, "after", guard("Died", function(c) EB.OnEnemyDown(c) end))
Ext.Osiris.RegisterListener("UsingSpell", 5, "after", guard("UsingSpell", function(caster, spell) EB.OnUsingSpell(caster, spell) end))
Ext.Osiris.RegisterListener("TurnStarted", 1, "after", guard("TurnStarted", function(c) EB.OnTurnStarted(c) end))
Ext.Events.Tick:Subscribe(function() local ok, err = pcall(EB.TickAugmentedHealth) if not ok then Log.Error("EpicBoons Tick: " .. tostring(err)) end end)
Ext.Osiris.RegisterListener("EnteredCombat", 2, "after", guard("EnteredCombat", function(object) EB.OnEnteredCombat(object) end))
Ext.Osiris.RegisterListener("LeveledUp", 1, "after", guard("LeveledUp", function(c) EB.Validate(c) end))

Apotheosis = Apotheosis or {}
Apotheosis.EpicBoons = EB
return EB
