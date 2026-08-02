--- Side-scrolling overworld: rooms are full-screen AI-painted backdrops,
--- the player walks left/right, exits at the screen edges link rooms.
--- Encounters, catching and battles reuse the existing systems.

import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

local GROUND_Y <const> = 232 -- feet line
local SPEED <const> = 2.5
local EDGE <const> = 10
local ENCOUNTER_STEP <const> = 26 -- px walked per encounter roll

--- Room graph. `sector` indexes Sectors for encounter tables.
local ROOMS = {
	lab = {
		bg = "lab",
		name = "HAB 7 - LAB",
		exits = { right = "colony" },
		npcs = {
			{
				sprite = "heroine",
				x = 300,
				onTalk = function(game)
					if #game.party == 0 then
						return {
							lines = {
								"Doc: You're the new Kop?",
								"Out there you'll need a Znome.",
								"Take a stasis pod from the rack.",
							},
							action = "starter",
						}
					end
					return {
						lines = { "Doc: Squad restored.", "Careful in the dust." },
						action = "heal",
					}
				end,
			},
		},
	},
	colony = {
		bg = "colony",
		name = "HELLAS COLONY",
		exits = { left = "lab", right = "flats" },
		gate = "right",
	},
	flats = {
		bg = "flats",
		name = "DUST FLATS",
		exits = { left = "colony", right = "canyon" },
		sector = 1,
	},
	canyon = {
		bg = "canyon",
		name = "RELAY CANYON",
		exits = { left = "flats" },
		sector = 2,
		anomaly = { x = 340 },
	},
}

SideScroller = {}
SideScroller.__index = SideScroller

function SideScroller.new(game)
	local self = setmetatable({}, SideScroller)
	self.game = game
	self.t = 0
	self.walked = 0
	self.dialog = nil
	self.dialogIndex = 1
	self.pending = nil
	self:enter(game.room or "lab", game.px or 120)
	return self
end

function SideScroller:enter(key, px)
	local game = self.game
	self.room = ROOMS[key] or ROOMS.lab
	game.room = ROOMS[key] and key or "lab"
	game.px = px
	self.bannerTimer = 60
	self.banner = self.room.name
	self.walked = 0
end

function SideScroller:sector()
	local index = self.room.sector
	return index and Sectors.get(index) or nil
end

-- --- dialog ----------------------------------------------------------------

function SideScroller:say(lines, after)
	self.dialog = type(lines) == "table" and lines or { lines }
	self.dialogIndex = 1
	self.dialogAfter = after
end

function SideScroller:closeDialog()
	local after = self.dialogAfter
	self.dialog = nil
	self.dialogAfter = nil
	if after then after() end
end

-- --- interaction -----------------------------------------------------------

function SideScroller:npcNear()
	for _, npc in ipairs(self.room.npcs or {}) do
		if math.abs(self.game.px - npc.x) < 44 then return npc end
	end
	return nil
end

function SideScroller:interact()
	local game = self.game
	local npc = self:npcNear()
	if npc then
		local result = npc.onTalk and npc.onTalk(game)
			or { lines = npc.lines or { "..." } }
		self:say(result.lines, function()
			self:runAction(result.action)
		end)
		return
	end
	self:say({ "Nothing but dust here." })
end

function SideScroller:runAction(action)
	if action == "heal" then
		self.game:healParty()
		Save.write(self.game)
	elseif action == "starter" then
		self.pending = "starter"
	end
end

-- --- encounters ------------------------------------------------------------

function SideScroller:rollEncounter()
	local game = self.game
	local sector = self:sector()
	if not sector then return end
	if #game.party == 0 or not game:partyAlive() then return end
	if not game.rng:chance(sector.rate) then return end
	self:startWildBattle(sector)
end

function SideScroller:startWildBattle(sector, forced)
	local game = self.game
	local speciesId = forced and forced.species
		or game.rng:weighted(sector.encounters).value
	local level = forced and forced.level
		or game.rng:range(sector.levels[1], sector.levels[2])
	local foe = Creature.new(speciesId, level, game.rng)
	game:logSeen(speciesId)
	Scenes.push(BattleScene.new(game, foe, { sector = sector, boss = forced ~= nil }))
