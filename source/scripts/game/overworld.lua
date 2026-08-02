--- Overworld scene: grid movement, encounters, interaction and warps.

import "CoreLibs/graphics"

local gfx <const> = playdate.graphics
local TILE <const> = 32
local STEP_PX <const> = 4 -- 8 frames per tile at 30 fps

Overworld = {}
Overworld.__index = Overworld

function Overworld.new(game)
	local self = setmetatable({}, Overworld)
	self.game = game
	self.moving = false
	self.offset = 0
	self.step = 0
	self.stepCount = 0
	self.dialog = nil
	self.dialogIndex = 1
	self.pending = nil
	self.bannerTimer = 0
	self.scanner = false
	self:enter(game.mapKey, game.x, game.y, game.dir)
	return self
end

function Overworld:enter(key, x, y, dir)
	local game = self.game
	self.map = World.load(game, key)
	self.map:buildTilemaps(Assets.tiles)
	game.mapKey = key
	game.x, game.y, game.dir = x, y, dir or "down"
	self.moving = false
	self.offset = 0
	self.bannerTimer = 60
	self.banner = self.map.name
end

function Overworld:sector()
	return World.sectorFor(self.map)
end

-- --- helpers -------------------------------------------------------------

function Overworld:facingTile()
	local d = Util.DIRS[self.game.dir]
	return self.game.x + d.x, self.game.y + d.y
end

function Overworld:say(lines, after)
	self.dialog = type(lines) == "table" and lines or { lines }
	self.dialogIndex = 1
	self.dialogAfter = after
end

function Overworld:closeDialog()
	local after = self.dialogAfter
	self.dialog = nil
	self.dialogAfter = nil
	if after then after() end
end

-- --- interaction ---------------------------------------------------------

function Overworld:interact()
	local fx, fy = self:facingTile()
	local game = self.game

	local npc = self.map:npcAt(fx, fy)
	if npc then
		npc.dir = Util.DIRS[game.dir] and ({ up = "down", down = "up", left = "right", right = "left" })[game.dir]
		local result = npc.onTalk and npc.onTalk(game) or { lines = npc.lines or { "..." } }
		self:say(result.lines, function()
			self:runAction(result.action)
		end)
		return
	end

	local sign = self.map:signAt(fx, fy)
	if sign then
		self:say(UI.wrap(sign, 340))
		return
	end

	local index = self.map:index(fx, fy)
	local cache = self.map.caches and self.map.caches[index]
	if cache and not cache.taken then
		cache.taken = true
		game:setFlag(self.map.key .. ":cache:" .. index, true)
		game:addItem(cache.item, cache.qty)
		self.map:setObject(fx, fy, 0)
		self.map:buildTilemaps(Assets.tiles)
		local item = Items.get(cache.item)
		self:say({ "Cracked a supply cache.", "Got " .. item.name .. " x" .. cache.qty .. "." })
		return
	end

	local warp = self.map:warpAt(fx, fy)
	if warp and warp.to == "sector" then
		self:useWarp(warp)
		return
	end

	self:say({ "Nothing but dust here." })
end

function Overworld:runAction(action)
	if action == "heal" or action == "rest" then
		self.game:healParty()
		Save.write(self.game)
		self:say({ "Squad restored.", action == "rest" and "Progress saved." or "Repair bay complete." })
	elseif action == "starter" then
		self.pending = "starter"
	end
end

-- --- warps and encounters -------------------------------------------------

function Overworld:useWarp(warp)
	local game = self.game
	if warp.to == "sector" then
		local index = warp.sector
		if index > Sectors.count() then
			self:say({ "The relay is dead.", "Nothing further out there." })
			return
		end
		if #game.party == 0 then
			self:say({ "No Znome, no airlock.", "See the Doc first." })
			return
		end
		game:unlock(index)
		game.sector = index
		local key = "sector:" .. index
		local map, x, y, dir = World.spawnFor(game, key, warp)
		self.transition = { timer = 8, key = key, x = x, y = y, dir = dir }
		return
	end
	local key = warp.to
	local map, x, y, dir = World.spawnFor(game, key, warp)
	self.transition = { timer = 8, key = key, x = x, y = y, dir = dir }
