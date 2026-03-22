extends Node

func generate_floor(seed_value: int, room_count: int) -> Dictionary:
	var count: int = max(5, room_count)
	var rooms: Array[Dictionary] = []
	for i in count:
		rooms.append({
			"id": i,
			"type": "combat",
			"difficulty": 1 + int(i / 2),
			"spawn_budget": 6 + i * 2,
			"neighbors": {}
		})

	rooms[0]["type"] = "start"
	rooms[count - 1]["type"] = "boss"
	if count > 3:
		rooms[2]["type"] = "shop"
	if count > 4:
		rooms[3]["type"] = "elite"

	# Main spine: east-west chain.
	for i in range(count - 1):
		_connect(rooms, i, i + 1, "east", "west")

	# Optional branch from room 1 downward.
	if count >= 6:
		_connect(rooms, 1, count - 2, "south", "north")

	return {
		"seed": seed_value,
		"room_count": count,
		"start_id": 0,
		"rooms": rooms
	}

func _connect(rooms: Array[Dictionary], a: int, b: int, dir_a: String, dir_b: String) -> void:
	var na: Dictionary = rooms[a]["neighbors"]
	var nb: Dictionary = rooms[b]["neighbors"]
	na[dir_a] = b
	nb[dir_b] = a
	rooms[a]["neighbors"] = na
	rooms[b]["neighbors"] = nb
