from pydantic import ValidationError

from ariadne.federal_data import (
    FederalDataCapabilityManifest,
    FederalDataCapabilityRegistry,
    FederalDataProductStatus,
    list_federal_data_capability_manifests,
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