--- Procedural sector generation.
---
--- Hybrid of wave function collapse and structured placement, sized for the
--- Playdate's CPU budget:
---   1. points of interest are pre-collapsed onto a coarse macro grid
---      (one macro cell = 4x4 tiles), so layouts feel purposeful;
---   2. the rest of the macro grid is solved with entropy-ordered WFC using
---      an adjacency table (a few hundred cells, not tens of thousands);
---   3. a minimum spanning tree over the POIs plus a couple of extra loops
---      is carved as corridors, guaranteeing traversability;
---   4. macro cells expand into tiles, and a flood fill validates the result,
---      repairing anything the expansion happened to seal off.

MapGen = {}

MapGen.MACRO = 4

local OPEN, ROUGH, FIELD, WALL, HAZARD, SITE = 1, 2, 3, 4, 5, 6
MapGen.labels = { "OPEN", "ROUGH", "FIELD", "WALL", "HAZARD", "SITE" }

--- Adjacency: which labels may share an edge.
local COMPAT = {
	[OPEN]   = { [OPEN] = true, [ROUGH] = true, [FIELD] = true, [WALL] = true, [HAZARD] = true, [SITE] = true },
	[ROUGH]  = { [OPEN] = true, [ROUGH] = true, [FIELD] = true, [WALL] = true, [HAZARD] = true, [SITE] = true },
	[FIELD]  = { [OPEN] = true, [ROUGH] = true, [FIELD] = true },
	[WALL]   = { [OPEN] = true, [ROUGH] = true, [WALL] = true },
	[HAZARD] = { [OPEN] = true, [ROUGH] = true, [HAZARD] = true },
	[SITE]   = { [OPEN] = true, [ROUGH] = true, [SITE] = true },
}

local SOLID_LABEL = { [WALL] = true, [HAZARD] = true }

local function weights(openness)
	return {
		[OPEN] = 40 + openness * 90,
		[ROUGH] = 45,
		[FIELD] = 26 + openness * 18,
		[WALL] = 20 + (1 - openness) * 110,
		[HAZARD] = 10 + (1 - openness) * 20,
		[SITE] = 0, -- only ever pre-placed
	}
end

-- --- macro grid ----------------------------------------------------------

local Grid = {}
Grid.__index = Grid

local function newGrid(w, h)
	local g = setmetatable({ w = w, h = h, cell = {} }, Grid)
	for i = 1, w * h do
		g.cell[i] = { OPEN, ROUGH, FIELD, WALL, HAZARD }
	end
	return g
end

function Grid:index(x, y) return (y - 1) * self.w + x end
function Grid:inBounds(x, y) return x >= 1 and y >= 1 and x <= self.w and y <= self.h end

function Grid:collapsed(x, y)
	if not self:inBounds(x, y) then return nil end
	local c = self.cell[self:index(x, y)]
	return #c == 1 and c[1] or nil
end

function Grid:set(x, y, label)
	self.cell[self:index(x, y)] = { label }
end

local NEIGHBOURS = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }

