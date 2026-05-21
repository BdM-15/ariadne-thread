from ariadne.config import HostedModelSettings
from ariadne.hosted_model import (
    HostedModelAssistStatus,
    HostedModelPurpose,
    request_hosted_model_assist,
)


class RecordingHostedModelClient:
    def __init__(self, response: str = "Draft support", error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


def test_hosted_model_disabled_skips_client_call() -> None:
    client = RecordingHostedModelClient()

    assist = request_hosted_model_assist(
        "Summarize route output.",
        purpose=HostedModelPurpose.OUTPUT_REVIEW_SUMMARY,
        settings=HostedModelSettings(enabled=False),
        client=client,
    )

    assert assist.status is HostedModelAssistStatus.DISABLED
    assert assist.used is False
    assert client.calls == []


def test_hosted_model_missing_key_skips_client_call() -> None:
    client = RecordingHostedModelClient()

    assist = request_hosted_model_assist(
        "Draft packet synthesis.",
        purpose=HostedModelPurpose.PACKET_SYNTHESIS_SUPPORT,
        settings=HostedModelSettings(enabled=True, provider="xai", xai_api_key=None),
        client=client,
    )

    assert assist.status is HostedModelAssistStatus.MISSING_CREDENTIALS
    assert assist.used is False
    assert "missing API key" in assist.reason
    assert client.calls == []


def test_hosted_model_success_uses_fake_client_without_trusted_write() -> None:
    client = RecordingHostedModelClient(response="Reviewable draft with gaps.")

    assist = request_hosted_model_assist(
        "Prepare review summary.",
        purpose=HostedModelPurpose.OUTPUT_REVIEW_SUMMARY,
        settings=HostedModelSettings(
            enabled=True,
            provider="xai",
            reasoning_model="grok-4.3",
            daily_model="grok-mini",
            xai_api_key="fake-key",
            timeout_seconds=9,
        ),
        client=client,
    )

    assert assist.status is HostedModelAssistStatus.USED
    assert assist.used is True
    assert assist.provider == "xai"
    assert assist.model == "grok-mini"
    assert assist.draft_text == "Reviewable draft with gaps."
    assert client.calls[0]["api_key"] == "fake-key"
    assert client.calls[0]["timeout_seconds"] == 9


def test_hosted_model_unavailable_falls_back_without_error() -> None:
    client = RecordingHostedModelClient(error=TimeoutError("cloud timeout"))

    assist = request_hosted_model_assist(
        "Draft artifact block.",
        purpose=HostedModelPurpose.ARTIFACT_BLOCK_DRAFTING,
        settings=HostedModelSettings(enabled=True, provider="xai", xai_api_key="fake"),
        client=client,
    )

    assert assist.status is HostedModelAssistStatus.UNAVAILABLE
    assert assist.used is False
    assert "cloud timeout" in assist.reason