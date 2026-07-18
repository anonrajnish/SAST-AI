"""SARIF 2.1.0 object model — the minimal subset the MVP emits (Reporting Slice 2).

Frozen, fully-typed Pydantic models whose field names are the SARIF JSON keys (camelCase),
except the log's ``$schema`` which is emitted via a serialization alias. Only the fields the MVP
produces are modelled; optional fields left ``None`` are dropped at serialization time.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

SARIF_SCHEMA_URI = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class SarifArtifactLocation(BaseModel):
    model_config = _FROZEN

    uri: str


class SarifRegion(BaseModel):
    model_config = _FROZEN

    startLine: int
    endLine: int | None = None


class SarifPhysicalLocation(BaseModel):
    model_config = _FROZEN

    artifactLocation: SarifArtifactLocation
    region: SarifRegion | None = None


class SarifLocation(BaseModel):
    model_config = _FROZEN

    physicalLocation: SarifPhysicalLocation


class SarifMessage(BaseModel):
    model_config = _FROZEN

    text: str


class SarifResultProperties(BaseModel):
    """Free-form property bag preserving the finer finding metadata."""

    model_config = _FROZEN

    rule_id: str | None = None
    cwe: str | None = None


class SarifResult(BaseModel):
    model_config = _FROZEN

    ruleId: str
    ruleIndex: int | None = None
    level: str
    message: SarifMessage
    locations: list[SarifLocation]
    partialFingerprints: dict[str, str]
    properties: SarifResultProperties


class SarifDescriptorProperties(BaseModel):
    model_config = _FROZEN

    tags: list[str]


class SarifReportingDescriptor(BaseModel):
    """A rule in ``tool.driver.rules`` (detector-grained in the MVP; see reporter docs)."""

    model_config = _FROZEN

    id: str
    name: str
    properties: SarifDescriptorProperties


class SarifToolComponent(BaseModel):
    model_config = _FROZEN

    name: str
    version: str
    informationUri: str | None = None
    rules: list[SarifReportingDescriptor]


class SarifTool(BaseModel):
    model_config = _FROZEN

    driver: SarifToolComponent


class SarifRun(BaseModel):
    model_config = _FROZEN

    tool: SarifTool
    results: list[SarifResult]


class SarifLog(BaseModel):
    model_config = _FROZEN

    schema_uri: str = Field(default=SARIF_SCHEMA_URI, serialization_alias="$schema")
    version: str = SARIF_VERSION
    runs: list[SarifRun]
