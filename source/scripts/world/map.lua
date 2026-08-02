--- Grid map: two tile layers, collision, warps, NPCs and signs.
--- Layer 1 is terrain, layer 2 holds objects and buildings (index 0 = empty).

Map = {}
Map.__index = Map

Map.TILE = 32

function Map.new(w, h, fillName)
	local self = setmetatable({}, Map)
	self.w, self.h = w, h
	self.ground = {}
	self.object = {}
	self.warps = {}
	self.npcs = {}
	self.signs = {}
	self.name = ""
	local fill = Atlas.tile[fillName or "dust"]
	for i = 1, w * h do
		self.ground[i] = fill
		self.object[i] = 0
	end
	return self
end

function Map:index(x, y)
	return (y - 1) * self.w + x
end

function Map:inBounds(x, y)
	return x >= 1 and y >= 1 and x <= self.w and y <= self.h
end

function Map:setGround(x, y, tile)
	if self:inBounds(x, y) then self.ground[self:index(x, y)] = tile end
end

function Map:setObject(x, y, tile)
	if self:inBounds(x, y) then self.object[self:index(x, y)] = tile end
end

function Map:groundAt(x, y)
	if not self:inBounds(x, y) then return 0 end
	return self.ground[self:index(x, y)]
end

function Map:objectAt(x, y)
	if not self:inBounds(x, y) then return 0 end
	return self.object[self:index(x, y)]
end

function Map:isBlocked(x, y)
	if not self:inBounds(x, y) then return true end
	local i = self:index(x, y)
	if self.solidOverride and self.solidOverride[i] then return true end
	local obj = self.object[i]
	if obj ~= 0 and Atlas.solid[obj] then return true end
	return Atlas.solid[self.ground[i]] == true
end

function Map:isEncounterTile(x, y)
	if not self:inBounds(x, y) then return false end
	return Atlas.encounter[self.ground[self:index(x, y)]] == true
end

--- Places a multi-tile building. `doorWarp` is attached to its doorway tiles.
function Map:stamp(structName, ox, oy, doorWarp)
	local s = Atlas.structures[structName]
	assert(s, "unknown structure " .. tostring(structName))
	for ty = 0, s.h - 1 do
		for tx = 0, s.w - 1 do
			local idx = ty * s.w + tx + 1
			local tile = s.tiles[idx]
			if tile ~= 0 then
				self:setObject(ox + tx, oy + ty, tile)
			end
		end
	end
	for _, d in ipairs(s.doors) do
		local dx, dy = ox + d.x, oy + d.y
		self:setObject(dx, dy, 0)
		self:setGround(dx, dy, Atlas.tile.plate)
		if doorWarp then
			self:addWarp(dx, dy, doorWarp)
		end
	end
	return self
end

function Map:addWarp(x, y, warp)
	warp = Util.copy(warp)
	warp.x, warp.y = x, y
	self.warps[self:index(x, y)] = warp
end

function Map:warpAt(x, y)
	if not self:inBounds(x, y) then return nil end
	return self.warps[self:index(x, y)]
end

function Map:addSign(x, y, text)
	self:setObject(x, y, Atlas.tile.sign)
	self.signs[self:index(x, y)] = text
end

function Map:signAt(x, y)
	if not self:inBounds(x, y) then return nil end
	return self.signs[self:index(x, y)]
end

--- npc = { x, y, dir, sprite, lines = {...}, onTalk = fn, wander = bool }
function Map:addNpc(npc)
	npc.dir = npc.dir or "down"
	npc.sprite = npc.sprite or "colonist"
	npc.frame = 0
	self.npcs[#self.npcs + 1] = npc
	return npc
end

function Map:npcAt(x, y)
	for _, n in ipairs(self.npcs) do
		if n.x == x and n.y == y then return n end
	end
	return nil
end

function Map:isWalkable(x, y)
	return not self:isBlocked(x, y) and self:npcAt(x, y) == nil
end

--- Builds the two playdate tilemaps used for drawing. No-op off device.
function Map:buildTilemaps(imagetable)
	if not playdate then return end
	local gfx <const> = playdate.graphics
	self.groundMap = gfx.tilemap.new()
	self.groundMap:setImageTable(imagetable)
	self.groundMap:setSize(self.w, self.h)
	self.objectMap = gfx.tilemap.new()
	self.objectMap:setImageTable(imagetable)
	self.objectMap:setSize(self.w, self.h)
	for y = 1, self.h do
		for x = 1, self.w do
			local i = self:index(x, y)
			self.groundMap:setTileAtPosition(x, y, self.ground[i])
			self.objectMap:setTileAtPosition(x, y, self.object[i])
		end
	end
end

function Map:pixelWidth() return self.w * Map.TILE end
function Map:pixelHeight() return self.h * Map.TILE end

--- Nearest walkable tile to (x, y), searched in rings. Used by generators
--- and warps so the player can never be dropped inside geometry.
function Map:nearestOpen(x, y, maxRadius)
	maxRadius = maxRadius or 12
	if self:isWalkable(x, y) then return x, y end
	for r = 1, maxRadius do
		for dy = -r, r do
			for dx = -r, r do
				if math.abs(dx) == r or math.abs(dy) == r then
					local nx, ny = x + dx, y + dy
					if self:inBounds(nx, ny) and self:isWalkable(nx, ny) then
						return nx, ny
					end
				end
			end
		end
	end
	return x, y
end

--- Flood fill from (sx, sy); returns a reachability grid and the tile count.
function Map:reachable(sx, sy)
	local seen = {}
	local queue = { { sx, sy } }
	local head, count = 1, 0
	seen[self:index(sx, sy)] = true
	while head <= #queue do
		local cell = queue[head]
		head = head + 1
		count = count + 1
		local x, y = cell[1], cell[2]
		for _, d in pairs(Util.DIRS) do
			local nx, ny = x + d.x, y + d.y
			if self:inBounds(nx, ny) then
				local i = self:index(nx, ny)
				if not seen[i] and not self:isBlocked(nx, ny) then
					seen[i] = true
					queue[#queue + 1] = { nx, ny }
				end
			end
		end
	end
	return seen, count
end

--- Paints a map from an ASCII layout. `legend` maps chars to tile names;
--- upper-case entries in `objects` paint the object layer instead.
function Map.fromAscii(rows, legend, objects)
	local h = #rows
	local w = #rows[1]
	local map = Map.new(w, h, "dust")
	for y = 1, h do
		local row = rows[y]
		assert(#row == w, "ascii map row " .. y .. " is " .. #row .. " wide, expected " .. w)
		for x = 1, w do
			local ch = row:sub(x, x)
			local groundName = legend[ch]
			if groundName then
				map:setGround(x, y, Atlas.tile[groundName])
			end
			local objName = objects and objects[ch]
			if objName then
				map:setGround(x, y, Atlas.tile[objName.under or "dust"])
				map:setObject(x, y, Atlas.tile[objName.tile])
			end
		end
	end
	return map
end