end

function Overworld:rollEncounter()
	local game = self.game
	if #game.party == 0 or not game:partyAlive() then return end
	if not self.map:isEncounterTile(game.x, game.y) then return end
	local sector = self:sector()
	if not game.rng:chance(sector.rate) then return end
	self:startWildBattle(sector)
end

function Overworld:startWildBattle(sector, forced)
	local game = self.game
	local speciesId = forced and forced.species or game.rng:weighted(sector.encounters).value
	local lo, hi = sector.levels[1], sector.levels[2]
	local level = forced and forced.level or game.rng:range(lo, hi)
	local foe = Creature.new(speciesId, level, game.rng)
	game:logSeen(speciesId)
	Scenes.push(BattleScene.new(game, foe, { sector = sector, boss = forced ~= nil }))
end

function Overworld:checkAnomaly()
	local a = self.map.anomaly
	if not a or a.cleared then return end
	if Util.dist(self.game.x, self.game.y, a.x, a.y) > 1 then return end
	a.cleared = true
	self.game:setFlag(self.map.key .. ":anomaly", true)
	local sector = self:sector()
	local boss = {
		species = sector.encounters[1].value,
		level = sector.levels[2] + 3,
	}
	self:say({ "Anomaly signal spikes!", "Something big is awake." }, function()
		self:startWildBattle(sector, boss)
	end)
end

-- --- movement -------------------------------------------------------------

function Overworld:tryMove(dir)
	local game = self.game
	if game.dir ~= dir then
		game.dir = dir
		self.turnDelay = 3
		return
	end
	if self.turnDelay and self.turnDelay > 0 then return end
	local d = Util.DIRS[dir]
	local nx, ny = game.x + d.x, game.y + d.y
	if not self.map:isWalkable(nx, ny) then
		self.bump = 4
		return
	end
	self.moving = true
	self.offset = 0
	self.target = { x = nx, y = ny }
end

function Overworld:finishStep()
	local game = self.game
	game.x, game.y = self.target.x, self.target.y
	self.moving = false
	self.offset = 0
	self.target = nil
	self.step = self.step + 1
	game.steps = game.steps + 1

	local warp = self.map:warpAt(game.x, game.y)
	if warp and warp.to ~= "sector" then
		self:useWarp(warp)
		return
	end
	if warp and warp.to == "sector" then
		self:useWarp(warp)
		return
	end
	self:checkAnomaly()
	if not self.transition then self:rollEncounter() end
end

-- --- update ---------------------------------------------------------------

function Overworld:update()
	local game = self.game

	if self.transition then
		self.transition.timer = self.transition.timer - 1
		if self.transition.timer <= 0 then
			local t = self.transition
			self.transition = nil
			self:enter(t.key, t.x, t.y, t.dir)
		end
		return
	end

	if self.pending == "starter" then
		self.pending = nil
		Scenes.push(StarterScene.new(game))
		return
	end

	if self.bannerTimer > 0 then self.bannerTimer = self.bannerTimer - 1 end
	if self.bump and self.bump > 0 then self.bump = self.bump - 1 end
	if self.turnDelay and self.turnDelay > 0 then self.turnDelay = self.turnDelay - 1 end

	if self.dialog then
		if playdate.buttonJustPressed(playdate.kButtonA) or playdate.buttonJustPressed(playdate.kButtonB) then
			self.dialogIndex = self.dialogIndex + 1
			if self.dialogIndex > #self.dialog then self:closeDialog() end
		end
		return
	end

	if self.moving then
		self.offset = self.offset + STEP_PX
		if self.offset >= TILE then self:finishStep() end
		return
	end

	if playdate.buttonJustPressed(playdate.kButtonB) then
		Scenes.push(PauseScene.new(game))
		return
	end
	if playdate.buttonJustPressed(playdate.kButtonA) then
		self:interact()
		return
	end

	local held = {
		up = playdate.buttonIsPressed(playdate.kButtonUp),
		down = playdate.buttonIsPressed(playdate.kButtonDown),
		left = playdate.buttonIsPressed(playdate.kButtonLeft),
		right = playdate.buttonIsPressed(playdate.kButtonRight),
	}
	for _, dir in ipairs(Util.DIR_ORDER) do
		if held[dir] then
			self:tryMove(dir)
			break
		end
	end

	local crank = playdate.getCrankChange()
	if math.abs(crank) > 2 then self.scanner = true end
	if playdate.buttonJustPressed(playdate.kButtonUp) then self.scanner = false end
