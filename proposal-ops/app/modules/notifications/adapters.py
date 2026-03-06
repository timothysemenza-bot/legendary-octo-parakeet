import json
import smtplib
import socket
from dataclasses import dataclass
from urllib import error as url_error
from urllib import request as url_request

from app.core.config import (
    NOTIFICATION_PROVIDER_MODE,
    NOTIFICATION_WEBHOOK_URL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SENDER,
    SMTP_USERNAME,
    SMTP_USE_TLS,
    WEBHOOK_TIMEOUT_SECONDS,
)


@dataclass
class AdapterResult:
    success: bool
    response: str = ""
    error: str = ""
    error_code: str | None = None
    retryable: bool = False


def classify_delivery_error(message: str) -> tuple[str, bool]:
    lowered = message.lower()
    if any(token in lowered for token in ["timed out", "timeout", "temporary failure", "connection reset", "connection refused", "dns"]):
        return ("TRANSIENT_NETWORK", True)
    if any(token in lowered for token in ["auth", "authentication", "credential", "login"]):
        return ("AUTH_FAILURE", False)
    if any(token in lowered for token in ["429", "rate limit", "too many requests"]):
        return ("RATE_LIMIT", True)
    if any(token in lowered for token in ["invalid", "bad request", "malformed", "unsupported", "recipient"]):
        return ("VALIDATION", False)
    return ("UNKNOWN", True)


def _mock_adapter(channel: str, target: str, notification_type: str) -> AdapterResult:
    if channel == "console":
        return AdapterResult(success=True, response=f"console:{target}:{notification_type}")
    if channel == "email":
        if "fail" in target.lower() or "invalid" in target.lower():
            return AdapterResult(
                success=False,
                error="Simulated invalid recipient",
                error_code="VALIDATION",
                retryable=False,
            )
        return AdapterResult(success=True, response=f"email:{target}:{notification_type}")
    if channel == "webhook":
        if "fail" in target.lower():
            return AdapterResult(
                success=False,
                error="Simulated webhook transient failure",
                error_code="TRANSIENT_NETWORK",
                retryable=True,
            )
        return AdapterResult(success=True, response=f"webhook:{target}:{notification_type}")
    return AdapterResult(success=False, error=f"Unsupported channel '{channel}'", error_code="VALIDATION", retryable=False)


def _send_email_real(target: str, subject: str, body: str) -> AdapterResult:
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=WEBHOOK_TIMEOUT_SECONDS) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            message = f"From: {SMTP_SENDER}\r\nTo: {target}\r\nSubject: {subject}\r\n\r\n{body}"
            smtp.sendmail(SMTP_SENDER, [target], message)
        return AdapterResult(success=True, response=f"smtp:{target}:sent")
    except (smtplib.SMTPException, socket.error, TimeoutError) as exc:
        code, retryable = classify_delivery_error(str(exc))
        return AdapterResult(success=False, error=str(exc), error_code=code, retryable=retryable)


def _send_webhook_real(target: str, payload: dict) -> AdapterResult:
    try:
        req = url_request.Request(
            target or NOTIFICATION_WEBHOOK_URL,
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with url_request.urlopen(req, timeout=WEBHOOK_TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8", errors="ignore")
        if 200 <= status_code < 300:
            return AdapterResult(success=True, response=f"http:{status_code}:{body[:120]}")
        code, retryable = classify_delivery_error(str(status_code))
        return AdapterResult(success=False, error=f"HTTP {status_code}", error_code=code, retryable=retryable)
    except (url_error.URLError, url_error.HTTPError, TimeoutError, socket.error) as exc:
        code, retryable = classify_delivery_error(str(exc))
        return AdapterResult(success=False, error=str(exc), error_code=code, retryable=retryable)


def dispatch_notification(channel: str, target: str, *, subject: str, body: str, payload: dict) -> AdapterResult:
    normalized = channel.lower().strip()
    if NOTIFICATION_PROVIDER_MODE != "real":
        return _mock_adapter(normalized, target, payload.get("notification_type", "UNKNOWN"))
    if normalized == "console":
        return AdapterResult(success=True, response=f"console:{target}:{payload.get('notification_type', 'UNKNOWN')}")
    if normalized == "email":
        return _send_email_real(target, subject, body)
    if normalized == "webhook":
        return _send_webhook_real(target, payload)
    return AdapterResult(success=False, error=f"Unsupported channel '{channel}'", error_code="VALIDATION", retryable=False)
