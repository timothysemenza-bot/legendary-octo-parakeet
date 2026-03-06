from pathlib import Path
import os
import json


BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
DB_DIR = BASE_DIR / ".artifacts"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "bosskey_pursuit_os.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
GATE_POLICY_PACK = os.getenv("BOSSKEY_GATE_POLICY_PACK", "default")
APPROVAL_SIGNING_SECRET = os.getenv("BOSSKEY_APPROVAL_SIGNING_SECRET", "dev-signing-secret")
SESSION_SECRET = os.getenv("BOSSKEY_SESSION_SECRET", "dev-session-secret")
SECRET_STORE_PATH = DB_DIR / "secrets.json"
SECRET_STORE_KEY = os.getenv("BOSSKEY_SECRET_STORE_KEY", SESSION_SECRET)
AUTH_AUTO_PROVISION = os.getenv("BOSSKEY_AUTH_AUTO_PROVISION", "true").lower() == "true"
NOTIFICATION_CHANNELS = [c.strip().lower() for c in os.getenv("BOSSKEY_NOTIFICATION_CHANNELS", "console,email,webhook").split(",") if c.strip()]
NOTIFICATION_WEBHOOK_URL = os.getenv("BOSSKEY_NOTIFICATION_WEBHOOK_URL", "http://localhost/notify")
NOTIFICATION_RETRY_DELAY_MINUTES = int(os.getenv("BOSSKEY_NOTIFICATION_RETRY_DELAY_MINUTES", "5"))
NOTIFICATION_MAX_RETRY_ATTEMPTS = int(os.getenv("BOSSKEY_NOTIFICATION_MAX_RETRY_ATTEMPTS", "3"))
NOTIFICATION_PROVIDER_MODE = os.getenv("BOSSKEY_NOTIFICATION_PROVIDER_MODE", "mock").lower()  # mock|real
SMTP_HOST = os.getenv("BOSSKEY_SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("BOSSKEY_SMTP_PORT", "25"))
SMTP_USE_TLS = os.getenv("BOSSKEY_SMTP_USE_TLS", "false").lower() == "true"
SMTP_USERNAME = os.getenv("BOSSKEY_SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("BOSSKEY_SMTP_PASSWORD", "")
SMTP_SENDER = os.getenv("BOSSKEY_SMTP_SENDER", "bosskey@localhost")
WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("BOSSKEY_WEBHOOK_TIMEOUT_SECONDS", "10"))

DEFAULT_NOTIFICATION_POLICY = {
    "global_thresholds": {
        "reminder_days_before_sla": 1,
        "escalation_tiers": [1, 3, 7],
    },
    "client_threshold_overrides": {},
    "routing": {
        "REMINDER": {"roles": ["proposal_manager"]},
        "SLA_BREACH": {"roles": ["proposal_manager", "executive_approver"]},
        "BLOCKER_ESCALATION": {"roles": ["compliance_lead", "review_lead", "executive_approver"]},
        "SLA_ESCALATION": {"roles": ["executive_approver", "admin"]},
    },
}


def _load_notification_policy() -> dict:
    raw = os.getenv("BOSSKEY_NOTIFICATION_POLICY_JSON", "").strip()
    if not raw:
        return DEFAULT_NOTIFICATION_POLICY
    try:
        policy = json.loads(raw)
        if not isinstance(policy, dict):
            return DEFAULT_NOTIFICATION_POLICY
        return policy
    except json.JSONDecodeError:
        return DEFAULT_NOTIFICATION_POLICY


NOTIFICATION_POLICY = _load_notification_policy()
