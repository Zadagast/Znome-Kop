--- Map loading and caching.
--- Map keys: "colony", "home", "neighbour", "lab", "sector:N".

World = {}

World.cache = {}

local function applyFlags(game, map, key)
	if map.caches then
		for index, cache in pairs(map.caches) do
			if game:flag(key .. ":cache:" .. index) then cache.taken = true end
		end
	end
	if map.anomaly and game:flag(key .. ":anomaly") then
		map.anomaly.cleared = true
	end
end

function World.build(game, key)
	if key == "colony" then
		return Colony.build(game)
	end
	local interior = Colony.interiors[key]
	if interior then return interior(game) end

	local index = tonumber(key:match("^sector:(%d+)$"))
	assert(index, "unknown map key " .. tostring(key))
	local sector = Sectors.get(index)
	local map, ex, ey = MapGen.generate(sector, game:seedFor(index))
	map.entryX, map.entryY = ex, ey
	map.key = key
	return map
end

function World.load(game, key)
	local map = World.cache[key]
	if not map then
		map = World.build(game, key)
		map.key = key
		World.cache[key] = map
	end
	applyFlags(game, map, key)
	return map
end

function World.forget(key)
	World.cache[key] = nil
end

function World.clear()
	World.cache = {}
end

--- Sector definition backing a map (colony interiors inherit sector 1).
function World.sectorFor(map)
	return Sectors.get(map.sector or 1)
end

--- Where the player should appear when a warp targets this map.
function World.spawnFor(game, key, warp)
	local map = World.load(game, key)
	if warp and warp.x and warp.to ~= "sector" then
		return map, warp.x, warp.y, warp.dir or "down"
	end
	if key:match("^sector:") then
		return map, map.entryX, map.entryY, "up"
	end
	if map.exitX then
		return map, map.exitX, map.exitY - 1, "up"
	end
	return map, math.floor(map.w / 2), math.floor(map.h / 2), "down"
end
