-- =====================================================================
-- Apotheosis functional feature tests.
--
-- Goes beyond "was the passive granted": performs character actions
-- (force-casts spells, provokes attacks), spawns targets with the
-- faction each scenario actually requires, and verifies observable
-- effects (statuses, scripted reactions).
--
-- TARGET DOCTRINE - each test declares the target its mechanic needs:
--   * FrozenHaunt gates on `Enemy(context.Target)` in its stats functor,
--     so its target MUST be hostile - a friendly target can never chill.
--   * AlterMemories marks enemies inside a 6m aura and locks them with
--     MM_HOLD (paralyze-type) / MM_SLOW, so it needs TWO hostile LIVING
--     creatures (undead can resist paralysis-type statuses).
--   * ElementalRebuke's AttackedBy listener is faction-agnostic, but the
--     real scenario is an enemy striking the sorcerer, so the default
--     attacker is hostile; pass an ally GUID to test without combat.
--   * Self-buff / self-scripted features need no target at all.
--
-- All template + faction GUIDs below were extracted from base-game data
-- (summon spell stats and Shared/Factions/Factions.lsx), not guessed.
--
-- Loaded by BootstrapServer.lua; exposed as _G.ApotheosisFeatureTests.
--
-- Console entry points (registered in BootstrapServer.lua):
--   !apofeatures                     -- list registered tests
--   !apofeature <PassiveName> [tgt]  -- run one test (optional target GUID)
--   !apospawn <template> [faction]   -- spawn a manual-test target, e.g.
--                                       !apospawn wolf hostile
--
-- Outcome log markers (stable, parsed by Scripts/test_subclass.sh):
--   FeatureTest <passive>: PASS
--   FeatureTest <passive>: FAILED <reason>
--   FeatureTest <passive>: SKIP (manual) <instructions>
-- =====================================================================

local FT = {
    Config = {
        -- Root templates proven spawnable (sourced from summon spells).
        Templates = {
            wolf     = "9beee5c9-279e-49d8-a4a8-18f9ee0b1519", -- living beast, melee
            boar     = "be71d66c-5328-490f-b962-4fdb7ca2647f", -- living beast, melee
            bear     = "ca66e982-91f6-4b60-8ebc-d4c4f2568f0c", -- living beast, tanky
            skeleton = "6c06cda2-6e13-4663-a6f6-c4bb7564c10f", -- undead (paralysis-resistant targets)
            zombie   = "c2a2c269-ede8-4887-99f1-e0c044cc0c75", -- undead melee
        },
        -- Base factions from Shared/Factions/Factions.lsx.
        Factions = {
            hostile  = "64321d50-d516-b1b2-cfac-2eb773de1ff6", -- Evil NPC
            friendly = "80182081-6bb1-95f1-c40f-4c3cea368269", -- Good NPC
            neutral  = "a66b2d45-1b6c-082d-8a01-c6d975ead314", -- Neutral
        },
        StatusPollMs = 400,
        StatusTimeoutMs = 8000,
        AuraTimeoutMs = 15000,      -- aura ticks need longer than direct hits
        CastSettleMs = 1500,
        SpawnSettleMs = 700,
    },
    tests = {},
}

local function log()
    if Apotheosis and Apotheosis.Log then
        return Apotheosis.Log
    end
    local TAG = "[Apotheosis]"
    return {
        Info = function(...) Ext.Utils.Print(TAG, ...) end,
        Warn = function(...) Ext.Utils.PrintWarning(TAG, ...) end,
        Error = function(...) Ext.Utils.PrintError(TAG, ...) end,
        Debug = function(...) end,
    }
end

-- ---------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------

function FT.GetHost()
    local host = Osi.GetHostCharacter and Osi.GetHostCharacter() or nil
    if not host or host == "" then
        error("No host character available")
    end
    return host
end

--- First party member that is not `host`, or nil.
function FT.GetAlly(host)
    local players = Osi.DB_Players and Osi.DB_Players:Get(nil) or nil
    if not players then return nil end
    local hostTail = tostring(host):sub(-36)
    for _, row in pairs(players) do
        local member = row[1]
        if member and Osi.IsDead(member) ~= 1 then
            if tostring(member):sub(-36) ~= hostTail then
                return member
            end
        end
    end
    return nil
