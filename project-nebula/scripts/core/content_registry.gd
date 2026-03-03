extends Node

const CONTENT_FILES := {
	"rooms": "res://data/rooms.json",
	"items": "res://data/items.json",
	"enemies": "res://data/enemies.json",
	"biomes": "res://data/biomes.json",
	"progression": "res://data/progression.json",
	"balance": "res://data/balance.json"
}

var content: Dictionary = {}

func load_all_content() -> Dictionary:
	var summary: Dictionary = {}
	content.clear()

	for key in CONTENT_FILES.keys():
		var path: String = CONTENT_FILES[key]
		var parsed: Variant = _load_json_file(path)
		content[key] = parsed
		summary[key] = _count_primary_entries(key, parsed)

	print("=== ContentRegistry Loaded ===")
	for key in summary.keys():
		print("%s: %d" % [key, summary[key]])

	return summary

func _load_json_file(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		push_warning("Missing content file: %s" % path)
		return {}

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("Unable to open content file: %s" % path)
		return {}

	var text := file.get_as_text()
	var parsed: Variant = JSON.parse_string(text)
	if parsed == null:
		push_warning("Invalid JSON in %s" % path)
		return {}

	return parsed

func _count_primary_entries(key: String, data: Variant) -> int:
	if typeof(data) != TYPE_DICTIONARY:
		return 0

	match key:
		"rooms":
			return (data as Dictionary).get("templates", []).size()
		"items":
			return (data as Dictionary).get("items", []).size()
		"enemies":
			return (data as Dictionary).get("archetypes", []).size()
		"biomes":
			return (data as Dictionary).get("biomes", []).size()
		"progression":
			return (data as Dictionary).get("traversal_modules", []).size()
		"balance":
			return (data as Dictionary).get("drop_tables", {}).size()
		_:
			return 0
