extends Node

var credits: int = 0

func add_credits(amount: int) -> void:
	credits += amount

func try_spend(amount: int) -> bool:
	if credits < amount:
		return false
	credits -= amount
	return true

