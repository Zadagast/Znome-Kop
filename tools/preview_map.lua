--- ASCII preview of a generated sector, for tuning generation offline.
---   lua5.4 tools/preview_map.lua [sectorIndex] [seed]

local root = (arg[0]:match("^(.*)tools[/\\][^/\\]*$") or "./")
dofile(root .. "tests/harness.lua")

local index = tonumber(arg[1] or "2")
local seed = tonumber(arg[2] or "12345")
local sector = Sectors.get(index)
local map, ex, ey = MapGen.generate(sector, seed)

local NAME = {}
for name, id in pairs(Atlas.tile) do NAME[id] = name end

local GLYPH = {
	rock = "#", cliff = "%", crater = "O", coolant = "~",
	sporegrass = '"', sporegrass_tall = "*", ash = ";",
	dust = ".", regolith = ",", gravel = ":", dunes = "-",
	plate = "=", grate = "+", tube = "'",
}

local poiAt = {}
for _, p in ipairs(map.pois) do poiAt[map:index(p.x, p.y)] = p.label:sub(1, 1) end

local seen = map:reachable(ex, ey)
print(string.format("%s  seed=%d  %dx%d  pois=%d", sector.name, seed, map.w, map.h, #map.pois))
for y = 1, map.h do
	local row = {}
	for x = 1, map.w do
		local i = map:index(x, y)
		local ch
		if x == ex and y == ey then
			ch = "@"
		elseif poiAt[i] then
			ch = poiAt[i]
		elseif map.object[i] ~= 0 then
			ch = Atlas.solid[map.object[i]] and "B" or "v"
		else
			ch = GLYPH[NAME[map.ground[i]]] or "?"
			if map:isBlocked(x, y) then
				ch = ch
			elseif not seen[i] then
				ch = "x" -- walkable but cut off from the entry
			end
		end
		row[#row + 1] = ch
	end
	print(table.concat(row))
end
