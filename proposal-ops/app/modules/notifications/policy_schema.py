from copy import deepcopy

from app.core.config import DEFAULT_NOTIFICATION_POLICY


NOTIFICATION_POLICY_SCHEMA = {
    "type": "object",
    "required": ["global_thresholds", "client_threshold_overrides", "routing"],
    "properties": {
        "global_thresholds": {
            "type": "object",
            "required": ["reminder_days_before_sla", "escalation_tiers"],
        },
        "client_threshold_overrides": {"type": "object"},
        "routing": {"type": "object"},
    },
}


def default_policy() -> dict:
    return deepcopy(DEFAULT_NOTIFICATION_POLICY)


def validate_policy(policy: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(policy, dict):
        return ["Policy must be a JSON object."]

    required_top = {"global_thresholds", "client_threshold_overrides", "routing"}
    missing = required_top - set(policy.keys())
    if missing:
        errors.append(f"Missing top-level keys: {', '.join(sorted(missing))}.")

    thresholds = policy.get("global_thresholds", {})
    if not isinstance(thresholds, dict):
        errors.append("global_thresholds must be an object.")
    else:
        reminder = thresholds.get("reminder_days_before_sla")
        if not isinstance(reminder, int) or reminder < 0:
            errors.append("global_thresholds.reminder_days_before_sla must be an integer >= 0.")
        tiers = thresholds.get("escalation_tiers")
        if not isinstance(tiers, list) or not tiers:
            errors.append("global_thresholds.escalation_tiers must be a non-empty integer array.")
        else:
            if not all(isinstance(x, int) and x > 0 for x in tiers):
                errors.append("global_thresholds.escalation_tiers entries must be integers > 0.")
            if tiers != sorted(tiers):
                errors.append("global_thresholds.escalation_tiers must be sorted ascending.")

    overrides = policy.get("client_threshold_overrides", {})
    if not isinstance(overrides, dict):
        errors.append("client_threshold_overrides must be an object.")
    else:
        for client_key, cfg in overrides.items():
            if not isinstance(cfg, dict):
                errors.append(f"client_threshold_overrides.{client_key} must be an object.")
                continue
            reminder = cfg.get("reminder_days_before_sla")
            if reminder is not None and (not isinstance(reminder, int) or reminder < 0):
                errors.append(
                    f"client_threshold_overrides.{client_key}.reminder_days_before_sla must be integer >= 0."
                )
            tiers = cfg.get("escalation_tiers")
            if tiers is not None:
                if not isinstance(tiers, list) or not tiers or not all(isinstance(x, int) and x > 0 for x in tiers):
                    errors.append(
                        f"client_threshold_overrides.{client_key}.escalation_tiers must be a non-empty integer array."
                    )

    routing = policy.get("routing", {})
    if not isinstance(routing, dict):
        errors.append("routing must be an object.")
    else:
        if not routing:
            errors.append("routing cannot be empty.")
        for notif_type, cfg in routing.items():
            if not isinstance(cfg, dict):
                errors.append(f"routing.{notif_type} must be an object.")
                continue
            roles = cfg.get("roles")
            if not isinstance(roles, list) or not roles or not all(isinstance(r, str) and r.strip() for r in roles):
                errors.append(f"routing.{notif_type}.roles must be a non-empty string array.")

    return errors
