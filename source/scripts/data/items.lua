Items = {}

Items.db = {
	pod = { name = "STASIS POD", kind = "pod", power = 1.0, battleOnly = true,
		desc = "Standard containment pod." },
	podmk2 = { name = "HARD POD", kind = "pod", power = 1.8, battleOnly = true,
		desc = "Reinforced field. Holds tougher Znomes." },
	podmk3 = { name = "VOID POD", kind = "pod", power = 3.0, battleOnly = true,
		desc = "Anomaly-grade containment." },
	repair = { name = "REPAIR KIT", kind = "heal", amount = 30,
		desc = "Restores 30 HP." },
	repair2 = { name = "FIELD RIG", kind = "heal", amount = 90,
		desc = "Restores 90 HP." },
	purge = { name = "PURGE SPRAY", kind = "cure",
		desc = "Clears any status condition." },
	jumpstart = { name = "JUMP START", kind = "revive", fraction = 0.5,
		desc = "Revives a downed Znome at half HP." },
}

Items.order = { "pod", "podmk2", "podmk3", "repair", "repair2", "purge", "jumpstart" }

function Items.get(id)
	return Items.db[id]
end
