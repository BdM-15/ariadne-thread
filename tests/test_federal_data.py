from pydantic import ValidationError

from ariadne.federal_data import (
    FederalDataCapabilityManifest,
    FederalDataCapabilityRegistry,
    FederalDataInitializeRunnerResult,
    FederalDataProductStatus,
    FederalDataSmokeCheckStatus,
    list_federal_data_capability_manifests,
    run_federal_data_initialize_smoke_check,
)


def test_lists_upstream_1102_federal_data_capability_manifests() -> None:
    registry = list_federal_data_capability_manifests()

    by_id = {manifest.id: manifest for manifest in registry.capabilities}

    assert tuple(by_id) == (
        "usaspending",
        "sam_gov",
        "gsa_calc",
        "bls_oews",
        "gsa_per_diem",
        "ecfr",
        "federal_register",
        "regulations_gov",
    )
    assert by_id["usaspending"].package == "usaspending-gov-mcp"
    assert by_id["usaspending"].version == "0.3.2"
    assert by_id["usaspending"].command == (
        "uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp"
    )
    assert by_id["usaspending"].product_status is (
        FederalDataProductStatus.PRODUCT_INTEGRATED
    )
    assert by_id["sam_gov"].required_env_vars == ("SAM_GOV_API_KEY",)
    assert by_id["sam_gov"].upstream_env_vars == ("SAM_API_KEY",)
    assert by_id["regulations_gov"].optional_env_vars == ("API_DATA_GOV_KEY",)
    assert all(manifest.source_url for manifest in registry.capabilities)
    assert all(manifest.license for manifest in registry.capabilities)
    assert all("uvx --from" in manifest.command for manifest in registry.capabilities)


def test_registry_rejects_duplicate_federal_data_capability_ids() -> None:
    manifest = FederalDataCapabilityManifest(
        id="usaspending",
        name="USAspending",
        description="Public federal spending data.",
        package="usaspending-gov-mcp",
        version="0.3.2",
        command="uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp",
        source_url="https://github.com/1102tools/federal-contracting-mcps",
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
    )

    try:
        FederalDataCapabilityRegistry(capabilities=(manifest, manifest))
    except ValidationError as error:
        assert "duplicate federal data capability id" in str(error)
    else:
        raise AssertionError("duplicate capability ids should be rejected")


def test_manifest_rejects_unpinned_mcp_command_shapes() -> None:
    try:
        FederalDataCapabilityManifest(
            id="usaspending",
            name="USAspending",
            description="Public federal spending data.",
            package="usaspending-gov-mcp",
            version="0.3.2",
            command="uvx usaspending-mcp",
            source_url="https://github.com/1102tools/federal-contracting-mcps",
            license="MIT",
            product_status=FederalDataProductStatus.REGISTERED,
        )
    except ValidationError as error:
        assert "command must pin the declared package and version" in str(error)
    else:
        raise AssertionError("unpinned MCP command shapes should be rejected")


def test_manifest_env_metadata_contains_names_only() -> None:
    try:
        FederalDataCapabilityManifest(
            id="sam_gov",
            name="SAM.gov",
            description="Public federal entity and opportunity data.",
            package="sam-gov-mcp",
            version="0.4.1",
            command="uvx --from sam-gov-mcp==0.4.1 sam-gov-mcp",
            source_url="https://github.com/1102tools/federal-contracting-mcps",
            license="MIT",
            product_status=FederalDataProductStatus.REGISTERED,
            required_env_vars=("SAM_GOV_API_KEY=live-value",),
        )
    except ValidationError as error:
        assert "env var metadata must contain names only" in str(error)
    else:
        raise AssertionError("env var metadata should reject assignments")


