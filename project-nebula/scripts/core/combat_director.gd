extends Node

func get_spawn_budget_for_floor(floor_index: int) -> int:
	return 8 + (floor_index * 3)

