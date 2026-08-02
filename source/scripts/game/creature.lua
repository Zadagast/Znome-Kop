--- Creature instances: stats, experience, moves and status.
--- Instances are plain tables so they serialise straight into the save file.

Creature = {}

local STATS = { "hp", "atk", "def", "tec", "res", "spd" }
Creature.STATS = STATS

local function statValue(base, grade, level, isHp)
	if isHp then
		return math.floor((base * 2 + grade) * level / 100) + level + 10
	end
	return math.floor((base * 2 + grade) * level / 100) + 5
end

function Creature.expForLevel(level)
	return level * level * level
end

function Creature.levelForExp(exp)
	local level = 1
	while level < 100 and exp >= Creature.expForLevel(level + 1) do
		level = level + 1
	end
	return level
end

function Creature.recalc(c)
	local base = Species.get(c.species).base
	c.stats = {}
	for _, s in ipairs(STATS) do
		c.stats[s] = statValue(base[s], c.grade, c.level, s == "hp")
	end
	if c.hp == nil or c.hp > c.stats.hp then c.hp = c.stats.hp end
end

function Creature.new(speciesId, level, rng)
	local def = Species.get(speciesId)
	assert(def, "unknown species " .. tostring(speciesId))
	local c = {
		species = speciesId,
		name = def.name,
		level = level,
		grade = rng and rng:range(0, 15) or 8,
		exp = Creature.expForLevel(level),
		status = nil,
		statusTimer = 0,
		moves = {},
	}
	for _, moveId in ipairs(Species.movesAt(speciesId, level)) do
		local m = Moves.get(moveId)
		c.moves[#c.moves + 1] = { id = moveId, pp = m.pp, maxpp = m.pp }
	end
	Creature.recalc(c)
	return c
end

function Creature.isFainted(c)
	return c.hp <= 0
end

function Creature.heal(c)
	Creature.recalc(c)
	c.hp = c.stats.hp
	c.status = nil
	c.statusTimer = 0
	for _, m in ipairs(c.moves) do m.pp = m.maxpp end
end

function Creature.hpFraction(c)
	return c.stats.hp > 0 and (c.hp / c.stats.hp) or 0
end

--- Teaches a move, replacing the oldest when the four slots are full.
function Creature.learn(c, moveId)
	for _, m in ipairs(c.moves) do
		if m.id == moveId then return false end
	end
	local def = Moves.get(moveId)
	if #c.moves < 4 then
		c.moves[#c.moves + 1] = { id = moveId, pp = def.pp, maxpp = def.pp }
	else
		table.remove(c.moves, 1)
		c.moves[#c.moves + 1] = { id = moveId, pp = def.pp, maxpp = def.pp }
	end
	return true
end

--- Adds experience. Returns a list of { level, learned, evolved } events.
function Creature.gainExp(c, amount)
	local events = {}
	c.exp = c.exp + amount
	local target = Creature.levelForExp(c.exp)
	while c.level < target and c.level < 100 do
		c.level = c.level + 1
		local hpBefore = c.stats.hp
		Creature.recalc(c)
		c.hp = math.min(c.stats.hp, c.hp + (c.stats.hp - hpBefore))
		local event = { level = c.level }
		local learned = Species.moveLearnedAt(c.species, c.level)
		if learned and Creature.learn(c, learned) then event.learned = learned end
		local def = Species.get(c.species)
		if def.evolve and c.level >= def.evolve.level then
			local from = def.name
			c.species = def.evolve.into
			c.name = Species.get(c.species).name
			Creature.recalc(c)
			event.evolved = { from = from, into = c.name }
		end
		events[#events + 1] = event
	end
	return events
end

--- Experience awarded to the winner for defeating `loser`.
function Creature.expYield(loser)
	local def = Species.get(loser.species)
	return math.max(1, math.floor(def.exp * loser.level / 7))
end
