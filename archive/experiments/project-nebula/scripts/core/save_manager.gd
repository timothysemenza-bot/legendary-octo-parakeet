extends Node

const SAVE_PATH := "user://savegame.json"

func save_meta_progress(data: Dictionary) -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data))

func load_meta_progress() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return {}
	var parsed := JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}

