--- Battle presentation: plays back the event list produced by Battle.

import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

BattleScene = {}
BattleScene.__index = BattleScene

local MENU_ITEMS = { "FIGHT", "PACK", "SQUAD", "RUN" }

function BattleScene.new(game, foe, opts)
	local self = setmetatable({}, BattleScene)
	opts = opts or {}
	self.game = game
	self.boss = opts.boss
	self.battle = Battle.new({
		rng = game.rng,
		party = game.party,
		playerCreature = game:leader(),
		foeCreature = foe,
		wild = true,
	})
	self.state = "events"
	self.menuIndex = 1
	self.moveIndex = 1
	self.listIndex = 1
	self.shake = 0
	self.anim = 0
	self.hpShown = {
		player = self.battle.player.creature.hp,
		foe = self.battle.foe.creature.hp,
	}
	local label = opts.boss and "An anomaly Znome attacks!" or "A wild Znome emerged!"
	self.queue = {
		{ kind = "text", text = label },
		{ kind = "text", text = "Wild " .. foe.name .. "  L" .. foe.level },
		{ kind = "text", text = "Go, " .. self.battle.player.creature.name .. "!" },
	}
	self:advance()
	return self
end

function BattleScene:advance()
	while true do
		local event = table.remove(self.queue, 1)
		if not event then
			self:afterQueue()
			return
		end
		if event.kind == "text" then
			self.message = event.text
			self.state = "events"
			return
		elseif event.kind == "pod" then
			self.shake = event.shakes * 10
		elseif event.kind == "faint" then
			self.faintSide = event.side
		elseif event.kind == "evolve" then
			self.message = event.into .. "!"
		end
	end
end

function BattleScene:afterQueue()
	local b = self.battle
	if b.over then
		self:finish()
		return
	end
	if b.needsSwap then
		if self.game:partyAlive() then
			self.state = "swapForced"
			self.listIndex = 1
			self.message = "Send out which Znome?"
		else
			b.over = true
			b.result = "lose"
			self:finish()
		end
		return
	end
	self.state = "menu"
	self.message = "What will " .. b.player.creature.name .. " do?"
end

function BattleScene:play(events)
	self.queue = events
	self:advance()
end

function BattleScene:finish()
	local b = self.battle
	local game = self.game
	self.state = "done"
	if b.result == "caught" then
		local where = game:add(b.foe.creature)
		self.message = b.foe.creature.name .. " logged to " ..
			(where == "party" and "the squad." or "storage.")
	elseif b.result == "lose" then
		self.message = "Signal lost. Recovered at the outpost."
	end
	self.doneTimer = 40
end

function BattleScene:leaveBattle()
	local game = self.game
	Scenes.pop()
	if self.battle.result == "lose" then
		game:healParty()
		Scenes.current():enter("lab", 200)
	end
	Save.write(game)
end

-- --- input ----------------------------------------------------------------

local function moveCursor(index, count, columns)
	if playdate.buttonJustPressed(playdate.kButtonUp) then index = index - (columns or 1) end
	if playdate.buttonJustPressed(playdate.kButtonDown) then index = index + (columns or 1) end
	if columns and columns > 1 then
		if playdate.buttonJustPressed(playdate.kButtonLeft) then index = index - 1 end
		if playdate.buttonJustPressed(playdate.kButtonRight) then index = index + 1 end
	end
	if index < 1 then index = index + count end
	if index > count then index = index - count end
	return index
end

