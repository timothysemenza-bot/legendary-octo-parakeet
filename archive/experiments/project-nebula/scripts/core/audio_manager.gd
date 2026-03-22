extends Node

@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var sfx_player: AudioStreamPlayer = $SFXPlayer

const MIX_RATE := 44100.0

var _music_playback: AudioStreamGeneratorPlayback
var _sfx_playback: AudioStreamGeneratorPlayback
var _music_t: float = 0.0
var _sfx_events: Array[Dictionary] = []
var _notes := PackedFloat32Array([110.0, 146.83, 220.0, 293.66])

func _ready() -> void:
	var music_stream := AudioStreamGenerator.new()
	music_stream.mix_rate = MIX_RATE
	music_stream.buffer_length = 0.35
	music_player.stream = music_stream
	music_player.volume_db = -11.0
	music_player.play()
	_music_playback = music_player.get_stream_playback()

	var sfx_stream := AudioStreamGenerator.new()
	sfx_stream.mix_rate = MIX_RATE
	sfx_stream.buffer_length = 0.15
	sfx_player.stream = sfx_stream
	sfx_player.volume_db = -8.0
	sfx_player.play()
	_sfx_playback = sfx_player.get_stream_playback()
	set_process(true)

func play_sfx(name: String) -> void:
	if name == "shoot":
		_sfx_events.append({"name": name, "t": 0.0, "dur": 0.12})
	elif name == "enemy_down":
		_sfx_events.append({"name": name, "t": 0.0, "dur": 0.20})

func _process(_delta: float) -> void:
	_fill_music()
	_fill_sfx()

func _exit_tree() -> void:
	if music_player:
		music_player.stop()
	if sfx_player:
		sfx_player.stop()

func _fill_music() -> void:
	if _music_playback == null:
		return
	var frames: int = _music_playback.get_frames_available()
	for _i in frames:
		var sample := _music_sample(_music_t)
		_music_playback.push_frame(Vector2(sample, sample))
		_music_t += 1.0 / MIX_RATE

func _music_sample(t: float) -> float:
	var pulse_gate := 1.0 if sin(TAU * 2.0 * t) > 0.0 else 0.35
	var bass := sin(TAU * 55.0 * t) * 0.27 + sin(TAU * 110.0 * t) * 0.12
	var idx: int = int(floor((t / 0.25))) % _notes.size()
	var note: float = _notes[idx]
	var phase := fmod(t, 0.25) / 0.25
	var arp_env: float = max(0.0, 1.0 - phase * 1.8)
	var arp: float = sin(TAU * note * t) * 0.17 * arp_env
	return (bass * pulse_gate + arp) * 0.5

func _fill_sfx() -> void:
	if _sfx_playback == null:
		return
	var frames: int = _sfx_playback.get_frames_available()
	for _i in frames:
		var mixed := 0.0
		for event in _sfx_events:
			mixed += _sample_event(event)
			event["t"] = float(event["t"]) + (1.0 / MIX_RATE)
		_sfx_events = _sfx_events.filter(func(e: Dictionary) -> bool: return float(e["t"]) < float(e["dur"]))
		mixed = clamp(mixed, -0.8, 0.8)
		_sfx_playback.push_frame(Vector2(mixed, mixed))

func _sample_event(event: Dictionary) -> float:
	var name: String = String(event.get("name", ""))
	var t: float = float(event.get("t", 0.0))
	var dur: float = float(event.get("dur", 0.1))
	var env: float = clamp(1.0 - (t / dur), 0.0, 1.0)

	if name == "shoot":
		var f: float = lerp(900.0, 620.0, t / dur)
		return sin(TAU * f * t) * env * 0.45
	if name == "enemy_down":
		var f2: float = lerp(320.0, 90.0, t / dur)
		var noise: float = 1.0 if int(t * MIX_RATE) % 2 == 0 else -1.0
		return (sin(TAU * f2 * t) * 0.5 + noise * 0.2) * env * 0.55
	return 0.0
