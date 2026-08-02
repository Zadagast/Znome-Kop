--- Six elemental classes. Each is strong against two others and weak to two,
--- so every matchup chart row is symmetric and easy to learn.

Types = {}

Types.list = { "REGOLITH", "CRYO", "PLASMA", "FERRIC", "SPORE", "VOID" }

Types.short = {
	REGOLITH = "REG", CRYO = "CRY", PLASMA = "PLA",
	FERRIC = "FER", SPORE = "SPO", VOID = "VOI",
}

local strong = {
	REGOLITH = { "PLASMA", "SPORE" },
	CRYO = { "FERRIC", "REGOLITH" },
	PLASMA = { "FERRIC", "CRYO" },
	FERRIC = { "SPORE", "VOID" },
	SPORE = { "CRYO", "VOID" },
	VOID = { "REGOLITH", "PLASMA" },
}

Types.chart = {}
for _, atk in ipairs(Types.list) do
	Types.chart[atk] = {}
	for _, def in ipairs(Types.list) do
		Types.chart[atk][def] = 1.0
	end
end
for atk, defs in pairs(strong) do
	for _, def in ipairs(defs) do
		Types.chart[atk][def] = 2.0
		Types.chart[def][atk] = 0.5
	end
end

function Types.effectiveness(attackType, defenderType)
	local row = Types.chart[attackType]
	if not row then return 1.0 end
	return row[defenderType] or 1.0
end

function Types.describe(mult)
	if mult >= 2.0 then return "It ruptures the target!" end
	if mult <= 0.5 then return "The plating absorbs it." end
	return nil
end
