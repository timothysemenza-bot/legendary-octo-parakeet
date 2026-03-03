extends Node2D

signal exit_requested(direction: String)

@onready var door_indicator: Label = $DoorIndicator
@onready var enemy_container: Node2D = $Enemies
@onready var player: CharacterBody2D = $Player

const ROOM_HALF_W := 560.0
const ROOM_HALF_H := 300.0
const EXIT_MARGIN := 42.0

var _doors_locked: bool = true
var _neighbors: Dictionary = {}
var _room_type: String = "combat"
var _exit_cooldown: float = 0.0

func _ready() -> void:
	configure_room({
		"id": 0,
		"type": "combat",
		"difficulty": 1,
		"spawn_budget": 8,
		"neighbors": {"east": 1}
	}, "")

func _process(delta: float) -> void:
	_exit_cooldown = max(0.0, _exit_cooldown - delta)
	_refresh_room_state()
	_handle_exit()

func _on_enemy_defeated() -> void:
	_refresh_room_state()

func configure_room(room_data: Dictionary, from_direction: String) -> void:
	_room_type = str(room_data.get("type", "combat"))
	_neighbors = room_data.get("neighbors", {})
	_clear_enemies()
	_spawn_enemies_for_room(room_data)
	_set_doors_locked(_should_lock_room())
	_place_player_for_entry(from_direction)
	_refresh_room_state()

func _refresh_room_state() -> void:
	var alive := 0
	for child in enemy_container.get_children():
		if is_instance_valid(child):
			alive += 1

	if alive == 0 and _doors_locked:
		_set_doors_locked(false)

	door_indicator.text = "Room: %s | Doors: %s | Enemies: %d | Exits: %s" % [
		_room_type.to_upper(),
		"LOCKED" if _doors_locked else "UNLOCKED",
		alive,
		", ".join(_neighbors.keys())
	]

func _set_doors_locked(locked: bool) -> void:
	_doors_locked = locked

func _should_lock_room() -> bool:
	return _room_type in ["combat", "elite", "boss"]

func _clear_enemies() -> void:
	for child in enemy_container.get_children():
		child.queue_free()

func _spawn_enemies_for_room(room_data: Dictionary) -> void:
	if _room_type == "start" or _room_type == "shop":
		return

	var budget: int = int(room_data.get("spawn_budget", 8))
	var difficulty: int = int(room_data.get("difficulty", 1))
	var count := clampi(1 + int((budget + difficulty * 2) / 8), 1, 6)
	if _room_type == "boss":
		count = max(count, 5)
	if _room_type == "elite":
		count = max(count, 3)

	var charger_scene := preload("res://scenes/enemies/charger.tscn")
	var rng := RandomNumberGenerator.new()
	rng.seed = int(room_data.get("id", 0)) * 9973 + difficulty * 31
	for i in count:
		var enemy := charger_scene.instantiate()
		enemy.position = Vector2(
			rng.randf_range(-220.0, 220.0) + float(i * 12),
			rng.randf_range(-140.0, 140.0)
		)
		if enemy.has_signal("defeated"):
			enemy.connect("defeated", Callable(self, "_on_enemy_defeated"))
		enemy_container.add_child(enemy)

func _place_player_for_entry(from_direction: String) -> void:
	match from_direction:
		"east":
			player.position = Vector2(-ROOM_HALF_W + 64.0, 0)
		"west":
			player.position = Vector2(ROOM_HALF_W - 64.0, 0)
		"north":
			player.position = Vector2(0, ROOM_HALF_H - 64.0)
		"south":
			player.position = Vector2(0, -ROOM_HALF_H + 64.0)
		_:
			player.position = Vector2(-180, 0)

func _handle_exit() -> void:
	if _doors_locked or _exit_cooldown > 0.0:
		return

	var dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var p := player.position

	if p.x >= ROOM_HALF_W - EXIT_MARGIN and dir.x > 0.3 and _neighbors.has("east"):
		_exit_cooldown = 0.25
		exit_requested.emit("east")
	elif p.x <= -ROOM_HALF_W + EXIT_MARGIN and dir.x < -0.3 and _neighbors.has("west"):
		_exit_cooldown = 0.25
		exit_requested.emit("west")
	elif p.y <= -ROOM_HALF_H + EXIT_MARGIN and dir.y < -0.3 and _neighbors.has("north"):
		_exit_cooldown = 0.25
		exit_requested.emit("north")
	elif p.y >= ROOM_HALF_H - EXIT_MARGIN and dir.y > 0.3 and _neighbors.has("south"):
		_exit_cooldown = 0.25
		exit_requested.emit("south")
