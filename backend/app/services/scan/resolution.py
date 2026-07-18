"""AUTO/MANUAL target-language resolution for the scan pipeline (Slice 2).

Turns a :class:`~app.services.scan.models.ScanConfig` and the detected language groups into
the concrete set of groups to scan. Pure — no detection, selection, or execution here.
"""

from __future__ import annotations

from contracts import LanguageGroup

from .models import ScanConfig, TargetMode


def resolve_target_groups(
    config: ScanConfig, detected_groups: frozenset[LanguageGroup]
) -> frozenset[LanguageGroup]:
    """Resolve which language groups to scan.

    AUTO uses ``detected_groups``; MANUAL uses the explicitly selected ``config.groups``,
    ignoring what was detected in the repository.
    """

    if config.mode is TargetMode.AUTO:
        return detected_groups
    return config.groups
