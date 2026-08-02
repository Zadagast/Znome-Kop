--- Pause menu, squad/Kodex/kit browsers, starter pick and title screen.

import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

local function cursor(index, count, step)
	step = step or 1
	if playdate.buttonJustPressed(playdate.kButtonUp) then index = index - step end
	if playdate.buttonJustPressed(playdate.kButtonDown) then index = index + step end
	if count < 1 then return 1 end
	if index < 1 then index = index + count end
	if index > count then index = index - count end
	return index
end

-- --- pause ---------------------------------------------------------------

PauseScene = {}
PauseScene.__index = PauseScene

local PAUSE_ITEMS = { "SQUAD", "KODEX", "KIT", "SAVE", "CLOSE" }

function PauseScene.new(game)
	local self = setmetatable({}, PauseScene)
	self.game = game
	self.index = 1
	self.mode = "root"
	self.sub = 1
	self.scroll = 0
	return self
end

function PauseScene:update()
	local game = self.game
	if self.mode == "root" then
		self.index = cursor(self.index, #PAUSE_ITEMS)
		if playdate.buttonJustPressed(playdate.kButtonB) then
			Scenes.pop()
		elseif playdate.buttonJustPressed(playdate.kButtonA) then
			local choice = PAUSE_ITEMS[self.index]
			if choice == "CLOSE" then
				Scenes.pop()
			elseif choice == "SAVE" then
				Save.write(game)
				self.mode = "saved"
			else
				self.mode = choice:lower()
				self.sub = 1
				self.scroll = 0
			end
		end
	elseif self.mode == "saved" then
		if playdate.buttonJustPressed(playdate.kButtonA) or playdate.buttonJustPressed(playdate.kButtonB) then
			self.mode = "root"
		end
	elseif self.mode == "squad" then
		self.sub = cursor(self.sub, math.max(1, #game.party))
		if playdate.buttonJustPressed(playdate.kButtonB) then self.mode = "root" end
	elseif self.mode == "kodex" then
		self.sub = cursor(self.sub, Species.count)
		if self.sub - self.scroll > 5 then self.scroll = self.sub - 5 end
		if self.sub - self.scroll < 1 then self.scroll = self.sub - 1 end
		if playdate.buttonJustPressed(playdate.kButtonB) then self.mode = "root" end
	elseif self.mode == "kit" then
		local list = game:bagList()
		self.sub = cursor(self.sub, math.max(1, #list))
		if playdate.buttonJustPressed(playdate.kButtonB) then self.mode = "root" end
	end
end

function PauseScene:draw()
	local game = self.game
	local under = Scenes.stack[#Scenes.stack - 1]
	if under then under:draw() end
	gfx.setColor(gfx.kColorBlack)
	gfx.setDitherPattern(0.5, gfx.image.kDitherTypeBayer4x4)
	gfx.fillRect(0, 0, UI.SCREEN_W, UI.SCREEN_H)
	gfx.setColor(gfx.kColorBlack)

	if self.mode == "root" or self.mode == "saved" then
		UI.menu(268, 12, 124, PAUSE_ITEMS, self.index)
		local seen, caught = game:kodexCounts()
		UI.frame(268, 168, 124, 60)
		UI.text("SECTOR " .. game.sector, 282, 176)
		UI.text("KODEX " .. caught .. "/" .. Species.count, 282, 198)
		if self.mode == "saved" then
			UI.dialog("Progress saved to the\ncolony network.")
		end
	elseif self.mode == "squad" then
		self:drawSquad()
	elseif self.mode == "kodex" then
		self:drawKodex()
	elseif self.mode == "kit" then
		self:drawKit()
	end
end

function PauseScene:drawSquad()
	local game = self.game
	UI.frame(8, 8, 384, 224)
	UI.text("SQUAD", 24, 16, true)
	if #game.party == 0 then
		UI.text("No Znomes yet.", 24, 48)
		return
	end
	for i, c in ipairs(game.party) do
		local y = 40 + (i - 1) * 30
		if i == self.sub then
			gfx.fillTriangle(20, y + 5, 20, y + 15, 27, y + 10)
		end
		UI.text(c.name, 34, y)
		UI.text("L" .. c.level, 150, y)
		UI.hpBar(190, y + 6, 90, Creature.hpFraction(c))
		UI.text(c.hp .. "/" .. c.stats.hp, 290, y)
		if c.status then UI.text(c.status, 344, y) end
	end
	local sel = game.party[self.sub]
	if sel then
		local img = Assets.znomeImage(sel.species)
		img:draw(316, 20)
		local def = Species.get(sel.species)
		UI.text(Types.short[def.type] .. "  GRADE " .. sel.grade, 24, 208)
		local names = {}
		for _, m in ipairs(sel.moves) do names[#names + 1] = Moves.get(m.id).name end
		UI.text(table.concat(names, ", "), 130, 208)
	end
end

function PauseScene:drawKodex()
	local game = self.game
	UI.frame(8, 8, 384, 224)
	local seen, caught = game:kodexCounts()
	UI.text("KODEX  " .. caught .. " caught / " .. seen .. " seen", 24, 16, true)
	for row = 1, 6 do
		local i = self.scroll + row
		local id = Species.order[i]
		if id then
			local y = 44 + (row - 1) * 26
			if i == self.sub then
				gfx.fillTriangle(20, y + 5, 20, y + 15, 27, y + 10)
			end
			local known = game.kodex.seen[id]
			local def = Species.get(id)
			UI.text(string.format("%02d", i), 34, y)
			UI.text(known and def.name or "-- -- -- --", 72, y)
			if game.kodex.caught[id] then
				UI.text("x" .. game.kodex.caught[id], 200, y)
			end
		end
	end
	local id = Species.order[self.sub]
	local def = Species.get(id)
	if game.kodex.seen[id] then
		Assets.znomeImage(id):draw(304, 44)
		UI.text(Types.short[def.type], 304, 112)
		UI.text(def.kodex, 24, 202)
	else
		UI.text("No field data recorded.", 24, 202)
	end
end

function PauseScene:drawKit()
	local game = self.game
	local list = game:bagList()
	UI.frame(8, 8, 384, 224)
	UI.text("KIT", 24, 16, true)
	if #list == 0 then
		UI.text("Empty.", 24, 48)
		return
	end
	for i, entry in ipairs(list) do
		local y = 44 + (i - 1) * 24
		if i == self.sub then
			gfx.fillTriangle(20, y + 5, 20, y + 15, 27, y + 10)
		end
		UI.text(entry.name, 34, y)
		UI.text("x" .. entry.count, 240, y)
	end
	local sel = list[self.sub]
	if sel then UI.text(Items.get(sel.id).desc, 24, 202) end
end

-- --- starter -------------------------------------------------------------

StarterScene = {}
StarterScene.__index = StarterScene

local STARTERS = { "rubblin", "frostpod", "sparklet" }

function StarterScene.new(game)
	local self = setmetatable({}, StarterScene)
	self.game = game
	self.index = 1
	self.confirm = false
	return self
end

function StarterScene:update()
	if self.done then
		if playdate.buttonJustPressed(playdate.kButtonA) then Scenes.pop() end
		return
	end
	if playdate.buttonJustPressed(playdate.kButtonLeft) then
		self.index = (self.index - 2) % #STARTERS + 1
	end
	if playdate.buttonJustPressed(playdate.kButtonRight) then
		self.index = self.index % #STARTERS + 1
	end
	if playdate.buttonJustPressed(playdate.kButtonA) then
		if self.confirm then
			local c = Creature.new(STARTERS[self.index], 5, self.game.rng)
			self.game:add(c)
			self.game:addItem("pod", 3)
			Save.write(self.game)
			self.done = true
			self.message = c.name .. " joined your squad!"
		else
			self.confirm = true
		end
	elseif playdate.buttonJustPressed(playdate.kButtonB) then
		self.confirm = false
	end
end

function StarterScene:draw()
	gfx.clear(gfx.kColorWhite)
	UI.text("SELECT A STASIS POD", 24, 16, true)
	for i, id in ipairs(STARTERS) do
		local x = 30 + (i - 1) * 124
		UI.frame(x, 44, 108, 118)
		Assets.znomeImage(id):draw(x + 26, 54)
		local def = Species.get(id)
		UI.text(def.name, x + 12, 128)
		UI.text(Types.short[def.type], x + 12, 144)
		if i == self.index then
			gfx.setLineWidth(3)
			gfx.drawRect(x - 4, 40, 116, 126)
			gfx.setLineWidth(1)
		end
	end
	if self.done then
		UI.dialog(self.message)
	elseif self.confirm then
		UI.dialog("Take " .. Species.get(STARTERS[self.index]).name .. "?\nA to confirm, B to look again.")
	else
		UI.dialog("Left and right to inspect.\nA to select.")
	end
end

-- --- title ---------------------------------------------------------------

TitleScene = {}
TitleScene.__index = TitleScene

function TitleScene.new()
	local self = setmetatable({}, TitleScene)
	self.index = 1
	self.saveData = Save.read()
	self.items = self.saveData and { "CONTINUE", "NEW RUN" } or { "NEW RUN" }
	self.t = 0
	return self
end

function TitleScene:update()
	self.t = self.t + 1
	self.index = cursor(self.index, #self.items)
	if playdate.buttonJustPressed(playdate.kButtonA) then
		local game
		if self.items[self.index] == "CONTINUE" then
			game = Game.fromSave(self.saveData)
		else
			Save.clear()
			game = Game.new()
		end
		World.clear()
		Scenes.replace(Overworld.new(game))
	end
end

function TitleScene:draw()
	gfx.clear(gfx.kColorWhite)
	gfx.setColor(gfx.kColorBlack)
	gfx.setDitherPattern(0.7, gfx.image.kDitherTypeBayer4x4)
	gfx.fillRect(0, 150, UI.SCREEN_W, 90)
	gfx.setColor(gfx.kColorBlack)

	UI.frame(60, 26, 280, 76)
	UI.text("ZNOME KOP", 128, 42, true)
	UI.text("MARS FIELD OPERATIONS", 112, 70)

	Assets.znomeImage("rubblin"):draw(44, 156)
	Assets.znomeImage("sparklet"):draw(300, 156)

	UI.menu(150, 112, 100, self.items, self.index)
end
