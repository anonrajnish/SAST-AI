"""Configurable extraction resource limits (Slice 3).

An immutable value object bounding what an extraction may consume, used to guard against
ZIP-bomb / resource-exhaustion attacks. The concrete default values live in the application
configuration (:class:`app.config.Settings`); the extractor builds an ``ExtractionLimits`` from
those settings when a caller does not supply explicit limits, so the bounds are configurable
through the existing configuration system (and overridable per call, e.g. in tests).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExtractionLimits(BaseModel):
    """Bounds enforced before/during ZIP extraction. All values must be positive."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_archive_bytes: int = Field(gt=0, description="Max on-disk size of the .zip archive.")
    max_total_uncompressed_bytes: int = Field(
        gt=0, description="Max total uncompressed size across all entries."
    )
    max_file_count: int = Field(gt=0, description="Max number of archive member entries.")
    max_compression_ratio: float = Field(
        gt=0, description="Max total uncompressed / total compressed ratio (ZIP-bomb guard)."
    )
