--- The Znome roster. Ids match the sprite order in tools/art_znomes.py.
--- base:     hp, atk, def, tec, res, spd
--- learn:    { level, moveId } sorted by level
--- evolve:   { level, into }
--- catch:    1..255, higher is easier
--- kodex:    one-line field note shown in the Kodex

Species = {}

Species.order = {
	"rubblin", "cragnome", "frostpod", "cryonaut", "sparklet", "arcfang",
	"tinplate", "ferrox", "mycomite", "bloomshade", "nullet", "vantabeast",
}

Species.db = {
	rubblin = {
		name = "RUBBLIN", type = "REGOLITH", sprite = "rubblin",
		base = { hp = 45, atk = 52, def = 55, tec = 35, res = 40, spd = 38 },
		catch = 190, exp = 62, evolve = { level = 16, into = "cragnome" },
		learn = {
			{ 1, "tackle" }, { 1, "gritspray" }, { 7, "ferrograde" },
			{ 12, "stoneshear" }, { 18, "firstmove" }, { 24, "quakepulse" },
		},
		kodex = "Digests loose regolith and packs it into a shell.",
	},
	cragnome = {
		name = "CRAGNOME", type = "REGOLITH", sprite = "cragnome",
		base = { hp = 80, atk = 90, def = 95, tec = 45, res = 60, spd = 45 },
		catch = 70, exp = 152,
		learn = {
			{ 1, "tackle" }, { 1, "stoneshear" }, { 20, "ferrograde" },
			{ 28, "quakepulse" }, { 34, "railspike" }, { 40, "rupture" },
		},
		kodex = "Colony crews use its shed plates as blast shielding.",
	},
	frostpod = {
		name = "FROSTPOD", type = "CRYO", sprite = "frostpod",
		base = { hp = 48, atk = 40, def = 50, tec = 58, res = 52, spd = 42 },
		catch = 190, exp = 64, evolve = { level = 16, into = "cryonaut" },
		learn = {
			{ 1, "tackle" }, { 1, "chill" }, { 8, "rimeshard" },
			{ 14, "hardweld" }, { 20, "cryolance" }, { 26, "frostlock" },
		},
		kodex = "Vents waste heat as frost; nests in shaded crater rims.",
	},
	cryonaut = {
		name = "CRYONAUT", type = "CRYO", sprite = "cryonaut",
		base = { hp = 78, atk = 60, def = 78, tec = 95, res = 88, spd = 60 },
		catch = 70, exp = 158,
		learn = {
			{ 1, "chill" }, { 1, "rimeshard" }, { 22, "cryolance" },
			{ 30, "frostlock" }, { 36, "hardweld" }, { 42, "entropy" },
		},
		kodex = "Walks the dust flats in a self-grown pressure shell.",
	},
	sparklet = {
		name = "SPARKLET", type = "PLASMA", sprite = "sparklet",
		base = { hp = 42, atk = 45, def = 40, tec = 62, res = 45, spd = 65 },
		catch = 190, exp = 66, evolve = { level = 16, into = "arcfang" },
		learn = {
			{ 1, "tackle" }, { 1, "arcspit" }, { 9, "surgecoil" },
			{ 15, "ionfang" }, { 21, "magpulse" }, { 27, "overvolt" },
		},
		kodex = "Feeds on stray current leaking from colony grids.",
	},
	arcfang = {
		name = "ARCFANG", type = "PLASMA", sprite = "arcfang",
		base = { hp = 70, atk = 88, def = 60, tec = 92, res = 62, spd = 105 },
		catch = 70, exp = 160,
		learn = {
			{ 1, "arcspit" }, { 1, "ionfang" }, { 24, "surgecoil" },
			{ 30, "overvolt" }, { 38, "entropy" }, { 44, "rupture" },
		},
		kodex = "Outruns dust devils. Grounding rods are mandatory nearby.",
	},
	tinplate = {
		name = "TINPLATE", type = "FERRIC", sprite = "tinplate",
		base = { hp = 50, atk = 58, def = 72, tec = 38, res = 50, spd = 40 },
		catch = 150, exp = 74, evolve = { level = 20, into = "ferrox" },
		learn = {
			{ 1, "platebash" }, { 1, "gritspray" }, { 10, "hardweld" },
			{ 16, "rivetstorm" }, { 22, "magpulse" }, { 30, "railspike" },
		},
		kodex = "Scavenges hull scrap and welds it on with molten saliva.",
	},
	ferrox = {
		name = "FERROX", type = "FERRIC", sprite = "ferrox",
		base = { hp = 88, atk = 95, def = 120, tec = 50, res = 75, spd = 48 },
		catch = 55, exp = 172,
		learn = {
			{ 1, "platebash" }, { 1, "rivetstorm" }, { 26, "railspike" },
			{ 32, "hardweld" }, { 38, "magpulse" }, { 46, "rupture" },
		},
		kodex = "A walking bulkhead. Rated to survive a depressurisation.",
	},
	mycomite = {
		name = "MYCOMITE", type = "SPORE", sprite = "mycomite",
		base = { hp = 55, atk = 48, def = 48, tec = 60, res = 58, spd = 44 },
		catch = 170, exp = 70, evolve = { level = 18, into = "bloomshade" },
		learn = {
			{ 1, "tackle" }, { 1, "sporeburst" }, { 11, "tendril" },
			{ 17, "graft" }, { 23, "dormantcloud" }, { 29, "bloomlash" },
		},
		kodex = "Thrives in lava tubes where water ice still lingers.",
	},
	bloomshade = {
		name = "BLOOMSHADE", type = "SPORE", sprite = "bloomshade",
		base = { hp = 95, atk = 70, def = 72, tec = 98, res = 90, spd = 52 },
		catch = 60, exp = 168,
		learn = {
			{ 1, "sporeburst" }, { 1, "tendril" }, { 24, "bloomlash" },
			{ 31, "dormantcloud" }, { 37, "graft" }, { 45, "entropy" },
		},
		kodex = "Its cap seeds an entire tube network in a single season.",
	},
	nullet = {
		name = "NULLET", type = "VOID", sprite = "nullet",
		base = { hp = 44, atk = 42, def = 44, tec = 70, res = 55, spd = 72 },
		catch = 120, exp = 80, evolve = { level = 22, into = "vantabeast" },
		learn = {
			{ 1, "glitch" }, { 1, "phaseslip" }, { 13, "nullbite" },
			{ 19, "gritspray" }, { 25, "entropy" }, { 33, "rupture" },
		},
		kodex = "Sensors read it as a hole in the survey data.",
	},
	vantabeast = {
		name = "VANTABEAST", type = "VOID", sprite = "vantabeast",
		base = { hp = 92, atk = 105, def = 78, tec = 108, res = 80, spd = 88 },
		catch = 40, exp = 196,
		learn = {
			{ 1, "glitch" }, { 1, "nullbite" }, { 28, "entropy" },
			{ 35, "phaseslip" }, { 42, "rupture" }, { 50, "overvolt" },
		},
		kodex = "Anomaly signals bloom wherever this one has fed.",
	},
}

function Species.get(id)
	return Species.db[id]
end

--- Every move the species knows at the given level, latest four kept.
function Species.movesAt(id, level)
	local def = Species.db[id]
	local pool = {}
	for _, entry in ipairs(def.learn) do
		if entry[1] <= level then pool[#pool + 1] = entry[2] end
	end
	local moves = {}
	local first = math.max(1, #pool - 3)
	for i = first, #pool do moves[#moves + 1] = pool[i] end
	if #moves == 0 then moves[1] = def.learn[1][2] end
	return moves
end

--- Move learned exactly on this level, if any.
function Species.moveLearnedAt(id, level)
	for _, entry in ipairs(Species.db[id].learn) do
		if entry[1] == level then return entry[2] end
	end
	return nil
end

Species.count = #Species.order
