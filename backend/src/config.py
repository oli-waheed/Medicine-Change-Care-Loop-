"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MAX_SOURCE_RELEASE_UPLOAD_BYTES = 250 * 1024 * 1024
# Feature 005: the address the n8n workflow downloads from.
DEFAULT_FIMEA_RELEASE_URL = "https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml"
_BACKEND_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class ApplicationConfig:
    source_release_storage_dir: Path
    max_source_release_upload_bytes: int
    database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'medicine-change-care-loop.sqlite3'}"
    medication_records_path: Path = _BACKEND_DIR / "seed" / "simulated-medication-records.json"
    fimea_release_url: str = DEFAULT_FIMEA_RELEASE_URL

    def __post_init__(self) -> None:
        if self.max_source_release_upload_bytes <= 0:
            raise ValueError("Maximum source release upload size must be positive.")

    @classmethod
    def from_environment(cls) -> "ApplicationConfig":
        default_storage_dir = _BACKEND_DIR / "data" / "source-releases"
        storage_dir = Path(os.environ.get("SOURCE_RELEASE_STORAGE_DIR", str(default_storage_dir)))
        max_upload_bytes = int(
            os.environ.get(
                "MAX_SOURCE_RELEASE_UPLOAD_BYTES",
                str(_DEFAULT_MAX_SOURCE_RELEASE_UPLOAD_BYTES),
            )
        )
        defaults = cls(storage_dir, max_upload_bytes)
        return cls(
            storage_dir,
            max_upload_bytes,
            database_url=os.environ.get("DATABASE_URL", defaults.database_url),
            medication_records_path=Path(
                os.environ.get(
                    "SIMULATED_MEDICATION_RECORDS_PATH",
                    str(defaults.medication_records_path),
                )
            ),
            fimea_release_url=os.environ.get("FIMEA_RELEASE_URL", DEFAULT_FIMEA_RELEASE_URL),
        )
