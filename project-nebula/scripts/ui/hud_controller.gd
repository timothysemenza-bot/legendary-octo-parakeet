extends Label

func _ready() -> void:
	text = "Move: WASD/Arrows | Shoot: Left Click or Enter"
	add_theme_color_override("font_color", Color(0.72, 0.93, 0.82, 1.0))
