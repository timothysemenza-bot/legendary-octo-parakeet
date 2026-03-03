extends Node2D

const HALF_W := 560
const HALF_H := 300
const TILE := 16

func _draw() -> void:
	var bg := Color(0.12, 0.17, 0.18, 1.0)
	var edge_dark := Color(0.06, 0.09, 0.1, 1.0)
	var edge_light := Color(0.23, 0.33, 0.30, 1.0)

	for x in range(-HALF_W, HALF_W, TILE):
		draw_rect(Rect2(x, -HALF_H, TILE, TILE), bg, true)
		draw_rect(Rect2(x, HALF_H - TILE, TILE, TILE), bg, true)
		if x % 32 == 0:
			draw_rect(Rect2(x, -HALF_H, TILE, 2), edge_light, true)
			draw_rect(Rect2(x, HALF_H - 2, TILE, 2), edge_dark, true)

	for y in range(-HALF_H, HALF_H, TILE):
		draw_rect(Rect2(-HALF_W, y, TILE, TILE), bg, true)
		draw_rect(Rect2(HALF_W - TILE, y, TILE, TILE), bg, true)
		if y % 32 == 0:
			draw_rect(Rect2(-HALF_W, y, 2, TILE), edge_light, true)
			draw_rect(Rect2(HALF_W - 2, y, 2, TILE), edge_dark, true)

