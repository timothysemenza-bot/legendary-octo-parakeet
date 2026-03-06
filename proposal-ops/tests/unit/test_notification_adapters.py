from app.modules.notifications.adapters import classify_delivery_error, dispatch_notification


def test_classify_delivery_error_transient_and_validation() -> None:
    code, retryable = classify_delivery_error("connection timed out")
    assert code == "TRANSIENT_NETWORK"
    assert retryable is True

    code2, retryable2 = classify_delivery_error("invalid recipient address")
    assert code2 == "VALIDATION"
    assert retryable2 is False


def test_mock_adapter_email_failure_non_retryable() -> None:
    result = dispatch_notification(
        "email",
        "fail.user@example.test",
        subject="Test",
        body="Body",
        payload={"notification_type": "SLA_BREACH"},
    )
    assert result.success is False
    assert result.error_code == "VALIDATION"
    assert result.retryable is False
