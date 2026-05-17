from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import json
import os
import re
import shlex
import subprocess
from typing import Any, Protocol

from pydantic import BaseModel, model_validator


class FederalDataProductStatus(StrEnum):
    REGISTERED = "registered"
    SMOKE_TESTED = "smoke_tested"
    PRODUCT_INTEGRATED = "product_integrated"
    DEFERRED_PRODUCT_WORKFLOW = "deferred_product_workflow"


class FederalDataSmokeCheckStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    MISSING_ENV = "missing_env"


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


class FederalDataInitializeRunnerResult(BaseModel):
    return_code: int | None = None
    initialized: bool = False
    timed_out: bool = False
    diagnostic_summary: str


class FederalDataMcpToolRunnerResult(BaseModel):
    return_code: int | None = None
    ok: bool = False
    payload: dict[str, Any] | None = None
    error_message: str | None = None
    timed_out: bool = False


class FederalDataSmokeCheckResult(BaseModel):
    capability_id: str
    capability_name: str
    package: str
    version: str
    command: str
    status: FederalDataSmokeCheckStatus
    checked_at: str
    diagnostic_summary: str
    missing_env_vars: tuple[str, ...] = ()
    data_tool_calls_invoked: tuple[str, ...] = ()


class FederalDataInitializeRunner(Protocol):
    def __call__(
        self,
        command: str,
        request: dict[str, Any],
        timeout_seconds: int,
        env: dict[str, str],
    ) -> FederalDataInitializeRunnerResult: ...


def list_federal_data_capability_manifests() -> FederalDataCapabilityRegistry:
    return FederalDataCapabilityRegistry(capabilities=_FEDERAL_DATA_CAPABILITIES)


def run_federal_data_initialize_smoke_check(
    manifest: FederalDataCapabilityManifest,
    *,
    runner: FederalDataInitializeRunner,
    env: dict[str, str],
    timeout_seconds: int = 60,
    checked_at: str | None = None,
) -> FederalDataSmokeCheckResult:
    missing_env_vars = tuple(
        env_var_name
        for env_var_name in manifest.required_env_vars
        if not env.get(env_var_name)
    )
    resolved_checked_at = checked_at or datetime.now(UTC).isoformat()
    if missing_env_vars:
        return FederalDataSmokeCheckResult(
            capability_id=manifest.id,
            capability_name=manifest.name,
            package=manifest.package,
            version=manifest.version,
            command=manifest.command,
            status=FederalDataSmokeCheckStatus.MISSING_ENV,
            checked_at=resolved_checked_at,
            diagnostic_summary=(
                "Missing required env vars: " + ", ".join(missing_env_vars)
            ),
            missing_env_vars=missing_env_vars,
        )

    runner_result = runner(
        manifest.command,
        _MCP_INITIALIZE_REQUEST,
        timeout_seconds,
        env,
    )
    if runner_result.timed_out:
        status = FederalDataSmokeCheckStatus.TIMEOUT
    elif runner_result.return_code == 0 and runner_result.initialized:
        status = FederalDataSmokeCheckStatus.SUCCESS
    else:
        status = FederalDataSmokeCheckStatus.FAILURE
    return FederalDataSmokeCheckResult(
        capability_id=manifest.id,
        capability_name=manifest.name,
        package=manifest.package,
        version=manifest.version,
        command=manifest.command,
        status=status,
        checked_at=resolved_checked_at,
        diagnostic_summary=_redact_env_values(runner_result.diagnostic_summary, env),
    )


def run_mcp_initialize_command(
    command: str,
    request: dict[str, Any],
    timeout_seconds: int,
    env: dict[str, str],
) -> FederalDataInitializeRunnerResult:
    try:
        completed = subprocess.run(
            shlex.split(command),
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=_minimal_process_env(env),
        )
    except FileNotFoundError as error:
        return FederalDataInitializeRunnerResult(
            return_code=None,
            initialized=False,
            diagnostic_summary=f"command not found: {error.filename}",
        )
    except subprocess.TimeoutExpired:
        return FederalDataInitializeRunnerResult(
            return_code=None,
            initialized=False,
            timed_out=True,
            diagnostic_summary=f"initialize timed out after {timeout_seconds} seconds",
        )

    initialized = _contains_initialize_result(completed.stdout)
    return FederalDataInitializeRunnerResult(
        return_code=completed.returncode,
        initialized=initialized,
        diagnostic_summary=_runner_diagnostic_summary(completed, initialized),
    )


