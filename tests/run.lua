--- Test suite for the pure gameplay systems.
--- Focus: generation always produces a traversable, playable sector, and the
--- battle model terminates with sane numbers.

local T = dofile((arg[0]:match("^(.*)run%.lua$") or "") .. "harness.lua")

local SEED_COUNT = tonumber(os.getenv("SEEDS") or "40")

T.group("rng determinism", function()
	local a, b = RNG.new(12345), RNG.new(12345)
	local same = true
	for _ = 1, 200 do
		if a:next() ~= b:next() then same = false end
	end
	T.check(same, "same seed yields the same stream")
	local c = RNG.new(12346)
	T.check(RNG.new(12345):next() ~= c:next(), "different seeds diverge")

	local counts = {}
	local rng = RNG.new(7)
	for _ = 1, 6000 do
		local v = rng:range(1, 6)
		counts[v] = (counts[v] or 0) + 1
	end
	for v = 1, 6 do
		T.check(counts[v] > 700 and counts[v] < 1300, "range(1,6) bucket " .. v .. " is fair")
	end
end)

T.group("type chart", function()
	T.eq(Types.effectiveness("REGOLITH", "PLASMA"), 2.0, "regolith beats plasma")
	T.eq(Types.effectiveness("PLASMA", "REGOLITH"), 0.5, "plasma resists into regolith")
	T.eq(Types.effectiveness("REGOLITH", "REGOLITH"), 1.0, "mirror matchup is neutral")
	for _, atk in ipairs(Types.list) do
		local strong, weak = 0, 0
		for _, def in ipairs(Types.list) do
			local m = Types.effectiveness(atk, def)
			if m > 1 then strong = strong + 1 elseif m < 1 then weak = weak + 1 end
		end
		T.eq(strong, 2, atk .. " is strong against two types")
		T.eq(weak, 2, atk .. " is weak against two types")
	end
end)

