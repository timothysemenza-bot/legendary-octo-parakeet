extends Node2D

var t: float = 0.0

const ROOM_HALF_SIZE := Vector2(560, 300)
const STAR_COLORS := [
	Color(0.70, 0.90, 1.0, 0.35),
	Color(0.56, 0.78, 0.92, 0.28),
	Color(0.86, 1.0, 0.88, 0.22)
]

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	_draw_base()
	_draw_stars()
	_draw_far_ridges()
	_draw_mid_ridges()
	_draw_haze()

func _draw_base() -> void:
	draw_rect(Rect2(-ROOM_HALF_SIZE, ROOM_HALF_SIZE * 2.0), Color(0.03, 0.05, 0.08, 1.0), true)

func _draw_stars() -> void:
	for i in 64:
		var x := -540.0 + fmod(float(i * 137), 1080.0)
		var y := -280.0 + fmod(float(i * 83), 560.0)
		var twinkle := 0.85 + sin(t * 2.2 + i * 0.43) * 0.15
		var c: Color = STAR_COLORS[i % STAR_COLORS.size()] * twinkle
		draw_circle(Vector2(x, y), 1.2 + float(i % 3) * 0.25, c)

func _draw_far_ridges() -> void:
	var sway := sin(t * 0.35) * 8.0
	var points := PackedVector2Array([
		Vector2(-560, 300),
		Vector2(-560, 120 + sway),
		Vector2(-380, 90),
		Vector2(-170, 138 + sway * 0.5),
		Vector2(40, 100),
		Vector2(260, 150 + sway * 0.3),
		Vector2(560, 110),
		Vector2(560, 300)
	])
	draw_colored_polygon(points, Color(0.11, 0.18, 0.21, 1.0))

func _draw_mid_ridges() -> void:
	var sway := sin(t * 0.55) * 10.0
	var points := PackedVector2Array([
		Vector2(-560, 300),
		Vector2(-560, 195 + sway),
		Vector2(-410, 165),
		Vector2(-280, 210 + sway * 0.4),
		Vector2(-90, 170),
		Vector2(80, 225 + sway * 0.3),
		Vector2(210, 190),
		Vector2(380, 232 + sway * 0.5),
		Vector2(560, 200),
		Vector2(560, 300)
	])
	draw_colored_polygon(points, Color(0.16, 0.24, 0.24, 1.0))

func _draw_haze() -> void:
	for band in 6:
		var y := -250 + band * 95 + sin(t * 0.9 + band) * 4.0
		var alpha := 0.05 + float(band) * 0.01
		draw_rect(Rect2(-560, y, 1120, 20), Color(0.56, 0.85, 0.68, alpha), true)

