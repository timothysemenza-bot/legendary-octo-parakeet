extends Node

signal room_changed(room_id: int, room_type: String, room_index: int, room_total: int)

@export var room_path: NodePath = NodePath("../CombatRoom")
@export var generator_path: NodePath = NodePath("../RoomGraphGenerator")

var _rooms: Dictionary = {}
var _current_room_id: int = -1
var _ordered_room_ids: Array[int] = []

@onready var _room: Node = get_node(room_path)
@onready var _generator: Node = get_node(generator_path)

func _ready() -> void:
	if _room.has_signal("exit_requested"):
		_room.connect("exit_requested", Callable(self, "_on_exit_requested"))
	_build_floor()
	_enter_room(0, "")

func _build_floor() -> void:
	var data: Dictionary = _generator.generate_floor(Time.get_unix_time_from_system(), 7)
	_rooms.clear()
	_ordered_room_ids.clear()
	for room_data in data.get("rooms", []):
		var id: int = int(room_data.get("id", -1))
		_rooms[id] = room_data
		_ordered_room_ids.append(id)
	_ordered_room_ids.sort()

func _on_exit_requested(direction: String) -> void:
	if not _rooms.has(_current_room_id):
		return
	var room_data: Dictionary = _rooms[_current_room_id]
	var neighbors: Dictionary = room_data.get("neighbors", {})
	if not neighbors.has(direction):
		return
	var next_room_id: int = int(neighbors[direction])
	_enter_room(next_room_id, direction)

func _enter_room(room_id: int, from_direction: String) -> void:
	if not _rooms.has(room_id):
		return
	_current_room_id = room_id
	var room_data: Dictionary = _rooms[room_id]
	if _room.has_method("configure_room"):
		_room.configure_room(room_data, from_direction)
	var idx := _ordered_room_ids.find(room_id) + 1
	room_changed.emit(room_id, str(room_data.get("type", "combat")), idx, _ordered_room_ids.size())

func get_current_room_state() -> Dictionary:
	if not _rooms.has(_current_room_id):
		return {}
	return {
		"room_id": _current_room_id,
		"room_type": str(_rooms[_current_room_id].get("type", "combat")),
		"room_index": _ordered_room_ids.find(_current_room_id) + 1,
		"room_total": _ordered_room_ids.size()
	}
