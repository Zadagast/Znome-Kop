--- Deterministic 32-bit xorshift RNG.
--- Map generation must be reproducible from a seed (and identical on device
--- and in the headless test harness), so it never touches math.random.

RNG = {}
RNG.__index = RNG

local MASK = 0xFFFFFFFF

function RNG.new(seed)
	local self = setmetatable({}, RNG)
	self:reseed(seed)
	return self
end

function RNG:reseed(seed)
	seed = math.floor(seed or 1) & MASK
	if seed == 0 then seed = 0x9E3779B9 end
	self.state = seed
	-- Warm up so nearby seeds diverge immediately.
	for _ = 1, 8 do self:next() end
end

--- Raw 32-bit value.
function RNG:next()
	local x = self.state
	x = (x ~ (x << 13)) & MASK
	x = x ~ (x >> 17)
	x = (x ~ (x << 5)) & MASK
	self.state = x
	return x
end

--- Float in [0, 1).
function RNG:float()
	return self:next() / 4294967296.0
end

--- Integer in [1, n].
function RNG:int(n)
	if n <= 1 then return 1 end
	return (self:next() % n) + 1
end

--- Integer in [a, b].
function RNG:range(a, b)
	if b <= a then return a end
	return a + (self:next() % (b - a + 1))
end

function RNG:chance(p)
	return self:float() < p
end

function RNG:pick(list)
	return list[self:int(#list)]
end

--- Pick from { { value = v, weight = w }, ... }.
function RNG:weighted(entries)
	local total = 0
	for i = 1, #entries do total = total + entries[i].weight end
	local roll = self:float() * total
	for i = 1, #entries do
		roll = roll - entries[i].weight
		if roll <= 0 then return entries[i] end
	end
	return entries[#entries]
end

function RNG:shuffle(list)
	for i = #list, 2, -1 do
		local j = self:int(i)
		list[i], list[j] = list[j], list[i]
	end
	return list
end
