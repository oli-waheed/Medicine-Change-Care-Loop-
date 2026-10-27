"""Source release identity and provenance for the Fimea Basic Register."""

from dataclasses import dataclass

from ..source_field import SourceField


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Identifies the source and the captured raw file without interpreting its contents."""

    source_name: str
    raw_file_name: str | None = None
    raw_file_checksum: str | None = None

    def __post_init__(self) -> None:
        if not self.source_name:
            raise ValueError("A source name is required.")


@dataclass(frozen=True, slots=True)
class SourceRelease:
    """A release's source-provided metadata; date values remain in their source form."""

    ajopvm: SourceField
    aineistoera: SourceField
    provenance: SourceProvenance
    kkera: SourceField
    kattavuus: SourceField