def test_initialize_smoke_check_sends_only_json_rpc_initialize_request() -> None:
    manifest = list_federal_data_capability_manifests().capabilities[0]
    calls = []

    def runner(command, request, timeout_seconds, env):
        calls.append((command, request, timeout_seconds, env))
        return FederalDataInitializeRunnerResult(
            return_code=0,
            initialized=True,
            diagnostic_summary="initialize accepted",
        )

    result = run_federal_data_initialize_smoke_check(
        manifest,
        runner=runner,
        env={},
        checked_at="2026-05-16T12:00:00Z",
    )

    assert result.capability_id == "usaspending"
    assert result.status is FederalDataSmokeCheckStatus.SUCCESS
    assert result.command == manifest.command
    assert result.checked_at == "2026-05-16T12:00:00Z"
    assert result.diagnostic_summary == "initialize accepted"
    assert result.missing_env_vars == ()
    assert result.data_tool_calls_invoked == ()
    assert len(calls) == 1
    command, request, timeout_seconds, env = calls[0]
    assert command == manifest.command
    assert request["method"] == "initialize"
    assert request["jsonrpc"] == "2.0"
    assert timeout_seconds == 60
    assert env == {}


def test_initialize_smoke_check_reports_missing_required_env_without_runner_call() -> None:
    sam_manifest = next(
        manifest
        for manifest in list_federal_data_capability_manifests().capabilities
        if manifest.id == "sam_gov"
    )
    calls = []

    def runner(command, request, timeout_seconds, env):
        calls.append((command, request, timeout_seconds, env))
        return FederalDataInitializeRunnerResult(
            return_code=0,
            initialized=True,
            diagnostic_summary="should not run",
        )

    result = run_federal_data_initialize_smoke_check(
        sam_manifest,
        runner=runner,
        env={},
        checked_at="2026-05-16T12:05:00Z",
    )

    assert result.status is FederalDataSmokeCheckStatus.MISSING_ENV
    assert result.missing_env_vars == ("SAM_GOV_API_KEY",)
    assert result.diagnostic_summary == "Missing required env vars: SAM_GOV_API_KEY"
    assert "SAM_API_KEY" not in result.diagnostic_summary
    assert calls == []


def test_initialize_smoke_check_classifies_failure_and_timeout_results() -> None:
    manifest = list_federal_data_capability_manifests().capabilities[0]

    failed = run_federal_data_initialize_smoke_check(
        manifest,
        runner=lambda command, request, timeout_seconds, env: (
            FederalDataInitializeRunnerResult(
                return_code=2,
                initialized=False,
                diagnostic_summary="process exited before initialize response",
            )
        ),
        env={},
        checked_at="2026-05-16T12:10:00Z",
    )
    timed_out = run_federal_data_initialize_smoke_check(
        manifest,
        runner=lambda command, request, timeout_seconds, env: (
            FederalDataInitializeRunnerResult(
                return_code=None,
                initialized=False,
                timed_out=True,
                diagnostic_summary="initialize timed out after 60 seconds",
            )
        ),
        env={},
        checked_at="2026-05-16T12:11:00Z",
    )

    assert failed.status is FederalDataSmokeCheckStatus.FAILURE
    assert failed.diagnostic_summary == "process exited before initialize response"
    assert timed_out.status is FederalDataSmokeCheckStatus.TIMEOUT
    assert timed_out.diagnostic_summary == "initialize timed out after 60 seconds"


def test_initialize_smoke_check_redacts_env_values_from_diagnostics() -> None:
    sam_manifest = next(
        manifest
        for manifest in list_federal_data_capability_manifests().capabilities
        if manifest.id == "sam_gov"
    )
    secret_value = "live-sam-secret-value"

    result = run_federal_data_initialize_smoke_check(
        sam_manifest,
        runner=lambda command, request, timeout_seconds, env: (
            FederalDataInitializeRunnerResult(
                return_code=1,
                initialized=False,
                diagnostic_summary=f"auth failed for {secret_value}",
            )
        ),
        env={"SAM_GOV_API_KEY": secret_value},
        checked_at="2026-05-16T12:15:00Z",
    )

    assert result.status is FederalDataSmokeCheckStatus.FAILURE
    assert secret_value not in result.diagnostic_summary
    assert result.diagnostic_summary == "auth failed for <redacted>"