end

function SideScroller:checkAnomaly()
	local a = self.room.anomaly
	if not a then return end
	local game = self.game
	local flagKey = game.room .. ":anomaly"
	if game:flag(flagKey) then return end
	if math.abs(game.px - a.x) > 20 then return end
	game:setFlag(flagKey, true)
	local sector = self:sector()
	self:say({ "Anomaly signal spikes!", "Something big is awake." }, function()
		self:startWildBattle(sector, {
			species = sector.encounters[1].value,
			level = sector.levels[2] + 3,
		})
	end)
end

-- --- update ----------------------------------------------------------------

function SideScroller:useExit(side)
	local game = self.game
	local key = self.room.exits[side]
	if not key then return end
	if self.room.gate == side and #game.party == 0 then
		game.px = side == "right" and (400 - EDGE - 2) or (EDGE + 2)
		self:say({ "No Znome, no wilds.", "See the Doc in the lab." })
		return
	end
	self.transition = {
		timer = 8,
		key = key,
		px = side == "right" and (EDGE + 4) or (400 - EDGE - 4),
	}
end

function SideScroller:update()
	local game = self.game

	if self.transition then
		self.transition.timer = self.transition.timer - 1
		if self.transition.timer <= 0 then
			local t = self.transition
			self.transition = nil
			self:enter(t.key, t.px)
		end
		return
	end

	if self.pending == "starter" then
		self.pending = nil
		Scenes.push(StarterScene.new(game))
		return
	end

	self.t = self.t + 1
	if self.bannerTimer > 0 then self.bannerTimer = self.bannerTimer - 1 end

	if self.dialog then
		if playdate.buttonJustPressed(playdate.kButtonA)
			or playdate.buttonJustPressed(playdate.kButtonB) then
			self.dialogIndex = self.dialogIndex + 1
			if self.dialogIndex > #self.dialog then self:closeDialog() end
		end
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

	local dx = 0
	if playdate.buttonIsPressed(playdate.kButtonLeft) then dx = -SPEED end
	if playdate.buttonIsPressed(playdate.kButtonRight) then dx = SPEED end
	self.moving = dx ~= 0
	if dx ~= 0 then
		game.face = dx > 0 and 1 or -1
		game.px = game.px + dx
		game.steps = game.steps + 1
		self.walked = self.walked + math.abs(dx)
		if game.px < EDGE then
			game.px = EDGE
			self:useExit("left")
		elseif game.px > 400 - EDGE then
			game.px = 400 - EDGE
			self:useExit("right")
		end
		self:checkAnomaly()
		if self.walked >= ENCOUNTER_STEP then
			self.walked = self.walked - ENCOUNTER_STEP
			if not self.transition then self:rollEncounter() end
		end
	end
end

-- --- draw ------------------------------------------------------------------

--- Frame 1 is idle; frames 2..7 are the baked walk cycle (tools/ai_rig.py).
local function heroFrame(moving, t)
	if not moving then return 1 end
	return 2 + (t // 4) % 6
end

function SideScroller:draw()
	local game = self.game
	gfx.clear(gfx.kColorWhite)

	local bg = Assets.scenes[self.room.bg]
	bg:draw(0, 0)

	for _, npc in ipairs(self.room.npcs or {}) do
		local img = Assets.heroine:getImage(1)
		local w, h = img:getSize()
		img:draw(npc.x - w // 2, GROUND_Y - h)
	end

	local frame = heroFrame(self.moving, self.t)
	local img = Assets.hero:getImage(frame)
	local flip = (game.face or 1) < 0 and gfx.kImageFlippedX or gfx.kImageUnflipped
	local w, h = img:getSize()
	img:draw(game.px - w // 2, GROUND_Y - h, flip)

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

	local npc = self:npcNear()
	if npc and not self.dialog then
		UI.text("A: TALK", 336, 220)
	end

	if self.dialog then
		UI.dialog(self.dialog[self.dialogIndex] or "", self.dialogIndex < #self.dialog)
	end
end
