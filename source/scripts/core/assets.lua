import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

Assets = {}

local SCENES <const> = { "lab", "colony", "flats", "canyon" }

function Assets.load()
	Assets.znomes = gfx.imagetable.new("images/znomes")
	Assets.znomesBig = gfx.imagetable.new("images/znomesbig")
	Assets.rigs = {}
	for name in pairs(Rigs) do
		if name ~= "frames" then
			Assets.rigs[name] = gfx.imagetable.new("images/" .. name .. "parts")
			assert(Assets.rigs[name], "missing rig parts: " .. name)
		end
	end
	assert(Assets.znomes and Assets.znomesBig, "missing image tables")
	Assets.scenes = {}
	for _, name in ipairs(SCENES) do
		local img = gfx.image.new("images/scenes/scene-" .. name)
		assert(img, "missing scene " .. name)
		Assets.scenes[name] = img
	end
end

function Assets.znomeImage(speciesId)
	local def = Species.get(speciesId)
	return Assets.znomes:getImage(Atlas.znomeSprite[def.sprite])
end

--- Idle-animation frame (1..Atlas.znomeFrames) for a species. Battle uses
--- the bigger render of the same sprites; menus the small one.
function Assets.znomeFrame(speciesId, frame, big)
	local def = Species.get(speciesId)
	local table_ = big and Assets.znomesBig or Assets.znomes
	return table_:getImage(Atlas.znomeSprite[def.sprite] + (frame - 1) % Atlas.znomeFrames)
end
