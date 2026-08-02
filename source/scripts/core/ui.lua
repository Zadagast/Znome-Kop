--- Shared 1-bit UI chrome: Game Boy style framed panels, menus and bars.

import "CoreLibs/graphics"

local gfx <const> = playdate.graphics

UI = {}

UI.SCREEN_W = 400
UI.SCREEN_H = 240
UI.DIALOG_H = 64

function UI.init()
	UI.font = gfx.getSystemFont()
	UI.fontBold = gfx.getSystemFont(gfx.font.kVariantBold)
	UI.lineHeight = UI.font:getHeight() + 2
end

--- White panel with the classic double border.
function UI.frame(x, y, w, h)
	gfx.setColor(gfx.kColorWhite)
	gfx.fillRect(x, y, w, h)
	gfx.setColor(gfx.kColorBlack)
	gfx.setLineWidth(1)
	gfx.drawRect(x, y, w, h)
	gfx.drawRect(x + 2, y + 2, w - 4, h - 4)
end

function UI.text(str, x, y, bold)
	gfx.setImageDrawMode(gfx.kDrawModeCopy)
	gfx.setFont(bold and UI.fontBold or UI.font)
	gfx.drawText(str, x, y)
end

function UI.textRight(str, x, y, bold)
	gfx.setFont(bold and UI.fontBold or UI.font)
	local w = gfx.getTextSize(str)
	gfx.drawText(str, x - w, y)
end

function UI.textWidth(str, bold)
	gfx.setFont(bold and UI.fontBold or UI.font)
	return (gfx.getTextSize(str))
end

--- Bottom dialog box. `str` may contain newlines. Returns the box rect.
function UI.dialog(str, more)
	local x, y = 4, UI.SCREEN_H - UI.DIALOG_H - 4
	UI.frame(x, y, UI.SCREEN_W - 8, UI.DIALOG_H)
	UI.text(str, x + 12, y + 10)
	if more then
		local t = playdate.getCurrentTimeMilliseconds() // 300 % 2
		gfx.fillTriangle(
			UI.SCREEN_W - 26, y + UI.DIALOG_H - 18 + t,
			UI.SCREEN_W - 16, y + UI.DIALOG_H - 18 + t,
			UI.SCREEN_W - 21, y + UI.DIALOG_H - 12 + t)
	end
	return x, y, UI.SCREEN_W - 8, UI.DIALOG_H
end

--- Vertical menu. `items` is a list of strings or { left, right } pairs.
function UI.menu(x, y, w, items, index, opts)
	opts = opts or {}
	local rowH = opts.rowH or (UI.lineHeight + 2)
	local h = opts.h or (#items * rowH + 16)
	UI.frame(x, y, w, h)
	for i, item in ipairs(items) do
		local ty = y + 8 + (i - 1) * rowH
		local left, right
		if type(item) == "table" then left, right = item[1], item[2] else left = item end
		UI.text(left, x + 20, ty)
		if right then UI.textRight(right, x + w - 10, ty) end
		if i == index then
			gfx.fillTriangle(x + 8, ty + 3, x + 8, ty + 13, x + 15, ty + 8)
		end
	end
	return h
end

function UI.hpBar(x, y, w, fraction)
	local h = 6
	gfx.setColor(gfx.kColorWhite)
	gfx.fillRect(x, y, w, h)
	gfx.setColor(gfx.kColorBlack)
	gfx.drawRect(x, y, w, h)
	local inner = math.max(0, math.floor((w - 4) * Util.clamp(fraction, 0, 1)))
	if fraction <= 0.25 then
		-- low HP reads as a dithered bar so it is obvious on a 1-bit screen
		gfx.setPattern({ 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55 })
	end
	gfx.fillRect(x + 2, y + 2, inner, h - 4)
	gfx.setColor(gfx.kColorBlack)
end

function UI.expBar(x, y, w, fraction)
	gfx.setColor(gfx.kColorBlack)
	gfx.drawRect(x, y, w, 3)
	gfx.fillRect(x + 1, y + 1, math.floor((w - 2) * Util.clamp(fraction, 0, 1)), 1)
end

--- Battle status plate for one creature.
function UI.statusPlate(x, y, creature, showHp, hpShown)
	local w = 150
	UI.frame(x, y, w, showHp and 46 or 36)
	UI.text(creature.name, x + 10, y + 6, true)
	UI.textRight("L" .. creature.level, x + w - 10, y + 6)
	UI.hpBar(x + 10, y + 24, w - 20, (hpShown or creature.hp) / creature.stats.hp)
	if showHp then
		UI.textRight(math.floor(hpShown or creature.hp) .. "/" .. creature.stats.hp, x + w - 10, y + 30)
	end
	if creature.status then
		UI.text(creature.status, x + 10, y + 30)
	end
	return w
end

--- Screen-wide banner used for sector titles.
function UI.banner(title, subtitle)
	local w = 260
	local x = (UI.SCREEN_W - w) // 2
	UI.frame(x, 78, w, subtitle and 60 or 44)
	UI.text(title, x + 16, 90, true)
	if subtitle then UI.text(subtitle, x + 16, 110) end
end

--- Wraps text to a pixel width, returning a list of lines.
function UI.wrap(str, maxWidth)
	local lines = {}
	for paragraph in (str .. "\n"):gmatch("(.-)\n") do
		local line = ""
		for word in paragraph:gmatch("%S+") do
			local candidate = (line == "") and word or (line .. " " .. word)
			if UI.textWidth(candidate) > maxWidth and line ~= "" then
				lines[#lines + 1] = line
				line = word
			else
				line = candidate
			end
		end
		lines[#lines + 1] = line
	end
	return lines
end
