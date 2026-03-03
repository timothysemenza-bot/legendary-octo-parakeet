extends Node2D

@onready var content_registry: Node = $ContentRegistry
@onready var status_label: Label = $CanvasLayer/StatusLabel
@onready var floor_manager: Node = $FloorManager

func _ready() -> void:
	if content_registry.has_method("load_all_content"):
		var summary: Dictionary = content_registry.load_all_content()
		status_label.text = "Loaded: rooms=%d items=%d enemies=%d biomes=%d" % [
			summary.get("rooms", 0),
			summary.get("items", 0),
			summary.get("enemies", 0),
			summary.get("biomes", 0)
		]
	else:
		status_label.text = "ContentRegistry missing load_all_content()"

	if floor_manager and floor_manager.has_signal("room_changed"):
		floor_manager.connect("room_changed", Callable(self, "_on_room_changed"))
	if floor_manager and floor_manager.has_method("get_current_room_state"):
		var state: Dictionary = floor_manager.get_current_room_state()
		if not state.is_empty():
			_on_room_changed(
				int(state.get("room_id", 0)),
				str(state.get("room_type", "combat")),
				int(state.get("room_index", 1)),
				int(state.get("room_total", 1))
			)

func _on_room_changed(room_id: int, room_type: String, room_index: int, room_total: int) -> void:
	status_label.text = "Floor Room %d/%d | ID %d | %s" % [
		room_index, room_total, room_id, room_type.to_upper()
	]