--- Arc-consistency propagation from a queue of changed cells.
function Grid:propagate(queue)
	local head = 1
	while head <= #queue do
		local cell = queue[head]
		head = head + 1
		local x, y = cell[1], cell[2]
		local options = self.cell[self:index(x, y)]
		for _, d in ipairs(NEIGHBOURS) do
			local nx, ny = x + d[1], y + d[2]
			if self:inBounds(nx, ny) then
				local ni = self:index(nx, ny)
				local nOpts = self.cell[ni]
				local kept = {}
				for _, candidate in ipairs(nOpts) do
					local ok = false
					for _, current in ipairs(options) do
						if COMPAT[current][candidate] then ok = true break end
					end
					if ok then kept[#kept + 1] = candidate end
				end
				if #kept == 0 then return false end
				if #kept < #nOpts then
					self.cell[ni] = kept
					queue[#queue + 1] = { nx, ny }
				end
			end
		end
	end
	return true
end

function Grid:lowestEntropy(rng)
	local best, bestCount, ties = nil, 99, 0
	for y = 1, self.h do
		for x = 1, self.w do
			local n = #self.cell[self:index(x, y)]
			if n > 1 then
				if n < bestCount then
					best, bestCount, ties = { x, y }, n, 1
				elseif n == bestCount then
					ties = ties + 1
					if rng:int(ties) == 1 then best = { x, y } end
				end
			end
		end
	end
	return best
end

--- Number of already-collapsed orthogonal neighbours carrying `label`.
function Grid:neighbourCount(x, y, label)
	local n = 0
	for _, d in ipairs(NEIGHBOURS) do
		if self:collapsed(x + d[1], y + d[2]) == label then n = n + 1 end
	end
	return n
end

--- Affinity keeps like labels together, so regions read as coherent rock
--- ridges and grass fields instead of per-cell noise.
local AFFINITY = { [OPEN] = 0.5, [ROUGH] = 0.6, [FIELD] = 2.2, [WALL] = 2.6, [HAZARD] = 2.4, [SITE] = 0 }

function Grid:observe(x, y, rng, w)
	local options = self.cell[self:index(x, y)]
	local entries = {}
	for _, label in ipairs(options) do
		local weight = w[label]
		if weight > 0 then
			weight = weight * (1 + AFFINITY[label] * self:neighbourCount(x, y, label))
			entries[#entries + 1] = { value = label, weight = weight }
		end
	end
	if #entries == 0 then entries = { { value = options[1], weight = 1 } } end
	local chosen = rng:weighted(entries).value
	self:set(x, y, chosen)
	return chosen
end

-- --- POI placement -------------------------------------------------------

local POI_KINDS = { "cache", "outpost", "camp", "cache", "camp" }

local function placeSites(grid, rng, count, entry)
	local sites = {}
	local minGap = math.max(3, math.floor(math.min(grid.w, grid.h) / 3))
	local tries = 0
	while #sites < count and tries < 400 do
		tries = tries + 1
		local x = rng:range(2, grid.w - 1)
		local y = rng:range(2, grid.h - 1)
		local ok = Util.dist(x, y, entry[1], entry[2]) >= 3
		for _, s in ipairs(sites) do
			if Util.dist(x, y, s[1], s[2]) < minGap then ok = false break end
		end
		if ok then sites[#sites + 1] = { x, y } end
		if tries % 120 == 0 and minGap > 2 then minGap = minGap - 1 end
	end
	return sites
end

-- --- corridors -----------------------------------------------------------

--- Minimum spanning tree over the node list (Prim, O(n^2), n is tiny).
local function spanningTree(nodes)
	local edges = {}
	if #nodes < 2 then return edges end
	local inTree = { [1] = true }
	local remaining = #nodes - 1
	while remaining > 0 do
		local bestA, bestB, bestD = nil, nil, 1e9
		for a = 1, #nodes do
			if inTree[a] then
				for b = 1, #nodes do
					if not inTree[b] then
						local d = Util.dist(nodes[a][1], nodes[a][2], nodes[b][1], nodes[b][2])
						if d < bestD then bestA, bestB, bestD = a, b, d end
					end
				end
			end
		end
		inTree[bestB] = true
		edges[#edges + 1] = { bestA, bestB }
		remaining = remaining - 1
	end
	return edges
end

local function carve(grid, ax, ay, bx, by, rng)
	local x, y = ax, ay
	local horizontalFirst = rng:chance(0.5)
	local function open(cx, cy)
		if grid:inBounds(cx, cy) then
			local label = grid:collapsed(cx, cy)
			if label ~= SITE then grid:set(cx, cy, OPEN) end
		end
	end
	local function walkX()
		while x ~= bx do
			x = x + Util.sign(bx - x)
			open(x, y)
		end
	end
	local function walkY()
		while y ~= by do
			y = y + Util.sign(by - y)
			open(x, y)
		end
	end
	open(x, y)
	if horizontalFirst then walkX() walkY() else walkY() walkX() end
end

-- --- tile expansion ------------------------------------------------------

local function expand(map, grid, palette, rng)
	local M = MapGen.MACRO
	local tileFor = {
		[OPEN] = palette.ground,
		[ROUGH] = palette.rough,
		[FIELD] = palette.field,
		[WALL] = palette.wall,
		[HAZARD] = palette.hazard,
		[SITE] = palette.floor,
	}
	for gy = 1, grid.h do
		for gx = 1, grid.w do
			local label = grid:collapsed(gx, gy) or OPEN
			local name = tileFor[label]
			local tile = Atlas.tile[name]
			local edgeSoft = (label == WALL or label == HAZARD)
			for ty = 0, M - 1 do
				for tx = 0, M - 1 do
					local x = (gx - 1) * M + tx + 1
					local y = (gy - 1) * M + ty + 1
					local put = tile
					if edgeSoft then
						-- soften the border against open neighbours so blobs
						-- read as organic rock rather than square blocks
						local nx = (tx == 0 and -1) or (tx == M - 1 and 1) or 0
						local ny = (ty == 0 and -1) or (ty == M - 1 and 1) or 0
						if (nx ~= 0 or ny ~= 0) then
							local n = grid:collapsed(gx + nx, gy + ny)
							if n and not SOLID_LABEL[n] and rng:chance(0.45) then
								put = Atlas.tile[palette.rough]
							end
						end
					elseif label == OPEN and rng:chance(0.05) then
						put = Atlas.tile[palette.rough]
					end
					map:setGround(x, y, put)
				end
			end
		end
	end
end

local function scatter(map, grid, rng)
	local M = MapGen.MACRO
	for gy = 1, grid.h do
		for gx = 1, grid.w do
			local label = grid:collapsed(gx, gy)
			if label == ROUGH and rng:chance(0.35) then
				local x = (gx - 1) * M + rng:range(1, M)
				local y = (gy - 1) * M + rng:range(1, M)
				if map:inBounds(x, y) and not map:isBlocked(x, y) then
					map:setObject(x, y, Atlas.tile.boulder)
				end
			elseif label == OPEN and rng:chance(0.18) then
				local x = (gx - 1) * M + rng:range(1, M)
				local y = (gy - 1) * M + rng:range(1, M)
				if map:inBounds(x, y) and not map:isBlocked(x, y) then
					map:setObject(x, y, Atlas.tile.lichen)
				end
			end
		end
	end
end

--- Frames the map with solid rock so the player can never walk off the edge.
local function border(map, palette)
	for x = 1, map.w do
		map:setGround(x, 1, Atlas.tile[palette.wall])
		map:setGround(x, map.h, Atlas.tile[palette.wall])
	end
	for y = 1, map.h do
		map:setGround(1, y, Atlas.tile[palette.wall])
		map:setGround(map.w, y, Atlas.tile[palette.wall])
	end
end

local function macroCentre(gx, gy)
	local M = MapGen.MACRO
	return (gx - 1) * M + math.floor(M / 2), (gy - 1) * M + math.floor(M / 2)
end

--- Straight-line repair used when the flood fill finds an isolated POI.
local function forceCorridor(map, ax, ay, bx, by, palette)
	local x, y = ax, ay
	local floor = Atlas.tile[palette.ground]
	local function clear(cx, cy)
		if map:inBounds(cx, cy) then
			map:setGround(cx, cy, floor)
			map:setObject(cx, cy, 0)
		end
	end
	clear(x, y)
	while x ~= bx do
		x = x + Util.sign(bx - x)
		clear(x, y)
		clear(x, y + 1)
	end
	while y ~= by do
		y = y + Util.sign(by - y)
		clear(x, y)
		clear(x + 1, y)
	end
end

-- --- entry point ---------------------------------------------------------

--- Returns map, entryX, entryY. Deterministic for a given (sector, seed).
function MapGen.generate(sector, seed)
	local rng = RNG.new(seed)
	local M = MapGen.MACRO
	local w = sector.size.w - (sector.size.w % M)
	local h = sector.size.h - (sector.size.h % M)
	local gw, gh = w // M, h // M
	local palette = sector.palette
	local weightTable = weights(sector.openness or 0.5)

	local grid, sites
	for attempt = 1, 6 do
		grid = newGrid(gw, gh)
		local entryCell = { math.floor(gw / 2), gh - 1 }
		sites = placeSites(grid, rng, sector.poi or 5, entryCell)

		local queue = {}
		local ok = true
		grid:set(entryCell[1], entryCell[2], OPEN)
		queue[#queue + 1] = entryCell
		for _, s in ipairs(sites) do
			grid:set(s[1], s[2], SITE)
			queue[#queue + 1] = { s[1], s[2] }
		end
		ok = grid:propagate(queue)

		while ok do
			local cell = grid:lowestEntropy(rng)
			if not cell then break end
			grid:observe(cell[1], cell[2], rng, weightTable)
			ok = grid:propagate({ cell })
		end

		if ok then
			-- corridors: MST over entry + sites, plus a couple of loops
			local nodes = { entryCell }
			for _, s in ipairs(sites) do nodes[#nodes + 1] = s end
			for _, e in ipairs(spanningTree(nodes)) do
				local a, b = nodes[e[1]], nodes[e[2]]
				carve(grid, a[1], a[2], b[1], b[2], rng)
			end
			for _ = 1, math.max(1, #nodes // 3) do
				local a = rng:pick(nodes)
				local b = rng:pick(nodes)
				if a ~= b then carve(grid, a[1], a[2], b[1], b[2], rng) end
			end
			grid.entry = entryCell
			break
		end
	end

	-- any cell left uncollapsed after a failed attempt becomes open ground
	for y = 1, gh do
		for x = 1, gw do
			if not grid:collapsed(x, y) then grid:set(x, y, OPEN) end
		end
	end

	local map = Map.new(w, h, palette.ground)
	map.name = sector.name
	map.sector = sector.index
	map.seed = seed
	expand(map, grid, palette, rng)
	border(map, palette)
	scatter(map, grid, rng)

	local entryX, entryY = macroCentre(grid.entry[1], grid.entry[2])
	entryY = math.min(h - 2, entryY + 1)
	for y = entryY, h - 1 do
		map:setGround(entryX, y, Atlas.tile[palette.floor])
		map:setObject(entryX, y, 0)
	end
	entryX, entryY = map:nearestOpen(entryX, entryY)

	MapGen.placePois(map, grid, sites, sector, rng, entryX, entryY)

	-- validation: everything important must be reachable from the entry
	local seen = map:reachable(entryX, entryY)
	for _, poi in ipairs(map.pois) do
		if not seen[map:index(poi.x, poi.y)] then
			forceCorridor(map, entryX, entryY, poi.x, poi.y, palette)
			seen = map:reachable(entryX, entryY)
		end
	end
	-- Pockets the corridors never reached are filled in, so every walkable
	-- tile the player can see is a tile the player can actually stand on.
	seen = map:reachable(entryX, entryY)
	local wallTile = Atlas.tile[palette.wall]
	for y = 1, map.h do
		for x = 1, map.w do
			local i = map:index(x, y)
			if not seen[i] and not map:isBlocked(x, y) then
				map:setGround(x, y, wallTile)
				map:setObject(x, y, 0)
			end
		end
	end

	MapGen.ensureEncounterGround(map, palette, rng, entryX, entryY)

	map.reachableCount = select(2, map:reachable(entryX, entryY))
	return map, entryX, entryY
end

MapGen.MIN_ENCOUNTER_TILES = 60

--- Guarantees the sector has enough reachable encounter ground to hunt in.
--- Sealing off pockets can eat a sector's grass, so patches are seeded back
--- along reachable ground until the quota is met.
function MapGen.ensureEncounterGround(map, palette, rng, entryX, entryY)
	local seen = map:reachable(entryX, entryY)
	local open, count = {}, 0
	for y = 2, map.h - 1 do
		for x = 2, map.w - 1 do
			local i = map:index(x, y)
			if seen[i] then
				if map:isEncounterTile(x, y) then
					count = count + 1
				elseif map.object[i] == 0 and Util.dist(x, y, entryX, entryY) > 4 then
					open[#open + 1] = i
				end
			end
		end
	end
	local field = Atlas.tile[palette.field]
	local guard = 0
	while count < MapGen.MIN_ENCOUNTER_TILES and #open > 0 and guard < 400 do
		guard = guard + 1
		local pick = table.remove(open, rng:int(#open))
		local cx = ((pick - 1) % map.w) + 1
		local cy = ((pick - 1) // map.w) + 1
		for dy = -1, 1 do
			for dx = -1, 1 do
				local x, y = cx + dx, cy + dy
				if map:inBounds(x, y) and seen[map:index(x, y)]
					and not map:isEncounterTile(x, y)
					and map.object[map:index(x, y)] == 0 then
					map:setGround(x, y, field)
					count = count + 1
				end
			end
		end
	end
	map.encounterTiles = count
	return count
end

--- Turns collapsed SITE cells into playable content.
function MapGen.placePois(map, grid, sites, sector, rng, entryX, entryY)
	map.pois = {}
	local ordered = {}
	for _, s in ipairs(sites) do
		local x, y = macroCentre(s[1], s[2])
		x, y = map:nearestOpen(x, y)
		ordered[#ordered + 1] = { x = x, y = y, d = Util.dist(x, y, entryX, entryY) }
	end
	table.sort(ordered, function(a, b) return a.d > b.d end)

	for i, p in ipairs(ordered) do
		local kind
		if i == 1 then
			kind = "relay" -- farthest site is always the way onward
		elseif i == 2 and sector.index >= 3 then
			kind = "anomaly"
		else
			kind = POI_KINDS[((i + sector.index) % #POI_KINDS) + 1]
		end
		MapGen.buildPoi(map, p.x, p.y, kind, sector, rng)
	end
end

function MapGen.buildPoi(map, x, y, kind, sector, rng)
	local poi = { x = x, y = y, kind = kind }
	if kind == "relay" then
		local sx = Util.clamp(x - 1, 2, map.w - 3)
		local sy = Util.clamp(y - 3, 2, map.h - 4)
		map:stamp("tower", sx, sy)
		map:setObject(x, y, 0)
		map:setGround(x, y, Atlas.tile.plate)
		map:addWarp(x, y, { to = "sector", sector = sector.index + 1, dir = "up" })
		map:setObject(x - 1, y, Atlas.tile.marker)
		poi.label = "RELAY"
	elseif kind == "outpost" then
		local sx = Util.clamp(x - 1, 2, map.w - 5)
		local sy = Util.clamp(y - 2, 2, map.h - 4)
		map:stamp("hab", sx, sy)
		local door = map:nearestOpen(x, y)
		map:addNpc({
			x = door, y = Util.clamp(y + 1, 2, map.h - 1), dir = "down", sprite = "tech",
			onTalk = function()
				return { lines = { "Field station online.\nSquad patched up." }, action = "heal" }
			end,
		})
		poi.label = "OUTPOST"
	elseif kind == "cache" then
		local loot = rng:weighted({
			{ value = "pod", weight = 40 },
			{ value = "repair", weight = 30 },
			{ value = "podmk2", weight = 15 },
			{ value = "repair2", weight = 10 },
			{ value = "purge", weight = 5 },
		}).value
		local qty = (loot == "pod") and rng:range(2, 4) or 1
		map:setObject(x, y, Atlas.tile.crate)
		map.caches = map.caches or {}
		map.caches[map:index(x, y)] = { item = loot, qty = qty, taken = false }
		poi.label = "CACHE"
	elseif kind == "anomaly" then
		for dy = -1, 1 do
			for dx = -1, 1 do
				if map:inBounds(x + dx, y + dy) and not map:isBlocked(x + dx, y + dy) then
					map:setGround(x + dx, y + dy, Atlas.tile[sector.palette.field])
				end
			end
		end
		map:setObject(x, y, Atlas.tile.vent)
		map.anomaly = { x = x, y = y, cleared = false, sector = sector.index }
		poi.label = "ANOMALY"
	elseif kind == "camp" then
		map:stamp("solar", Util.clamp(x - 1, 2, map.w - 3), Util.clamp(y - 1, 2, map.h - 3))
		map:setObject(x, y, 0)
		map:addSign(Util.clamp(x + 1, 2, map.w - 1), y,
			sector.name .. "\nSurvey marker " .. rng:range(10, 99) .. ".")
		poi.label = "CAMP"
	end
	map.pois[#map.pois + 1] = poi
	return poi
end
