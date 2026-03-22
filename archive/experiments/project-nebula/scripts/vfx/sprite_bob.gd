extends ColorRect

@export var bob_speed: float = 4.0
@export var bob_amount: float = 1.5

var _origin_y: float
var _t: float = 0.0

func _ready() -> void:
	_origin_y = position.y

func _process(delta: float) -> void:
	_t += delta
	position.y = _origin_y + sin(_t * bob_speed) * bob_amount
