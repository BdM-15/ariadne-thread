from __future__ import annotations

from enum import StrEnum
import re

from pydantic import BaseModel, model_validator


class FederalDataProductStatus(StrEnum):
    REGISTERED = "registered"
    SMOKE_TESTED = "smoke_tested"
    PRODUCT_INTEGRATED = "product_integrated"
    DEFERRED_PRODUCT_WORKFLOW = "deferred_product_workflow"


class FederalDataCapabilityManifest(BaseModel):
    id: str
    name: str
    description: str
    package: str
    version: str
    command: str
    source_url: str
    license: str
    product_status: FederalDataProductStatus
    required_env_vars: tuple[str, ...] = ()
    optional_env_vars: tuple[str, ...] = ()
    upstream_env_vars: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_pinned_command_shape(self) -> FederalDataCapabilityManifest:
        expected_package_spec = f"--from {self.package}=={self.version}"
        if not self.command.startswith("uvx --from ") or (
            expected_package_spec not in self.command
        ):
            raise ValueError("command must pin the declared package and version")
        return self

    @model_validator(mode="after")
    def validate_env_var_names_only(self) -> FederalDataCapabilityManifest:
        for env_var_name in (
            self.required_env_vars + self.optional_env_vars + self.upstream_env_vars
        ):
            if not _ENV_VAR_NAME_PATTERN.fullmatch(env_var_name):
                raise ValueError("env var metadata must contain names only")
        return self


class FederalDataCapabilityRegistry(BaseModel):
    capabilities: tuple[FederalDataCapabilityManifest, ...]
    read_only: bool = True
    provenance_note: str = (
        "Pinned upstream 1102tools MCP package declarations; Ariadne does not "
        "vendor upstream MCP source code."
    )

    @model_validator(mode="after")
    def validate_unique_capability_ids(self) -> FederalDataCapabilityRegistry:
        seen: set[str] = set()
        for capability in self.capabilities:
            if capability.id in seen:
                raise ValueError(
                    f"duplicate federal data capability id: {capability.id}"
                )
            seen.add(capability.id)
        return self


def list_federal_data_capability_manifests() -> FederalDataCapabilityRegistry:
    return FederalDataCapabilityRegistry(capabilities=_FEDERAL_DATA_CAPABILITIES)


_FEDERAL_CONTRACTING_MCPS_URL = (
    "https://github.com/1102tools/federal-contracting-mcps"
)

_ENV_VAR_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")


_FEDERAL_DATA_CAPABILITIES = (
    FederalDataCapabilityManifest(
        id="usaspending",
        name="USAspending",
        description=(
            "Public federal award, obligation, transaction, recipient, agency, "
            "and vehicle context for recompete intelligence."
        ),
        package="usaspending-gov-mcp",
        version="0.3.2",
        command="uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.PRODUCT_INTEGRATED,
    ),
    FederalDataCapabilityManifest(
        id="sam_gov",
        name="SAM.gov",
        description=(
            "Public entity, registration, opportunity, and solicitation lookup "
            "candidate for follow-on enrichment."
        ),
        package="sam-gov-mcp",
        version="0.4.1",
        command="uvx --from sam-gov-mcp==0.4.1 sam-gov-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
        required_env_vars=("SAM_GOV_API_KEY",),
        upstream_env_vars=("SAM_API_KEY",),
    ),
    FederalDataCapabilityManifest(
        id="gsa_calc",
        name="GSA CALC+",
        description=(
            "Labor category and ceiling-rate context candidate for pricing and "
            "market-rate enrichment."
        ),
        package="gsa-calc-mcp",
        version="0.2.7",
        command="uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
    ),
    FederalDataCapabilityManifest(
        id="bls_oews",
        name="BLS OEWS",
        description=(
            "Occupational wage context candidate for labor-market enrichment "
            "from NAICS, geography, and labor signals."
        ),
        package="bls-oews-mcp",
        version="0.2.7",
        command="uvx --from bls-oews-mcp==0.2.7 bls-oews-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
        optional_env_vars=("BLS_API_KEY",),
    ),
    FederalDataCapabilityManifest(
        id="gsa_per_diem",
        name="GSA Per Diem",
        description=(
            "Travel and locality-rate context candidate for opportunity cost and "
            "execution-environment enrichment."
        ),
        package="gsa-perdiem-mcp",
        version="0.2.6",
        command="uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
        optional_env_vars=("PERDIEM_API_KEY",),
    ),
    FederalDataCapabilityManifest(
        id="ecfr",
        name="eCFR",
        description=(
            "Regulatory text context candidate for compliance, acquisition, and "
            "policy-driven capture implications."
        ),
        package="ecfr-mcp",
        version="0.2.6",
        command="uvx --from ecfr-mcp==0.2.6 ecfr-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
    ),
    FederalDataCapabilityManifest(
        id="federal_register",
        name="Federal Register",
        description=(
            "Federal notice and rulemaking context candidate for policy and "
            "market-timing enrichment."
        ),
        package="federal-register-mcp",
        version="0.2.7",
        command=(
            "uvx --from federal-register-mcp==0.2.7 federal-register-mcp"
        ),
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
    ),
    FederalDataCapabilityManifest(
        id="regulations_gov",
        name="Regulations.gov",
        description=(
            "Public docket and comment context candidate for regulatory and "
            "stakeholder-signal enrichment."
        ),
        package="regulationsgov-mcp",
        version="0.2.5",
        command="uvx --from regulationsgov-mcp==0.2.5 regulationsgov-mcp",
        source_url=_FEDERAL_CONTRACTING_MCPS_URL,
        license="MIT",
        product_status=FederalDataProductStatus.REGISTERED,
        optional_env_vars=("API_DATA_GOV_KEY",),
        upstream_env_vars=("REGULATIONS_GOV_API_KEY",),
    ),
)