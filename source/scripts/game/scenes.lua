--- Minimal scene stack. Only the top scene updates and draws.

Scenes = {}
Scenes.stack = {}

function Scenes.push(scene)
	Scenes.stack[#Scenes.stack + 1] = scene
	return scene
end

function Scenes.pop()
	local scene = table.remove(Scenes.stack)
	if scene and scene.onExit then scene:onExit() end
	return Scenes.current()
end

function Scenes.current()
	return Scenes.stack[#Scenes.stack]
end

function Scenes.replace(scene)
	Scenes.stack = { scene }
	return scene
end

function Scenes.update()
	local scene = Scenes.current()
	if scene then scene:update() end
end

function Scenes.draw()
	local scene = Scenes.current()
	if scene then scene:draw() end
end
