extends Node

var unlocked_abilities := {}

func unlock(ability_id: String) -> void:
	unlocked_abilities[ability_id] = true

func has(ability_id: String) -> bool:
	return unlocked_abilities.get(ability_id, false)

