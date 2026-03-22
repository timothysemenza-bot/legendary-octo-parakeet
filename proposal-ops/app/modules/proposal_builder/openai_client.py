from __future__ import annotations

import json
import math
import time
from typing import Any

import httpx

from app.core.config import (
    BOSSKEY_OPENAI_ENABLE_TOKEN_GUARDS,
    BOSSKEY_OPENAI_ESTIMATED_CHARS_PER_TOKEN,
    BOSSKEY_OPENAI_MODEL,
    BOSSKEY_OPENAI_TIMEOUT_SECONDS,
    OPENAI_API_KEY,
)


class OpenAIStructuredOutputError(RuntimeError):
    pass


class ProposalBuilderOpenAIClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
        chars_per_token: int | None = None,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = (api_key or OPENAI_API_KEY).strip()
        self.model = (model or BOSSKEY_OPENAI_MODEL).strip() or "gpt-5.4"
        self.timeout_seconds = timeout_seconds or BOSSKEY_OPENAI_TIMEOUT_SECONDS
        self.chars_per_token = max(chars_per_token or BOSSKEY_OPENAI_ESTIMATED_CHARS_PER_TOKEN, 1)
        self.base_url = base_url.rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
        max_estimated_input_tokens: int | None = None,
        guardrail_label: str | None = None,
    ) -> dict[str, Any]:
        parsed, _metadata = self.generate_json_with_metadata(
            system_prompt=system_prompt,
            user_payload=user_payload,
            schema_name=schema_name,
            schema=schema,
            max_output_tokens=max_output_tokens,
            max_estimated_input_tokens=max_estimated_input_tokens,
            guardrail_label=guardrail_label,
        )
        return parsed

    def generate_json_with_metadata(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        reasoning_effort: str | None = None,
        background: bool = False,
        poll_interval_seconds: int = 3,
        max_wait_seconds: int | None = None,
        max_output_tokens: int | None = None,
        max_estimated_input_tokens: int | None = None,
        guardrail_label: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not self.available:
            raise OpenAIStructuredOutputError("OPENAI_API_KEY is not configured.")

        strict_schema = self._strict_json_schema(schema)
        user_text = json.dumps(user_payload, indent=2, default=str)
        estimated_input_tokens = self._estimate_request_input_tokens(
            system_prompt=system_prompt,
            user_text=user_text,
            schema=strict_schema,
        )
        self._enforce_token_guardrails(
            estimated_input_tokens=estimated_input_tokens,
            max_estimated_input_tokens=max_estimated_input_tokens,
            guardrail_label=guardrail_label or schema_name,
        )
        body: dict[str, Any] = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_text}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": strict_schema,
                    "strict": True,
                }
            },
        }
        if reasoning_effort:
            body["reasoning"] = {"effort": reasoning_effort}
        if max_output_tokens:
            body["max_output_tokens"] = max(int(max_output_tokens), 1)
        if background:
            body["background"] = True
            body["store"] = True
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/responses", headers=headers, json=body)
                payload = self._raise_for_payload(response)
                if background:
                    payload = self._poll_background_response(
                        client=client,
                        headers=headers,
                        response_id=str(payload.get("id", "")).strip(),
                        poll_interval_seconds=poll_interval_seconds,
                        max_wait_seconds=max_wait_seconds or max(self.timeout_seconds * 4, 600),
                    )
        except httpx.TimeoutException as exc:
            raise OpenAIStructuredOutputError(f"OpenAI request timed out after {self.timeout_seconds} seconds.") from exc
        except httpx.HTTPError as exc:
            raise OpenAIStructuredOutputError(f"OpenAI request failed before a response was returned: {exc}") from exc
        parsed = self._extract_output_json(payload)
        if not isinstance(parsed, dict):
            raise OpenAIStructuredOutputError("OpenAI response JSON root must be an object.")
        metadata = {
            "response_id": payload.get("id"),
            "status": payload.get("status"),
            "usage": payload.get("usage", {}),
            "background": background,
            "reasoning_effort": reasoning_effort,
            "estimated_input_tokens": estimated_input_tokens,
            "max_estimated_input_tokens": max_estimated_input_tokens,
            "max_output_tokens": max_output_tokens,
        }
        return parsed, metadata

    def _estimate_request_input_tokens(self, *, system_prompt: str, user_text: str, schema: dict[str, Any]) -> int:
        schema_text = json.dumps(schema, separators=(",", ":"), default=str)
        approximate_chars = len(system_prompt) + len(user_text) + len(schema_text) + 300
        return max(math.ceil(approximate_chars / self.chars_per_token), 1)

    def _enforce_token_guardrails(
        self,
        *,
        estimated_input_tokens: int,
        max_estimated_input_tokens: int | None,
        guardrail_label: str,
    ) -> None:
        if not BOSSKEY_OPENAI_ENABLE_TOKEN_GUARDS or not max_estimated_input_tokens:
            return
        if estimated_input_tokens <= max_estimated_input_tokens:
            return
        raise OpenAIStructuredOutputError(
            f"OpenAI usage safeguard blocked '{guardrail_label}': estimated input tokens "
            f"{estimated_input_tokens:,} exceed the configured cap of {max_estimated_input_tokens:,}. "
            "Reduce the payload size or split the work into smaller updates."
        )

    def _raise_for_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:600]
            raise OpenAIStructuredOutputError(f"OpenAI request failed: {detail}") from exc
        return response.json()

    def _poll_background_response(
        self,
        *,
        client: httpx.Client,
        headers: dict[str, str],
        response_id: str,
        poll_interval_seconds: int,
        max_wait_seconds: int,
    ) -> dict[str, Any]:
        if not response_id:
            raise OpenAIStructuredOutputError("OpenAI background response did not return an id.")
        deadline = time.monotonic() + max_wait_seconds
        while True:
            response = client.get(f"{self.base_url}/responses/{response_id}", headers=headers)
            payload = self._raise_for_payload(response)
            status = str(payload.get("status", "")).lower()
            if status in {"completed", "succeeded"}:
                return payload
            if status in {"failed", "cancelled", "incomplete", "expired"}:
                raise OpenAIStructuredOutputError(f"OpenAI background response ended with status '{status}'.")
            if time.monotonic() >= deadline:
                raise OpenAIStructuredOutputError(
                    f"OpenAI background response timed out after {max_wait_seconds} seconds."
                )
            time.sleep(max(poll_interval_seconds, 1))

    def _strict_json_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        def transform(node: Any) -> Any:
            if isinstance(node, dict):
                updated = {key: transform(value) for key, value in node.items()}
                if updated.get("type") == "object":
                    updated.setdefault("additionalProperties", False)
                    properties = updated.get("properties")
                    if isinstance(properties, dict):
                        updated["required"] = list(properties.keys())
                return updated
            if isinstance(node, list):
                return [transform(item) for item in node]
            return node

        return transform(schema)

    def _extract_output_json(self, payload: dict[str, Any]) -> Any:
        direct = payload.get("output_parsed")
        if direct is None:
            direct = payload.get("parsed")
        direct_object = self._coerce_root_object_candidate(direct)
        if direct_object is not None:
            return direct_object
        direct_list_fallback = direct if direct is not None else None

        string_candidates: list[str] = []
        list_candidates: list[Any] = []
        top_level = payload.get("output_text")
        if isinstance(top_level, str) and top_level.strip():
            string_candidates.append(top_level)

        for item in payload.get("output", []):
            if not isinstance(item, dict):
                continue
            direct_item = item.get("parsed")
            direct_object = self._coerce_root_object_candidate(direct_item)
            if direct_object is not None:
                return direct_object
            if direct_item is not None:
                list_candidates.append(direct_item)
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                for key in ("parsed", "json", "arguments", "value", "text"):
                    candidate = content.get(key)
                    direct_object = self._coerce_root_object_candidate(candidate)
                    if direct_object is not None:
                        return direct_object
                    if isinstance(candidate, list):
                        list_candidates.append(candidate)
                    if isinstance(candidate, str) and candidate.strip():
                        string_candidates.append(candidate)

        for candidate in string_candidates:
            parsed = self._try_parse_json_candidate(candidate)
            if parsed is not None:
                return parsed

        for candidate in ([direct_list_fallback] if direct_list_fallback is not None else []) + list_candidates:
            direct_object = self._coerce_root_object_candidate(candidate)
            if direct_object is not None:
                return direct_object

        text = self._extract_output_text(payload)
        if not text:
            raise OpenAIStructuredOutputError("OpenAI response did not include structured output text.")
        raise OpenAIStructuredOutputError("OpenAI response returned invalid JSON.")

    def _coerce_root_object_candidate(self, candidate: Any) -> dict[str, Any] | None:
        if isinstance(candidate, dict):
            return candidate
        if isinstance(candidate, list) and len(candidate) == 1 and isinstance(candidate[0], dict):
            return candidate[0]
        return None

    def _try_parse_json_candidate(self, raw_text: str) -> Any | None:
        cleaned = raw_text.strip()
        if not cleaned:
            return None

        fence_stripped = self._strip_markdown_fences(cleaned)
        decoder = json.JSONDecoder()
        for candidate in (cleaned, fence_stripped):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
            recovered = self._extract_embedded_json(candidate, decoder=decoder)
            if recovered is not None:
                return recovered
        return None

    def _strip_markdown_fences(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if not lines:
            return stripped
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _extract_embedded_json(self, text: str, *, decoder: json.JSONDecoder) -> Any | None:
        for index, char in enumerate(text):
            if char not in "{[":
                continue
            try:
                parsed, _end = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            return parsed
        return None

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        top_level = payload.get("output_text")
        if isinstance(top_level, str) and top_level.strip():
            return top_level

        fragments: list[str] = []
        for item in payload.get("output", []):
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                if isinstance(content.get("text"), str) and content["text"].strip():
                    fragments.append(content["text"])
                elif isinstance(content.get("value"), str) and content["value"].strip():
                    fragments.append(content["value"])
        return "\n".join(fragments).strip()
