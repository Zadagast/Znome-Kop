--- Turn-based battle model. Pure logic: it mutates creature tables and
--- returns an ordered list of events for the battle scene to play back.
--- Kept free of playdate APIs so it can run in the headless test harness.

Battle = {}
Battle.__index = Battle

local STAGE_STATS = { "atk", "def", "tec", "res", "spd", "acc", "eva" }

local function newSide(creature)
	local side = { creature = creature, stages = {} }
	for _, s in ipairs(STAGE_STATS) do side.stages[s] = 0 end
	return side
end

local function stageMult(stage)
	if stage >= 0 then return (2 + stage) / 2 end
	return 2 / (2 - stage)
end

local function effective(side, stat)
	local value = side.creature.stats[stat] * stageMult(side.stages[stat] or 0)
	if side.creature.status == "STATIC" and stat == "spd" then value = value * 0.5 end
	return math.max(1, math.floor(value))
end

function Battle.new(opts)
	local self = setmetatable({}, Battle)
	self.rng = opts.rng
	self.party = opts.party
	self.player = newSide(opts.playerCreature)
	self.foe = newSide(opts.foeCreature)
	self.wild = opts.wild ~= false
	self.canCatch = self.wild
	self.runAttempts = 0
	self.over = false
	self.result = nil -- "win" | "lose" | "run" | "caught"
	self.events = {}
	return self
end

