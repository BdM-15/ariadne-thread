from ariadne.config import LocalAdminModelSettings
from ariadne.local_admin_model import (
    LocalAdminDraftSuggestion,
    LocalAdminModelAssistStatus,
    request_local_admin_draft_assist,
)


class RecordingLocalModelClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response or {}
        self.error = error
        self.calls = []

    def generate_json(self, *, prompt, model_name, base_url, timeout_seconds):
        self.calls.append(
            {
                "prompt": prompt,
                "model_name": model_name,
                "base_url": base_url,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


def test_local_admin_model_disabled_skips_client_call() -> None:
    client = RecordingLocalModelClient()

    assist = request_local_admin_draft_assist(
        "Customer says transition risk needs proof.",
        settings=LocalAdminModelSettings(enabled=False),
        client=client,
    )

    assert assist.status is LocalAdminModelAssistStatus.DISABLED
    assert assist.used is False
    assert assist.suggestion is None
    assert client.calls == []


def test_local_admin_model_success_returns_validated_suggestion() -> None:
    client = RecordingLocalModelClient(
        response={
            "inferred_claims": ["Model claim: transition risk needs evidence."],
            "likely_risks": ["Model risk: weak transition proof may hurt score."],
            "action_candidates": ["Ask PM for transition proof points."],
            "confidence_notes": ["Model saw explicit transition and proof signal."],
        }
    )
    settings = LocalAdminModelSettings(
        enabled=True,
        ollama_base_url="http://localhost:11434",
        model="qwen3.5:9b",
        timeout_seconds=7,
    )

    assist = request_local_admin_draft_assist(
        "Customer says transition proof is weak.",
        settings=settings,
        client=client,
    )

    assert assist.status is LocalAdminModelAssistStatus.USED
    assert assist.used is True
    assert assist.model == "qwen3.5:9b"
    assert isinstance(assist.suggestion, LocalAdminDraftSuggestion)
    assert assist.suggestion.inferred_claims == (
        "Model claim: transition risk needs evidence.",
    )
    assert client.calls[0]["base_url"] == "http://localhost:11434"
    assert client.calls[0]["timeout_seconds"] == 7


def test_local_admin_model_unavailable_falls_back_without_error() -> None:
    client = RecordingLocalModelClient(error=TimeoutError("offline"))

    assist = request_local_admin_draft_assist(
        "Customer says transition proof is weak.",
        settings=LocalAdminModelSettings(enabled=True),
        client=client,
    )

    assert assist.status is LocalAdminModelAssistStatus.UNAVAILABLE
    assert assist.used is False
    assert assist.suggestion is None
    assert "offline" in assist.reason


def test_local_admin_model_malformed_response_falls_back() -> None:
    client = RecordingLocalModelClient(response={"inferred_claims": "not a list"})

    assist = request_local_admin_draft_assist(
        "Customer says transition proof is weak.",
        settings=LocalAdminModelSettings(enabled=True),
        client=client,
    )

    assert assist.status is LocalAdminModelAssistStatus.INVALID_RESPONSE
    assert assist.used is False
    assert assist.suggestion is None