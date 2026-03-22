import pytest

from app.modules.proposal_builder.openai_client import OpenAIStructuredOutputError, ProposalBuilderOpenAIClient


def test_openai_client_blocks_oversized_request_before_http() -> None:
    client = ProposalBuilderOpenAIClient(api_key="test-key", timeout_seconds=5)

    with pytest.raises(OpenAIStructuredOutputError, match="usage safeguard blocked 'extract'"):
        client.generate_json_with_metadata(
            system_prompt="Summarize the request.",
            user_payload={"source_excerpt": "x" * 8_000},
            schema_name="demo_schema",
            schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                },
            },
            max_estimated_input_tokens=25,
            guardrail_label="extract",
        )


def test_openai_client_sends_max_output_tokens_and_returns_guardrail_metadata(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "id": "resp_demo",
                "status": "completed",
                "output_text": '{"summary":"ok"}',
                "usage": {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160},
            }

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            captured["timeout"] = kwargs.get("timeout")

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):  # type: ignore[no-untyped-def]
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _FakeResponse()

    monkeypatch.setattr("app.modules.proposal_builder.openai_client.httpx.Client", _FakeClient)

    client = ProposalBuilderOpenAIClient(api_key="test-key", timeout_seconds=5)
    parsed, metadata = client.generate_json_with_metadata(
        system_prompt="Summarize the request.",
        user_payload={"source_excerpt": "Short excerpt."},
        schema_name="demo_schema",
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
        },
        max_output_tokens=321,
        max_estimated_input_tokens=5_000,
        guardrail_label="draft",
    )

    assert parsed == {"summary": "ok"}
    assert metadata["response_id"] == "resp_demo"
    assert metadata["max_output_tokens"] == 321
    assert metadata["max_estimated_input_tokens"] == 5_000
    assert int(metadata["estimated_input_tokens"]) > 0
    assert captured["json"]["max_output_tokens"] == 321


def test_openai_client_recovers_json_from_markdown_wrapped_output(monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "id": "resp_demo",
                "status": "completed",
                "output_text": 'Here is the JSON you requested:\n```json\n{"summary":"ok"}\n```',
                "usage": {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160},
            }

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            pass

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):  # type: ignore[no-untyped-def]
            return _FakeResponse()

    monkeypatch.setattr("app.modules.proposal_builder.openai_client.httpx.Client", _FakeClient)

    client = ProposalBuilderOpenAIClient(api_key="test-key", timeout_seconds=5)
    parsed, metadata = client.generate_json_with_metadata(
        system_prompt="Summarize the request.",
        user_payload={"source_excerpt": "Short excerpt."},
        schema_name="demo_schema",
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
        },
        max_output_tokens=128,
        max_estimated_input_tokens=5_000,
        guardrail_label="extract",
    )

    assert parsed == {"summary": "ok"}
    assert metadata["response_id"] == "resp_demo"


def test_openai_client_coerces_single_object_list_root(monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "id": "resp_demo",
                "status": "completed",
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "parsed": [{"summary": "ok"}],
                            }
                        ]
                    }
                ],
                "usage": {"input_tokens": 120, "output_tokens": 40, "total_tokens": 160},
            }

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            pass

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):  # type: ignore[no-untyped-def]
            return _FakeResponse()

    monkeypatch.setattr("app.modules.proposal_builder.openai_client.httpx.Client", _FakeClient)

    client = ProposalBuilderOpenAIClient(api_key="test-key", timeout_seconds=5)
    parsed = client.generate_json(
        system_prompt="Summarize the request.",
        user_payload={"source_excerpt": "Short excerpt."},
        schema_name="demo_schema",
        schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
        },
        max_output_tokens=128,
        max_estimated_input_tokens=5_000,
        guardrail_label="extract",
    )

    assert parsed == {"summary": "ok"}
