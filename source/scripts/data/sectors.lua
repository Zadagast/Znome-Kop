--- Sector progression. Sector 1 is the hand-authored colony; every later
--- sector is generated from these parameters by world/mapgen.lua using a
--- fixed, dev-picked seed, so the world is the same on every playthrough.
--- Re-pick with: lua5.4 tools/preview_map.lua <sectorIndex> <seed>

Sectors = {}

Sectors.list = {
	{
		id = "colony", name = "HELLAS COLONY", generated = false,
		levels = { 2, 4 }, rate = 0.10,
		encounters = {
			{ value = "rubblin", weight = 40 },
			{ value = "frostpod", weight = 30 },
			{ value = "sparklet", weight = 30 },
		},
	},
	{
		id = "flats", name = "DUST FLATS", generated = true, seed = 89,
		size = { w = 64, h = 48 }, levels = { 3, 7 }, rate = 0.12,
		palette = { ground = "dust", rough = "regolith", field = "sporegrass",
			wall = "rock", hazard = "crater", floor = "gravel" },
		openness = 0.62, poi = 5,
		encounters = {
			{ value = "rubblin", weight = 35 },
			{ value = "frostpod", weight = 25 },
			{ value = "sparklet", weight = 25 },
			{ value = "mycomite", weight = 15 },
		},
	},
	{
		id = "canyon", name = "RUST CANYON", generated = true, seed = 23,
		size = { w = 72, h = 56 }, levels = { 8, 13 }, rate = 0.14,
		palette = { ground = "gravel", rough = "dunes", field = "sporegrass_tall",
			wall = "cliff", hazard = "coolant", floor = "plate" },
		openness = 0.44, poi = 6,
		encounters = {
			{ value = "tinplate", weight = 30 },
			{ value = "rubblin", weight = 20 },
			{ value = "sparklet", weight = 20 },
			{ value = "mycomite", weight = 20 },
			{ value = "cragnome", weight = 10 },
		},
	},
	{
		id = "tubes", name = "LAVA TUBES", generated = true, seed = 74,
		size = { w = 64, h = 64 }, levels = { 14, 20 }, rate = 0.18,
		palette = { ground = "tube", rough = "ash", field = "ash",
			wall = "rock", hazard = "crater", floor = "grate" },
		openness = 0.34, poi = 6,
		encounters = {
			{ value = "mycomite", weight = 30 },
			{ value = "frostpod", weight = 20 },
			{ value = "tinplate", weight = 25 },
			{ value = "bloomshade", weight = 15 },
			{ value = "nullet", weight = 10 },
		},
	},
	{
		id = "relay", name = "RELAY STATION", generated = true, seed = 105,
		size = { w = 72, h = 56 }, levels = { 21, 28 }, rate = 0.13,
		palette = { ground = "plate", rough = "grate", field = "sporegrass",
			wall = "cliff", hazard = "coolant", floor = "plate" },
		openness = 0.5, poi = 7,
		encounters = {
			{ value = "tinplate", weight = 20 },
			{ value = "ferrox", weight = 20 },
			{ value = "cryonaut", weight = 20 },
			{ value = "arcfang", weight = 20 },
			{ value = "nullet", weight = 20 },
		},
	},
	{
		id = "anomaly", name = "ANOMALY FIELD", generated = true, seed = 11,
		size = { w = 80, h = 64 }, levels = { 29, 38 }, rate = 0.16,
		palette = { ground = "ash", rough = "dunes", field = "sporegrass_tall",
			wall = "rock", hazard = "crater", floor = "tube" },
		openness = 0.4, poi = 8,
		encounters = {
			{ value = "vantabeast", weight = 12 },
			{ value = "bloomshade", weight = 22 },
			{ value = "arcfang", weight = 22 },
			{ value = "ferrox", weight = 22 },
			{ value = "cryonaut", weight = 22 },
		},
	},
}

Sectors.byId = {}
for i, s in ipairs(Sectors.list) do
	s.index = i
	Sectors.byId[s.id] = s
end

function Sectors.get(index)
	return Sectors.list[Util.clamp(index, 1, #Sectors.list)]
end

function Sectors.count()
	return #Sectors.list
end