end

--- Spawn `templateKey` near host with `factionKey`. cb(guid or nil, err).
function FT.SpawnCreature(host, templateKey, factionKey, dx, dz, cb)
    local L = log()
    local template = FT.Config.Templates[templateKey]
    if not template then
        cb(nil, "unknown template key '" .. tostring(templateKey) .. "'")
        return
    end
    local x, y, z = Osi.GetPosition(host)
    if not x then
        cb(nil, "could not resolve host position")
        return
    end
    local guid = Osi.CreateAt(template, x + (dx or 3), y, z + (dz or 3), 0, 0, "")
    if not guid or guid == "" then
        cb(nil, "CreateAt returned nothing for " .. templateKey .. " (" .. template .. ")")
        return
    end
    local faction = FT.Config.Factions[factionKey or "neutral"]
    if faction and Osi.SetFaction then
        pcall(Osi.SetFaction, guid, faction)
    end
    L.Debug("Spawned " .. templateKey .. " as " .. tostring(factionKey) .. ": " .. tostring(guid))
    -- let the entity finish materializing before it is acted upon
    Ext.Timer.WaitFor(FT.Config.SpawnSettleMs, function()
        cb(guid, nil)
    end)
end

function FT.RemoveSpawned(guid)
    if guid and Osi.RequestDelete then
        pcall(Osi.RequestDelete, guid)
    end
end

--- Poll until `target` has `status` (cb(true)) or timeout (cb(false)).
function FT.ExpectStatus(target, status, timeoutMs, cb)
    local deadline = Ext.Utils.MonotonicTime() + (timeoutMs or FT.Config.StatusTimeoutMs)
    local function poll()
        if Osi.HasActiveStatus(target, status) == 1 then
            cb(true)
            return
        end
        if Ext.Utils.MonotonicTime() >= deadline then
            cb(false)
            return
        end
        Ext.Timer.WaitFor(FT.Config.StatusPollMs, poll)
    end
    poll()
end

--- Poll until `target` has ANY of the listed statuses. cb(found, which).
function FT.ExpectAnyStatus(target, statuses, timeoutMs, cb)
    local deadline = Ext.Utils.MonotonicTime() + (timeoutMs or FT.Config.StatusTimeoutMs)
    local function poll()
        for _, s in ipairs(statuses) do
            if Osi.HasActiveStatus(target, s) == 1 then
                cb(true, s)
                return
            end
        end
        if Ext.Utils.MonotonicTime() >= deadline then
            cb(false, nil)
            return
        end
        Ext.Timer.WaitFor(FT.Config.StatusPollMs, poll)
    end
    poll()
end

