"""Run-context metadata for a report (Reporting Slice 1).

A :class:`ScanResult` carries findings and scan summary but no run identity (tool name/version,
scan id, timestamps, target label). ``ReportMetadata`` supplies that context and is built by the
caller (from a ``ScanJob`` + ``app.meta`` in a later slice), keeping the reporting layer decoupled
from the jobs/app layers.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportMetadata(BaseModel):
    """Caller-supplied run context for a report. Immutable."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_name: str
    tool_version: str
    scan_id: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    target_label: str | None = None
    # Optional project/tool URL for SARIF tool.driver.informationUri (None until one exists).
    information_uri: str | None = None
