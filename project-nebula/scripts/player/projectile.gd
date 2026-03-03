extends Area2D

@export var speed: float = 460.0
@export var damage: int = 1

var direction: Vector2 = Vector2.RIGHT

func set_direction(new_direction: Vector2) -> void:
	direction = new_direction.normalized()
	rotation = direction.angle()

func _physics_process(delta: float) -> void:
	global_position += direction * speed * delta
	global_position = global_position.round()

	for enemy in get_tree().get_nodes_in_group("enemy"):
		if enemy is Node2D and global_position.distance_to(enemy.global_position) <= 14.0:
			if enemy.has_method("take_damage"):
				enemy.take_damage(damage)
			queue_free()
			return

	if global_position.length() > 5000.0:
		queue_free()
