import logging

from fastapi import FastAPI, HTTPException

from models import AnalyzeEmailRequest, ChangeEvidence, ChangeSignal
from rule_detector import detect_changes_with_evidence
import re


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s - "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Integration Tracking AI Service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "integration-tracking-ai"
    }


@app.post(
    "/analyze",
    response_model=ChangeSignal,
)
async def analyze_email(
    request: AnalyzeEmailRequest,
) -> ChangeSignal:
    try:
        logger.info(
            "Analyzing email %s from %s",
            request.emailId,
            request.sender,
        )

        if not request.body.strip() and not request.subject.strip():
            raise HTTPException(
                status_code=400,
                detail="Email subject or body is required.",
            )

        change_types, matched_terms = detect_changes_with_evidence(
            request.subject,
            request.body,
        )

        change_detected = len(change_types) > 0

        breaking_change = (
            "BREAKING_CHANGE" in change_types
            or "DEPRECATION" in change_types
        )

        migration_required = (
            "VERSION_CHANGE" in change_types
            or "DEPRECATION" in change_types
        )

        confidence = calculate_confidence(
            change_types,
        )

        result = ChangeSignal(
            emailId=request.emailId,
            isApiRelated=change_detected,
            changeDetected=change_detected,
            changeTypes=change_types,
            summary=(
                "Potential API change detected."
                if change_detected
                else "No API change detected."
            ),
            breakingChange=breaking_change,
            migrationRequired=migration_required,
            confidence=confidence,
            evidence=ChangeEvidence(
                matchedTerms=matched_terms,
                urls=re.findall(r"https?://[^\s)]+", f"{request.subject} {request.body}"),
            ),
        )

        logger.info(
            "Finished email %s. "
            "changeDetected=%s confidence=%.2f",
            request.emailId,
            result.changeDetected,
            result.confidence,
        )

        return result

    except HTTPException:
        raise

    except Exception as exception:
        logger.exception(
            "Failed to analyze email %s",
            request.emailId,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to analyze email.",
        ) from exception


def calculate_confidence(
    change_types: list[str],
) -> float:
    if not change_types:
        return 0.0

    score = 0.5 + len(change_types) * 0.1

    return min(score, 0.95)