T.group("species data", function()
	for _, id in ipairs(Species.order) do
		local def = Species.get(id)
		T.check(def ~= nil, id .. " exists")
		T.check(Util.indexOf(Types.list, def.type) ~= nil, id .. " has a valid type")
		T.check(#def.learn >= 4, id .. " learns at least four moves")
		for _, entry in ipairs(def.learn) do
			T.check(Moves.get(entry[2]) ~= nil, id .. " references move " .. entry[2])
		end
		if def.evolve then
			T.check(Species.get(def.evolve.into) ~= nil, id .. " evolves into a real species")
		end
		local moves = Species.movesAt(id, 50)
		T.check(#moves >= 1 and #moves <= 4, id .. " keeps at most four moves")
	end
end)

T.group("creature progression", function()
	local rng = RNG.new(99)
	local c = Creature.new("rubblin", 5, rng)
	T.eq(c.level, 5, "starts at the requested level")
	T.check(c.stats.hp > 10, "has hp")
	c.hp = 1
	Creature.heal(c)
	T.eq(c.hp, c.stats.hp, "heal restores full hp")

	local events = Creature.gainExp(c, Creature.expForLevel(17) - c.exp)
	T.check(c.level >= 16, "levels up from experience")
	local evolved = false
	for _, e in ipairs(events) do
		if e.evolved then evolved = true end
	end
	T.check(evolved, "rubblin evolves at 16")
	T.eq(c.species, "cragnome", "evolution changes species")
	T.check(#c.moves <= 4, "never exceeds four move slots")
end)

T.group("battle", function()
	local wins, losses, longest = 0, 0, 0
	for seed = 1, 60 do
		local rng = RNG.new(seed * 7919)
		local mine = Creature.new("sparklet", 12, rng)
		local foe = Creature.new("tinplate", 12, rng)
		local battle = Battle.new({ rng = rng, party = { mine }, playerCreature = mine, foeCreature = foe })
		local turns = 0
		while not battle.over and turns < 200 do
			turns = turns + 1
			battle:peekFoeMove()
			local moveIndex = rng:int(#mine.moves)
			battle:takeTurn({ type = "move", index = moveIndex })
			if battle.needsSwap then break end
		end
		longest = math.max(longest, turns)
		if battle.result == "win" then wins = wins + 1 end
		if battle.result == "lose" or battle.needsSwap then losses = losses + 1 end
		T.check(turns < 200, "battle " .. seed .. " terminates")
		T.check(mine.hp >= 0 and foe.hp >= 0, "hp never goes negative")
	end
	T.check(wins > 0 and losses > 0, "matchups are not one-sided (" .. wins .. "W/" .. losses .. "L)")
	T.check(longest <= 60, "battles resolve in a reasonable number of turns (" .. longest .. ")")

	-- type advantage should matter
	local rng = RNG.new(4242)
	local plasma = Creature.new("sparklet", 20, rng)
	local ferric = Creature.new("tinplate", 20, rng)
	local battle = Battle.new({ rng = rng, party = { plasma }, playerCreature = plasma, foeCreature = ferric })
	local strong = battle:damage(Moves.get("arcspit"), battle.player, battle.foe)
	local neutral = battle:damage(Moves.get("glitch"), battle.player, battle.foe)
	T.check(strong > neutral, "super effective STAB out-damages a neutral move")
end)

T.group("catching", function()
	local rng = RNG.new(31337)
	local mine = Creature.new("rubblin", 10, rng)
	local foe = Creature.new("rubblin", 5, rng)
	local battle = Battle.new({ rng = rng, party = { mine }, playerCreature = mine, foeCreature = foe })
	local full = battle:catchChance(1.0)
	foe.hp = 1
	local hurt = battle:catchChance(1.0)
	T.check(hurt > full, "weakened targets are easier to contain")
	foe.status = "DORMANT"
	T.check(battle:catchChance(1.0) > hurt, "status improves catch odds")
	T.check(battle:catchChance(3.0) <= 0.95, "catch chance stays capped")
end)

T.group("map generation", function()
	local slowest = 0
	for i = 2, #Sectors.list do
		local sector = Sectors.get(i)
		for s = 1, SEED_COUNT do
			local seed = s * 104729 + i
			local started = os.clock()
			local map, ex, ey = MapGen.generate(sector, seed)
			local elapsed = os.clock() - started
			slowest = math.max(slowest, elapsed)

			T.check(not map:isBlocked(ex, ey), sector.id .. " seed " .. seed .. ": entry is walkable")

			local seen, count = map:reachable(ex, ey)
			local walkable = 0
			for y = 1, map.h do
				for x = 1, map.w do
					if not map:isBlocked(x, y) then walkable = walkable + 1 end
				end
			end
			T.eq(count, walkable,
				sector.id .. " seed " .. seed .. ": every walkable tile is reachable")
			T.check(count > (map.w * map.h) * 0.12,
				sector.id .. " seed " .. seed .. ": enough room to walk")

			local relay, encounters = nil, 0
			for _, poi in ipairs(map.pois) do
				if poi.kind == "relay" then relay = poi end
				T.check(seen[map:index(poi.x, poi.y)] ~= nil,
					sector.id .. " seed " .. seed .. ": " .. poi.kind .. " is reachable")
			end
			T.check(relay ~= nil, sector.id .. " seed " .. seed .. ": has a relay onward")

			for y = 1, map.h do
				for x = 1, map.w do
					if map:isEncounterTile(x, y) and seen[map:index(x, y)] then
						encounters = encounters + 1
					end
				end
			end
			T.check(encounters > 20,
				sector.id .. " seed " .. seed .. ": has reachable encounter ground (" .. encounters .. ")")
		end
	end
	T.check(slowest < 0.75, string.format("slowest generation %.3fs stays inside budget", slowest))
	print(string.format("  slowest sector generation: %.3fs", slowest))
end)

T.group("determinism of generation", function()
	local sector = Sectors.get(3)
	local a = MapGen.generate(sector, 777)
	local b = MapGen.generate(sector, 777)
	local identical = true
	for i = 1, a.w * a.h do
		if a.ground[i] ~= b.ground[i] or a.object[i] ~= b.object[i] then identical = false break end
	end
	T.check(identical, "same seed rebuilds the identical map")
end)

T.finish()