--- Force-cast `spell` from `caster` at `target` (works even if the caster
--- doesn't own the spell), then wait CastSettleMs before `cb`.
function FT.UseSpellOn(caster, spell, target, cb)
    Osi.UseSpell(caster, spell, target)
    Ext.Timer.WaitFor(FT.Config.CastSettleMs, cb)
end

-- ---------------------------------------------------------------------
-- Registry / runner
-- ---------------------------------------------------------------------

--- Register a functional test for a passive.
--- spec = {
---   mode   = "auto" | "manual",
---   target = "none"                      -- self-contained
---          | "ally"                      -- party ally (spawned friendly wolf as fallback)
---          | { role = "enemy",  template = "wolf", count = 1 [, hp = N] }  (hp: extra max HP so the target survives)
---          | { role = "enemy",  template = "wolf", count = 2 },
---   note   = string,                     -- scenario description / manual steps
---   run    = function(ctx, finish) end,  -- ctx = { host, target, targets }
--- }
function FT.Register(passive, spec)
    FT.tests[passive] = spec
end

local function describeTarget(t)
    if t == nil or t == "none" then return "self" end
    if t == "ally" then return "friendly ally" end
    if type(t) == "table" then
        return (t.count or 1) .. "x hostile " .. (t.template or "wolf")
    end
    return tostring(t)
end

function FT.List()
    local L = log()
    local names = {}
    for k in pairs(FT.tests) do names[#names + 1] = k end
    table.sort(names)
    L.Info("Registered feature tests (" .. tostring(#names) .. "):")
    for _, n in ipairs(names) do
        local t = FT.tests[n]
        L.Info("  " .. n .. " [" .. t.mode .. ", target: " .. describeTarget(t.target) .. "]")
        if t.note then
            L.Info("      " .. t.note)
        end
    end
end

--- Resolve spec.target into ctx.targets, spawning as needed. cb(ok, err).
local function resolveTargets(spec, ctx, explicitTarget, cb)
    local t = spec.target
    if t == nil or t == "none" then
        cb(true)
        return
    end

    if explicitTarget then
        ctx.target = explicitTarget
        ctx.targets = { explicitTarget }
        cb(true)
        return
    end

    if t == "ally" then
        local ally = FT.GetAlly(ctx.host)
        if ally then
            ctx.target = ally
            ctx.targets = { ally }
            cb(true)
            return
        end
        FT.SpawnCreature(ctx.host, "wolf", "friendly", 2, 2, function(guid, why)
            if not guid then
                cb(false, "no party ally and spawn failed: " .. tostring(why))
                return
            end
            ctx.spawned[#ctx.spawned + 1] = guid
            ctx.target = guid
            ctx.targets = { guid }
            cb(true)
        end)
        return
    end

    if type(t) == "table" and t.role == "enemy" then
        local count = t.count or 1
        local template = t.template or "wolf"
        ctx.targets = {}
        local function spawnNext(i)
            if i > count then
                ctx.target = ctx.targets[1]
                cb(true)
                return
            end
            FT.SpawnCreature(ctx.host, template, "hostile", 2 + i, 2, function(guid, why)
                if not guid then
                    cb(false, "enemy spawn " .. i .. "/" .. count .. " failed: " .. tostring(why))
                    return
                end
                ctx.spawned[#ctx.spawned + 1] = guid
                ctx.targets[#ctx.targets + 1] = guid
                if t.hp then
                    -- tougher target (a level 15+ cantrip kills a 15 HP wolf outright, and a dead target never gets the
                    -- status under test): raise max HP, then fill it a moment later once the boost has applied
                    Osi.AddBoosts(guid, "IncreaseMaxHP(" .. tostring(t.hp) .. ")", "FeatureTest", guid)
                    Ext.Timer.WaitFor(300, function()
                        Osi.SetHitpointsPercentage(guid, 100)
                        spawnNext(i + 1)
                    end)
                    return
                end
                spawnNext(i + 1)
            end)
        end
        spawnNext(1)
        return
    end

    cb(false, "unsupported target spec")
end

--- Run the test registered for `passive`. explicitTarget (optional GUID)
--- overrides target resolution. onDone(ok|nil) is optional.
function FT.Run(passive, explicitTarget, onDone)
    local L = log()
    local finishothers = onDone or function() end

    local test = FT.tests[passive]
    if not test then
        L.Warn("FeatureTest " .. passive .. ": SKIP (no test registered)")
        finishothers(nil)
        return
    end

    local ok, err = pcall(function()
        local host = FT.GetHost()

        if Osi.HasPassive(host, passive) ~= 1 then
            L.Error("FeatureTest " .. passive .. ": FAILED host does not have the passive (precondition)")
            finishothers(false)
            return
        end

        if test.mode == "manual" then
            L.Warn("FeatureTest " .. passive .. ": SKIP (manual) " .. tostring(test.note or ""))
            finishothers(nil)
            return
        end

        local ctx = { host = host, target = nil, targets = {}, spawned = {} }

        local function finish(passOk, reason)
            for _, guid in ipairs(ctx.spawned) do
                FT.RemoveSpawned(guid)
            end
            if passOk then
                L.Info("FeatureTest " .. passive .. ": PASS")
            else
                L.Error("FeatureTest " .. passive .. ": FAILED " .. tostring(reason or "unknown"))
            end
            finishothers(passOk)
        end

        resolveTargets(test, ctx, explicitTarget, function(resolved, why)
            if not resolved then
                L.Error("FeatureTest " .. passive .. ": FAILED target setup: " .. tostring(why))
                finishothers(false)
                return
            end
            test.run(ctx, finish)
        end)
    end)

    if not ok then
        L.Error("FeatureTest " .. passive .. ": FAILED runtime error: " .. tostring(err))
        finishothers(false)
    end
end

--- Run tests for every passive in `passives` (sequentially).
function FT.RunForPassives(character, passives)
    local queue = {}
    for _, p in ipairs(passives or {}) do
        if FT.tests[p] then
            queue[#queue + 1] = p
        end
    end
    if #queue == 0 then return end

    local L = log()
    L.Info("FeatureTests: running " .. tostring(#queue) .. " test(s): " .. table.concat(queue, ", "))
    local i = 0
    local function nextTest()
        i = i + 1
        if i > #queue then
            L.Info("FeatureTests: batch complete")
            return
        end
        FT.Run(queue[i], nil, function() nextTest() end)
    end
    nextTest()
end

-- ---------------------------------------------------------------------
-- Built-in tests
-- ---------------------------------------------------------------------

-- Winter Walker L15.
-- Functor: Conditions "IsDamageTypeCold(context.Target) and Enemy(context.Target)"
-- => the target MUST be hostile; a friendly can never be chilled by this.
-- Living beast chosen so the status side is unambiguous.
FT.Register("WinterWalker_15_FrozenHaunt", {
    mode = "auto",
    target = { role = "enemy", template = "wolf", count = 1, hp = 300 },   -- survives a level 15-20 Ray of Frost
    note = "Ray of Frost at a HOSTILE living target must apply CHILLED (Enemy() gate in the functor)",
    run = function(ctx, finish)
        FT.UseSpellOn(ctx.host, "Projectile_RayOfFrost", ctx.target, function()
            FT.ExpectStatus(ctx.target, "CHILLED", nil, function(found)
                finish(found, found and nil or "hostile target never gained CHILLED after cold damage")
            end)
        end)
    end,
})

-- Noble Genies L15.
-- The AttackedBy listener is faction-agnostic, but the real scenario is an
-- enemy striking the sorcerer, so the default attacker is a hostile wolf.
-- To test without starting combat: !apofeature NobleGenies_15_ElementalRebuke <allyGuid>
FT.Register("NobleGenies_15_ElementalRebuke", {
    mode = "auto",
    target = { role = "enemy", template = "wolf", count = 1 },
    note = "hostile attacker Fire Bolts the host; the attacker must gain ELEMENTAL_REBUKE_HIT lash-back",
    run = function(ctx, finish)
        FT.UseSpellOn(ctx.target, "Projectile_FireBolt", ctx.host, function()
            FT.ExpectStatus(ctx.target, "ELEMENTAL_REBUKE_HIT", nil, function(found)
                finish(found, found and nil or "attacker never gained ELEMENTAL_REBUKE_HIT")
            end)
        end)
    end,
})

-- Enchanter L14 (Alter Memories).
-- The Modify Memory aura tags ENEMIES within 6m; actives get MM_HOLD
-- (paralyze-type) or MM_SLOW. With the L14 passive the FIFO cap is 2, so
-- two LIVING hostile targets must BOTH end up locked down (undead would
-- resist the paralyze branch and corrupt the result).
FT.Register("Enchanter_14_AlterMemories", {
    mode = "auto",
    target = { role = "enemy", template = "wolf", count = 2 },
    note = "cast Modify Memory aura with 2 hostile living targets in range; both must gain MM_HOLD or MM_SLOW (cap=2)",
    run = function(ctx, finish)
        FT.UseSpellOn(ctx.host, "Shout_Apotheosis_ModifyMemory", ctx.host, function()
            local first, second = ctx.targets[1], ctx.targets[2]
            FT.ExpectAnyStatus(first, { "MM_HOLD", "MM_SLOW" }, FT.Config.AuraTimeoutMs, function(ok1)
                if not ok1 then
                    finish(false, "first victim never gained MM_HOLD/MM_SLOW")
                    return
                end
                FT.ExpectAnyStatus(second, { "MM_HOLD", "MM_SLOW" }, FT.Config.AuraTimeoutMs, function(ok2)
                    finish(ok2, ok2 and nil
                        or "second victim never locked down - L14 cap=2 not honored (cap=1 behavior?)")
                end)
            end)
        end)
    end,
})

-- Diviner L14: self-scripted; no target needed.
FT.Register("Diviner_14_GreaterPortent", {
    mode = "auto",
    target = "none",
    note = "GrantExtraPortentDie must apply a PORTENT_<n> status to the diviner",
    run = function(ctx, finish)
        local grant = Apotheosis and Apotheosis.Features and Apotheosis.Features.GrantExtraPortentDie
        if not grant then
            finish(false, "Apotheosis.Features.GrantExtraPortentDie not exposed")
            return
        end
        grant(ctx.host)
        local portents = {}
        for v = 1, 20 do portents[#portents + 1] = "PORTENT_" .. v end
        FT.ExpectAnyStatus(ctx.host, portents, 5000, function(found)
            finish(found, found and nil or "no PORTENT_<n> status appeared after grant")
        end)
    end,
})

-- Archfey L14: self status hook; no target needed.
FT.Register("Archfey_14_BewitchingMagic", {
    mode = "auto",
    target = "none",
    note = "applying BEWITCHING_MAGIC to self must stick (scripted charisma-scaled boost hook)",
    run = function(ctx, finish)
        Osi.ApplyStatus(ctx.host, "BEWITCHING_MAGIC", 12.0, 1, ctx.host)
        FT.ExpectStatus(ctx.host, "BEWITCHING_MAGIC", 4000, function(found)
            finish(found, found and nil or "BEWITCHING_MAGIC did not apply")
        end)
    end,
})

-- Scion of the Three L13: static self boosts; no target needed.
FT.Register("DeadThree_UnholyInfiltration", {
    mode = "auto",
    target = "none",
    note = "static boosts (Stealth/Deception advantage, 18m darkvision); presence is the observable",
    run = function(ctx, finish)
        finish(true)
    end,
})

-- Barbarian L15: self only. Checks both halves of Persistent Rage: the
-- permanent RAGE_STOP_REMOVE marker, and the scripted Initiative refill
-- (spend one Rage use, call the feature, expect full Rage + the marker).
FT.Register("Barbarian_PersistentRage", {
    mode = "auto",
    target = "none",
    note = "RAGE_STOP_REMOVE must be present; after spending 1 Rage, TryPersistentRage must refill to max and set APO_PERSISTENT_RAGE_USED",
    run = function(ctx, finish)
        local F = Apotheosis and Apotheosis.Features
        if not (F and F.TryPersistentRage and F.GetRageUses) then
            finish(false, "Apotheosis.Features.TryPersistentRage not exposed")
            return
        end
        FT.ExpectStatus(ctx.host, "RAGE_STOP_REMOVE", 3000, function(found)
            if not found then
                finish(false, "RAGE_STOP_REMOVE missing - Rage would still end unless extended")
                return
            end
            Osi.RemoveStatus(ctx.host, "APO_PERSISTENT_RAGE_USED")
            local amount, max = F.GetRageUses(ctx.host)
            if not amount or max < 1 then
                finish(false, "host has no Rage resource")
                return
            end
            local entity = Ext.Entity.Get(ctx.host)
            entity.ActionResources.Resources[F.GetRageResourceUUID()][1].Amount = max - 1
            entity:Replicate("ActionResources")
            local refilled, why = F.TryPersistentRage(ctx.host)
            if not refilled then
                finish(false, "TryPersistentRage did not refill: " .. tostring(why))
                return
            end
            FT.ExpectStatus(ctx.host, "APO_PERSISTENT_RAGE_USED", 3000, function(marked)
                local now = F.GetRageUses(ctx.host)
                finish(marked and now == max, string.format("used-marker=%s rage=%s/%s", tostring(marked), tostring(now), tostring(max)))
            end)
        end)
    end,
})

-- Manual-only entries: reaction prompts / UI flows that can't be safely
-- automated. Each names the target to stage with !apospawn.
FT.Register("Berserker_10_Retaliation", {
    mode = "manual",
    target = "none",
    note = "stage: !apospawn wolf hostile - let it MELEE-hit the barbarian in combat; expect the Retaliation reaction prompt (dnd55e interrupt)",
})
FT.Register("Druid_BeastSpells", {
    mode = "manual",
    target = "none",
    note = "self only: enter Wild Shape at L18+; expect curated support spells + temp slots; revert must remove them",
})
FT.Register("Celestial_14_SearingVengeance", {
    mode = "manual",
    target = "none",
    note = "stage: !apospawn bear hostile - let it down the warlock; expect the scripted half-HP revive (SEARING_VENGEANCE_DOWNED)",
})

_G.ApotheosisFeatureTests = FT
return FT
