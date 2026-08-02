import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

Assets = {}

local SCENES <const> = { "lab", "colony", "flats", "canyon" }

function Assets.load()
	Assets.znomes = gfx.imagetable.new("images/znomes")
	Assets.hero = gfx.imagetable.new("images/hero")
	Assets.heroine = gfx.imagetable.new("images/heroine")
	assert(Assets.znomes and Assets.hero and Assets.heroine, "missing image tables")
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

--- Idle-animation frame (1..Atlas.znomeFrames) for a species.
function Assets.znomeFrame(speciesId, frame)
	local def = Species.get(speciesId)
	return Assets.znomes:getImage(Atlas.znomeSprite[def.sprite] + (frame - 1) % Atlas.znomeFrames)
end
