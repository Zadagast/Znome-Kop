--- Sector 1: Hellas Colony, the hand-authored starting town.
--- Small pressurised dome: two habs, the Znome lab, farm plots, a coolant
--- pond to the south and the north airlock out into the Dust Flats.

Colony = {}

local LEGEND = {
	["."] = "dust",
	[","] = "regolith",
	[":"] = "gravel",
	["g"] = "sporegrass",
	["~"] = "coolant",
	["#"] = "rock",
	["C"] = "cliff",
	["p"] = "plate",
}

local ROWS = {
	"CCCCCCCCCCCCCCCCCCCCCCCC",
	"CCCCCCCCCCCCCCCCCCCCCCCC",
	"#......................#",
	"#......................#",
	"#......................#",
	"#......................#",
	"#..,,,,.........,,,,...#",
	"#..,g,,.........,g,,...#",
	"#..,,,,.........,,,,...#",
	"#......................#",
	"#......................#",
	"#......................#",
	"#......................#",
	"#......................#",
	"#.........:::..........#",
	"#.........:::..........#",
	"#~~~~~~...........~~~~~#",
	"#~~~~~~~~~~~~~~~~~~~~~~#",
	"CCCCCCCCCCCCCCCCCCCCCCCC",
	"CCCCCCCCCCCCCCCCCCCCCCCC",
}

--- Small interior room helper: plate floor, rock walls, exit mat at bottom.
local function room(w, h, exitWarp, exitX)
	local map = Map.new(w, h, "plate")
	for x = 1, w do
		map:setGround(x, 1, Atlas.tile.rock)
		map:setGround(x, 2, Atlas.tile.cliff)
		map:setGround(x, h, Atlas.tile.rock)
	end
	for y = 1, h do
		map:setGround(1, y, Atlas.tile.rock)
		map:setGround(w, y, Atlas.tile.rock)
	end
	exitX = exitX or math.floor(w / 2) + 1
	map:setGround(exitX, h, Atlas.tile.grate)
	map:addWarp(exitX, h, exitWarp)
	map.exitX, map.exitY = exitX, h
	return map
end

function Colony.build(game)
	local map = Map.fromAscii(ROWS, LEGEND)
	map.name = "HELLAS COLONY"
	map.sector = 1

	map:stamp("hab", 3, 3, { to = "home", x = 5, y = 8, dir = "up" })
	map:stamp("hab", 16, 3, { to = "neighbour", x = 5, y = 8, dir = "up" })
	map:stamp("lab", 8, 11, { to = "lab", x = 6, y = 10, dir = "up" })
	map:stamp("gate", 11, 1, { to = "sector", sector = 2, dir = "up" })
	map:stamp("solar", 20, 11)
	map:stamp("tank", 2, 11)
	map:stamp("tower", 21, 6)

	-- fenced lab yard with a gap in front of the doorway
	for x = 7, 13 do
		if x ~= 10 then map:setObject(x, 10, Atlas.tile.fence_h) end
	end
	map:setObject(6, 12, Atlas.tile.crate)
	map:setObject(6, 13, Atlas.tile.crate)
	map:setObject(14, 12, Atlas.tile.vent)
	map:setObject(4, 15, Atlas.tile.boulder)
	map:setObject(19, 15, Atlas.tile.boulder)
	for _, p in ipairs({ { 3, 16 }, { 20, 16 }, { 12, 9 } }) do
		map:setObject(p[1], p[2], Atlas.tile.lichen)
	end

	map:addSign(7, 5, "HELLAS COLONY\nPopulation 31.\nMind the dust.")
	map:addSign(14, 14, "OUTPOST 7\nZnome research and\nfield repair bay.")
	map:addSign(14, 3, "NORTH AIRLOCK\nDUST FLATS beyond.\nCarry a pod.")

	map:addNpc({
		x = 15, y = 12, dir = "left", sprite = "colonist", wander = true,
		onTalk = function()
			return { lines = {
				"Wild Znomes hide in the\nspore grass out there.",
				"No pod, no catch. Get one\nfrom the Doc first.",
			} }
		end,
	})
	map:addNpc({
		x = 5, y = 16, dir = "up", sprite = "colonist",
		onTalk = function()
			return { lines = {
				"That coolant pond feeds the\nwhole dome.",
				"Frostpods used to nest here\nbefore the drills came.",
			} }
		end,
	})
	map:addNpc({
		x = 12, y = 4, dir = "down", sprite = "tech",
		onTalk = function(game)
			if #game.party == 0 then
				return { lines = {
					"Hold it. Nobody cycles the\nairlock without a Znome.",
					"The Doc has a spare in the\noutpost. Go on.",
				}, block = true }
			end
			return { lines = { "Dust Flats are all yours,\nKop. Watch your HP." } }
		end,
	})
	return map
