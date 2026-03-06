from dataclasses import dataclass

import httpx


@dataclass
class OutlookFetchResult:
    messages: list[dict]
    next_cursor: str | None
    errors: list[str]


@dataclass
class OutlookTokenRefreshResult:
    access_token: str | None
    expires_in: int | None
    refresh_token: str | None
    errors: list[str]


def fetch_outlook_messages(config: dict) -> OutlookFetchResult:
    # Test/dev path: deterministic mock pages from config.
    mock_pages = config.get("graph_mock_pages", [])
    if isinstance(mock_pages, list) and mock_pages:
        cursor = str(config.get("graph_cursor", "START"))
        page = None
        for candidate in mock_pages:
            if not isinstance(candidate, dict):
                continue
            candidate_cursor = str(candidate.get("cursor", "START"))
            if candidate_cursor == cursor:
                page = candidate
                break
        if page is None:
            return OutlookFetchResult(messages=[], next_cursor=None, errors=[])
        messages = page.get("messages", [])
        if not isinstance(messages, list):
            return OutlookFetchResult(messages=[], next_cursor=None, errors=["graph_mock_pages.messages must be an array"])
        next_cursor = page.get("next_cursor")
        return OutlookFetchResult(messages=messages, next_cursor=str(next_cursor) if next_cursor else None, errors=[])

    access_token = str(config.get("access_token", "")).strip()
    mailbox = str(config.get("mailbox", "")).strip()
    if not access_token:
        return OutlookFetchResult(messages=[], next_cursor=None, errors=["OUTLOOK_GRAPH access_token is required for live sync"])
    if not mailbox:
        return OutlookFetchResult(messages=[], next_cursor=None, errors=["OUTLOOK_GRAPH mailbox is required for live sync"])

    next_link = str(config.get("graph_next_link", "")).strip()
    if next_link:
        request_url = next_link
    else:
        request_url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages?$top=25"

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(request_url, headers=headers)
        if response.status_code >= 400:
            return OutlookFetchResult(
                messages=[],
                next_cursor=None,
                errors=[f"Graph API returned HTTP {response.status_code}"],
            )
        payload = response.json()
    except Exception as exc:
        return OutlookFetchResult(messages=[], next_cursor=None, errors=[f"Graph API request failed: {exc}"])

    raw_messages = payload.get("value", [])
    if not isinstance(raw_messages, list):
        return OutlookFetchResult(messages=[], next_cursor=None, errors=["Graph response missing message list"])

    messages: list[dict] = []
    for row in raw_messages:
        if not isinstance(row, dict):
            continue
        from_block = row.get("from", {}) if isinstance(row.get("from"), dict) else {}
        email_block = from_block.get("emailAddress", {}) if isinstance(from_block.get("emailAddress"), dict) else {}
        body_block = row.get("body", {}) if isinstance(row.get("body"), dict) else {}
        messages.append(
            {
                "id": row.get("id"),
                "subject": row.get("subject", ""),
                "from_address": email_block.get("address", ""),
                "body": body_block.get("content", ""),
                "auto_apply": False,
            }
        )
    next_cursor = payload.get("@odata.nextLink")
    return OutlookFetchResult(messages=messages, next_cursor=str(next_cursor) if next_cursor else None, errors=[])


def refresh_outlook_token(config: dict) -> OutlookTokenRefreshResult:
    # Test/dev path for deterministic refresh behavior.
    mock_refresh = config.get("graph_mock_refresh", {})
    if isinstance(mock_refresh, dict) and mock_refresh:
        if mock_refresh.get("enabled") is False:
            return OutlookTokenRefreshResult(access_token=None, expires_in=None, refresh_token=None, errors=["Mock refresh disabled"])
        token = str(mock_refresh.get("access_token", "")).strip()
        if not token:
            return OutlookTokenRefreshResult(access_token=None, expires_in=None, refresh_token=None, errors=["Mock refresh missing access_token"])
        expires_in = int(mock_refresh.get("expires_in", 3600))
        refresh_token = str(mock_refresh.get("refresh_token", "")).strip() or None
        return OutlookTokenRefreshResult(
            access_token=token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            errors=[],
        )

    tenant_id = str(config.get("tenant_id", "")).strip()
    client_id = str(config.get("client_id", "")).strip()
    refresh_token_value = str(config.get("refresh_token", "")).strip()
    client_secret = str(config.get("client_secret", "")).strip()
    if not tenant_id or not client_id or not refresh_token_value:
        return OutlookTokenRefreshResult(
            access_token=None,
            expires_in=None,
            refresh_token=None,
            errors=["Missing tenant_id, client_id, or refresh_token for live refresh"],
        )

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    form_data = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
        "scope": "https://graph.microsoft.com/.default offline_access",
    }
    if client_secret:
        form_data["client_secret"] = client_secret
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(token_url, data=form_data)
        if response.status_code >= 400:
            return OutlookTokenRefreshResult(
                access_token=None,
                expires_in=None,
                refresh_token=None,
                errors=[f"Token refresh failed HTTP {response.status_code}"],
            )
        payload = response.json()
    except Exception as exc:
        return OutlookTokenRefreshResult(
            access_token=None,
            expires_in=None,
            refresh_token=None,
            errors=[f"Token refresh request failed: {exc}"],
        )

    access_token = str(payload.get("access_token", "")).strip()
    if not access_token:
        return OutlookTokenRefreshResult(
            access_token=None,
            expires_in=None,
            refresh_token=None,
            errors=["Token refresh response missing access_token"],
        )
    expires_in_raw = payload.get("expires_in", 3600)
    try:
        expires_in = int(expires_in_raw)
    except Exception:
        expires_in = 3600
    refreshed_token = str(payload.get("refresh_token", "")).strip() or None
    return OutlookTokenRefreshResult(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refreshed_token,
        errors=[],
    )
