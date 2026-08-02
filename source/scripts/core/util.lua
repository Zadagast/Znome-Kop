Util = {}

function Util.clamp(v, lo, hi)
	if v < lo then return lo end
	if v > hi then return hi end
	return v
end

function Util.round(v)
	return math.floor(v + 0.5)
end

function Util.sign(v)
	if v > 0 then return 1 elseif v < 0 then return -1 end
	return 0
end

function Util.copy(t)
	local out = {}
	for k, v in pairs(t) do
		out[k] = (type(v) == "table") and Util.copy(v) or v
	end
	return out
end

function Util.count(t)
	local n = 0
	for _ in pairs(t) do n = n + 1 end
	return n
end

function Util.indexOf(list, value)
	for i = 1, #list do
		if list[i] == value then return i end
	end
	return nil
end

--- Manhattan distance between grid cells.
function Util.dist(ax, ay, bx, by)
	return math.abs(ax - bx) + math.abs(ay - by)
end

Util.DIRS = {
	up = { x = 0, y = -1 },
	down = { x = 0, y = 1 },
	left = { x = -1, y = 0 },
	right = { x = 1, y = 0 },
}

Util.DIR_ORDER = { "down", "up", "left", "right" }
