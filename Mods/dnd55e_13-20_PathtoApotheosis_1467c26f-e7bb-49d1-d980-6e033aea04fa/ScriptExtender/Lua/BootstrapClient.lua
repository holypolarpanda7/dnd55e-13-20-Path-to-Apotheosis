-- =====================================================================
-- Path to Apotheosis - Client bootstrap (Script Extender)
-- Client-side features only: anything that has to act on the player's own UI or static data copy.
-- Logging matches BootstrapServer.lua (tag [Apotheosis]).
-- =====================================================================
local TAG = "[Apotheosis]"
Apotheosis = Apotheosis or {}
Apotheosis.DEBUG = Apotheosis.DEBUG or false

local Log = {}
function Log.Info(...)  Ext.Utils.Print(TAG, "[client]", ...) end
function Log.Warn(...)  Ext.Utils.PrintWarning(TAG, "[client]", ...) end
function Log.Error(...) Ext.Utils.PrintError(TAG, "[client]", ...) end
function Log.Debug(...) if Apotheosis.DEBUG then Ext.Utils.Print(TAG, "[client] [dbg]", ...) end end
Apotheosis.Log = Log

Log.Info("BootstrapClient.lua loading - client context")

Ext.Require("MCMSettings.lua")
Ext.Require("EpicBoonFeatLock.lua")
