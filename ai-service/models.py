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

    breakingChange: bool = False

    migrationRequired: bool = False

    effectiveDate: datetime | None = None

    documentationUrls: list[str] = Field(default_factory=list)

    confidence: float = 0.0