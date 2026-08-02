--- Persistence. Generated sectors use fixed dev-picked seeds, so only the
--- mutable flags (looted caches, cleared anomalies) are stored and a save
--- file stays tiny; maps rebuild identically on load.

Save = {}

Save.SLOT = "znomekop"
Save.VERSION = 2

function Save.serialise(game)
	return {
		version = Save.VERSION,
		party = game.party,
		box = game.box,
		bag = game.bag,
		kodex = game.kodex,
		sector = game.sector,
		room = game.room,
		px = game.px,
		face = game.face,
		flags = game.flags,
		steps = game.steps,
		unlocked = game.unlocked,
	}
end

function Save.write(game)
	if not playdate then return false end
	playdate.datastore.write(Save.serialise(game), Save.SLOT)
	return true
end

function Save.read()
	if not playdate then return nil end
	local data = playdate.datastore.read(Save.SLOT)
	if not data or data.version ~= Save.VERSION then return nil end
	return data
end

function Save.apply(game, data)
	for _, key in ipairs({ "party", "box", "bag", "kodex", "sector", "room",
		"px", "face", "flags", "steps", "unlocked" }) do
		if data[key] ~= nil then game[key] = data[key] end
	end
	for _, c in ipairs(game.party) do Creature.recalc(c) end
	return game
end

function Save.clear()
	if not playdate then return end
	playdate.datastore.delete(Save.SLOT)
end