def run_mcp_tool_command(
    command: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout_seconds: int,
    env: dict[str, str],
) -> FederalDataMcpToolRunnerResult:
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    stdin_payload = "\n".join(
        (
            json.dumps(_MCP_INITIALIZE_REQUEST),
            json.dumps(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            ),
            json.dumps(request),
            "",
        )
    )
    try:
        completed = subprocess.run(
            shlex.split(command),
            input=stdin_payload,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=_minimal_process_env(env),
        )
    except FileNotFoundError as error:
        return FederalDataMcpToolRunnerResult(
            return_code=None,
            ok=False,
            error_message=f"command not found: {error.filename}",
        )
    except subprocess.TimeoutExpired:
        return FederalDataMcpToolRunnerResult(
            return_code=None,
            ok=False,
            timed_out=True,
            error_message=f"tool call timed out after {timeout_seconds} seconds",
        )

    tool_response = _json_rpc_response_by_id(completed.stdout, request_id=2)
    if completed.returncode != 0:
        return FederalDataMcpToolRunnerResult(
            return_code=completed.returncode,
            ok=False,
            error_message=_runner_diagnostic_summary(completed, initialized=False),
        )
    if tool_response is None:
        return FederalDataMcpToolRunnerResult(
            return_code=completed.returncode,
            ok=False,
            error_message="MCP tool response missing.",
        )
    if error := tool_response.get("error"):
        return FederalDataMcpToolRunnerResult(
            return_code=completed.returncode,
            ok=False,
            error_message=str(error),
        )
    payload = _payload_from_mcp_tool_result(tool_response.get("result"))
    return FederalDataMcpToolRunnerResult(
        return_code=completed.returncode,
        ok=True,
        payload=payload,
    )


_FEDERAL_CONTRACTING_MCPS_URL = (
    "https://github.com/1102tools/federal-contracting-mcps"
)

_ENV_VAR_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")

_MCP_INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "ariadne-thread", "version": "0.1.0"},
    },
}


def _redact_env_values(summary: str, env: dict[str, str]) -> str:
    redacted = summary
    for value in env.values():
        if len(value) >= 4:
            redacted = redacted.replace(value, "<redacted>")
    return redacted


def _contains_initialize_result(stdout: str) -> bool:
    response = _json_rpc_response_by_id(stdout, request_id=1)
    return response is not None and "result" in response


def _json_rpc_response_by_id(stdout: str, *, request_id: int) -> dict[str, Any] | None:
    for line in stdout.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("id") == request_id:
            return payload
    return None


def _payload_from_mcp_tool_result(result: Any) -> dict[str, Any] | None:
    if isinstance(result, dict) and "content" in result:
        for item in result.get("content", ()):
            if not isinstance(item, dict) or item.get("type") != "text":
                continue
            text = str(item.get("text", ""))
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        return result
    return result if isinstance(result, dict) else None


def _runner_diagnostic_summary(
    completed: subprocess.CompletedProcess[str], initialized: bool
) -> str:
    if completed.returncode == 0 and initialized:
        return "initialize accepted"
    detail = (completed.stderr or completed.stdout).strip().splitlines()
    if detail:
        return f"return code {completed.returncode}: {detail[0][:240]}"
    return f"return code {completed.returncode}: initialize response missing"


def _minimal_process_env(env: dict[str, str]) -> dict[str, str]:
    base_names = (
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "SystemRoot",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
    )
    process_env = {
        name: value for name in base_names if (value := os.environ.get(name))
    }
    process_env.update(env)
    return process_env


_FEDERAL_DATA_CAPABILITIES = (
    FederalDataCapabilityManifest(
        id="usaspending",
        name="USAspending",
        description=(
            "USASpending.gov MCP server from 1102tools/federal-contracting-mcps. "
            "Provides 55 read-only tools for federal awards, contracts, IDVs, "
            "subawards, recipients, agencies, federal accounts, obligations, "
            "and transaction history. No API key required; first Ariadne "
            "product-integrated source for PIID recompete profiles."
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
            "SAM.gov MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only entity registration, responsibility, opportunity, "
            "solicitation, and notice lookup for UEI, customer, incumbent, "
            "and recompete follow-on enrichment. Requires a SAM.gov API key; "
            "registered now, product workflow deferred."
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
            "GSA CALC+ MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only labor category, awarded-rate, ceiling-rate, vendor, "
            "schedule, and market-rate context for price-to-win and labor "
            "category enrichment. No API key required; product workflow deferred."
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
            "BLS OEWS MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only occupational employment and wage statistics for SOC, "
            "geography, labor-market, and compensation context seeded by NAICS, "
            "place of performance, or role signals. API key optional; product "
            "workflow deferred."
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
            "GSA Per Diem MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only lodging, meals, incidentals, and locality-rate lookup "
            "for travel cost, place-of-performance, and execution-context "
            "enrichment. API key optional or recommended; product workflow "
            "deferred."
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
            "eCFR MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only Code of Federal Regulations lookup for FAR, DFARS, "
            "agency supplements, compliance clauses, and policy-driven capture "
            "implications. No API key required; product workflow deferred."
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
            "Federal Register MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only notice, proposed rule, final rule, presidential document, "
            "agency, topic, and publication-date lookup for policy timing and "
            "market-signal enrichment. No API key required; product workflow "
            "deferred."
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
            "Regulations.gov MCP server from 1102tools/federal-contracting-mcps. "
            "Read-only docket, document, comment, agency, rulemaking, and "
            "stakeholder-signal lookup for regulatory context around capture "
            "strategy. API.data.gov key optional or recommended; product "
            "workflow deferred."
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