function BattleScene:update()
	self:tweenHp()
	self.anim = self.anim + 1
	if self.shake > 0 then self.shake = self.shake - 1 end

	if self.state == "events" then
		if playdate.buttonJustPressed(playdate.kButtonA) or playdate.buttonJustPressed(playdate.kButtonB) then
			self:advance()
		end
	elseif self.state == "done" then
		if self.doneTimer and self.doneTimer > 0 then self.doneTimer = self.doneTimer - 1 end
		if playdate.buttonJustPressed(playdate.kButtonA) or (self.doneTimer or 0) <= 0
			and playdate.buttonJustPressed(playdate.kButtonB) then
			self:leaveBattle()
		end
	elseif self.state == "menu" then
		self.menuIndex = moveCursor(self.menuIndex, #MENU_ITEMS, 2)
		if playdate.buttonJustPressed(playdate.kButtonA) then
			local choice = MENU_ITEMS[self.menuIndex]
			if choice == "FIGHT" then
				self.state = "moves"
				self.moveIndex = 1
			elseif choice == "PACK" then
				self.bag = self.game:bagList(function(item)
					return item.kind == "pod" or item.kind == "heal" or item.kind == "cure"
				end)
				self.listIndex = 1
				self.state = "bag"
			elseif choice == "SQUAD" then
				self.listIndex = 1
				self.state = "swap"
			elseif choice == "RUN" then
				self:play(self.battle:takeTurn({ type = "run" }))
			end
		end
	elseif self.state == "moves" then
		local moves = self.battle.player.creature.moves
		self.moveIndex = moveCursor(self.moveIndex, #moves, 2)
		if playdate.buttonJustPressed(playdate.kButtonB) then
			self.state = "menu"
		elseif playdate.buttonJustPressed(playdate.kButtonA) then
			self.battle:peekFoeMove()
			self:play(self.battle:takeTurn({ type = "move", index = self.moveIndex }))
		end
	elseif self.state == "bag" then
		local n = math.max(1, #self.bag)
		self.listIndex = moveCursor(self.listIndex, n, 1)
		if playdate.buttonJustPressed(playdate.kButtonB) then
			self.state = "menu"
		elseif playdate.buttonJustPressed(playdate.kButtonA) and #self.bag > 0 then
			local entry = self.bag[self.listIndex]
			if self.game:consumeItem(entry.id) then
				self.battle:peekFoeMove()
				self:play(self.battle:takeTurn({ type = "item", id = entry.id }))
			end
		end
	elseif self.state == "swap" or self.state == "swapForced" then
		local party = self.game.party
		self.listIndex = moveCursor(self.listIndex, #party, 1)
		if self.state == "swap" and playdate.buttonJustPressed(playdate.kButtonB) then
			self.state = "menu"
		elseif playdate.buttonJustPressed(playdate.kButtonA) then
			local pick = party[self.listIndex]
			if pick and not Creature.isFainted(pick) and pick ~= self.battle.player.creature then
				if self.state == "swapForced" then
					self.battle.needsSwap = false
					self.battle:swapTo(self.listIndex)
					self.hpShown.player = pick.hp
					self:play(self.battle.events)
				else
					self.battle:peekFoeMove()
					self:play(self.battle:takeTurn({ type = "swap", index = self.listIndex }))
				end
			end
		end
	end
end

function BattleScene:tweenHp()
	for _, side in ipairs({ "player", "foe" }) do
		local actual = self.battle[side].creature.hp
		local shown = self.hpShown[side]
		local speed = math.max(1, self.battle[side].creature.stats.hp / 40)
		if shown > actual then
			self.hpShown[side] = math.max(actual, shown - speed)
		elseif shown < actual then
			self.hpShown[side] = math.min(actual, shown + speed)
		end
	end
end

-- --- draw -----------------------------------------------------------------

function BattleScene:draw()
	gfx.clear(gfx.kColorWhite)
	local b = self.battle

	-- ground shading strips, GB battle style
	gfx.setColor(gfx.kColorBlack)
	gfx.setDitherPattern(0.75, gfx.image.kDitherTypeBayer4x4)
	gfx.fillRect(202, 116, 190, 8)
	gfx.fillRect(6, 162, 190, 8)
	gfx.setColor(gfx.kColorBlack)

	local shakeX = (self.shake > 0) and ((self.shake // 3) % 2 == 0 and 2 or -2) or 0
	local frame = (self.anim // 8) % Atlas.znomeFrames + 1
	local foeImg = Assets.znomeFrame(b.foe.creature.species, frame, true)
	foeImg:draw(262 + shakeX, 0)
	local myImg = Assets.znomeFrame(b.player.creature.species, frame + 2, true)
	myImg:draw(10, 44)

	UI.statusPlate(8, 8, b.foe.creature, false, self.hpShown.foe)
	UI.statusPlate(236, 124, b.player.creature, true, self.hpShown.player)

	if self.state == "menu" then
		self:drawTextBox("What will " .. b.player.creature.name .. " do?")
		self:drawGrid(MENU_ITEMS, self.menuIndex, 224, 172)
	elseif self.state == "moves" then
		local slots = {}
		for _, m in ipairs(b.player.creature.moves) do
			local def = Moves.get(m.id)
			slots[#slots + 1] = def.name
		end
		local current = b.player.creature.moves[self.moveIndex]
		local def = Moves.get(current.id)
		self:drawTextBox(Types.short[def.type] .. "  PP " .. current.pp .. "/" .. current.maxpp ..
			"\nPOW " .. (def.power > 0 and def.power or "--") .. "   ACC " .. def.acc)
		self:drawGrid(slots, self.moveIndex, 176, 172, 210)
	elseif self.state == "bag" then
		local items = {}
		for _, entry in ipairs(self.bag) do
			items[#items + 1] = { entry.name, "x" .. entry.count }
		end
		if #items == 0 then items = { "-- empty --" } end
		self:drawTextBox("Use which item?")
		UI.menu(176, 240 - 8 - (#items * 22 + 16), 216, items, self.listIndex)
	elseif self.state == "swap" or self.state == "swapForced" then
		local items = {}
		for _, c in ipairs(self.game.party) do
			items[#items + 1] = { c.name .. " L" .. c.level, c.hp .. "/" .. c.stats.hp }
		end
		self:drawTextBox(self.message or "Send out which Znome?")
		UI.menu(176, 240 - 8 - (#items * 22 + 16), 216, items, self.listIndex)
	else
		self:drawTextBox(self.message or "", self.state == "events" and #self.queue >= 0)
	end
end

function BattleScene:drawTextBox(text, more)
	UI.dialog(text, more and self.state == "events")
end

function BattleScene:drawGrid(items, index, x, y, w)
	w = w or 168
	local h = 60
	UI.frame(x, y - 4, w, h)
	for i, item in ipairs(items) do
		local col = (i - 1) % 2
		local row = (i - 1) // 2
		local ix = x + 16 + col * (w // 2 - 8)
		local iy = y + 4 + row * 24
		UI.text(item, ix, iy)
		if i == index then
			gfx.fillTriangle(ix - 12, iy + 3, ix - 12, iy + 13, ix - 5, iy + 8)
		end
	end
end