end

function Colony.home()
	local map = room(9, 8, { to = "colony", x = 5, y = 6, dir = "down" })
	map.name = "KOP HAB"
	map.sector = 1
	map:setObject(2, 3, Atlas.tile.crate)
	map:setObject(3, 3, Atlas.tile.crate)
	map:setObject(7, 3, Atlas.tile.vent)
	map:setObject(8, 5, Atlas.tile.pipe_v)
	map:addSign(6, 3, "BUNK TERMINAL\nSleep to restore your\nsquad and save.")
	map:addNpc({
		x = 3, y = 5, dir = "down", sprite = "tech",
		onTalk = function()
			return {
				lines = { "Rest up. I patched the bunk\nterminal this morning." },
				action = "rest",
			}
		end,
	})
	return map
end

function Colony.neighbour()
	local map = room(9, 8, { to = "colony", x = 18, y = 6, dir = "down" })
	map.name = "SURVEY HAB"
	map.sector = 1
	map:setObject(2, 3, Atlas.tile.vent)
	map:setObject(7, 3, Atlas.tile.crate)
	map:addNpc({
		x = 6, y = 5, dir = "left", sprite = "colonist",
		onTalk = function(game)
			local seen = game.kodex and Util.count(game.kodex.seen or {}) or 0
			return { lines = {
				"Logged " .. seen .. " species so far?\nThe Kodex is in your menu.",
				"Every sector runs its own\nspawn table. Keep moving.",
			} }
		end,
	})
	return map
end

function Colony.lab()
	local map = room(11, 10, { to = "colony", x = 10, y = 15, dir = "down" })
	map.name = "OUTPOST 7"
	map.sector = 1
	for x = 3, 9 do
		map:setObject(x, 4, Atlas.tile.crate)
	end
	map:setObject(2, 3, Atlas.tile.vent)
	map:setObject(10, 3, Atlas.tile.vent)
	map:setObject(2, 7, Atlas.tile.pipe_v)
	map:setObject(10, 7, Atlas.tile.pipe_v)
	map:addSign(9, 7, "REPAIR BAY\nFree squad repairs for\nfield Kops.")

	map:addNpc({
		x = 6, y = 5, dir = "down", sprite = "tech",
		onTalk = function(game)
			if #game.party == 0 then
				return {
					lines = {
						"You must be the new Kop.",
						"Three pods on the bench.\nPick the one that answers.",
					},
					action = "starter",
				}
			end
			return {
				lines = { "Bring me anything you catch.\nThe Kodex logs it all." },
				action = "heal",
			}
		end,
	})
	map:addNpc({
		x = 9, y = 8, dir = "left", sprite = "colonist",
		onTalk = function()
			return { lines = { "Repair bay is open. Talk to\nthe Doc for a full patch." },
				action = "heal" }
		end,
	})
	return map
end

Colony.interiors = {
	home = Colony.home,
	neighbour = Colony.neighbour,
	lab = Colony.lab,
}
