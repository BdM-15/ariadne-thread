from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class LocalAdminModelSettings(BaseModel):
    enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    model: str = "qwen3.5:9b"
    timeout_seconds: int = 30


class RuntimeSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 9622
    public_app_name: str = "Ariadne Thread"
    ariadne_env: str = "development"
    ariadne_workspace: str = "default"
    ariadne_evidence_dir: Path = Field(default=Path(".ariadne/evidence"))
    ariadne_reference_wiki_dir: Path = Field(
        default=Path("docs/reference/project-ariadne/knowledge")
    )
    local_admin_model: LocalAdminModelSettings = Field(
        default_factory=LocalAdminModelSettings
    )

    @property
    def local_url(self) -> str:
        browser_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
        return f"http://{browser_host}:{self.port}"

    @classmethod
    def from_env_file(cls, path: Path | str = ".env") -> RuntimeSettings:
        values = _read_env_file(Path(path))
        return cls.from_mapping(values | os.environ)

    @classmethod
    def from_mapping(cls, values: dict[str, str]) -> RuntimeSettings:
        return cls(
            host=values.get("HOST", cls.model_fields["host"].default),
            port=int(values.get("PORT", cls.model_fields["port"].default)),
            public_app_name=values.get(
                "PUBLIC_APP_NAME", cls.model_fields["public_app_name"].default
            ),
            ariadne_env=values.get("ARIADNE_ENV", cls.model_fields["ariadne_env"].default),
            ariadne_workspace=values.get(
                "ARIADNE_WORKSPACE", cls.model_fields["ariadne_workspace"].default
            ),
            ariadne_evidence_dir=Path(
                values.get(
                    "ARIADNE_EVIDENCE_DIR",
                    str(cls.model_fields["ariadne_evidence_dir"].default),
                )
            ),
            ariadne_reference_wiki_dir=Path(
                values.get(
                    "ARIADNE_REFERENCE_WIKI_DIR",
                    str(cls.model_fields["ariadne_reference_wiki_dir"].default),
                )
            ),
            local_admin_model=LocalAdminModelSettings(
                enabled=_parse_bool(values.get("LOCAL_ADMIN_MODEL_ENABLED", "false")),
                ollama_base_url=values.get(
                    "OLLAMA_HOST",
                    LocalAdminModelSettings.model_fields["ollama_base_url"].default,
                ),
                model=values.get(
                    "LOCAL_DAILY_MODEL",
                    LocalAdminModelSettings.model_fields["model"].default,
                ),
                timeout_seconds=int(
                    values.get(
                        "LOCAL_ADMIN_MODEL_TIMEOUT_SECONDS",
                        LocalAdminModelSettings.model_fields[
                            "timeout_seconds"
                        ].default,
                    )
                ),
            ),
        )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}