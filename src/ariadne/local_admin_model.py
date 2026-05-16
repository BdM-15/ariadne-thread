from __future__ import annotations

import json
from enum import StrEnum
from typing import Protocol
from urllib import error, request

from pydantic import BaseModel, field_validator

from ariadne.config import LocalAdminModelSettings


class LocalAdminModelAssistStatus(StrEnum):
    DISABLED = "disabled"
    USED = "used"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"


class LocalAdminDraftSuggestion(BaseModel):
    inferred_claims: tuple[str, ...] = ()
    likely_risks: tuple[str, ...] = ()
    discriminator_candidates: tuple[str, ...] = ()
    packet_implications: tuple[str, ...] = ()
    action_candidates: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    follow_up_questions: tuple[str, ...] = ()
    confidence_notes: tuple[str, ...] = ()

    @field_validator("*", mode="before")
    @classmethod
    def validate_string_sequence(cls, value):
        if value is None:
            return ()
        if not isinstance(value, list | tuple):
            raise ValueError("local admin model suggestion fields must be arrays")
        return tuple(str(item).strip() for item in value if str(item).strip())

    @property
    def has_content(self) -> bool:
        return any(
            (
                self.inferred_claims,
                self.likely_risks,
                self.discriminator_candidates,
                self.packet_implications,
                self.action_candidates,
                self.gaps,
                self.follow_up_questions,
                self.confidence_notes,
            )
        )


class LocalAdminDraftAssist(BaseModel):
    status: LocalAdminModelAssistStatus
    used: bool = False
    model: str | None = None
    reason: str
    suggestion: LocalAdminDraftSuggestion | None = None


class LocalAdminModelClient(Protocol):
    def generate_json(
        self,
        *,
        prompt: str,
        model_name: str,
        base_url: str,
        timeout_seconds: int,
    ) -> dict[str, object]: ...


class OllamaLocalAdminModelClient:
    def generate_json(
        self,
        *,
        prompt: str,
        model_name: str,
        base_url: str,
        timeout_seconds: int,
    ) -> dict[str, object]:
        payload = json.dumps(
            {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        endpoint = base_url.rstrip("/") + "/api/generate"
        req = request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, error.URLError) as exc:
            raise TimeoutError(str(exc)) from exc

        model_response = body.get("response", body)
        if isinstance(model_response, str):
            return json.loads(model_response)
        if isinstance(model_response, dict):
            return model_response
        raise ValueError("local admin model returned unsupported response shape")


def request_local_admin_draft_assist(
    content: str,
    *,
    settings: LocalAdminModelSettings,
    client: LocalAdminModelClient | None = None,
) -> LocalAdminDraftAssist:
    if not settings.enabled:
        return LocalAdminDraftAssist(
            status=LocalAdminModelAssistStatus.DISABLED,
            used=False,
            model=settings.model,
            reason="local admin model disabled",
        )

    adapter = client or OllamaLocalAdminModelClient()
    try:
        response = adapter.generate_json(
            prompt=_draft_support_prompt(content),
            model_name=settings.model,
            base_url=settings.ollama_base_url,
            timeout_seconds=settings.timeout_seconds,
        )
        suggestion = LocalAdminDraftSuggestion.model_validate(response)
        if not suggestion.has_content:
            raise ValueError("local admin model returned no draft support")
    except Exception as exc:
        status = (
            LocalAdminModelAssistStatus.INVALID_RESPONSE
            if isinstance(exc, (ValueError, TypeError, json.JSONDecodeError))
            else LocalAdminModelAssistStatus.UNAVAILABLE
        )
        return LocalAdminDraftAssist(
            status=status,
            used=False,
            model=settings.model,
            reason=str(exc),
        )

    return LocalAdminDraftAssist(
        status=LocalAdminModelAssistStatus.USED,
        used=True,
        model=settings.model,
        reason="local admin model returned draft support",
        suggestion=suggestion,
    )


def _draft_support_prompt(content: str) -> str:
    return "\n".join(
        (
            "You support Ariadne Quick Capture as a local admin model.",
            "Return strict JSON with array fields only:",
            "inferred_claims, likely_risks, discriminator_candidates,",
            "packet_implications, action_candidates, gaps, follow_up_questions,",
            "confidence_notes.",
            "Do not write trusted evidence. Draft reviewable support only.",
            "Raw capture material:",
            content,
        )
    )