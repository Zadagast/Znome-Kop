--- Character rendering: every person in the game is a paper-doll rig,
--- composed each frame from head/torso/arm/leg images with the limbs
--- rotated by sine math. Art pipeline: tools/ai_rig.py; pivot offsets:
--- source/scripts/game/rigs.lua.

local gfx <const> = playdate.graphics

Rig = {}

local LEG_SWING <const> = 24
local ARM_SWING <const> = 18
local CYCLE <const> = 24 -- frames per stride at 30fps
local IDLE_CYCLE <const> = 60

--- drawRotated has no flip argument, so left-facing characters need their
--- own mirrored part images; built once per character on first use.
local mirrored = {}

local function mirroredParts(name)
	local cache = mirrored[name]
	if cache then return cache end
	cache = {}
	local parts = Assets.rigs[name]
	for i = 1, 4 do
		local src = parts:getImage(i)
		local w, h = src:getSize()
		local img = gfx.image.new(w, h)
		gfx.pushContext(img)
		src:draw(0, 0, gfx.kImageFlippedX)
		gfx.popContext()
		cache[i] = img
	end
	mirrored[name] = cache
	return cache
end

--- Draw a character standing on groundY, centred on px. Walking scissors
--- the legs and swings the arms; standing still just breathes.
function Rig.draw(name, px, groundY, moving, t, face)
	local rig = Rigs[name]
	local parts = Assets.rigs[name]
	local mirror = (face or 1) < 0
	local flipped = mirror and mirroredParts(name) or nil

	local legA, armA, bob = 0, 0, 0
	if moving then
		local phase = (t % CYCLE) / CYCLE * 2 * math.pi
		local s = math.sin(phase)
		legA = LEG_SWING * s
		armA = -ARM_SWING * s
		bob = math.abs(math.cos(phase)) < 0.5 and -1 or 0
	elseif t % IDLE_CYCLE < IDLE_CYCLE // 2 then
		bob = -1
	end

	local dir = mirror and -1 or 1
	local function place(part, spread, angle)
		local o = rig[part]
		local index = Rigs.frames[part]
		local img = flipped and flipped[index] or parts:getImage(index)
		local x = px + dir * (o.x + spread)
		local y = groundY + o.y + bob
		if angle ~= 0 then
			img:drawRotated(x, y, dir * angle)
		else
			img:drawAnchored(x, y, 0.5, 0.5)
		end
	end

	place("leg", rig.hipSpread, -legA)
	place("arm", -rig.shoulderSpread, -armA)
	place("torso", 0, 0)
	place("leg", -rig.hipSpread, legA)
	place("head", 0, 0)
	place("arm", rig.shoulderSpread, armA)
end
