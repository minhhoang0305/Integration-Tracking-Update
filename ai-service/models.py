from datetime import datetime

from pydantic import BaseModel, Field


class AnalyzeEmailRequest(BaseModel):
    emailId: str
    sender: str
    subject: str = ""
    body: str
    receivedAt: datetime


class ChangeSignal(BaseModel):
    emailId: str

    provider: str | None = None

    isApiRelated: bool = False

    changeDetected: bool = False

    changeTypes: list[str] = Field(default_factory=list)

    summary: str | None = None

    affectedEndpoints: list[str] = Field(default_factory=list)

    deprecatedEndpoints: list["ApiEndpoint"] = Field(default_factory=list)

    announcedEndpoints: list["ApiEndpoint"] = Field(default_factory=list)

    breakingChange: bool = False

    migrationRequired: bool = False

    effectiveDate: datetime | None = None

    documentationUrls: list[str] = Field(default_factory=list)

    confidence: float = 0.0

    evidence: "ChangeEvidence" = Field(default_factory=lambda: ChangeEvidence())


class ChangeEvidence(BaseModel):
    matchedTerms: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    parserWarnings: list[str] = Field(default_factory=list)


class ApiEndpoint(BaseModel):
    method: str
    path: str
