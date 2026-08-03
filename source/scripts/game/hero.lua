--- Hero rendering: a paper-doll rig composed every frame from the part
--- images, limbs rotated by sine math (see tools/ai_rig.py for the art
--- pipeline and source/scripts/game/herorig.lua for the pivot offsets).

local gfx <const> = playdate.graphics

Hero = {}

local LEG_SWING <const> = 24
local ARM_SWING <const> = 18
local CYCLE <const> = 24 -- frames per full stride at 30fps

--- Mirrored copies of the part images, built once (drawRotated has no flip
--- argument, so the left-facing hero needs its own set).
local mirrored = nil

local function mirroredParts()
	if mirrored then return mirrored end
	mirrored = {}
	for i = 1, 4 do
		local src = Assets.heroParts:getImage(i)
		local w, h = src:getSize()
		local img = gfx.image.new(w, h)
		gfx.pushContext(img)
		src:draw(0, 0, gfx.kImageFlippedX)
		gfx.popContext()
		mirrored[i] = img
	end
	return mirrored
end

local function drawRig(px, groundY, moving, t, mirror)
	local parts = mirror and mirroredParts() or Assets.heroParts
	local rig = HeroRig
	local legA, armA, bob = 0, 0, 0
	if moving then
		local phase = (t % CYCLE) / CYCLE * 2 * math.pi
		local s = math.sin(phase)
		legA = LEG_SWING * s
		armA = -ARM_SWING * s
		bob = math.abs(math.cos(phase)) < 0.5 and -1 or 0
	end

	local dir = mirror and -1 or 1
	local function place(part, spread, angle)
		local o = rig[part]
		local x = px + dir * (o.x + spread)
		local y = groundY + o.y + bob
		local index = rig.frames[part]
		local img = mirror and parts[index] or parts:getImage(index)
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

--- Draw the hero standing on groundY, centred on px.
function Hero.draw(px, groundY, moving, t, face)
	drawRig(px, groundY, moving, t, (face or 1) < 0)
end
