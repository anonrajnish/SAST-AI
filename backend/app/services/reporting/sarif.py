"""SARIF 2.1.0 export (Reporting Slice 2).

Pure, deterministic projection of a :class:`ScanResult` (+ :class:`ReportMetadata`) into a valid
SARIF 2.1.0 log. Independent of the JSON report — it consumes ``ScanResult`` directly and never
serializes :class:`~app.services.reporting.models.ScanReport`.

**Intentional MVP compromise — detector-grained rules.** The deterministic registry currently
exposes analyzer-level metadata (``detector_name`` + ``cwes``) but not per-rule metadata (rule
ids/names live in each analyzer's private rule list). So ``tool.driver.rules`` has one
``reportingDescriptor`` per *analyzer* (id = ``detector_name``), and each result's ``ruleId`` is
the detector. The finer ``rule_id`` is preserved in ``result.properties`` and the partial
fingerprint. A future version may migrate to rule-level descriptors once the registry exposes rule
metadata (which would require surfacing it from the deterministic analyzer package).

Every deterministic finding is reported at SARIF ``level: "warning"`` (no per-rule severity yet).
CWE is conveyed via rule ``tags`` only (no taxonomy objects). Messages are generic and never expose
internal rule names or source text.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from contracts import Finding

from app.services.deterministic import ANALYZER_REGISTRY, AnalyzerEntry
from app.services.scan import ScanResult

from .metadata import ReportMetadata
from .sarif_models import (
    SarifArtifactLocation,
    SarifDescriptorProperties,
    SarifLocation,
    SarifLog,
    SarifMessage,
    SarifPhysicalLocation,
    SarifRegion,
    SarifReportingDescriptor,
    SarifResult,
    SarifResultProperties,
    SarifRun,
    SarifTool,
    SarifToolComponent,
)

_LEVEL_WARNING = "warning"
_SECURITY_TAG = "security"
_FINGERPRINT_KEY = "aiSastFindingHash/v1"
_UNKNOWN_RULE_ID = "unknown"


def build_sarif_report(
    scan_result: ScanResult,
    meta: ReportMetadata,
    *,
    registry: Sequence[AnalyzerEntry] = ANALYZER_REGISTRY,
) -> SarifLog:
    """Project ``scan_result`` + ``meta`` into a SARIF 2.1.0 log."""

    descriptors, index = _build_rule_catalog(registry)
    driver = SarifToolComponent(
        name=meta.tool_name,
        version=meta.tool_version,
        informationUri=meta.information_uri,
        rules=descriptors,
    )
    results = [_to_result(finding, index) for finding in scan_result.findings]
    run = SarifRun(tool=SarifTool(driver=driver), results=results)
    return SarifLog(runs=[run])


def render_sarif_report(
    scan_result: ScanResult,
    meta: ReportMetadata,
    *,
    registry: Sequence[AnalyzerEntry] = ANALYZER_REGISTRY,
) -> str:
    """Return the canonical SARIF JSON string (deterministic; trailing newline)."""

    log = build_sarif_report(scan_result, meta, registry=registry)
    dumped = log.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(dumped, indent=2, ensure_ascii=False) + "\n"


def _build_rule_catalog(
    registry: Sequence[AnalyzerEntry],
) -> tuple[list[SarifReportingDescriptor], dict[str, int]]:
    """Build detector-grained rule descriptors (registry order) + a detector→index map."""

    descriptors: list[SarifReportingDescriptor] = []
    index: dict[str, int] = {}
    for position, entry in enumerate(registry):
        detector = entry.analyzer.detector_name
        tags = sorted([_cwe_tag(cwe) for cwe in entry.cwes] + [_SECURITY_TAG])
        descriptors.append(
            SarifReportingDescriptor(
                id=detector,
                name=detector,
                properties=SarifDescriptorProperties(tags=tags),
            )
        )
        index[detector] = position
    return descriptors, index


def _cwe_tag(cwe: str) -> str:
    """Map ``"CWE-328"`` to the conventional SARIF tag ``"external/cwe/cwe-328"``."""

    return f"external/cwe/{cwe.lower()}"


def _to_result(finding: Finding, index: dict[str, int]) -> SarifResult:
    location = finding.location
    region = (
        SarifRegion(startLine=location.start_line, endLine=location.end_line)
        if location.start_line is not None
        else None
    )
    physical = SarifPhysicalLocation(
        artifactLocation=SarifArtifactLocation(uri=location.file),
        region=region,
    )
    detector = finding.detector
    return SarifResult(
        ruleId=detector if detector is not None else _UNKNOWN_RULE_ID,
        ruleIndex=index.get(detector) if detector is not None else None,
        level=_LEVEL_WARNING,
        message=SarifMessage(text=_message_text(finding.cwe)),
        locations=[SarifLocation(physicalLocation=physical)],
        partialFingerprints=_fingerprint(finding),
        properties=SarifResultProperties(rule_id=finding.rule_id, cwe=finding.cwe),
    )


def _message_text(cwe: str | None) -> str:
    """A generic message that never exposes internal rule names or source text."""

    if cwe is None:
        return "Potential security issue detected."
    return f"Potential security issue detected ({cwe})."


def _fingerprint(finding: Finding) -> dict[str, str]:
    """Stable SHA-256 fingerprint over detector|rule_id|file|start_line|end_line|cwe."""

    location = finding.location
    canonical = "|".join(
        [
            finding.detector or "",
            finding.rule_id or "",
            location.file,
            str(location.start_line) if location.start_line is not None else "",
            str(location.end_line) if location.end_line is not None else "",
            finding.cwe or "",
        ]
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {_FINGERPRINT_KEY: digest}
