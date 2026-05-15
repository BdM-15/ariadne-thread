from __future__ import annotations

import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ariadne.config import RuntimeSettings  # noqa: E402
from ariadne.server import create_app  # noqa: E402

logger = logging.getLogger(__name__)


def build_app(env_file: Path | str = ".env") -> FastAPI:
    return create_app(RuntimeSettings.from_env_file(env_file))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = RuntimeSettings.from_env_file()
    logger.info("Starting %s at %s", settings.public_app_name, settings.local_url)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()