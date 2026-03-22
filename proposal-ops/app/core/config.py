from pathlib import Path
import os
import json


BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
ENV_FILE_OVERRIDE_KEYS = {
    "OPENAI_API_KEY",
    "BOSSKEY_OPENAI_MODEL",
    "BOSSKEY_OPENAI_TIMEOUT_SECONDS",
    "BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS",
    "BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS",
    "BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS",
    "BOSSKEY_OPENAI_MAX_TIMEOUT_SECONDS",
    "BOSSKEY_OPENAI_ENABLE_TOKEN_GUARDS",
    "BOSSKEY_OPENAI_ESTIMATED_CHARS_PER_TOKEN",
    "BOSSKEY_OPENAI_GLOBAL_MAX_ESTIMATED_INPUT_TOKENS",
    "BOSSKEY_OPENAI_GLOBAL_MAX_OUTPUT_TOKENS",
    "BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK",
    "BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK",
    "BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS",
}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key in os.environ and key not in ENV_FILE_OVERRIDE_KEYS:
            continue
        cleaned = value.strip().strip("'").strip('"')
        os.environ[key] = cleaned


for _env_path in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
    _load_env_file(_env_path)


def _path_from_env(env_var: str, default: Path) -> Path:
    raw = os.getenv(env_var, "").strip()
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate
    return BASE_DIR / candidate


def _int_from_env(env_var: str, default: int) -> int:
    raw = os.getenv(env_var, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


ARTIFACTS_DIR = _path_from_env("BOSSKEY_ARTIFACTS_DIR", BASE_DIR / ".artifacts")
DB_PATH = _path_from_env("BOSSKEY_DB_PATH", ARTIFACTS_DIR / "bosskey_pursuit_os.sqlite3")
DB_DIR = DB_PATH.parent
DB_DIR.mkdir(parents=True, exist_ok=True)
RFP_SOURCE_STORAGE_DIR = _path_from_env("BOSSKEY_RFP_SOURCE_STORAGE_DIR", DB_DIR / "rfp_source_documents")
RFP_SOURCE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
GATE_POLICY_PACK = os.getenv("BOSSKEY_GATE_POLICY_PACK", "default")
APPROVAL_SIGNING_SECRET = os.getenv("BOSSKEY_APPROVAL_SIGNING_SECRET", "dev-signing-secret")
SESSION_SECRET = os.getenv("BOSSKEY_SESSION_SECRET", "dev-session-secret")
SECRET_STORE_PATH = _path_from_env("BOSSKEY_SECRET_STORE_PATH", DB_DIR / "secrets.json")
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
BOSSKEY_OPENAI_MODEL = os.getenv("BOSSKEY_OPENAI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
BOSSKEY_OPENAI_TIMEOUT_SECONDS = _int_from_env("BOSSKEY_OPENAI_TIMEOUT_SECONDS", 45)
BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS = _int_from_env(
    "BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS", max(BOSSKEY_OPENAI_TIMEOUT_SECONDS, 120)
)
BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS = _int_from_env(
    "BOSSKEY_OPENAI_SKELETON_TIMEOUT_SECONDS", max(BOSSKEY_OPENAI_TIMEOUT_SECONDS, 180)
)
BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS = _int_from_env(
    "BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS", max(BOSSKEY_OPENAI_TIMEOUT_SECONDS, 300)
)
BOSSKEY_OPENAI_MAX_TIMEOUT_SECONDS = _int_from_env(
    "BOSSKEY_OPENAI_MAX_TIMEOUT_SECONDS", max(BOSSKEY_OPENAI_DRAFT_TIMEOUT_SECONDS, 600)
)
BOSSKEY_OPENAI_ENABLE_TOKEN_GUARDS = os.getenv("BOSSKEY_OPENAI_ENABLE_TOKEN_GUARDS", "true").lower() == "true"
BOSSKEY_OPENAI_ESTIMATED_CHARS_PER_TOKEN = max(_int_from_env("BOSSKEY_OPENAI_ESTIMATED_CHARS_PER_TOKEN", 4), 1)
BOSSKEY_OPENAI_GLOBAL_MAX_ESTIMATED_INPUT_TOKENS = _int_from_env(
    "BOSSKEY_OPENAI_GLOBAL_MAX_ESTIMATED_INPUT_TOKENS", 20_000
)
BOSSKEY_OPENAI_GLOBAL_MAX_OUTPUT_TOKENS = _int_from_env(
    "BOSSKEY_OPENAI_GLOBAL_MAX_OUTPUT_TOKENS", 8_000
)
BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK = (
    os.getenv("BOSSKEY_PROPOSAL_BUILDER_ALLOW_CACHED_DEMO_FALLBACK", "true").lower() == "true"
)
BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK = (
    os.getenv("BOSSKEY_PROPOSAL_BUILDER_ALLOW_LIVE_STAGE_FALLBACK", "false").lower() == "true"
)
BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS = os.getenv("BOSSKEY_ENABLE_COLOR_TEAM_REVIEWS", "false").lower() == "true"
EXPORTS_DIR = _path_from_env("BOSSKEY_EXPORTS_DIR", ARTIFACTS_DIR / "exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

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
