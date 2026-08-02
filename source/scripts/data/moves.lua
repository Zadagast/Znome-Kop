--- Move table. category: "PHYS" uses atk/def, "TECH" uses tec/res,
--- "STAT" never deals damage. Optional fields:
---   status  = { id, chance }        inflict a status condition
---   stages  = { stat, delta, target, chance }
---   drain   = fraction of damage healed
---   recoil  = fraction of damage taken
---   priority = turn order bonus
---   hits    = { min, max }          multi-hit

Moves = {}

Moves.db = {
	-- REGOLITH
	tackle = { name = "RAM", type = "REGOLITH", category = "PHYS", power = 40, acc = 100, pp = 35 },
	gritspray = { name = "GRIT SPRAY", type = "REGOLITH", category = "TECH", power = 35, acc = 100, pp = 30,
		stages = { stat = "acc", delta = -1, target = "foe", chance = 0.3 } },
	stoneshear = { name = "STONE SHEAR", type = "REGOLITH", category = "PHYS", power = 70, acc = 95, pp = 15 },
	quakepulse = { name = "QUAKE PULSE", type = "REGOLITH", category = "TECH", power = 85, acc = 90, pp = 10 },
	ferrograde = { name = "FERROGRADE", type = "REGOLITH", category = "STAT", power = 0, acc = 100, pp = 20,
		stages = { stat = "def", delta = 2, target = "self", chance = 1.0 } },

	-- CRYO
	chill = { name = "CHILL JET", type = "CRYO", category = "TECH", power = 40, acc = 100, pp = 30,
		stages = { stat = "spd", delta = -1, target = "foe", chance = 0.2 } },
	rimeshard = { name = "RIME SHARD", type = "CRYO", category = "PHYS", power = 55, acc = 95, pp = 20 },
	cryolance = { name = "CRYO LANCE", type = "CRYO", category = "TECH", power = 80, acc = 90, pp = 10,
		status = { id = "FROST", chance = 0.15 } },
	frostlock = { name = "FROSTLOCK", type = "CRYO", category = "STAT", power = 0, acc = 75, pp = 10,
		status = { id = "FROST", chance = 1.0 } },

	-- PLASMA
	arcspit = { name = "ARC SPIT", type = "PLASMA", category = "TECH", power = 40, acc = 100, pp = 30,
		status = { id = "STATIC", chance = 0.15 } },
	ionfang = { name = "ION FANG", type = "PLASMA", category = "PHYS", power = 65, acc = 95, pp = 15,
		status = { id = "STATIC", chance = 0.2 } },
	overvolt = { name = "OVERVOLT", type = "PLASMA", category = "TECH", power = 95, acc = 85, pp = 8,
		recoil = 0.25 },
	surgecoil = { name = "SURGE COIL", type = "PLASMA", category = "STAT", power = 0, acc = 100, pp = 20,
		stages = { stat = "spd", delta = 2, target = "self", chance = 1.0 } },

	-- FERRIC
	platebash = { name = "PLATE BASH", type = "FERRIC", category = "PHYS", power = 45, acc = 100, pp = 30 },
	railspike = { name = "RAIL SPIKE", type = "FERRIC", category = "PHYS", power = 75, acc = 90, pp = 12 },
	magpulse = { name = "MAG PULSE", type = "FERRIC", category = "TECH", power = 60, acc = 100, pp = 15,
		stages = { stat = "spd", delta = -1, target = "foe", chance = 0.35 } },
	rivetstorm = { name = "RIVET STORM", type = "FERRIC", category = "PHYS", power = 20, acc = 90, pp = 15,
		hits = { min = 2, max = 4 } },
	hardweld = { name = "HARD WELD", type = "FERRIC", category = "STAT", power = 0, acc = 100, pp = 15,
		stages = { stat = "res", delta = 2, target = "self", chance = 1.0 } },

	-- SPORE
	sporeburst = { name = "SPORE BURST", type = "SPORE", category = "TECH", power = 40, acc = 100, pp = 30,
		status = { id = "ROT", chance = 0.2 } },
	tendril = { name = "TENDRIL", type = "SPORE", category = "PHYS", power = 55, acc = 100, pp = 20,
		drain = 0.5 },
	bloomlash = { name = "BLOOM LASH", type = "SPORE", category = "TECH", power = 80, acc = 95, pp = 10 },
	dormantcloud = { name = "TORPOR CLOUD", type = "SPORE", category = "STAT", power = 0, acc = 70, pp = 10,
		status = { id = "DORMANT", chance = 1.0 } },
	graft = { name = "GRAFT", type = "SPORE", category = "STAT", power = 0, acc = 100, pp = 10, heal = 0.5 },

	-- VOID
	glitch = { name = "GLITCH", type = "VOID", category = "TECH", power = 45, acc = 100, pp = 25 },
	nullbite = { name = "NULL BITE", type = "VOID", category = "PHYS", power = 65, acc = 95, pp = 15 },
	entropy = { name = "ENTROPY", type = "VOID", category = "TECH", power = 90, acc = 85, pp = 8,
		stages = { stat = "res", delta = -1, target = "foe", chance = 0.3 } },
	phaseslip = { name = "PHASE SLIP", type = "VOID", category = "STAT", power = 0, acc = 100, pp = 15,
		stages = { stat = "eva", delta = 1, target = "self", chance = 1.0 } },
	rupture = { name = "RUPTURE", type = "VOID", category = "PHYS", power = 100, acc = 80, pp = 5,
		priority = -1 },

	-- universal
	scrapstrike = { name = "SCRAP STRIKE", type = "FERRIC", category = "PHYS", power = 50, acc = 100, pp = 25 },
	firstmove = { name = "SNAP JAB", type = "REGOLITH", category = "PHYS", power = 35, acc = 100, pp = 25,
		priority = 1 },
}

function Moves.get(id)
	return Moves.db[id]
end

Moves.STATUS_NAMES = {
	ROT = "ROT", FROST = "FROST", STATIC = "STATIC", DORMANT = "DORMANT", SCORCH = "SCORCH",
}