end

-- --- draw -----------------------------------------------------------------

function Overworld:camera()
	local game = self.game
	local d = self.moving and Util.DIRS[game.dir] or { x = 0, y = 0 }
	local px = (game.x - 1) * TILE + d.x * self.offset
	local py = (game.y - 1) * TILE + d.y * self.offset
	local camX = px - UI.SCREEN_W // 2 + TILE // 2
	local camY = py - UI.SCREEN_H // 2 + TILE // 2
	local maxX = math.max(0, self.map:pixelWidth() - UI.SCREEN_W)
	local maxY = math.max(0, self.map:pixelHeight() - UI.SCREEN_H)
	return Util.clamp(camX, 0, maxX), Util.clamp(camY, 0, maxY), px, py
end

function Overworld:draw()
	local game = self.game
	gfx.clear(gfx.kColorWhite)
	local camX, camY, px, py = self:camera()

	self.map.groundMap:draw(-camX, -camY)
	self.map.objectMap:draw(-camX, -camY)

	for _, npc in ipairs(self.map.npcs) do
		local img = Assets.actorFrame(npc.sprite, npc.dir, 0)
		img:draw((npc.x - 1) * TILE - camX, (npc.y - 1) * TILE - camY)
	end

	local frame = self.moving and ((self.step + (self.offset // 8)) % 2) or 0
	local bump = (self.bump and self.bump > 0) and 1 or 0
	Assets.actorFrame("kop", game.dir, frame):draw(px - camX + bump, py - camY)

	if self.transition then
		local t = 8 - self.transition.timer
		gfx.setColor(gfx.kColorBlack)
		local h = math.floor(UI.SCREEN_H * t / 8)
		gfx.fillRect(0, 0, UI.SCREEN_W, h // 2)
		gfx.fillRect(0, UI.SCREEN_H - h // 2, UI.SCREEN_W, h // 2)
	end

	if self.bannerTimer > 0 then
		local w = UI.textWidth(self.banner, true) + 32
		UI.frame(8, 8, w, 32)
		UI.text(self.banner, 24, 16, true)
	end

	if self.scanner then self:drawScanner() end

	if self.dialog then
		UI.dialog(self.dialog[self.dialogIndex] or "", self.dialogIndex < #self.dialog)
	end
end

--- Crank-driven survey scanner: bearing and range to nearby points of interest.
function Overworld:drawScanner()
	local game = self.game
	local pois = self.map.pois
	UI.frame(UI.SCREEN_W - 150, 8, 142, 74)
	UI.text("SURVEY SCAN", UI.SCREEN_W - 136, 14, true)
	if not pois or #pois == 0 then
		UI.text("no signals", UI.SCREEN_W - 136, 38)
		return
	end
	local list = {}
	for _, p in ipairs(pois) do
		list[#list + 1] = { p = p, d = Util.dist(game.x, game.y, p.x, p.y) }
	end
	table.sort(list, function(a, b) return a.d < b.d end)
	for i = 1, math.min(2, #list) do
		local entry = list[i]
		local dx, dy = entry.p.x - game.x, entry.p.y - game.y
		local bearing = (math.abs(dx) > math.abs(dy))
			and (dx > 0 and "E" or "W") or (dy > 0 and "S" or "N")
		UI.text(entry.p.label .. " " .. bearing .. " " .. entry.d,
			UI.SCREEN_W - 136, 32 + (i - 1) * 20)
	end
end
