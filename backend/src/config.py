"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MAX_SOURCE_RELEASE_UPLOAD_BYTES = 250 * 1024 * 1024
# Feature 005: the address the n8n workflow downloads from.
DEFAULT_FIMEA_RELEASE_URL = "https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml"
# Feature 006: Fimea's open-data shortage file and the daily automatic update.
DEFAULT_FIMEA_SHORTAGES_URL = "https://data.pilvi.fimea.fi/avoin-data/Shortages.txt"
DEFAULT_DAILY_UPDATE_TIME = "06:00"


def parse_daily_update_time(value: str | None) -> str | None:
    """``HH:MM`` in the machine's local time, or None when the daily update is off."""
    if value is None or value.strip().lower() in {"", "off", "none", "disabled"}:
        return None
    hours, _, minutes = value.strip().partition(":")
    if not (hours.isdigit() and minutes.isdigit() and int(hours) < 24 and int(minutes) < 60):
        raise ValueError(f"DAILY_UPDATE_TIME must be HH:MM or 'off', not {value!r}.")
    return f"{int(hours):02d}:{int(minutes):02d}"


_BACKEND_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class ApplicationConfig:
    source_release_storage_dir: Path
    max_source_release_upload_bytes: int
    database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'medicine-change-care-loop.sqlite3'}"
    medication_records_path: Path = _BACKEND_DIR / "seed" / "simulated-medication-records.json"
    fimea_release_url: str = DEFAULT_FIMEA_RELEASE_URL
    fimea_shortages_url: str = DEFAULT_FIMEA_SHORTAGES_URL
    # None = no daily automatic update (the default when built directly, as in tests).
    daily_update_time: str | None = None

    def __post_init__(self) -> None:
        if self.max_source_release_upload_bytes <= 0:
            raise ValueError("Maximum source release upload size must be positive.")

    @property
    def shortage_storage_dir(self) -> Path:
        """Raw shortage files, next to the source-release captures."""
        return Path(self.source_release_storage_dir).parent / "shortages"

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
            fimea_shortages_url=os.environ.get("FIMEA_SHORTAGES_URL", DEFAULT_FIMEA_SHORTAGES_URL),
            daily_update_time=parse_daily_update_time(
                os.environ.get("DAILY_UPDATE_TIME", DEFAULT_DAILY_UPDATE_TIME)
            ),
        )