function Battle:emit(kind, data)
	data = data or {}
	data.kind = kind
	self.events[#self.events + 1] = data
	return data
end

function Battle:text(str)
	return self:emit("text", { text = str })
end

function Battle:sideOf(who)
	return who == "player" and self.player or self.foe
end

function Battle:otherSide(who)
	return who == "player" and self.foe or self.player
end

-- --- damage -------------------------------------------------------------

function Battle:accuracyCheck(move, attacker, defender)
	if move.acc >= 100 and (attacker.stages.acc or 0) >= 0 and (defender.stages.eva or 0) <= 0 then
		return true
	end
	local chance = move.acc / 100
	chance = chance * stageMult(attacker.stages.acc or 0) / stageMult(defender.stages.eva or 0)
	return self.rng:float() < chance
end

function Battle:damage(move, attacker, defender)
	local a = attacker.creature
	local d = defender.creature
	local atkStat, defStat = "atk", "def"
	if move.category == "TECH" then atkStat, defStat = "tec", "res" end
	local A = effective(attacker, atkStat)
	local D = effective(defender, defStat)
	local base = math.floor(((2 * a.level / 5 + 2) * move.power * A / D) / 50) + 2
	local mult = 1.0
	if move.type == Species.get(a.species).type then mult = mult * 1.5 end
	local eff = Types.effectiveness(move.type, Species.get(d.species).type)
	mult = mult * eff
	if a.status == "SCORCH" and move.category == "PHYS" then mult = mult * 0.5 end
	local roll = 0.85 + self.rng:float() * 0.15
	local crit = self.rng:float() < 0.0625
	if crit then mult = mult * 1.8 end
	return math.max(1, math.floor(base * mult * roll)), eff, crit
end

function Battle:applyDamage(side, amount)
	local c = side.creature
	c.hp = math.max(0, c.hp - amount)
	self:emit("damage", { side = (side == self.player) and "player" or "foe", amount = amount })
	return c.hp <= 0
end

-- --- status -------------------------------------------------------------

local STATUS_TEXT = {
	ROT = "%s is rotting!",
	FROST = "%s is frosted over!",
	STATIC = "%s is static-locked!",
	DORMANT = "%s went dormant!",
	SCORCH = "%s is scorched!",
}

function Battle:inflict(side, statusId)
	local c = side.creature
	if c.status then return false end
	c.status = statusId
	c.statusTimer = (statusId == "DORMANT") and self.rng:range(1, 3) or 0
	self:emit("status", { side = (side == self.player) and "player" or "foe", status = statusId })
	self:text(string.format(STATUS_TEXT[statusId] or "%s is afflicted!", c.name))
	return true
end

--- Returns true when the creature is unable to act this turn.
function Battle:startOfTurnBlock(side)
	local c = side.creature
	if c.status == "DORMANT" then
		if c.statusTimer <= 0 then
			c.status = nil
			self:text(c.name .. " powered back up!")
			return false
		end
		c.statusTimer = c.statusTimer - 1
		self:text(c.name .. " is dormant.")
		return true
	elseif c.status == "FROST" then
		if self.rng:chance(0.25) then
			c.status = nil
			self:text(c.name .. " thawed out!")
			return false
		end
		self:text(c.name .. " is frozen solid.")
		return true
	elseif c.status == "STATIC" and self.rng:chance(0.25) then
		self:text(c.name .. " is stunned by static.")
		return true
	end
	return false
end

function Battle:endOfTurnDamage(side)
	local c = side.creature
	if c.hp <= 0 then return false end
	if c.status == "ROT" or c.status == "SCORCH" then
		local tick = math.max(1, math.floor(c.stats.hp / 16))
		self:text(c.name .. " takes " .. c.status .. " damage.")
		return self:applyDamage(side, tick)
	end
	return false
end

-- --- actions ------------------------------------------------------------

function Battle:useMove(who, moveIndex)
	local attacker = self:sideOf(who)
	local defender = self:otherSide(who)
	local slot = attacker.creature.moves[moveIndex]
	if not slot then return false end
	local move = Moves.get(slot.id)
	if slot.pp <= 0 then
		self:text(attacker.creature.name .. " has no power left for " .. move.name .. "!")
		return false
	end
	slot.pp = slot.pp - 1
	self:text(attacker.creature.name .. " used " .. move.name .. "!")

	if not self:accuracyCheck(move, attacker, defender) then
		self:text("It missed!")
		return false
	end

	if move.category == "STAT" then
		if move.heal then
			local c = attacker.creature
			local amount = math.floor(c.stats.hp * move.heal)
			c.hp = math.min(c.stats.hp, c.hp + amount)
			self:emit("heal", { side = who, amount = amount })
			self:text(c.name .. " repaired itself.")
		end
		if move.status then self:inflict(defender, move.status.id) end
		if move.stages then self:applyStages(move.stages, attacker, defender) end
		return false
	end

	local hits = 1
	if move.hits then hits = self.rng:range(move.hits.min, move.hits.max) end
	local fainted, total, eff, crit = false, 0, 1, false
	for _ = 1, hits do
		local dmg, e, c = self:damage(move, attacker, defender)
		eff, crit = e, crit or c
		total = total + dmg
		fainted = self:applyDamage(defender, dmg)
		if fainted then break end
	end
	if crit then self:text("A critical breach!") end
	local note = Types.describe(eff)
	if note then self:text(note) end
	if hits > 1 then self:text("Hit " .. hits .. " times!") end

	if move.drain then
		local c = attacker.creature
		local gain = math.max(1, math.floor(total * move.drain))
		c.hp = math.min(c.stats.hp, c.hp + gain)
		self:emit("heal", { side = who, amount = gain })
		self:text(c.name .. " drained energy.")
	end
	if move.recoil then
		local kick = math.max(1, math.floor(total * move.recoil))
		self:text(attacker.creature.name .. " takes recoil!")
		if self:applyDamage(attacker, kick) then
			self:faint(attacker)
		end
	end
	if not fainted then
		if move.status and self.rng:chance(move.status.chance) then
			self:inflict(defender, move.status.id)
		end
		if move.stages and self.rng:chance(move.stages.chance or 1.0) then
			self:applyStages(move.stages, attacker, defender)
		end
	end
	return fainted
end

function Battle:applyStages(spec, attacker, defender)
	local side = (spec.target == "self") and attacker or defender
	local before = side.stages[spec.stat] or 0
	local after = Util.clamp(before + spec.delta, -6, 6)
	side.stages[spec.stat] = after
	if after == before then
		self:text(side.creature.name .. "'s " .. spec.stat:upper() .. " won't change.")
	else
		local word = spec.delta > 0 and "rose" or "fell"
		self:text(side.creature.name .. "'s " .. spec.stat:upper() .. " " .. word .. "!")
	end
end

function Battle:faint(side)
	local who = (side == self.player) and "player" or "foe"
	self:emit("faint", { side = who })
	self:text(side.creature.name .. " went offline!")
end

-- --- catching and fleeing -----------------------------------------------

function Battle:catchChance(podPower)
	local c = self.foe.creature
	local def = Species.get(c.species)
	local hpTerm = (3 * c.stats.hp - 2 * c.hp) / (3 * c.stats.hp)
	local statusBonus = 1.0
	if c.status == "DORMANT" or c.status == "FROST" then statusBonus = 2.0
	elseif c.status then statusBonus = 1.5 end
	local p = hpTerm * (def.catch / 255) * podPower * statusBonus
	return Util.clamp(p, 0.03, 0.95)
end

function Battle:throwPod(itemId)
	local item = Items.get(itemId)
	self:text("Launched a " .. item.name .. "!")
	local p = self:catchChance(item.power)
	local shakes = 0
	for _ = 1, 3 do
		if self.rng:float() < p ^ 0.34 then shakes = shakes + 1 else break end
	end
	local caught = shakes >= 3 and self.rng:float() < p ^ 0.34
	self:emit("pod", { shakes = shakes, caught = caught })
	if caught then
		self:text(self.foe.creature.name .. " was contained!")
		self.over = true
		self.result = "caught"
	else
		self:text("It broke free!")
	end
	return caught
end

function Battle:tryRun()
	if not self.wild then
		self:text("No escape from a duel!")
		return false
	end
	self.runAttempts = self.runAttempts + 1
	local ps = effective(self.player, "spd")
	local fs = effective(self.foe, "spd")
	local odds = (ps * 32) / math.max(1, math.floor(fs / 4) % 256) + 30 * self.runAttempts
	if ps > fs or odds > 255 or self.rng:range(0, 255) < odds then
		self:text("Disengaged!")
		self.over = true
		self.result = "run"
		return true
	end
	self:text("Couldn't disengage!")
	return false
end

function Battle:swapTo(index)
	local next = self.party[index]
	if not next or Creature.isFainted(next) or next == self.player.creature then return false end
	self:text(self.player.creature.name .. ", stand down!")
	self.player = newSide(next)
	self:emit("swap", { index = index })
	self:text("Go, " .. next.name .. "!")
	return true
end

-- --- turn ---------------------------------------------------------------

function Battle:foeAction()
	local foe = self.foe.creature
	local best, bestScore = 1, -1
	for i, slot in ipairs(foe.moves) do
		if slot.pp > 0 then
			local move = Moves.get(slot.id)
			local score
			if move.category == "STAT" then
				score = 12 + self.rng:range(0, 10)
			else
				local dmg = self:damage(move, self.foe, self.player)
				score = dmg * (move.acc / 100) + self.rng:range(0, 6)
				if dmg >= self.player.creature.hp then score = score + 60 end
			end
			if score > bestScore then best, bestScore = i, score end
		end
	end
	return best
end

--- action = { type = "move", index } | { type = "item", id, target }
---        | { type = "swap", index } | { type = "run" }
--- Returns the event list produced by this turn.
function Battle:takeTurn(action)
	self.events = {}
	if self.over then return self.events end

	if action.type == "run" then
		if self:tryRun() then return self.events end
	elseif action.type == "item" then
		self:useItem(action)
		if self.over then return self.events end
	elseif action.type == "swap" then
		self:swapTo(action.index)
	end

	local playerFirst
	if action.type == "move" then
		local pm = Moves.get(self.player.creature.moves[action.index].id)
		local fm = Moves.get(self.foe.creature.moves[self:peekFoeMove()].id)
		local pp, fp = pm.priority or 0, fm.priority or 0
		if pp ~= fp then
			playerFirst = pp > fp
		else
			local ps, fs = effective(self.player, "spd"), effective(self.foe, "spd")
			playerFirst = (ps == fs) and self.rng:chance(0.5) or (ps > fs)
		end
	else
		playerFirst = false -- items, swaps and failed runs cost the turn
	end

	local order = playerFirst and { "player", "foe" } or { "foe", "player" }
	for _, who in ipairs(order) do
		if self.over then break end
		local side = self:sideOf(who)
		if side.creature.hp > 0 then
			local blocked = self:startOfTurnBlock(side)
			if not blocked then
				local index = (who == "player") and action.index or self.foeMoveIndex
				if who == "foe" then index = self.foeMoveIndex or self:foeAction() end
				if who == "player" and action.type ~= "move" then
					index = nil
				end
				if index then
					local fainted = self:useMove(who, index)
					if fainted then
						self:faint(self:otherSide(who))
						self:checkEnd()
					end
				end
			end
		end
	end
	self.foeMoveIndex = nil

	if not self.over then
		for _, who in ipairs({ "player", "foe" }) do
			local side = self:sideOf(who)
			if self:endOfTurnDamage(side) then
				self:faint(side)
				self:checkEnd()
			end
		end
	end
	return self.events
end

--- Locks in the foe's move so speed ordering can inspect its priority.
function Battle:peekFoeMove()
	self.foeMoveIndex = self.foeMoveIndex or self:foeAction()
	return self.foeMoveIndex
end

function Battle:useItem(action)
	local item = Items.get(action.id)
	if item.kind == "pod" then
		self:throwPod(action.id)
		return
	end
	local target = action.target or self.player.creature
	if item.kind == "heal" then
		local before = target.hp
		target.hp = math.min(target.stats.hp, target.hp + item.amount)
		self:emit("heal", { side = "player", amount = target.hp - before })
		self:text(target.name .. " recovered " .. (target.hp - before) .. " HP.")
	elseif item.kind == "cure" then
		target.status = nil
		self:text(target.name .. " is stable again.")
	elseif item.kind == "revive" then
		target.hp = math.max(1, math.floor(target.stats.hp * item.fraction))
		self:text(target.name .. " is back online.")
	end
end

function Battle:partyAlive()
	for _, c in ipairs(self.party) do
		if not Creature.isFainted(c) then return true end
	end
	return false
end

function Battle:checkEnd()
	if self.foe.creature.hp <= 0 then
		self.over = true
		self.result = "win"
		local gain = Creature.expYield(self.foe.creature)
		self.expGain = gain
		local events = Creature.gainExp(self.player.creature, gain)
		self:emit("exp", { amount = gain })
		self:text(self.player.creature.name .. " gained " .. gain .. " EXP.")
		for _, e in ipairs(events) do
			self:text(self.player.creature.name .. " reached level " .. e.level .. "!")
			if e.learned then
				self:text("Learned " .. Moves.get(e.learned).name .. "!")
			end
			if e.evolved then
				self:emit("evolve", e.evolved)
				self:text(e.evolved.from .. " reconfigured into " .. e.evolved.into .. "!")
			end
		end
	elseif self.player.creature.hp <= 0 then
		if self:partyAlive() then
			self.needsSwap = true
		else
			self.over = true
			self.result = "lose"
			self:text("All Znomes are offline...")
		end
	end
end
