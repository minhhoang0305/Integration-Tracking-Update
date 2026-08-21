import logging
import re

from models import ApiEndpoint

logger = logging.getLogger(__name__)


API_CHANGE_KEYWORDS: dict[str, list[str]] = {
    "DEPRECATION": [
        "deprecated",
        "deprecating",
        "deprecation",
        "sunset",
        "end of life",
        "eol",
        "discontinued",
    ],

    "VERSION_CHANGE": [
        "new api version",
        "api v2",
        "api v3",
        "api v4",
        "migrate",
        "migration",
        "upgrade api",
    ],

    "BREAKING_CHANGE": [
        "breaking change",
        "breaking changes",
        "no longer supported",
        "will stop working",
        "will no longer be available",
    ],

    "AUTH_CHANGE": [
        "oauth",
        "oauth2",
        "authentication",
        "authorization",
        "api key",
        "access token",
        "scope",
    ],

    "ENDPOINT_CHANGE": [
        "endpoint",
        "base url",
        "api url",
        "route",
    ],

    "RATE_LIMIT_CHANGE": [
        "rate limit",
        "rate limits",
        "requests per minute",
        "requests per second",
    ],
}

ENDPOINT_PATTERN = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[-A-Za-z0-9_./{}]+?)(?=\s*(?:GET|POST|PUT|PATCH|DELETE)\s+/|\s|$|[`),])",
    re.IGNORECASE,
)
NEW_ENDPOINT_MARKERS = ("new v3 endpoints", "latest api resources are now available", "new endpoints")


def extract_endpoint_changes(subject: str, body: str) -> tuple[list[ApiEndpoint], list[ApiEndpoint]]:
    """Extract announced endpoint paths from both Markdown and plain-text provider notices."""
    text = f"{subject}\n{body}"
    normalized = text.lower()
    marker_positions = [normalized.find(marker) for marker in NEW_ENDPOINT_MARKERS if normalized.find(marker) >= 0]
    split_at = min(marker_positions) if marker_positions else len(text)
    deprecated = _unique_endpoints(text[:split_at])
    announced = _unique_endpoints(text[split_at:]) if split_at < len(text) else []
    return deprecated, announced


def _unique_endpoints(text: str) -> list[ApiEndpoint]:
    values: list[ApiEndpoint] = []
    seen: set[tuple[str, str]] = set()
    for match in ENDPOINT_PATTERN.finditer(text):
        endpoint = ApiEndpoint(method=match.group(1).upper(), path=match.group(2).rstrip(".`"))
        key = (endpoint.method, endpoint.path)
        if key not in seen:
            seen.add(key)
            values.append(endpoint)
    return values


def detect_changes(
    subject: str,
    body: str,
) -> list[str]:
    text = f"{subject} {body}".lower()

    detected: list[str] = []

    for change_type, keywords in API_CHANGE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            detected.append(change_type)

    logger.info(
        "Rule detector found change types: %s",
        detected,
    )

    return detected


def detect_changes_with_evidence(
    subject: str,
    body: str,
) -> tuple[list[str], list[str]]:
    text = f"{subject} {body}".lower()
    change_types: list[str] = []
    matched_terms: list[str] = []

    for change_type, keywords in API_CHANGE_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword in text]
        if matches:
            change_types.append(change_type)
            matched_terms.extend(matches)

    return change_types, list(dict.fromkeys(matched_terms))
