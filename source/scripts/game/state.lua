--- Persistent game state and the operations the scenes perform on it.

Game = {}
Game.__index = Game

Game.PARTY_MAX = 6

function Game.new()
	local self = setmetatable({}, Game)
	self.party = {}
	self.box = {}
	self.bag = { pod = 5, repair = 3 }
	self.kodex = { seen = {}, caught = {} }
	self.sector = 1
	self.room = "lab"
	self.px = 120
	self.face = 1
	self.flags = {}
	self.unlocked = 1
	self.steps = 0
	self.rng = RNG.new(playdate and playdate.getSecondsSinceEpoch() or os.time())
	return self
end

function Game.fromSave(data)
	local self = Game.new()
	Save.apply(self, data)
	return self
end

-- --- party ---------------------------------------------------------------

function Game:leader()
	for _, c in ipairs(self.party) do
		if not Creature.isFainted(c) then return c end
	end
	return self.party[1]
end

function Game:partyAlive()
	for _, c in ipairs(self.party) do
		if not Creature.isFainted(c) then return true end
	end
	return false
end

function Game:add(creature)
	self:logCaught(creature.species)
	if #self.party < Game.PARTY_MAX then
		self.party[#self.party + 1] = creature
		return "party"
	end
	self.box[#self.box + 1] = creature
	return "box"
end

function Game:healParty()
	for _, c in ipairs(self.party) do Creature.heal(c) end
end

-- --- kodex ---------------------------------------------------------------

function Game:logSeen(speciesId)
	self.kodex.seen[speciesId] = true
end

function Game:logCaught(speciesId)
	self.kodex.seen[speciesId] = true
	self.kodex.caught[speciesId] = (self.kodex.caught[speciesId] or 0) + 1
end

function Game:kodexCounts()
	local seen, caught = 0, 0
	for _ in pairs(self.kodex.seen) do seen = seen + 1 end
	for _ in pairs(self.kodex.caught) do caught = caught + 1 end
	return seen, caught
end

-- --- bag -----------------------------------------------------------------

function Game:itemCount(id)
	return self.bag[id] or 0
end

function Game:addItem(id, n)
	self.bag[id] = (self.bag[id] or 0) + (n or 1)
end

function Game:consumeItem(id)
	local have = self.bag[id] or 0
	if have <= 0 then return false end
	self.bag[id] = have - 1
	if self.bag[id] == 0 then self.bag[id] = nil end
	return true
end

--- Bag contents in display order: { id, name, count }.
function Game:bagList(filter)
	local list = {}
	for _, id in ipairs(Items.order) do
		local n = self.bag[id]
		if n and n > 0 then
			local item = Items.get(id)
			if not filter or filter(item) then
				list[#list + 1] = { id = id, name = item.name, count = n }
			end
		end
	end
	return list
end

-- --- world flags ---------------------------------------------------------

function Game:flag(key)
	return self.flags[key] == true
end

function Game:setFlag(key, value)
	self.flags[key] = (value ~= false) and true or nil
end

function Game:unlock(sectorIndex)
	if sectorIndex > self.unlocked then self.unlocked = sectorIndex end
end
