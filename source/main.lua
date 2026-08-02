-- ZNOME KOP - Mars field operations
-- Playdate entry point: load modules, then run the scene stack at 30 fps.

import "CoreLibs/graphics"
import "CoreLibs/object"
import "CoreLibs/timer"

import "scripts/core/util"
import "scripts/core/rng"
import "scripts/core/ui"
import "scripts/core/assets"
import "scripts/core/save"

import "scripts/data/types"
import "scripts/data/moves"
import "scripts/data/species"
import "scripts/data/items"
import "scripts/data/sectors"

import "scripts/world/atlas"

import "scripts/game/creature"
import "scripts/game/battle"
import "scripts/game/state"
import "scripts/game/scenes"
import "scripts/game/herorig"
import "scripts/game/hero"
import "scripts/game/sidescroller"
import "scripts/game/battlescene"
import "scripts/game/menus"

local gfx <const> = playdate.graphics

playdate.display.setRefreshRate(30)

UI.init()
Assets.load()
gfx.setBackgroundColor(gfx.kColorWhite)
Scenes.replace(TitleScene.new())

-- Dev toggles: compare the live limb rig against the baked walk frames and
-- watch the frame time while doing it (the device is far slower than the
-- simulator).
SHOW_FPS = false
do
	local menu = playdate.getSystemMenu()
	menu:addCheckmarkMenuItem("live rig", Hero.RUNTIME, function(on)
		Hero.RUNTIME = on
	end)
	menu:addCheckmarkMenuItem("show fps", SHOW_FPS, function(on)
		SHOW_FPS = on
	end)
end

function playdate.update()
	Scenes.update()
	Scenes.draw()
	playdate.timer.updateTimers()
end

function playdate.gameWillTerminate()
	local scene = Scenes.current()
	if scene and scene.game then Save.write(scene.game) end
end

function playdate.deviceWillSleep()
	playdate.gameWillTerminate()
end
