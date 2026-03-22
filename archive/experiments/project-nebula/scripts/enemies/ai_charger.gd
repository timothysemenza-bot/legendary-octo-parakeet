extends CharacterBody2D

signal defeated

@export var move_speed: float = 120.0
@export var max_hp: int = 5

var _hp: int = 0
var _player: Node2D

func _ready() -> void:
	add_to_group("enemy")
	_hp = max_hp
	_player = get_tree().get_first_node_in_group("player") as Node2D

func _physics_process(_delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node2D
		return

	var dir := (_player.global_position - global_position).normalized()
	velocity = dir * move_speed
	move_and_slide()
	global_position = global_position.round()
	if has_node("Shell"):
		$Shell.scale.x = -1.0 if dir.x < 0.0 else 1.0

func take_damage(amount: int) -> void:
	_hp -= amount
	if _hp <= 0:
		var audio := get_tree().current_scene.get_node_or_null("AudioManager")
		if audio and audio.has_method("play_sfx"):
			audio.play_sfx("enemy_down")
		defeated.emit()
		queue_free()
