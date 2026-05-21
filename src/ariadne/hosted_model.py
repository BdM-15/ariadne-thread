from __future__ import annotations

import json
from enum import StrEnum
from typing import Protocol
from urllib import error, request

from pydantic import BaseModel

from ariadne.config import HostedModelSettings


class HostedModelAssistStatus(StrEnum):
    DISABLED = "disabled"
    MISSING_CREDENTIALS = "missing_credentials"
    USED = "used"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"


class HostedModelPurpose(StrEnum):
    CAPTURE_NEED_ANALYSIS = "capture_need_analysis"
    PACKET_SYNTHESIS_SUPPORT = "packet_synthesis_support"
    CALL_ENGAGEMENT_PREP = "call_engagement_prep"
    VALUE_PROPOSITION_MESSAGING = "value_proposition_messaging"
    RESEARCH_BRIEF_CREATION = "research_brief_creation"
    OUTPUT_REVIEW_SUMMARY = "output_review_summary"
    ARTIFACT_BLOCK_DRAFTING = "artifact_block_drafting"


class HostedModelAssist(BaseModel):
    status: HostedModelAssistStatus
    used: bool = False
    provider: str
    model: str
    purpose: HostedModelPurpose
    reason: str
    draft_text: str | None = None


class HostedModelClient(Protocol):
    def generate_text(
        self,
        *,
        prompt: str,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float,
        max_output_tokens: int,
        timeout_seconds: int,
    ) -> str: ...


class OpenAICompatibleHostedModelClient:
    def generate_text(
        self,
        *,
        prompt: str,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float,
        max_output_tokens: int,
        timeout_seconds: int,
    ) -> str:
        endpoint = _chat_completions_endpoint(provider)
        payload = json.dumps(
            {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You support Ariadne capture workflows. Return concise "
                            "reviewable draft support only. Do not claim trusted facts."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_output_tokens,
            }
        ).encode("utf-8")
        req = request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, error.URLError) as exc:
            raise TimeoutError(str(exc)) from exc

        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("hosted model returned no choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("hosted model returned empty content")
        return content.strip()


def request_hosted_model_assist(
    content: str,
    *,
    purpose: HostedModelPurpose,
    settings: HostedModelSettings,
    client: HostedModelClient | None = None,
) -> HostedModelAssist:
    model = _model_for_purpose(purpose, settings)
    provider = settings.provider.lower().strip()
    if not settings.enabled:
        return HostedModelAssist(
            status=HostedModelAssistStatus.DISABLED,
            used=False,
            provider=provider,
            model=model,
            purpose=purpose,
            reason="hosted reasoning model disabled",
        )
    api_key = _api_key_for_provider(provider, settings)
    if not api_key:
        return HostedModelAssist(
            status=HostedModelAssistStatus.MISSING_CREDENTIALS,
            used=False,
            provider=provider,
            model=model,
            purpose=purpose,
            reason=f"missing API key for hosted provider {provider}",
        )

    adapter = client or OpenAICompatibleHostedModelClient()
    try:
        draft_text = adapter.generate_text(
            prompt=_reviewable_support_prompt(content, purpose),
            provider=provider,
            model_name=model,
            api_key=api_key,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            timeout_seconds=settings.timeout_seconds,
        )
        if not draft_text.strip():
            raise ValueError("hosted model returned empty draft support")
    except Exception as exc:
        status = (
            HostedModelAssistStatus.INVALID_RESPONSE
            if isinstance(exc, (ValueError, TypeError, json.JSONDecodeError))
            else HostedModelAssistStatus.UNAVAILABLE
        )
        return HostedModelAssist(
            status=status,
            used=False,
            provider=provider,
            model=model,
            purpose=purpose,
            reason=str(exc),
        )

    return HostedModelAssist(
        status=HostedModelAssistStatus.USED,
        used=True,
        provider=provider,
        model=model,
        purpose=purpose,
        reason="hosted model returned reviewable draft support",
        draft_text=draft_text,
    )


def _model_for_purpose(
    purpose: HostedModelPurpose,
    settings: HostedModelSettings,
) -> str:
    if purpose in {
        HostedModelPurpose.OUTPUT_REVIEW_SUMMARY,
        HostedModelPurpose.CALL_ENGAGEMENT_PREP,
    } and settings.daily_model:
        return settings.daily_model
    return settings.reasoning_model


def _api_key_for_provider(provider: str, settings: HostedModelSettings) -> str | None:
    if provider == "xai":
        return settings.xai_api_key
    if provider == "openai":
        return settings.openai_api_key
    if provider == "google":
        return settings.google_api_key
    return None


def _chat_completions_endpoint(provider: str) -> str:
    if provider == "xai":
        return "https://api.x.ai/v1/chat/completions"
    if provider == "openai":
        return "https://api.openai.com/v1/chat/completions"
    raise ValueError(f"unsupported hosted model provider: {provider}")


def _reviewable_support_prompt(content: str, purpose: HostedModelPurpose) -> str:
    return "\n".join(
        (
            f"Ariadne hosted model purpose: {purpose.value}.",
            "Prepare reviewable capture support only.",
            "Include assumptions, gaps, source limits, and reviewer next step.",
            "Do not write trusted packet answers, evidence, actions, or artifacts.",
            "Input:",
            content,
        )
    )