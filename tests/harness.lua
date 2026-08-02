--- Headless harness: loads the game's pure Lua modules under plain lua5.4 by
--- stubbing the handful of Playdate globals they touch.
--- Run with: lua5.4 tests/run.lua

local root = (arg and arg[0] or ""):match("^(.*)tests[/\\][^/\\]*$") or "./"

-- The game modules use `import`; map it onto dofile with the source root.
function import(path)
	local file = root .. "source/" .. path
	if not file:match("%.lua$") then file = file .. ".lua" end
	local chunk, err = loadfile(file)
	if not chunk then
		if path:match("^CoreLibs") then return end -- SDK libraries: nothing to load
		error(err)
	end
	return chunk()
end

-- Nothing in the tested modules draws, so `playdate` stays nil and the
-- rendering guards (`if not playdate then return end`) take over.
playdate = nil

local function load(path)
	local chunk, err = loadfile(root .. "source/scripts/" .. path .. ".lua")
	assert(chunk, err)
	chunk()
end

load("core/util")
load("core/rng")
load("data/types")
load("data/moves")
load("data/species")
load("data/items")
load("data/sectors")
load("world/atlas")
load("world/map")
load("world/mapgen")
load("game/creature")
load("game/battle")

local T = {}
T.root = root
T.failures = 0
T.checks = 0

function T.check(condition, message)
	T.checks = T.checks + 1
	if not condition then
		T.failures = T.failures + 1
		print("  FAIL: " .. message)
	end
	return condition
end

function T.eq(a, b, message)
	return T.check(a == b, string.format("%s (got %s, want %s)", message, tostring(a), tostring(b)))
end

function T.group(name, fn)
	print(name)
	fn(T)
end

function T.finish()
	print(string.format("\n%d checks, %d failures", T.checks, T.failures))
	os.exit(T.failures == 0 and 0 or 1)
end

return T
