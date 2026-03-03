extends CharacterBody2D

@export var move_speed: float = 220.0
@export var fire_cooldown: float = 0.2
@export var projectile_scene: PackedScene

var _fire_timer: float = 0.0

func _ready() -> void:
	add_to_group("player")
	if projectile_scene == null:
		projectile_scene = preload("res://scenes/player/projectile.tscn")

func _physics_process(delta: float) -> void:
	var input_dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	velocity = input_dir * move_speed
	move_and_slide()
	position.x = clamp(position.x, -540.0, 540.0)
	position.y = clamp(position.y, -280.0, 280.0)
	global_position = global_position.round()
	rotation = (get_global_mouse_position() - global_position).angle()

	_fire_timer = max(0.0, _fire_timer - delta)
	var is_firing := Input.is_action_pressed("ui_accept") or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	if is_firing and _fire_timer <= 0.0:
		_shoot()
		_fire_timer = fire_cooldown

func _shoot() -> void:
	var projectile := projectile_scene.instantiate()
	projectile.global_position = global_position

	var dir := (get_global_mouse_position() - global_position).normalized()
	if dir == Vector2.ZERO:
		dir = Vector2.RIGHT

	if projectile.has_method("set_direction"):
		projectile.set_direction(dir)

	get_tree().current_scene.add_child(projectile)
	var audio := get_tree().current_scene.get_node_or_null("AudioManager")
	if audio and audio.has_method("play_sfx"):
		audio.play_sfx("shoot")
