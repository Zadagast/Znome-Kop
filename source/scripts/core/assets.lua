import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

Assets = {}

function Assets.load()
	Assets.tiles = gfx.imagetable.new("images/tiles")
	Assets.actors = gfx.imagetable.new("images/actors")
	Assets.znomes = gfx.imagetable.new("images/znomes")
	assert(Assets.tiles and Assets.actors and Assets.znomes, "missing image tables")
end

--- Actor frames are laid out per actor: down0, down1, up0, up1, left0, left1,
--- right0, right1.
local DIR_OFFSET = { down = 0, up = 2, left = 4, right = 6 }

function Assets.actorFrame(spriteName, dir, step)
	local base = Atlas.actors[spriteName] or Atlas.actors.colonist
	return Assets.actors:getImage(base + DIR_OFFSET[dir] + (step % 2))
end

function Assets.znomeImage(speciesId)
	local def = Species.get(speciesId)
	return Assets.znomes:getImage(Atlas.znomeSprite[def.sprite])
end
